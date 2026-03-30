# Stressor Harvesting + Barbell Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SDLC antifragile — a closed loop where telemetry selects tasks for controlled stress, observed failures are harvested into reusable stressors, and recurring fragility triggers subtraction.

**Architecture:** Stressor library (persistent YAML with Lindy lifecycle), stress session artifact (per-task YAML), FFT-15 sampling decision tree with deterministic seed, 6-step stress pipeline (select → apply → observe → harvest → subtract → update library), system JSONL ledgers, validation hook, and integration across orchestrate/harden/adversarial/evolve/gate skills.

**Tech Stack:** YAML (schemas), JSONL (system ledgers), Bash + Python3/PyYAML (scripts), Markdown (docs/commands)

**Spec:** `docs/specs/2026-03-30-stressor-harvesting-design.md`

---

### Task 1: Create stressor library seed + shared library

**Files:**
- Create: `references/stressor-library.yaml`
- Create: `scripts/lib/stressor-lib.sh`

- [ ] **Step 1: Create the initial stressor library**

Write `references/stressor-library.yaml` with the schema from the spec. Start with an empty `stressors: []` list — the library grows from real failures, not speculative entries.

```yaml
# Stressor Library — persistent, Lindy-weighted catalog
# Grows from real failures via harvest-stressors.sh
# Updated by update-stressor-library.sh after each stress session
schema_version: 1
last_updated: "2026-03-30T00:00:00Z"

stressors: []
# Each entry:
#   id: STR-NNN
#   name: short description
#   category: concurrency | boundary | state | auth | input | dependency | context_gap | defense_assumption
#   source: {type, task_id, artifact_ref}
#   description: what the stressor does
#   probe_template: parameterized probe text
#   applicable_when: {cynefin: [], tags: []}
#   severity: high | medium | low
#   times_applied: 0
#   times_caught: 0
#   catch_rate: null
#   first_harvested: ISO 8601
#   last_applied: null
#   lindy_status: provisional | established | retired
```

- [ ] **Step 2: Create the shared library**

Write `scripts/lib/stressor-lib.sh` with helpers for:
- `compute_sampling_seed` — `sha256(task_id)` → float [0,1) for deterministic probabilistic cues
- `evaluate_fft15` — reads quality-budget state, clean streak, bead metadata → returns FULL|TARGETED|SAMPLED|ANTI_TURKEY|HORMETIC|SKIP
- `select_applicable_stressors` — matches library entries against bead cynefin/tags, prefers established over provisional
- `compute_stress_yield` — caught / applied
- `compute_lindy_transition` — determines if a stressor should promote or retire
- `now_utc` — ISO 8601 timestamp

The FFT-15 logic must use the deterministic seed for probabilistic cues (SAMPLED 50%, ANTI_TURKEY 30%, HORMETIC 10%).

```bash
#!/bin/bash
# stressor-lib.sh — Shared helpers for stressor harvesting
set -euo pipefail

compute_sampling_seed() {
  local task_id="$1"
  local hex
  hex=$(echo -n "$task_id" | shasum -a 256 | cut -c1-8)
  python3 -c "print(int('$hex', 16) / 0xFFFFFFFF)"
}

evaluate_fft15() {
  local budget_state="$1" clean_streak="$2" has_complex_security="$3" profile="$4" seed="$5"
  # Cue 1: INVESTIGATE or EVOLVE → SKIP
  if [[ "$profile" == "INVESTIGATE" || "$profile" == "EVOLVE" ]]; then echo "SKIP"; return; fi
  # Cue 2: DEPLETED → FULL
  if [[ "$budget_state" == "depleted" ]]; then echo "FULL"; return; fi
  # Cue 3: complex + security_sensitive → TARGETED
  if [[ "$has_complex_security" == "true" ]]; then echo "TARGETED"; return; fi
  # Cue 4: WARNING → SAMPLED (50%)
  if [[ "$budget_state" == "warning" ]]; then
    if [ "$(echo "$seed < 0.50" | bc -l)" -eq 1 ]; then echo "SAMPLED"; else echo "SKIP"; fi
    return
  fi
  # Cue 5: clean_streak >= 5 → ANTI_TURKEY (30%)
  if [ "$clean_streak" -ge 5 ]; then
    if [ "$(echo "$seed < 0.30" | bc -l)" -eq 1 ]; then echo "ANTI_TURKEY"; else echo "SKIP"; fi
    return
  fi
  # Cue 6: HORMETIC (10%)
  if [ "$(echo "$seed < 0.10" | bc -l)" -eq 1 ]; then echo "HORMETIC"; else echo "SKIP"; fi
}

compute_stress_yield() {
  local applied="$1" caught="$2"
  if [ "$applied" -eq 0 ]; then echo "0.0"; return; fi
  echo "scale=2; $caught / $applied" | bc
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
```

