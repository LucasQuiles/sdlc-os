import { openEventsDb, insertEvent, closeEventsDb } from '../events-db.js';
const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
for (const taskId of ['018','019','020','021']) {
  insertEvent({
    event_id: 'bp-long-running-' + taskId + '-' + Date.now(),
    event_type: 'retry_pattern_detected',
    workstream_id: 'whatsoup-backlog-scan',
    bead_id: 'T-' + taskId,
    timestamp: new Date().toISOString(),
    payload: { signal: 'long_running_task', duration_minutes: 57, threshold_minutes: 15, task_id: taskId },
    processing_level: 'pending',
    idempotency_key: 'long_running:T-' + taskId + ':57min',
  });
}
closeEventsDb();
console.log('4 long-running backpressure events captured');
