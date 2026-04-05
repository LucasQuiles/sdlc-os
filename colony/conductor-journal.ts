/**
 * Conductor journal — write and read structured + narrative decision entries.
 *
 * Each entry captures what a Conductor session did: beads dispatched/evaluated,
 * findings created/promoted, decisions with evidence, and narrative context.
 * Stored in the events.db conductor_journal table (§9.3).
 *
 * G6 error handling:
 * - Write operations (writeJournalEntry): throw ColonyDbError on failure
 * - Read operations (readLatestJournal, readJournalHistory): return null/empty on error, log warning
 */

import { getEventsDb, ColonyDbError } from './events-db.js';
import { parseJsonField, readOne, readMany } from './db-utils.js';
import type { ConductorJournalEntry } from './event-types.js';

export function writeJournalEntry(entry: ConductorJournalEntry): void {
  try {
    const db = getEventsDb();
    db.prepare(`
      INSERT INTO conductor_journal
        (entry_id, workstream_id, session_type, timestamp, structured, narrative)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(
      entry.entry_id,
      entry.workstream_id,
      entry.session_type,
      entry.timestamp,
      JSON.stringify(entry.structured),
      entry.narrative,
    );
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to write journal entry ${entry.entry_id}`, err);
  }
}

export function readLatestJournal(workstream_id: string): ConductorJournalEntry | null {
  return readOne(
    'SELECT * FROM conductor_journal WHERE workstream_id = ? ORDER BY timestamp DESC LIMIT 1',
    [workstream_id],
    rowToEntry,
    `readLatestJournal(${workstream_id})`,
  );
}

export function readJournalHistory(workstream_id: string, limit: number = 10): ConductorJournalEntry[] {
  return readMany(
    'SELECT * FROM conductor_journal WHERE workstream_id = ? ORDER BY timestamp DESC LIMIT ?',
    [workstream_id, limit],
    rowToEntry,
    `readJournalHistory(${workstream_id})`,
  );
}

function rowToEntry(row: Record<string, unknown>): ConductorJournalEntry {
  return {
    entry_id: row.entry_id as string,
    workstream_id: row.workstream_id as string,
    session_type: row.session_type as string,
    timestamp: row.timestamp as string,
    structured: parseJsonField(row.structured, {}),
    narrative: row.narrative as string,
  };
}
