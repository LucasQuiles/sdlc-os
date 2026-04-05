/**
 * Colony bootstrap — cold-start initialization for the events database.
 *
 * Seeds the schema and remediation patterns so the first Conductor session
 * has enough context to operate without hitting the promotion cold-start
 * deadlock (H1).
 */

import { openEventsDb, getEventsDb, ColonyDbError } from './events-db.js';

const SEED_PATTERNS = [
  { pattern_id: 'lint-fix', pattern_type: 'hygiene', description: 'Lint/format fix in single file', confidence: 0.9 },
  { pattern_id: 'dead-code-removal', pattern_type: 'hygiene', description: 'Remove unused export/function', confidence: 0.85 },
  { pattern_id: 'test-coverage', pattern_type: 'quality', description: 'Add missing test for existing function', confidence: 0.8 },
  { pattern_id: 'type-safety', pattern_type: 'quality', description: 'Replace any-cast with typed interface', confidence: 0.75 },
  { pattern_id: 'import-cleanup', pattern_type: 'hygiene', description: 'Fix unused/circular imports', confidence: 0.85 },
  { pattern_id: 'error-handling', pattern_type: 'reliability', description: 'Add missing error handling path', confidence: 0.7 },
];

/**
 * Bootstrap the colony events database with schema + seed data.
 * Idempotent — safe to call multiple times.
 */
export function bootstrapColony(eventsDbPath: string): void {
  try {
    openEventsDb(eventsDbPath);
    const db = getEventsDb();

    // Seed remediation patterns (H1: cold-start deadlock fix)
    const now = new Date().toISOString();
    const insert = db.prepare(`
      INSERT OR IGNORE INTO remediation_patterns
        (pattern_id, pattern_type, description, confidence, usage_count, created_at, updated_at)
      VALUES (?, ?, ?, ?, 0, ?, ?)
    `);
    for (const p of SEED_PATTERNS) {
      insert.run(p.pattern_id, p.pattern_type, p.description, p.confidence, now, now);
    }
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError('Failed to bootstrap colony database', err);
  }
}

/**
 * Create a minimal state ledger row for a new workstream.
 * This is the cold-start state packet — enough for the first Conductor session.
 */
export function createWorkstream(opts: {
  workstream_id: string;
  repo: string;
  branch: string;
  mission_id: string;
  scope_region?: string;
}): void {
  try {
    const db = getEventsDb();
    const now = new Date().toISOString();
    db.prepare(`
      INSERT OR IGNORE INTO state_ledger
        (workstream_id, repo, branch, mission_id, scope_region, active_beads, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, '{}', ?, ?)
    `).run(opts.workstream_id, opts.repo, opts.branch, opts.mission_id, opts.scope_region ?? null, now, now);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to create workstream ${opts.workstream_id}`, err);
  }
}
