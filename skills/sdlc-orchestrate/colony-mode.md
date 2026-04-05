# Colony Mode Dispatch Protocol

This document defines the colony dispatch protocol used when a tmup session is active. It is an additive extension to the sync mode defined in SKILL.md. All sync behavior is preserved when tmup is unavailable.

---

## Detection

After Phase 3 (Architect) produces a bead manifest, the Conductor checks for colony mode:

1. Call `tmup_status`.
2. If it returns a valid session: **colony mode**. Use the dispatch sequence below.
3. If no session exists (or tmup plugin not loaded): **sync mode**. Use the existing Agent tool dispatch from SKILL.md. No changes.

Colony mode is detected, not configured. There is no `COLONY_MODE` flag.

---

## Colony Dispatch Sequence

When colony mode is active, the Conductor follows this sequence to dispatch beads as tmup tasks:

### Step 1: Initialize Session

```
tmup_init  (idempotent — reattaches if session already exists)
```

### Step 2: Pre-Flight Handoff

Write a pre-flight handoff block to `state.md`:

```markdown
## Pre-Flight Handoff
**Session type:** DISPATCH
**Beads in manifest:** [bead-001, bead-002, ...]
**In-flight tasks:** []
**Timestamp:** 2026-04-03T14:00:00Z
```

### Step 3: Dispatch Each Bead

For each bead in the manifest (respecting dependency order per SC-COL-10):

#### 3a. Check for Existing Tasks (SC-COL-09)

Query tmup for active tasks with the same `bead_id`. If an active task exists at the same loop level, skip dispatch. If a stale task exists, cancel it first (SC-COL-13).

#### 3b. Create Task

```
tmup_task_create:
  title: "Bead {bead-id}: {short description}"
  description: JSON string containing:
    {
      "cynefin_domain": "complicated",
      "acceptance_criteria": [
        "All tests pass",
        "No regressions in existing tests"
      ],
      "scope_files": [
        "src/module/foo.ts",
        "src/module/bar.ts"
      ],
      "sdlc_phase": "execute"
    }
  priority: mapped from cynefin_domain (complex=high, complicated=medium, clear=low)
  tags: ["colony", "bead-{bead-id}", "L0"]
```

#### 3c. Write bead-context.md to Clone

Before dispatching the worker, write `{clone_dir}/bead-context.md` following the bead-context.md write protocol below.

#### 3d. Dispatch Worker

```
tmup_dispatch:
  task_id: {task-id from step 3b}
  worker_type: "codex" | "claude_code"  (based on bead complexity)
  clone_isolation: true
```

Worker type selection:
- **codex**: Default for CLEAR and COMPLICATED beads. Cheaper, faster.
- **claude_code**: For COMPLEX beads or beads requiring multi-file coordination.

### Step 4: Update Handoff

Update the pre-flight handoff block in `state.md` with the list of dispatched task IDs.

### Step 5: Exit

The Conductor exits. The Deacon watches for worker completions and spawns an EVALUATE session.

### Cross-Model Workers
Cross-model review workers are dispatched via `tmup_dispatch` with `worker_type: codex` and `clone_isolation: true`. They review code independently from Claude-based AQS agents, providing inter-model adversarial leverage. Managed by `sdlc-os:sdlc-crossmodel` skill.

---

## bead-context.md Write Protocol

Before every `tmup_dispatch` call, the Conductor MUST write `{clone_dir}/bead-context.md`. This file is the worker's primary input. The worker reads it as its first action.

### File Format

```markdown
# Bead Context: {bead-id}

## Bead Specification
**Type:** {investigate | design | implement | verify | review | evolve}
**Status:** {current status}
**Cynefin Domain:** {clear | complicated | complex}
**Security Sensitive:** {true | false}
**Profile:** {BUILD | INVESTIGATE | REPAIR | EVOLVE}
**Loop Level:** {L0 | L1 | L2}
**Prior Worker Type:** {claude_code | codex | none}

## Objective
{Full objective from bead file — what the worker must accomplish}

## Acceptance Criteria
{Numbered list of acceptance criteria from bead file}

## Scope Files
{List of files the worker may modify — worker MUST NOT modify files outside this list}

## Input Context
{Relevant prior outputs: discovery findings, design decisions, architectural constraints}
{File paths and architectural hints — NOT the Conductor's session history}

## Dependencies
{List of dependency bead IDs and their current status}
{Summary of dependency outputs if relevant}

## Correction History
{If this is a retry or higher loop level, include ALL prior corrections:}

### Correction L0 Cycle 1
**Finding:** {what failed}
**Evidence:** {file:line or test output}
**What to try:** {specific suggestion}
**What NOT to try:** {approaches already failed}

### Correction L1 Cycle 1
**Finding:** {sentinel finding}
...

## Output Protocol
1. Execute the work described in the Objective section.
2. Stay within the Scope Files listed above. Do not modify other files.
3. Write your output to `bead-output.md` in the working directory.
4. End `bead-output.md` with the sentinel: `<!-- BEAD_OUTPUT_COMPLETE -->`
5. If you succeed: call `tmup_complete` with a summary.
6. If you fail after L0 self-correction (3 attempts):
   - Write `correction.json` with: what_failed, evidence, what_to_try, what_not_to_try
   - Call `tmup_fail` with reason and brief message.
7. Call `tmup_heartbeat` periodically during long tasks.
```

### Construction Rules

1. **Full bead spec**: Copy all fields from the bead markdown file.
2. **Relevant context only**: Include outputs from dependency beads and architectural decisions. Do NOT dump the Conductor's full session history.
3. **Correction history**: Include ALL corrections from ALL prior cycles and loop levels. The worker must see what was already tried to avoid repeating failed approaches.
4. **Output protocol**: Always include the output protocol section verbatim. Workers must know how to report results.
5. **Scope enforcement**: The scope_files list is authoritative. Workers must not modify files outside it.
6. **Prior worker type**: When dispatching a review bead, include the worker_type of the agent that produced the work being reviewed. This enables the reviewer to understand model-specific patterns in the code.

### When to Rewrite

Write a fresh `bead-context.md` before EVERY dispatch, including retries. The file must reflect the current state of the bead, including any corrections appended since the last dispatch.

---

## Sync Mode (Unchanged)

When `tmup_status` returns no valid session, the Conductor uses the existing Agent tool dispatch from SKILL.md:

- Dispatch `sonnet-implementer` runners via the Agent tool.
- Runners execute synchronously within the Conductor's session.
- No clones, no tmup tasks, no bead-context.md files.
- All correction loops run inline.

This behavior is fully preserved. Colony mode is purely additive.
