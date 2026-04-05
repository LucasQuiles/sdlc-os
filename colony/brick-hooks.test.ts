import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { preprocessForEvaluation, buildBrickEvalParams } from './brick-hooks.js';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';

const CLONE_DIR = '/tmp/colony-brick-test-clone';

describe('brick-hooks', () => {
  beforeEach(() => {
    mkdirSync(CLONE_DIR, { recursive: true });
  });

  afterEach(() => {
    rmSync(CLONE_DIR, { recursive: true, force: true });
  });

  it('returns available=true when bead-output.md exists', async () => {
    writeFileSync(
      `${CLONE_DIR}/bead-output.md`,
      '# Output\nTask completed successfully.\n<!-- BEAD_OUTPUT_COMPLETE -->',
    );
    const result = await preprocessForEvaluation(CLONE_DIR, 'B-test');
    expect(result.available).toBe(true);
    expect(result.summary).toContain('B-test');
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
});
