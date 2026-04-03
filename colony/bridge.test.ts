import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import Database from 'better-sqlite3';
import { bridgeUpdateBead, bridgeCommitBeadUpdate, markBridgeSynced } from './bridge.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeTmpDir(): string {
  return mkdtempSync(join(tmpdir(), 'bridge-test-'));
}

function writeBeadFile(dir: string, content: string): string {
  const path = join(dir, 'bead-001.md');
  writeFileSync(path, content, 'utf-8');
  return path;
}

function writeValidOutput(cloneDir: string): void {
  const sentinel = '<!-- BEAD_OUTPUT_COMPLETE -->';
  const content = 'x'.repeat(80) + '\n' + sentinel + '\n' + 'y'.repeat(20) + '\n';
  writeFileSync(join(cloneDir, 'bead-output.md'), content, 'utf-8');
}

/**
 * Initialize a git repo with an initial commit and a remote "origin"
 * pointing at a bare clone, so origin/main exists for SC-COL-26 checks.
 */
function initGitRepoWithOrigin(dir: string): void {
  execFileSync('git', ['init', dir], { encoding: 'utf-8' });
  execFileSync('git', ['-C', dir, 'config', 'user.email', 'test@test.com'], { encoding: 'utf-8' });
  execFileSync('git', ['-C', dir, 'config', 'user.name', 'Test'], { encoding: 'utf-8' });
  const readmePath = join(dir, 'README.md');
  writeFileSync(readmePath, '# Test\n', 'utf-8');
  execFileSync('git', ['-C', dir, 'add', '--', 'README.md'], { encoding: 'utf-8' });
  execFileSync('git', ['-C', dir, 'commit', '-m', 'init'], { encoding: 'utf-8' });

  // Create a bare clone to serve as "origin"
  const bareDir = dir + '-bare';
  execFileSync('git', ['clone', '--bare', dir, bareDir], { encoding: 'utf-8' });
  execFileSync('git', ['-C', dir, 'remote', 'add', 'origin', bareDir], { encoding: 'utf-8' });
  execFileSync('git', ['-C', dir, 'fetch', 'origin'], { encoding: 'utf-8' });
}

const RUNNING_BEAD = `# Bead

**BeadID:** bead-001
**Status:** running
**LoopLevel:** L0
**CorrectionHistory:** (none)
`;

const SUBMITTED_BEAD = `# Bead

**BeadID:** bead-001
**Status:** submitted
**LoopLevel:** L1
**CorrectionHistory:** (none)
`;

// ---------------------------------------------------------------------------
// T3.2: Bridge status update tests
// ---------------------------------------------------------------------------

