// Colony event types — typed event model for the events database

export type EventType =
  // High-value (full enrichment)
  | 'bead_started'
  | 'bead_completed'
  | 'bead_failed'
  | 'commit_created'
  | 'test_run_completed'
  | 'patch_applied'
  | 'escalation_requested'
  | 'finding_opened'
  | 'finding_promoted'
  | 'session_checkpointed'
  // Medium-value (batched condensation)
  | 'finding_deferred'
  | 'large_file_batch_read'
  | 'notable_tool_failure'
  | 'retry_pattern_detected'
  // Low-value (append-only logging)
  | 'shell_command_executed'
  | 'trivial_file_read'
  | 'intermediate_tool_chatter';

export type ProcessingLevel = 'pending' | 'logged' | 'condensed' | 'enriched';

export type FindingType =
  | 'in_scope'
  | 'exploratory'
  | 'boundary_crossing'
  | 'backpressure'
  | 'duplicate_candidate';

export type PromotionState =
  | 'open'
  | 'promoted'
  | 'deferred'
  | 'suppressed'
  | 'merged'
  | 'escalated'
  | 'archived';

export const HIGH_VALUE_EVENTS: Set<EventType> = new Set([
  'bead_started', 'bead_completed', 'bead_failed', 'commit_created',
  'test_run_completed', 'patch_applied', 'escalation_requested',
  'finding_opened', 'finding_promoted', 'session_checkpointed',
]);

export const MEDIUM_VALUE_EVENTS: Set<EventType> = new Set([
  'finding_deferred', 'large_file_batch_read',
  'notable_tool_failure', 'retry_pattern_detected',
]);

export interface TypedEvent {
  event_id: string;
  event_type: EventType;
  workstream_id: string;
  bead_id?: string;
  agent_id?: string;
  timestamp: string;
  payload: Record<string, unknown>;
  processing_level: ProcessingLevel;
  idempotency_key: string;
}

export interface Finding {
  finding_id: string;
  workstream_id: string;
  source_bead_id?: string;
  source_agent_id?: string;
  finding_type: FindingType;
  evidence: Record<string, unknown>;
  confidence: number;
  affected_scope?: string;
  suspected_domain?: string;
  related_findings: string[];
  suggested_actions: string[];
  promotion_state: PromotionState;
  suppression_reason?: string;
  salience: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

export interface StateLedgerRow {
  workstream_id: string;
  repo: string;
  branch: string;
  mission_id: string;
  scope_region?: string;
  bead_lineage?: string;
  active_beads: Record<string, string>;
  latest_commit?: string;
  diff_summary?: string;
  changed_files: string[];
  hotspots: string[];
  linked_artifacts: Array<{ path: string; type: string; checksum?: string }>;
  linked_findings: string[];
  decision_anchors: Array<Record<string, unknown>>;
  unresolved: string[];
  provenance: Record<string, unknown>;
  last_enriched_at?: string;
  vector_refs: string[];
}

export interface ConductorJournalEntry {
  entry_id: string;
  workstream_id: string;
  session_type: string;
  timestamp: string;
  structured: {
    beads_dispatched?: string[];
    beads_evaluated?: string[];
    findings_created?: string[];
    findings_promoted?: string[];
    findings_suppressed?: string[];
    decisions?: Array<{
      what: string;
      why: string;
      evidence: string[];
      alternatives_rejected?: string[];
      uncertainty?: string[];
      scope_assumed?: string[];
    }>;
    next_actions?: string[];
    backpressure_signals?: string[];
  };
  narrative: string;
}

/** Generate an idempotency key from event components + content hash */
export function makeIdempotencyKey(
  event_type: EventType,
  workstream_id: string,
  bead_id: string | undefined,
  payload: Record<string, unknown>,
): string {
  const contentStr = JSON.stringify(payload);
  // Simple hash for dedup — sufficient for idempotency within a workstream
  let hash = 0;
  for (let i = 0; i < contentStr.length; i++) {
    const char = contentStr.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return `${event_type}:${workstream_id}:${bead_id ?? 'none'}:${hash.toString(36)}`;
}
