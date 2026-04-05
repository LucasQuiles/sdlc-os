import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.js';
import { getEventsDb, closeEventsDb } from './events-db.js';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-bootstrap-test.db';

function cleanupDb(): void {
  for (const suffix of ['', '-wal', '-shm']) {
    try { unlinkSync(TEST_DB + suffix); } catch {}
  }
}

describe('bootstrap', () => {
  beforeEach(() => {
    cleanupDb();
  });

  afterEach(() => {
    closeEventsDb();
    cleanupDb();
  });

  it('seeds remediation patterns on first boot', () => {
    bootstrapColony(TEST_DB);
    const db = getEventsDb();
    const patterns = db.prepare('SELECT * FROM remediation_patterns').all() as Array<Record<string, unknown>>;
    expect(patterns.length).toBeGreaterThanOrEqual(6);
    expect(patterns.some(p => p.pattern_id === 'lint-fix')).toBe(true);
  });

  it('is idempotent — second call does not duplicate patterns', () => {
    bootstrapColony(TEST_DB);
    closeEventsDb();
    bootstrapColony(TEST_DB);
    const db = getEventsDb();
    const patterns = db.prepare('SELECT * FROM remediation_patterns').all();
    expect(patterns).toHaveLength(6);
  });

  it('creates a minimal workstream state ledger row', () => {
    bootstrapColony(TEST_DB);
    createWorkstream({
      workstream_id: 'ws-test-001',
      repo: '/home/q/LAB/WhatSoup',
      branch: 'main',
      mission_id: 'test-mission',
    });
    const db = getEventsDb();
    const row = db.prepare('SELECT * FROM state_ledger WHERE workstream_id = ?').get('ws-test-001') as Record<string, unknown>;
    expect(row).toBeDefined();
    expect(row.repo).toBe('/home/q/LAB/WhatSoup');
    expect(row.active_beads).toBe('{}');
  });

  it('createWorkstream is idempotent', () => {
    bootstrapColony(TEST_DB);
    createWorkstream({
      workstream_id: 'ws-dup',
      repo: '/repo',
      branch: 'main',
      mission_id: 'mission-1',
    });
    // Second call should not throw
    createWorkstream({
      workstream_id: 'ws-dup',
      repo: '/repo',
      branch: 'main',
      mission_id: 'mission-1',
    });
    const db = getEventsDb();
    const rows = db.prepare('SELECT * FROM state_ledger WHERE workstream_id = ?').all('ws-dup');
    expect(rows).toHaveLength(1);
  });

  it('creates workstream with optional scope_region', () => {
    bootstrapColony(TEST_DB);
    createWorkstream({
      workstream_id: 'ws-scoped',
      repo: '/repo',
      branch: 'feat/x',
      mission_id: 'mission-2',
      scope_region: 'src/utils/',
    });
    const db = getEventsDb();
    const row = db.prepare('SELECT * FROM state_ledger WHERE workstream_id = ?').get('ws-scoped') as Record<string, unknown>;
    expect(row.scope_region).toBe('src/utils/');
  });
});
