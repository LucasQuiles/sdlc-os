# Decision-Noise Controls — Phase 3b of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-30
**Status:** Draft
**Roadmap position:** Phase 3b of 5 (Quality Budget [DONE] → Hazard/Defense Ledger [DONE] → Stressor Harvesting [DONE] → **Decision-Noise Controls** → Mode/Convergence Signals)
**Source:** Mission brief and artifact model drafted at `LAB/OnePlatform/Docs/sdlc/active/aqs-decision-noise-controls-20260330/`

---

## Problem Statement

AQS has strong generation mechanisms for dissent and simplification: adversarial collaboration, red/blue opposition, pre-mortem hardening, and FFT routing. The gap is not idea generation — it is decision reliability at the verdict layer.

Arbiter verdicts are holistic. Reviewers can disagree on evidence, impact, precedent fit, or probability while converging on the same narrative, and that disagreement is lost. Later reviewers can inherit anchors from earlier findings, but exposure order is not recorded and anchoring drift is not measured. The system knows what the final verdict was, but not how sensitive that verdict was to order, framing, or reviewer exposure.

There is no systematic spot-check where the same bead is reviewed twice independently. Decision noise is discussed as a risk but not measured. Probability language uses "likely" or "possible" without natural frequencies backed by named reference classes.

FFTs and take-the-best cues exist but their predictive value is assumed, not measured. No feedback loop says which cues actually correlate with missed defects, accepted findings, or false alarms.

### Goal

Add decision-quality controls to the AQS review stack so arbiter outcomes become less anchorable, more repeatable, and measurable over time — without replacing the existing red/blue/arbiter or FFT machinery.

### Design Principles

1. Measure noise before trying to optimize it
2. Preserve the current AQS flow — add controls around it
3. Separate blind judgment from precedent-assisted judgment
4. Keep the scoring surface small and stable
5. Make the canonical record append-only; derive summaries elsewhere

---

## Thinker Connections

| Concept | Source | What Phase 3b operationalizes |
|---------|--------|------------------------------|
| MAP (Mediating Assessments Protocol) | Kahneman, Noise | Independent dimension scoring before holistic synthesis. Pre-synthesis vectors make verdict sensitivity visible. |
| Decision noise | Kahneman, Noise | Repeat-review spot checks measure actual reviewer disagreement. Noise becomes an operational metric, not an assumed risk. |
| Anchoring bias | Kahneman, Thinking Fast and Slow | Blind-first protocol with exposure metadata. Anchoring drift is measured by comparing pre- and post-exposure passes. |
| Natural frequencies | Gigerenzer, Calculated Risks | Probability claims rendered as `x/n` for named reference classes. Calibration becomes possible. |
| Take-the-best | Gigerenzer, Simple Heuristics | FFT cue outcomes captured alongside verdicts. Cue precision validated against real outcomes over time. |
| Reference class forecasting | Kahneman, Thinking Fast and Slow | Base rate frequency in MAP vector backed by historical reference class data. |

---

## Schema

### Canonical Artifact: System Review Passes Ledger

**Location:** `docs/sdlc/decision-noise/review-passes.jsonl`

Append-only. One line per independent review pass. This is the canonical source of truth — per-task summaries are derived views.

**Record shape:**

**Append-only invariants:**
- Records are immutable after write. No field is ever modified in place.
- Idempotent write key: `review_pass_id` (globally unique). Duplicate `review_pass_id` appends are rejected.
- Post-exposure revisions are stored as NEW records with `parent_review_pass_id` pointing to the blind pass.
- `supersedes_review_pass_id` is set when a pass explicitly replaces a prior pass (e.g., arbiter override).
- Schema evolution: `schema_version` field on every record. Consumers must handle version differences.

