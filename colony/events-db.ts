/**
 * Colony events database — open/close, insert, query operations.
 *
 * WRITE SERIALIZATION (G4): All writes to events.db should be funneled through
 * the Deacon process. Other colony components (bridge, workers, conductors)
 * write to JSONL inbox files, not directly to this DB. The functions exported
 * here are intended for Deacon-side consumption only.
 */

import Database from 'better-sqlite3';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { TypedEvent } from './event-types.js';
import { parseJsonField } from './db-utils.js';

// ---------------------------------------------------------------------------
// Error class (G6)
// ---------------------------------------------------------------------------

export class ColonyDbError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'ColonyDbError';
  }
}

// ---------------------------------------------------------------------------
// Module state
// ---------------------------------------------------------------------------

let db: Database.Database | null = null;

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

export function openEventsDb(dbPath: string): void {
  if (db) return;
  try {
    db = new Database(dbPath);
    // PRAGMAs must succeed — execute outside error-swallowing loop
    db.pragma('journal_mode = WAL');
    const mode = db.pragma('journal_mode', { simple: true });
    if (mode !== 'wal') {
      console.warn(`events-db: WAL mode not set (got ${mode})`);
    }
    db.pragma('busy_timeout = 8000');
    db.pragma('foreign_keys = ON');

    const __dirname = dirname(fileURLToPath(import.meta.url));
    const schemaPath = join(__dirname, 'events-schema.sql');
    const schema = readFileSync(schemaPath, 'utf8');
    // Execute each CREATE TABLE/INDEX statement separately, tolerating collisions
    for (const stmt of schema.split(';').map(s => s.trim()).filter(Boolean)) {
      // Skip PRAGMA statements — already handled above
      if (/^\s*PRAGMA\b/i.test(stmt)) continue;
      try {
        db.exec(stmt);
      } catch {
        // Ignore CREATE IF NOT EXISTS collisions
      }
    }
  } catch (err) {
    db = null;
    throw new ColonyDbError('Failed to open events database', err);
  }
}

export function closeEventsDb(): void {
  if (!db) return;
  try {
    db.pragma('wal_checkpoint(PASSIVE)');
  } catch {
    // Best-effort checkpoint on close
  }
  try {
    db.close();
  } catch {
    // Ignore close errors
  }
  db = null;
}

export function getEventsDb(): Database.Database {
  if (!db) throw new ColonyDbError('Events DB not open — call openEventsDb first');
  return db;
}

// ---------------------------------------------------------------------------
// Insert (with idempotency)
// ---------------------------------------------------------------------------

export function insertEvent(event: TypedEvent): void {
  try {
    const d = getEventsDb();
    d.prepare(`
      INSERT OR IGNORE INTO events
        (event_id, event_type, workstream_id, bead_id, agent_id,
         timestamp, payload, processing_level, idempotency_key)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      event.event_id,
      event.event_type,
      event.workstream_id,
      event.bead_id ?? null,
      event.agent_id ?? null,
      event.timestamp,
      JSON.stringify(event.payload),
      event.processing_level,
      event.idempotency_key,
    );
  } catch (err) {
    throw new ColonyDbError(`Failed to insert event ${event.event_id}`, err);
  }
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export function queryEvents(
  workstream_id: string,
  opts?: { event_type?: string; limit?: number },
): TypedEvent[] {
  try {
    const d = getEventsDb();
    let sql = 'SELECT * FROM events WHERE workstream_id = ?';
    const params: unknown[] = [workstream_id];
    if (opts?.event_type) {
      sql += ' AND event_type = ?';
      params.push(opts.event_type);
    }
    sql += ' ORDER BY timestamp DESC';
    if (opts?.limit) {
      sql += ' LIMIT ?';
      params.push(opts.limit);
    }
    const rows = d.prepare(sql).all(...params) as Array<Record<string, unknown>>;
    return rows.map(r => ({
      event_id: r.event_id as string,
      event_type: r.event_type as TypedEvent['event_type'],
      workstream_id: r.workstream_id as string,
      bead_id: (r.bead_id as string | null) ?? undefined,
      agent_id: (r.agent_id as string | null) ?? undefined,
      timestamp: r.timestamp as string,
      payload: parseJsonField(r.payload, {}),
      processing_level: r.processing_level as TypedEvent['processing_level'],
      idempotency_key: r.idempotency_key as string,
    }));
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    // G6: read operations return empty on error
    return [];
  }
}
