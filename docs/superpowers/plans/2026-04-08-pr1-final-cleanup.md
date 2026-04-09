# PR #1 Final Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address all remaining deferred items from 4 review rounds of PR #1 before merge.

**Architecture:** 5 independent cleanup tasks — no interdependencies. All changes on branch `feat/colony-hardening-and-hook-portability`.

**Tech Stack:** Bash, Python 3.12, TypeScript

---

### Task 1: Fix /home/q/ paths in E2E bead docs

**Files:**
- Modify: `docs/sdlc/active/colony-e2e-20260404/beads/E2E-01-colony-loop-test.md:11`
- Modify: `docs/sdlc/active/colony-e2e-20260404/beads/E2E-02-handoff-update.md:11-12`
- Modify: `docs/sdlc/active/colony-e2e-20260404/beads/E2E-03-open-questions.md:11-12`

These bead files contain absolute `/home/q/LAB/...` paths in their `Decision trace` and `Deterministic checks` fields. Replace with relative paths.

- [ ] **Step 1: Fix E2E-01-colony-loop-test.md**

Change line 11 from:
```
**Decision trace:** /home/q/LAB/sdlc-os/docs/sdlc/active/colony-e2e-20260404/beads/E2E-01-decision-trace.md
```
to:
```
**Decision trace:** docs/sdlc/active/colony-e2e-20260404/beads/E2E-01-decision-trace.md
```

- [ ] **Step 2: Fix E2E-02-handoff-update.md**

Change line 11 from:
```
**Decision trace:** /home/q/LAB/sdlc-os/docs/sdlc/active/colony-e2e-20260404/beads/E2E-02-decision-trace.md
```
to:
```
**Decision trace:** docs/sdlc/active/colony-e2e-20260404/beads/E2E-02-decision-trace.md
```

Change line 12 — this references an external repo, so remove the absolute path but keep the command form:
```
**Deterministic checks:** wc -l HANDOFF-DEDUP-CONSOLIDATION.md  # in WhatSoup repo
```

- [ ] **Step 3: Fix E2E-03-open-questions.md**

Change line 11 from:
```
**Decision trace:** /home/q/LAB/sdlc-os/docs/sdlc/active/colony-e2e-20260404/beads/E2E-03-decision-trace.md
```
to:
```
**Decision trace:** docs/sdlc/active/colony-e2e-20260404/beads/E2E-03-decision-trace.md
```

Change line 12 — external repo reference:
```
**Deterministic checks:** grep -c 'Open Questions' docs/superpowers/specs/2026-04-04-colony-orchestration-design.md  # in WhatSoup repo
```

- [ ] **Step 4: Verify no /home/q/ remains in bead docs**

Run: `grep -rn '/home/q/' docs/sdlc/active/colony-e2e-20260404/`
Expected: No output

- [ ] **Step 5: Commit**

```bash
git add docs/sdlc/active/colony-e2e-20260404/
git commit -m "fix(docs): replace absolute /home/q/ paths with relative paths in E2E beads"
```

---

### Task 2: Unify hook script sourcing pattern

**Files:**
- Modify: `hooks/scripts/validate-decision-noise-summary.sh:5`
- Modify: `hooks/scripts/validate-hazard-defense-ledger.sh:5`
- Modify: `hooks/scripts/validate-mode-convergence-summary.sh:5`
- Modify: `hooks/scripts/validate-quality-budget.sh:5`
- Modify: `hooks/scripts/validate-stress-session.sh:5`
- Modify: `hooks/scripts/warn-phase-transition.sh:4`

6 scripts use the compact `source "$(dirname "$0")/../lib/common.sh"` form. The other 11 use the robust `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` + `source "$SCRIPT_DIR/../lib/common.sh"` form. Unify to the robust pattern.

- [ ] **Step 1: Fix validate-decision-noise-summary.sh**

