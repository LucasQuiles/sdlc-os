// colony/discovery.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

import { findAdjacentFiles, generateDiscoveryChecks } from './discovery.ts';

// ---------------------------------------------------------------------------
// Mock dependencies for runAdjacentDiscovery
// ---------------------------------------------------------------------------

vi.mock('./boundary-detector.js', () => ({
  classifyFinding: vi.fn((affectedScope: string, missionScope: string) => {
    if (affectedScope.includes(missionScope) || affectedScope.startsWith(missionScope)) {
      return { classification: 'in_scope', reason: 'in scope', shouldAutoPromote: true };
    }
    return { classification: 'adjacent', reason: 'adjacent', shouldAutoPromote: false };
  }),
}));

vi.mock('./finding-ops.js', () => {
  let counter = 0;
  return {
    createFinding: vi.fn(() => `f-mock-${++counter}`),
  };
});

// Import after mocks are set up
const { runAdjacentDiscovery } = await import('./discovery.ts');
const { classifyFinding } = await import('./boundary-detector.js');
const { createFinding } = await import('./finding-ops.js');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let tempDir: string;

beforeEach(() => {
  tempDir = mkdtempSync(join(tmpdir(), 'discovery-test-'));
  vi.clearAllMocks();
});

afterEach(() => {
  rmSync(tempDir, { recursive: true, force: true });
});

function writeFile(relPath: string, content: string): string {
  const absPath = join(tempDir, relPath);
  const dir = absPath.substring(0, absPath.lastIndexOf('/'));
  mkdirSync(dir, { recursive: true });
  writeFileSync(absPath, content, 'utf-8');
  return absPath;
}

// ---------------------------------------------------------------------------
// findAdjacentFiles
// ---------------------------------------------------------------------------

describe('findAdjacentFiles', () => {
  it('returns sibling source files in the same directory', () => {
    writeFile('src/foo.ts', 'export const foo = 1;');
    writeFile('src/bar.ts', 'export const bar = 2;');
    writeFile('src/baz.ts', 'export const baz = 3;');

    const result = findAdjacentFiles(['src/foo.ts'], tempDir);

    // bar.ts and baz.ts are siblings of foo.ts
    const names = result.map(f => f.split('/').pop());
    expect(names).toContain('bar.ts');
    expect(names).toContain('baz.ts');
    expect(names).not.toContain('foo.ts'); // touched file excluded
  });

  it('excludes non-source files', () => {
    writeFile('src/foo.ts', 'export const foo = 1;');
    writeFile('src/data.json', '{}');
    writeFile('src/README.md', '# readme');

    const result = findAdjacentFiles(['src/foo.ts'], tempDir);
    expect(result).toHaveLength(0);
  });

  it('excludes node_modules paths', () => {
    writeFile('node_modules/pkg/index.ts', 'export default 1;');
    writeFile('src/foo.ts', 'export const foo = 1;');

    // Touch a file whose sibling dir is node_modules — shouldn't traverse it
    const result = findAdjacentFiles(['src/foo.ts'], tempDir);
    const names = result.map(f => f.split('/').pop());
    expect(names).not.toContain('index.ts');
  });

  it('deduplicates when multiple touched files share a directory', () => {
    writeFile('src/a.ts', '');
    writeFile('src/b.ts', '');
    writeFile('src/c.ts', '');

    const result = findAdjacentFiles(['src/a.ts', 'src/b.ts'], tempDir);
    const names = result.map(f => f.split('/').pop());
    // c.ts should appear once, a.ts and b.ts are touched
    expect(names).toEqual(['c.ts']);
  });
});

// ---------------------------------------------------------------------------
// generateDiscoveryChecks
// ---------------------------------------------------------------------------

