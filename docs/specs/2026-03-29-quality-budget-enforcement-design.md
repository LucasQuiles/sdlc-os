# Quality Budget Enforcement — Phase 1 of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-29
**Status:** Draft
**Roadmap position:** Phase 1 of 5 (Foundation → Hazard Ledger → Stressor Harvesting → Decision-Noise Controls → Mode/Convergence Signals)

---

## Problem Statement

The SDLC-OS has a Quality Budget concept but it is structurally unenforceable. `quality-budget.md` is referenced in 7 files but has no mandatory schema — it is a free-text markdown file. The template in `quality-slos.md:57-65` tracks only 5 SLIs (lint, types, coverage, complexity, critical findings), missing the signals that bridge structure to Deming/Meadows/Rasmussen: L0/L1/L2 corrections, turbulence trends, estimate vs actual, review latency, WIP beads, queue depth, buffer hits, and defect escapes.

Live tasks confirm the gap: some have the budget populated, others empty or missing entirely. Different tasks populate different ad-hoc metrics. One complex bead requires full hardening while the task rollup says hardening was deferred.

The fix: make Quality Budget a machine-readable, mandatory, derivation-first, schema-validated artifact that aggregates metrics from bead traces, task state, and execution telemetry into a canonical store that Deming control charts, Meadows stock-flow analysis, and Rasmussen workload classification can all consume.

### Design Principles

1. **Derived-first, not hand-maintained.** Most fields are computed from bead traces, task state, review outcomes, and reliability telemetry. Humans fill only exceptions, interpretations, and override rationale.
2. **Two scopes.** Task-local budget for gating and resume logic. System-level longitudinal ledger for cross-task analysis.
3. **Enforcement as control surface.** A task cannot transition to Synthesize or Complete unless the budget artifact exists, validates, and meets minimum completeness.

---

## Thinker Connections

| Thinker | What Quality Budget unlocks |
|---------|---------------------------|
| **Deming** | Control charts on zero_turbulence_rate, turbulence_sum, review_latency over the system ledger. Variation classifier distinguishes common vs special cause on any metric. |
| **Meadows** | Stock-flow: WIP beads = stock, completion rate = outflow, dispatch rate = inflow. Buffer hits visible. Feedback delays measurable via review_latency. |
| **Rasmussen** | Workload classification from WIP + turbulence + latency. High WIP + rising turbulence = knowledge-based mode (slow, error-prone). Low WIP + low turbulence = skill-based (fast, reliable). |
| **Taleb** | Asymmetric budget response: never fully relax on healthy. Track-record skepticism from the system ledger (long clean streaks trigger increased scrutiny, not relaxation). |
| **Kahneman** | Noise audits: re-derive budget from bead traces independently, compare with recorded values. Spot inconsistencies = noise. |
| **Gigerenzer** | FFT decision trees already branch on budget state (FFT-01/04/05); canonical budget_state makes those branches reliable. |

---

## Schema

### Threshold Rules (`references/quality-budget-rules.yaml`)

Externalized, recalibrable without touching historical artifacts.

```yaml
schema_version: 1

# Weighted complexity factor: higher = more lenient thresholds
# weight = (clear * 0.0 + complicated * 0.5 + complex * 1.0 + chaotic * 1.5) / total_beads
complexity_thresholds:
  - max_weight: 0.2    # mostly clear
    healthy_floor: 0.90
    depleted_floor: 0.60
  - max_weight: 0.5    # mixed
    healthy_floor: 0.75
    depleted_floor: 0.50
  - max_weight: 0.8    # mostly complex
    healthy_floor: 0.60
    depleted_floor: 0.35
  - max_weight: 999    # extreme
    healthy_floor: 0.50
    depleted_floor: 0.25

# Hard-stop invariants: budget_state CANNOT be healthy if ANY are true
hard_stops:
  - lint_clean == false
  - types_clean == false
  - critical_findings > 0
  - beads.stuck > 0
  - beads.blocked > 0 AND wip_age_max_s > 3600

# v1 gating metrics (budget_state depends on these)
gating_metrics:
  - zero_turbulence_rate
  - escapes.known_at_close
  - hard_stops
  - turbulence_sum_per_bead  # turbulence_sum / beads.completed

# v1 observed-only metrics (recorded but not gated)
observed_metrics:
  - queue_depth_peak
  - buffer_hits
  - wip_age_max_s
  - review_latency_avg_s
  - review_latency_p95_s
  - review_pass_rate

system_rolling_window:
  tasks: 10
  max_days: 30
```

