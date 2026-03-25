# AQS Model-Routing Evaluation Harness

Borrowed from Gas Town's model evaluation pattern: before changing which model serves an AQS role, run these evals to verify the replacement model meets the role's requirements. This prevents quality collapse when optimizing for cost or speed.

## Why This Exists

AQS assigns models by role: haiku for guppies, sonnet for red/blue commanders, opus for arbiter. These assignments are not arbitrary — each role requires specific capabilities. Swapping a cheaper model into a role without evaluation risks silent quality degradation (Karpathy's "fails silently" anti-pattern).

## Two Eval Classes (from Gas Town)

### Class B: Instruction-Following

Can the model reliably follow the role's structured protocol? These are pass/fail mechanical tests.

**Guppy role (haiku baseline):**
- Given a recon directive, does it respond with exactly SIGNAL or NO_SIGNAL?
- Given a strike probe, does it respond with HIT/MISS + evidence?
- Does it stay within scope (one probe, one answer, no scope expansion)?
- Does it include confidence labels?

**Red team commander (sonnet baseline):**
- Given a bead + recon signals, does it produce findings in the required format?
- Does each finding include all required fields (Domain, Severity, Claim, Minimal reproduction, Impact, Evidence, Confidence)?
- Does it dispatch guppies with properly scoped directives?
- Does it apply mandatory shrinking (downgrade findings without reproduction)?

**Blue team defender (sonnet baseline):**
- Given findings, does it respond with exactly accepted/rebutted/disputed per finding?
- Does it follow the defensive iteration pattern (reproduce → fix → verify → regression check)?
- Does it produce evidence-based rebuttals (not "looks fine")?
- Does it correctly escalate ambiguous findings to arbiter?

**Arbiter (opus baseline):**
- Given a dispute package, does it lock the dispute contract before analysis?
- Does it extract pre-registered commitments from both sides?
- Does it design a test that addresses the core disagreement type?
- Does it issue a binding verdict with evidence?
- Does it handle inconclusive results with the two-round protocol?

### Class A: Evidence Reasoning

Can the model reason correctly about evidence and produce genuine (not performative) analysis? These require human or stronger-model judgment.

**Red team — genuine attack design:**
- Given a code snippet with a known vulnerability, does the model find it?
- Given a code snippet without vulnerabilities, does the model correctly report clean (or does it fabricate findings)?
- Does severity calibration match ground truth? (critical issues rated critical, low issues rated low)
- Does the model shrink findings to minimal reproductions, or does it report bloated, vague concerns?

**Blue team — genuine triage:**
- Given a real finding, does the model produce a correct fix?
- Given a false positive, does the model correctly rebut with specific evidence?
- Does the model distinguish between "I don't know" (dispute) and "this is clearly wrong" (rebut)?

**Arbiter — fair test design:**
- Given a dispute, does the test actually address the core disagreement?
- Does the model resist anchoring to one side's framing?
- Does the verdict follow from the evidence (not from prior beliefs)?

## Eval Procedure

1. **Select test cases** — 5-10 representative beads from recent SDLC tasks (mix of clean and buggy code)
2. **Run current model** — Establish baseline scores on both Class A and Class B
3. **Run candidate model** — Score the candidate on the same test cases
4. **Compare** — Candidate must meet or exceed baseline on Class B (mechanical). Class A regressions require Conductor judgment — a 10% drop in evidence reasoning for a 50% cost reduction may or may not be acceptable depending on the role.

## When to Run

- Before changing any AQS role's model assignment
- After a model provider releases a new version (verify no regression)
- When the Conductor observes quality degradation in AQS outputs (diagnostic)

## Role-Specific Minimum Requirements

| Role | Class B Minimum | Class A Minimum | Current Model |
|------|----------------|-----------------|---------------|
| Guppy | 95% instruction compliance | N/A (too simple to eval reasoning) | haiku |
| Red team | 90% format compliance | 70% genuine finding rate on known-vulnerability test set | sonnet |
| Blue team | 90% format compliance | 70% correct triage on known-finding test set | sonnet |
| Arbiter | 95% protocol compliance | 80% correct verdict on known-dispute test set | opus |

## File Structure

```
docs/evals/aqs-model-eval/
├── README.md                ← this file
├── test-cases/              ← representative beads for evaluation
│   ├── clean-bead-01.md     ← bead with no issues (false positive test)
│   ├── vuln-bead-01.md      ← bead with known security vulnerability
│   ├── logic-bead-01.md     ← bead with known logic error
│   └── dispute-01.md        ← known dispute with ground truth verdict
└── results/                 ← eval run results
    └── {date}-{model}-{role}.md
```

Test cases should be added incrementally from real SDLC tasks as the system runs. Start with 2-3 cases per role and grow the set over time.
