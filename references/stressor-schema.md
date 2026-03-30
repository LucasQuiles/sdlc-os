# Stressor Harvesting — Schema Reference

Canonical schemas for all stressor harvesting artifacts. Source of truth for scripts,
hooks, and agent instructions. Derived from `docs/specs/2026-03-30-stressor-harvesting-design.md`.

---

## Stressor Library YAML (`references/stressor-library.yaml`)

Persistent, append-only, Lindy-weighted catalog. Grows from real failures via
`scripts/harvest-stressors.sh`. Updated by `scripts/update-stressor-library.sh`
after each stress session.

```yaml
schema_version: 1                          # int, must be 1
last_updated: "2026-03-30T00:00:00Z"       # ISO 8601, updated on every write

stressors:
  - id: "STR-001"                          # string, STR-NNN format, unique
    name: "state mutation ordering"         # short human-readable description
    category: concurrency                   # enum — see Category Values below
    source:
      type: escape                          # enum — see Source Type Values below
      task_id: "wizard-modal-rebuild-20260328"
      artifact_ref: "HDL-B03-CA1-UCA2"    # optional reference to source artifact
    description: |                         # full description of what the stressor does
      Apply state mutation before guard commit completes.
    probe_template: |                      # parameterized probe text; {target} is filled at apply time
      Verify that {target} handles the case where state mutation
      is applied before the guard state is fully committed.
    applicable_when:
      cynefin: [complex, complicated]      # cynefin domains where this stressor applies
      tags: [state_management, concurrent_access, modal_transitions]  # scope/content tags
    severity: high                         # enum: high | medium | low
    times_applied: 0                       # int, incremented by update-stressor-library.sh
    times_caught: 0                        # int, incremented when result == caught
    catch_rate: null                       # float [0.0,1.0] = times_caught/times_applied; null until first apply
    first_harvested: "2026-03-30T00:00:00Z"
    last_applied: null                     # ISO 8601 or null
    lindy_status: provisional              # enum — see Lindy Lifecycle below
```

### Category Values

| Value | Meaning |
|-------|---------|
| `concurrency` | Race conditions, ordering dependencies, parallel mutations |
| `boundary` | Edge cases at input/output limits, off-by-one, overflow |
| `state` | Unexpected state transitions, invalid state combinations |
| `auth` | Authentication/authorization gaps, privilege escalation paths |
| `input` | Malformed, adversarial, or unexpected input handling |
| `dependency` | External service failures, version mismatches, missing fallbacks |
| `context_gap` | Missing context that causes silent mis-interpretation |
| `defense_assumption` | Assumed defenses that do not actually exist or do not fire |

### Source Type Values

| Value | Meaning |
|-------|---------|
| `escape` | Found by a user or downstream system, not caught during SDLC |
| `aqs_finding` | Caught during Adversarial Quality Scrutiny |
| `losa_catch` | Caught during a Line-of-System-Assurance observation |
| `hdl_gap` | Derived from an open Unsafe Control Action in the Hazard/Defense Ledger |
| `premortem` | Generated during a premortem exercise |
| `calibration` | Planted as a calibration defect |

### Lindy Lifecycle Rules

```
                   ┌─────────────────────────────────────────────────────────────┐
                   │                     lindy_status                            │
                   │                                                             │
                   │  provisional ──────────────────────────────► established   │
                   │      │          times_applied >= 3                          │
                   │      │          AND catch_rate > 0                          │
                   │      │                                                      │
                   │      │                                      ┌── retired     │
                   │      │                                      │               │
                   │      ▼                                      │               │
                   │   retired ◄── times_applied >= 5           │               │
                   │               AND catch_rate == 0          │               │
                   │                                            │               │
                   │              established ──────────────────┘               │
                   │                   times_applied >= 10                      │
                   │                   AND last 5 applications all misses       │
                   └─────────────────────────────────────────────────────────────┘
```

Transition rules enforced by `scripts/update-stressor-library.sh`:

| From | To | Condition |
|------|----|-----------|
| `provisional` | `established` | `times_applied >= 3` AND `catch_rate > 0` |
| `provisional` | `retired` | `times_applied >= 5` AND `catch_rate == 0` |
| `established` | `retired` | `times_applied >= 10` AND catch_rate over last 5 applications == 0 |

A `provisional` stressor that never catches anything after 5 tries retires directly without becoming established. An `established` stressor requires a longer runway (10+ applications, last 5 all misses) before retirement — it has earned its authority.

---

## Stress Session YAML (`docs/sdlc/active/{task-id}/stress-session.yaml`)

Per-task stress session artifact. Created during Execute phase when FFT-15 returns
anything other than SKIP.

```yaml
schema_version: 1                    # int, must be 1
task_id: ""                          # string, matches task directory name
artifact_status: planned             # enum: planned | active | final
sampling_reason: hormetic            # enum — see Sampling Reason Values below
derived_at: "2026-03-30T00:00:00Z"  # ISO 8601, when session was created
last_updated: "2026-03-30T00:00:00Z"

selection:
  sampling_seed: 0.0                 # float [0,1), deterministic: sha256(task_id) → hex → float
  quality_budget_state: healthy      # enum: healthy | warning | depleted
  clean_streak_length: 0            # int, consecutive tasks with zero escapes
  complexity_weight: 0.0            # float, from quality-budget.yaml
  security_sensitive_beads: 0       # int, count of beads with security_sensitive: true
  hdl_open_ucas: 0                  # int, count of open UCAs from hazard-defense-ledger.yaml

stressors_applied:
  - stressor_id: "STR-001"         # references stressor-library.yaml id, or STR-NEW-NNN for ad hoc
    bead_id: "B03"                  # bead this stressor was applied against
    target: "modal state transition guard"  # filled-in value for probe_template {target}
    result: held                    # enum: caught | held | not_applicable
    catch_layer: null               # enum: L0 | L1 | L2 | L2_5 | L2_75 | escaped | null
    finding_ref: null               # reference to AQS finding, HDL entry, etc. — null if held
    notes: ""

harvest:
  new_stressors: []                 # list of STR-IDs added to library from this session
  new_hardening_recipes: []         # list of recipe IDs added to hardening patterns
  subtraction_candidates: []        # list of mechanism names flagged for removal
  constitution_rules: []            # list of code constitution rules proposed
  safety_rules: []                  # list of safety constraint rules proposed

subtraction_log:
  - mechanism: ""                   # name of the mechanism under review
    reason: ""                      # why it was flagged (redundant, brittle, over-specified)
    action: flagged_for_review      # enum: removed | simplified | flagged_for_review
    evidence: ""                    # reference to finding or session that surfaced this

summary:
  stressors_applied: 0             # int, count of stressors_applied entries
  stressors_caught: 0              # int, count with result == caught
  stressors_held: 0                # int, count with result == held
  new_stressors_harvested: 0       # int, len(harvest.new_stressors)
  subtraction_candidates: 0        # int, len(subtraction_log)
  stress_yield: 0.0                # float = stressors_caught / stressors_applied (0.0 if applied == 0)
```

### Sampling Reason Values (7 values)

| Value | FFT-15 Outcome | Trigger Condition |
|-------|----------------|-------------------|
| `budget_depleted` | FULL | `quality_budget.budget_state == depleted` — all beads get stress |
| `consequence_sensitive` | TARGETED | Any bead is `security_sensitive: true` AND `cynefin_domain: complex` |
| `budget_warning` | SAMPLED | `budget_state == warning`; sampling_seed < 0.50 |
| `anti_turkey` | ANTI_TURKEY | `clean_streak_length >= 5`; sampling_seed < 0.30 |
| `hormetic` | HORMETIC | Baseline 10% random; sampling_seed < 0.10 |
| `manual` | — | User-directed `/stress` command |
| `random_sample` | — | Deprecated alias — use `hormetic` or `anti_turkey` instead |

