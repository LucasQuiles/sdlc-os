# Hazard/Defense Ledger — Schema Reference

**Schema version:** 1
**Spec source:** `docs/specs/2026-03-29-hazard-defense-ledger-design.md`
**Phase:** Phase 2 of Cross-Cutting Thinker Enhancement

---

## Overview

The Hazard/Defense Ledger (HDL) is the canonical machine-readable artifact for STPA safety control analysis. It links hazards, unsafe control actions (UCAs), intended defenses, and actual catch points into an auditable control loop for every STPA-required task.

Two canonical artifacts:

| Artifact | Path | Scope |
|----------|------|-------|
| Task ledger | `docs/sdlc/active/{task-id}/hazard-defense-ledger.yaml` | One per qualifying task |
| System ledger | `docs/sdlc/system-hazard-defense.jsonl` | One line per completed task |
| System events | `docs/sdlc/system-hazard-defense-events.jsonl` | Late-arriving corrections |

Structured intermediate from `safety-analyst`:

| Artifact | Path |
|----------|------|
| STPA analysis output | `docs/sdlc/active/{task-id}/stpa-analysis.yaml` |

---

## Task Ledger YAML Schema

**Path:** `docs/sdlc/active/{task-id}/hazard-defense-ledger.yaml`

```yaml
schema_version: 1
task_id: ""
artifact_status: seeded | active | final
#   seeded: created in Architect/pre-Execute by safety-analyst for qualifying beads
#   active: enriched during Execute by AQS, LOSA, latent-condition-tracer
#   final: locked in Synthesize/Complete with catch points and residual risk resolved
stpa_required: true
derived_at: "2026-03-29T14:22:00Z"  # UTC ISO 8601
last_updated: "2026-03-29T14:22:00Z"

summary:
  qualifying_beads: 0       # beads that triggered STPA (COMPLEX or security_sensitive: true)
  records_total: 0          # total HDL records across all qualifying beads
  records_with_defense: 0   # records with at least one intended_defense
  records_without_defense: 0 # records with no intended defense (open risk)
  residual_high_risk: 0     # records with residual_risk: high
  escapes_known_at_close: 0 # records where actual_catch_point is later than intended
  coverage_state: healthy | warning | depleted

records:
  - id: "HDL-{bead-id}-{CA-index}-{UCA-index}"
    bead_id: ""
    cynefin_domain: clear | complicated | complex | chaotic  # any domain — trigger is complex OR security_sensitive
    security_sensitive: true | false

    # === STPA core (seeded by safety-analyst) ===
    interface: 0               # STPA interface number from control structure
    controller: ""             # controller name from control structure
    control_action: ""         # what the controller does
    hazard: ""                 # what can go wrong

    unsafe_control_action:
      category: not_provided | wrong_timing_or_order | stopped_too_soon | applied_too_long
      scenario: ""             # specific UCA scenario

    safety_constraint: ""      # SC-NNN reference from safety-constraints.md, or null

    # === Defense mapping (enriched during Execute) ===
    intended_defenses:         # which layers SHOULD catch this
      - layer: L0 | L1 | L2 | L2_5 | L2_75
        mechanism: ""          # specific check/agent that should detect

    actual_catch_point:        # which layer DID catch this (null until caught or escaped)
      layer: null              # L0 | L1 | L2 | L2_5 | L2_75 | escaped | not_tested
      source: ""               # agent or script that detected
      artifact_ref: ""         # path to finding/bead file
      finding_ref: null        # specific finding ID if from AQS

    # === Latent condition trace (enriched by latent-condition-tracer) ===
    latent_condition_trace:
      source_layer: null       # which loop level harbored the latent condition
      source_reason: ""        # why the condition existed
      artifact_ref: ""         # path to decision trace or bead file

    # === Resolution ===
    status: open | caught | escaped | accepted_residual
    residual_risk: low | medium | high
    owner: ""                  # Conductor or specific agent
    notes: ""
```

---

## Canonical Unit of Record

One record per `bead + control_action + UCA scenario`.

**Record ID format:** `HDL-{bead-id}-CA{ca-index}-UCA{uca-index}`

Example: `HDL-B03-CA1-UCA2`

