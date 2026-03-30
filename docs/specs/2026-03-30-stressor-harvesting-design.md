# Stressor Harvesting + Barbell Hardening — Phase 3a of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-30
**Status:** Draft
**Roadmap position:** Phase 3a of 5 (Quality Budget [DONE] → Hazard/Defense Ledger [DONE] → **Stressor Harvesting** → Decision-Noise Controls → Mode/Convergence Signals)
**Depends on:** Phase 1 (quality-budget.yaml), Phase 2 (hazard-defense-ledger.yaml)

---

## Problem Statement

Phase 3a exists in fragments but not as an antifragile learning loop.

The SDLC already has barbell allocation in FFT-11, Lindy-weighted trust for precedents, resilience-focused adversarial probing, and anti-pattern guidance against over-protection. But these detect failures without making stress produce adaptation.

Signals from quality-budget.yaml, AQS artifacts, LOSA observations, and the Hazard/Defense Ledger identify failures, escapes, and defense gaps. But those signals do not feed into a disciplined stressor pipeline. New failure modes are handled locally, then mostly disappear. The SDLC treats stress as something to survive, not something to selectively harvest.

Five operational failures:

1. New failure modes are not automatically harvested into a reusable stressor library
2. Hardening intensity is driven by bead class and local judgment, not consequence-first sampled stress
3. No deliberate stress injection at the workflow level — tests code paths more than control paths, context gaps, and defense assumptions
4. No via-negativa loop that removes brittle prompts, checks, or process steps when they create fragility
5. Long clean streaks reduce scrutiny instead of increasing skeptical sampling — hidden brittleness accumulates

### Goal

Make the SDLC antifragile: small, controlled stressors improve the system. Every genuine failure mode leaves behind durable adaptations:
- A new reusable stressor
- A new hardening recipe
- A new subtraction candidate
- A new sampling rule
- A new constitution or safety rule when warranted

For every task selected into the stress program, the system answers:
- What stressors were applied?
- Why was this task sampled?
- Which defenses held, failed, or were bypassed?
- What new stressors were harvested?
- What brittle mechanism should be removed, not expanded?

### Design Principle

Most tasks stay lightweight. A small sampled slice receives extreme scrutiny. Avoid the middle. Create a closed loop:

```
telemetry → sampling → stress → observation → harvest → adaptation
                                                  ↓
                                            subtraction of fragility
```

---

## Thinker Connections

| Concept | Source | What Phase 3a operationalizes |
|---------|--------|------------------------------|
| Antifragile triad | Taleb, Antifragile | System gets stronger from stress, not just survives it. Harvested stressors = compound improvement. |
| Hormesis | Taleb, Antifragile | Controlled dosing: sampled tasks get deliberate stress; most tasks stay light. Sweet spot, not overload. |
| Barbell strategy | Taleb, Antifragile | No medium scrutiny. Most tasks minimal (L0 only), sampled tasks maximum (full stress pipeline). FFT-11 extended. |
| Via negativa | Taleb, Antifragile | Subtraction log: every stress cycle asks "what can we remove?" Fragile mechanisms get cut, not patched. |
| Turkey problem | Taleb, Black Swan | Long clean streaks trigger increased sampling, not relaxation. Anti-turkey sampling rule. |
| Lindy effect | Taleb, Antifragile | Stressors that catch real bugs gain authority over time. New stressors are provisional. |

---

## Artifact Model

### Stressor Library (`references/stressor-library.yaml`)

Persistent, append-only, Lindy-weighted. The reusable stressor catalog that grows from real failures.

```yaml
schema_version: 1
last_updated: "2026-03-30T00:00:00Z"

stressors:
  - id: "STR-001"
    name: "state mutation ordering"
    category: concurrency | boundary | state | auth | input | dependency | context_gap | defense_assumption
    source:
      type: escape | aqs_finding | losa_catch | hdl_gap | premortem | calibration
      task_id: "wizard-modal-rebuild-20260328"
      artifact_ref: "HDL-B03-CA1-UCA2"
    description: "Apply state mutation before guard commit completes"
    probe_template: |
      Verify that {target} handles the case where state mutation
      is applied before the guard state is fully committed.
    applicable_when:
      cynefin: [complex, complicated]
      tags: [state_management, concurrent_access, modal_transitions]
    severity: high | medium | low
    times_applied: 0
    times_caught: 0
    catch_rate: null          # times_caught / times_applied (Lindy signal)
    first_harvested: "2026-03-30T00:00:00Z"
    last_applied: null
    lindy_status: provisional | established | retired
    #   provisional: < 3 applications (or >= 3 with catch_rate == 0 — still unproven)
    #   established: >= 3 applications with catch_rate > 0 (proven value)
    #   retired: (provisional + times_applied >= 5 + catch_rate == 0) OR
    #            (established + times_applied >= 10 + catch_rate dropped to 0 over last 5)
    #   Lifecycle: provisional can retire directly if it never catches anything after 5 tries.
    #   Established stressors retire only after a longer runway (10+ applications, last 5 all misses).
```

