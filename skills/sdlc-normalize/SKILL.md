---
name: sdlc-normalize
description: "Mid-stream pickup and session entry normalization. Mandatory on every SDLC entry — detects clean state, interrupted workflows, or unstructured changes. Dispatches normalizer agent with smart depth detection. Also invocable via /normalize command for manual convention refresh."
---

# Normalization Protocol

Every SDLC session begins with normalization. No exceptions.

## Why Normalization is Mandatory

Agents duplicate work, drift from conventions, and redo completed beads because they lack context — not because they are careless. The cost of running normalization on a clean repository is under 5 seconds. The cost of skipping normalization on a dirty repository is convention drift, duplicate utilities, wasted runner cycles, and bead outputs that contradict each other.

The normalizer does not make assumptions about session state. It reads the actual state of the repository and reports what it finds. If the state is clean, it exits immediately. If work is in progress, it recovers it. If unstructured changes exist, it produces directives to align them with conventions before any new work begins.

Skipping Phase 0 to save a few seconds is a false economy. Every minute saved at session entry costs multiples later in the Execute phase.

## The Protocol

### Step 1: Dispatch Normalizer (always)

Dispatch the normalizer agent at the start of every SDLC session, before any other work begins:

```
Agent tool:
  subagent_type: sdlc-os:normalizer
  model: sonnet
  mode: auto
  name: "normalizer-entry"
  description: "Phase 0: session entry normalization"
  prompt: |
    You are the Normalizer running in Mode 1: Pickup (session entry).

    ## Project Root
    {project root path}

    ## Convention Map
    {paste contents of docs/sdlc/convention-map.md if it exists, or "NOT FOUND"}

    ## Code Constitution
    {paste contents of docs/sdlc/code-constitution.md if it exists, or "NOT FOUND"}

    Perform state detection in order (SDLC artifacts → git state → clean).
    Stop at the first matching condition and produce the appropriate output.
    Do NOT run cross-bead checks (Mode 2) during session entry.
```

The normalizer will return one of three status values: `NO-OP`, `RESUME`, or `FULL NORMALIZATION REQUIRED`.

### Step 2: Route Based on Report

Route to the appropriate path based on the normalizer's status:

**Path A — Clean (NO-OP)**

No active SDLC artifacts, no uncommitted changes, no unpushed commits. Proceed directly to Phase 1: Frame. The normalizer's report is the only output from Phase 0.

**Path B — Resume (SDLC State Recovery)**

Active SDLC artifacts detected in `docs/sdlc/active/`. The normalizer has identified the interrupted task, reconstructed bead states, and recommended a re-entry point.

1. Present the normalizer's recovery summary to the user
2. Ask explicit confirmation: "Resume at `<recommended re-entry point>`?"
3. On approval, load the task state from the referenced `state.md` file, bead files, and any persisted Scout artifacts (`standards-profile.md`, `quality-budget.yaml`, `hazard-defense-ledger.yaml (if exists)`, `observability-profile.md`, `rule-governance-profile.md`, `suppression-allowlist.md`). Continue from the recommended bead or phase.
4. Do NOT restart from Phase 1 — that would duplicate completed beads. If `standards-profile.md` is missing and the task is past Scout, note this gap but do not re-run Scout — the enforcement agents can fall back to the full `references/standards-checklist.md`.

**Path C — Full Normalization (Unstructured Changes)**

Uncommitted changes or unpushed commits detected without SDLC artifacts. The normalizer has produced an alignment assessment and normalization directives.

1. Check Convention Map status from the normalizer's report:
   - If `docs/sdlc/convention-map.md` is missing or flagged as stale, dispatch `convention-scanner` before proceeding:

     ```
     Agent tool:
       subagent_type: sdlc-os:convention-scanner
       model: sonnet
       mode: auto
       name: "convention-scanner-phase0"
       description: "Phase 0: scan codebase conventions before normalization"
       prompt: |
         You are the Convention Scanner. Produce docs/sdlc/convention-map.md
         for the project at {project root path}.

         ## Existing Constitution
         {paste contents of docs/sdlc/code-constitution.md if it exists, or "NOT FOUND"}

         Run an initial scan across all dimensions in
         references/convention-dimensions.md. Do NOT modify any project file
         other than docs/sdlc/convention-map.md.
     ```

   - If the Convention Map exists and is current, skip the scanner dispatch

