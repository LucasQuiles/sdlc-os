# Mode & Convergence Signals — Phase 3c of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-30
**Status:** Draft
**Roadmap position:** Phase 3c of 5 (Quality Budget [DONE] → Hazard/Defense Ledger [DONE] → Stressor Harvesting [DONE] → Decision-Noise Controls [DONE] → **Mode/Convergence Signals**)
**Depends on:** Phase 1 (quality-budget.yaml telemetry), Phase 3b (review-passes.jsonl MAP vectors)

---

## Problem Statement

The SDLC has loops with fixed budgets (L0: 3 attempts, L1: 2 cycles, AQS: 2 cycles) but no information-rate signal telling it when to stop early or persist longer. Escalations happen because a budget is exhausted, but the escalation doesn't say WHY — was it ambiguity, coupling, statefulness, concurrency, reviewer overload, or missing precedent? The system cannot distinguish a loop that's converging slowly from one that's stuck.

Three operational failures:

1. **No convergence signal.** AQS uses 3 heuristic indicators (diversity, severity, volume) checked once after Cycle 1. This is better than pure round-counting, but it doesn't measure information rate — whether new cycles are producing genuinely new evidence or just rehashing. The belief entropy stopping criterion from the research synthesis (`docs/specs/2026-03-25-aqs-v2-research-synthesis.md`) is proposed but not implemented.

2. **No escalation reason.** When a bead escalates from L0→L1 or L1→L2, the correction signal format includes "what was tried" and "why it failed" but not a structured reason category. Without categories, the system can't detect patterns (e.g., "80% of L1 escalations are coupling-related" → decomposition is too coarse).

3. **No workload mode classification.** Phase 1 gave us the telemetry (WIP, turbulence, latency from quality-budget.yaml), but the Rasmussen SRK classification is still prose in the design spec, not an operational signal. The system can't distinguish skill-based execution (fast, low-error, routine) from knowledge-based execution (slow, high-error, novel) and adjust its loop budgets accordingly.

### Goal

Make loop control information-aware, escalation reasons structured, and execution mode observable. For every loop iteration, the system should know:
- Is this loop converging or stuck? (evidence rate)
- If stuck, why? (escalation reason category)
- What mode is the runner/task operating in? (SRK classification)
- Should the loop budget be extended, shortened, or the approach changed?

### Design Principle

Don't add new loops or phases. Enrich the existing loop system with signals that make its fixed budgets adaptive. The changes are:
- Convergence: measure → stop early or persist
- Escalation: categorize → detect patterns → improve decomposition
- Mode: classify → adjust expectations → avoid mode-mismatched budgets

---

## Thinker Connections

| Concept | Source | What Phase 3c operationalizes |
|---------|--------|------------------------------|
| SRK model | Rasmussen | Classify execution mode from telemetry. Skill-based (routine, fast) vs rule-based (procedural, moderate) vs knowledge-based (novel, slow). Different modes have different error profiles and appropriate loop budgets. |
| Sensemaking | Weick | Escalation reasons are sensemaking cues — they explain WHY the loop failed, not just THAT it failed. Pattern detection across reasons = organizational learning. |
| Requisite variety | Weick/Ashby | When escalation reasons cluster (same category repeatedly), the system's variety is insufficient for that problem class. Signal to the Conductor to change approach, not just retry. |
| Convergence detection | Yegge/RvB research | Stop adversarial cycles when new-evidence rate collapses. Information entropy across findings drops below threshold = no value in continuing. |
| Colony efficiency | Yegge | Don't waste colony resources on loops that aren't producing value. Convergence signals enable early termination of low-value cycles. |

---

## Schema

### Escalation Reason Categories

Structured enum attached to every escalation in the loop system:

```yaml
escalation_reasons:
  - ambiguity           # spec/requirements unclear
  - coupling            # bead scope crosses too many boundaries
  - statefulness        # complex state management the runner can't reason about
  - concurrency         # race conditions, ordering, parallelism issues
  - reviewer_overload   # too many findings for the blue team to process
  - missing_precedent   # no prior case guides the decision
  - domain_gap          # runner lacks domain expertise for this bead
  - tooling_limitation  # deterministic check needed but unavailable
  - decomposition_error # bead is too large or too entangled
  - context_exhaustion  # runner ran out of context before completing
```

### Convergence Signal (`convergence_signal` on each loop iteration)