Replace line 5:
```bash
source "$(dirname "$0")/../lib/common.sh"
```
with:
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
```

- [ ] **Step 2: Repeat for remaining 5 scripts**

Apply the identical replacement in:
- `hooks/scripts/validate-hazard-defense-ledger.sh` (line 5)
- `hooks/scripts/validate-mode-convergence-summary.sh` (line 5)
- `hooks/scripts/validate-quality-budget.sh` (line 5)
- `hooks/scripts/validate-stress-session.sh` (line 5)
- `hooks/scripts/warn-phase-transition.sh` (line 4)

- [ ] **Step 3: Verify syntax**

Run: `for f in hooks/scripts/*.sh; do bash -n "$f" || echo "FAIL: $f"; done`
Expected: No FAILs

- [ ] **Step 4: Commit**

```bash
git add hooks/scripts/*.sh
git commit -m "refactor: unify hook script sourcing to SCRIPT_DIR pattern"
```

---

### Task 3: Simplify _aggregate_bead_cost API

**Files:**
- Modify: `colony/deacon.py:827-836`
- Modify: `colony/deacon_test.py` (update test callsite)

The `_aggregate_bead_cost` method has parameter sprawl from the `_cost_map` cache injection. The two loop callers (`check_for_work`, `spawn_conductor`) already call `_build_cost_map()` and use `cost_map.get(bid, 0.0)` inline. Remove `_aggregate_bead_cost` entirely and have callers use `_build_cost_map` + `.get()` directly.

- [ ] **Step 1: Check current callers**

Run: `grep -n '_aggregate_bead_cost' colony/deacon.py colony/deacon_test.py`

Identify all call sites. The loop callers should already be using `cost_map.get(bid, 0.0)`. If `_aggregate_bead_cost` is still called in the loops, replace with `cost_map.get(bid, 0.0)`.

- [ ] **Step 2: Check if _aggregate_bead_cost is called outside loops**

If it is only called from `check_for_work` and `spawn_conductor` (which already have `cost_map`), and from the test, then we can simplify. If there are other callers, keep the method but remove the `_cost_map` param.

- [ ] **Step 3: Update based on findings**

If safe to remove: delete `_aggregate_bead_cost`, update loop callers to `cost_map.get(bid, 0.0)`, update test to call `_build_cost_map` directly and assert on the returned dict.

If not safe to remove: simplify the signature to just `_aggregate_bead_cost(self, bead_id, log_path=None)` (remove `_cost_map`).

- [ ] **Step 4: Run tests**

Run: `cd colony && python3 -m pytest deacon_test.py -q 2>&1 | tail -5`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add colony/deacon.py colony/deacon_test.py
git commit -m "refactor: simplify cost aggregation API — callers use _build_cost_map directly"
```

---

### Task 4: Fix _fire_and_forget docstring

**Files:**
- Modify: `colony/deacon.py:279`

- [ ] **Step 1: Update docstring**

Change:
```python
        """Schedule a coroutine as a fire-and-forget task. No-op outside event loop."""
```
to:
```python
        """Schedule a coroutine as a fire-and-forget task. Closes the coroutine outside event loop."""
```

- [ ] **Step 2: Commit**

```bash
git add colony/deacon.py
git commit -m "fix(docs): clarify _fire_and_forget docstring — closes coroutine, not no-op"
```

---

### Task 5: Remove numbered step comments from brick-hooks.ts

**Files:**
- Modify: `colony/brick-hooks.ts`

Lines 40, 46, 52, 60, 76 have `// 1.`, `// 2.`, etc. comments that describe obvious sequential flow and create renumbering maintenance burden.

- [ ] **Step 1: Read the file**

Read `colony/brick-hooks.ts` lines 36-80.

- [ ] **Step 2: Remove or simplify numbered comments**

Remove the numbered prefixes. Keep only comments that explain WHY, not WHAT:
- `// 1. Verify bead output exists` → remove (the `existsSync` call is self-explanatory)
- `// 2. Resolve API key before any file I/O` → keep as `// Fail fast if API key is missing — avoids wasted file I/O`
- `// 3. Read bead output` → remove
- `// 4. Try to read git diff` → remove (the try/catch with comment "No diff available" is sufficient)
- `// 5. Call Brick preprocess endpoint` → remove

- [ ] **Step 3: Verify**

Run: `cd colony && npx tsc --noEmit 2>&1; echo "TSC: $?"`
Expected: TSC: 0

- [ ] **Step 4: Commit**

```bash
git add colony/brick-hooks.ts
git commit -m "refactor: remove numbered step comments from preprocessForEvaluation"
```

---

### Post-Implementation Verification

After all 5 tasks:

```bash
cd colony && npx tsc --noEmit                    # TypeScript: 0 errors
cd colony && npx vitest run                       # 141 tests pass
cd colony && python3 -m pytest deacon_test.py -q  # 94 tests pass
for f in hooks/scripts/*.sh; do bash -n "$f" || echo "FAIL: $f"; done  # All pass
grep -rn '/home/q/' docs/sdlc/active/ colony/deacon.py colony/scripts/*.ts  # No matches
```

Push:
```bash
git push origin feat/colony-hardening-and-hook-portability
```
