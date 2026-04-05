/**
 * Colony Phase 1 — Integration smoke test.
 *
 * Exercises the full core loop end-to-end:
 *   bootstrap -> schema -> seeds -> workstream -> event -> finding ->
 *   promotion -> journal -> cost enforcement -> idempotency -> error handling
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.js';
import {
  openEventsDb,
  closeEventsDb,
  getEventsDb,
  insertEvent,
  queryEvents,
  ColonyDbError,
} from './events-db.js';
import { createFinding, checkAutoPromotion, getFinding } from './finding-ops.js';
import { writeJournalEntry, readLatestJournal } from './conductor-journal.js';
import { CostEnforcer } from './cost-enforcer.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-integration-test.db';

function cleanupDb(): void {
  for (const ext of ['', '-wal', '-shm']) {
    try { unlinkSync(TEST_DB + ext); } catch { /* ignore */ }
  }
}

describe('Colony Phase 1 Integration', () => {
  beforeEach(() => {
    cleanupDb();
    bootstrapColony(TEST_DB);
  });

  afterEach(() => {
    closeEventsDb();
    cleanupDb();
  });

  // -----------------------------------------------------------------------
  // 1-2. Schema verification
  // -----------------------------------------------------------------------
  it('bootstrap creates all 6 required tables', () => {
    const db = getEventsDb();
    const tables = db
      .prepare(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
      )
      .all() as Array<{ name: string }>;
    const names = tables.map((t) => t.name).sort();
    expect(names).toEqual(
      expect.arrayContaining([
        'conductor_journal',
        'events',
        'findings',
        'remediation_patterns',
        'schema_meta',
        'state_ledger',
      ]),
    );
  });

  // -----------------------------------------------------------------------
  // 3. Seed patterns
  // -----------------------------------------------------------------------
  it('seeds at least 6 remediation patterns', () => {
    const db = getEventsDb();
    const patterns = db.prepare('SELECT * FROM remediation_patterns').all();
    expect(patterns.length).toBeGreaterThanOrEqual(6);
  });

  // -----------------------------------------------------------------------
  // 4-7. Full lifecycle
  // -----------------------------------------------------------------------
  it('full lifecycle: workstream -> event -> finding -> promotion -> journal', () => {
    // 4. Create workstream
    createWorkstream({
      workstream_id: 'int-ws',
      repo: '/home/q/LAB/WhatSoup',
      branch: 'main',
      mission_id: 'int-mission',
      scope_region: 'src/',
    });

    const db = getEventsDb();
    const ws = db
      .prepare('SELECT * FROM state_ledger WHERE workstream_id = ?')
      .get('int-ws') as Record<string, unknown> | undefined;
    expect(ws).toBeDefined();
    expect(ws!.repo).toBe('/home/q/LAB/WhatSoup');

    // 5. Insert event
    insertEvent({
      event_id: 'int-evt-001',
      event_type: 'bead_completed',
      workstream_id: 'int-ws',
      bead_id: 'B-int-01',
      timestamp: new Date().toISOString(),
      payload: { summary: 'integration bead done' },
      processing_level: 'pending',
      idempotency_key: 'bead_completed:int-ws:B-int-01:int',
    });

    const events = queryEvents('int-ws');
    expect(events).toHaveLength(1);
    expect(events[0].event_type).toBe('bead_completed');
    expect(events[0].payload).toEqual({ summary: 'integration bead done' });

    // 6. Create finding and auto-promote
    const fid = createFinding({
      workstream_id: 'int-ws',
      finding_type: 'in_scope',
      evidence: { observed: 'dead import', file_refs: ['src/foo.ts:10'] },
      confidence: 0.85,
      affected_scope: 'src/foo.ts',
    });
    expect(fid).toBeTruthy();

    const before = getFinding(fid);
    expect(before).not.toBeNull();
    expect(before!.promotion_state).toBe('open');

    const result = checkAutoPromotion(fid, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(true);

    const after = getFinding(fid);
    expect(after!.promotion_state).toBe('promoted');

    // 7. Write + read journal
    writeJournalEntry({
      entry_id: 'j-int-001',
      workstream_id: 'int-ws',
      session_type: 'EVALUATE',
      timestamp: new Date().toISOString(),
      structured: {
        beads_evaluated: ['B-int-01'],
        findings_promoted: [fid],
        decisions: [
          {
            what: 'Promoted dead-import finding',
            why: 'High confidence with file anchor',
            evidence: ['src/foo.ts:10'],
          },
        ],
      },
      narrative:
        'Evaluated B-int-01. Found and promoted dead import in src/foo.ts.',
    });

    const journal = readLatestJournal('int-ws');
    expect(journal).not.toBeNull();
    expect(journal!.entry_id).toBe('j-int-001');
    expect(journal!.session_type).toBe('EVALUATE');
    expect(journal!.structured.findings_promoted).toContain(fid);
    expect(journal!.narrative).toContain('dead import');
  });

  // -----------------------------------------------------------------------
  // 8. Cost enforcement phases
  // -----------------------------------------------------------------------
  it('cost enforcement: normal -> warning -> exceeded', () => {
    const enforcer = new CostEnforcer(50.0);

    // Normal phase
    enforcer.recordCost('ws', 30.0);
    const normal = enforcer.checkBudget('ws');
    expect(normal.phase).toBe('normal');
    expect(normal.allowed).toBe(true);
    expect(normal.discovery_disabled).toBe(false);

    // Warning phase (80%+)
    enforcer.recordCost('ws', 12.0); // total: 42
    const warning = enforcer.checkBudget('ws');
    expect(warning.phase).toBe('warning');
    expect(warning.allowed).toBe(true);
    expect(warning.discovery_disabled).toBe(true);

    // Exceeded phase (100%+)
    enforcer.recordCost('ws', 10.0); // total: 52
    const exceeded = enforcer.checkBudget('ws');
    expect(exceeded.phase).toBe('exceeded');
    expect(exceeded.allowed).toBe(false);
    expect(exceeded.discovery_disabled).toBe(true);
  });

  // -----------------------------------------------------------------------
  // 9. Idempotency
  // -----------------------------------------------------------------------
  it('duplicate event insert is a no-op (idempotency)', () => {
    insertEvent({
      event_id: 'dup-001',
      event_type: 'bead_started',
      workstream_id: 'int-ws',
      timestamp: new Date().toISOString(),
      payload: {},
      processing_level: 'pending',
      idempotency_key: 'unique-key-123',
    });

    // Second insert with same idempotency key — different event_id
    insertEvent({
      event_id: 'dup-002',
      event_type: 'bead_started',
      workstream_id: 'int-ws',
      timestamp: new Date().toISOString(),
      payload: {},
      processing_level: 'pending',
      idempotency_key: 'unique-key-123',
    });

    const events = queryEvents('int-ws');
    expect(events).toHaveLength(1);
    expect(events[0].event_id).toBe('dup-001');
  });

  // -----------------------------------------------------------------------
  // 10. Error handling — operations on closed DB throw ColonyDbError
  // -----------------------------------------------------------------------
  it('operations after closeEventsDb throw ColonyDbError', () => {
    closeEventsDb();

    expect(() => getEventsDb()).toThrow(ColonyDbError);
    expect(() =>
      insertEvent({
        event_id: 'fail-001',
        event_type: 'bead_started',
        workstream_id: 'int-ws',
        timestamp: new Date().toISOString(),
        payload: {},
        processing_level: 'pending',
        idempotency_key: 'fail-key',
      }),
    ).toThrow(ColonyDbError);
  });

  // -----------------------------------------------------------------------
  // Bonus: auto-promotion rejects findings that don't meet criteria
  // -----------------------------------------------------------------------
  it('auto-promotion rejects low-confidence finding', () => {
    const fid = createFinding({
      workstream_id: 'int-ws',
      finding_type: 'in_scope',
      evidence: { observed: 'maybe stale', file_refs: ['src/bar.ts:5'] },
      confidence: 0.5, // below 0.7 threshold
      affected_scope: 'src/bar.ts',
    });

    const result = checkAutoPromotion(fid, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('confidence');
    expect(getFinding(fid)!.promotion_state).toBe('open');
  });

  it('auto-promotion rejects out-of-scope finding', () => {
    const fid = createFinding({
      workstream_id: 'int-ws',
      finding_type: 'in_scope',
      evidence: { observed: 'issue', file_refs: ['lib/util.ts:1'] },
      confidence: 0.9,
      affected_scope: 'lib/util.ts',
    });

    const result = checkAutoPromotion(fid, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('outside mission');
  });

  it('bootstrap is idempotent — calling twice does not error or duplicate', () => {
    // bootstrapColony already called in beforeEach; call again
    // Note: openEventsDb is itself idempotent (returns early if already open)
    // So we close first and re-bootstrap to test full path
    closeEventsDb();
    bootstrapColony(TEST_DB);

    const db = getEventsDb();
    const patterns = db.prepare('SELECT * FROM remediation_patterns').all();
    expect(patterns.length).toBe(6); // exactly 6, not doubled
  });
});