Attached to bead correction signals and AQS cycle transitions:

```yaml
convergence_signal:
  cycle: 1                    # which iteration
  new_findings: 3             # findings not seen in prior cycles
  repeated_findings: 1        # findings that restate prior cycle content
  evidence_rate: 0.75         # new_findings / (new_findings + repeated_findings)
  severity_trend: declining | stable | escalating
  entropy_estimate: 2.1       # Shannon entropy of finding categories this cycle
  convergence_state: converging | stable | diverging | stuck
  recommendation: continue | stop_early | extend_budget | change_approach
```

**convergence_state derivation:**
```
IF evidence_rate >= 0.50 AND severity_trend != escalating:
  converging (new evidence still arriving, not getting worse)
ELSE IF evidence_rate < 0.20 AND severity_trend == stable:
  stable (findings are repetitive, no new information)
ELSE IF severity_trend == escalating:
  diverging (getting worse — deeper problem)
ELSE:
  stuck (low evidence rate, unclear trend)
```

**recommendation derivation:**
```
converging → continue (loop is working)
stable → stop_early (no value in continuing)
diverging → change_approach (escalate with reason)
stuck → extend_budget if budget < 2x original, else change_approach
```

### Execution Mode Classification (Rasmussen SRK)

Derived from quality-budget.yaml telemetry per task:

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

**Classification rules (from `references/mode-convergence-rules.yaml`):**

| Signal | Skill-based | Rule-based | Knowledge-based |
|--------|------------|------------|-----------------|
| turbulence_sum_per_bead | < 1.0 | 1.0-3.0 | > 3.0 |
| zero_turbulence_rate | > 0.80 | 0.50-0.80 | < 0.50 |
| review_latency_p95_s | < 60 | 60-300 | > 300 |
| escalation_count (L2+) | 0 | 1-2 | > 2 |

Majority vote across 4 signals. Ties → rule_based (middle).

### Per-Task Mode/Convergence Summary

**Location:** `docs/sdlc/active/{task-id}/mode-convergence-summary.yaml`

```yaml
schema_version: 1
task_id: ""
artifact_status: partial | final
derived_at: ""

execution_mode:
  classification: skill_based | rule_based | knowledge_based
  confidence: high | medium | low
  signals: {}

convergence_history:
  - bead_id: ""
    loop_level: L0 | L1 | L2 | L2_5
    cycles: []  # list of convergence_signal per cycle

escalation_log:
  - bead_id: ""
    from_level: L0 | L1 | L2
    to_level: L1 | L2 | L3
    reason: ambiguity | coupling | statefulness | ...
    evidence: ""
    timestamp: ""

summary:
  total_escalations: 0
  reason_distribution: {}     # {ambiguity: 2, coupling: 1, ...}
  dominant_reason: null        # most frequent reason
  early_stops: 0              # loops stopped early on convergence
  budget_extensions: 0        # loops that got extended budget
  approach_changes: 0         # loops where approach was changed
  mode_transitions: 0         # times classification changed during task
```

### System Ledger

**Location:** `docs/sdlc/system-mode-convergence.jsonl`

```jsonl
{"task_id":"","date":"","execution_mode":"","mode_confidence":"","total_escalations":0,"reason_distribution":{},"dominant_reason":null,"early_stops":0,"convergence_yield":0.0,"beads":0}
```

`convergence_yield` = `early_stops / total_loop_iterations` — higher is better (system knows when to stop).

---

## Integration Points

### Loop System (`sdlc-loop`)

Every correction signal gains two new fields:
- `escalation_reason`: structured category from the enum
- `convergence_signal`: current cycle's evidence rate, entropy, and recommendation

The loop budget handler checks `convergence_signal.recommendation`:
- `stop_early` → skip remaining budget, advance bead
- `extend_budget` → add 1 cycle if within 2x limit
- `change_approach` → escalate with structured reason

### AQS Convergence (`sdlc-adversarial`)

Replace the current 3-indicator heuristic check with convergence_signal computation:
- After each AQS cycle, compute `new_findings` vs `repeated_findings`
- Compute `evidence_rate` and `entropy_estimate`
- If `convergence_state == stable` → skip remaining cycles
- If `convergence_state == diverging` → mandatory Cycle 2 regardless of budget

### Orchestrate Lifecycle

