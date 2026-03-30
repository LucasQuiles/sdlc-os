# Mode & Convergence Schema

**Version:** 1
**Rules file:** `references/mode-convergence-rules.yaml` (single source of truth for all thresholds, enums, and derivation parameters)
**Design spec:** `docs/specs/2026-03-30-mode-convergence-signals-design.md`

---

## Escalation Reason Enum

Structured category attached to every loop escalation. All valid values are defined in `references/mode-convergence-rules.yaml:escalation_reasons`.

| Value | Description |
|-------|-------------|
| `ambiguity` | Spec or requirements are unclear — the runner cannot determine the correct behavior |
| `coupling` | Bead scope crosses too many system boundaries; changes in one place cascade unexpectedly |
| `statefulness` | Complex state management that the runner cannot fully reason about within context |
| `concurrency` | Race conditions, ordering dependencies, or parallelism issues that require deeper analysis |
| `reviewer_overload` | Too many findings for the blue team to process in one cycle; signal to decompose |
| `missing_precedent` | No prior case or established pattern guides the decision |
| `domain_gap` | Runner lacks the domain expertise required to complete this bead correctly |
| `tooling_limitation` | A deterministic check is needed but the required tool is unavailable |
| `decomposition_error` | Bead is too large, too entangled, or incorrectly scoped at decomposition time |
| `context_exhaustion` | Runner ran out of context window before completing the bead |

---

## Convergence Signal Schema

Attached to bead correction signals and AQS cycle transitions. All threshold values are read from `references/mode-convergence-rules.yaml`.

```yaml
convergence_signal:
  cycle: 1                    # which loop iteration (integer, 1-indexed)
  new_findings: 3             # findings not seen in prior cycles (integer >= 0)
  repeated_findings: 1        # findings that restate prior cycle content (integer >= 0)
  evidence_rate: 0.75         # new_findings / (new_findings + repeated_findings); 0.0 if no findings
  severity_trend: declining | stable | escalating
  entropy_estimate: 2.1       # Shannon entropy of finding categories this cycle (float >= 0)
  convergence_state: converging | stable | diverging | stuck
  recommendation: continue | stop_early | extend_budget | change_approach
```

### severity_trend Derivation

Compare the maximum finding severity in the current cycle vs the prior cycle. Severity ordinal (from `references/mode-convergence-rules.yaml:convergence.severity_ordinal`): P4=1, P3=2, P2=3, P1=4.

```
IF no prior cycle exists:
  severity_trend = stable
ELSE IF max_severity_ordinal(current) > max_severity_ordinal(prior):
  severity_trend = escalating
ELSE IF max_severity_ordinal(current) < max_severity_ordinal(prior):
  severity_trend = declining
ELSE:
  severity_trend = stable
```

For AQS cycles: compare across the full finding set per cycle (all domains). For L0-L2 loops: compare the correction signal severity across iterations.

### convergence_state Derivation

Four states. The `stuck` state requires both low evidence rate AND low entropy — this distinguishes a loop stuck on the same problem class from one that has genuinely exhausted the search space. Thresholds are read from `references/mode-convergence-rules.yaml:convergence`.

```
IF evidence_rate >= convergence.evidence_rate_converging (0.50)
   AND severity_trend != escalating:
  convergence_state = converging    # new evidence still arriving, not getting worse

ELSE IF severity_trend == escalating:
  convergence_state = diverging     # getting worse — deeper problem, change approach

ELSE IF evidence_rate < convergence.evidence_rate_stable (0.20)
        AND entropy_estimate < convergence.entropy_stuck_threshold (1.0):
  convergence_state = stuck         # low evidence + low entropy = same issues repeating

ELSE IF evidence_rate < convergence.evidence_rate_stable (0.20)
        AND severity_trend == stable:
  convergence_state = stable        # low evidence + diverse categories = search space exhausted

ELSE:
  convergence_state = stuck         # low evidence rate, unclear trend
```

### Entropy Computation

`entropy_estimate` is Shannon entropy over the distribution of finding categories in the current cycle:

```
entropy = -sum(p_i * log2(p_i) for each category i where p_i > 0)
```

where `p_i = count(findings in category i) / total_findings`.