```json
{
  "schema_version": 1,
  "review_pass_id": "rp_20260330_001",
  "parent_review_pass_id": null,
  "supersedes_review_pass_id": null,
  "task_id": "wizard-modal-rebuild-20260328",
  "bead_id": "B03",
  "decision_trace_id": "B03-decision-trace",
  "timestamp": "2026-03-30T14:22:00Z",

  "review_stage": "arbiter_pre_synthesis | red_team | blue_team | repeat_blind | repeat_exposed",
  "reviewer_role": "arbiter | red-functionality | red-security | red-usability | red-resilience | blue-functionality | blue-security | blue-usability | blue-resilience",
  "reviewer_model": "opus | sonnet | haiku",

  "exposure_mode": "blind_first | precedent_exposed | peer_exposed | full_context",
  "exposure_order": 0,
  "anchor_sources_seen": [],
  "anchor_verdicts_seen": [],
  "anchor_map_targets_seen": [],
  "precedent_pack_id": null,

  "repeat_review_group_id": null,
  "arbiter_group_id": "aqs_B03_01",

  "map": {
    "evidence_strength": 4,
    "impact_severity": 5,
    "base_rate_frequency": {
      "bucket": 3,
      "hits": 3,
      "sample": 10,
      "reference_class_id": "complex-state-mutation-90d",
      "reference_class_state": "available"
    },
    "pattern_familiarity": 4,
    "decision_confidence": 3,
    "precedent_match_delta": null
  },

  "probability_judgments": [
    {
      "claim_id": "p1",
      "text": "state divergence after retry",
      "severity": "high",
      "hits": 3,
      "sample": 10,
      "reference_class_id": "complex-state-mutation-90d"
    }
  ],

  "heuristics": {
    "top_cue": "FFT-05-complex-loop-depth",
    "cue_vector": ["FFT-02-complex", "FFT-08-llm-agent-check"]
  },

  "verdict": {
    "decision": "escalate | accept | dismiss | defer",
    "severity": "P1 | P2 | P3 | P4",
    "confidence_bucket": 3
  }
}
```

### MAP Vector (5 dimensions)

| Dimension | What it measures | Scale |
|-----------|-----------------|-------|
| `evidence_strength` | How well the claim is supported by concrete evidence | 1-5 |
| `impact_severity` | If true, how much user/system/compliance harm follows | 1-5 |
| `base_rate_frequency` | How often similar beads historically produced this issue class | 1-5 bucket + hits/sample/reference_class_id + reference_class_state |
| `pattern_familiarity` | How familiar this pattern feels to the reviewer based on their own judgment (blind — no precedent exposure) | 1-5 |
| `decision_confidence` | How stable the reviewer believes this pass is under re-review | 1-5 |
| `precedent_match_delta` | Post-exposure only: how much the reviewer's assessment changed after seeing precedent packs. Null on blind passes. | -5 to +5 (negative = precedent weakened confidence, positive = strengthened) |

**Blind vs exposed:** On blind passes, `pattern_familiarity` is scored and `precedent_match_delta` is null. On post-exposure passes, both are scored. The delta between blind `pattern_familiarity` and post-exposure `pattern_familiarity` is the raw anchoring signal.

**reference_class_state:** `available` (class exists with sufficient history), `insufficient_history` (class exists but < 5 samples), `not_applicable` (no meaningful reference class for this issue type). When `insufficient_history` or `not_applicable`, the `hits/sample` fields are null and the soft escalation for unbacked high-severity claims does NOT fire — the claim is explicitly marked as novel, not negligently unbacked.

### Per-Task Summary (derived view)

**Location:** `docs/sdlc/active/{task-id}/decision-noise-summary.yaml`

```yaml
schema_version: 1
task_id: ""
artifact_status: partial | final
derived_at: ""

beads_reviewed: 0
passes_total: 0
repeat_review_pairs: 0

metrics:
  repeat_review_noise_index: null     # avg MAP vector distance across repeat pairs
  weighted_verdict_agreement: null     # weighted agreement across paired blind reviews
  map_convergence_score: null          # dispersion across MAP vectors for same bead
  anchoring_drift_rate: null           # score movement after exposure to anchors
  natural_frequency_coverage: null     # share of probability claims backed by hits/sample
  high_severity_unbacked_claims: 0    # high-severity claims without frequency backing
  spot_check_coverage_rate: null       # repeat-reviewed beads / eligible beads

escalations:
  verdict_flips: 0
  map_divergence_2plus: 0
  anchoring_drift_2plus: 0
  unbacked_high_severity: 0
```

### System Events Ledger

**Location:** `docs/sdlc/decision-noise/noise-events.jsonl`

