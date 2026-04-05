/**
 * Bead-Task Bridge -- deterministic (no LLM) synchronization layer.
 *
 * Called by the Conductor after evaluating each completed task.
 * Synchronizes tmup task completion to sdlc-os bead files.
 *
 * Safety constraints implemented:
 *   SC-COL-14: NULL loop level = fatal error
 *   SC-COL-15: Compare-and-swap on bead status
 *   SC-COL-22: Verify bead-output.md exists, >100 bytes, has sentinel
 *   SC-COL-26: Verify clone has commits beyond source HEAD before advancement
 *   SC-COL-28: Atomic write via temp + rename
 *   SC-COL-29: git add -- specific file only
 *   SC-COL-30: Verify branch before commit
 */

import { readFileSync, writeFileSync, appendFileSync, renameSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import Database from 'better-sqlite3';
import { parseBeadFile, updateBeadField, appendCorrection } from './bead-parser.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BridgeInput {
  beadFilePath: string;
  cloneDir: string;
  loopLevel: string | null | undefined;
  taskCompleted: boolean;
  finding?: string;
  cycle?: number;
  expectedSourceStatus?: string;
}

export interface BridgeResult {
  success: boolean;
  action: 'advanced' | 'correction' | 'skipped' | 'error';
  error?: string;
  newStatus?: string;
}

export interface CommitResult {
  success: boolean;
  commitHash?: string;
  error?: string;
  taskId?: string;
}

// ---------------------------------------------------------------------------
// Bridge telemetry
// ---------------------------------------------------------------------------

export interface BridgeLogEntry {
  timestamp: string;
  bead_id: string;
  loop_level: string;
  action: 'advanced' | 'correction' | 'skipped' | 'error';
  elapsed_ms: number;
  safety_constraints: string[];
  error?: string;
}

/**
 * Append a JSON-line log entry to the bridge log file.
 * Path is taken from COLONY_BRIDGE_LOG env var, defaulting to ./colony-bridge.log.
 */
export function logBridgeCall(entry: BridgeLogEntry): void {
  try {
    const logPath = process.env['COLONY_BRIDGE_LOG'] || '/tmp/sdlc-colony/colony-bridge.log';
    appendFileSync(logPath, JSON.stringify(entry) + '\n', 'utf-8');
  } catch {
    // Logging must never crash the bridge
  }
}

// ---------------------------------------------------------------------------
// Event emission (spec §11.4 — JSONL inbox for Deacon batch ingest)
// ---------------------------------------------------------------------------

export interface BridgeEvent {
  event_id: string;
  event_type: string;
  workstream_id: string;
  bead_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
  processing_level: string;
  idempotency_key: string;
}

/**
 * Append a typed event JSON line to the events inbox file.
 * The Deacon batch-ingests from this file into events.db.
 * Uses appendFileSync for atomic-at-line-level writes under concurrent access.
 */
export function appendEventToInbox(inboxPath: string, event: BridgeEvent): void {
  const line = JSON.stringify(event) + '\n';
  appendFileSync(inboxPath, line, 'utf8');
}

function makeEventId(beadId: string): string {
  return `evt-${Date.now()}-${beadId.slice(0, 8)}`;
}

// ---------------------------------------------------------------------------
// Status transition map (spec SS5.3)
// ---------------------------------------------------------------------------

export const STATUS_TRANSITIONS: Record<string, { from: string; to: string }> = {
  L0:      { from: 'running',   to: 'submitted' },
  L1:      { from: 'submitted', to: 'verified' },
  L2:      { from: 'verified',  to: 'proven' },
  'L2.5':  { from: 'proven',    to: 'hardened' },
  'L2.75': { from: 'hardened',  to: 'reliability-proven' },
};

const STATUS_ORDER: string[] = [
  'running',
  'submitted',
  'verified',
  'proven',
  'hardened',
  'reliability-proven',
];

function statusIndex(status: string): number {
  return STATUS_ORDER.indexOf(status);
}

// ---------------------------------------------------------------------------
// Output validation (SC-COL-22)
// ---------------------------------------------------------------------------

const OUTPUT_SENTINEL = '<!-- BEAD_OUTPUT_COMPLETE -->';
const MIN_OUTPUT_BYTES = 100;

