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

Read `scripts/lib/sdlc-common.sh`. After the existing functions, add the `classify_task_lanes()` function. The function:
- Takes `<task-dir> <task-id> <project-dir>`
- Sets globals: `HAS_BEADS`, `IS_STPA`, `IS_AQS`, `IS_STRESSED`

Classification rules (execution-grounded, not domain-inferred):
- `HAS_BEADS`: `beads/` directory exists with `*.md` files
- `IS_STPA`: artifact-first (`hazard-defense-ledger.yaml` exists), bead-metadata fallback (grep for bold-markdown `**Cynefin domain:**.*complex` or `**Security sensitive:**.*true`)
- `IS_AQS`: **artifact-only, NO bead-domain fallback.** Check `decision-noise-summary.yaml` exists OR `review-passes.jsonl` contains task_id. AQS can be skipped for Chaotic/Clear/ACCIDENTAL beads even when the domain would suggest it — only the actual execution record is authoritative.
- `IS_STRESSED`: `stress-session.yaml` exists (no fallback needed)

- [ ] **Step 2: Create check-sdlc-gates.sh**

Create `scripts/check-sdlc-gates.sh`. Takes `<task-dir> <target-phase> --project-dir <dir>`. Sources `sdlc-common.sh`, calls `classify_task_lanes()`.

**Synthesize checks:**
- `quality-budget.yaml` exists with `artifact_status: ready` (if HAS_BEADS)
- `quality-budget.yaml` has all derived fields non-null except `estimate_s` and `sli_readings` (per spec: "All derived fields non-null")
- `hazard-defense-ledger.yaml` exists with `artifact_status: active`+ (if IS_STPA)
- `stress-session.yaml` exists with `artifact_status: active`+ (if IS_STRESSED)
- `decision-noise-summary.yaml` exists with `artifact_status: partial`+ (if IS_AQS)
- `mode-convergence-summary.yaml` exists with `artifact_status: partial`+ (if HAS_BEADS)

**Complete checks (task-local):**
- All of the above with `artifact_status: final`
- `quality-budget.yaml` has `budget_state` computed (not null)
- `quality-budget.yaml` `sli_readings`: **relaxed in this phase.** sli_readings require project-specific deterministic checks (lint, tsc, test coverage) that the automation scripts cannot run generically. The gate checker WARNS on null sli_readings but does NOT fail. Full sli_readings enforcement is deferred until the Conductor or a project-specific hook populates them before calling run-complete-gates.sh.
- If IS_STPA: HDL has every record with `status` in {caught, escaped, accepted_residual} — no `open` records remain. `summary.coverage_state` is computed.
- If IS_STRESSED: `stress-session.yaml` has all stressor applications resolved (no pending results)
- If IS_AQS: `decision-noise-summary.yaml` has `artifact_status: final`

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

The hook parses `current-phase:` from the FILE on disk, not from the JSON fixture. Tests must create real temp state.md files with YAML frontmatter:

```bash
# In test-hooks.sh, create temp state.md files that the hook can read:
_pt_tmp=$(mktemp -d)
mkdir -p "$_pt_tmp/beads"

# state.md with current-phase: complete (should trigger warning — no artifacts)
cat > "$_pt_tmp/state.md" << 'YAML'
---
task-id: test-gate-task
current-phase: complete
---
# Test state
YAML

# JSON fixture points at the real temp state.md
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/state-complete.json"
run_test_advisory "warn: complete without artifacts" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/state-complete.json" "yes"

# state.md with current-phase: execute (should NOT trigger)
cat > "$_pt_tmp/state-exec.md" << 'YAML'
---
task-id: test-gate-task
current-phase: execute
---
YAML
_pt_json "$_pt_tmp/state-exec.md" "$_pt_tmp/state-execute.json"
# Rename to state.md for the hook to recognize it
cp "$_pt_tmp/state-exec.md" "$_pt_tmp/state.md"
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/state-execute.json"
run_test "skip: execute phase (no warning)" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/state-execute.json" 0

# state.md with current-phase: synthesize (should also trigger warning)
cat > "$_pt_tmp/state.md" << 'YAML'
---
task-id: test-gate-task
current-phase: synthesize
---
YAML
_pt_json "$_pt_tmp/state.md" "$_pt_tmp/state-synthesize.json"
run_test_advisory "warn: synthesize without artifacts" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/state-synthesize.json" "yes"

# Non-state.md file (should skip entirely)
_pt_json "/tmp/not-state.txt" "$_pt_tmp/non-state.json"
run_test "skip: non-state file" "$HOOKS_DIR/warn-phase-transition.sh" "$_pt_tmp/non-state.json" 0

rm -rf "$_pt_tmp"
```