### `sampling_seed` Field

The `sampling_seed` is a deterministic float in `[0, 1)` derived from `sha256(task_id)`.

Derivation:
1. `hex = sha256(task_id)[0:8]`  (first 8 hex chars = 32 bits)
2. `seed = int(hex, 16) / 0xFFFFFFFF`

This ensures that the same task always gets the same sampling decision on reruns or
session resumes. The seed is recorded in `selection.sampling_seed` for audit. Implemented
in `scripts/lib/stressor-lib.sh:compute_sampling_seed`.

---

## System Stress Ledger JSONL (`docs/sdlc/system-stress.jsonl`)

Append-only. One JSON object per line, one line per completed stress session.
Written by `scripts/append-system-stress.sh`.

```jsonl
{
  "task_id": "",
  "date": "",
  "sampling_reason": "",
  "stressors_applied": 0,
  "stressors_caught": 0,
  "stress_yield": 0.0,
  "new_stressors_harvested": 0,
  "subtraction_candidates": 0,
  "clean_streak_at_sample": 0,
  "quality_budget_state": "",
  "complexity_weight": 0.0
}
```

Field notes:
- `stress_yield`: float, `stressors_caught / stressors_applied`; `0.0` when `stressors_applied == 0`
- `clean_streak_at_sample`: the `clean_streak_length` value recorded at sampling time
- `quality_budget_state`: value at sampling time, not at session close

---

## System Stress Events JSONL (`docs/sdlc/system-stress-events.jsonl`)

Append-only. One JSON object per line. Written by `scripts/update-stressor-library.sh`
when stressors are promoted, retired, or reclassified during library update.

```jsonl
{
  "stressor_id": "STR-001",
  "event": "promotion",
  "date": "",
  "details": "",
  "task_id": ""
}
```

### Event Types

| `event` Value | Trigger |
|---------------|---------|
| `promotion` | Stressor moved from `provisional` to `established` (`times_applied >= 3`, `catch_rate > 0`) |
| `retirement` | Stressor moved to `retired` (provisional never caught after 5 tries, or established gone stale after 10+ with last 5 all misses) |
| `catch_rate_update` | Significant catch_rate change: delta > 20% from previous value |
| `reclassified` | Severity or category changed based on new evidence |

---

## FFT-15: Stress Sampling Decision Tree

6-cue fast-and-frugal tree. Deterministic for reproducible probabilistic cues.

```
Cue 1: Is profile INVESTIGATE or EVOLVE?
  → YES → SKIP stress
  → NO  → continue

Cue 2: Is quality_budget.budget_state DEPLETED?
  → YES → FULL stress (all beads)
  → NO  → continue

Cue 3: Does any bead have security_sensitive AND cynefin complex?
  → YES → TARGETED stress (those beads only)
  → NO  → continue

Cue 4: Is budget_state WARNING?
  → YES → SAMPLED if sampling_seed < 0.50, else SKIP
  → NO  → continue

Cue 5: Is clean_streak_length >= 5?
  → YES → ANTI_TURKEY if sampling_seed < 0.30, else SKIP
  → NO  → continue

Cue 6: sampling_seed < 0.10?
  → YES → HORMETIC (1–2 beads, random selection)
  → NO  → SKIP stress
```

Outcomes: `FULL` | `TARGETED` | `SAMPLED` | `ANTI_TURKEY` | `HORMETIC` | `SKIP`

Deterministic seed: `sha256(task_id)` first 8 hex chars → integer → divided by `0xFFFFFFFF` → float in `[0, 1)`. Recorded in `stress-session.yaml:selection.sampling_seed`.

Implementation: `scripts/lib/stressor-lib.sh:evaluate_fft15(budget_state, clean_streak, has_complex_security, profile, seed)`

**Never stressed:** INVESTIGATE (read-only) and EVOLVE (system improvement) profiles always SKIP.