function validateOutput(cloneDir: string): { valid: boolean; error?: string } {
  const outputPath = join(cloneDir, 'bead-output.md');

  if (!existsSync(outputPath)) {
    return { valid: false, error: `bead-output.md not found at ${outputPath}` };
  }

  // Single read: derive size from buffer length instead of separate statSync
  const content = readFileSync(outputPath, 'utf-8');
  const byteSize = Buffer.byteLength(content, 'utf-8');
  if (byteSize < MIN_OUTPUT_BYTES) {
    return { valid: false, error: `bead-output.md too small: ${byteSize} bytes (minimum ${MIN_OUTPUT_BYTES})` };
  }

  if (!content.includes(OUTPUT_SENTINEL)) {
    return { valid: false, error: `bead-output.md missing sentinel: ${OUTPUT_SENTINEL}` };
  }

  return { valid: true };
}

// ---------------------------------------------------------------------------
// Clone commit verification (SC-COL-26)
// ---------------------------------------------------------------------------

function verifyCloneHasCommits(cloneDir: string): { valid: boolean; error?: string } {
  for (const ref of ['origin/main', 'origin/master']) {
    try {
      const output = execFileSync(
        'git',
        ['-C', cloneDir, 'log', '--oneline', `${ref}..HEAD`],
        { encoding: 'utf-8' },
      ).trim();

      const lines = output.split('\n').filter(l => l.length > 0);
      if (lines.length >= 1) {
        return { valid: true };
      }
      return { valid: false, error: 'SC-COL-26: clone has no commits beyond source HEAD' };
    } catch {
      continue;
    }
  }
  return { valid: false, error: 'SC-COL-26: could not resolve remote ref for commit verification' };
}

// ---------------------------------------------------------------------------
// Atomic file write (SC-COL-28)
// ---------------------------------------------------------------------------

function atomicWriteFile(filePath: string, content: string): void {
  const tmpPath = filePath + '.tmp.' + process.pid;
  writeFileSync(tmpPath, content, 'utf-8');
  renameSync(tmpPath, filePath);
}

// ---------------------------------------------------------------------------
// Mark bridge_synced in tmup DB (Gap 1 fix)
// ---------------------------------------------------------------------------

/**
 * Set bridge_synced = 1 for a task in the tmup SQLite DB.
 * Called after successful bead commit so clone pruning, check_for_work,
 * and recovery know this task's bead file has been synced.
 */
export function markBridgeSynced(dbPath: string, taskId: string): { success: boolean; error?: string } {
  try {
    const db = new Database(dbPath, { timeout: 8000 });
    try {
      db.prepare('UPDATE tasks SET bridge_synced = 1 WHERE id = ?').run(taskId);
      return { success: true };
    } finally {
      db.close();
    }
  } catch (err) {
    return { success: false, error: (err as Error).message };
  }
}

// ---------------------------------------------------------------------------
// Core bridge function
// ---------------------------------------------------------------------------