The `_pt_json` helper writes a JSON fixture with the file_path pointing at the real temp file. The hook reads the file at that path and parses YAML frontmatter.

This tests:
1. complete transition with no artifacts → HOOK_WARNING emitted (advisory, exit 0)
2. synthesize transition with no artifacts → HOOK_WARNING emitted (advisory, exit 0)
3. execute transition → no warning, exit 0
4. non-state.md file → skip, exit 0

- [ ] **Step 3: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (62/62 — 58 existing + 4 new).

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/warn-phase-transition.sh hooks/hooks.json hooks/tests/test-hooks.sh
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

The 4 append scripts have different structures — 2 use shell `echo >> ledger`, 2 use Python `print() >> ledger`. Apply the guard in the appropriate language for each:

**Shell-based scripts** (`append-system-budget.sh`, `append-system-mode-convergence.sh`):
Before the `echo "$ENTRY" >> "$LEDGER"` line, add:
```bash
# Duplicate guard: skip if task_id already in ledger
if [ -f "$LEDGER" ] && grep -qF "\"$TASK_ID\"" "$LEDGER" 2>/dev/null; then
  echo "SKIP: $TASK_ID already in $(basename "$LEDGER") (idempotent)" >&2
  exit 0
fi
```

**`append-system-hazard-defense.sh`** (Python block at line 22, appends via `print() >> "$SYSTEM_LEDGER"` at line 63-64):

The Python code reads the ledger YAML and prints JSON to stdout, which the shell redirects to the ledger. The task_id is in `data['task_id']` and the ledger path is `$SYSTEM_LEDGER` (shell variable). Add the guard in SHELL before the Python block:

```bash
# Duplicate guard (before the python3 -c block)
if [ -f "$SYSTEM_LEDGER" ] && grep -qF "\"task_id\":\"$(python3 -c "import yaml; print(yaml.safe_load(open('$LEDGER'))['task_id'])")\"" "$SYSTEM_LEDGER" 2>/dev/null; then
  echo "SKIP: task already in $(basename "$SYSTEM_LEDGER") (idempotent)" >&2
  exit 0
fi
```

Insert this AFTER `[ -f "$LEDGER" ]` check (line 19) and BEFORE the `python3 -c` block (line 22).

**`append-system-stress.sh`** (Python heredoc at line 28, appends via `f.write()` at line 66-67):

The Python code receives both the session path and ledger path as `sys.argv[1]` and `sys.argv[2]`. The task_id is `session['task_id']` and the ledger path is `sys.argv[2]`. Add the guard INSIDE the Python block, after reading the session but before writing:

```python
# After "session = yaml.safe_load(f)" (line 35) and status check (line 37-40):
# Duplicate guard
import os
if os.path.exists(ledger_path):
    with open(ledger_path) as lf:
        task_id = session.get('task_id', '')
        for line in lf:
            if f'"task_id":"{task_id}"' in line or f'"task_id": "{task_id}"' in line:
                print(f'SKIP: {task_id} already in ledger (idempotent)', file=sys.stderr)
                sys.exit(0)
```

Insert after line 40 (status check) and before line 42 (summary extraction).

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

- [ ] **Step 5: Controlled end-to-end test with temp task fixture**

Create a synthetic task with beads, run both gate scripts, verify success AND failure cases:

```bash
# Create temp task with minimal bead data
_e2e=$(mktemp -d)
mkdir -p "$_e2e/beads"
cat > "$_e2e/state.md" << 'YAML'
---
task-id: e2e-gate-test
current-phase: execute
---
YAML

cat > "$_e2e/beads/B01.md" << 'YAML'
**Status:** merged
**Cynefin domain:** complicated
**Security sensitive:** false
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Dispatched at:** "2026-03-30T10:00:00Z"
**Review started at:** "2026-03-30T10:05:00Z"
**Completed at:** "2026-03-30T10:10:00Z"
YAML

PROJECT_E2E=$(mktemp -d)

# --- FAILURE CASE: synthesize gate should FAIL (no artifacts yet) ---
echo "=== Failure case: synthesize without artifacts ==="
bash scripts/check-sdlc-gates.sh "$_e2e" synthesize --project-dir "$PROJECT_E2E" 2>&1
SYNTH_EXIT=$?
echo "Exit code: $SYNTH_EXIT"
[ "$SYNTH_EXIT" -eq 1 ] && echo "PASS: gate correctly rejected" || echo "FAIL: gate should have rejected"

# --- SUCCESS CASE: run synthesize automation, then check ---
echo "=== Success case: run-synthesize-gates then check ==="
bash scripts/run-synthesize-gates.sh "$_e2e" "$PROJECT_E2E" 2>&1
bash scripts/check-sdlc-gates.sh "$_e2e" synthesize --project-dir "$PROJECT_E2E" 2>&1
SYNTH_EXIT2=$?
echo "Exit code: $SYNTH_EXIT2"
[ "$SYNTH_EXIT2" -eq 0 ] && echo "PASS: gate passed after automation" || echo "FAIL: gate should have passed"

# --- SUCCESS CASE: run complete automation, then check ---
echo "=== Success case: run-complete-gates then check ==="
bash scripts/run-complete-gates.sh "$_e2e" "$PROJECT_E2E" 2>&1
bash scripts/check-sdlc-gates.sh "$_e2e" complete --project-dir "$PROJECT_E2E" 2>&1
COMP_EXIT=$?
echo "Exit code: $COMP_EXIT"
[ "$COMP_EXIT" -eq 0 ] && echo "PASS: complete gate passed" || echo "FAIL: complete gate should have passed"

# --- Verify system ledger was populated ---
echo "=== System ledger check ==="
cat "$PROJECT_E2E/docs/sdlc/system-budget.jsonl" 2>/dev/null | head -1
[ -f "$PROJECT_E2E/docs/sdlc/system-budget.jsonl" ] && echo "PASS: system ledger populated" || echo "FAIL: system ledger empty"

# --- IDEMPOTENCY: run complete again, verify no duplicate ---
bash scripts/run-complete-gates.sh "$_e2e" "$PROJECT_E2E" 2>&1
LINES=$(wc -l < "$PROJECT_E2E/docs/sdlc/system-budget.jsonl" 2>/dev/null || echo 0)
echo "Ledger lines after rerun: $LINES"
[ "$LINES" -eq 1 ] && echo "PASS: no duplicate append" || echo "FAIL: duplicate detected"

rm -rf "$_e2e" "$PROJECT_E2E"
```

Expected results:
1. Synthesize without artifacts → exit 1 (PASS: correctly rejected)
2. Synthesize after automation → exit 0 (PASS: gate passed)
3. Complete after automation → exit 0 (PASS: gate passed — sli_readings null produces WARN, not failure)
4. System ledger populated with 1 entry
5. Rerun produces no duplicate (still 1 line)

- [ ] **Step 6: Run backfill on sdlc-os plugin tasks**

```bash
bash scripts/backfill-telemetry.sh docs/sdlc/active/ .
```

Expected: Creates artifacts for tasks with bead data. System ledger entries appended.

- [ ] **Step 7: Verify backfill idempotency**

Run backfill again. Expected: All "already exists" / "already has" messages.

- [ ] **Step 8: Spot-check key files**

1. `scripts/lib/sdlc-common.sh` — has `classify_task_lanes()` with artifact-first + bead-metadata fallback
2. `scripts/check-sdlc-gates.sh` — checks task-local AND system ledger
3. `scripts/run-synthesize-gates.sh` — calls classify_task_lanes, derives all applicable, checks gates
4. `scripts/run-complete-gates.sh` — finalizes all (including decision-noise + stress), appends ledgers, checks gates
5. `skills/sdlc-orchestrate/SKILL.md` — has REQUIRED gate automation callout
6. All 4 append scripts — have duplicate guards