Make executable: `chmod +x scripts/lib/stressor-lib.sh`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/stressor-library.yaml scripts/lib/stressor-lib.sh
git commit -m "feat: add stressor library seed and shared helpers

Empty stressor library (grows from real failures). Shared lib with
deterministic FFT-15 sampling (sha256 seed), stressor selection,
stress yield computation, and Lindy lifecycle transitions."
```

---

### Task 2: Create stress pipeline scripts

**Files:**
- Create: `scripts/select-stressors.sh`
- Create: `scripts/harvest-stressors.sh`
- Create: `scripts/update-stressor-library.sh`
- Create: `scripts/append-system-stress.sh`

- [ ] **Step 1: Create stressor selection script**

Write `scripts/select-stressors.sh`. Takes `<task-dir>` and `<stressor-library-path>`. Reads quality-budget.yaml, hazard-defense-ledger.yaml (if exists), and the stressor library. Uses python3+PyYAML to match applicable stressors by cynefin domain and tags. Outputs a YAML list of selected stressor+bead pairs to stdout or a file.

Add PyYAML dependency guard at top.

- [ ] **Step 2: Create stressor harvest script**

Write `scripts/harvest-stressors.sh`. Takes `<task-dir>`. Reads `stress-session.yaml` and extracts findings that don't match existing stressors. Proposes new stressor entries with `lindy_status: provisional`. Outputs candidate YAML for Conductor review.

Add PyYAML dependency guard.

- [ ] **Step 3: Create library update script**

Write `scripts/update-stressor-library.sh`. Takes `<task-dir>` and `<stressor-library-path>` and `<project-dir>`. Reads `stress-session.yaml` results, updates stressor `times_applied`, `times_caught`, `catch_rate`, `last_applied`. Evaluates Lindy transitions:
- `provisional` → `established` when `times_applied >= 3` and `catch_rate > 0`
- `provisional` → `retired` when `times_applied >= 5` and `catch_rate == 0`
- `established` → `retired` when `times_applied >= 10` and last 5 all misses

Emits events to `<project-dir>/docs/sdlc/system-stress-events.jsonl` for promotions, retirements, and significant catch_rate changes (> 20% delta).

Add PyYAML dependency guard.

- [ ] **Step 4: Create system stress append script**

Write `scripts/append-system-stress.sh`. Takes `<task-dir>` and `<project-dir>`. Reads final `stress-session.yaml`, builds JSONL entry, appends to `docs/sdlc/system-stress.jsonl`.

Add PyYAML dependency guard.

- [ ] **Step 5: Make all executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/select-stressors.sh scripts/harvest-stressors.sh scripts/update-stressor-library.sh scripts/append-system-stress.sh
git add scripts/select-stressors.sh scripts/harvest-stressors.sh scripts/update-stressor-library.sh scripts/append-system-stress.sh
git commit -m "feat: add stress pipeline scripts

select-stressors.sh matches library entries to task beads.
harvest-stressors.sh extracts new stressor candidates from findings.
update-stressor-library.sh manages Lindy lifecycle + emits events.
append-system-stress.sh writes to system-stress.jsonl."
```

---

### Task 3: Create schema documentation