export function bridgeUpdateBead(input: BridgeInput): BridgeResult {
  const startMs = Date.now();
  const { beadFilePath, cloneDir, loopLevel, taskCompleted, finding, cycle } = input;
  const constraintsChecked: string[] = [];

  // Extract bead ID from file path for logging
  const beadId = beadFilePath.replace(/.*\//, '').replace(/\.md$/, '');

  function finalize(result: BridgeResult): BridgeResult {
    const elapsed = Date.now() - startMs;
    logBridgeCall({
      timestamp: new Date().toISOString(),
      bead_id: beadId,
      loop_level: loopLevel ?? 'null',
      action: result.action,
      elapsed_ms: elapsed,
      safety_constraints: constraintsChecked,
      ...(result.error ? { error: result.error } : {}),
    });
    return result;
  }

  // SC-COL-14: NULL loop level is fatal
  constraintsChecked.push('SC-COL-14');
  if (loopLevel === null || loopLevel === undefined || loopLevel === '') {
    return finalize({
      success: false,
      action: 'error',
      error: 'SC-COL-14: NULL loop level is a fatal error',
    });
  }

  // Read current bead file
  let beadContent: string;
  try {
    beadContent = readFileSync(beadFilePath, 'utf-8');
  } catch (err) {
    return finalize({
      success: false,
      action: 'error',
      error: `Failed to read bead file: ${(err as Error).message}`,
    });
  }

  const beadFields = parseBeadFile(beadContent);

  // Handle failure: append correction, no status change
  if (!taskCompleted) {
    const correctionText = finding || 'Task failed (no finding provided)';
    const correctionCycle = cycle ?? 0;
    const updatedContent = appendCorrection(beadContent, loopLevel, correctionCycle, correctionText);
    // SC-COL-28: atomic write
    constraintsChecked.push('SC-COL-28');
    atomicWriteFile(beadFilePath, updatedContent);

    // Emit bead_failed event to JSONL inbox
    try {
      const inboxPath = join(dirname(cloneDir), 'events-inbox.jsonl');
      appendEventToInbox(inboxPath, {
        event_id: makeEventId(beadId),
        event_type: 'bead_failed',
        workstream_id: '',
        bead_id: beadId,
        timestamp: new Date().toISOString(),
        payload: {
          finding: correctionText,
          cycle: correctionCycle,
          loop_level: loopLevel,
        },
        processing_level: loopLevel,
        idempotency_key: `bead_failed:${beadId}:${loopLevel}:${correctionCycle}`,
      });
    } catch {
      // Event emission must never crash the bridge
    }

    return finalize({
      success: true,
      action: 'correction',
    });
  }

  // Task completed -- validate output (SC-COL-22)
  constraintsChecked.push('SC-COL-22');
  const outputCheck = validateOutput(cloneDir);
  if (!outputCheck.valid) {
    return finalize({
      success: false,
      action: 'error',
      error: `SC-COL-22: ${outputCheck.error}`,
    });
  }

  // Look up expected transition
  const transition = STATUS_TRANSITIONS[loopLevel];
  if (!transition) {
    return finalize({
      success: false,
      action: 'error',
      error: `Unknown loop level: ${loopLevel}`,
    });
  }

  // SC-COL-15: Compare-and-swap on bead status
  // Status checks run BEFORE SC-COL-26 so that idempotent skips and CAS
  // rejections short-circuit without requiring clone verification.
  constraintsChecked.push('SC-COL-15');
  const currentStatus = beadFields.Status;
  const currentIdx = statusIndex(currentStatus);
  const targetIdx = statusIndex(transition.to);

  // If expectedSourceStatus is provided, verify it matches current FIRST.
  // Compare-and-swap takes priority over idempotent skip.
  if (input.expectedSourceStatus !== undefined) {
    if (currentStatus !== input.expectedSourceStatus) {
      return finalize({
        success: false,
        action: 'error',
        error: `status mismatch: expected '${input.expectedSourceStatus}', found '${currentStatus}'`,
      });
    }
  }

  // Guard: reject unknown/corrupted bead status
  if (currentIdx === -1) {
    return finalize({
      success: false,
      action: 'error',
      error: `Bead status not recognized: '${currentStatus}'. Cannot advance from unknown state.`,
    });
  }

  // Idempotent: if already at or beyond target, skip
  if (currentIdx >= targetIdx && targetIdx !== -1) {
    return finalize({
      success: true,
      action: 'skipped',
      newStatus: currentStatus,
    });
  }

  // Default check (no explicit expectedSourceStatus): current must match transition.from
  if (input.expectedSourceStatus === undefined && currentStatus !== transition.from) {
    return finalize({
      success: false,
      action: 'error',
      error: `status mismatch: expected '${transition.from}', found '${currentStatus}'`,
    });
  }

  // SC-COL-26: Verify clone has commits at L0 (first advancement)
  // Runs after status checks so idempotent skips don't need clone verification.
  if (loopLevel === 'L0') {
    constraintsChecked.push('SC-COL-26');
    const commitCheck = verifyCloneHasCommits(cloneDir);
    if (!commitCheck.valid) {
      return finalize({
        success: false,
        action: 'error',
        error: commitCheck.error!,
      });
    }
  }

  // Apply status transition (SC-COL-28: atomic write)
  constraintsChecked.push('SC-COL-28');
  const updatedContent = updateBeadField(beadContent, 'Status', transition.to);
  atomicWriteFile(beadFilePath, updatedContent);

  // Emit bead_completed event to JSONL inbox
  try {
    const inboxPath = join(dirname(cloneDir), 'events-inbox.jsonl');
    appendEventToInbox(inboxPath, {
      event_id: makeEventId(beadId),
      event_type: 'bead_completed',
      workstream_id: '',
      bead_id: beadId,
      timestamp: new Date().toISOString(),
      payload: {
        new_status: transition.to,
        loop_level: loopLevel,
        output_summary: `Bead ${beadId} advanced to ${transition.to}`,
      },
      processing_level: loopLevel,
      idempotency_key: `bead_completed:${beadId}:${loopLevel}:${statusIndex(transition.to)}`,
    });
  } catch {
    // Event emission must never crash the bridge
  }

  return finalize({
    success: true,
    action: 'advanced',
    newStatus: transition.to,
  });
}

// ---------------------------------------------------------------------------
// Git commit (SC-COL-29, SC-COL-30)
// ---------------------------------------------------------------------------

/**
 * Commit a bead file update to git.
 *
 * SC-COL-29: Uses `git add -- specific-file` (never git add -A).
 *            Uses execFileSync (no shell injection).
 * SC-COL-30: Verifies current branch matches expectedBranch before committing.
 *
 * @param taskId - Optional tmup task ID; returned in result so caller can call markBridgeSynced.
 */
export function bridgeCommitBeadUpdate(
  projectDir: string,
  beadFilePath: string,
  beadId: string,
  loopLevel: string,
  expectedBranch: string,
  taskId?: string,
): CommitResult {
  // SC-COL-30: Verify branch
  let currentBranch: string;
  try {
    currentBranch = execFileSync(
      'git',
      ['-C', projectDir, 'rev-parse', '--abbrev-ref', 'HEAD'],
      { encoding: 'utf-8' },
    ).trim();
  } catch (err) {
    return {
      success: false,
      error: `Failed to determine current branch: ${(err as Error).message}`,
    };
  }

  if (currentBranch !== expectedBranch) {
    return {
      success: false,
      error: `SC-COL-30: branch mismatch: expected '${expectedBranch}', on '${currentBranch}'`,
    };
  }

  // SC-COL-29: Stage only the specific bead file
  try {
    execFileSync('git', ['-C', projectDir, 'add', '--', beadFilePath], {
      encoding: 'utf-8',
    });
  } catch (err) {
    return {
      success: false,
      error: `git add failed: ${(err as Error).message}`,
    };
  }

  // Commit
  const commitMessage = `fix(sdlc): bridge update bead ${beadId} [${loopLevel}]`;
  try {
    execFileSync(
      'git',
      ['-C', projectDir, 'commit', '-m', commitMessage],
      { encoding: 'utf-8' },
    );
  } catch (err) {
    return {
      success: false,
      error: `git commit failed: ${(err as Error).message}`,
    };
  }

  // Get commit hash
  let commitHash: string;
  try {
    commitHash = execFileSync(
      'git',
      ['-C', projectDir, 'rev-parse', 'HEAD'],
      { encoding: 'utf-8' },
    ).trim();
  } catch {
    commitHash = 'unknown';
  }

  // Get changed files for event payload
  let changedFiles: string[] = [];
  try {
    const diffOutput = execFileSync(
      'git',
      ['-C', projectDir, 'diff', 'HEAD~1', 'HEAD', '--name-only'],
      { encoding: 'utf-8' },
    ).trim();
    changedFiles = diffOutput.split('\n').filter(l => l.length > 0);
  } catch {
    changedFiles = [beadFilePath];
  }

  // Emit commit_created event to JSONL inbox
  try {
    const inboxPath = join(dirname(projectDir), 'events-inbox.jsonl');
    appendEventToInbox(inboxPath, {
      event_id: makeEventId(beadId),
      event_type: 'commit_created',
      workstream_id: '',
      bead_id: beadId,
      timestamp: new Date().toISOString(),
      payload: {
        commit_hash: commitHash,
        changed_files: changedFiles,
        loop_level: loopLevel,
      },
      processing_level: loopLevel,
      idempotency_key: `commit_created:${beadId}:${loopLevel}:${commitHash.slice(0, 8)}`,
    });
  } catch {
    // Event emission must never crash the bridge
  }

  return {
    success: true,
    commitHash,
    taskId,
  };
}
