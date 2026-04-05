import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.js';
import { getEventsDb, closeEventsDb } from './events-db.js';
import { writeJournalEntry } from './conductor-journal.js';
import { createFinding } from './finding-ops.js';
import { getLedger, updateLedger, rehydrateStatePacket } from './state-ledger.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-state-ledger-test.db';

function cleanupDb(): void {
  for (const suffix of ['', '-wal', '-shm']) {
    try { unlinkSync(TEST_DB + suffix); } catch {}
  }
}

function seedWorkstream(id: string = 'ws-test-001'): void {
  createWorkstream({
    workstream_id: id,
    repo: '/home/q/LAB/TestRepo',
    branch: 'main',
    mission_id: 'mission-alpha',
  });
}

describe('state-ledger', () => {
  beforeEach(() => {
    cleanupDb();
    bootstrapColony(TEST_DB);
  });

  afterEach(() => {
    closeEventsDb();
    cleanupDb();
  });

  // Test 1: Create workstream -> getLedger returns row with defaults
  it('getLedger returns row with defaults after createWorkstream', () => {
    seedWorkstream();
    const ledger = getLedger('ws-test-001');
    expect(ledger).not.toBeNull();
    expect(ledger!.workstream_id).toBe('ws-test-001');
    expect(ledger!.repo).toBe('/home/q/LAB/TestRepo');
    expect(ledger!.branch).toBe('main');
    expect(ledger!.mission_id).toBe('mission-alpha');
    expect(ledger!.active_beads).toEqual({});
    expect(ledger!.changed_files).toEqual([]);
    expect(ledger!.hotspots).toEqual([]);
    expect(ledger!.linked_artifacts).toEqual([]);
    expect(ledger!.linked_findings).toEqual([]);
    expect(ledger!.decision_anchors).toEqual([]);
    expect(ledger!.unresolved).toEqual([]);
    expect(ledger!.provenance).toEqual({});
    expect(ledger!.vector_refs).toEqual([]);
  });

  // Test 2: updateLedger with active_beads -> getLedger shows update
  it('updateLedger with active_beads persists change', () => {
    seedWorkstream();
    updateLedger('ws-test-001', {
      active_beads: { 'bead-1': 'running', 'bead-2': 'pending' },
    });
    const ledger = getLedger('ws-test-001');
    expect(ledger).not.toBeNull();
    expect(ledger!.active_beads).toEqual({ 'bead-1': 'running', 'bead-2': 'pending' });
  });

  // Test 3: rehydrateStatePacket assembles ledger + journal + findings
  it('rehydrateStatePacket assembles full state packet', () => {
    seedWorkstream();

    // Add journal entries
    writeJournalEntry({
      entry_id: 'j-001',
      workstream_id: 'ws-test-001',
      session_type: 'planning',
      timestamp: new Date().toISOString(),
      structured: { decisions: [{ what: 'start feature X', why: 'priority', evidence: [] }] },
      narrative: 'Planned feature X implementation.',
    });

    // Add an open finding
    createFinding({
      workstream_id: 'ws-test-001',
      finding_type: 'in_scope',
      evidence: { description: 'Missing error handler' },
      confidence: 0.8,
    });

    const packet = rehydrateStatePacket('ws-test-001');
    expect(packet).not.toBeNull();
    expect(packet!.ledger.workstream_id).toBe('ws-test-001');
    expect(packet!.recentJournal).toHaveLength(1);
    expect(packet!.recentJournal[0].entry_id).toBe('j-001');
    expect(packet!.openFindings).toHaveLength(1);
    expect(packet!.openFindings[0].finding_type).toBe('in_scope');
    expect(packet!.rehydratedAt).toBeDefined();
    expect(typeof packet!.rehydratedAt).toBe('string');
  });

  // Test 4: rehydrateStatePacket returns null for nonexistent workstream
  it('rehydrateStatePacket returns null for nonexistent workstream', () => {
    const packet = rehydrateStatePacket('ws-nonexistent');
    expect(packet).toBeNull();
  });

  // Test 5: updateLedger with multiple fields in one call
  it('updateLedger updates multiple fields atomically', () => {
    seedWorkstream();
    updateLedger('ws-test-001', {
      active_beads: { 'bead-a': 'complete' },
      latest_commit: 'abc123def',
      diff_summary: '+10 -3 in src/main.ts',
      changed_files: ['src/main.ts', 'src/utils.ts'],
      hotspots: ['src/main.ts:42'],
      linked_findings: ['f-001', 'f-002'],
    });
    const ledger = getLedger('ws-test-001');
    expect(ledger).not.toBeNull();
    expect(ledger!.active_beads).toEqual({ 'bead-a': 'complete' });
    expect(ledger!.latest_commit).toBe('abc123def');
    expect(ledger!.diff_summary).toBe('+10 -3 in src/main.ts');
    expect(ledger!.changed_files).toEqual(['src/main.ts', 'src/utils.ts']);
    expect(ledger!.hotspots).toEqual(['src/main.ts:42']);
    expect(ledger!.linked_findings).toEqual(['f-001', 'f-002']);
  });

  // Additional edge cases
  it('getLedger returns null for nonexistent workstream', () => {
    const ledger = getLedger('ws-does-not-exist');
    expect(ledger).toBeNull();
  });

  it('updateLedger throws for nonexistent workstream', () => {
    expect(() => {
      updateLedger('ws-ghost', { latest_commit: 'abc' });
    }).toThrow(/not found/);
  });

  it('updateLedger with empty fields is a no-op', () => {
    seedWorkstream();
    const before = getLedger('ws-test-001');
    updateLedger('ws-test-001', {});
    const after = getLedger('ws-test-001');
    // Core fields unchanged (updated_at may differ only if there were set clauses)
    expect(after!.repo).toBe(before!.repo);
    expect(after!.active_beads).toEqual(before!.active_beads);
  });
});