Late-arriving outcome data for cue validation:

```jsonl
{"review_pass_id":"rp_001","event":"outcome_confirmed|regression_detected|false_alarm_confirmed|cue_validated","task_id":"","date":"","details":""}
```

---

## Anti-Anchoring Protocol

The core mechanism is sequence control:

1. Reviewer sees bead evidence and decision trace metadata, but NOT prior verdicts
2. Reviewer records a **blind MAP vector** and provisional verdict
3. Only after that lock may the system reveal precedent packs or peer findings
4. Any post-exposure revision is stored as a **new pass** with `parent_review_pass_id` pointing to the blind pass, `exposure_order` incremented, and `anchor_sources_seen` / `anchor_verdicts_seen` / `anchor_map_targets_seen` populated

This makes anchoring computable: the drift between the blind pass MAP vector and the post-exposure pass MAP vector, toward or away from the anchor's MAP target, is a measurable signal. The `precedent_match_delta` field captures the reviewer's own assessment of how much the precedent changed their judgment.

---

## Repeat-Review Sampling

Oversample reviews most likely to carry noise:

| Bead class | Sample rate | Minimum |
|------------|------------|---------|
| Complex beads with AQS | 20% | 1 per task when any complex bead exists |
| Complicated beads with AQS | 10% | — |
| Clear or accidental | 0% | Incident-triggered only |

Repeat passes are blind-first. Precedent packs shown only after first MAP vector is locked.

---

## Gate Points

### Initial Rollout: Advisory-Only

No hard blocking. Noise metrics are tracked and reported but do not gate phase transitions.

### Soft Escalation Conditions

Trigger a second arbiter pass or mandatory re-review when ANY of:
- Blind pair produces a **verdict flip** (different decision class across passes sharing `repeat_review_group_id`)
- `evidence_strength` or `impact_severity` differs by **2+ buckets** across paired blind reviews
- A **high-severity claim** has `reference_class_state: available` but no `hits/sample` values (negligently unbacked). Claims with `insufficient_history` or `not_applicable` do NOT trigger this — they are explicitly novel.
- A post-exposure pass shifts **2+ MAP buckets** toward the anchor's MAP target (computed: compare `parent_review_pass_id` blind MAP vector vs this pass's MAP vector, in the direction of `anchor_map_targets_seen[0]`)

### Hard Gates

Deferred until at least 50 repeat-review pairs and one full SLO reporting cycle. The measurement system must learn its own variance bands before gating.

---

## Derived Metrics

### Primary

| Metric | Definition |
|--------|-----------|
| `repeat_review_noise_index` | Average MAP vector distance across repeat-review pairs |
| `weighted_verdict_agreement` | Weighted agreement across paired blind reviews |
| `map_convergence_score` | Dispersion across MAP vectors for the same bead |
| `anchoring_drift_rate` | Score/verdict movement after exposure to anchors |
| `natural_frequency_coverage` | Share of probability claims backed by `hits/sample` |
| `reference_class_forecast_error` | Difference between forecasted rate and observed outcome rate |
| `top_cue_precision` | Precision of the top FFT cue against later outcomes |
| `spot_check_coverage_rate` | Repeat-reviewed beads / eligible beads |

### Secondary

| Metric | Definition |
|--------|-----------|
| `arbiter_override_rate` | How often arbiter overrides initial red/blue consensus |
| `precedent_dependence_rate` | Score movement after seeing precedent pack |
| `high_severity_unbacked_claim_rate` | High-severity claims without frequency backing |

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `references/decision-noise-schema.md` | Schema docs for review pass JSONL, MAP vector, per-task summary, events ledger |
| `references/decision-noise-rules.yaml` | Externalized rules: repeat-review sampling rates, soft escalation thresholds (2-bucket divergence, verdict flip), MAP scale definitions |
| `scripts/lib/decision-noise-lib.sh` | Shared helpers: MAP vector distance, noise index computation, escalation detection, review pass ID generation |
| `scripts/record-review-pass.sh` | Appends one review_pass record to review-passes.jsonl |
| `scripts/derive-decision-noise-summary.sh` | Reads review-passes.jsonl for a task → produces decision-noise-summary.yaml |
| `scripts/evaluate-escalations.sh` | Reads paired passes → detects soft escalation conditions → outputs advisory |
| `hooks/scripts/validate-decision-noise-summary.sh` | PostToolUse hook for decision-noise-summary.yaml |
| `hooks/tests/fixtures/dn-valid/decision-noise-summary.yaml` | Test fixture |
| `hooks/tests/fixtures/dn-missing/decision-noise-summary.yaml` | Test fixture |
| `hooks/tests/fixtures/dn-malformed/decision-noise-summary.yaml` | Test fixture |

