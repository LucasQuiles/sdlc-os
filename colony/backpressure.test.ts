import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.ts';
import { closeEventsDb, getEventsDb, insertEvent } from './events-db.ts';
import { createFinding } from './finding-ops.ts';
import { evaluateBackpressure } from './backpressure.ts';
import { unlinkSync } from 'node:fs';
import type { TypedEvent } from './event-types.ts';

const TEST_DB = '/tmp/colony-backpressure-test.db';
const WS = 'ws-bp-test';

function makeEvent(overrides: Partial<TypedEvent> & Pick<TypedEvent, 'event_type'>): TypedEvent {
  const id = `evt-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  return {
    event_id: id,
    event_type: overrides.event_type,
    workstream_id: overrides.workstream_id ?? WS,
    bead_id: overrides.bead_id,
    agent_id: overrides.agent_id,
    timestamp: overrides.timestamp ?? new Date().toISOString(),
    payload: overrides.payload ?? {},
    processing_level: overrides.processing_level ?? 'logged',
    idempotency_key: overrides.idempotency_key ?? id,
  };
}

describe('backpressure control loop', () => {
  beforeEach(() => {
    try { unlinkSync(TEST_DB); } catch {}
    try { unlinkSync(TEST_DB + '-wal'); } catch {}
    try { unlinkSync(TEST_DB + '-shm'); } catch {}
    bootstrapColony(TEST_DB);
    createWorkstream({ workstream_id: WS, repo: 'test', branch: 'main', mission_id: 'm-1' });
  });

  afterEach(() => {
    closeEventsDb();
    try { unlinkSync(TEST_DB); } catch {}
  });

  // -----------------------------------------------------------------------
  // 1. stuck_task -> pause_retries
  // -----------------------------------------------------------------------
  it('detects stuck_task when a bead has 3+ retries and emits pause_retries', () => {
    for (let i = 0; i < 3; i++) {
      insertEvent(makeEvent({
        event_type: 'retry_pattern_detected',
        bead_id: 'bead-stuck',
      }));
    }

    const result = evaluateBackpressure(WS);
    const stuckSignals = result.signals.filter(s => s.signal === 'stuck_task');
    expect(stuckSignals).toHaveLength(1);
    expect(stuckSignals[0].evidence).toContain('bead-stuck');

    const pauseActions = result.actions.filter(a => a.type === 'pause_retries');
    expect(pauseActions).toHaveLength(1);
    expect(pauseActions[0]).toMatchObject({ type: 'pause_retries', beadId: 'bead-stuck' });
  });

  // -----------------------------------------------------------------------
  // 2. oscillating_state -> freeze_bead
  // -----------------------------------------------------------------------
  it('detects oscillating_state when a bead bounces 3+ times and emits freeze_bead', () => {
    // Simulate alternating completed/failed
    for (let i = 0; i < 2; i++) {
      insertEvent(makeEvent({ event_type: 'bead_completed', bead_id: 'bead-osc' }));
      insertEvent(makeEvent({ event_type: 'bead_failed', bead_id: 'bead-osc' }));
    }
    // That gives 4 total (2 completed + 2 failed), which is >= 3

    const result = evaluateBackpressure(WS);
    const oscSignals = result.signals.filter(s => s.signal === 'oscillating_state');
    expect(oscSignals).toHaveLength(1);
    expect(oscSignals[0].evidence).toContain('bead-osc');

    const freezeActions = result.actions.filter(a => a.type === 'freeze_bead');
    expect(freezeActions).toHaveLength(1);
    expect(freezeActions[0]).toMatchObject({ type: 'freeze_bead', beadId: 'bead-osc' });
  });

  // -----------------------------------------------------------------------
  // 3. rising_escalation -> slow_promotion
  // -----------------------------------------------------------------------
  it('detects rising_escalation when >50% findings are escalated and emits slow_promotion', () => {
    const db = getEventsDb();
    const now = new Date().toISOString();

    // Create 3 findings: 2 escalated, 1 open -> 2/3 = 67% > 50%
    for (let i = 0; i < 2; i++) {
      const id = `f-esc-${i}`;
      db.prepare(`
        INSERT INTO findings (finding_id, workstream_id, finding_type, evidence, confidence,
          promotion_state, salience, created_at, updated_at)
        VALUES (?, ?, 'backpressure', '{}', 0.5, 'escalated', 1.0, ?, ?)
      `).run(id, WS, now, now);
    }
    createFinding({
      workstream_id: WS,
      finding_type: 'backpressure',
      evidence: { note: 'normal' },
      confidence: 0.5,
    });

    const result = evaluateBackpressure(WS);
    const escSignals = result.signals.filter(s => s.signal === 'rising_escalation');
    expect(escSignals).toHaveLength(1);
    expect(escSignals[0].evidence).toContain('67%');

    const slowActions = result.actions.filter(a => a.type === 'slow_promotion');
    expect(slowActions).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // 4. queue_starvation -> trigger_discover
  // -----------------------------------------------------------------------
  it('detects queue_starvation when no events for >30min and no active beads', () => {
    // Insert an event 45 minutes ago
    const oldTime = new Date(Date.now() - 45 * 60 * 1000).toISOString();
    insertEvent(makeEvent({
      event_type: 'bead_completed',
      timestamp: oldTime,
    }));

    const result = evaluateBackpressure(WS);
    const starveSignals = result.signals.filter(s => s.signal === 'queue_starvation');
    expect(starveSignals).toHaveLength(1);
    expect(starveSignals[0].evidence).toContain('minutes');

    const discoverActions = result.actions.filter(a => a.type === 'trigger_discover');
    expect(discoverActions).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // 5. low_confidence_flood -> trigger_clustering
  // -----------------------------------------------------------------------
  it('detects low_confidence_flood when >10 low-confidence findings and emits trigger_clustering', () => {
    // Create 11 low-confidence open findings
    for (let i = 0; i < 11; i++) {
      createFinding({
        workstream_id: WS,
        finding_type: 'exploratory',
        evidence: { note: `low-conf-${i}` },
        confidence: 0.3,
      });
    }

    const result = evaluateBackpressure(WS);
    const floodSignals = result.signals.filter(s => s.signal === 'low_confidence_flood');
    expect(floodSignals).toHaveLength(1);
    expect(floodSignals[0].evidence).toContain('11');

    const clusterActions = result.actions.filter(a => a.type === 'trigger_clustering');
    expect(clusterActions).toHaveLength(1);
  });

  // -----------------------------------------------------------------------
  // 6. review_disagreement -> escalate_to_human
  // -----------------------------------------------------------------------
  it('detects review_disagreement when 3+ reviewer rejections and emits escalate_to_human', () => {
    for (let i = 0; i < 3; i++) {
      insertEvent(makeEvent({
        event_type: 'bead_failed',
        bead_id: 'bead-review',
        payload: { loop_level: 'L1', reason: 'reviewer rejected' },
      }));
    }

    const result = evaluateBackpressure(WS);
    const reviewSignals = result.signals.filter(s => s.signal === 'review_disagreement');
    expect(reviewSignals).toHaveLength(1);
    expect(reviewSignals[0].evidence).toContain('bead-review');

    const escalateActions = result.actions.filter(a => a.type === 'escalate_to_human');
    expect(escalateActions).toHaveLength(1);
    expect(escalateActions[0]).toMatchObject({ type: 'escalate_to_human', beadId: 'bead-review' });
  });

  // -----------------------------------------------------------------------
  // 7. Healthy system -> no signals, no actions
  // -----------------------------------------------------------------------
  it('returns empty signals and actions when system is healthy', () => {
    // Insert a recent event so no starvation
    insertEvent(makeEvent({ event_type: 'bead_completed' }));

    // Create a single high-confidence finding
    createFinding({
      workstream_id: WS,
      finding_type: 'in_scope',
      evidence: { note: 'healthy' },
      confidence: 0.9,
    });

    const result = evaluateBackpressure(WS);
    expect(result.signals).toHaveLength(0);
    expect(result.actions).toHaveLength(0);
  });
});
