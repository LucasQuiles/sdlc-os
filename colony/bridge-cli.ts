#!/usr/bin/env node
/**
 * Bridge CLI wrapper.
 *
 * Parses command-line arguments, calls bridgeUpdateBead then
 * bridgeCommitBeadUpdate, and outputs JSON result.
 *
 * Usage:
 *   npx tsx bridge-cli.ts \
 *     --bead-file path/to/bead.md \
 *     --clone-dir /tmp/sdlc-colony/session/worker-1 \
 *     --loop-level L0 \
 *     --completed \
 *     --project-dir /path/to/project \
 *     --expected-branch main \
 *     --expected-status running \
 *     --task-id <tmup-task-id> \
 *     --db-path /path/to/tmup.db
 *
 * On failure (not completed):
 *   npx tsx bridge-cli.ts \
 *     --bead-file path/to/bead.md \
 *     --clone-dir /tmp/sdlc-colony/session/worker-1 \
 *     --loop-level L0 \
 *     --finding "Tests failed" \
 *     --cycle 1 \
 *     --project-dir /path/to/project \
 *     --expected-branch main
 */

import { bridgeUpdateBead, bridgeCommitBeadUpdate, markBridgeSynced } from './bridge.js';
import type { BridgeInput } from './bridge.js';
import { basename } from 'node:path';

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function parseArgs(argv: string[]): {
  beadFile: string;
  cloneDir: string;
  loopLevel: string;
  completed: boolean;
  finding?: string;
  cycle?: number;
  projectDir: string;
  expectedBranch: string;
  expectedStatus?: string;
  taskId?: string;
  dbPath?: string;
} {
  const args: Record<string, string> = {};
  const flags = new Set<string>();

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--completed') {
      flags.add('completed');
    } else if (arg.startsWith('--') && i + 1 < argv.length) {
      const key = arg.slice(2);
      args[key] = argv[++i];
    }
  }

  const required = (name: string): string => {
    const value = args[name];
    if (!value) {
      throw new Error(`Missing required argument: --${name}`);
    }
    return value;
  };

  return {
    beadFile: required('bead-file'),
    cloneDir: required('clone-dir'),
    loopLevel: required('loop-level'),
    completed: flags.has('completed'),
    finding: args['finding'],
    cycle: args['cycle'] !== undefined ? parseInt(args['cycle'], 10) : undefined,
    projectDir: required('project-dir'),
    expectedBranch: required('expected-branch'),
    expectedStatus: args['expected-status'],
    taskId: args['task-id'],
    dbPath: args['db-path'],
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  const startMs = Date.now();

  let parsed;
  try {
    parsed = parseArgs(process.argv);
  } catch (err) {
    const elapsedMs = Date.now() - startMs;
    const output = {
      success: false,
      error: (err as Error).message,
      elapsed_ms: elapsedMs,
    };
    process.stdout.write(JSON.stringify(output, null, 2) + '\n');
    process.exit(1);
  }

  // Step 1: Update bead file
  const bridgeInput: BridgeInput = {
    beadFilePath: parsed.beadFile,
    cloneDir: parsed.cloneDir,
    loopLevel: parsed.loopLevel,
    taskCompleted: parsed.completed,
    finding: parsed.finding,
    cycle: parsed.cycle,
    expectedSourceStatus: parsed.expectedStatus,
  };

  const beadResult = bridgeUpdateBead(bridgeInput);

  if (!beadResult.success) {
    const elapsedMs = Date.now() - startMs;
    process.stdout.write(JSON.stringify({ beadUpdate: beadResult, elapsed_ms: elapsedMs }, null, 2) + '\n');
    process.exit(1);
  }

  // Adversarial A1: If bead is already at target status, skip commit entirely.
  // bridgeUpdateBead returns {action: 'skipped'} when bead is already at or beyond
  // the target status. Attempting git commit on an unmodified file would fail.
  if (beadResult.action === 'skipped') {
    const elapsedMs = Date.now() - startMs;
    process.stdout.write(JSON.stringify({ beadUpdate: beadResult, elapsed_ms: elapsedMs }, null, 2) + '\n');
    process.exit(0);
  }

  // Step 2: Commit the bead update to git
  const commitResult = bridgeCommitBeadUpdate(
    parsed.projectDir,
    parsed.beadFile,
    basename(parsed.beadFile, '.md'), // beadId extracted from filename
    parsed.loopLevel,
    parsed.expectedBranch,
    parsed.taskId,
  );

  // Step 3: Mark bridge_synced only on successful advancement (not corrections)
  if (commitResult.success && beadResult.action === 'advanced' && parsed.taskId && parsed.dbPath) {
    try {
      markBridgeSynced(parsed.dbPath, parsed.taskId);
    } catch (err) {
      // Non-fatal: log but don't fail the overall bridge operation
      console.error(`[bridge-cli] Warning: failed to mark bridge_synced: ${(err as Error).message}`);
    }
  }

  const elapsedMs = Date.now() - startMs;
  const output = {
    beadUpdate: beadResult,
    commit: commitResult,
    elapsed_ms: elapsedMs,
  };

  process.stdout.write(JSON.stringify(output, null, 2) + '\n');

  if (!commitResult.success) {
    process.exit(1);
  }
}

main();
