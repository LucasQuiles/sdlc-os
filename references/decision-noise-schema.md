# Decision-Noise Schema Reference

**Spec:** `docs/specs/2026-03-30-decision-noise-controls-design.md`
**Rules:** `references/decision-noise-rules.yaml`

---

## Review Pass JSONL Record

**Location:** `docs/sdlc/decision-noise/review-passes.jsonl`

One line per independent review pass. Append-only canonical ledger; per-task summaries are derived views.

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

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | int | yes | Record schema version. Always 1 in v1. |
| `review_pass_id` | string | yes | Globally unique ID. Idempotent write key. |
| `parent_review_pass_id` | string\|null | yes | Points to blind pass when this is a post-exposure revision. |
| `supersedes_review_pass_id` | string\|null | yes | Set when this pass explicitly replaces a prior pass (e.g., arbiter override). |
| `task_id` | string | yes | Task this review belongs to. |
| `bead_id` | string | yes | Bead within the task. |
| `decision_trace_id` | string | yes | Decision trace artifact ID. |
| `timestamp` | ISO 8601 | yes | UTC timestamp of record creation. |
| `review_stage` | enum | yes | See review_stages in rules file. |
| `reviewer_role` | string | yes | Role of the reviewing agent. |
| `reviewer_model` | string | yes | Model used for this pass. |
| `exposure_mode` | enum | yes | See exposure_modes in rules file. |
| `exposure_order` | int | yes | 0 = blind first pass; increments for each subsequent exposure. |
| `anchor_sources_seen` | array | yes | Precedent pack IDs or peer pass IDs seen before this pass. Empty on blind passes. |
| `anchor_verdicts_seen` | array | yes | Verdict objects from anchors seen. Empty on blind passes. |
| `anchor_map_targets_seen` | array | yes | MAP vector objects from anchors seen. Empty on blind passes. |
| `precedent_pack_id` | string\|null | yes | Precedent pack shown for this pass, or null. |
| `repeat_review_group_id` | string\|null | yes | Groups paired blind passes for noise measurement. Null if not a repeat-review bead. |
| `arbiter_group_id` | string | yes | Groups all passes for a single AQS session. |
| `map` | object | yes | MAP vector. See MAP Vector section. |
| `probability_judgments` | array | yes | Natural-frequency probability claims. |
| `heuristics` | object | yes | FFT cue tracking fields. |
| `verdict` | object | yes | Decision, severity, confidence. |

---

## Append-Only Invariants

1. **Immutable records.** No field is ever modified in place after a record is written.
2. **Idempotent write key.** `review_pass_id` is globally unique. Any attempt to append a record with a duplicate `review_pass_id` is silently rejected (not an error). Scripts must check existence before appending.
3. **Lineage via new records.** Post-exposure revisions are stored as NEW records with `parent_review_pass_id` pointing to the original blind pass. The blind pass is never modified.
4. **Supersession.** When an arbiter override explicitly replaces a prior pass, the new record sets `supersedes_review_pass_id` to the replaced pass ID. Both records remain in the ledger.
5. **Schema evolution.** Every record carries `schema_version`. Consumers must handle version differences gracefully and must not reject unknown fields.

---

## MAP Vector (Mediating Assessments Protocol)

The MAP vector forces independent dimension scoring before holistic synthesis. Reviewers score each dimension separately before arriving at a verdict, making verdict sensitivity visible across dimensions.

### 5 Blind Dimensions (scored before precedent exposure)

| Dimension | What it measures | Scale |
|-----------|-----------------|-------|
| `evidence_strength` | How well the claim is supported by concrete evidence | 1–5 |
| `impact_severity` | If true, how much user/system/compliance harm follows | 1–5 |
| `base_rate_frequency` | How often similar beads historically produced this issue class | 1–5 bucket + hits/sample/reference_class_id/reference_class_state |
| `pattern_familiarity` | How familiar this pattern feels to the reviewer based on their own judgment (blind — no precedent exposure) | 1–5 |
| `decision_confidence` | How stable the reviewer believes this pass is under re-review | 1–5 |

### 1 Post-Exposure Dimension (only on exposed passes)

| Dimension | What it measures | Scale |
|-----------|-----------------|-------|
| `precedent_match_delta` | How much the reviewer's assessment changed after seeing precedent packs. **Null on blind passes.** | −5 to +5 (negative = precedent weakened confidence; positive = strengthened) |

### base_rate_frequency Object