### Files to Modify

| File | Change |
|------|--------|
| `skills/sdlc-orchestrate/SKILL.md` | Add repeat-review sampling during AQS phase. Add decision-noise-summary derivation in Synthesize. Add noise artifacts to inventory. |
| `skills/sdlc-adversarial/SKILL.md` | Add MAP vector requirement to arbiter pre-synthesis. Add blind-first protocol to arbiter dispatch. Add repeat-review pass dispatch for sampled beads. |
| `skills/sdlc-adversarial/arbitration-protocol.md` | Update arbiter verdict format to include MAP vector. Add blind-first → precedent-exposed two-pass flow. |
| `agents/arbiter.md` (or equivalent) | Update output format to produce structured MAP vector + natural frequency probability judgments |
| `skills/sdlc-evolve/SKILL.md` | Add cue-calibration evolution bead: consume review-passes.jsonl + outcome events → compute cue precision → propose FFT recalibration |
| `skills/sdlc-gate/SKILL.md` | Add decision-noise advisory checklist for AQS-engaged tasks |
| `references/quality-slos.md` | Add noise metrics: repeat_review_noise_index, natural_frequency_coverage, spot_check_coverage_rate |
| `references/calibration-protocol.md` | Wire repeat-review into calibration: calibration beads can also measure noise (known-answer → reviewer answer → MAP distance) |
| `agents/process-drift-monitor.md` | Add noise trend analysis from review-passes.jsonl |
| `skills/sdlc-normalize/SKILL.md` | Add decision-noise-summary.yaml to resume artifact list |
| `references/artifact-templates.md` | Add decision-noise-summary.yaml to Task Artifacts table |
| `hooks/hooks.json` | Add validate-decision-noise-summary.sh PostToolUse hook |
| `hooks/tests/test-hooks.sh` | Add decision-noise summary validation tests |
| `README.md` | Add noise artifacts, hook, noise metrics |

### Files Unchanged but Consuming

| File | Consumes |
|------|----------|
| `references/fft-decision-trees.md` | Cue precision data feeds FFT recalibration (via evolve) |
| `agents/losa-observer.md` | Outcome confirmations feed noise-events.jsonl |
| `references/stressor-library.yaml` | High-noise findings may become new stressor candidates |

---

## Scope Boundary

### In scope (Phase 3b)

- Review passes JSONL ledger (system-level canonical)
- MAP vector definition (5 dimensions, 1-5 scale)
- Per-task decision-noise-summary.yaml (derived view)
- Anti-anchoring protocol (blind-first → precedent-exposed)
- Repeat-review sampling model
- Natural frequency conversion for probability claims
- Soft escalation conditions (advisory-only)
- Cue/outcome capture for FFT validation
- Noise events ledger (outcome joins)
- Validation hook + tests
- Rules file (sampling rates, escalation thresholds)
- Integration with orchestrate, adversarial, arbitration, evolve, gate

### Out of scope

- Hard blocking on noise signals (deferred until 50+ repeat-review baseline)
- Automated FFT recalibration (evolve proposes, Conductor decides)
- Reference class database (Phase 3b captures reference_class_id; the class catalog is a v2 concern)
- Noise-based model selection (choosing reviewer model based on noise history)

---

## First Implementation Slice

The smallest high-value slice:
1. Add blind-first MAP scoring to arbiter pre-synthesis passes
2. Add repeat-review pairing for a sampled subset of AQS beads
3. Store probability claims as natural frequencies when a reference class exists
4. Report advisory-only rollups in the quality SLO layer

This lands the two highest-value mechanisms first: structured dimension scoring and measured repeat-review noise.
