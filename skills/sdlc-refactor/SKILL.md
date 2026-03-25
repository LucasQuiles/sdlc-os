---
name: sdlc-refactor
description: "Refactoring mode for working with existing code. Preserves behavior while improving structure. Establishes baseline proof, characterizes existing behavior via LSP, transforms in atomic steps with continuous equivalence verification."
---

# Refactor Mode

Refactoring is NOT implementation. The objective is different, the risks are different, and the verification is different.

**Implementation asks:** "Does it work?"
**Refactoring asks:** "Does it still work the same way, but better?"

## When to Use

- Restructuring existing code (splitting files, extracting functions, consolidating duplicates)
- Changing internal patterns without changing external behavior
- Migration from one approach to another (raw toast → safeToast, Math.random → generateId)
- Consolidating duplication found by drift-detector or /audit

## The Refactor Protocol

### Step 1: Baseline

Before touching anything, establish behavioral proof.

1. Run the full test suite. Record: N tests, M passing, K failing.
2. If tests don't exist for the code being refactored, WRITE THEM FIRST. This is non-negotiable. Refactoring without tests is guessing.
3. Record the baseline: "Before refactor: 247 pass, 3 fail (pre-existing), 0 skip"
4. Pre-existing failures are NOT your problem. Your job: don't add new ones.

The Oracle behavioral-prover runs the baseline. This is the ground truth.

### Step 2: Characterize

Before changing structure, understand the existing behavior.

1. Map the code being refactored using LSP:
   - Who calls it? (`incomingCalls`)
   - What does it call? (`outgoingCalls`)
   - What types flow through it? (`hover`)
   - Where is it imported? (`findReferences`)
2. Produce a characterization document:
   - **Public interface** (what callers see — this is the CONTRACT)
   - **Internal structure** (what will change)
   - **Dependencies** (what it needs)
   - **Consumers** (what needs it)
3. The public interface is sacred. Refactoring changes internals, not the contract.

### Step 3: Plan the Transformation

1. Define the target structure (what it should look like after)
2. Decompose into atomic transformation steps — each leaves code WORKING
3. Order: **extract → redirect → delete**
   - Extract: create the new structure alongside the old
   - Redirect: point callers to the new structure (re-exports for backwards compat)
   - Delete: remove the old structure once nothing references it

### Step 4: Execute with Continuous Proof

Each refactor bead follows a tighter loop than implementation:

```
REFACTOR BEAD LOOP (budget: 3 attempts):
  1. Make ONE structural change
  2. tsc --noEmit (types still valid?)
  3. Run test suite (baseline still holds?)
  4. PASS both → commit this step. Next bead.
  5. FAIL either → revert. Diagnose. Try different approach.
  6. Budget exhausted → escalate with what broke and why.
```

The metric is NOT "does my new code work" — it is "does EVERYTHING STILL work."

### Step 5: Verify Equivalence

After all transformation beads complete:

1. **Oracle behavioral-prover:** run full test suite. Compare to baseline.
   - Same or more passes = equivalence maintained
   - Fewer passes = REGRESSION. Revert and investigate.
2. **Oracle test-integrity:** did the refactor introduce any vacuous tests?
3. **Drift-detector:** does the refactored code follow project conventions?
4. **LSP findReferences** on all modified exports: did any caller break?

## Refactor vs Implementation

| Dimension | Implementation | Refactoring |
|-----------|---------------|-------------|
| Goal | Make it work | Make it better without changing behavior |
| Metric | Tests pass | SAME tests still pass |
| Risk | Doesn't work | Silently breaks something |
| Verification | New behavior proven | Old behavior preserved |
| Decomposition | By feature | By transformation step |
| Test requirement | Write tests for new code | Ensure tests EXIST before touching code |

## Refactor Anti-Patterns

- **Refactoring without tests** — Write characterization tests first
- **Big bang refactor** — Each step must leave code working
- **Changing behavior during refactor** — That is implementation, separate concerns
- **Not running baseline after each step** — Continuous proof is the whole point
- **Refactoring code you don't understand** — Characterize first via LSP