describe('generateDiscoveryChecks', () => {
  it('detects missing test file', () => {
    const absPath = writeFile('src/utils.ts', 'export function helper() {}');

    const checks = generateDiscoveryChecks([absPath], tempDir);
    const testChecks = checks.filter(c => c.checkType === 'missing_test');

    expect(testChecks).toHaveLength(1);
    expect(testChecks[0].confidence).toBe(0.75);
    expect(testChecks[0].description).toContain('no corresponding test');
  });

  it('does not flag missing test when sibling test exists', () => {
    const absPath = writeFile('src/utils.ts', 'export function helper() {}');
    writeFile('src/utils.test.ts', 'it("works", () => {})');

    const checks = generateDiscoveryChecks([absPath], tempDir);
    const testChecks = checks.filter(c => c.checkType === 'missing_test');

    expect(testChecks).toHaveLength(0);
  });

  it('detects "as any" casts', () => {
    const absPath = writeFile('src/loose.ts', [
      'const x = foo as any;',
      'const y = bar as any;',
      'export { x, y };',
    ].join('\n'));

    const checks = generateDiscoveryChecks([absPath], tempDir);
    const typeChecks = checks.filter(c => c.checkType === 'type_safety');

    expect(typeChecks).toHaveLength(1);
    expect(typeChecks[0].confidence).toBe(0.7);
    expect(typeChecks[0].description).toContain("2 'as any' casts");
  });

  it('detects unused imports', () => {
    const absPath = writeFile('src/consumer.ts', [
      "import { used, unused } from './lib';",
      '',
      'console.log(used);',
    ].join('\n'));

    const checks = generateDiscoveryChecks([absPath], tempDir);
    const importChecks = checks.filter(c => c.checkType === 'import_anomaly');

    expect(importChecks).toHaveLength(1);
    expect(importChecks[0].confidence).toBe(0.5);
    expect(importChecks[0].description).toContain('unused');
  });

  it('detects dead exports when no sibling imports the file', () => {
    const a = writeFile('src/orphan.ts', 'export function lonely() {}\nexport const alone = 1;');
    const b = writeFile('src/other.ts', "import { something } from './somewhere';");

    const checks = generateDiscoveryChecks([a, b], tempDir);
    const deadChecks = checks.filter(c => c.checkType === 'dead_export' && c.filePath === a);

    expect(deadChecks).toHaveLength(1);
    expect(deadChecks[0].description).toContain('lonely');
  });
});

// ---------------------------------------------------------------------------
// runAdjacentDiscovery
// ---------------------------------------------------------------------------

describe('runAdjacentDiscovery', () => {
  it('creates in-scope finding for discovered issue within mission scope', () => {
    // Set up: touched file + adjacent file with an issue, all within mission scope
    writeFile('src/runtimes/touched.ts', 'export const x = 1;');
    writeFile('src/runtimes/adjacent.ts', 'const y = foo as any;\nexport { y };');

    // classifyFinding mock: files under src/runtimes/ are in_scope
    vi.mocked(classifyFinding).mockReturnValue({
      classification: 'in_scope',
      reason: 'in scope',
      shouldAutoPromote: true,
    });

    const result = runAdjacentDiscovery(
      ['src/runtimes/touched.ts'],
      'src/runtimes/',
      'ws-1',
      tempDir,
    );

    expect(result.adjacentFiles.length).toBeGreaterThan(0);
    expect(result.checks.length).toBeGreaterThan(0);
    expect(result.findingsCreated.length).toBeGreaterThan(0);

    // Verify createFinding was called with in_scope type
    expect(createFinding).toHaveBeenCalledWith(
      expect.objectContaining({
        finding_type: 'in_scope',
        workstream_id: 'ws-1',
      }),
    );
  });

  it('creates exploratory finding for out-of-scope discovered issue', () => {
    writeFile('src/runtimes/touched.ts', 'export const x = 1;');
    writeFile('src/runtimes/adjacent.ts', 'const y = foo as any;\nexport { y };');

    // classifyFinding mock: files are adjacent (not in_scope)
    vi.mocked(classifyFinding).mockReturnValue({
      classification: 'adjacent',
      reason: 'adjacent to scope',
      shouldAutoPromote: false,
    });

    const result = runAdjacentDiscovery(
      ['src/runtimes/touched.ts'],
      'src/core/',
      'ws-2',
      tempDir,
    );

    expect(result.findingsCreated.length).toBeGreaterThan(0);

    // Verify createFinding was called with exploratory type
    expect(createFinding).toHaveBeenCalledWith(
      expect.objectContaining({
        finding_type: 'exploratory',
        workstream_id: 'ws-2',
      }),
    );
  });

  it('returns empty results when no adjacent files found', () => {
    writeFile('src/alone/only.ts', 'export const x = 1;');

    const result = runAdjacentDiscovery(
      ['src/alone/only.ts'],
      'src/',
      'ws-3',
      tempDir,
    );

    expect(result.adjacentFiles).toHaveLength(0);
    expect(result.checks).toHaveLength(0);
    expect(result.findingsCreated).toHaveLength(0);
  });
});
