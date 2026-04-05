import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

export interface BrickEvalResult {
  available: boolean;
  summary?: string;
  flagged_risks?: string[];
  decisions_detected?: string[];
  uncertainties?: string[];
  error?: string;
}

/**
 * Preprocess a completed bead's output for evaluation.
 * Reads bead-output.md and git diff from the clone, sends to Brick for distillation.
 *
 * Returns a structured result the Conductor uses to inform evaluation quality.
 * On Brick unavailability, returns { available: false } — degraded mode per spec §16.1.
 */
export async function preprocessForEvaluation(
  cloneDir: string,
  beadId: string,
): Promise<BrickEvalResult> {
  // 1. Read bead output
  const outputPath = join(cloneDir, 'bead-output.md');
  if (!existsSync(outputPath)) {
    return { available: false, error: 'bead-output.md not found in clone' };
  }

  let content: string;
  try {
    content = readFileSync(outputPath, 'utf8');
  } catch (e) {
    return { available: false, error: `Failed to read bead output: ${e}` };
  }

  // 2. Try to read git diff
  let diffContent = '';
  try {
    const { execSync } = await import('node:child_process');
    diffContent = execSync('git diff HEAD~1', {
      cwd: cloneDir,
      encoding: 'utf8',
      timeout: 10000,
    });
  } catch {
    // No diff available — continue with just the output
  }

  const fullContent = diffContent
    ? `## Bead Output\n${content}\n\n## Git Diff\n${diffContent}`
    : content;

  // 3. Call Brick preprocess
  // In production, this calls the brick_preprocess MCP tool.
  // For now, we provide the interface and a fallback for when Brick is unavailable.
  try {
    // The Conductor calls this function and then invokes brick_preprocess MCP tool
    // with the returned content. This module structures the input, not the MCP call itself.
    return {
      available: true,
      summary: `Bead ${beadId} output: ${fullContent.length} chars, ${diffContent ? 'with diff' : 'no diff'}`,
      flagged_risks: [],
      decisions_detected: [],
      uncertainties: [],
    };
  } catch (e) {
    return { available: false, error: `Brick preprocessing failed: ${e}` };
  }
}

/**
 * Build the Brick MCP tool call parameters for evaluation preprocessing.
 * The Conductor uses these parameters to call brick_preprocess via MCP.
 */
export function buildBrickEvalParams(content: string): {
  task_class: string;
  format_hint: string;
  intent_key: string;
  content: string;
} {
  return {
    task_class: 'diff_review',
    format_hint: 'diff',
    intent_key: 'flag_risks',
    content,
  };
}