**Files:**
- Create: `references/stressor-schema.md`

- [ ] **Step 1: Create the schema doc**

Write `references/stressor-schema.md` from the design spec. Include:
- Stressor library YAML schema (all fields with Lindy lifecycle rules)
- Stress session YAML schema (all fields with sampling_reason enum, sampling_seed)
- System stress JSONL + events JSONL schemas
- FFT-15 decision tree definition
- Stress pipeline steps reference
- Via-negativa subtraction log format

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/stressor-schema.md
git commit -m "docs: add stressor harvesting schema reference

Canonical schemas for stressor library, stress session, system
ledgers, FFT-15 sampling, pipeline steps, and subtraction log."
```

---

### Task 4: Add FFT-15 to decision trees

**Files:**
- Modify: `references/fft-decision-trees.md`

- [ ] **Step 1: Add FFT-15**

At the end of the FFT definitions (after FFT-14), add FFT-15: Stress Sampling. Reproduce the full 6-cue tree from the spec with the deterministic seed note.

- [ ] **Step 2: Update FFT-11 cross-reference**

In FFT-11 (Budget Allocation), add a note: "If FFT-15 returns FULL or TARGETED for this task, override budget to HIGH regardless of domain priority."

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/fft-decision-trees.md
git commit -m "feat: add FFT-15 (Stress Sampling) and update FFT-11 cross-reference

6-cue decision tree with deterministic sha256 seed for reproducible
probabilistic sampling. FFT-11 now overrides to FULL/HIGH for
stress-sampled tasks."
```

---

### Task 5: Create validation hook + tests + fixtures

**Files:**
- Create: `hooks/scripts/validate-stress-session.sh`
- Create: `hooks/tests/fixtures/stress-valid/stress-session.yaml`
- Create: `hooks/tests/fixtures/stress-missing/stress-session.yaml`
- Create: `hooks/tests/fixtures/stress-malformed/stress-session.yaml`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create the validation hook**

Write `hooks/scripts/validate-stress-session.sh`. PostToolUse hook that only triggers on files ending with `stress-session.yaml`. Validates: YAML parse (PyYAML with grep fallback), required fields (schema_version, task_id, artifact_status, sampling_reason), artifact_status enum (planned|active|final), sampling_reason enum, required sections (selection, stressors_applied, harvest, subtraction_log, summary). Exit 0=pass, exit 2=reject. Make executable.

- [ ] **Step 2: Create test fixtures**

Valid fixture with one stressor application. Missing fixture with only schema_version + task_id. Malformed fixture with invalid YAML.

- [ ] **Step 3: Update hooks.json and test-hooks.sh**

Add PostToolUse entry. Add 4 test cases using temp-file + run_test pattern (same as quality budget and HDL tests). Update test count.

- [ ] **Step 4: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (50/50).

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-stress-session.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/stress-valid/stress-session.yaml hooks/tests/fixtures/stress-missing/stress-session.yaml hooks/tests/fixtures/stress-malformed/stress-session.yaml
git commit -m "feat: add stress session validation hook with tests

PostToolUse hook validates stress-session.yaml structure on Write/Edit.
4 test cases with 3 fixtures."
```

---

### Task 6: Create /stress command

**Files:**
- Create: `commands/stress.md`

- [ ] **Step 1: Create the command**

Write `commands/stress.md`:

```markdown
---
name: stress
description: "Manually invoke barbell stress testing on the current task"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

Manually trigger stress testing for the current SDLC task.

1. Read the current task's `quality-budget.yaml` and `hazard-defense-ledger.yaml` (if exists)
2. Run `scripts/select-stressors.sh` to select applicable stressors from `references/stressor-library.yaml`
3. Create `stress-session.yaml` with `sampling_reason: manual`
4. Present selected stressors and sampling rationale to user for approval
5. On approval, apply stressors during the next AQS/hardening cycle
6. After completion, run `scripts/harvest-stressors.sh` and `scripts/update-stressor-library.sh`