### Task Budget (`docs/sdlc/active/{task-id}/quality-budget.yaml`)

YAML file, derivation-first. Machine-readable frontmatter is the entire file (no markdown body).

```yaml
schema_version: 1
task_id: ""
artifact_status: partial | ready | final
#   partial: during Execute (fields accumulating)
#   ready: all derived fields populated, gate-check passable (enter Synthesize)
#   final: Synthesize complete, SLI readings filled, budget_state locked
budget_state: healthy | warning | depleted
derived_at: "2026-03-28T14:22:00Z"  # UTC ISO 8601
last_updated: "2026-03-28T14:22:00Z"

cynefin_mix:
  clear: 0
  complicated: 0
  complex: 0
  chaotic: 0
complexity_weight: 0.0  # derived: (clear*0 + complicated*0.5 + complex*1.0 + chaotic*1.5) / total

beads:
  total: 0
  completed: 0
  wip: 0
  stuck: 0
  blocked: 0
  wip_age_max_s: 0  # seconds, longest-running WIP bead

corrections:
  L0: 0
  L1: 0
  L2: 0
  L2_5: 0
  L2_75: 0

turbulence_sum: 0
turbulence_max_bead: null

metrics:
  # === Gating (budget_state depends on these in v1) ===
  zero_turbulence_rate: 0.0
  #   Denominator: completed beads.
  #   Numerator: completed beads with turbulence_sum == 0.
  #   Eligibility: all completed beads count. Stuck/blocked before completion excluded.

  turbulence_sum_per_bead: 0.0
  #   turbulence_sum / beads.completed. Undefined (null) when completed == 0.

  # === Observed (recorded, not gated in v1) ===
  review_pass_rate: 0.0
  #   Denominator: completed beads that reached L1 (excludes Clear beads that skip
  #   L1 under healthy budget per orchestrate SKILL.md:230 skip-condition).
  #   Numerator: beads with turbulence.L1 == 0 among eligible.

  queue_depth_peak: 0      # max concurrent WIP beads during task
  buffer_hits: 0           # times queue_depth hit grid/dispatch capacity
  review_latency_avg_s: 0  # mean seconds between bead submission and review start
  review_latency_p95_s: 0  # 95th percentile, same

timing:
  estimate_s: null          # optional in v1; required from v2 onward. Seconds.
  actual_s: null            # wall clock init to synthesize. Seconds.

sli_readings:               # populated during Synthesize (null while partial/ready)
  lint_clean: null
  types_clean: null
  test_coverage_delta: null
  complexity_delta: null
  critical_findings: null

escapes:
  known_at_close: 0         # defect escapes confirmed before Complete

overrides: []
#  - field: budget_state
#    value: warning
#    reason: "Deferred hardening on B03 despite complex domain"
notes: ""
```

### budget_state Derivation

```
complexity_weight = (clear*0 + complicated*0.5 + complex*1.0 + chaotic*1.5) / total_beads
threshold = lookup(complexity_weight, quality-budget-rules.yaml.complexity_thresholds)

IF any hard_stop is true:
  budget_state = "depleted" if critical_findings > 0 or stuck > 0
  budget_state = "warning" otherwise

ELSE IF zero_turbulence_rate >= threshold.healthy_floor
     AND escapes.known_at_close == 0:
  budget_state = "healthy"

ELSE IF zero_turbulence_rate < threshold.depleted_floor
     OR escapes.known_at_close > 1
     OR turbulence_sum > 6 * beads.completed:
  budget_state = "depleted"

ELSE:
  budget_state = "warning"
```

