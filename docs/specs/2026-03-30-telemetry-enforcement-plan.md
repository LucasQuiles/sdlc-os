# Telemetry Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SDLC telemetry gates enforceable — collapse 21 manual Conductor steps into 2 automation scripts that derive, validate, and append all required artifacts.

**Architecture:** Shared `classify_task_lanes()` function for phase-stable lane detection, deterministic gate checker (task-local + system ledger), synthesize/complete automation scripts, advisory hook on state.md writes, idempotent backfill for existing tasks.

**Tech Stack:** Bash (scripts, hooks), Python3/PyYAML (YAML parsing in gate checker), JSONL (ledger verification)

**Spec:** `docs/specs/2026-03-30-telemetry-enforcement-design.md`

**Slice order:** Shared helper + gate checker → automation scripts → hook + tests → append duplicate guards → backfill

---

### Task 1: Add classify_task_lanes() to sdlc-common.sh + create gate checker

**Files:**
- Modify: `scripts/lib/sdlc-common.sh`
- Create: `scripts/check-sdlc-gates.sh`

- [ ] **Step 1: Add classify_task_lanes() to sdlc-common.sh**

Read `scripts/lib/sdlc-common.sh`. After the existing functions, add the `classify_task_lanes()` function from the spec's "Classification in scripts" section. The function:
- Takes `<task-dir> <task-id> <project-dir>`
- Sets globals: `HAS_BEADS`, `IS_STPA`, `IS_AQS`, `IS_STRESSED`
- Artifact-first: checks for HDL/stress-session/dn-summary existence
- Bead-metadata fallback: grep for bold-markdown Cynefin/Security fields
- Review-passes fallback: grep for task_id in review-passes.jsonl

- [ ] **Step 2: Create check-sdlc-gates.sh**

Create `scripts/check-sdlc-gates.sh`. Takes `<task-dir> <target-phase> --project-dir <dir>`. Sources `sdlc-common.sh`, calls `classify_task_lanes()`.

**Synthesize checks:**
- `quality-budget.yaml` exists with `artifact_status: ready` (if HAS_BEADS)
- `hazard-defense-ledger.yaml` exists with `artifact_status: active`+ (if IS_STPA)
- `stress-session.yaml` exists with `artifact_status: active`+ (if IS_STRESSED)
- `decision-noise-summary.yaml` exists with `artifact_status: partial`+ (if IS_AQS)
- `mode-convergence-summary.yaml` exists with `artifact_status: partial`+ (if HAS_BEADS)

**Complete checks (task-local):**
- All of the above with `artifact_status: final`
- `quality-budget.yaml` has `sli_readings` non-null and `budget_state` computed

**Complete checks (system ledger):**
- `system-budget.jsonl` contains `task_id` (if HAS_BEADS)
- `system-hazard-defense.jsonl` contains `task_id` (if IS_STPA)
- `system-stress.jsonl` contains `task_id` (if IS_STRESSED)
- `system-mode-convergence.jsonl` contains `task_id` (if HAS_BEADS)

Each check: print PASS/FAIL to stderr, accumulate failures, exit 0 if all pass, exit 1 if any fail. For tasks with no beads, warn but don't fail.

Make executable. Commit both.

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/lib/sdlc-common.sh scripts/check-sdlc-gates.sh
git commit -m "feat: add classify_task_lanes() and check-sdlc-gates.sh

Shared classification function (artifact-first, bead-metadata fallback)
ensures phase-stable lane detection. Gate checker validates task-local
artifacts AND system ledger entries for synthesize/complete transitions."
```

---

### Task 2: Create synthesize and complete automation scripts

**Files:**
- Create: `scripts/run-synthesize-gates.sh`
- Create: `scripts/run-complete-gates.sh`

- [ ] **Step 1: Create run-synthesize-gates.sh**

From the spec. Sources `sdlc-common.sh`, calls `classify_task_lanes()`, then runs applicable derivation scripts:
1. `derive-quality-budget.sh --status ready` (if HAS_BEADS)
2. `derive-hazard-defense-summary.sh --status active` (if IS_STPA + HDL exists)
3. `derive-decision-noise-summary.sh --status partial` (if IS_AQS, with `|| warn`)
4. `derive-mode-convergence-summary.sh --status partial` (if HAS_BEADS)
5. `check-sdlc-gates.sh synthesize`

All script calls use `$SCRIPT_DIR/` prefix. Make executable.

- [ ] **Step 2: Create run-complete-gates.sh**

From the spec. Sources `sdlc-common.sh`, calls `classify_task_lanes()`, then:
1. Finalize quality budget (`--status final`, if HAS_BEADS)
2. Finalize HDL (`--status final`, if IS_STPA)
3. Finalize decision-noise summary (`--status final`, if IS_AQS)
4. Finalize stress session (write `artifact_status: final` to YAML + `update-stressor-library.sh`, if IS_STRESSED)
5. Finalize mode-convergence (`--status final`, if HAS_BEADS)
6. Append to all applicable system ledgers
7. `check-sdlc-gates.sh complete`

Stress finalization explicitly writes `artifact_status: final` via python3 before calling `update-stressor-library.sh`. Stressor library path anchored to `$SCRIPT_DIR/../references/stressor-library.yaml`.

All script calls use `$SCRIPT_DIR/` prefix. Make executable. Commit both.

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/run-synthesize-gates.sh scripts/run-complete-gates.sh
git commit -m "feat: add synthesize and complete gate automation scripts

run-synthesize-gates.sh derives all applicable artifacts.
run-complete-gates.sh finalizes artifacts + appends system ledgers.
Both use classify_task_lanes() for phase-stable classification."
```