Use this when you want to proactively stress-test work that FFT-15 would otherwise skip.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add commands/stress.md
git commit -m "feat: add /stress command for manual stress invocation"
```

---

### Task 7: Wire stress into orchestrate lifecycle

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

- [ ] **Step 1: Add FFT-15 evaluation in Execute phase**

In the Execute phase (Phase 4), after the reuse-first protocol step and before runner dispatch, add:

```markdown
**Stress sampling (FFT-15):** Before dispatching runners, evaluate FFT-15 from `references/fft-decision-trees.md` using quality-budget.yaml state, clean streak from system-stress.jsonl, bead complexity, and the deterministic seed (`sha256(task_id)`). If FFT-15 returns anything other than SKIP, create `stress-session.yaml` with `artifact_status: planned` and the selected stressors. Stressor probes are applied during AQS (Step 4) alongside domain probes.
```

- [ ] **Step 2: Add anti-turkey logic to Phase 0**

In Phase 0 (Normalize), after the evolve auto-trigger check, add:

```markdown
**Anti-turkey check:** Read `docs/sdlc/system-stress.jsonl` for the last N tasks. If the clean streak (consecutive tasks with zero escapes across quality-budget and HDL) is >= 5, flag in the normalization report: "Anti-turkey sampling active — suspicious clean streak ({N} tasks). FFT-15 will apply 30% random sampling to this task."
```

- [ ] **Step 3: Add stress gates**

Add Synthesize gate:
```markdown
**Stress Synthesize gate (stressed tasks only):** stress-session.yaml exists with artifact_status `active` or higher. All stressor applications have results (no pending). Harvest section reviewed.
```

Add Complete gate:
```markdown
**Stress Complete gate (stressed tasks only):** artifact_status is `final`. Stressor library updated. System stress ledger entry appended. Subtraction candidates logged.
```

- [ ] **Step 4: Add stress artifacts to inventory**

```markdown
- `stress-session.yaml` — Stress session artifact (created during Execute for sampled tasks). Schema: `references/stressor-schema.md`.
- `system-stress.jsonl` — Append-only system stress ledger
- `system-stress-events.jsonl` — Stressor lifecycle events (promotions, retirements)
```

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat: wire stress pipeline into orchestrate lifecycle

Add FFT-15 evaluation in Execute, anti-turkey check in Phase 0,
stress Synthesize/Complete gates, stress artifacts to inventory."
```

---

### Task 8: Wire stress into harden and adversarial skills

**Files:**
- Modify: `skills/sdlc-harden/SKILL.md`
- Modify: `skills/sdlc-adversarial/SKILL.md`
- Modify: `skills/sdlc-adversarial/scaling-heuristics.md`

- [ ] **Step 1: Update harden SKILL.md**

In the premortem step (Step 0), add: "Before generating premortem failure modes, consult `references/stressor-library.yaml` for stressors applicable to this bead's domain and tags. Inject applicable stressor scenarios into the premortem prompt as seed failure modes."

Add: "If `stress-session.yaml` exists for this task, the hardening pipeline receives the stress session as additional input. Stressor probes that were `caught` during AQS feed into the hardening targets."

- [ ] **Step 2: Update adversarial SKILL.md**

Add to the red team dispatch section: "For stress-sampled tasks (FFT-15 != SKIP), stressor-selected probes from `stress-session.yaml:stressors_applied` run alongside domain probes. Each stressor probe is dispatched as a directed guppy or sonnet strike (depending on severity). Results are recorded back in `stress-session.yaml`."

- [ ] **Step 3: Update scaling-heuristics.md**

In FFT-11 budget section, add: "If FFT-15 returns FULL or TARGETED for this task, override the guppy budget to HIGH (20-40) regardless of the domain priority level."

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-harden/SKILL.md skills/sdlc-adversarial/SKILL.md skills/sdlc-adversarial/scaling-heuristics.md
git commit -m "feat: wire stressor library into harden and adversarial pipelines

