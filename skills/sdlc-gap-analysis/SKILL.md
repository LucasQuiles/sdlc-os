---
name: sdlc-gap-analysis
description: "Coordinated gap analysis waves — Feature Finder pre-implementation maps what exists vs what's needed, Feature Finisher post-implementation verifies delivery completeness. Automatically during Scout (Finder) and Synthesize (Finisher), or on-demand via /gap-analysis."
---

# Gap Analysis Waves

Gap analysis runs in two coordinated waves: the **Finder** wave runs before implementation to map what exists against what is needed, and the **Finisher** wave runs after implementation to verify delivery completeness. Together they close the loop between requirements and code.

---

## Finder Wave (Pre-Implementation)

Runs automatically during the **Scout** phase, before the Architect produces beads.

### Purpose

Produce a completeness map that tells the Architect exactly which beads are needed. EXISTS items are skipped. PARTIAL and MISSING items become beads. Without the Finder, the team risks implementing what already exists and ignoring what does not.

### Flow

1. **Collect truth sources** — Gather all applicable sources before scanning. Document each source used; undocumented sources are inadmissible.

   | Source | When to Use |
   |--------|-------------|
   | Mission brief | Primary source when a brief exists |
   | External spec | API contracts, design docs, tickets |
   | Codebase state | No brief; derive requirements from existing patterns |
   | Precedent system | `references/precedent-system.md` — prior reuse candidates |

2. **Dispatch gap-analyst in Finder mode** — Send the gap-analyst agent with the collected truth sources and codebase context.

   ```
   Agent tool:
     subagent_type: general-purpose
     mode: auto
     name: "gap-analyst-finder"
     description: "Feature Finder: map requirements against codebase before implementation"
     prompt: |
       You are a Gap Analyst running in Finder mode (pre-implementation).

       ## Truth Sources
       {mission_brief or spec or inferred requirements}

       ## Codebase Context
       {relevant file paths, module structure, recent changes}

       ## Your Task
       1. Collect and decompose requirements from the truth source
       2. Scan the codebase for each requirement
       3. Classify each requirement: EXISTS | PARTIAL | MISSING
       4. Cross-reference PARTIAL and MISSING items against the precedent system
       5. Produce the Finder Report in the standard format

       See agent: gap-analyst for full instructions.
   ```

3. **For large scope: swarm guppies** — When the requirement list exceeds ~10 items, the gap-analyst spawns one guppy per requirement after decomposing. Each guppy searches for its assigned requirement using Grep and `workspaceSymbol`, then returns status, evidence, and confidence. The gap-analyst aggregates guppy results before classifying.

4. **Synthesize completeness map** — The gap-analyst produces a Finder Report with a completeness map table (requirement → status → evidence → action) and a summary count of EXISTS / PARTIAL / MISSING items.

5. **Feed into Architect phase** — The Conductor passes the Finder Report to the Architect (sonnet-designer). **Beads are created only for MISSING and PARTIAL items.** EXISTS items are explicitly excluded from bead decomposition. The reuse-scout receives any reuse opportunities identified in the report.

### Output Consumed By

| Consumer | What They Use |
|----------|--------------|
| Architect (sonnet-designer) | Completeness map → bead decomposition scope |
| Conductor | EXISTS list → skip list for bead tracking |
| reuse-scout | Reuse opportunities identified during cross-reference |

---

## Finisher Wave (Post-Implementation)

Runs automatically during the **Synthesize** phase, after all beads have merged.

### Purpose

Verify that the delivered code actually satisfies the original requirements. Catch gaps between what was specified, what was built, and what was wired up. Surface inferred gaps — obvious missing pieces that no one wrote down but any reasonable engineer would expect.

### Flow

1. **Collect truth sources** — Gather the mission brief (or Finder Report if one was produced), bead outputs, and current codebase state. If no brief or Finder Report exists, reconstruct requirements from commit history and merged beads.

2. **Dispatch gap-analyst in Finisher mode** — Send the gap-analyst agent with all bead outputs and original requirements.

   ```
   Agent tool:
     subagent_type: general-purpose
     mode: auto
     name: "gap-analyst-finisher"
     description: "Feature Finisher: verify delivery completeness after all beads merged"
     prompt: |
       You are a Gap Analyst running in Finisher mode (post-implementation).

       ## Original Requirements
       {mission_brief or Finder Report or reconstructed requirements}

       ## Beads Completed
       {list of bead IDs, names, and output summaries}

       ## Your Task
       1. Map each requirement to the bead(s) that were supposed to satisfy it
       2. Verify each bead output: does the code satisfy the criterion, is it reachable, is there a test?
       3. Apply inferred gap detection (forms without validation, incomplete CRUD, missing auth guards, etc.)
       4. Produce the Finisher Report with Delivery Completeness table, Inferred Gaps table, Closing Checklist, and Verdict

       See agent: gap-analyst for full instructions.
   ```

3. **Route based on Verdict** — The Conductor reads the Finisher Report Verdict and routes accordingly:

   | Verdict | Action |
   |---------|--------|
   | **COMPLETE** | Proceed to normalizer Final Pass → haiku-handoff |
   | **GAPS** (minor inferred gaps only) | Log gaps as follow-up beads; proceed to normalizer → handoff |
   | **INCOMPLETE** (unmet criteria) | Present gap report to user; do not proceed to handoff |

### Output Consumed By

| Consumer | What They Use |
|----------|--------------|
| Conductor | Verdict → routing decision |
| normalizer | Closing Checklist → Final Pass scope |
| haiku-handoff | Finisher Report summary → delivery narrative |

---

## Manual Invocation

Trigger via the `/gap-analysis` command at any point in the SDLC.

**Auto-detect mode:** The skill inspects the current SDLC artifact state to determine which mode is appropriate:

- If no bead outputs exist yet → **Finder mode**
- If bead outputs exist but no Finisher Report → **Finisher mode**
- If both exist → prompt user to specify mode or scope

The `/gap-analysis` command accepts an optional scope argument to restrict analysis to a specific feature, directory, or requirement subset.

---

## Integration with Quality SLOs

Gap analysis findings feed directly into the quality error budget.

- **NOT_DELIVERED criteria** (MISSING or INCOMPLETE in the Finisher Report) count against the delivery quality SLO. Each unmet criterion is a quality debit.
- **HIGH-severity inferred gaps** may trigger an error budget warning if the count exceeds the session threshold. The Conductor flags this to the user before proceeding.
- **Closing Checklist items** that are deferred (not resolved) are logged as known debt in `references/known-debt.md`. Known debt is surfaced at the next session start and tracked across tasks.

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| Running Finder after Architect has produced beads | Beads already reflect assumptions about what's missing. The Finder will contradict the bead plan, not inform it. Run Finder before Architect, always. |
| Running Finisher before all beads have merged | Partial bead outputs produce incomplete verification. Finisher requires a stable codebase state. |
| Marking EXISTS without reading the code | File names lie. A function can exist but be commented out, unreachable, or wrong. Always confirm at the symbol level. |
| Creating beads for EXISTS items | Wastes the team's time rebuilding what already works. The Finder Report EXISTS list is the authoritative skip list. |
| Ignoring inferred gaps in the Finisher Report | Explicit requirements are a floor, not a ceiling. HIGH-severity inferred gaps must be resolved or explicitly deferred — they cannot be silently dropped. |