This grain is correct because:
- `safety-analyst` already produces control actions and UCAs at this level
- AQS probes UCAs individually
- Defenses and catch points are meaningful at the UCA level
- Repeated-pattern analysis becomes possible across tasks via UCA fingerprinting

---

## safety-analyst Output Contract (`stpa-analysis.yaml`)

**Path:** `docs/sdlc/active/{task-id}/stpa-analysis.yaml`

This is the structured intermediate artifact produced by `safety-analyst`. It is the input to the seeding script. The agent MUST produce structured YAML — not prose.

```yaml
schema_version: 1
task_id: ""
beads_analyzed:
  - bead_id: ""
    cynefin_domain: ""
    security_sensitive: false
    control_actions:
      - interface: 0
        controller: ""
        action: ""
        hazard: ""
        ucas:
          - category: not_provided | wrong_timing_or_order | stopped_too_soon | applied_too_long
            scenario: ""
            safety_constraint: ""  # SC-NNN or null
            suggested_defenses:
              - layer: L0 | L1 | L2 | L2_5 | L2_75
                mechanism: ""
```

The seeding script (`scripts/seed-hazard-defense-ledger.sh`) reads this output and produces `hazard-defense-ledger.yaml` with one HDL record per bead + control_action + UCA combination. For each record:

- STPA core fields populated from the analysis
- `safety_constraint` cross-referenced from the analysis
- `intended_defenses` seeded from `suggested_defenses`
- `status: open`
- `actual_catch_point: null`

---

## coverage_state Derivation Algorithm

`coverage_state` is a derived field — never hand-edited. It is computed from summary counters:

```
IF records_without_defense > 0 AND any undefended record has residual_risk: high:
  coverage_state = "depleted"
ELSE IF records_without_defense > 0 OR escapes_known_at_close > 0:
  coverage_state = "warning"
ELSE IF all records have status caught or accepted_residual:
  coverage_state = "healthy"
ELSE:
  coverage_state = "warning"  # open records remain
```

### Derived Summary Fields

All `summary.*` fields are derived — never hand-edited:

| Field | Source |
|-------|--------|
| `summary.qualifying_beads` | Count of beads with `cynefin_domain: complex` or `security_sensitive: true` |
| `summary.records_total` | Count of records in `records` array |
| `summary.records_with_defense` | Records where `intended_defenses` is non-empty |
| `summary.records_without_defense` | Records where `intended_defenses` is empty |
| `summary.residual_high_risk` | Records with `residual_risk: high` |
| `summary.escapes_known_at_close` | Records with `status: escaped` |
| `summary.coverage_state` | Algorithm above |

### Human-Provided Fields

| Field | When |
|-------|------|
| `residual_risk` | Conductor assessment after all defenses tested |
| `owner` | Conductor assignment |
| `notes` | Justification for accepted_residual, escape explanation |
| `status: accepted_residual` | Explicit Conductor decision |

---

## System Ledger JSONL Schema

### Primary (`docs/sdlc/system-hazard-defense.jsonl`)

One immutable line per completed task. Appended by `scripts/append-system-hazard-defense.sh` at Complete gate.