**Anti-turkey rationale:** A long clean streak is not evidence of quality — it may mean that stressors stopped, not that the system improved. Suspicion increases with streak length (Turkey problem, Taleb).

---

## Stress Pipeline — 6-Step Reference

| Step | Name | Description | Script |
|------|------|-------------|--------|
| 1 | **Select** | Match library stressors to bead by `applicable_when.cynefin` and `applicable_when.tags`. Prefer `established` over `provisional`. Include at least one `provisional` if available. Derive additional stressors from open UCAs in HDL if present. | `scripts/select-stressors.sh` |
| 2 | **Apply** | For each stressor + bead pair, fill `probe_template` with target and dispatch as a guppy probe (Haiku) during AQS, or as a directed Sonnet strike for `severity: high`. Record result in `stressors_applied`. | `skills/sdlc-adversarial` |
| 3 | **Observe** | Classify each application result: `caught` (real issue found, record `catch_layer` and `finding_ref`), `held` (defense worked, stressor found nothing), `not_applicable` (stressor did not fit context, do not count). | Conductor review |
| 4 | **Harvest** | Extract findings that do not match any existing stressor as new stressor candidates with `lindy_status: provisional`. Identify recurring patterns as hardening recipes. Propose `constitution_rules` and `safety_rules` for `severity: high` findings. | `scripts/harvest-stressors.sh` |
| 5 | **Subtract** | Via-negativa step. For each stressor application, ask: was any mechanism redundant, brittle, or over-specified? Record candidates in `subtraction_log`. After 3 independent sessions flag the same mechanism, escalate to Evolve for formal removal review. | Conductor review |
| 6 | **Update Library** | Increment `times_applied` and `times_caught`. Recompute `catch_rate`. Evaluate Lindy transitions (see lifecycle rules). Emit promotion/retirement events to `system-stress-events.jsonl`. | `scripts/update-stressor-library.sh` |

---

## Via-Negativa Subtraction Log Format

The `subtraction_log` array in `stress-session.yaml` records mechanisms flagged for
removal during Step 5. Each entry:

```yaml
subtraction_log:
  - mechanism: "triple-null guard on already-validated input"
    reason: "redundant — L1 hook catches this before it reaches L2; adds complexity without catching anything"
    action: flagged_for_review    # enum: removed | simplified | flagged_for_review
    evidence: "AQS-042 — stressor STR-003 applied 5 times, held every time at L1, this guard never fired"
```

### Action Values

| Value | Meaning |
|-------|---------|
| `removed` | Mechanism has already been removed in this session |
| `simplified` | Mechanism was simplified (not fully removed) in this session |
| `flagged_for_review` | Candidate for removal — needs Conductor sign-off or further evidence |

### Escalation Rule

When 3 or more independent stress sessions record the same `mechanism` in their
`subtraction_log`, the Evolve skill escalates it to a formal removal proposal. The
`system-stress.jsonl` entries for those sessions provide the cross-session evidence.
`subtraction_candidates` from `system-stress-events.jsonl` feed the Evolve skill's
subtraction review evolution bead type.

---

## Related Files

| File | Role |
|------|------|
| `references/stressor-library.yaml` | Live stressor catalog |
| `docs/sdlc/system-stress.jsonl` | Cross-task stress session ledger |
| `docs/sdlc/system-stress-events.jsonl` | Stressor lifecycle events |
| `docs/sdlc/active/{task-id}/stress-session.yaml` | Per-task stress artifact |
| `scripts/lib/stressor-lib.sh` | Shared helpers (seed, FFT-15, yield, Lindy) |
| `scripts/select-stressors.sh` | Step 1: stressor selection |
| `scripts/harvest-stressors.sh` | Step 4: new stressor extraction |
| `scripts/update-stressor-library.sh` | Step 6: library update + events |
| `scripts/append-system-stress.sh` | Appends to system-stress.jsonl |
| `hooks/scripts/validate-stress-session.sh` | PostToolUse validation hook |
| `references/fft-decision-trees.md` | FFT-15 full definition (authoritative) |