### Stress Session Record (`docs/sdlc/active/{task-id}/stress-session.yaml`)

Per-task stress session artifact. Created when a task is sampled for barbell hardening.

```yaml
schema_version: 1
task_id: ""
artifact_status: planned | active | final
sampling_reason: consequence_sensitive | budget_warning | random_sample | anti_turkey | budget_depleted | hormetic | manual
#   consequence_sensitive: FFT-15 TARGETED (security_sensitive + complex)
#   budget_warning: FFT-15 SAMPLED (budget_state WARNING, 50% sample)
#   random_sample: deprecated alias — use hormetic or anti_turkey
#   anti_turkey: FFT-15 ANTI_TURKEY (clean_streak >= 5, 30% sample)
#   budget_depleted: FFT-15 FULL (budget_state DEPLETED)
#   hormetic: FFT-15 HORMETIC (10% baseline random)
#   manual: user-directed /stress command
derived_at: "2026-03-30T00:00:00Z"
last_updated: "2026-03-30T00:00:00Z"

selection:
  sampling_seed: 0.0           # deterministic: sha256(task_id) → float [0,1)
  quality_budget_state: healthy | warning | depleted
  clean_streak_length: 0      # consecutive tasks with zero escapes
  complexity_weight: 0.0      # from quality-budget.yaml
  security_sensitive_beads: 0 # count
  hdl_open_ucas: 0            # from hazard-defense-ledger.yaml

stressors_applied:
  - stressor_id: "STR-001"
    bead_id: "B03"
    target: "modal state transition guard"
    result: caught | held | not_applicable
    catch_layer: null          # L0 | L1 | L2 | L2_5 | L2_75 | escaped
    finding_ref: null
    notes: ""

  - stressor_id: "STR-NEW-001"   # ad hoc stressor discovered during session
    bead_id: "B03"
    target: "rollback path on partial commit"
    result: caught
    catch_layer: L2_5
    finding_ref: "AQS-042"
    notes: "New failure mode — harvest into stressor library"

harvest:
  new_stressors: []            # STR-IDs created from this session's findings
  new_hardening_recipes: []    # recipe IDs added to hardening patterns
  subtraction_candidates: []   # mechanisms flagged for removal
  constitution_rules: []       # code constitution rules proposed
  safety_rules: []             # safety constraint rules proposed

subtraction_log:
  - mechanism: ""
    reason: ""
    action: removed | simplified | flagged_for_review
    evidence: ""

summary:
  stressors_applied: 0
  stressors_caught: 0
  stressors_held: 0
  new_stressors_harvested: 0
  subtraction_candidates: 0
  stress_yield: 0.0            # stressors_caught / stressors_applied
```

### System Stress Ledger (`docs/sdlc/system-stress.jsonl`)

One line per completed stress session. Feeds longitudinal analysis.

```jsonl
{"task_id":"","date":"","sampling_reason":"","stressors_applied":0,"stressors_caught":0,"stress_yield":0.0,"new_stressors_harvested":0,"subtraction_candidates":0,"clean_streak_at_sample":0,"quality_budget_state":"","complexity_weight":0.0}
```

### System Stress Events (`docs/sdlc/system-stress-events.jsonl`)

Late-arriving corrections and stressor retirement events. **Producer: `scripts/update-stressor-library.sh`** — emits events when stressors are promoted, retired, or reclassified during the library update step.

```jsonl
{"stressor_id":"STR-001","event":"retirement|promotion|catch_rate_update|reclassified","date":"","details":"","task_id":""}
```

Event types:
- `retirement`: stressor moved to `retired` (provisional never caught, or established gone stale)
- `promotion`: stressor moved from `provisional` to `established`
- `catch_rate_update`: significant catch_rate change (> 20% delta)
- `reclassified`: severity or category changed based on new evidence

---

## Sampling Model

### Who Gets Stressed

Not every task. The barbell principle: most tasks stay light, a few get maximum stress.

**Mandatory sampling triggers:**
- `quality_budget.budget_state == depleted` — all beads get stress
- Any bead with `security_sensitive: true` AND `cynefin_domain: complex` — always
- Manual `/stress` command — user-directed

**Probabilistic sampling triggers:**
- `quality_budget.budget_state == healthy` AND `clean_streak_length >= 5` — anti-turkey: 30% sample rate (suspicion increases with clean streak)
- `quality_budget.budget_state == warning` — 50% sample rate
- Random baseline: 10% of all tasks regardless of budget state (hormetic minimum)

