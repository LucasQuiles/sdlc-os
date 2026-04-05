import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { openEventsDb, closeEventsDb, insertEvent, queryEvents, getEventsDb, ColonyDbError } from './events-db.js';
import type { TypedEvent } from './event-types.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-events-test.db';

function cleanupDb(): void {
  for (const suffix of ['', '-wal', '-shm']) {
    try { unlinkSync(TEST_DB + suffix); } catch {}
  }
}

describe('events-db', () => {
  beforeEach(() => {
    cleanupDb();
    openEventsDb(TEST_DB);
  });

  afterEach(() => {
    closeEventsDb();
    cleanupDb();
  });

  it('inserts and queries events by workstream', () => {
    const event: TypedEvent = {
      event_id: 'evt-001',
      event_type: 'bead_completed',
      workstream_id: 'ws-abc',
      bead_id: 'B01',
      timestamp: new Date().toISOString(),
      payload: { summary: 'task done' },
      processing_level: 'pending',
      idempotency_key: 'bead_completed:ws-abc:B01:test1',
    };
    insertEvent(event);
    const results = queryEvents('ws-abc');
    expect(results).toHaveLength(1);
    expect(results[0].event_type).toBe('bead_completed');
  });

  it('enforces idempotency — duplicate insert is a no-op', () => {
    const event: TypedEvent = {
      event_id: 'evt-002',
      event_type: 'bead_started',
      workstream_id: 'ws-abc',
      timestamp: new Date().toISOString(),
      payload: {},
      processing_level: 'pending',
      idempotency_key: 'bead_started:ws-abc:none:dup1',
    };
    insertEvent(event);
    // Second insert with same idempotency key — should not throw or duplicate
    const event2 = { ...event, event_id: 'evt-003' };
    insertEvent(event2);
    const results = queryEvents('ws-abc');
    expect(results).toHaveLength(1);
    expect(results[0].event_id).toBe('evt-002');
  });

  it('creates all required tables', () => {
    const db = getEventsDb();
    const tables = db.prepare(
      "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).all() as Array<{ name: string }>;
    const names = tables.map(t => t.name);
    expect(names).toContain('events');
    expect(names).toContain('findings');
    expect(names).toContain('state_ledger');
    expect(names).toContain('conductor_journal');
    expect(names).toContain('remediation_patterns');
    expect(names).toContain('schema_meta');
  });

  it('throws ColonyDbError when DB is not open', () => {
    closeEventsDb();
    expect(() => getEventsDb()).toThrow(ColonyDbError);
  });

  it('queries with event_type filter', () => {
    const base = {
      workstream_id: 'ws-filter',
      timestamp: new Date().toISOString(),
      payload: {},
      processing_level: 'pending' as const,
    };
    insertEvent({ ...base, event_id: 'e1', event_type: 'bead_started', idempotency_key: 'k1' });
    insertEvent({ ...base, event_id: 'e2', event_type: 'bead_completed', idempotency_key: 'k2' });
    insertEvent({ ...base, event_id: 'e3', event_type: 'bead_started', idempotency_key: 'k3' });

    const started = queryEvents('ws-filter', { event_type: 'bead_started' });
    expect(started).toHaveLength(2);

    const completed = queryEvents('ws-filter', { event_type: 'bead_completed' });
    expect(completed).toHaveLength(1);
  });

  it('queries with limit', () => {
    const base = {
      workstream_id: 'ws-limit',
      event_type: 'bead_started' as const,
      payload: {},
      processing_level: 'pending' as const,
    };
    for (let i = 0; i < 5; i++) {
      insertEvent({
        ...base,
        event_id: `e-${i}`,
        timestamp: new Date(Date.now() + i * 1000).toISOString(),
        idempotency_key: `k-${i}`,
      });
    }
    const limited = queryEvents('ws-limit', { limit: 2 });
    expect(limited).toHaveLength(2);
  });
});
