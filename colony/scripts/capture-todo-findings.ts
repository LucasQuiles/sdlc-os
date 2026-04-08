import { openEventsDb, closeEventsDb } from '../events-db.js';
import { createFinding } from '../finding-ops.js';

const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
const WS = 'whatsoup-backlog-scan';

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'TODO: send admin notification — missing feature in heal.ts', file_refs: ['src/core/heal.ts:82'] }, confidence: 0.85, affected_scope: 'src/core/heal.ts', suggested_actions: ['Implement admin notification via WhatsApp or webhook'] });

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'Tool execution not yet wired — placeholder in OpenAI + Anthropic API providers', file_refs: ['src/runtimes/agent/providers/openai-api.ts:164', 'src/runtimes/agent/providers/anthropic-api.ts:167'] }, confidence: 0.9, affected_scope: 'src/runtimes/agent/providers/', suggested_actions: ['Wire MCP tool execution bridge for HTTP API providers'] });

createFinding({ workstream_id: WS, finding_type: 'in_scope', evidence: { observed: 'TODO: Store per-instance API key in keyring', file_refs: ['src/fleet/routes/ops.ts:562'] }, confidence: 0.8, affected_scope: 'src/fleet/routes/ops.ts', suggested_actions: ['Implement GNOME Keyring storage for per-instance API keys'] });

closeEventsDb();
console.log('3 TODO/FIXME findings captured');