```json
{
  "bucket": 3,
  "hits": 3,
  "sample": 10,
  "reference_class_id": "complex-state-mutation-90d",
  "reference_class_state": "available"
}
```

- `bucket` (1–5): Translated frequency score used in MAP distance computation.
- `hits`: Count of matching events in the reference class. Null when state is not `available`.
- `sample`: Total size of the reference class. Null when state is not `available`.
- `reference_class_id`: Named reference class used for this judgment. Null when not applicable.
- `reference_class_state`: See reference_class_state enum below.

---

## reference_class_state Enum

| Value | Meaning | hits/sample |
|-------|---------|-------------|
| `available` | Class exists with >= 5 samples. Frequency judgment is backed by data. | Required (non-null) |
| `insufficient_history` | Class exists but has fewer than 5 samples. Too sparse to rely on. | Null |
| `not_applicable` | No meaningful reference class for this issue type. | Null |

### Null-Path Rules

- When `reference_class_state` is `insufficient_history` or `not_applicable`, the `hits`, `sample`, and `reference_class_id` fields MUST be null.
- The soft escalation for `unbacked_high_severity` does NOT fire for `insufficient_history` or `not_applicable`. These states represent explicitly novel claims, not negligently unbacked ones.
- The `unbacked_high_severity` escalation fires ONLY when `reference_class_state: available` AND a high-severity claim has null `hits`/`sample` — meaning a reference class exists and was not used.

---

## Per-Task decision-noise-summary.yaml Schema

**Location:** `docs/sdlc/active/{task-id}/decision-noise-summary.yaml`

Derived view computed from `review-passes.jsonl`. Not a canonical record — regenerate at any time from the ledger.

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
  weighted_verdict_agreement: null    # weighted agreement across paired blind reviews
  map_convergence_score: null         # dispersion across MAP vectors for same bead
  anchoring_drift_rate: null          # score movement after exposure to anchors
  natural_frequency_coverage: null    # share of probability claims backed by hits/sample
  high_severity_unbacked_claims: 0    # high-severity claims without frequency backing
  spot_check_coverage_rate: null      # repeat-reviewed beads / eligible beads

escalations:
  verdict_flips: 0
  map_divergence_2plus: 0
  anchoring_drift_2plus: 0
  unbacked_high_severity: 0
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | int | Schema version. Always 1 in v1. |
| `task_id` | string | Task this summary covers. |
| `artifact_status` | enum | `partial` = derived mid-task; `final` = derived after task completion. |
| `derived_at` | ISO 8601 | UTC timestamp when this summary was last computed. |
| `beads_reviewed` | int | Count of distinct bead_ids with at least one review pass. |
| `passes_total` | int | Total review pass records for this task. |
| `repeat_review_pairs` | int | Count of paired blind passes sharing a `repeat_review_group_id`. |
| `metrics.repeat_review_noise_index` | float\|null | Average MAP Euclidean distance across repeat-review pairs. Null if no pairs. |
| `metrics.weighted_verdict_agreement` | float\|null | Agreement rate across paired blind reviews, weighted by bead complexity. Null if no pairs. |
| `metrics.map_convergence_score` | float\|null | Inverse dispersion of MAP vectors for the same bead across passes. Lower = more scattered. |
| `metrics.anchoring_drift_rate` | float\|null | Proportion of exposed passes that show 2+ bucket shift toward anchor target. |
| `metrics.natural_frequency_coverage` | float\|null | Fraction of probability_judgments with non-null hits/sample. |
| `metrics.high_severity_unbacked_claims` | int | Count of high-severity claims with `reference_class_state: available` but null hits/sample. |
| `metrics.spot_check_coverage_rate` | float\|null | Repeat-reviewed beads divided by eligible beads (complex/complicated with AQS). |
| `escalations.verdict_flips` | int | Count of blind pairs with different decision class. |
| `escalations.map_divergence_2plus` | int | Count of pairs where evidence_strength or impact_severity differs by 2+ buckets. |
| `escalations.anchoring_drift_2plus` | int | Count of exposed passes with 2+ bucket shift toward anchor target. |
| `escalations.unbacked_high_severity` | int | Count of high-severity + available reference class + no hits/sample. |

---

## Noise Events JSONL Schema

**Location:** `docs/sdlc/decision-noise/noise-events.jsonl`

Late-arriving outcome data for cue validation. One line per outcome event.

