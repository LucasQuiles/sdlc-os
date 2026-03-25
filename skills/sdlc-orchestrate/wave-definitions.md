# Phase Reference

Phases are orientation markers, not approval gates. The Conductor flows through them as fast as the work allows. Each phase describes what happens, who does it, and what comes out — not a ceremony to perform.

---

## Phase 1: Frame

**Purpose:** Turn an ambiguous request into a crisp mission. Define what "done" looks like.

**Conductor does:**
- Assess complexity (trivial / moderate / complex)
- Dispatch `sonnet-investigator` to analyze requirements if ambiguity exists
- Dispatch `haiku-evidence` to check for gaps in the framing
- Write mission brief with objective, scope, constraints, success criteria

**Runner:** `sonnet-investigator` (model: sonnet) — requirements analysis mode
**Sentinel:** `haiku-evidence` (model: haiku) — checks for unstated assumptions, missing constraints

**Output:** `mission.md` — Objective, Scope (in/out), Constraints, Success Criteria (testable), Risks

**Skip when:** Task is trivial and well-specified. Go straight to Execute.

**Failure signals:**
- Success criteria are not testable
- Scope is unbounded ("improve everything")
- Hidden assumptions in the request

---

## Phase 2: Scout

**Purpose:** Gather evidence about the codebase and problem space before committing to an approach.

**Conductor does:**
- Define investigation scope and key questions
- Dispatch one or more `sonnet-investigator` runners (parallel if exploring different areas)
- Dispatch `haiku-evidence` to validate findings independently

**Runner:** `sonnet-investigator` (model: sonnet) — codebase investigation mode
**Sentinel:** `haiku-evidence` (model: haiku) — fact-checks claims, captures evidence

**Output:** `discovery.md` — Findings (labeled Verified/Likely/Assumed/Unknown), Evidence items, Impact areas, Open questions

**Parallelize:** Yes — multiple investigators can explore different subsystems simultaneously.

**Skip when:** Sufficient context already exists (e.g., from prior conversation or well-known codebase area).

**Failure signals:**
- Inference presented as fact
- Single-file reading without checking callers/tests
- Missing dependency analysis

---

## Phase 3: Architect

**Purpose:** Choose an approach and decompose into atomic work units (beads).

**Conductor does:**
- Dispatch `sonnet-designer` with discovery findings
- Evaluate options, select approach
- Dispatch `haiku-verifier` to stress-test the tradeoff analysis
- Create bead manifest (list of all work units with dependencies and scopes)

**Runner:** `sonnet-designer` (model: sonnet)
**Sentinel:** `haiku-verifier` (model: haiku) — checks tradeoff completeness, missed edge cases

**Output:**
- `design.md` — Options, Tradeoffs, Recommendation, Validation strategy
- `beads/*.md` — One file per work unit with scope, dependencies, input, expected output

**Skip when:** Implementation path is obvious and low-risk. Conductor creates beads directly.

**Failure signals:**
- Strawman alternatives (only one real option)
- No validation strategy
- Beads with overlapping file scopes (collision risk)

---

## Phase 4: Execute

**Purpose:** Build the thing. This is where most time is spent.

**Conductor does:**
- Dispatch `sonnet-implementer` runners — one per bead
- Parallelize independent beads, serialize dependent ones
- Sentinel watches continuously (not after completion)
- Re-dispatch fresh runners when sentinel flags problems (max 3 cycles per bead)

**Runner:** `sonnet-implementer` (model: sonnet) — one bead per runner, disposable
**Sentinel:** `haiku-verifier` (model: haiku) — continuous patrol, checks each bead output as it arrives

**Adversarial Quality (after Oracle):** Red/blue team cycle via `sdlc-os:sdlc-adversarial` — recon burst, directed strike, blue team response, arbiter on disputes. Beads marked `hardened` after cycle completes. Skip for trivial beads.

**Output:** Updated bead files with implementation output, test results, validation notes, adversarial quality reports per bead

**Parallelize:** Yes — any beads with non-overlapping scopes and no dependency chain.

**Recovery patterns:**
- Runner NEEDS_CONTEXT → Conductor provides, dispatches fresh runner
- Runner BLOCKED → Conductor assesses: context problem, design flaw, or real blocker
- Sentinel flags problem → Conductor re-dispatches fresh runner with sentinel findings
- Parallel beads conflict → Dispatch conflict resolver with both outputs

**Failure signals:**
- Large undifferentiated changes (should be smaller beads)
- Runner drifting beyond bead scope
- Tests not written alongside implementation

---

## Phase 5: Synthesize

**Purpose:** Merge all runner outputs into coherent delivery. Final quality check.

**Conductor does:**
- Review all completed beads
- Dispatch `sonnet-reviewer` for critical assessment of the whole
- Dispatch `haiku-handoff` for final sentinel sweep and delivery packaging
- Resolve any remaining conflicts
- Write delivery summary

**Runner:** `sonnet-reviewer` (model: sonnet) — reviews the integrated result, not individual beads
**Sentinel:** `haiku-handoff` (model: haiku) — packages delivery, separates verified from uncertain

**Output:** `delivery.md` — What changed, How we know, What's uncertain, Next actions

**Failure signals:**
- Ceremonial review ("looks good" without substance)
- Missing regression checks on the integrated result
- Uncertainty buried instead of named