---

### Task 3: Create advisory hook + tests

**Files:**
- Create: `hooks/scripts/warn-phase-transition.sh`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create the advisory hook**

From the spec. Triggers on state.md Write/Edit. Parses `current-phase:` from YAML frontmatter (not date grep). For `synthesize` or `complete` transitions, re-runs `check-sdlc-gates.sh` against filesystem state. Emits `HOOK_WARNING` on failure. Never blocks (exit 0 always).

Make executable.

- [ ] **Step 2: Create test fixtures and update hooks.json**

Add PostToolUse entry for `warn-phase-transition.sh`, matcher `"Write|Edit"`, timeout 15.

Create test fixtures:
- `hooks/tests/fixtures/state-synthesize.json` — state.md write with `current-phase: synthesize`
- `hooks/tests/fixtures/state-complete.json` — state.md write with `current-phase: complete`
- `hooks/tests/fixtures/state-execute.json` — state.md write with `current-phase: execute` (no warning)
- `hooks/tests/fixtures/state-non-state.json` — non-state.md file write (skip)

Note: The hook calls `check-sdlc-gates.sh` which will fail for test fixtures (no real task dir). The hook should handle this gracefully (warn, not crash). Tests verify: non-state files are skipped (exit 0), state.md files trigger the check path.

- [ ] **Step 3: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (62/62 — 58 existing + 4 new).

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/warn-phase-transition.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/state-*.json
git commit -m "feat: add advisory phase-transition hook

Warns when state.md current-phase changes to synthesize/complete
without passing gate check. Parses YAML frontmatter, never blocks."
```

---

### Task 4: Add duplicate guards to append scripts

**Files:**
- Modify: `scripts/append-system-budget.sh`
- Modify: `scripts/append-system-hazard-defense.sh`
- Modify: `scripts/append-system-stress.sh`
- Modify: `scripts/append-system-mode-convergence.sh`

- [ ] **Step 1: Add duplicate-task-id guard to each append script**

For each of the 4 scripts, before the `echo "$ENTRY" >> "$LEDGER"` line, add:

```bash
# Duplicate guard: skip if task_id already in ledger
if [ -f "$LEDGER" ] && grep -qF "\"$TASK_ID\"" "$LEDGER" 2>/dev/null; then
  echo "SKIP: $TASK_ID already in $(basename "$LEDGER") (idempotent)" >&2
  exit 0
fi
```

This matches the pattern from `pass_exists()` in decision-noise-lib.sh — grep for the task_id string before appending.

Read each file to find the exact insertion point (before the append line).

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/append-system-budget.sh scripts/append-system-hazard-defense.sh scripts/append-system-stress.sh scripts/append-system-mode-convergence.sh
git commit -m "fix: add duplicate-task-id guards to all append scripts

Prevents double-append on rerun/crash-recovery. grep -qF for task_id
before appending to system JSONL ledgers. Same pattern as pass_exists()
in decision-noise-lib.sh."
```

---

### Task 5: Create backfill script

**Files:**
- Create: `scripts/backfill-telemetry.sh`

- [ ] **Step 1: Create the backfill script**

