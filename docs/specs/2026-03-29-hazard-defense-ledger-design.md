# Hazard/Defense Ledger — Phase 2 of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-29
**Status:** Draft
**Roadmap position:** Phase 2 of 5 (Quality Budget [DONE] → **Hazard/Defense Ledger** → Stressor Harvesting → Decision-Noise Controls → Mode/Convergence Signals)
**Depends on:** Phase 1 (quality-budget.yaml, derivation scripts, system ledger pattern)

---

## Problem Statement

Phase B of the SDLC safety control layer exists in pieces but not as an auditable control loop.

The SDLC already has:
- A system STPA reference (`references/stpa-control-structure.md`)
- A `safety-analyst` agent that derives control actions and UCAs for COMPLEX and security_sensitive beads
- Bead fields for `Control actions`, `Unsafe control actions`, and `Latent condition trace` explicitly reserved for Phase B (`skills/sdlc-orchestrate/SKILL.md:120`)
- Downstream consumers that expect STPA output, especially AQS probe selection (`skills/sdlc-adversarial/SKILL.md:96`)

What is missing is a canonical artifact that links all of that into one machine-readable record.

Safety information is currently fragmented across bead fields, decision traces, AQS findings, LOSA/calibration outcomes, latent-condition tracing, and safety/drift agents. This fragmentation creates four operational failures:

1. STPA output is not durable or queryable across a task
2. No single record says: hazard → control action → UCA → intended defense → actual catch point → residual risk
3. Cannot measure defense coverage, repeated UCA patterns, or drift of catches outward from earlier to later layers
4. Phase B fields can be populated narratively without becoming enforceable telemetry

### Goal

Make safety control analysis a first-class, machine-readable, derived-first artifact that turns STPA from annotation into workflow control. For every STPA-required bead, the system should answer:
- What hazards and UCAs were identified?
- Which defense layer was supposed to catch each one?
- Which layer actually caught it?
- Which UCAs had no defense?
- Which patterns are repeating across tasks?

### Design Principle

The Hazard/Defense Ledger IS Phase B — not a parallel side artifact. Bead fields become projections of the ledger, not the source of truth. One safety data model, not two competing ones.

---

## Thinker Connections

| Thinker | What the ledger operationalizes |
|---------|--------------------------------|
| **Leveson (STPA/STAMP)** | UCAs become first-class tracked records. Control action → UCA → defense → catch point is the STPA loop made auditable. |
| **Reason (Swiss Cheese)** | Defense layers become measurable: intended vs actual catch point reveals which cheese slices have holes. Coverage metric = slice integrity. |
| **Dekker (Drift/Just Culture)** | Repeated UCA patterns across tasks = normalization of deviance. Catch-layer distribution shifting outward = drift into failure. |
| **Deming** | Catch-layer distribution over time feeds control charts. Defense coverage is an SLI. |
| **Meadows** | Defense layers are system buffers. Buffer hits (escapes past intended defense) are stock-flow signals. |

---

## Schema

### Task Ledger (`docs/sdlc/active/{task-id}/hazard-defense-ledger.yaml`)

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
  qualifying_beads: 0       # beads that triggered STPA (COMPLEX or security_sensitive)
  records_total: 0          # total HDL records across all qualifying beads
  records_with_defense: 0   # records with at least one intended_defense
  records_without_defense: 0 # records with no intended defense (open risk)
  residual_high_risk: 0     # records with residual_risk: high
  escapes_known_at_close: 0 # records where actual_catch_point is later than intended
  coverage_state: healthy | warning | depleted

records:
  - id: "HDL-{bead-id}-{CA-index}-{UCA-index}"
    bead_id: ""
    cynefin_domain: complex | chaotic
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

### Canonical Unit of Record

One record per `bead + control_action + UCA scenario`. This is the right grain because:
- `safety-analyst` already produces control actions and UCAs at this level
- AQS probes UCAs
- Defenses and catch points are meaningful at the UCA level
- Repeated-pattern analysis becomes possible across tasks via UCA fingerprinting

### coverage_state Derivation

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

---

## Lifecycle

### Seeded (Architect / pre-Execute)