describe('bridgeUpdateBead', () => {
  let beadDir: string;
  let cloneDir: string;

  beforeEach(() => {
    beadDir = makeTmpDir();
    cloneDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(beadDir, { recursive: true, force: true });
    rmSync(cloneDir, { recursive: true, force: true });
    // Clean up bare repos if they exist
    try { rmSync(cloneDir + '-bare', { recursive: true, force: true }); } catch {}
  });

  it('L0 complete: running -> submitted', () => {
    initGitRepoWithOrigin(cloneDir);
    // Add a commit beyond origin/main
    writeFileSync(join(cloneDir, 'work.ts'), 'export const x = 1;\n', 'utf-8');
    execFileSync('git', ['-C', cloneDir, 'add', '--', 'work.ts'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'commit', '-m', 'worker commit'], { encoding: 'utf-8' });

    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('advanced');
    expect(result.newStatus).toBe('submitted');

    const updated = readFileSync(beadPath, 'utf-8');
    expect(updated).toContain('**Status:** submitted');
  });

  it('SC-COL-14: rejects NULL loop level', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: null,
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-14');
  });

  it('SC-COL-14: rejects undefined loop level', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: undefined,
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-14');
  });

  it('SC-COL-14: rejects empty string loop level', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: '',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-14');
  });

  it('SC-COL-15: compare-and-swap rejects status mismatch', () => {
    const beadPath = writeBeadFile(beadDir, SUBMITTED_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
      expectedSourceStatus: 'running',
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('status mismatch');
  });

  it('SC-COL-15: idempotent skip when already at target', () => {
    // Bead is already submitted, L0 wants running->submitted
    const beadPath = writeBeadFile(beadDir, SUBMITTED_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('skipped');
  });

  it('Adversarial A1: skipped action means no git commit is attempted', () => {
    // When bead is already at target status, bridgeUpdateBead returns {action: 'skipped'}.
    // bridge-cli must NOT call bridgeCommitBeadUpdate in this case.
    // We verify the invariant at the bridgeUpdateBead level: skipped result is
    // success=true with action='skipped', so bridge-cli will short-circuit.
    const beadPath = writeBeadFile(beadDir, SUBMITTED_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('skipped');
    // Verify the bead file was NOT modified (no write occurred)
    const content = readFileSync(beadPath, 'utf-8');
    expect(content).toBe(SUBMITTED_BEAD);
  });

  it('SC-COL-22: rejects missing bead-output.md', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    // No output file written to cloneDir

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-22');
    expect(result.error).toContain('not found');
  });

  it('SC-COL-22: rejects output < 100 bytes', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeFileSync(join(cloneDir, 'bead-output.md'), 'too small\n<!-- BEAD_OUTPUT_COMPLETE -->', 'utf-8');

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-22');
    expect(result.error).toContain('too small');
  });

  it('SC-COL-22: rejects missing sentinel', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    // >100 bytes but no sentinel
    writeFileSync(join(cloneDir, 'bead-output.md'), 'x'.repeat(200), 'utf-8');

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-22');
    expect(result.error).toContain('sentinel');
  });

  it('appends correction on failure without status change', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: false,
      finding: 'Tests failed: assertion error in line 42',
      cycle: 1,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('correction');

    const updated = readFileSync(beadPath, 'utf-8');
    expect(updated).toContain('**Status:** running');
    expect(updated).toContain('- [L0 cycle 1] Tests failed: assertion error in line 42');
    expect(updated).not.toContain('(none)');
  });

  // --- Adversarial audit tests ---

  it('CRITICAL: rejects CAS bypass via unknown/corrupted status', () => {
    const CORRUPTED_BEAD = `# Bead

**BeadID:** bead-001
**Status:** corrupted
**LoopLevel:** L0
**CorrectionHistory:** (none)
`;
    const beadPath = writeBeadFile(beadDir, CORRUPTED_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
      expectedSourceStatus: 'corrupted',
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('not recognized');
  });

  it('HIGH: rejects unknown loop level with taskCompleted=true', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L99',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('Unknown loop level');
  });

  it('HIGH: sentinel-with-garbage passes (content quality is Conductor concern)', () => {
    // 200 spaces + sentinel = valid per bridge rules.
    // Content quality enforcement is the Conductor's responsibility, not the bridge's.
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    const sentinel = '<!-- BEAD_OUTPUT_COMPLETE -->';
    const garbageContent = ' '.repeat(200) + sentinel + '\n';
    writeFileSync(join(cloneDir, 'bead-output.md'), garbageContent, 'utf-8');

    // Clone needs commits for L0 check -- init a git repo with origin
    initGitRepoWithOrigin(cloneDir);
    writeFileSync(join(cloneDir, 'work.ts'), 'export const x = 1;\n', 'utf-8');
    execFileSync('git', ['-C', cloneDir, 'add', '--', 'work.ts'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'commit', '-m', 'worker commit'], { encoding: 'utf-8' });
    // Re-write the output after git init overwrote it
    writeFileSync(join(cloneDir, 'bead-output.md'), garbageContent, 'utf-8');

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    // This passes because the bridge only checks size + sentinel presence.
    // Documenting this as a known limitation per adversarial audit.
    expect(result.success).toBe(true);
    expect(result.action).toBe('advanced');
  });

  it('MEDIUM: exactly 100 bytes with sentinel succeeds', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    const sentinel = '<!-- BEAD_OUTPUT_COMPLETE -->';
    // sentinel is 28 bytes, need 72 more bytes of content to reach exactly 100
    const padding = 'x'.repeat(100 - sentinel.length);
    const content = padding + sentinel;
    expect(Buffer.byteLength(content, 'utf-8')).toBe(100);
    writeFileSync(join(cloneDir, 'bead-output.md'), content, 'utf-8');

    // Clone needs commits for L0 -- init git repo with origin
    initGitRepoWithOrigin(cloneDir);
    writeFileSync(join(cloneDir, 'work.ts'), 'export const x = 1;\n', 'utf-8');
    execFileSync('git', ['-C', cloneDir, 'add', '--', 'work.ts'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'commit', '-m', 'worker commit'], { encoding: 'utf-8' });
    // Re-write output after git init
    writeFileSync(join(cloneDir, 'bead-output.md'), content, 'utf-8');

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('advanced');
  });

  it('MEDIUM: exactly 99 bytes with sentinel fails', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    const sentinel = '<!-- BEAD_OUTPUT_COMPLETE -->';
    // sentinel is 28 bytes, need 71 more bytes of content to reach exactly 99
    const padding = 'x'.repeat(99 - sentinel.length);
    const content = padding + sentinel;
    expect(Buffer.byteLength(content, 'utf-8')).toBe(99);
    writeFileSync(join(cloneDir, 'bead-output.md'), content, 'utf-8');

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('too small');
  });

  // --- SC-COL-26: Clone commit verification ---

  it('SC-COL-26: rejects L0 advancement when clone has no commits beyond origin', () => {
    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeValidOutput(cloneDir);

    // Init git repo with origin but make NO additional commits
    initGitRepoWithOrigin(cloneDir);
    // Re-write output after git init
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-26');
    expect(result.error).toContain('no commits beyond source HEAD');
  });

  it('SC-COL-26: fails when clone has no origin remote (unresolvable ref)', () => {
    // Init git repo WITHOUT any remote -- verifyCloneHasCommits should return valid: false
    execFileSync('git', ['init', cloneDir], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'config', 'user.email', 'test@test.com'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'config', 'user.name', 'Test'], { encoding: 'utf-8' });
    writeFileSync(join(cloneDir, 'README.md'), '# Test\n', 'utf-8');
    execFileSync('git', ['-C', cloneDir, 'add', '--', 'README.md'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', cloneDir, 'commit', '-m', 'init'], { encoding: 'utf-8' });
    // No remote added -- origin/main and origin/master are unresolvable

    const beadPath = writeBeadFile(beadDir, RUNNING_BEAD);
    writeValidOutput(cloneDir);

    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L0',
      taskCompleted: true,
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-26');
    expect(result.error).toContain('Could not resolve remote ref');
  });

  it('SC-COL-26: allows L1 advancement without commit check', () => {
    const beadPath = writeBeadFile(beadDir, SUBMITTED_BEAD);
    writeValidOutput(cloneDir);

    // L1 does not check for commits, so no git repo needed in cloneDir
    const result = bridgeUpdateBead({
      beadFilePath: beadPath,
      cloneDir,
      loopLevel: 'L1',
      taskCompleted: true,
    });

    expect(result.success).toBe(true);
    expect(result.action).toBe('advanced');
    expect(result.newStatus).toBe('verified');
  });
});

