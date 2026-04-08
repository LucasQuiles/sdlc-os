import { openEventsDb, closeEventsDb } from '../events-db.js';
import { createFinding } from '../finding-ops.js';

openEventsDb('/home/q/.local/state/tmup/colony-events.db');
const WS = 'whatsoup-backlog-scan';

// From episodic memory search
createFinding({ workstream_id: WS, finding_type: 'exploratory', evidence: { observed: 'Repair protocol spec does not define handling of additional incidents during active repair — signal loss risk', source: 'episodic-memory conversation 2026-04-01' }, confidence: 0.7, affected_scope: 'docs/', suspected_domain: 'repair-protocol', suggested_actions: ['Update repair protocol spec with concurrent incident handling'] });

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'service_crash fallback example in docs drops required /heal auth headers — security gap', source: 'episodic-memory conversation 2026-04-03' }, confidence: 0.8, affected_scope: 'docs/', suggested_actions: ['Fix fallback example to include heal auth headers'] });

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'Repeated signals from same source can spam incident/history path — dedup underspecified', source: 'episodic-memory conversation 2026-04-03' }, confidence: 0.85, affected_scope: 'src/', suggested_actions: ['Add signal dedup to open-incident flow'] });

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'Startup step 4b references outdated messages.upsert history sync text', source: 'episodic-memory conversation 2026-03-30', file_refs: ['docs/'] }, confidence: 0.6, affected_scope: 'docs/', suggested_actions: ['Update startup documentation'] });

// From git log scan - colony spec deferred items (already tracked but worth linking)
createFinding({ workstream_id: WS, finding_type: 'exploratory', evidence: { observed: 'Colony spec §7.2 deferred: Brick daemon, local model triage, policy adjudication, federation, Refinery', source: 'git commit b015a4c' }, confidence: 0.5, affected_scope: 'colony/', suspected_domain: 'colony-future-work', suggested_actions: ['Track as future colony phases, not current backlog'] });

closeEventsDb();
console.log('5 memory/git findings captured');