From the spec. Idempotent and resumable:
- For each task with `beads/*.md` files
- Check each artifact independently (don't short-circuit on first)
- Check each ledger entry independently (task_in_ledger guard)
- Skip derivation if artifact already exists
- Skip append if ledger already has task_id

Make executable.

- [ ] **Step 2: Test on the sdlc-os plugin tasks**

```bash
cd /Users/q/.claude/plugins/sdlc-os
bash scripts/backfill-telemetry.sh docs/sdlc/active/ .
```

Expected: Creates quality-budget.yaml and mode-convergence-summary.yaml for tasks with bead data. Appends to system ledgers. Reports per-task results.

- [ ] **Step 3: Verify idempotency**

Run the same command again. Expected: All "already exists" / "already has" messages, zero new appends.

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/backfill-telemetry.sh
git commit -m "feat: add idempotent telemetry backfill script

Retroactively derives quality-budget.yaml and mode-convergence-summary
for tasks with bead data. Per-artifact + per-ledger independent checks.
Safe to rerun after partial failures."
```

---

### Task 6: Update orchestrate SKILL.md, gate SKILL.md, and README

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`
- Modify: `skills/sdlc-gate/SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Add REQUIRED gate automation callout to orchestrate**

Add the prominent callout from the spec near the top of the workflow section:

```markdown
## REQUIRED: Gate Automation

Before Synthesize: `bash scripts/run-synthesize-gates.sh <task-dir> <project-dir>`
Before Complete: `bash scripts/run-complete-gates.sh <task-dir> <project-dir>`

These scripts automatically:
- Detect which telemetry lanes apply (STPA, AQS, stress) using deterministic rules
- Run all applicable derivation scripts in the correct order
- Append to all applicable system JSONL ledgers
- Validate both task-local artifacts AND system ledger entries
- Report pass/fail with details

Do NOT manually update state.md phase log without running the appropriate gate script first.
```

- [ ] **Step 2: Update gate SKILL.md**

Reference `check-sdlc-gates.sh` as the enforcement mechanism. Add: "The gate checker validates both task-local artifacts (quality-budget.yaml, hazard-defense-ledger.yaml, etc.) AND system ledger entries (system-budget.jsonl, etc.). Run via `scripts/run-synthesize-gates.sh` or `scripts/run-complete-gates.sh` which automate the full derivation + validation flow."

- [ ] **Step 3: Update README**

Add gate automation section. Update hook count (increment by 1). Add `warn-phase-transition.sh` to hook table. Update test count.

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md skills/sdlc-gate/SKILL.md README.md
git commit -m "docs: add REQUIRED gate automation to orchestrate, gate, README

Conductor must run run-synthesize-gates.sh / run-complete-gates.sh
before phase transitions. Gate checker validates task-local + system
ledger artifacts. Advisory hook warns on ungated transitions."
```

---

### Task 7: End-to-end verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass.

- [ ] **Step 2: Verify all new files exist**

```bash
ls -la scripts/check-sdlc-gates.sh scripts/run-synthesize-gates.sh scripts/run-complete-gates.sh scripts/backfill-telemetry.sh hooks/scripts/warn-phase-transition.sh
```

Expected: All 5 files exist, executable.

- [ ] **Step 3: Verify classify_task_lanes exists in sdlc-common.sh**

```bash
grep -n "classify_task_lanes" scripts/lib/sdlc-common.sh
```

Expected: Function definition present.

- [ ] **Step 4: Verify duplicate guards in append scripts**

```bash
grep -l "already in\|SKIP.*idempotent" scripts/append-system-*.sh
```

Expected: All 4 append scripts have the guard.

- [ ] **Step 5: Run backfill on sdlc-os plugin tasks**

```bash
bash scripts/backfill-telemetry.sh docs/sdlc/active/ .
```

Expected: Creates artifacts for tasks with bead data. System ledger entries appended.

- [ ] **Step 6: Verify backfill idempotency**

Run backfill again. Expected: All "already exists" / "already has" messages.

- [ ] **Step 7: Verify gate checker works on a backfilled task**

```bash
# Pick a task that was backfilled (has quality-budget.yaml)
TASK=$(ls -d docs/sdlc/active/*/quality-budget.yaml 2>/dev/null | head -1 | xargs dirname)
if [ -n "$TASK" ]; then
  bash scripts/check-sdlc-gates.sh "$TASK" complete --project-dir .
fi
```

Expected: Gate check reports results (may pass or fail depending on which artifacts exist).

- [ ] **Step 8: Spot-check key files**

1. `scripts/lib/sdlc-common.sh` — has `classify_task_lanes()` with artifact-first + bead-metadata fallback
2. `scripts/check-sdlc-gates.sh` — checks task-local AND system ledger
3. `scripts/run-synthesize-gates.sh` — calls classify_task_lanes, derives all applicable, checks gates
4. `scripts/run-complete-gates.sh` — finalizes all (including decision-noise + stress), appends ledgers, checks gates
5. `skills/sdlc-orchestrate/SKILL.md` — has REQUIRED gate automation callout
6. All 4 append scripts — have duplicate guards