**Never stressed:**
- Profile: INVESTIGATE (read-only)
- Profile: EVOLVE (system improvement, not user code)
- Clear beads under healthy budget with clean_streak < 5

### Sampling Decision Tree (FFT-15)

```
Cue 1: Is profile INVESTIGATE or EVOLVE?
  → YES → SKIP stress
  → NO  → continue

Cue 2: Is quality_budget.budget_state DEPLETED?
  → YES → FULL stress (all beads)
  → NO  → continue

Cue 3: Does any bead have security_sensitive AND cynefin complex?
  → YES → TARGETED stress (those beads)
  → NO  → continue

Cue 4: Is budget_state WARNING?
  → YES → SAMPLED (50% of complicated+ beads)
  → NO  → continue

Cue 5: Is clean_streak_length >= 5?
  → YES → ANTI_TURKEY (30% random sample, priority to highest-complexity beads)
  → NO  → continue

Cue 6: Random(0,1) < 0.10?
  → YES → HORMETIC (10% baseline, 1-2 beads, random selection)
  → NO  → SKIP stress
```

Outcomes: FULL | TARGETED | SAMPLED | ANTI_TURKEY | HORMETIC | SKIP

**Reproducibility:** Probabilistic cues (SAMPLED 50%, ANTI_TURKEY 30%, HORMETIC 10%) use a deterministic seed derived from `sha256(task_id)` truncated to a float in [0,1). This ensures the same task always gets the same sampling decision on reruns/resumes. The seed is recorded in `stress-session.yaml:selection.sampling_seed` for audit. Implementation: `echo -n "$TASK_ID" | shasum -a 256 | cut -c1-8` → interpret as hex → divide by 0xFFFFFFFF.

---

## Stress Pipeline

For each sampled task:

### 1. Select Stressors

From `references/stressor-library.yaml`, select applicable stressors by matching:
- `applicable_when.cynefin` against bead cynefin_domain
- `applicable_when.tags` against bead scope/content
- Prefer `established` stressors (Lindy-validated) over `provisional`
- Always include at least one `provisional` stressor if available (test the new ones)

If HDL exists for this task, also derive stressors from open UCAs that lack defense coverage.

### 2. Apply Stressors

For each selected stressor + bead pair:
- Construct a probe from the `probe_template`, filling in the target
- Dispatch as a guppy swarm probe (Haiku) during the AQS phase
- Or dispatch as a directed red team strike (Sonnet) for high-severity stressors
- Record result in `stress-session.yaml`

### 3. Observe Results

For each stressor application:
- `caught`: the stressor found a real issue → record catch_layer and finding_ref
- `held`: the defense worked, stressor found nothing → good signal
- `not_applicable`: stressor didn't apply to this context → don't count

### 4. Harvest

After all stressors are applied:

**New stressors:** Any finding that doesn't match an existing stressor becomes a candidate for a new stressor entry. The Conductor reviews and adds to `references/stressor-library.yaml` with `lindy_status: provisional`.

**Hardening recipes:** Patterns that appear in 2+ sessions become reusable hardening recipes (referenced from `skills/sdlc-harden/SKILL.md`).

**Constitution/safety rules:** Findings with `severity: high` that represent systematic weaknesses are proposed as code constitution or safety constraint additions.

### 5. Subtract

The via-negativa step. After each stress session:

**Ask:** "What mechanism in this task's pipeline was:
- Redundant (caught by a later layer but added no value)?
- Brittle (broke under stress in a way that made things worse)?
- Over-specified (added complexity without catching anything)?"

Record candidates in `subtraction_log`. After 3 independent sessions flag the same mechanism, escalate to Evolve for formal removal review.

### 6. Update Library

- Increment `times_applied` for each stressor used
- Increment `times_caught` for each stressor that found something
- Recompute `catch_rate`
- Promote `provisional` → `established` when `times_applied >= 3` and `catch_rate > 0`
- Retire `provisional` → `retired` when `times_applied >= 5` and `catch_rate == 0` (never proved value — Lindy says remove)
- Retire `established` → `retired` when `times_applied >= 10` and catch_rate over last 5 applications == 0 (was valuable, now stale)
- Emit retirement events to `system-stress-events.jsonl` via `update-stressor-library.sh` (see below)

---

## Phase Gates

### Stress Session Gate (before Synthesize, stressed tasks only)

- `stress-session.yaml` exists with `artifact_status: active` or higher
- All stressor applications have a result (no pending/unanswered)
- Harvest section has been reviewed (new_stressors, subtraction_candidates populated or explicitly empty)

### Complete Gate (stressed tasks only)

