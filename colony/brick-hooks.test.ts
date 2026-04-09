import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';

let secretToolShouldFail = false;

vi.mock('node:child_process', async () => {
  const actual = await vi.importActual<typeof import('node:child_process')>('node:child_process');
  return {
    ...actual,
    execSync: (cmd: string, opts?: object) => {
      if (typeof cmd === 'string' && cmd.includes('secret-tool') && secretToolShouldFail) {
        throw new Error('keyring unavailable');
      }
      return actual.execSync(cmd, opts as Parameters<typeof actual.execSync>[1]);
    },
  };
});

// Must import after vi.mock so the mock is applied
const { preprocessForEvaluation, buildBrickEvalParams } = await import('./brick-hooks.js');

const CLONE_DIR = '/tmp/colony-brick-test-clone';

const fakeBrickResponse = {
  summary: 'Brick analysis complete',
  flagged_risks: ['potential regression in auth module'],
  decisions_detected: ['switched from JWT to session tokens'],
  uncertainties: ['unclear error handling in edge case'],
};

describe('brick-hooks', () => {
  beforeEach(() => {
    process.env.BRICK_API_KEY = 'test-key-for-unit-tests';
    mkdirSync(CLONE_DIR, { recursive: true });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(fakeBrickResponse),
        text: () => Promise.resolve(JSON.stringify(fakeBrickResponse)),
      }),
    );
  });

  afterEach(() => {
    delete process.env.BRICK_API_KEY;
    vi.restoreAllMocks();
    rmSync(CLONE_DIR, { recursive: true, force: true });
  });

  it('returns available=true when bead-output.md exists', async () => {
    writeFileSync(
      `${CLONE_DIR}/bead-output.md`,
      '# Output\nTask completed successfully.\n<!-- BEAD_OUTPUT_COMPLETE -->',
    );
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-test');
    expect(result.available).toBe(true);
    expect(result.summary).toBe('Brick analysis complete');
    expect(result.flagged_risks).toContain('potential regression in auth module');
  });

  it('returns available=false when bead-output.md missing', async () => {
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-missing');
    expect(result.available).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('builds correct Brick MCP parameters', () => {
    const params = buildBrickEvalParams('diff content here');
    expect(params.task_class).toBe('diff_review');
    expect(params.format_hint).toBe('diff');
    expect(params.intent_key).toBe('flag_risks');
    expect(params.content).toBe('diff content here');
  });

  it('handles empty bead output gracefully', async () => {
    writeFileSync(`${CLONE_DIR}/bead-output.md`, '');
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-empty');
    expect(result.available).toBe(true);
  });

  it('returns degraded mode when BRICK_API_KEY is missing and keyring unavailable', async () => {
    delete process.env.BRICK_API_KEY;
    secretToolShouldFail = true;
    writeFileSync(`${CLONE_DIR}/bead-output.md`, 'some output');
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-nokey');
    expect(result.available).toBe(false);
    expect(result.error).toContain('BRICK_API_KEY not configured');
    secretToolShouldFail = false;
  });

  it('returns degraded mode on Brick 503', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        text: () => Promise.resolve('Service Unavailable'),
      }),
    );
    writeFileSync(`${CLONE_DIR}/bead-output.md`, 'some output');
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-503');
    expect(result.available).toBe(false);
    expect(result.error).toContain('503');
  });

  it('returns degraded mode on network error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('fetch failed')),
    );
    writeFileSync(`${CLONE_DIR}/bead-output.md`, 'some output');
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-net');
    expect(result.available).toBe(false);
    expect(result.error).toContain('fetch failed');
  });
});