Low entropy (below `convergence.entropy_stuck_threshold = 1.0`) means findings cluster in 1-2 categories — the loop is stuck on the same problem class. High entropy means diverse issue categories are surfacing — the loop may be productive despite a low evidence rate.

If there are no findings: `entropy_estimate = 0.0`.

### recommendation Derivation

```
converging  → continue         (loop is working, proceed normally)
stable      → stop_early       (no value in continuing, findings are repetitive)
diverging   → change_approach  (escalate with structured escalation_reason)
stuck       → extend_budget    if current_cycle < original_budget * max_budget_multiplier (2)
           → change_approach   if current_cycle >= original_budget * max_budget_multiplier (2)
```

`max_budget_multiplier` is read from `references/mode-convergence-rules.yaml:max_budget_multiplier`. The budget comparison always uses the **original** (initial) budget, not the current (possibly already extended) budget, to prevent runaway extension beyond 2x.

---

## Execution Mode Schema (Rasmussen SRK)

Derived from `quality-budget.yaml` telemetry per task. All classification thresholds are read from `references/mode-convergence-rules.yaml:srk_thresholds`.

```yaml
execution_mode:
  classification: skill_based | rule_based | knowledge_based
  signals:
    wip_beads: 2
    turbulence_sum_per_bead: 0.5
    review_latency_p95_s: 30
    zero_turbulence_rate: 0.80
    escalation_count: 0
  confidence: high | medium | low
```

### SRK Classification Rules

Boundary values are **inclusive for rule-based** (the middle band). Skill-based and knowledge-based use strict inequalities. Source of truth: `references/mode-convergence-rules.yaml:srk_thresholds`.

| Signal | Skill-based | Rule-based | Knowledge-based |
|--------|------------|------------|-----------------|
| `turbulence_sum_per_bead` | **< 1.0** | **>= 1.0 AND <= 3.0** | **> 3.0** |
| `zero_turbulence_rate` | **> 0.80** | **>= 0.50 AND <= 0.80** | **< 0.50** |
| `review_latency_p95_s` | **< 60** | **>= 60 AND <= 300** | **> 300** |
| `escalation_count` (L2+) | **== 0** | **>= 1 AND <= 2** | **> 2** |

Majority vote across 4 signals. Ties (2-2 split) resolve to `rule_based`.

### Confidence Derivation

From `references/mode-convergence-rules.yaml:srk_confidence`:

```
4 signals vote the same class  →  confidence = high    (unanimous)
3 signals vote the same class  →  confidence = medium  (supermajority, 3-1)
2-2 split (tie)                →  confidence = low     (resolved to rule_based)
```

---

## Per-Task Mode-Convergence Summary Schema

**Location:** `docs/sdlc/active/{task-id}/mode-convergence-summary.yaml`

```yaml
schema_version: 1
task_id: ""                      # matches the task directory name
artifact_status: partial | final # partial during task, final after Synthesize
derived_at: ""                   # ISO 8601 UTC timestamp

execution_mode:
  classification: skill_based | rule_based | knowledge_based
  confidence: high | medium | low
  signals:
    wip_beads: 0
    turbulence_sum_per_bead: 0.0
    review_latency_p95_s: 0
    zero_turbulence_rate: 0.0
    escalation_count: 0

convergence_history:
  - bead_id: ""                  # bead identifier
    loop_level: L0 | L1 | L2 | L2_5
    cycles:                      # list of convergence_signal, one per cycle
      - cycle: 1
        new_findings: 0
        repeated_findings: 0
        evidence_rate: 0.0
        severity_trend: stable
        entropy_estimate: 0.0
        convergence_state: converging
        recommendation: continue

escalation_log:
  - bead_id: ""
    from_level: L0 | L1 | L2
    to_level: L1 | L2 | L3
    reason: ambiguity | coupling | statefulness | concurrency | reviewer_overload | missing_precedent | domain_gap | tooling_limitation | decomposition_error | context_exhaustion
    evidence: ""                 # brief description of what triggered the escalation
    timestamp: ""                # ISO 8601 UTC

summary:
  total_escalations: 0
  reason_distribution: {}        # map of reason → count, e.g. {ambiguity: 2, coupling: 1}
  dominant_reason: null          # most frequent escalation reason, or null if none
  early_stops: 0                 # loop iterations stopped early on convergence signal
  budget_extensions: 0           # loop iterations that received an extended budget
  approach_changes: 0            # loop iterations where approach was changed (change_approach recommendation)
  mode_transitions: 0            # times SRK classification changed during the task (deferred to v2)
```