// ---------------------------------------------------------------------------
// T3.3: Bridge git commit tests
// ---------------------------------------------------------------------------

describe('bridgeCommitBeadUpdate', () => {
  let projectDir: string;

  beforeEach(() => {
    projectDir = makeTmpDir();
    // Initialize git repo
    execFileSync('git', ['init', projectDir], { encoding: 'utf-8' });
    execFileSync('git', ['-C', projectDir, 'config', 'user.email', 'test@test.com'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', projectDir, 'config', 'user.name', 'Test'], { encoding: 'utf-8' });
    // Create initial commit so HEAD exists
    const readmePath = join(projectDir, 'README.md');
    writeFileSync(readmePath, '# Test\n', 'utf-8');
    execFileSync('git', ['-C', projectDir, 'add', '--', 'README.md'], { encoding: 'utf-8' });
    execFileSync('git', ['-C', projectDir, 'commit', '-m', 'init'], { encoding: 'utf-8' });
  });

  afterEach(() => {
    rmSync(projectDir, { recursive: true, force: true });
  });

  it('SC-COL-29: commits only the specific bead file (decoy not in diff)', () => {
    // Write bead file
    const beadDir = join(projectDir, 'beads');
    mkdirSync(beadDir, { recursive: true });
    const beadPath = join(beadDir, 'bead-001.md');
    writeFileSync(beadPath, '**BeadID:** bead-001\n**Status:** submitted\n', 'utf-8');

    // Write decoy file (should NOT be committed)
    const decoyPath = join(projectDir, 'decoy.txt');
    writeFileSync(decoyPath, 'I should not be committed\n', 'utf-8');

    const result = bridgeCommitBeadUpdate(
      projectDir,
      beadPath,
      'bead-001',
      'L0',
      'main',
    );

    expect(result.success).toBe(true);
    expect(result.commitHash).toBeDefined();

    // Verify: decoy should NOT be in the committed diff
    const diffOutput = execFileSync(
      'git',
      ['-C', projectDir, 'diff', 'HEAD~1', 'HEAD', '--name-only'],
      { encoding: 'utf-8' },
    );
    expect(diffOutput.trim()).toBe('beads/bead-001.md');
    expect(diffOutput).not.toContain('decoy.txt');

    // Verify decoy is still untracked
    const statusOutput = execFileSync(
      'git',
      ['-C', projectDir, 'status', '--porcelain'],
      { encoding: 'utf-8' },
    );
    expect(statusOutput).toContain('decoy.txt');
  });

  it('SC-COL-30: rejects commit when on wrong branch', () => {
    // Create and switch to a different branch
    execFileSync('git', ['-C', projectDir, 'checkout', '-b', 'feature-branch'], { encoding: 'utf-8' });

    const beadPath = join(projectDir, 'bead-001.md');
    writeFileSync(beadPath, '**BeadID:** bead-001\n**Status:** submitted\n', 'utf-8');

    const result = bridgeCommitBeadUpdate(
      projectDir,
      beadPath,
      'bead-001',
      'L0',
      'main', // expected main, but we're on feature-branch
    );

    expect(result.success).toBe(false);
    expect(result.error).toContain('SC-COL-30');
    expect(result.error).toContain('branch mismatch');
  });

  it('returns taskId in result when provided', () => {
    const beadPath = join(projectDir, 'bead-001.md');
    writeFileSync(beadPath, '**BeadID:** bead-001\n**Status:** submitted\n', 'utf-8');

    const result = bridgeCommitBeadUpdate(
      projectDir,
      beadPath,
      'bead-001',
      'L0',
      'main',
      'task-abc-123',
    );

    expect(result.success).toBe(true);
    expect(result.taskId).toBe('task-abc-123');
  });
});

// ---------------------------------------------------------------------------
// markBridgeSynced tests (Gap 1)
// ---------------------------------------------------------------------------

describe('markBridgeSynced', () => {
  let dbPath: string;
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
    dbPath = join(tmpDir, 'test-tmup.db');
    const db = new Database(dbPath);
    db.exec(`
      CREATE TABLE tasks (
        id TEXT PRIMARY KEY,
        bridge_synced INTEGER DEFAULT 0
      );
      INSERT INTO tasks (id, bridge_synced) VALUES ('task-001', 0);
      INSERT INTO tasks (id, bridge_synced) VALUES ('task-002', 0);
    `);
    db.close();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it('sets bridge_synced to 1 for the specified task', () => {
    markBridgeSynced(dbPath, 'task-001');

    const db = new Database(dbPath, { readonly: true });
    const row = db.prepare('SELECT bridge_synced FROM tasks WHERE id = ?').get('task-001') as { bridge_synced: number };
    const other = db.prepare('SELECT bridge_synced FROM tasks WHERE id = ?').get('task-002') as { bridge_synced: number };
    db.close();

    expect(row.bridge_synced).toBe(1);
    expect(other.bridge_synced).toBe(0);
  });

  it('is idempotent (calling twice does not error)', () => {
    markBridgeSynced(dbPath, 'task-001');
    markBridgeSynced(dbPath, 'task-001');

    const db = new Database(dbPath, { readonly: true });
    const row = db.prepare('SELECT bridge_synced FROM tasks WHERE id = ?').get('task-001') as { bridge_synced: number };
    db.close();

    expect(row.bridge_synced).toBe(1);
  });
});
