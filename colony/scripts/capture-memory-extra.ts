import { openEventsDb, closeEventsDb } from '../events-db.js';
import { createFinding } from '../finding-ops.js';
import { DEFAULT_EVENTS_DB, BACKLOG_WORKSTREAM } from './lib/defaults.js';

const dbPath = process.argv[2] || DEFAULT_EVENTS_DB;
openEventsDb(dbPath);
const WS = BACKLOG_WORKSTREAM;

// Connection exhaustion — recurring production issue
createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'Multiple connection_exhausted critical incidents on 2026-04-04. Auto-recovery resolves but root cause not addressed — recurring issue.', source: 'episodic-memory alerts from q-agent' }, confidence: 0.9, affected_scope: 'src/transport/connection.ts', suggested_actions: ['Investigate connection pool exhaustion root cause', 'Add connection count monitoring', 'Consider connection recycling or keepalive tuning'] });

// Infrastructure hardening directive still open
createFinding({ workstream_id: WS, finding_type: 'exploratory', evidence: { observed: 'Open directive from 2026-03-31: examine logs, reliability concerns, harden infrastructure. Status unclear — some hardening tasks completed but systematic log analysis not done.', source: 'episodic-memory conversation 2026-03-31' }, confidence: 0.6, affected_scope: 'src/', suspected_domain: 'infrastructure-reliability', suggested_actions: ['Schedule systematic log analysis as DISCOVER bead', 'Cross-reference with completed hardening tasks'] });

closeEventsDb();
console.log('2 additional memory findings captured');
