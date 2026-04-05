// colony/discovery.ts — Completion-triggered adjacency discovery engine.
//
// After a bead completes, this module inspects adjacent files (siblings in the
// same directories as the touched files) and generates discovery checks that
// may become findings.

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, basename, join, extname, resolve } from 'node:path';
import { classifyFinding } from './boundary-detector.js';
import { createFinding } from './finding-ops.js';
import type { FindingType } from './event-types.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DiscoveryCheck {
  checkType: 'dead_export' | 'missing_test' | 'type_safety' | 'import_anomaly';
  filePath: string;
  description: string;
  confidence: number;
}

export interface DiscoveryResult {
  adjacentFiles: string[];
  checks: DiscoveryCheck[];
  findingsCreated: string[]; // finding IDs
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SOURCE_EXTENSIONS = new Set(['.ts', '.js', '.tsx', '.jsx', '.py']);
const EXCLUDED_DIRS = new Set(['node_modules', 'dist', '.git']);

const CHECK_CONFIDENCE: Record<DiscoveryCheck['checkType'], number> = {
  dead_export: 0.6,
  missing_test: 0.75,
  type_safety: 0.7,
  import_anomaly: 0.5,
};

// ---------------------------------------------------------------------------
// findAdjacentFiles
// ---------------------------------------------------------------------------

/**
 * Given files a bead touched, identify adjacent source files in the same
 * directories. Returns a deduplicated list excluding the touched files
 * themselves.
 */
export function findAdjacentFiles(touchedFiles: string[], projectDir: string): string[] {
  const touchedSet = new Set(touchedFiles.map(f => resolve(projectDir, f)));
  const seen = new Set<string>();
  const result: string[] = [];

  for (const file of touchedFiles) {
    const absFile = resolve(projectDir, file);
    const dir = dirname(absFile);

    // Skip if the directory itself is excluded
    if (isExcludedPath(dir)) continue;

    let entries: string[];
    try {
      entries = readdirSync(dir, { withFileTypes: true })
        .filter(e => e.isFile())
        .map(e => e.name);
    } catch {
      continue; // directory may not exist in tests
    }

    for (const entry of entries) {
      const ext = extname(entry);
      if (!SOURCE_EXTENSIONS.has(ext)) continue;

      const absEntry = join(dir, entry);
      if (touchedSet.has(absEntry)) continue;
      if (seen.has(absEntry)) continue;
      if (isExcludedPath(absEntry)) continue;

      seen.add(absEntry);
      result.push(absEntry);
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// generateDiscoveryChecks
// ---------------------------------------------------------------------------

/**
 * Generate discovery checks for a set of files. Each check is a potential
 * finding candidate with a confidence score.
 */
export function generateDiscoveryChecks(files: string[], projectDir: string): DiscoveryCheck[] {
  const checks: DiscoveryCheck[] = [];

  for (const filePath of files) {
    let content: string;
    try {
      content = readFileSync(filePath, 'utf-8');
    } catch {
      continue;
    }

    // --- missing_test ---
    if (isMissingTest(filePath, projectDir)) {
      checks.push({
        checkType: 'missing_test',
        filePath,
        description: `Source file has no corresponding test file`,
        confidence: CHECK_CONFIDENCE.missing_test,
      });
    }

    // --- type_safety: 'as any' casts ---
    if (content.includes('as any')) {
      const count = content.split('as any').length - 1;
      checks.push({
        checkType: 'type_safety',
        filePath,
        description: `File contains ${count} 'as any' cast${count > 1 ? 's' : ''}`,
        confidence: CHECK_CONFIDENCE.type_safety,
      });
    }

    // --- import_anomaly: unused imports ---
    const unusedImports = findUnusedImports(content);
    if (unusedImports.length > 0) {
      checks.push({
        checkType: 'import_anomaly',
        filePath,
        description: `Potentially unused imports: ${unusedImports.join(', ')}`,
        confidence: CHECK_CONFIDENCE.import_anomaly,
      });
    }

    // --- dead_export: exported names not imported elsewhere ---
    const deadExports = findDeadExports(filePath, files);
    if (deadExports.length > 0) {
      checks.push({
        checkType: 'dead_export',
        filePath,
        description: `Potentially dead exports: ${deadExports.join(', ')}`,
        confidence: CHECK_CONFIDENCE.dead_export,
      });
    }
  }

  return checks;
}

// ---------------------------------------------------------------------------
// runAdjacentDiscovery
// ---------------------------------------------------------------------------

/**
 * Run adjacency discovery after a bead completes:
 * 1. Find adjacent files from the bead's changed files
 * 2. Generate checks on adjacent files
 * 3. Classify each via BoundaryDetector
 * 4. Create findings for in-scope items, exploratory findings for others
 */
export function runAdjacentDiscovery(
  touchedFiles: string[],
  missionScope: string,
  workstreamId: string,
  projectDir: string,
): DiscoveryResult {
  const adjacentFiles = findAdjacentFiles(touchedFiles, projectDir);
  const checks = generateDiscoveryChecks(adjacentFiles, projectDir);
  const findingsCreated: string[] = [];

  for (const check of checks) {
    // Classify relative to mission scope
    const classification = classifyFinding(check.filePath, missionScope);

    // Map boundary classification to finding type
    let findingType: FindingType;
    if (classification.classification === 'in_scope') {
      findingType = 'in_scope';
    } else if (classification.classification === 'boundary_crossing') {
      findingType = 'boundary_crossing';
    } else {
      findingType = 'exploratory';
    }

    const findingId = createFinding({
      workstream_id: workstreamId,
      finding_type: findingType,
      evidence: {
        check_type: check.checkType,
        file_refs: [check.filePath],
        description: check.description,
        discovery_source: 'adjacency_engine',
      },
      confidence: check.confidence,
      affected_scope: check.filePath,
      suggested_actions: [suggestedAction(check)],
    });

    findingsCreated.push(findingId);
  }

  return { adjacentFiles, checks, findingsCreated };
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function isExcludedPath(filePath: string): boolean {
  const parts = filePath.split('/');
  return parts.some(p => EXCLUDED_DIRS.has(p));
}

/**
 * Check if a source file is missing a corresponding test file.
 * Looks for: sibling `foo.test.ts`, or `tests/foo.test.ts` relative to project dir.
 */
function isMissingTest(filePath: string, projectDir: string): boolean {
  const ext = extname(filePath);
  const base = basename(filePath, ext);

  // Skip if this is already a test file
  if (base.endsWith('.test') || base.endsWith('.spec')) return false;

  // Check sibling test file
  const dir = dirname(filePath);
  const siblingTest = join(dir, `${base}.test${ext}`);
  if (existsSync(siblingTest)) return false;

  // Check tests/ directory relative to project dir
  const relPath = filePath.startsWith(projectDir)
    ? filePath.slice(projectDir.length).replace(/^\//, '')
    : filePath;
  const testsDir = join(projectDir, 'tests', `${basename(relPath, ext)}.test${ext}`);
  if (existsSync(testsDir)) return false;

  return true;
}

/**
 * Find import identifiers that don't appear in the rest of the file body.
 * Simplified heuristic: extract named imports and check if they appear
 * outside the import statement.
 */
function findUnusedImports(content: string): string[] {
  const lines = content.split('\n');
  const importPattern = /import\s+\{([^}]+)\}/g;
  const unused: string[] = [];

  // Collect all import lines and the body (everything after imports)
  const importLines: string[] = [];
  const bodyLines: string[] = [];
  let pastImports = false;

  for (const line of lines) {
    if (!pastImports && (line.trim().startsWith('import ') || line.trim() === '')) {
      importLines.push(line);
    } else {
      pastImports = true;
      bodyLines.push(line);
    }
  }

  const body = bodyLines.join('\n');

  // Extract named imports
  const fullImportBlock = importLines.join('\n');
  let match: RegExpExecArray | null;
  while ((match = importPattern.exec(fullImportBlock)) !== null) {
    const names = match[1].split(',').map(n => {
      // Handle "Foo as Bar" — use the local alias
      const parts = n.trim().split(/\s+as\s+/);
      return parts[parts.length - 1].trim();
    }).filter(Boolean);

    for (const name of names) {
      // Check if the identifier appears in the body (word boundary check)
      const wordPattern = new RegExp(`\\b${escapeRegex(name)}\\b`);
      if (!wordPattern.test(body)) {
        unused.push(name);
      }
    }
  }

  return unused;
}

/**
 * Simplified dead export detection: check if the file's stem appears in
 * import statements of sibling files. If no sibling imports the file,
 * all its exports are considered potentially dead.
 */
function findDeadExports(filePath: string, siblingFiles: string[]): string[] {
  const ext = extname(filePath);
  const stem = basename(filePath, ext);

  // Check if any sibling file references this file's stem
  for (const sibling of siblingFiles) {
    if (sibling === filePath) continue;
    try {
      const sibContent = readFileSync(sibling, 'utf-8');
      // Look for import from './stem' or '../stem' etc.
      if (sibContent.includes(stem)) return [];
    } catch {
      continue;
    }
  }

  // If no sibling references it, extract exported names
  let content: string;
  try {
    content = readFileSync(filePath, 'utf-8');
  } catch {
    return [];
  }

  const exportPattern = /export\s+(?:function|const|class|type|interface|enum)\s+(\w+)/g;
  const exports: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = exportPattern.exec(content)) !== null) {
    exports.push(match[1]);
  }

  return exports;
}

function suggestedAction(check: DiscoveryCheck): string {
  switch (check.checkType) {
    case 'dead_export':
      return `Review exports in ${basename(check.filePath)} — may be unused`;
    case 'missing_test':
      return `Add test coverage for ${basename(check.filePath)}`;
    case 'type_safety':
      return `Replace 'as any' casts in ${basename(check.filePath)} with proper types`;
    case 'import_anomaly':
      return `Clean up unused imports in ${basename(check.filePath)}`;
  }
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
