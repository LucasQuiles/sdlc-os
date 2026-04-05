// sdlc-os/colony/boundary-detector.test.ts
import { describe, it, expect } from 'vitest';
import { classifyFinding } from './boundary-detector.ts';

describe('classifyFinding', () => {
  it('classifies in-scope file correctly', () => {
    const result = classifyFinding('src/runtimes/agent/session.ts', 'src/runtimes/');
    expect(result.classification).toBe('in_scope');
    expect(result.shouldAutoPromote).toBe(true);
  });

  it('classifies adjacent file (shared parent) correctly', () => {
    const result = classifyFinding('src/core/database.ts', 'src/runtimes/');
    expect(result.classification).toBe('adjacent');
    expect(result.reason).toContain('src');
    expect(result.shouldAutoPromote).toBe(false);
  });

  it('classifies boundary crossing (different tree) correctly', () => {
    const result = classifyFinding('console/src/pages/Ops.tsx', 'src/runtimes/');
    expect(result.classification).toBe('boundary_crossing');
    expect(result.shouldAutoPromote).toBe(false);
  });

  it('classifies novel (no scope) correctly', () => {
    const result = classifyFinding(undefined, 'src/runtimes/');
    expect(result.classification).toBe('novel');
    expect(result.shouldAutoPromote).toBe(false);
  });

  it('classifies novel (pattern not in known set) correctly', () => {
    const known = new Set(['src/runtimes/agent/session.ts', 'src/runtimes/worker/pool.ts']);
    const result = classifyFinding('src/runtimes/agent/unknown.ts', 'src/runtimes/', known);
    expect(result.classification).toBe('novel');
    expect(result.reason).toContain('not in known patterns');
    expect(result.shouldAutoPromote).toBe(false);
  });

  it('shouldAutoPromote is true only for in_scope', () => {
    const inScope = classifyFinding('src/runtimes/agent/session.ts', 'src/runtimes/');
    const adjacent = classifyFinding('src/core/database.ts', 'src/runtimes/');
    const crossing = classifyFinding('console/src/pages/Ops.tsx', 'src/runtimes/');
    const novel = classifyFinding(undefined, 'src/runtimes/');

    expect(inScope.shouldAutoPromote).toBe(true);
    expect(adjacent.shouldAutoPromote).toBe(false);
    expect(crossing.shouldAutoPromote).toBe(false);
    expect(novel.shouldAutoPromote).toBe(false);
  });

  it('handles empty string affectedScope as novel', () => {
    const result = classifyFinding('', 'src/runtimes/');
    expect(result.classification).toBe('novel');
  });

  it('handles missionScope without trailing slash', () => {
    const result = classifyFinding('src/runtimes/agent/session.ts', 'src/runtimes');
    expect(result.classification).toBe('in_scope');
    expect(result.shouldAutoPromote).toBe(true);
  });
});
