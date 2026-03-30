# Quality Budget Schema Reference

Canonical schema definition for quality budget artifacts. See `references/quality-budget-rules.yaml` for externalized thresholds.

---

## Task Budget (`docs/sdlc/active/{task-id}/quality-budget.yaml`)

YAML file, derivation-first. Created during Execute (`partial`), promoted to `ready` before Synthesize, `final` after Synthesize.

### Fields

| Field | Type | Derived from | When updated |
|-------|------|-------------|-------------|
| `schema_version` | int | Constant: 1 | Creation |
| `task_id` | string | Task directory name | Creation |
| `artifact_status` | enum: partial, ready, final | Phase lifecycle | Each phase transition |
| `budget_state` | enum: healthy, warning, depleted | Derivation algorithm (see below) | Each derivation run |
| `derived_at` | UTC ISO 8601 | System clock | Each derivation run |
| `last_updated` | UTC ISO 8601 | System clock | Any update |

### cynefin_mix

| Field | Type | Derived from |
|-------|------|-------------|
| `clear` | int | Count of beads with `Cynefin domain: clear` |
| `complicated` | int | Count of beads with `Cynefin domain: complicated` |
| `complex` | int | Count of beads with `Cynefin domain: complex` |
| `chaotic` | int | Count of beads with `Cynefin domain: chaotic` |

`complexity_weight = (clear * 0 + complicated * 0.5 + complex * 1.0 + chaotic * 1.5) / total_beads`

### beads

| Field | Type | Derived from |
|-------|------|-------------|
| `total` | int | Count of all bead files in `beads/*.md` |
| `completed` | int | Beads with terminal status (merged, hardened, reliability-proven, verified, proven) |
| `wip` | int | Beads with status running or submitted |
| `stuck` | int | Beads with status stuck |
| `blocked` | int | Beads with status blocked |
| `wip_age_max_s` | int (seconds) | Longest-running WIP bead (wall clock since `Dispatched at`) |

### corrections

| Field | Type | Derived from |
|-------|------|-------------|
| `L0` | int | Sum of `Turbulence.L0` across all beads |
| `L1` | int | Sum of `Turbulence.L1` across all beads |
| `L2` | int | Sum of `Turbulence.L2` across all beads |
| `L2_5` | int | Sum of `Turbulence.L2.5` across all beads |
| `L2_75` | int | Sum of `Turbulence.L2.75` across all beads |

`turbulence_sum = L0 + L1 + L2 + L2_5 + L2_75`

`turbulence_max_bead` = bead ID with highest individual turbulence sum.

### metrics

#### Gating metrics (budget_state depends on these in v1)

| Metric | Formula | Denominator | Numerator | Eligibility |
|--------|---------|-------------|-----------|-------------|
| `zero_turbulence_rate` | `count(zero) / completed` | All completed beads | Completed beads with `turbulence_sum == 0` | Stuck/blocked before completion excluded |
| `turbulence_sum_per_bead` | `turbulence_sum / completed` | `beads.completed` | `turbulence_sum` | Null when completed == 0 |

#### Observed metrics (recorded, not gated in v1)

| Metric | Formula | Denominator | Numerator | Eligibility |
|--------|---------|-------------|-----------|-------------|
| `review_pass_rate` | `count(L1==0) / eligible` | Completed beads that reached L1 | Beads with `turbulence.L1 == 0` among eligible | Excludes Clear beads that skip L1 under healthy budget (per orchestrate SKILL.md skip-condition) |
| `queue_depth_peak` | max(concurrent WIP) | — | — | All beads |
| `buffer_hits` | count(queue_depth >= capacity) | — | — | During task lifetime |
| `review_latency_avg_s` | mean(review_started_at - submitted_at) | All reviewed beads | — | Seconds |
| `review_latency_p95_s` | p95(review_started_at - submitted_at) | All reviewed beads | — | Seconds |

### timing

| Field | Type | Notes |
|-------|------|-------|
| `estimate_s` | int or null | Optional in v1; required from v2 onward. Seconds. |
| `actual_s` | int or null | Wall clock from task init to Synthesize completion. Seconds. |

### sli_readings

Populated during Synthesize phase. Null while `artifact_status` is `partial` or `ready`.

