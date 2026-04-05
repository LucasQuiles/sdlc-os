/**
 * Colony finding operations — CRUD + promotion policy + archival.
 *
 * All DB functions use try/catch per G6:
 * - Read ops (getFinding, getOpenFindings): return null/empty on error, log warning
 * - Write ops (createFinding, promoteFinding, etc.): throw ColonyDbError
 */

import { getEventsDb, ColonyDbError } from './events-db.js';
import { parseJsonField } from './db-utils.js';
import type { Finding, FindingType } from './event-types.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const MAX_OPEN_FINDINGS_PER_WORKSTREAM = 100;
export const SALIENCE_ARCHIVE_THRESHOLD = 0.05;
export const AUTO_PROMOTION_CONFIDENCE_THRESHOLD = 0.7;
export const STALE_FINDING_TTL_DAYS = 30;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateId(): string {
  return `f-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function rowToFinding(row: Record<string, unknown>): Finding {
  return {
    finding_id: row.finding_id as string,
    workstream_id: row.workstream_id as string,
    source_bead_id: row.source_bead_id as string | undefined,
    source_agent_id: row.source_agent_id as string | undefined,
    finding_type: row.finding_type as Finding['finding_type'],
    evidence: parseJsonField(row.evidence, {}),
    confidence: row.confidence as number,
    affected_scope: row.affected_scope as string | undefined,
    suspected_domain: row.suspected_domain as string | undefined,
    related_findings: JSON.parse((row.related_findings as string) || '[]'),
    suggested_actions: JSON.parse((row.suggested_actions as string) || '[]'),
    promotion_state: row.promotion_state as Finding['promotion_state'],
    suppression_reason: row.suppression_reason as string | undefined,
    salience: row.salience as number,
    created_at: row.created_at as string,
    updated_at: row.updated_at as string,
    resolved_at: row.resolved_at as string | undefined,
  };
}

// ---------------------------------------------------------------------------
// CRUD
// ---------------------------------------------------------------------------

export function createFinding(opts: {
  workstream_id: string;
  finding_type: FindingType;
  evidence: Record<string, unknown>;
  confidence: number;
  affected_scope?: string;
  suspected_domain?: string;
  source_bead_id?: string;
  source_agent_id?: string;
  suggested_actions?: string[];
  related_findings?: string[];
}): string {
  try {
    const db = getEventsDb();
    const id = generateId();
    const now = new Date().toISOString();

    db.prepare(`
      INSERT INTO findings
        (finding_id, workstream_id, source_bead_id, source_agent_id, finding_type,
         evidence, confidence, affected_scope, suspected_domain,
         related_findings, suggested_actions,
         created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      id, opts.workstream_id, opts.source_bead_id ?? null, opts.source_agent_id ?? null,
      opts.finding_type, JSON.stringify(opts.evidence), opts.confidence,
      opts.affected_scope ?? null, opts.suspected_domain ?? null,
      JSON.stringify(opts.related_findings ?? []),
      JSON.stringify(opts.suggested_actions ?? []), now, now,
    );

    // Enforce cap
    enforceOpenFindingsCap(opts.workstream_id);

    return id;
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError('Failed to create finding', err);
  }
}

export function getFinding(finding_id: string): Finding | null {
  try {
    const db = getEventsDb();
    const row = db.prepare('SELECT * FROM findings WHERE finding_id = ?').get(finding_id) as Record<string, unknown> | undefined;
    if (!row) return null;
    return rowToFinding(row);
  } catch (err) {
    // G6: read operations return null on error
    console.warn('getFinding error:', err);
    return null;
  }
}

export function getOpenFindings(workstream_id: string): Finding[] {
  try {
    const db = getEventsDb();
    const rows = db.prepare(
      "SELECT * FROM findings WHERE workstream_id = ? AND promotion_state = 'open' ORDER BY salience DESC"
    ).all(workstream_id) as Array<Record<string, unknown>>;
    return rows.map(rowToFinding);
  } catch (err) {
    // G6: read operations return empty on error
    console.warn('getOpenFindings error:', err);
    return [];
  }
}

// ---------------------------------------------------------------------------
// Promotion policy
// ---------------------------------------------------------------------------

export function checkAutoPromotion(
  finding_id: string,
  context: { active_mission_scope: string },
): { promoted: boolean; reason?: string } {
  const f = getFinding(finding_id);
  if (!f) return { promoted: false, reason: 'finding not found' };
  if (f.promotion_state !== 'open') return { promoted: false, reason: `already ${f.promotion_state}` };

  // All conditions must be met for auto-promotion
  if (f.finding_type !== 'in_scope') {
    return { promoted: false, reason: `not in_scope (is ${f.finding_type})` };
  }
  if (f.confidence < AUTO_PROMOTION_CONFIDENCE_THRESHOLD) {
    return { promoted: false, reason: `confidence below ${AUTO_PROMOTION_CONFIDENCE_THRESHOLD} (is ${f.confidence})` };
  }
  const evidence = f.evidence as Record<string, unknown>;
  const fileRefs = evidence['file_refs'] as string[] | undefined;
  if (!fileRefs || fileRefs.length === 0) {
    return { promoted: false, reason: 'no file/line anchor in evidence' };
  }
  if (f.affected_scope && !f.affected_scope.startsWith(context.active_mission_scope)) {
    return { promoted: false, reason: `affected scope ${f.affected_scope} outside mission ${context.active_mission_scope}` };
  }

  // Pattern match check (spec §14.1)
  try {
    const db = getEventsDb();
    const patterns = db.prepare(
      'SELECT * FROM remediation_patterns WHERE confidence >= 0.5'
    ).all() as Array<{ pattern_id: string; pattern_type: string; description: string; confidence: number; usage_count: number }>;

    const evidenceStr = JSON.stringify(f.evidence).toLowerCase();
    const matchedPattern = patterns.find(p => {
      const keywords = p.description.toLowerCase().split(/\s+/);
      // Match if at least 2 keywords from the pattern description appear in the evidence
      const matchCount = keywords.filter(kw => kw.length > 3 && evidenceStr.includes(kw)).length;
      return matchCount >= 2;
    });

    if (!matchedPattern) {
      // Cold-start relaxation: check workstream count
      const wsCount = (db.prepare('SELECT COUNT(*) as cnt FROM state_ledger').get() as { cnt: number }).cnt;
      if (wsCount > 10) {
        return { promoted: false, reason: 'no matching remediation pattern and system past cold-start (>10 workstreams)' };
      }
      // Cold-start: allow without pattern match
    }

    // If pattern matched, increment usage_count
    if (matchedPattern) {
      const now = new Date().toISOString();
      db.prepare('UPDATE remediation_patterns SET usage_count = usage_count + 1, updated_at = ? WHERE pattern_id = ?')
        .run(now, matchedPattern.pattern_id);
    }
  } catch (err) {
    // G6: pattern match failure should not block promotion — log and continue
    console.warn('checkAutoPromotion pattern match error:', err);
  }

  // Promote
  promoteFinding(finding_id);
  return { promoted: true };
}

