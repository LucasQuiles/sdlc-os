/**
 * State ledger CRUD + coordinated rehydration.
 *
 * Reads/updates the state_ledger table and assembles StatePackets
 * that combine ledger state, journal context, and open findings
 * for Conductor session rehydration.
 *
 * G6 error handling:
 * - Read operations (getLedger, rehydrateStatePacket): return null/empty on error, log warning
 * - Write operations (updateLedger): throw ColonyDbError
 */

import { getEventsDb, ColonyDbError } from './events-db.js';
import type { StateLedgerRow, ConductorJournalEntry, Finding } from './event-types.js';
import { readJournalHistory } from './conductor-journal.js';
import { getOpenFindings } from './finding-ops.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StatePacket {
  ledger: StateLedgerRow;
  recentJournal: ConductorJournalEntry[];
  openFindings: Finding[];
  rehydratedAt: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** JSON columns that are stored as TEXT in SQLite but parsed as arrays/objects. */
const JSON_COLUMNS: Record<string, 'object' | 'array'> = {
  active_beads: 'object',
  changed_files: 'array',
  hotspots: 'array',
  linked_artifacts: 'array',
  linked_findings: 'array',
  decision_anchors: 'array',
  unresolved: 'array',
  provenance: 'object',
  vector_refs: 'array',
};

function rowToLedger(row: Record<string, unknown>): StateLedgerRow {
  return {
    workstream_id: row.workstream_id as string,
    repo: row.repo as string,
    branch: row.branch as string,
    mission_id: row.mission_id as string,
    scope_region: row.scope_region as string | undefined,
    bead_lineage: row.bead_lineage as string | undefined,
    active_beads: JSON.parse((row.active_beads as string) || '{}'),
    latest_commit: row.latest_commit as string | undefined,
    diff_summary: row.diff_summary as string | undefined,
    changed_files: JSON.parse((row.changed_files as string) || '[]'),
    hotspots: JSON.parse((row.hotspots as string) || '[]'),
    linked_artifacts: JSON.parse((row.linked_artifacts as string) || '[]'),
    linked_findings: JSON.parse((row.linked_findings as string) || '[]'),
    decision_anchors: JSON.parse((row.decision_anchors as string) || '[]'),
    unresolved: JSON.parse((row.unresolved as string) || '[]'),
    provenance: JSON.parse((row.provenance as string) || '{}'),
    last_enriched_at: row.last_enriched_at as string | undefined,
    vector_refs: JSON.parse((row.vector_refs as string) || '[]'),
  };
}

// ---------------------------------------------------------------------------
// CRUD
// ---------------------------------------------------------------------------

/**
 * Read the full state ledger row for a workstream.
 * Returns null if workstream doesn't exist.
 */
export function getLedger(workstreamId: string): StateLedgerRow | null {
  try {
    const db = getEventsDb();
    const row = db.prepare(
      'SELECT * FROM state_ledger WHERE workstream_id = ?',
    ).get(workstreamId) as Record<string, unknown> | undefined;
    if (!row) return null;
    return rowToLedger(row);
  } catch (err) {
    console.warn(`[state-ledger] getLedger failed for ${workstreamId}:`, err);
    return null;
  }
}

/**
 * Update specific fields on an existing state ledger row.
 * Only updates non-undefined fields (partial update).
 */
const ALLOWED_COLUMNS = new Set([
  'repo', 'branch', 'mission_id', 'scope_region', 'bead_lineage',
  'active_beads', 'latest_commit', 'diff_summary', 'changed_files',
  'hotspots', 'linked_artifacts', 'linked_findings', 'decision_anchors',
  'unresolved', 'provenance', 'last_enriched_at', 'vector_refs',
]);

export function updateLedger(workstreamId: string, fields: Partial<StateLedgerRow>): void {
  try {
    const db = getEventsDb();

    // Verify workstream exists
    const exists = db.prepare(
      'SELECT 1 FROM state_ledger WHERE workstream_id = ?',
    ).get(workstreamId);
    if (!exists) {
      throw new ColonyDbError(`Workstream ${workstreamId} not found in state ledger`);
    }

    // Build SET clause from non-undefined fields (excluding workstream_id)
    const setClauses: string[] = [];
    const values: unknown[] = [];

    const entries = Object.entries(fields).filter(
      ([key, value]) => key !== 'workstream_id' && value !== undefined,
    );

    // Validate column names against whitelist to prevent SQL injection
    for (const [column] of entries) {
      if (!ALLOWED_COLUMNS.has(column)) {
        throw new ColonyDbError(`Invalid column name: ${column}`);
      }
    }

    for (const [key, value] of entries) {
      // Map TypeScript field names to SQL column names (they match in this schema)
      const column = key;

      if (column in JSON_COLUMNS) {
        setClauses.push(`${column} = ?`);
        values.push(JSON.stringify(value));
      } else {
        setClauses.push(`${column} = ?`);
        values.push(value);
      }
    }

    if (setClauses.length === 0) return;

    // Always bump updated_at
    setClauses.push('updated_at = ?');
    values.push(new Date().toISOString());

    values.push(workstreamId);

    db.prepare(
      `UPDATE state_ledger SET ${setClauses.join(', ')} WHERE workstream_id = ?`,
    ).run(...values);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to update ledger for ${workstreamId}`, err);
  }
}

// ---------------------------------------------------------------------------
// Rehydration
// ---------------------------------------------------------------------------

/**
 * Orchestrated rehydration: assemble a state packet for a Conductor session.
 * 1. Read ledger row (authoritative structured state)
 * 2. Read latest 3 journal entries (decision context)
 * 3. Read open findings for this workstream (active issues)
 * 4. Combine into a StatePacket
 */
export function rehydrateStatePacket(workstreamId: string): StatePacket | null {
  try {
    const ledger = getLedger(workstreamId);
    if (!ledger) return null;

    const recentJournal = readJournalHistory(workstreamId, 3);
    const openFindings = getOpenFindings(workstreamId);

    return {
      ledger,
      recentJournal,
      openFindings,
      rehydratedAt: new Date().toISOString(),
    };
  } catch (err) {
    console.warn(`[state-ledger] rehydrateStatePacket failed for ${workstreamId}:`, err);
    return null;
  }
}