| Field | Type | Source |
|-------|------|--------|
| `lint_clean` | bool | Deterministic lint check |
| `types_clean` | bool | Deterministic type check |
| `test_coverage_delta` | float | Percentage points vs baseline |
| `complexity_delta` | float | Cyclomatic complexity vs baseline |
| `critical_findings` | int | Count of critical-severity findings |

### escapes

| Field | Type | Notes |
|-------|------|-------|
| `known_at_close` | int | Defect escapes confirmed before Complete |

### overrides / notes

Human-provided only. `overrides` is a list of `{field, value, reason}` objects for manual budget_state adjustments. `notes` is free text.

---

## budget_state Derivation Algorithm

```
1. Compute complexity_weight from cynefin_mix
2. Look up thresholds from quality-budget-rules.yaml:
   - Find first complexity_threshold where complexity_weight <= max_weight
   - Extract healthy_floor and depleted_floor

3. Check hard-stop invariants (from rules file):
   - IF any hard_stop is true:
     - budget_state = "depleted" if critical_findings > 0 or beads.stuck > 0
     - budget_state = "warning" otherwise
     - STOP

4. Check gating metrics:
   - IF zero_turbulence_rate >= healthy_floor AND escapes.known_at_close == 0:
     - budget_state = "healthy"
   - ELSE IF zero_turbulence_rate < depleted_floor
            OR escapes.known_at_close > 1
            OR turbulence_sum > 6 * beads.completed:
     - budget_state = "depleted"
   - ELSE:
     - budget_state = "warning"
```

---

## System Budget (`docs/sdlc/system-budget.jsonl`)

Append-only JSONL. One line per completed task. Immutable after write.

### Entry schema

```jsonl
{"task_id":"<string>","date":"<UTC ISO 8601>","beads":<int>,"cynefin_mix":{"clear":<int>,"complicated":<int>,"complex":<int>,"chaotic":<int>},"complexity_weight":<float>,"turbulence_sum":<int>,"zero_turbulence_rate":<float>,"review_pass_rate":<float>,"L0":<int>,"L1":<int>,"L2":<int>,"L2_5":<int>,"L2_75":<int>,"escapes_at_close":<int>,"estimate_s":<int|null>,"actual_s":<int|null>,"latency_avg_s":<int>,"latency_p95_s":<int>,"queue_peak":<int>,"buffer_hits":<int>,"budget_state":"<healthy|warning|depleted>"}
```

### System budget_state derivation

Rolling window: last 10 tasks or 30 days (whichever is smaller), per `quality-budget-rules.yaml`.

| Condition | State |
|-----------|-------|
| Rolling `zero_turbulence_rate >= 0.70` AND `sum(escapes_at_close) == 0` in last 3 tasks | healthy |
| Below healthy OR `sum(escapes_at_close) > 0` in last 3 tasks | warning |
| Rolling `zero_turbulence_rate < 0.50` OR `sum(escapes_at_close) > 1` in last 3 OR 2+ tasks with `turbulence_sum > 6 * beads` | depleted |

---

## System Budget Events (`docs/sdlc/system-budget-events.jsonl`)

Late-arriving corrections. Keyed by task_id.

```jsonl
{"task_id":"<string>","event":"escape_confirmed","date":"<UTC ISO 8601>","escape_count":<int>,"source":"losa","finding_id":"<string>"}
```

Consumers merge primary + events when computing rolling window.

---

## Phase Gates

### Synthesize Gate

Task cannot transition to Synthesize unless:
1. `quality-budget.yaml` exists
2. Parses as valid YAML with `schema_version: 1`
3. `artifact_status` is `ready`
4. All derived fields non-null (except `estimate_s` in v1, `sli_readings.*`)
5. No hard-stop invariants violated

### Complete Gate

Task cannot transition to Complete unless:
1. `artifact_status` is `final`
2. `sli_readings` fully populated
3. `budget_state` computed with hard-stops applied
4. System ledger entry appended

---

## Source

- Design spec: `docs/specs/2026-03-29-quality-budget-enforcement-design.md`
- Threshold rules: `references/quality-budget-rules.yaml`
- Derivation script: `scripts/derive-quality-budget.sh`
- System append script: `scripts/append-system-budget.sh`
- Shared library: `scripts/lib/quality-budget-lib.sh`
- Validation hook: `hooks/scripts/validate-quality-budget.sh`
