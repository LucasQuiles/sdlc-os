import { describe, it, expect } from 'vitest';
import { parseBeadFile, updateBeadField, appendCorrection } from './bead-parser.js';

const WELL_FORMED_BEAD = `# Bead: Add login form

**BeadID:** bead-001
**Status:** running
**LoopLevel:** L1
**WorkerType:** claude_code
**Phase:** execute
**CynefinDomain:** complicated
**Description:** Implement login form with email/password
**AcceptanceCriteria:** Form renders, validates, submits
**ScopeFiles:** src/login.ts, src/login.test.ts
**Output:** bead-output.md
**CorrectionHistory:** (none)
`;

const MINIMAL_BEAD = `# Bead: Quick fix

**BeadID:** bead-002
**Status:** submitted
`;

describe('parseBeadFile', () => {
  it('parses well-formed bead with all fields', () => {
    const fields = parseBeadFile(WELL_FORMED_BEAD);
    expect(fields.BeadID).toBe('bead-001');
    expect(fields.Status).toBe('running');
    expect(fields.LoopLevel).toBe('L1');
    expect(fields.WorkerType).toBe('claude_code');
    expect(fields.Phase).toBe('execute');
    expect(fields.CynefinDomain).toBe('complicated');
    expect(fields.Description).toBe('Implement login form with email/password');
    expect(fields.AcceptanceCriteria).toBe('Form renders, validates, submits');
    expect(fields.ScopeFiles).toEqual(['src/login.ts', 'src/login.test.ts']);
    expect(fields.Output).toBe('bead-output.md');
    expect(fields.CorrectionHistory).toBe('(none)');
  });

  it('parses minimal bead with defaults', () => {
    const fields = parseBeadFile(MINIMAL_BEAD);
    expect(fields.BeadID).toBe('bead-002');
    expect(fields.Status).toBe('submitted');
    expect(fields.LoopLevel).toBe('L0');
    expect(fields.WorkerType).toBe('codex');
    expect(fields.Phase).toBe('execute');
    expect(fields.CynefinDomain).toBe('complicated');
    expect(fields.Description).toBe('');
    expect(fields.AcceptanceCriteria).toBe('');
    expect(fields.ScopeFiles).toEqual([]);
    expect(fields.Output).toBe('');
    expect(fields.CorrectionHistory).toBe('');
  });

  it('throws on missing BeadID', () => {
    const content = `**Status:** running\n`;
    expect(() => parseBeadFile(content)).toThrow('Missing required field: BeadID');
  });

  it('throws on missing Status', () => {
    const content = `**BeadID:** bead-003\n`;
    expect(() => parseBeadFile(content)).toThrow('Missing required field: Status');
  });
});

describe('updateBeadField', () => {
  it('replaces existing field value', () => {
    const result = updateBeadField(WELL_FORMED_BEAD, 'Status', 'submitted');
    expect(result).toContain('**Status:** submitted');
    expect(result).not.toContain('**Status:** running');
  });

  it('appends field if not present', () => {
    const result = updateBeadField(MINIMAL_BEAD, 'Description', 'A new description');
    expect(result).toContain('**Description:** A new description');
  });
});

describe('appendCorrection', () => {
  it('replaces (none) placeholder with first correction', () => {
    const result = appendCorrection(WELL_FORMED_BEAD, 'L0', 1, 'Tests failed: missing import');
    expect(result).toContain('- [L0 cycle 1] Tests failed: missing import');
    expect(result).not.toContain('(none)');
  });

  it('appends to existing corrections', () => {
    const content = `**BeadID:** bead-001
**Status:** running
**CorrectionHistory:**
- [L0 cycle 1] First finding
`;
    const result = appendCorrection(content, 'L1', 2, 'Second finding');
    expect(result).toContain('- [L0 cycle 1] First finding');
    expect(result).toContain('- [L1 cycle 2] Second finding');
    // Second should come after first
    const firstIdx = result.indexOf('- [L0 cycle 1]');
    const secondIdx = result.indexOf('- [L1 cycle 2]');
    expect(secondIdx).toBeGreaterThan(firstIdx);
  });

  it('adds CorrectionHistory field if missing', () => {
    const result = appendCorrection(MINIMAL_BEAD, 'L0', 1, 'New correction');
    expect(result).toContain('- [L0 cycle 1] New correction');
  });
});