- `artifact_status: final`
- `stressor_library.yaml` updated with new stressors (if any harvested)
- System stress ledger entry appended
- Subtraction candidates logged

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `references/stressor-library.yaml` | Persistent stressor catalog with Lindy-weighted entries |
| `references/stressor-schema.md` | Schema docs for all stress artifacts |
| `references/fft-decision-trees.md` (FFT-15) | New decision tree for stress sampling |
| `scripts/lib/stressor-lib.sh` | Shared helpers: stressor selection, library updates, yield computation |
| `scripts/select-stressors.sh` | Reads task context + library → selects applicable stressors |
| `scripts/harvest-stressors.sh` | Post-session: extracts new stressor candidates from findings |
| `scripts/update-stressor-library.sh` | Updates application counts, catch rates, Lindy promotions/retirements. **Also produces** `system-stress-events.jsonl` entries for promotions, retirements, and significant catch_rate changes. |
| `scripts/append-system-stress.sh` | Appends to system-stress.jsonl |
| `hooks/scripts/validate-stress-session.sh` | PostToolUse hook for stress-session.yaml |
| `hooks/tests/fixtures/stress-valid/stress-session.yaml` | Test fixture |
| `hooks/tests/fixtures/stress-missing/stress-session.yaml` | Test fixture |
| `hooks/tests/fixtures/stress-malformed/stress-session.yaml` | Test fixture |
| `commands/stress.md` | `/stress` command for manual stress invocation |

### Files to Modify

| File | Change |
|------|--------|
| `skills/sdlc-orchestrate/SKILL.md` | Add FFT-15 evaluation in Execute phase. Add stress session creation for sampled tasks. Add stress gates to Synthesize/Complete. Add stress artifacts to inventory. |
| `skills/sdlc-orchestrate/SKILL.md` (Phase 0) | Add anti-turkey logic: if system-stress.jsonl shows clean_streak >= 5, flag for suspicious-clean sampling |
| `skills/sdlc-harden/SKILL.md` | Wire stressor library into premortem step (premortems check library for applicable stressors). Add stress-session.yaml as input to hardening pipeline. |
| `skills/sdlc-adversarial/SKILL.md` | Wire stressor-selected probes into red team dispatch. Stressor probes run alongside domain probes. |
| `skills/sdlc-adversarial/scaling-heuristics.md` | Update FFT-11 to account for stress-sampled tasks (override budget to FULL for stressed beads). |
| `skills/sdlc-evolve/SKILL.md` | Add subtraction review evolution bead: consume subtraction_log across sessions, propose removals. Add stressor retirement as evolution signal. |
| `skills/sdlc-gate/SKILL.md` | Add stress session gate checks for sampled tasks. |
| `references/fft-decision-trees.md` | Add FFT-15 (Stress Sampling). Update FFT-11 to reference FFT-15 output. |
| `references/quality-slos.md` | Add stress_yield as a tracked metric. Add clean_streak_length as an anti-turkey SLI. |
| `references/anti-patterns.md` | Add "Turkey Complacency" anti-pattern (relaxing scrutiny on clean streaks). |
| `references/calibration-protocol.md` | Wire stressor library into calibration bead design (planted defects drawn from library). |
| `agents/reliability-conductor.md` | Update premortem step to consult stressor library for applicable failure modes. |
| `agents/process-drift-monitor.md` | Add clean-streak detection. Add stress_yield trend analysis from system-stress.jsonl. |
| `hooks/hooks.json` | Add validate-stress-session.sh PostToolUse hook. |
| `hooks/tests/test-hooks.sh` | Add stress session validation tests. |
| `skills/sdlc-normalize/SKILL.md` | Add stress-session.yaml to resume artifact list. |
| `references/artifact-templates.md` | Add stress-session.yaml to Task Artifacts table. |
| `README.md` | Add stress artifacts, hook, and /stress command. |

### Files Unchanged but Consuming

| File | Consumes |
|------|----------|
| `references/code-constitution.md` | New rules proposed from high-severity stress findings |
| `references/safety-constraints.md` | New constraints proposed from stress findings |
| `agents/latent-condition-tracer.md` | Stressor catch patterns feed latent condition analysis |

---

## Scope Boundary

### In scope (Phase 3a)

- Stressor library (persistent catalog with Lindy lifecycle)
- Stress session artifact (per-task when sampled)
- FFT-15 sampling decision tree
- Stressor selection, harvest, and library update scripts
- Via-negativa subtraction log
- System stress ledger + events
- Validation hook + tests
- /stress command for manual invocation
- Integration with orchestrate, harden, adversarial, evolve, gate
- Anti-turkey clean-streak sampling

### Out of scope

- Automated calibration bead generation from stressor library (v2)
- Stressor effectiveness visualization
- Cross-task stressor pattern clustering (feeds Phase 3c mode/convergence)
- Automated process subtraction (evolve beads propose, Conductor decides)