2. Present the normalization directives to the user for review. Do NOT auto-execute. Every directive must be explicitly approved:
   - Renaming files requires user approval
   - Moving files requires user approval
   - Fixing code requires user approval
   - Dispatching additional agents requires user approval

3. On approval, execute only the approved directives. Re-dispatch the normalizer for any directive that requires codebase changes to verify the correction

### Step 3: Gap Analysis (if Full Normalization)

After executing approved normalization directives, dispatch `gap-analyst` in Finder mode to establish a baseline of what exists before any new implementation begins:

```
Agent tool:
  subagent_type: sdlc-os:gap-analyst
  model: sonnet
  mode: auto
  name: "gap-analyst-phase0"
  description: "Phase 0: feature gap baseline after normalization"
  prompt: |
    You are the Gap Analyst running in Mode 1: Feature Finder.

    ## Project Root
    {project root path}

    ## Truth Source
    {paste the mission brief or task description, or "INFER FROM CODEBASE"}

    ## Normalization Directives Applied
    {list the directives that were approved and executed}

    Produce a Feature Gap Analysis — Finder Report. Classify all relevant
    requirements as EXISTS, PARTIAL, or MISSING. Record reuse opportunities.
    This report will feed into the recommended SDLC entry point for Phase 1.
```

The gap analyst's Finder Report feeds directly into Phase 1: Frame. The Conductor uses the completeness map to avoid creating beads for items already marked EXISTS, and to prioritize MISSING and PARTIAL items.

## Manual Invocation

The `/normalize` command runs Full Normalization regardless of current state detection. Use it to refresh conventions at any point in the session without waiting for Phase 0.

When invoked via `/normalize`:
1. Dispatch the normalizer with explicit override: treat state as `FULL NORMALIZATION REQUIRED`
2. Check Convention Map status and dispatch `convention-scanner` if missing or stale
3. Present directives and await approval exactly as in Path C above
4. After approved directives execute, dispatch `gap-analyst` in Finder mode
5. Present the gap analysis report before continuing

This is useful when:
- Conventions have evolved mid-session and runners are drifting
- A new team member introduces patterns that conflict with the existing map
- The Convention Map has not been refreshed after significant refactoring
- The user explicitly wants a convention checkpoint before a major implementation phase

## Integration with SDLC Orchestrate

Normalization is Phase 0 — it runs before the orchestration phases, not as part of them. The flow:

```
Session Start
    │
    ▼
Phase 0: Normalize  ◄──── /normalize (manual, any time)
    │
    ├── NO-OP ──────────────────────────────────► Phase 1: Frame
    │                                                  │
    ├── RESUME ──► present recovery ──► confirm ──► Re-entry at recommended phase
    │                                                  │
    └── FULL NORMALIZATION                             │
            │                                          │
            ├── convention-scanner (if needed)         │
            ├── present directives ──► approve         │
            ├── execute approved directives            │
            └── gap-analyst (Finder) ────────────────► Phase 1: Frame
                                                           │
                                                       Phase 2: Scout
                                                           │
                                                       Phase 3: Architect
                                                           │
                                                       Phase 4: Execute
                                                           │
                                                       Phase 5: Synthesize
                                                       (normalizer Mode 2
                                                        runs here as
                                                        cross-bead check)
```

The normalizer runs again at Phase 5: Synthesize in Mode 2 (Final Pass) to catch naming drift and duplicate utilities introduced by parallel beads. That invocation is separate from Phase 0 and is orchestrated by the `sdlc-orchestrate` skill.

## Anti-Patterns

| Anti-Pattern | Why It Is Wrong |
|---|---|
| Skipping Phase 0 for "trivial" tasks | State detection takes under 5 seconds on clean repos. Skipping it means a dirty repo stays dirty, and the next session inherits the mess. |
| Auto-executing normalization directives | Directives may rename or move files. Only the user can authorize changes to the working tree. Auto-execution violates the approval requirement and may destroy in-progress work. |
| Re-scanning conventions when a valid map exists | Running `convention-scanner` when `docs/sdlc/convention-map.md` is current wastes context and may overwrite Conductor-approved entries. Check the map status first. |
| Not dispatching gap-analyst after full normalization | The gap analyst establishes the baseline that prevents Phase 1 from creating beads for already-complete work. Skipping it causes duplicate effort in Execute. |