`safety-analyst` runs STPA analysis for qualifying beads (COMPLEX or security_sensitive). For each control action + UCA pair, creates a ledger record with:
- STPA core fields populated (interface, controller, control_action, hazard, UCA)
- `safety_constraint` cross-referenced from `references/safety-constraints.md`
- `intended_defenses` seeded based on UCA category and existing defense layer mapping
- `status: open`
- `actual_catch_point: null`

### Active (Execute)

Records are enriched by:
- **AQS findings:** When a red team probe catches a UCA-related issue, the matching record's `actual_catch_point` is populated with the AQS layer and finding reference
- **LOSA observations:** Post-merge catch confirmations populate `actual_catch_point` for records that escaped inner layers
- **Latent-condition-tracer:** Populates `latent_condition_trace` with root cause analysis
- **Decision trace updates:** Conductor updates `intended_defenses` if defense strategy changes during execution
- **Runner/sentinel catches:** L0/L1 catches populate `actual_catch_point` at the relevant layer

### Final (Synthesize / Complete)

Every record must be resolved:
- `caught`: defense worked, catch point recorded
- `escaped`: no defense caught it — requires explanation and owner
- `accepted_residual`: explicitly accepted with justification in `notes`
- No record may remain `open`

---

## Derivation Model

### Derived fields (never hand-edited)

| Field | Source |
|-------|--------|
| `summary.qualifying_beads` | Count of beads with `cynefin_domain: complex/chaotic` or `security_sensitive: true` |
| `summary.records_total` | Count of records in `records` array |
| `summary.records_with_defense` | Records where `intended_defenses` is non-empty |
| `summary.records_without_defense` | Records where `intended_defenses` is empty |
| `summary.residual_high_risk` | Records with `residual_risk: high` |
| `summary.escapes_known_at_close` | Records with `status: escaped` |
| `summary.coverage_state` | Derivation algorithm above |

### Human-provided fields

| Field | When |
|-------|------|
| `residual_risk` | Conductor assessment after all defenses tested |
| `owner` | Conductor assignment |
| `notes` | Justification for accepted_residual, escape explanation |
| `status: accepted_residual` | Explicit Conductor decision |

---

## Bead Projection Rules

Existing bead fields become summaries/references from the ledger, not the source of truth:

| Bead field | Projection from ledger |
|------------|----------------------|
| `Control actions` | Distinct `control_action` values for records matching this bead_id |
| `Unsafe control actions` | UCA summaries: `[control_action] — [category] — [scenario]` for this bead_id |
| `Latent condition trace` | Compact ref: `See hazard-defense-ledger.yaml HDL-{bead-id}-*` + summary of latent conditions found |

This preserves local usability in the bead file without duplicating the canonical data model.

---

## Phase Gates

### Pre-Execute Gate (STPA-required beads only)

For beads where `cynefin_domain` is COMPLEX or `security_sensitive` is true:
- `hazard-defense-ledger.yaml` must exist with `artifact_status: seeded`
- At least one record must exist for each qualifying bead

### Synthesize Gate

- `artifact_status` must be `active` or higher
- No record may have `status: open` unless explicitly justified
- `summary.records_without_defense` must be 0, or each undefended record must have `status: accepted_residual` with a non-empty `notes` field

### Complete Gate

- `artifact_status` must be `final`
- Every record must have `status` in {caught, escaped, accepted_residual} — no `open` records
- System ledger entry appended

---

## System Ledger

### Primary (`docs/sdlc/system-hazard-defense.jsonl`)

One immutable line per completed task:

```jsonl
{"task_id":"","date":"","qualifying_beads":0,"records_total":0,"records_with_defense":0,"records_without_defense":0,"catch_layer_distribution":{"L0":0,"L1":0,"L2":0,"L2_5":0,"L2_75":0,"escaped":0},"escapes_at_close":0,"residual_high_risk":0,"repeated_uca_fingerprints":[],"coverage_state":"healthy"}
```

### Events (`docs/sdlc/system-hazard-defense-events.jsonl`)

Late-arriving corrections:

```jsonl
{"task_id":"","event":"escape_confirmed|defense_reclassified|repeated_uca_cluster|residual_risk_change","date":"","details":""}
```

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/lib/hazard-defense-lib.sh` | Shared helpers: record ID generation, summary derivation, coverage_state computation |
| `scripts/seed-hazard-defense-ledger.sh` | Reads safety-analyst output → creates seeded hazard-defense-ledger.yaml |
| `scripts/derive-hazard-defense-summary.sh` | Recomputes summary fields from records array |
| `scripts/append-system-hazard-defense.sh` | Reads final ledger → appends to system-hazard-defense.jsonl |
| `references/hazard-defense-schema.md` | Canonical schema documentation |
| `hooks/scripts/validate-hazard-defense-ledger.sh` | PostToolUse hook: validates ledger structure on Write/Edit |
| `hooks/tests/fixtures/hdl-valid/hazard-defense-ledger.yaml` | Test fixture: valid ledger |
| `hooks/tests/fixtures/hdl-missing/hazard-defense-ledger.yaml` | Test fixture: missing required fields |
| `hooks/tests/fixtures/hdl-malformed/hazard-defense-ledger.yaml` | Test fixture: invalid YAML |

### Files to Modify

| File | Change |
|------|--------|
| `skills/sdlc-orchestrate/SKILL.md:120-122` | Replace "Phase B — not yet populated" placeholders with projection rules from ledger |
| `skills/sdlc-orchestrate/SKILL.md:195` | Add ledger seeding step after safety-analyst dispatch in Architect |
| `skills/sdlc-orchestrate/SKILL.md:394` | Add REPAIR profile ledger seeding in pre-Execute mini-Architect |
| `skills/sdlc-orchestrate/SKILL.md` (artifact list) | Add hazard-defense-ledger.yaml + system ledger artifacts |
| `skills/sdlc-orchestrate/SKILL.md` (Synthesize/Complete) | Add HDL gate checks |
| `agents/safety-analyst.md:70-71` | Update output format to produce ledger-compatible records instead of bead-only fields |
| `agents/latent-condition-tracer.md:61` | Update to write to ledger record's latent_condition_trace, not just bead field |
| `agents/process-drift-monitor.md:113-115` | Replace Phase B field checks with ledger existence/staleness checks; consume system-hazard-defense.jsonl |
| `agents/losa-observer.md` | Add escape reporting to system-hazard-defense-events.jsonl |
| `references/artifact-templates.md:30-32` | Replace Phase B placeholders with projection rules |
| `references/stpa-control-structure.md:4` | Update "Maintained per Phase B" note to reference hazard-defense-ledger.yaml; add ledger as telemetry artifact |
| `hooks/scripts/validate-decision-trace.sh:90-124` | Update Phase B enforcement to check ledger existence instead of raw bead field presence |
| `hooks/hooks.json` | Add validate-hazard-defense-ledger.sh PostToolUse hook |
| `hooks/tests/test-hooks.sh` | Add HDL validation test cases |
| `skills/sdlc-gate/SKILL.md` | Add hazard-defense-ledger checks for COMPLEX/security-sensitive transitions |
| `skills/sdlc-adversarial/SKILL.md:96` | Update AQS probe selection to read from ledger records instead of bead UCA fields |
| `README.md` | Add hazard-defense-ledger artifacts to table; update hook count |

### Files Unchanged but Consuming

| File | Consumes |
|------|----------|
| `agents/safety-constraints-guardian.md` | Cross-references safety_constraint field in ledger records |
| `references/safety-constraints.md` | Referenced by safety_constraint field; no changes needed |
| `references/quality-budget-rules.yaml` | coverage_state feeds into quality budget WARNING/DEPLETED thresholds (Phase 3+ consideration) |

---

## Scope Boundary

### In scope (Phase 2)

- Hazard/Defense Ledger schema (task + system)
- Seeding script from safety-analyst output
- Summary derivation script
- System ledger append script
- Shared helper library
- Validation hook + tests + fixtures
- Phase gate enforcement (pre-Execute, Synthesize, Complete)
- Bead field projection rules (replacing Phase B placeholders)
- All file modifications listed above

### Out of scope

- Automated UCA fingerprinting for cross-task pattern detection (Phase 3a candidate)
- Coverage_state feeding into quality budget thresholds (Phase 3+ integration)
- Visualization of defense-layer distribution
- Automated defense recommendation based on historical catch patterns