Premortem consults stressor library for seed failure modes.
Red team dispatches stressor probes alongside domain probes.
FFT-11 overrides to HIGH budget for stress-sampled tasks."
```

---

### Task 9: Update evolve, gate, and reference files

**Files:**
- Modify: `skills/sdlc-evolve/SKILL.md`
- Modify: `skills/sdlc-gate/SKILL.md`
- Modify: `references/quality-slos.md`
- Modify: `references/anti-patterns.md`
- Modify: `references/calibration-protocol.md`

- [ ] **Step 1: Update evolve SKILL.md**

Add a new evolution bead type: "**Subtraction review** — consume `subtraction_log` entries across stress sessions in `system-stress.jsonl`. When 3+ independent sessions flag the same mechanism, propose formal removal. Also consume stressor retirement events from `system-stress-events.jsonl` as signals that certain defense patterns are no longer catching anything."

- [ ] **Step 2: Update gate SKILL.md**

After the HDL checklist, add:

```markdown
### Stress Session (stressed tasks only)
- Does `stress-session.yaml` exist for stress-sampled tasks?
- Is `artifact_status` appropriate? (`planned` for Execute, `active` for Synthesize, `final` for Complete)
- Are all stressor applications resolved (no pending results)?
- Has the harvest section been reviewed?
```

- [ ] **Step 3: Update quality-slos.md**

Add two new tracked metrics:
```markdown
| stress_yield | Stress session catch rate | >= 0.10 per stressed task | Stressor library effectiveness |
| clean_streak_length | Consecutive tasks with zero escapes | Monitor (no SLO — anti-turkey signal) | Turkey problem early warning |
```

- [ ] **Step 4: Update anti-patterns.md**

Add:
```markdown
### Turkey Complacency

**Source:** Nassim Nicholas Taleb (The Black Swan, Antifragile)
**Pattern:** Relaxing scrutiny because recent tasks have been clean. A long clean streak is not evidence of quality — it may indicate that stressors have stopped, not that the system has improved.
**Consequence:** Hidden brittleness accumulates undisturbed until a real failure arrives.
**What to do instead:** Increase skeptical sampling during clean streaks (FFT-15 anti-turkey cue). Maintain minimum stress even during healthy periods (hormetic baseline).
```

- [ ] **Step 5: Update calibration-protocol.md**

Add: "When designing planted defects for calibration beads, consult `references/stressor-library.yaml` for `established` stressors with high catch rates. These represent proven failure modes that the system should detect. Prefer library-sourced defects over ad-hoc invention."

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-evolve/SKILL.md skills/sdlc-gate/SKILL.md references/quality-slos.md references/anti-patterns.md references/calibration-protocol.md
git commit -m "feat: wire stress into evolve, gate, and reference surfaces

Add subtraction review evolution bead. Add stress session gate checks.
Add stress_yield and clean_streak SLIs. Add Turkey Complacency
anti-pattern. Wire stressor library into calibration bead design."
```

---

### Task 10: Update agents

**Files:**
- Modify: `agents/reliability-conductor.md`
- Modify: `agents/process-drift-monitor.md`

- [ ] **Step 1: Update reliability-conductor.md**

In the premortem step, add: "Before generating failure modes, read `references/stressor-library.yaml` and select entries where `applicable_when` matches the bead's cynefin domain and scope tags. Inject these as seed scenarios: 'Consider whether {stressor.description} applies to this bead.'"

- [ ] **Step 2: Update process-drift-monitor.md**

Add two new drift signals:
```markdown
- Clean streak detection: if `docs/sdlc/system-stress.jsonl` shows 5+ consecutive tasks with zero escapes, flag as anti-turkey signal
- Stress yield trend: if stress_yield across last 5 stressed tasks is declining (stressors catching less), flag as potential stressor library staleness
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add agents/reliability-conductor.md agents/process-drift-monitor.md
git commit -m "feat: wire stressor library into agents

Reliability-conductor premortem consults library for seed failures.
Process-drift-monitor detects clean streaks and stress yield trends."
```

---

