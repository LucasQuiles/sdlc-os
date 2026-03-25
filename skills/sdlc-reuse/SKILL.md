---
name: sdlc-reuse
description: "Reuse-first protocol. Ensures runners see existing solutions before they start work. Pre-dispatch context injection via the 6-layer analysis chain. Every implementation bead gets a reuse scout report injected into its runner context."
---

# Reuse-First Protocol

Before any implementation runner is dispatched, the Conductor MUST run this protocol. It prevents the most common failure mode: creating new code when existing solutions already exist.

## Why Agents Duplicate

Agents duplicate because they lack context, not because they are careless ([Faros AI](https://www.faros.ai/blog/ai-generated-code-and-the-dry-principle)). The fix is not post-hoc detection — it is pre-dispatch visibility.

## The Protocol

### Step 1: Dispatch Reuse Scout

Before every implementation bead, dispatch `reuse-scout` (haiku):

```
Agent tool:
  subagent_type: sdlc-os:reuse-scout
  model: haiku
  name: "scout-{bead-id}"
  description: "Reuse scout for bead {id}"
  prompt: |
    ## Bead Objective
    {bead description — what needs to be built}

    ## Bead Scope
    {files/areas the bead will touch}

    ## Project
    {project root path}

    Run the 6-layer analysis chain and produce the Existing Solutions report.
```

### Step 2: Inject Scout Report Into Runner Context

The runner dispatch now includes an additional section:

```
## Existing Solutions (from Reuse Scout)
{paste complete scout report here}

## Reuse Obligation
You MUST reuse existing solutions listed above. Create new code ONLY for
functionality not covered. Every new function you create must include a
justification for why existing solutions do not suffice.
```

### Step 3: Runner Reports Reuse

Every implementation runner must include in its output:

```markdown
## Reuse Report
### Reused
- [function] from [path] — [how it was used]

### Extended
- [function] from [path] — [what was added and why]

### Created New
- [function] — Justification: [why nothing existing suffices]
```

### Step 4: Drift Detector Validates

After the runner submits, the drift-detector runs as part of the L1 sentinel loop:
- Compares runner's Reuse Report against scout's Existing Solutions
- Flags any case where the scout found an existing solution but the runner created new code anyway
- Flags any new creation that lacks justification


## Consume Prior Findings

If Phase 2 (Scout) already ran and explored the bead's scope, the reuse-scout should NOT re-search from scratch. Instead:

1. Read the Scout phase discovery brief
2. Extract relevant findings for this specific bead
3. Run ONLY the layers that the Scout phase didn't cover (e.g., LSP call hierarchy on specific functions)
4. Supplement, don't duplicate

This prevents the Scout → reuse-scout redundancy without losing per-bead precision.

## Alternate Paths (No Skipping)

If a layer in the analysis chain is unavailable, the system works HARDER through other means — it does not lower the bar.

| Layer Down | Alternate Path |
|------------|---------------|
| Episodic memory unavailable | Query Pinecone for prior patterns + grep git log for related commits |
| Pinecone unavailable | Broader grep sweep + LSP workspaceSymbol with more patterns |
| LSP unavailable | Deeper grep + read actual file contents + dispatch guppy swarm for targeted checks |
| Grep fails (no matches) | This is information, not failure. Document the absence. Proceed to LSP. |

The principle: if one path to truth is blocked, find another. Never accept reduced rigor.

## When to Skip

- **Investigation beads**: Read-only, no code creation — skip reuse scout
- **Design beads**: No implementation — skip reuse scout
- **Trivial beads**: Single-line changes with obvious intent — Conductor judgment

## Integration with Loop Mechanics

- Reuse scout runs BEFORE L0 (runner loop)
- Scout report feeds INTO L0 as part of the runner's context
- Drift detector runs DURING L1 (sentinel loop)
- Scout failures (UNCLEAR/incomplete) do NOT block the runner — the runner proceeds with whatever context is available, and the drift detector catches what the scout missed

## Guppy Swarm Variant

For large beads touching many files, the Conductor can upgrade the scout from a single haiku dispatch to a guppy swarm:

1. Decompose the bead's scope into N file-groups
2. Swarm N guppies, each scanning one file-group for reuse opportunities
3. Synthesize guppy findings into a combined scout report
4. Inject into runner context as usual
