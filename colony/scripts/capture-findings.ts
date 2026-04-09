/**
 * Capture external observations as structured findings in the colony events DB.
 * Run: cd colony && npx tsx scripts/capture-findings.ts
 */
import { openEventsDb, insertEvent, closeEventsDb } from '../events-db.js';
import { createFinding } from '../finding-ops.js';
import { DEFAULT_EVENTS_DB, BACKLOG_WORKSTREAM } from './lib/defaults.js';

const dbPath = process.argv[2] || DEFAULT_EVENTS_DB;
openEventsDb(dbPath);

const WS = BACKLOG_WORKSTREAM;

// Finding 1: Deacon thread safety issue on startup
createFinding({
  workstream_id: WS,
  finding_type: 'in_scope',
  evidence: {
    observed: 'Deacon _prune_stale_clones crashes with sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread',
    file_refs: ['colony/deacon.py:378'],
    log: 'Apr 04 23:06:05 clone_prune_db_error',
  },
  confidence: 0.9,
  affected_scope: 'colony/deacon.py',
  suggested_actions: ['Use asyncio.to_thread with fresh sqlite3 connection per thread call'],
});

// Finding 2: 829 plan checkboxes never updated
createFinding({
  workstream_id: WS,
  finding_type: 'exploratory',
  evidence: {
    observed: '25 plan files with 829 total unchecked tasks. Work happened without updating checkboxes.',
    file_refs: ['docs/plans/', 'docs/superpowers/plans/'],
  },
  confidence: 0.7,
  affected_scope: 'docs/',
  suspected_domain: 'documentation-hygiene',
  suggested_actions: ['Run codebase-vs-plan reconciliation', 'Archive completed plans', 'Add post-hook for checkbox updates'],
});

// Finding 3: Colony Phase 1 plan not marked complete
createFinding({
  workstream_id: WS,
  finding_type: 'in_scope',
  evidence: {
    observed: 'colony-orchestration-phase1.md shows 35 unchecked tasks but ALL were implemented and tested (138 tests)',
    file_refs: ['docs/superpowers/plans/2026-04-04-colony-orchestration-phase1.md'],
  },
  confidence: 0.95,
  affected_scope: 'docs/superpowers/plans/',
  suggested_actions: ['Update checkboxes or add completion note'],
});

// Finding 4: Deacon systemd RestartMaxDelaySec warning
createFinding({
  workstream_id: WS,
  finding_type: 'in_scope',
  evidence: {
    observed: 'systemd warns: RestartMaxDelaySec= but no RestartSteps= setting',
    file_refs: ['~/.config/systemd/user/sdlc-colony-deacon.service'],
  },
  confidence: 0.8,
  affected_scope: 'colony/systemd/',
  suggested_actions: ['Add RestartSteps=5 or remove RestartMaxDelaySec'],
});

// Finding 5: tmup session reuse — colony attached to stale session
createFinding({
  workstream_id: WS,
  finding_type: 'exploratory',
  evidence: {
    observed: 'tmup_init reattached to multi-provider-30a0d3 with 17 old tasks and 4 stale agents',
  },
  confidence: 0.7,
  affected_scope: 'colony/',
  suspected_domain: 'session-lifecycle',
  suggested_actions: ['Force new session for colony workstreams', 'Add task tagging to separate colony from legacy'],
});

// Backpressure event
insertEvent({
  event_id: `bp-deacon-thread-${Date.now()}`,
  event_type: 'notable_tool_failure',
  workstream_id: WS,
  timestamp: new Date().toISOString(),
  payload: { component: 'deacon', error: 'sqlite3 thread safety violation in _prune_stale_clones', severity: 'non-critical' },
  processing_level: 'pending',
  idempotency_key: 'notable_tool_failure:deacon:thread_safety:prune',
});

closeEventsDb();
console.log('5 findings + 1 backpressure event captured');
