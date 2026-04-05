import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.ts';
import { closeEventsDb, getEventsDb } from './events-db.ts';
import {
  createFinding, getFinding, promoteFinding, suppressFinding,
  deferFinding, checkAutoPromotion, archiveStaleFindings,
  getOpenFindings, resurfaceFinding,
} from './finding-ops.ts';
import { unlinkSync } from 'node:fs';

const TEST_DB = '/tmp/colony-findings-test.db';

describe('finding-ops', () => {
  beforeEach(() => {
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
    bootstrapColony(TEST_DB);
  });

  afterEach(() => {
    closeEventsDb();
    try { unlinkSync(TEST_DB); } catch {}
  });

  // -------------------------------------------------------------------------
  // Core CRUD
  // -------------------------------------------------------------------------

  it('creates a finding with evidence', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'import anomaly in utils.ts', file_refs: ['src/utils.ts:42'] },
      confidence: 0.8,
      affected_scope: 'src/utils.ts',
    });
    const f = getFinding(id);
    expect(f).toBeDefined();
    expect(f!.finding_type).toBe('in_scope');
    expect(f!.confidence).toBe(0.8);
    expect(f!.promotion_state).toBe('open');
  });

  // -------------------------------------------------------------------------
  // Auto-promotion policy
  // -------------------------------------------------------------------------

  it('auto-promotes in-scope finding with high confidence and file anchor', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'dead export', file_refs: ['src/foo.ts:10'] },
      confidence: 0.8,
      affected_scope: 'src/foo.ts',
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(true);
    const f = getFinding(id);
    expect(f!.promotion_state).toBe('promoted');
  });

  it('does NOT auto-promote exploratory finding', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'exploratory',
      evidence: { observed: 'database inconsistency' },
      confidence: 0.9,
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('not in_scope');
  });

  it('does NOT auto-promote low-confidence finding', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'maybe a problem' },
      confidence: 0.4,
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('confidence below');
  });

  // -------------------------------------------------------------------------
  // State transitions
  // -------------------------------------------------------------------------

  it('suppresses finding with reason', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: {},
      confidence: 0.2,
    });
    suppressFinding(id, 'below confidence threshold');
    const f = getFinding(id);
    expect(f!.promotion_state).toBe('suppressed');
    expect(f!.suppression_reason).toBe('below confidence threshold');
  });

  it('archives findings below salience threshold', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: {},
      confidence: 0.5,
    });
    // Manually set salience below threshold
    getEventsDb().prepare('UPDATE findings SET salience = 0.01 WHERE finding_id = ?').run(id);

    const archived = archiveStaleFindings('ws-001');
    expect(archived).toBeGreaterThanOrEqual(1);
    const f = getFinding(id);
    expect(f!.promotion_state).toBe('archived');
  });

  it('respects 100-finding cap per workstream', () => {
    for (let i = 0; i < 105; i++) {
      createFinding({
        workstream_id: 'ws-full',
        finding_type: 'in_scope',
        evidence: { idx: i },
        confidence: 0.5 + (i * 0.001),
      });
    }
    const open = getOpenFindings('ws-full');
    expect(open.length).toBeLessThanOrEqual(100);
  });

  // -------------------------------------------------------------------------
  // G8 edge case tests
  // -------------------------------------------------------------------------

  it('resurfaces suppressed findings with new evidence', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'original issue' },
      confidence: 0.6,
    });
    suppressFinding(id, 'insufficient evidence');
    const suppressed = getFinding(id);
    expect(suppressed!.promotion_state).toBe('suppressed');

    resurfaceFinding(id, { new_observed: 'confirmed in production logs' });
    const resurfaced = getFinding(id);
    expect(resurfaced!.promotion_state).toBe('open');
    expect(resurfaced!.suppression_reason).toBeNull();
    expect(resurfaced!.evidence).toHaveProperty('new_observed');
    expect(resurfaced!.evidence).toHaveProperty('resurfaced_at');
  });

  it('deferFinding sets salience to 0.1', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'low priority' },
      confidence: 0.5,
    });
    deferFinding(id, 'not urgent');
    const f = getFinding(id);
    expect(f!.promotion_state).toBe('deferred');
    expect(f!.salience).toBe(0.1);
  });

  it('creates and retrieves duplicate_candidate with related_findings', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'duplicate_candidate',
      evidence: { observed: 'looks like f-other-id' },
      confidence: 0.7,
      related_findings: ['f-other-id'],
    });
    const f = getFinding(id);
    expect(f).toBeDefined();
    expect(f!.finding_type).toBe('duplicate_candidate');
    expect(f!.related_findings).toEqual(['f-other-id']);
  });

  it('archives findings past 30-day hard TTL regardless of salience', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'old finding' },
      confidence: 0.9,
    });
    // Set updated_at to 31 days ago via direct DB update
    const thirtyOneDaysAgo = new Date(Date.now() - 31 * 24 * 60 * 60 * 1000).toISOString();
    getEventsDb().prepare('UPDATE findings SET updated_at = ? WHERE finding_id = ?').run(thirtyOneDaysAgo, id);

    const archived = archiveStaleFindings('ws-001');
    expect(archived).toBeGreaterThanOrEqual(1);
    const f = getFinding(id);
    expect(f!.promotion_state).toBe('archived');
  });

  it('machine adjudication zone: confidence 0.5 in_scope does not auto-promote', () => {
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'ambiguous signal', file_refs: ['src/a.ts:1'] },
      confidence: 0.5,
      affected_scope: 'src/a.ts',
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('confidence below');
  });

  // -------------------------------------------------------------------------
  // Remediation pattern matching (spec §14.1)
  // -------------------------------------------------------------------------

  it('pattern match: evidence matching seed pattern promotes finding', () => {
    // Evidence with "dead" and "export" should match 'dead-code-removal' seed pattern
    // ("Remove unused export/function" — keywords: remove, unused, export/function)
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'dead unused export in utils.ts', file_refs: ['src/utils.ts:10'] },
      confidence: 0.8,
      affected_scope: 'src/utils.ts',
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(true);
  });

  it('no pattern match, cold-start (<10 workstreams): still promoted with relaxation', () => {
    // Evidence that does NOT match any seed pattern keywords
    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'completely novel xyz qqq issue', file_refs: ['src/novel.ts:1'] },
      confidence: 0.8,
      affected_scope: 'src/novel.ts',
    });
    // No workstreams in state_ledger = cold-start, so relaxation allows promotion
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(true);
  });

  it('no pattern match, mature system (>10 workstreams): NOT promoted', () => {
    // Create >10 workstreams to exit cold-start
    for (let i = 0; i < 11; i++) {
      createWorkstream({
        workstream_id: `ws-mature-${i}`,
        repo: 'test-repo',
        branch: 'main',
        mission_id: 'm-001',
      });
    }

    const id = createFinding({
      workstream_id: 'ws-mature-0',
      finding_type: 'in_scope',
      evidence: { observed: 'completely novel xyz qqq issue', file_refs: ['src/novel.ts:1'] },
      confidence: 0.8,
      affected_scope: 'src/novel.ts',
    });
    const result = checkAutoPromotion(id, { active_mission_scope: 'src/' });
    expect(result.promoted).toBe(false);
    expect(result.reason).toContain('no matching remediation pattern');
  });

  it('pattern usage_count incremented on match', () => {
    const db = getEventsDb();
    const before = db.prepare("SELECT usage_count FROM remediation_patterns WHERE pattern_id = 'dead-code-removal'").get() as { usage_count: number };
    expect(before.usage_count).toBe(0);

    const id = createFinding({
      workstream_id: 'ws-001',
      finding_type: 'in_scope',
      evidence: { observed: 'remove unused export leftover', file_refs: ['src/foo.ts:5'] },
      confidence: 0.8,
      affected_scope: 'src/foo.ts',
    });
    checkAutoPromotion(id, { active_mission_scope: 'src/' });

    const after = db.prepare("SELECT usage_count FROM remediation_patterns WHERE pattern_id = 'dead-code-removal'").get() as { usage_count: number };
    expect(after.usage_count).toBe(1);
  });
});
