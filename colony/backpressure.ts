/**
 * Backpressure control loop -- detects system stress signals and maps them
 * to concrete corrective actions (spec S15).
 *
 * Six signal/response pairs:
 *   stuck_task          -> pause_retries
 *   oscillating_state   -> freeze_bead
 *   rising_escalation   -> slow_promotion
 *   queue_starvation    -> trigger_discover
 *   low_confidence_flood-> trigger_clustering
 *   review_disagreement -> escalate_to_human
 */

import { getEventsDb } from './events-db.js';
import { getOpenFindings } from './finding-ops.js';
import { getLedger } from './state-ledger.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BackpressureSignal =
  | 'stuck_task'
  | 'oscillating_state'
  | 'rising_escalation'
  | 'queue_starvation'
  | 'low_confidence_flood'
  | 'review_disagreement';

export type BackpressureAction =
  | { type: 'pause_retries'; beadId: string; reason: string }
  | { type: 'freeze_bead'; beadId: string; reason: string }
  | { type: 'slow_promotion'; reason: string }
  | { type: 'trigger_discover'; reason: string }
  | { type: 'trigger_clustering'; reason: string }
  | { type: 'escalate_to_human'; beadId?: string; reason: string };

export interface BackpressureEvaluation {
  signals: Array<{ signal: BackpressureSignal; evidence: string }>;
  actions: BackpressureAction[];
}

// ---------------------------------------------------------------------------
// Thresholds
// ---------------------------------------------------------------------------

const STUCK_RETRY_THRESHOLD = 3;
const OSCILLATION_THRESHOLD = 3;
const ESCALATION_RATIO_THRESHOLD = 0.5;
const STARVATION_MINUTES = 30;
const LOW_CONFIDENCE_THRESHOLD = 0.5;
const LOW_CONFIDENCE_COUNT = 10;
const REVIEW_REJECTION_THRESHOLD = 3;

// ---------------------------------------------------------------------------
// Signal detectors (each returns zero or more signal+action pairs)
// ---------------------------------------------------------------------------