// ---------------------------------------------------------------------------
// State transitions
// ---------------------------------------------------------------------------

export function promoteFinding(finding_id: string): void {
  try {
    const db = getEventsDb();
    const now = new Date().toISOString();
    db.prepare("UPDATE findings SET promotion_state = 'promoted', updated_at = ? WHERE finding_id = ?").run(now, finding_id);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to promote finding ${finding_id}`, err);
  }
}

export function suppressFinding(finding_id: string, reason: string): void {
  try {
    const db = getEventsDb();
    const now = new Date().toISOString();
    db.prepare("UPDATE findings SET promotion_state = 'suppressed', suppression_reason = ?, updated_at = ? WHERE finding_id = ?").run(reason, now, finding_id);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to suppress finding ${finding_id}`, err);
  }
}

export function deferFinding(finding_id: string, reason: string): void {
  try {
    const db = getEventsDb();
    const now = new Date().toISOString();
    db.prepare("UPDATE findings SET promotion_state = 'deferred', suppression_reason = ?, salience = 0.1, updated_at = ? WHERE finding_id = ?").run(reason, now, finding_id);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to defer finding ${finding_id}`, err);
  }
}

export function resurfaceFinding(finding_id: string, newEvidence: Record<string, unknown>): void {
  try {
    const f = getFinding(finding_id);
    if (!f) throw new ColonyDbError(`Finding ${finding_id} not found for resurfacing`);
    if (f.promotion_state !== 'suppressed') {
      throw new ColonyDbError(`Finding ${finding_id} is not suppressed (is ${f.promotion_state})`);
    }

    const db = getEventsDb();
    const now = new Date().toISOString();
    // Merge new evidence with existing
    const mergedEvidence = { ...f.evidence, ...newEvidence, resurfaced_at: now };
    db.prepare(
      "UPDATE findings SET promotion_state = 'open', suppression_reason = NULL, evidence = ?, salience = 1.0, updated_at = ? WHERE finding_id = ?"
    ).run(JSON.stringify(mergedEvidence), now, finding_id);
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to resurface finding ${finding_id}`, err);
  }
}

// ---------------------------------------------------------------------------
// Archival
// ---------------------------------------------------------------------------

export function archiveStaleFindings(workstream_id: string): number {
  try {
    const db = getEventsDb();
    const now = new Date().toISOString();

    // Archive findings below salience threshold
    const salienceResult = db.prepare(`
      UPDATE findings SET promotion_state = 'archived', updated_at = ?
      WHERE workstream_id = ? AND promotion_state = 'open' AND salience < ?
    `).run(now, workstream_id, SALIENCE_ARCHIVE_THRESHOLD);

    // Archive findings past the hard TTL (30 days)
    const ttlCutoff = new Date(Date.now() - STALE_FINDING_TTL_DAYS * 24 * 60 * 60 * 1000).toISOString();
    const ttlResult = db.prepare(`
      UPDATE findings SET promotion_state = 'archived', updated_at = ?
      WHERE workstream_id = ? AND promotion_state = 'open' AND updated_at < ?
    `).run(now, workstream_id, ttlCutoff);

    return (salienceResult as { changes: number }).changes + (ttlResult as { changes: number }).changes;
  } catch (err) {
    if (err instanceof ColonyDbError) throw err;
    throw new ColonyDbError(`Failed to archive stale findings for ${workstream_id}`, err);
  }
}

// ---------------------------------------------------------------------------
// Internal
// ---------------------------------------------------------------------------

function enforceOpenFindingsCap(workstream_id: string): void {
  const db = getEventsDb();
  const count = (db.prepare(
    "SELECT COUNT(*) as cnt FROM findings WHERE workstream_id = ? AND promotion_state = 'open'"
  ).get(workstream_id) as { cnt: number }).cnt;

  if (count > MAX_OPEN_FINDINGS_PER_WORKSTREAM) {
    const excess = count - MAX_OPEN_FINDINGS_PER_WORKSTREAM;
    const now = new Date().toISOString();
    // Archive lowest-salience findings
    db.prepare(`
      UPDATE findings SET promotion_state = 'archived', updated_at = ?
      WHERE finding_id IN (
        SELECT finding_id FROM findings
        WHERE workstream_id = ? AND promotion_state = 'open'
        ORDER BY salience ASC LIMIT ?
      )
    `).run(now, workstream_id, excess);
  }
}