```jsonl
{"task_id":"","date":"","qualifying_beads":0,"records_total":0,"records_with_defense":0,"records_without_defense":0,"catch_layer_distribution":{"L0":0,"L1":0,"L2":0,"L2_5":0,"L2_75":0,"escaped":0},"escapes_at_close":0,"residual_high_risk":0,"repeated_uca_fingerprints":[],"coverage_state":"healthy"}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Task identifier |
| `date` | string | ISO 8601 UTC timestamp of completion |
| `qualifying_beads` | integer | Beads that triggered STPA |
| `records_total` | integer | Total HDL records |
| `records_with_defense` | integer | Records with at least one intended defense |
| `records_without_defense` | integer | Records with no intended defense |
| `catch_layer_distribution` | object | Count of catches per defense layer |
| `escapes_at_close` | integer | Records with status escaped at task close |
| `residual_high_risk` | integer | Records with residual_risk high |
| `repeated_uca_fingerprints` | array | UCA fingerprints matching prior tasks (Phase 3+ population) |
| `coverage_state` | string | healthy / warning / depleted |

### Events (`docs/sdlc/system-hazard-defense-events.jsonl`)

Late-arriving corrections appended after task completion:

```jsonl
{"task_id":"","event":"escape_confirmed|defense_reclassified|repeated_uca_cluster|residual_risk_change","date":"","details":""}
```

**Event types:**

| Event | Trigger |
|-------|---------|
| `escape_confirmed` | A UCA escape confirmed post-close |
| `defense_reclassified` | Intended defense layer reassigned |
| `repeated_uca_cluster` | Pattern match found across tasks |
| `residual_risk_change` | Residual risk level revised |

---

## Phase Gate Requirements

### STPA Trigger Rule

A bead qualifies for STPA if:
- `cynefin_domain` is `complex`, OR
- `security_sensitive: true`

### Pre-Execute Gate (seeded)

For every qualifying bead:
- `hazard-defense-ledger.yaml` must exist with `artifact_status: seeded`
- At least one record must exist for each qualifying bead
- Record-level existence is checked, not just task-level file existence

### Synthesize Gate (active)

- `artifact_status` must be `active` or higher
- No record may have `status: open` unless explicitly justified
- `summary.records_without_defense` must be 0, or each undefended record must have `status: accepted_residual` with a non-empty `notes` field

### Complete Gate (final)

- `artifact_status` must be `final`
- Every record must have `status` in {caught, escaped, accepted_residual} — no `open` records
- System ledger entry appended to `docs/sdlc/system-hazard-defense.jsonl`

### Lifecycle Summary

```
Architect/pre-Execute  →  artifact_status: seeded
       ↓                  (safety-analyst → seed script)
    Execute            →  artifact_status: active
       ↓                  (AQS / LOSA / tracer enrich records)
  Synthesize           →  no open records
       ↓
   Complete            →  artifact_status: final
                          system ledger appended
```

---

## Bead Projection Rules

Bead fields are summaries derived from the ledger — not the source of truth. After the ledger is seeded, a projection step writes compact summaries to bead files.

| Bead field | Projection from ledger |
|------------|----------------------|
| `Control actions` | Distinct `control_action` values for records matching this `bead_id` |
| `Unsafe control actions` | UCA summaries: `[control_action] — [category] — [scenario]` for this `bead_id` |
| `Latent condition trace` | Compact ref: `See hazard-defense-ledger.yaml HDL-{bead-id}-*` + summary of latent conditions found |

This preserves local usability in the bead file without duplicating the canonical data model.

---

## Defense Layer Reference

| Layer | Description |
|-------|-------------|
| `L0` | Pre-commit / static checks (deterministic, fast) |
| `L1` | CI pipeline automated checks |
| `L2` | Adversarial / red-team probes (AQS) |
| `L2_5` | LOSA post-merge observation |
| `L2_75` | Process drift monitor / longitudinal signal |
| `escaped` | No layer caught the UCA |
| `not_tested` | Defense not exercised in this task |

---

## Related Artifacts

| File | Role |
|------|------|
| `docs/specs/2026-03-29-hazard-defense-ledger-design.md` | Authoritative design spec |
| `references/stpa-control-structure.md` | STPA interface and controller definitions |
| `references/safety-constraints.md` | SC-NNN constraint registry (safety_constraint field source) |
| `references/artifact-templates.md` | Task artifact table (hazard-defense-ledger.yaml entry) |
| `scripts/lib/hazard-defense-lib.sh` | Shared helpers: record ID gen, summary derivation, coverage_state |
| `scripts/seed-hazard-defense-ledger.sh` | Reads stpa-analysis.yaml → creates seeded ledger |
| `scripts/derive-hazard-defense-summary.sh` | Recomputes summary fields from records array |
| `scripts/append-system-hazard-defense.sh` | Reads final ledger → appends to system JSONL |
| `hooks/scripts/validate-hazard-defense-ledger.sh` | PostToolUse hook: validates ledger on Write/Edit |
| `agents/safety-analyst.md` | Agent that produces stpa-analysis.yaml |
| `agents/latent-condition-tracer.md` | Agent that populates latent_condition_trace |
| `skills/sdlc-adversarial/SKILL.md` | AQS probe selection reads from ledger records |