```jsonl
{"review_pass_id":"rp_001","event":"outcome_confirmed|regression_detected|false_alarm_confirmed|cue_validated","task_id":"","date":"","details":""}
```

| Field | Description |
|-------|-------------|
| `review_pass_id` | Links back to the originating review pass. |
| `event` | Outcome type: `outcome_confirmed`, `regression_detected`, `false_alarm_confirmed`, `cue_validated`. |
| `task_id` | Task the outcome belongs to. |
| `date` | ISO 8601 date of observed outcome. |
| `details` | Free-form description of the observed outcome. |

Note: `noise-events.jsonl` has no automated producer in v1. Records are written manually or by the LOSA observer agent when late-arriving evidence surfaces.

---

## Anti-Anchoring Protocol

The core mechanism is sequence control — blind judgment before precedent exposure:

1. Reviewer receives bead evidence and decision trace metadata, but NOT prior verdicts or precedent packs.
2. Reviewer scores all 5 blind MAP dimensions and records a provisional verdict. `precedent_match_delta` is null.
3. System records the blind pass via `record-review-pass.sh`. The pass is immutable after write.
4. System reveals precedent packs or peer findings.
5. Reviewer may revise their assessment. The revision is stored as a NEW pass with:
   - `parent_review_pass_id` = blind pass ID
   - `exposure_order` incremented
   - `anchor_sources_seen`, `anchor_verdicts_seen`, `anchor_map_targets_seen` populated
   - `precedent_match_delta` scored (reviewer's own estimate of shift)

Anchoring drift is computable: compare blind pass MAP dimensions vs. post-exposure pass MAP dimensions in the direction of `anchor_map_targets_seen[0]`. Shift of 2+ buckets toward the anchor target triggers soft escalation.

---

## Soft Escalation Conditions

All escalations are advisory-only in v1. No hard gates.

| Condition | Trigger | Computable Definition |
|-----------|---------|----------------------|
| `verdict_flip` | Blind pair produces different decision class | `p1.verdict.decision != p2.verdict.decision` where p1 and p2 share `repeat_review_group_id` and both have `exposure_mode: blind_first` |
| `map_bucket_divergence` | `evidence_strength` or `impact_severity` differs by 2+ buckets | `abs(p1.map.evidence_strength - p2.map.evidence_strength) >= 2` OR `abs(p1.map.impact_severity - p2.map.impact_severity) >= 2` |
| `unbacked_high_severity` | High-severity claim with available reference class but no hits/sample | `claim.severity == "high" AND claim.hits is null AND map.base_rate_frequency.reference_class_state == "available"` |
| `anchoring_drift` | Post-exposure MAP shifts 2+ buckets toward anchor target | `abs(exposed_val - anchor_val) < abs(blind_val - anchor_val) AND abs(exposed_val - blind_val) >= 2` for any of evidence_strength, impact_severity, pattern_familiarity |

Thresholds (bucket counts) are read from `references/decision-noise-rules.yaml`, not hardcoded.

---

## Derived Metrics Formulas

### repeat_review_noise_index

Average MAP Euclidean distance across all repeat-review pairs for the task.

```
noise_index = mean(MAP_distance(p1, p2))
  for each (p1, p2) pair sharing repeat_review_group_id
  where both have exposure_mode: blind_first

MAP_distance(p1, p2) = sqrt(
  (p1.evidence_strength - p2.evidence_strength)^2 +
  (p1.impact_severity - p2.impact_severity)^2 +
  (p1.base_rate_frequency.bucket - p2.base_rate_frequency.bucket)^2 +
  (p1.pattern_familiarity - p2.pattern_familiarity)^2 +
  (p1.decision_confidence - p2.decision_confidence)^2
)
```

### natural_frequency_coverage

```
coverage = count(judgments where hits is not null) / count(all judgments)
```

### spot_check_coverage_rate

```
coverage = count(distinct bead_ids with repeat_review_group_id) /
           count(eligible beads)

eligible = complex beads with AQS + complicated beads with AQS
```

### anchoring_drift_rate

```
drift_rate = count(exposed passes with 2+ bucket shift toward anchor) /
             count(all exposed passes with parent_review_pass_id)
```

### SLO Targets (from quality-slos.md)

| Metric | Target | Direction |
|--------|--------|-----------|
| `repeat_review_noise_index` | < 2.0 | Lower is better |
| `natural_frequency_coverage` | >= 0.80 | Higher is better |
| `spot_check_coverage_rate` | >= sampling target | Higher is better |