function detectStuckTask(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const db = getEventsDb();
    const rows = db
      .prepare(
        `SELECT bead_id, COUNT(*) as cnt
         FROM events
         WHERE workstream_id = ? AND event_type = 'retry_pattern_detected' AND bead_id IS NOT NULL
         GROUP BY bead_id
         HAVING cnt >= ?`,
      )
      .all(workstreamId, STUCK_RETRY_THRESHOLD) as Array<{ bead_id: string; cnt: number }>;

    for (const row of rows) {
      signals.push({
        signal: 'stuck_task',
        evidence: `bead ${row.bead_id} retried ${row.cnt} times`,
      });
      actions.push({
        type: 'pause_retries',
        beadId: row.bead_id,
        reason: `bead ${row.bead_id} retried ${row.cnt} times (threshold: ${STUCK_RETRY_THRESHOLD})`,
      });
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

function detectOscillatingState(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const db = getEventsDb();
    // Find beads that have alternating completed/failed events.
    // Count total completed+failed per bead; 3+ alternations means 3+ of each type
    // (simplification: if a bead has >= OSCILLATION_THRESHOLD of each, it is oscillating)
    const rows = db
      .prepare(
        `SELECT bead_id,
                SUM(CASE WHEN event_type = 'bead_completed' THEN 1 ELSE 0 END) as completions,
                SUM(CASE WHEN event_type = 'bead_failed' THEN 1 ELSE 0 END) as failures
         FROM events
         WHERE workstream_id = ?
           AND event_type IN ('bead_completed', 'bead_failed')
           AND bead_id IS NOT NULL
         GROUP BY bead_id
         HAVING completions + failures >= ?`,
      )
      .all(workstreamId, OSCILLATION_THRESHOLD) as Array<{
      bead_id: string;
      completions: number;
      failures: number;
    }>;

    for (const row of rows) {
      const total = row.completions + row.failures;
      if (total >= OSCILLATION_THRESHOLD) {
        signals.push({
          signal: 'oscillating_state',
          evidence: `bead ${row.bead_id} bounced ${total} times (${row.completions} completions, ${row.failures} failures)`,
        });
        actions.push({
          type: 'freeze_bead',
          beadId: row.bead_id,
          reason: `bead ${row.bead_id} oscillating with ${total} state changes`,
        });
      }
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

function detectRisingEscalation(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const findings = getOpenFindings(workstreamId);
    if (findings.length === 0) return { signals, actions };

    const escalated = findings.filter(f => f.promotion_state === 'escalated').length;
    // getOpenFindings returns promotion_state='open' only, so we need to query all non-archived
    const db = getEventsDb();
    const allOpen = db
      .prepare(
        `SELECT promotion_state, COUNT(*) as cnt
         FROM findings
         WHERE workstream_id = ? AND promotion_state NOT IN ('archived', 'suppressed')
         GROUP BY promotion_state`,
      )
      .all(workstreamId) as Array<{ promotion_state: string; cnt: number }>;

    let total = 0;
    let escalatedCount = 0;
    for (const row of allOpen) {
      total += row.cnt;
      if (row.promotion_state === 'escalated') {
        escalatedCount = row.cnt;
      }
    }

    if (total > 0 && escalatedCount / total > ESCALATION_RATIO_THRESHOLD) {
      const ratio = Math.round((escalatedCount / total) * 100);
      signals.push({
        signal: 'rising_escalation',
        evidence: `${ratio}% of findings are escalated (${escalatedCount}/${total})`,
      });
      actions.push({
        type: 'slow_promotion',
        reason: `${ratio}% escalation rate exceeds ${ESCALATION_RATIO_THRESHOLD * 100}% threshold`,
      });
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

function detectQueueStarvation(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const db = getEventsDb();

    // Check latest event timestamp
    const latest = db
      .prepare(
        `SELECT MAX(timestamp) as ts FROM events WHERE workstream_id = ?`,
      )
      .get(workstreamId) as { ts: string | null } | undefined;

    if (!latest?.ts) return { signals, actions };

    const latestTime = new Date(latest.ts).getTime();
    const now = Date.now();
    const minutesSinceLastEvent = (now - latestTime) / (1000 * 60);

    if (minutesSinceLastEvent < STARVATION_MINUTES) return { signals, actions };

    // Check if ledger shows no active work
    const ledger = getLedger(workstreamId);
    const activeBeads = ledger?.active_beads ?? {};
    const hasActiveWork = Object.values(activeBeads).some(
      status => status !== 'completed' && status !== 'failed' && status !== 'cancelled',
    );

    if (!hasActiveWork) {
      signals.push({
        signal: 'queue_starvation',
        evidence: `no events for ${Math.round(minutesSinceLastEvent)} minutes and no active beads`,
      });
      actions.push({
        type: 'trigger_discover',
        reason: `queue idle for ${Math.round(minutesSinceLastEvent)} minutes with no active work`,
      });
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

function detectLowConfidenceFlood(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const db = getEventsDb();
    const row = db
      .prepare(
        `SELECT COUNT(*) as cnt
         FROM findings
         WHERE workstream_id = ? AND promotion_state = 'open' AND confidence < ?`,
      )
      .get(workstreamId, LOW_CONFIDENCE_THRESHOLD) as { cnt: number };

    if (row.cnt > LOW_CONFIDENCE_COUNT) {
      signals.push({
        signal: 'low_confidence_flood',
        evidence: `${row.cnt} open findings with confidence below ${LOW_CONFIDENCE_THRESHOLD}`,
      });
      actions.push({
        type: 'trigger_clustering',
        reason: `${row.cnt} low-confidence findings exceed threshold of ${LOW_CONFIDENCE_COUNT}`,
      });
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

function detectReviewDisagreement(
  workstreamId: string,
): { signals: BackpressureEvaluation['signals']; actions: BackpressureAction[] } {
  const signals: BackpressureEvaluation['signals'] = [];
  const actions: BackpressureAction[] = [];

  try {
    const db = getEventsDb();
    // bead_failed events at L1+ loop level (payload.loop_level >= 1) grouped by bead
    const rows = db
      .prepare(
        `SELECT bead_id, COUNT(*) as cnt
         FROM events
         WHERE workstream_id = ?
           AND event_type = 'bead_failed'
           AND bead_id IS NOT NULL
           AND json_extract(payload, '$.loop_level') >= 1
         GROUP BY bead_id
         HAVING cnt >= ?`,
      )
      .all(workstreamId, REVIEW_REJECTION_THRESHOLD) as Array<{ bead_id: string; cnt: number }>;

    for (const row of rows) {
      signals.push({
        signal: 'review_disagreement',
        evidence: `bead ${row.bead_id} rejected ${row.cnt} times at review level`,
      });
      actions.push({
        type: 'escalate_to_human',
        beadId: row.bead_id,
        reason: `bead ${row.bead_id} rejected ${row.cnt} times by reviewers (threshold: ${REVIEW_REJECTION_THRESHOLD})`,
      });
    }
  } catch {
    // G6: read failure -> skip signal
  }

  return { signals, actions };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Evaluate backpressure signals for a workstream.
 * Queries events.db for patterns that indicate the system is struggling.
 */
export function evaluateBackpressure(workstreamId: string): BackpressureEvaluation {
  const allSignals: BackpressureEvaluation['signals'] = [];
  const allActions: BackpressureAction[] = [];

  const detectors = [
    detectStuckTask,
    detectOscillatingState,
    detectRisingEscalation,
    detectQueueStarvation,
    detectLowConfidenceFlood,
    detectReviewDisagreement,
  ];

  for (const detect of detectors) {
    const result = detect(workstreamId);
    allSignals.push(...result.signals);
    allActions.push(...result.actions);
  }

  return { signals: allSignals, actions: allActions };
}