- Compute `execution_mode` from quality-budget.yaml after Execute phase
- Log mode transitions if classification changes during task (started skill-based, became knowledge-based after hitting complex bead)
- Derive mode-convergence-summary.yaml during Synthesize

---

## Phase Gates

Advisory-only in v1. Mode/convergence signals are tracked and reported but do not gate phase transitions.

**Soft signals:**
- `execution_mode: knowledge_based` with `confidence: high` → flag for Conductor: "This task is operating in knowledge-based mode — expect higher turbulence and longer loops"
- `dominant_reason` appearing in 3+ escalations within one task → flag: "Systematic issue — consider re-decomposition"
- `convergence_yield < 0.10` across last 5 tasks → flag: "Loops rarely stop early — convergence detection may need recalibration"

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `references/mode-convergence-rules.yaml` | SRK classification thresholds, convergence_state derivation rules, escalation reason enum |
| `references/mode-convergence-schema.md` | Schema docs for all mode/convergence artifacts |
| `scripts/lib/mode-convergence-lib.sh` | Shared helpers: SRK classification, convergence signal computation, evidence rate, entropy estimate |
| `scripts/classify-execution-mode.sh` | Reads quality-budget.yaml → computes SRK classification |
| `scripts/compute-convergence-signal.sh` | Reads cycle findings → computes convergence signal |
| `scripts/derive-mode-convergence-summary.sh` | Reads escalation log + convergence history → produces per-task summary |
| `scripts/append-system-mode-convergence.sh` | Reads final summary → appends to system-mode-convergence.jsonl |
| `hooks/scripts/validate-mode-convergence-summary.sh` | PostToolUse hook for mode-convergence-summary.yaml |
| `hooks/tests/fixtures/mc-valid/mode-convergence-summary.yaml` | Test fixture |
| `hooks/tests/fixtures/mc-missing/mode-convergence-summary.yaml` | Test fixture |
| `hooks/tests/fixtures/mc-malformed/mode-convergence-summary.yaml` | Test fixture |

### Files to Modify

| File | Change |
|------|--------|
| `skills/sdlc-orchestrate/SKILL.md` | Add execution mode classification after Execute. Add mode-convergence-summary derivation in Synthesize. Add mode/convergence artifacts to inventory. |
| `skills/sdlc-loop/SKILL.md` | Add `escalation_reason` and `convergence_signal` to correction signal format. Add convergence-aware budget handling (stop_early, extend_budget, change_approach). |
| `skills/sdlc-adversarial/SKILL.md:234-250` | Replace 3-indicator convergence check with convergence_signal computation. Add evidence_rate and entropy-based stopping. |
| `skills/sdlc-gate/SKILL.md` | Add advisory mode/convergence checklist |
| `skills/sdlc-evolve/SKILL.md` | Add escalation-reason pattern analysis evolution bead: consume system ledger, detect dominant reasons, propose decomposition improvements |
| `references/quality-slos.md` | Add convergence_yield and dominant_escalation_reason as tracked metrics |
| `agents/process-drift-monitor.md` | Add mode-transition detection and escalation-reason clustering from system-mode-convergence.jsonl |
| `skills/sdlc-normalize/SKILL.md` | Add mode-convergence-summary.yaml to resume artifact list |
| `references/artifact-templates.md` | Add mode-convergence-summary.yaml to Task Artifacts table |
| `hooks/hooks.json` | Add validate-mode-convergence-summary.sh PostToolUse hook |
| `hooks/tests/test-hooks.sh` | Add mode-convergence summary validation tests |
| `README.md` | Add mode/convergence artifacts, hook, metrics |

---

## Scope Boundary

### In scope (Phase 3c)

- Escalation reason categories (structured enum)
- Convergence signal computation (evidence rate, entropy, state, recommendation)
- Execution mode classification (Rasmussen SRK from quality-budget telemetry)
- Per-task mode-convergence-summary.yaml
- System ledger (system-mode-convergence.jsonl)
- Loop system integration (convergence-aware budget handling)
- AQS convergence replacement (evidence-rate based, not just indicator count)
- Validation hook + tests
- Rules file (SRK thresholds, convergence rules)
- Advisory soft signals

### Out of scope

- Hard gates on mode/convergence signals (advisory-only v1)
- Automated decomposition based on escalation reason patterns (evolve proposes, Conductor decides)
- Cross-task mode prediction (predicting SRK classification before execution starts)
- Full Shannon entropy computation with token-level analysis (use finding-category entropy as proxy)