**Required fields:** `schema_version`, `task_id`, `artifact_status`, `execution_mode`, `summary`
**`artifact_status` enum:** `partial` (task in progress), `final` (task complete, ready for system ledger)
**`mode_transitions`:** collected but not computed in v1 (requires per-iteration snapshots); set to 0.

---

## System JSONL Schema

**Location:** `docs/sdlc/system-mode-convergence.jsonl`

One JSON object per line, one entry per completed task:

```jsonl
{"task_id":"","date":"","execution_mode":"","mode_confidence":"","total_escalations":0,"reason_distribution":{},"dominant_reason":null,"early_stops":0,"convergence_yield":0.0,"beads":0}
```

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Task identifier |
| `date` | string | ISO 8601 date (YYYY-MM-DD) of task completion |
| `execution_mode` | string | `skill_based`, `rule_based`, or `knowledge_based` |
| `mode_confidence` | string | `high`, `medium`, or `low` |
| `total_escalations` | integer | Total escalations across all beads in the task |
| `reason_distribution` | object | Map of escalation_reason → count |
| `dominant_reason` | string or null | Most frequent escalation reason; null if no escalations |
| `early_stops` | integer | Loop iterations stopped early via `stop_early` recommendation |
| `convergence_yield` | float | `early_stops / total_loop_iterations` — higher is better |
| `beads` | integer | Total beads in the task |

`convergence_yield` is the primary loop-efficiency signal. A yield below 0.10 across recent tasks indicates that the convergence detection may need recalibration.

---

## Integration Points

### Loop System (`skills/sdlc-loop/SKILL.md`)

Every correction signal gains two fields:
- `escalation_reason`: one value from the escalation reason enum (required on every escalation)
- `convergence_signal`: current cycle's evidence rate, entropy, state, and recommendation

The loop budget handler reads `convergence_signal.recommendation`:
- `stop_early` → skip remaining budget iterations, advance bead
- `extend_budget` → add 1 cycle if `current_cycle < original_budget * max_budget_multiplier`
- `change_approach` → escalate with the structured `escalation_reason`
- `continue` → proceed normally within existing budget

### AQS Convergence (`skills/sdlc-adversarial/SKILL.md`)

After each AQS cycle, compute the convergence signal via `scripts/compute-convergence-signal.sh`:
1. Count `new_findings` (not seen in prior cycles) vs `repeated_findings` (restating prior content)
2. Compute `severity_trend` from max finding severity ordinal comparison
3. Compute `entropy_estimate` via Shannon entropy over finding category distribution
4. Act on the `recommendation` field

The prior 3-indicator heuristic check (low diversity, low severity, low volume) is replaced by this convergence signal.

### Orchestrate Lifecycle (`skills/sdlc-orchestrate/SKILL.md`)

- **Execute phase (end):** Run `scripts/classify-execution-mode.sh <task-dir>` to compute SRK classification from final `quality-budget.yaml` telemetry
- **Synthesize phase:** Run `scripts/derive-mode-convergence-summary.sh <task-dir> --status final` to produce `mode-convergence-summary.yaml`
- **Complete phase:** Run `scripts/append-system-mode-convergence.sh <task-dir> <project-dir>` to append to system ledger

### Advisory Soft Signals

These signals are informational and non-phase-gating in v1:

- `execution_mode: knowledge_based` with `confidence: high` → flag for Conductor: higher turbulence and longer loops expected
- `dominant_reason` appearing in 3+ escalations within one task → "Systematic issue — consider re-decomposition"
- `convergence_yield < 0.10` across last 5 tasks → "Loops rarely stop early — convergence detection may need recalibration"
- Same escalation reason clustering across 5+ consecutive tasks in the system ledger → systematic decomposition quality signal
