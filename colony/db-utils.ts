// colony/db-utils.ts
import { getEventsDb, ColonyDbError } from './events-db.js';

/**
 * Safely parse a JSON column from a database row.
 * Returns the default value if the raw value is null, undefined, or empty string.
 * Throws ColonyDbError if the value exists but is not valid JSON.
 */
export function parseJsonField<T>(raw: unknown, fallback: T): T {
  if (raw === null || raw === undefined || raw === '') return fallback;
  try {
    return JSON.parse(raw as string) as T;
  } catch (err) {
    throw new ColonyDbError(`Invalid JSON in database column: ${String(raw).slice(0, 100)}`, err);
  }
}

/**
 * Get current ISO timestamp. Centralizes the 20+ `new Date().toISOString()` calls.
 */
export function now(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// Shared DB read helpers
// ---------------------------------------------------------------------------

/**
 * Read a single row from events.db with G6 error handling.
 * Returns null if not found or on error.
 */
export function readOne<T>(
  sql: string,
  params: unknown[],
  mapper: (row: Record<string, unknown>) => T,
  context: string,
): T | null {
  try {
    const db = getEventsDb();
    const row = db.prepare(sql).get(...params) as Record<string, unknown> | undefined;
    if (!row) return null;
    return mapper(row);
  } catch (err) {
    console.warn(`readOne failed (${context}):`, err);
    return null;
  }
}

/**
 * Read multiple rows from events.db with G6 error handling.
 * Returns empty array on error.
 */
export function readMany<T>(
  sql: string,
  params: unknown[],
  mapper: (row: Record<string, unknown>) => T,
  context: string,
): T[] {
  try {
    const db = getEventsDb();
    const rows = db.prepare(sql).all(...params) as Array<Record<string, unknown>>;
    return rows.map(mapper);
  } catch (err) {
    console.warn(`readMany failed (${context}):`, err);
    return [];
  }
}
