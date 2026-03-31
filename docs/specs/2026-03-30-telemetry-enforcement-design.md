# Telemetry Enforcement — Gate Automation for Thinker Enhancement Artifacts

**Date:** 2026-03-30
**Status:** Draft
**Profile:** REPAIR
**Problem:** 41 active tasks, zero telemetry artifacts. Gates are prose instructions, not enforced checkpoints.

---

## Problem Statement

The SDLC-OS has 5 telemetry pipelines (Quality Budget, Hazard/Defense Ledger, Stressor Harvesting, Decision-Noise Controls, Mode/Convergence Signals) with working derivation scripts, validation hooks, and system ledgers. But zero data flows because:

1. **Gates are prose.** The orchestrate SKILL.md says "run derive-quality-budget.sh before Synthesize" but nothing enforces this.
2. **No hook blocks phase transitions.** Existing hooks validate artifact FORMAT on Write/Edit, but nothing checks artifact EXISTENCE at phase boundaries.
3. **The Conductor must remember 21 manual steps.** No checklist, no automation, no accountability.
4. **Bead turbulence is never populated.** Beads carry `{L0: 0, L1: 0, ...}` placeholders that are never incremented during execution.

## Design

### 1. Gate Checker Script (`scripts/check-sdlc-gates.sh`)

A deterministic script that validates all required artifacts for a given phase transition. Called by the Conductor before updating state.md, or by a hook.

```
Usage: check-sdlc-gates.sh <task-dir> <target-phase> [--project-dir <dir>]

Target phases: synthesize | complete

Exit codes:
  0 = all gates pass
  1 = gate failures (details on stderr)
  2 = usage error
```

**Synthesize gate checks:**
- quality-budget.yaml exists with artifact_status: ready
- All derived fields non-null (except estimate_s, sli_readings)
- For STPA tasks: hazard-defense-ledger.yaml exists with artifact_status: active+
- For stressed tasks: stress-session.yaml exists with artifact_status: active+

**Complete gate checks:**
- quality-budget.yaml exists with artifact_status: final
- sli_readings populated
- budget_state computed
- For STPA tasks: HDL artifact_status: final, all records resolved
- For stressed tasks: stress-session.yaml final
- decision-noise-summary.yaml exists (if AQS-engaged)
- mode-convergence-summary.yaml exists

### 2. Synthesize Automation Script (`scripts/run-synthesize-gates.sh`)

Runs all derivation scripts in the correct order, then validates:

```bash
#!/bin/bash
# 1. Derive quality budget (→ ready)
derive-quality-budget.sh "$TASK_DIR" --status ready

# 2. Derive HDL summary (if STPA task)
if [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  derive-hazard-defense-summary.sh "$TASK_DIR" --status active
fi

# 3. Classify execution mode
classify-execution-mode.sh "$TASK_DIR"

# 4. Derive decision-noise summary (if review-passes exist for this task)
derive-decision-noise-summary.sh "$TASK_ID" "$PROJECT_DIR"

# 5. Derive mode-convergence summary
derive-mode-convergence-summary.sh "$TASK_DIR" --status partial

# 6. Evaluate escalations
evaluate-escalations.sh "$TASK_ID" "$PROJECT_DIR"

# 7. Check all synthesize gates
check-sdlc-gates.sh "$TASK_DIR" synthesize
```

### 3. Complete Automation Script (`scripts/run-complete-gates.sh`)

Finalizes all artifacts and appends to system ledgers:

```bash
#!/bin/bash
# 1. Finalize quality budget
derive-quality-budget.sh "$TASK_DIR" --status final

# 2. Finalize HDL (if STPA task)
if [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  derive-hazard-defense-summary.sh "$TASK_DIR" --status final
fi

# 3. Finalize mode-convergence summary
derive-mode-convergence-summary.sh "$TASK_DIR" --status final

# 4. Append to all system ledgers
append-system-budget.sh "$TASK_DIR" "$PROJECT_DIR"
if [ -f "$TASK_DIR/hazard-defense-ledger.yaml" ]; then
  append-system-hazard-defense.sh "$TASK_DIR" "$PROJECT_DIR"
fi
if [ -f "$TASK_DIR/stress-session.yaml" ]; then
  append-system-stress.sh "$TASK_DIR" "$PROJECT_DIR"
fi
append-system-mode-convergence.sh "$TASK_DIR" "$PROJECT_DIR"

# 5. Check all complete gates
check-sdlc-gates.sh "$TASK_DIR" complete --project-dir "$PROJECT_DIR"
```

### 4. Hook Enforcement (Optional — Advisory First)

A `PostToolUse` hook on state.md writes that warns (not blocks) when phase transitions occur without gates passing. Advisory in v1 to avoid breaking existing workflows.

```json
{
  "matcher": "Write|Edit",
  "hooks": [{
    "type": "command",
    "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/warn-phase-transition.sh",
    "timeout": 15
  }]
}
```

The hook checks if the written file is `state.md`, detects phase transitions, and warns if the corresponding gate script hasn't been run.

### 5. Backfill Script (`scripts/backfill-telemetry.sh`)

Retroactively derives quality-budget.yaml for tasks that have bead data:

```bash
#!/bin/bash
# For each task with beads/*.md files containing Turbulence fields:
#   1. Run derive-quality-budget.sh --status final
#   2. Run classify-execution-mode.sh
#   3. Run derive-mode-convergence-summary.sh --status final
#   4. Append to system ledgers
```

### 6. Conductor Checklist Update

Add to `skills/sdlc-orchestrate/SKILL.md` a prominent callout:

```markdown
## REQUIRED: Gate Automation

Before Synthesize: `bash scripts/run-synthesize-gates.sh <task-dir> <project-dir>`
Before Complete: `bash scripts/run-complete-gates.sh <task-dir> <project-dir>`

These scripts run all derivation, classification, and validation automatically.
Do NOT manually update state.md phase log without running the appropriate gate script first.
```

---

## Implementation Surface

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/check-sdlc-gates.sh` | Deterministic gate validator for synthesize/complete |
| `scripts/run-synthesize-gates.sh` | Run all pre-Synthesize derivation + validation |
| `scripts/run-complete-gates.sh` | Finalize artifacts + append ledgers + validate |
| `scripts/backfill-telemetry.sh` | Retroactively derive telemetry for existing tasks |
| `hooks/scripts/warn-phase-transition.sh` | Advisory hook warning on ungated transitions |

### Files to Modify

| File | Change |
|------|--------|
| `skills/sdlc-orchestrate/SKILL.md` | Add prominent REQUIRED gate automation callout |
| `skills/sdlc-gate/SKILL.md` | Reference check-sdlc-gates.sh as the enforcement mechanism |
| `hooks/hooks.json` | Add warn-phase-transition.sh PostToolUse hook |
| `hooks/tests/test-hooks.sh` | Add tests for the new hook |
| `README.md` | Update with gate automation instructions |

---

## Scope

### In scope
- Gate checker script
- Synthesize/Complete automation scripts
- Backfill script for existing tasks
- Advisory phase-transition hook
- Orchestrate SKILL.md update
- Testing and verification

### Out of scope
- Blocking (non-advisory) hook enforcement (v2)
- Automatic turbulence population during bead execution (requires runner changes)
- Dashboard/visualization of system ledger data
