import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { bootstrapColony, createWorkstream } from './bootstrap.js';
import { openEventsDb, closeEventsDb, getEventsDb, insertEvent, queryEvents } from './events-db.js';
import { createFinding, checkAutoPromotion, getFinding, getOpenFindings } from './finding-ops.js';
import { writeJournalEntry, readLatestJournal, readJournalHistory } from './conductor-journal.js';
import { updateLedger, getLedger, rehydrateStatePacket } from './state-ledger.js';
import { evaluateBackpressure } from './backpressure.js';
import { classifyFinding } from './boundary-detector.js';
import { CostEnforcer } from './cost-enforcer.js';
import { appendFileSync, readFileSync, unlinkSync, existsSync } from 'node:fs';

const TEST_DB = '/tmp/colony-e2e-full.db';
const INBOX = '/tmp/events-inbox.jsonl';

describe('Colony E2E: Full Protocol Flow', () => {
  beforeEach(() => {
    for (const f of [TEST_DB, TEST_DB + '-wal', TEST_DB + '-shm', INBOX]) {
      try { unlinkSync(f); } catch {}
    }
    bootstrapColony(TEST_DB);
    createWorkstream({
      workstream_id: 'e2e-ws',
      repo: '/home/q/LAB/WhatSoup',
      branch: 'main',
      mission_id: 'e2e-test',
      scope_region: 'src/',
    });
  });

  afterEach(() => {
    closeEventsDb();
    for (const f of [TEST_DB, TEST_DB + '-wal', TEST_DB + '-shm', INBOX]) {
      try { unlinkSync(f); } catch {}
    }
  });

  it('exercises the complete colony data flow', () => {
    // === Phase 1: Worker completes a bead ===
    // Simulate bead_completed event (as if bridge emitted it)
    insertEvent({
      event_id: 'e2e-evt-001',
      event_type: 'bead_completed',
      workstream_id: 'e2e-ws',
      bead_id: 'B-e2e-01',
      timestamp: new Date().toISOString(),
      payload: { new_status: 'submitted', loop_level: 'L0', output_summary: 'lint fixes applied' },
      processing_level: 'pending',
      idempotency_key: 'bead_completed:e2e-ws:B-e2e-01:L0',
    });

    // Verify event stored
    const events = queryEvents('e2e-ws');
    expect(events).toHaveLength(1);
    expect(events[0].event_type).toBe('bead_completed');

    // === Phase 2: Update state ledger (Conductor would do this) ===
    updateLedger('e2e-ws', {
      active_beads: { 'B-e2e-01': 'submitted' },
      latest_commit: 'abc123',
      changed_files: ['src/utils.ts'],
      hotspots: ['src/utils.ts'],
    });

    const ledger = getLedger('e2e-ws');
    expect(ledger).toBeDefined();
    expect(ledger!.active_beads['B-e2e-01']).toBe('submitted');

    // === Phase 3: Worker discovers adjacent issue ===
    // Boundary check: src/utils.ts is in-scope for mission scope 'src/'
    const classification = classifyFinding('src/utils.ts', 'src/');
    expect(classification.classification).toBe('in_scope');
    expect(classification.shouldAutoPromote).toBe(true);

    // Create finding
    const findingId = createFinding({
      workstream_id: 'e2e-ws',
      finding_type: 'in_scope',
      evidence: { observed: 'dead export in utils', file_refs: ['src/utils.ts:42'] },
      confidence: 0.85,
      affected_scope: 'src/utils.ts',
      source_bead_id: 'B-e2e-01',
    });

    // Auto-promote (should match seed pattern 'dead-code-removal')
    const promoResult = checkAutoPromotion(findingId, { active_mission_scope: 'src/' });
    expect(promoResult.promoted).toBe(true);
    expect(getFinding(findingId)!.promotion_state).toBe('promoted');

    // === Phase 4: Boundary crossing detected ===
    const crossClassification = classifyFinding('console/src/pages/Ops.tsx', 'src/');
    expect(crossClassification.classification).toBe('boundary_crossing');
    expect(crossClassification.shouldAutoPromote).toBe(false);

    // Create exploratory finding (not auto-promoted)
    const exploratoryId = createFinding({
      workstream_id: 'e2e-ws',
      finding_type: 'exploratory',
      evidence: { observed: 'stale prop types in Ops page' },
      confidence: 0.6,
      affected_scope: 'console/src/pages/Ops.tsx',
    });
    const exploPromo = checkAutoPromotion(exploratoryId, { active_mission_scope: 'src/' });
    expect(exploPromo.promoted).toBe(false);

    // === Phase 5: Write journal (Conductor session end) ===
    writeJournalEntry({
      entry_id: 'j-e2e-001',
      workstream_id: 'e2e-ws',
      session_type: 'EVALUATE',
      timestamp: new Date().toISOString(),
      structured: {
        beads_evaluated: ['B-e2e-01'],
        findings_promoted: [findingId],
        decisions: [{
          what: 'Promoted dead-export finding',
          why: 'High confidence + file anchor + pattern match',
          evidence: ['src/utils.ts:42'],
          uncertainty: ['Pattern match confidence threshold may need tuning'],
        }],
        next_actions: ['Dispatch follow-on bead for dead export fix'],
        backpressure_signals: [],
      },
      narrative: 'Evaluated B-e2e-01. Promoted dead-export finding. Boundary-crossing Ops.tsx finding logged as exploratory.',
    });

    // === Phase 6: Rehydrate state for next Conductor session ===
    // Update ledger with findings link
    updateLedger('e2e-ws', {
      linked_findings: [findingId, exploratoryId],
      decision_anchors: [{
        session: 'j-e2e-001',
        decision: 'Promoted dead-export finding',
        evidence: ['src/utils.ts:42'],
      }],
    });

    const packet = rehydrateStatePacket('e2e-ws');
    expect(packet).toBeDefined();
    expect(packet!.ledger.active_beads['B-e2e-01']).toBe('submitted');
    expect(packet!.ledger.linked_findings).toContain(findingId);
    expect(packet!.recentJournal).toHaveLength(1);
    expect(packet!.recentJournal[0].session_type).toBe('EVALUATE');
    expect(packet!.openFindings.length).toBeGreaterThanOrEqual(1);

    // === Phase 7: Cost enforcement ===
    const enforcer = new CostEnforcer(50.0);
    enforcer.recordCost('e2e-ws', 42.0);
    const budget = enforcer.checkBudget('e2e-ws');
    expect(budget.phase).toBe('warning');
    expect(budget.discovery_disabled).toBe(true);

    // === Phase 8: Backpressure detection ===
    // Simulate 3 retries on same bead
    for (let i = 0; i < 3; i++) {
      insertEvent({
        event_id: `e2e-retry-${i}`,
        event_type: 'retry_pattern_detected',
        workstream_id: 'e2e-ws',
        bead_id: 'B-stuck',
        timestamp: new Date().toISOString(),
        payload: { count: i + 1 },
        processing_level: 'pending',
        idempotency_key: `retry:e2e-ws:B-stuck:${i}`,
      });
    }

    const bp = evaluateBackpressure('e2e-ws');
    expect(bp.signals.length).toBeGreaterThanOrEqual(1);
    const stuckSignal = bp.signals.find(s => s.signal === 'stuck_task');
    expect(stuckSignal).toBeDefined();
    const pauseAction = bp.actions.find(a => a.type === 'pause_retries');
    expect(pauseAction).toBeDefined();
  });

  it('JSONL inbox simulation: bridge writes, ingest reads', () => {
    // Simulate bridge writing to inbox
    const event = {
      event_id: 'inbox-evt-001',
      event_type: 'bead_completed',
      workstream_id: 'e2e-ws',
      bead_id: 'B-inbox',
      timestamp: new Date().toISOString(),
      payload: { new_status: 'submitted' },
      processing_level: 'pending',
      idempotency_key: 'bead_completed:e2e-ws:B-inbox:test',
    };
    appendFileSync(INBOX, JSON.stringify(event) + '\n', 'utf8');

    // Verify file exists with content
    expect(existsSync(INBOX)).toBe(true);
    const content = readFileSync(INBOX, 'utf8');
    expect(content.trim().length).toBeGreaterThan(0);

    // Parse the line back
    const parsed = JSON.parse(content.trim());
    expect(parsed.event_type).toBe('bead_completed');
    expect(parsed.bead_id).toBe('B-inbox');
  });
});