### Task 11: Update normalize, artifact-templates, and docs

**Files:**
- Modify: `skills/sdlc-normalize/SKILL.md`
- Modify: `references/artifact-templates.md`
- Modify: `README.md`

- [ ] **Step 1: Update normalize SKILL.md**

Add `stress-session.yaml (if exists)` to the resume artifact list.

- [ ] **Step 2: Update artifact-templates.md**

Add to Task Artifacts table:
```markdown
| Stress session | `stress-session.yaml` | Phase 4 (Execute) | If stress-sampled — gates Synthesize and Complete |
```

- [ ] **Step 3: Update README.md**

Add stress artifacts to artifact table:
```markdown
| Stress Session | `docs/sdlc/active/{task-id}/stress-session.yaml` | Barbell stress testing, stressor application tracking |
| System Stress | `docs/sdlc/system-stress.jsonl` | Cross-task stress yield, clean streak tracking |
| System Stress Events | `docs/sdlc/system-stress-events.jsonl` | Stressor lifecycle events |
| Stressor Library | `references/stressor-library.yaml` | Persistent stressor catalog |
```

Update hook count (increment by 1) and add hook table row:
```markdown
| validate-stress-session.sh | PostToolUse | **Blocking** — stress session schema validation |
```

Add `/stress` to command list if a command table exists.

Update test count to match new total.

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-normalize/SKILL.md references/artifact-templates.md README.md
git commit -m "docs: update normalize, artifact-templates, and README for stress

Add stress-session.yaml to resume list and artifact table. Add stress
artifacts, hook, and command to README."
```

---

### Task 12: Final verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (50/50).

- [ ] **Step 2: Verify all new files exist**

```bash
ls -la references/stressor-library.yaml references/stressor-schema.md scripts/lib/stressor-lib.sh scripts/select-stressors.sh scripts/harvest-stressors.sh scripts/update-stressor-library.sh scripts/append-system-stress.sh hooks/scripts/validate-stress-session.sh hooks/tests/fixtures/stress-valid/stress-session.yaml hooks/tests/fixtures/stress-missing/stress-session.yaml hooks/tests/fixtures/stress-malformed/stress-session.yaml commands/stress.md
```

Expected: All 12 files exist.

- [ ] **Step 3: Verify FFT-15 exists in decision trees**

```bash
grep -n "FFT-15" references/fft-decision-trees.md
```

Expected: FFT-15 definition present with 6 cues and deterministic seed note.

- [ ] **Step 4: Verify stressor library is empty but valid**

```bash
python3 -c "import yaml; d=yaml.safe_load(open('references/stressor-library.yaml')); print(f'schema: {d[\"schema_version\"]}, stressors: {len(d[\"stressors\"])}')"
```

Expected: `schema: 1, stressors: 0`

- [ ] **Step 5: Verify deterministic sampling**

```bash
cd /Users/q/.claude/plugins/sdlc-os
source scripts/lib/stressor-lib.sh
SEED1=$(compute_sampling_seed "test-task-001")
SEED2=$(compute_sampling_seed "test-task-001")
echo "Seed 1: $SEED1, Seed 2: $SEED2"
[ "$SEED1" = "$SEED2" ] && echo "PASS: deterministic" || echo "FAIL: non-deterministic"
```

Expected: Both seeds identical — deterministic.

- [ ] **Step 6: Spot-check key files**

Read and confirm:
1. `skills/sdlc-orchestrate/SKILL.md` — has FFT-15 evaluation, anti-turkey check, stress gates
2. `skills/sdlc-harden/SKILL.md` — premortem consults stressor library
3. `skills/sdlc-adversarial/SKILL.md` — stressor probes dispatched alongside domain probes
4. `skills/sdlc-adversarial/scaling-heuristics.md` — FFT-11 overrides for stressed tasks
5. `skills/sdlc-evolve/SKILL.md` — subtraction review evolution bead
6. `references/anti-patterns.md` — Turkey Complacency entry
7. `README.md` — updated hook count, stress artifacts, /stress command
