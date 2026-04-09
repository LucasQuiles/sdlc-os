import { readFileSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { join } from 'node:path';

const BRICK_BASE_URL = 'https://brick.tail64ad01.ts.net:8443';
const BRICK_TIMEOUT_MS = 30_000;

export interface BrickEvalResult {
  available: boolean;
  summary?: string;
  flagged_risks?: string[];
  decisions_detected?: string[];
  uncertainties?: string[];
  error?: string;
}

function getBrickApiKey(): string | undefined {
  if (process.env.BRICK_API_KEY) return process.env.BRICK_API_KEY;
  try {
    return execSync('secret-tool lookup service brick-api-key', {
      encoding: 'utf8',
      timeout: 5000,
    }).trim();
  } catch {
    return undefined;
  }
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
  const outputPath = join(cloneDir, 'bead-output.md');
  if (!existsSync(outputPath)) {
    return { available: false, error: 'bead-output.md not found in clone' };
  }

  // Fail fast if API key is missing — avoids wasted file I/O
  const apiKey = getBrickApiKey();
  if (!apiKey) {
    return { available: false, error: 'BRICK_API_KEY not configured' };
  }

  let content: string;
  try {
    content = readFileSync(outputPath, 'utf8');
  } catch (e) {
    return { available: false, error: `Failed to read bead output: ${e}` };
  }

  let diffContent = '';
  try {
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

  const params = buildBrickEvalParams(fullContent);
  try {
    const response = await fetch(`${BRICK_BASE_URL}/enrich/v1/preprocess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        ...params,
        tree_depth: 2,
      }),
      signal: AbortSignal.timeout(BRICK_TIMEOUT_MS),
    });

    if (response.status === 503) {
      return { available: false, error: 'Brick service unavailable (503)' };
    }

    if (!response.ok) {
      return {
        available: false,
        error: `Brick returned HTTP ${response.status}: ${await response.text().catch(() => 'unknown')}`,
      };
    }

    const data = await response.json();

    // Brick API v1 returns fields at top level; v2 nests them under tree_manifest
    return {
      available: true,
      summary: data.summary ?? data.tree_manifest?.summary ?? `Bead ${beadId} preprocessed`,
      flagged_risks: data.flagged_risks ?? data.tree_manifest?.flagged_risks ?? [],
      decisions_detected: data.decisions_detected ?? data.tree_manifest?.decisions_detected ?? [],
      uncertainties: data.uncertainties ?? data.tree_manifest?.uncertainties ?? [],
    };
  } catch (e) {
    // Network errors, timeouts — degrade gracefully
    const message = e instanceof Error ? e.message : String(e);
    return { available: false, error: `Brick preprocessing failed: ${message}` };
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
