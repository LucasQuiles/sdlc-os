-- Colony events database — separate from tmup.db to avoid write contention (C2)

PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 8000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', '1');

-- Typed event log (§11.1)
CREATE TABLE IF NOT EXISTS events (
  event_id         TEXT PRIMARY KEY,
  event_type       TEXT NOT NULL,
  workstream_id    TEXT NOT NULL,
  bead_id          TEXT,
  agent_id         TEXT,
  timestamp        TEXT NOT NULL,
  payload          TEXT NOT NULL,
  processing_level TEXT NOT NULL DEFAULT 'pending'
    CHECK (processing_level IN ('pending','logged','condensed','enriched')),
  idempotency_key  TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_events_workstream ON events (workstream_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_processing ON events (processing_level, timestamp);

-- State ledger (§10.2)
CREATE TABLE IF NOT EXISTS state_ledger (
  workstream_id    TEXT PRIMARY KEY,
  repo             TEXT NOT NULL,
  branch           TEXT NOT NULL,
  mission_id       TEXT NOT NULL,
  scope_region     TEXT,
  bead_lineage     TEXT,
  active_beads     TEXT NOT NULL DEFAULT '{}',
  latest_commit    TEXT,
  diff_summary     TEXT,
  changed_files    TEXT DEFAULT '[]',
  hotspots         TEXT DEFAULT '[]',
  linked_artifacts TEXT DEFAULT '[]',
  linked_findings  TEXT DEFAULT '[]',
  decision_anchors TEXT DEFAULT '[]',
  unresolved       TEXT DEFAULT '[]',
  provenance       TEXT DEFAULT '{}',
  last_enriched_at TEXT,
  vector_refs      TEXT DEFAULT '[]',
  schema_version   INTEGER NOT NULL DEFAULT 1,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL
);

-- Findings store (§11.3)
CREATE TABLE IF NOT EXISTS findings (
  finding_id        TEXT PRIMARY KEY,
  workstream_id     TEXT NOT NULL,
  source_bead_id    TEXT,
  source_agent_id   TEXT,
  finding_type      TEXT NOT NULL
    CHECK (finding_type IN ('in_scope','exploratory','boundary_crossing','backpressure','duplicate_candidate')),
  evidence          TEXT NOT NULL DEFAULT '{}',
  confidence        REAL NOT NULL DEFAULT 0.5
    CHECK (confidence BETWEEN 0.0 AND 1.0),
  affected_scope    TEXT,
  suspected_domain  TEXT,
  related_findings  TEXT DEFAULT '[]',
  suggested_actions TEXT DEFAULT '[]',
  promotion_state   TEXT NOT NULL DEFAULT 'open'
    CHECK (promotion_state IN ('open','promoted','deferred','suppressed','merged','escalated','archived')),
  suppression_reason TEXT,
  salience          REAL NOT NULL DEFAULT 1.0,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  resolved_at       TEXT,
  schema_version    INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_findings_workstream ON findings (workstream_id, promotion_state);
CREATE INDEX IF NOT EXISTS idx_findings_salience ON findings (salience DESC) WHERE promotion_state = 'open';

-- Conductor journal (§9.3)
CREATE TABLE IF NOT EXISTS conductor_journal (
  entry_id       TEXT PRIMARY KEY,
  workstream_id  TEXT NOT NULL,
  session_type   TEXT NOT NULL,
  timestamp      TEXT NOT NULL,
  structured     TEXT NOT NULL DEFAULT '{}',
  narrative      TEXT NOT NULL DEFAULT '',
  schema_version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_journal_workstream ON conductor_journal (workstream_id, timestamp DESC);

-- Seed remediation patterns (H1: cold-start deadlock fix)
CREATE TABLE IF NOT EXISTS remediation_patterns (
  pattern_id   TEXT PRIMARY KEY,
  pattern_type TEXT NOT NULL,
  description  TEXT NOT NULL,
  confidence   REAL NOT NULL DEFAULT 0.5,
  usage_count  INTEGER NOT NULL DEFAULT 0,
  created_at   TEXT NOT NULL,
  updated_at   TEXT NOT NULL
);