### System Budget

**Primary ledger** (`docs/sdlc/system-budget.jsonl`) — one line per completed task, immutable after write:

```jsonl
{"task_id":"wizard-modal-rebuild-20260328","date":"2026-03-28T15:00:00Z","beads":6,"cynefin_mix":{"clear":2,"complicated":3,"complex":1,"chaotic":0},"complexity_weight":0.42,"turbulence_sum":4,"zero_turbulence_rate":0.50,"review_pass_rate":0.75,"L0":3,"L1":1,"L2":0,"L2_5":0,"L2_75":0,"escapes_at_close":0,"estimate_s":null,"actual_s":null,"latency_avg_s":45,"latency_p95_s":120,"queue_peak":3,"buffer_hits":0,"budget_state":"healthy"}
```

**Events ledger** (`docs/sdlc/system-budget-events.jsonl`) — late-arriving corrections keyed by task_id:

```jsonl
{"task_id":"wizard-modal-rebuild-20260328","event":"escape_confirmed","date":"2026-04-04T10:00:00Z","escape_count":1,"source":"losa","finding_id":"LOSA-042"}
```

Consumers merge primary + events when computing rolling window. Primary is source of truth at close time; events overlay retroactive discoveries.

**System budget_state derivation** (rolling window per rules file):

| Condition | State |
|-----------|-------|
| Rolling `zero_turbulence_rate >= 0.70` AND `sum(escapes_at_close) == 0` in last 3 | healthy |
| Below healthy OR `sum(escapes_at_close) > 0` in last 3 | warning |
| Rolling `zero_turbulence_rate < 0.50` OR `sum(escapes_at_close) > 1` in last 3 OR 2+ tasks with `turbulence_sum > 6 * beads` | depleted |

---

## Phase Gates

### Synthesize Gate

Task cannot transition to Synthesize unless:
1. `quality-budget.yaml` exists in the task directory
2. Parses as valid YAML with `schema_version: 1`
3. `artifact_status` is `ready`
4. All derived fields non-null except: `estimate_s` (optional v1), `sli_readings.*` (filled during Synthesize)
5. No hard-stop invariants violated (per rules file, checked against available data)

### Complete Gate

Task cannot transition to Complete unless:
1. `artifact_status` is `final`
2. `sli_readings` fully populated (not null)
3. `budget_state` computed with hard-stops applied
4. System ledger entry appended

---

## Telemetry Prerequisites

For derivation to work, bead artifacts must contain structured timestamps. These fields must be added to the bead schema before the derivation engine can populate timing and latency metrics.

| Required field | Location | Current status | Action |
|----------------|----------|----------------|--------|
| `turbulence: {L0, L1, L2, L2_5, L2_75}` | `beads/B*.md` frontmatter | Schema exists, partially populated | Enforce population |
| `cynefin_domain` | `beads/B*.md` frontmatter | Exists | No change |
| `dispatched_at` | `beads/B*.md` frontmatter | **Missing** | Add to bead schema |
| `review_started_at` | `beads/B*.md` frontmatter | **Missing** | Add to bead schema |
| `completed_at` | `beads/B*.md` frontmatter | **Missing** | Add to bead schema |
| Bead status with timestamps | `state.md` bead table | Exists, inconsistent format | Normalize |

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `references/quality-budget-rules.yaml` | Externalized threshold rules, hard-stops, gating vs observed metric lists |
| `references/quality-budget-schema.md` | Human-readable schema documentation: field definitions, denominators, eligibility rules, derivation sources |
| `scripts/lib/quality-budget-lib.sh` | Shared helper: YAML parsing, metric computation, threshold lookup, budget_state derivation |
| `scripts/derive-quality-budget.sh` | Reads bead traces + state.md → produces/updates quality-budget.yaml. Sources quality-budget-lib.sh |
| `scripts/append-system-budget.sh` | Reads final quality-budget.yaml → appends to system-budget.jsonl. Sources quality-budget-lib.sh |
| `hooks/scripts/validate-quality-budget.sh` | Hook script: validates quality-budget.yaml structure and completeness at gate transitions |

### Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `skills/sdlc-orchestrate/SKILL.md` | :135, :230, :396 | Replace `quality-budget.md` references with `quality-budget.yaml`. Add Synthesize gate (artifact_status: ready) and Complete gate (artifact_status: final). Add derivation trigger after each bead completion. Update artifact inventory. |
| `skills/sdlc-normalize/SKILL.md` | :64 | Replace `quality-budget.md` with `quality-budget.yaml` in resume artifact list |
| `skills/sdlc-gate/SKILL.md` | (gate logic) | Add artifact_status: partial/ready/final understanding and hard-stop failure reporting |
| `references/quality-slos.md` | :57-67 | Replace old markdown template with pointer to quality-budget-schema.md and quality-budget-rules.yaml |
| `references/artifact-templates.md` | (bead template) | Add `dispatched_at`, `review_started_at`, `completed_at` timestamp fields to bead frontmatter template. Add quality-budget.yaml to task artifact contract. |
| `references/fft-decision-trees.md` | (FFT-01, FFT-04, FFT-05) | Wire budget_state branches to consume quality-budget.yaml via rules file, not inline thresholds |
| `references/reliability-ledger.md` | :7-9 | Reconcile: reliability-ledger.md remains the per-level first-pass-rate document. System-budget.jsonl is the cross-task aggregate. Remove conflicting "canonical append-only ledger" claim; clarify that reliability-ledger.md feeds into system-budget.jsonl via the derivation scripts. |
| `agents/normalizer.md` | (resume artifacts) | Add quality-budget.yaml to resume artifact list; validate on mid-stream pickup |
| `agents/reliability-ledger.md` | (computation) | Consume quality-budget.yaml task entries for turbulence aggregation instead of reimplementing |
| `agents/process-drift-monitor.md` | (trend analysis) | Consume system-budget.jsonl for longitudinal trend analysis |
| `agents/losa-observer.md` | (escape reporting) | Write to system-budget-events.jsonl when escape confirmed |
| `agents/llm-self-security.md` | :83 | Replace `quality-budget.md` with `quality-budget.yaml` for unbounded-consumption checks |
| `skills/sdlc-evolve/SKILL.md` | (evolution prioritization) | Consume system-budget.jsonl for evolution prioritization |
| `hooks/hooks.json` | (hook list) | Add validate-quality-budget.sh as PreToolUse or phase-transition hook |
| `commands/sdlc.md` | (artifact description) | Reflect that a task now owns quality-budget.yaml |
| `README.md` | :124 area | Update artifact list to include quality-budget.yaml and system-budget.jsonl |

### Files Unchanged but Consuming

| File | Consumes |
|------|----------|
| `references/calibration-protocol.md` | Cross-references system budget for detection rate trends |
| `agents/variation-classifier.md` | Classifies system budget metrics as common/special cause |

---

## Scope Boundary

### In scope (Phase 1)

- Quality budget schema (task + system)
- Threshold rules file
- Derivation scripts + shared lib
- Bead timestamp prerequisites
- Phase gate enforcement
- All file modifications listed above
- Validation hook + tests

### Out of scope (Phase 2-5)

- Hazard/Defense Ledger (Phase 2)
- Stressor harvesting + barbell hardening (Phase 3a)
- Decision-noise + precedent controls (Phase 3b)
- Mode + convergence signals (Phase 3c)
- Deming control chart visualization
- Meadows stock-flow diagrams
- Reference-class forecasting from estimate_s (v2 requirement)
- Retroactive escape confirmation workflow (confirmed_7d — v2)
