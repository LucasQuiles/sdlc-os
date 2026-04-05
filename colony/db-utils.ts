// colony/db-utils.ts
import { ColonyDbError } from './events-db.js';

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
