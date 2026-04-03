import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { bridgeUpdateBead, bridgeCommitBeadUpdate } from './bridge.js';

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
  });

  it('L0 complete: running -> submitted', () => {
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
});
