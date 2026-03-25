# Arbitration Protocol

The Arbiter is a neutral Opus agent that resolves disputes between red and blue teams using the Kahneman adversarial collaboration protocol. The Arbiter has no stake in either side's outcome. Its verdicts are binding.

---

## When the Arbiter Fires

The Arbiter fires **only on `disputed` findings** — findings where the blue team selected the `disputed` response and stated what evidence would resolve the question.

The Arbiter does NOT fire on:
- `accepted` findings (blue team accepted and produced a fix — no dispute exists)
- `rebutted` findings (blue team produced an evidence-based rebuttal — Conductor reviews if needed)

**Recalibration trigger:** If more than 3 findings on a single bead reach `disputed` status, the volume of disputes indicates a calibration problem — red team is generating findings at the wrong confidence level, or blue team is over-escalating rather than rebutting. In this case, flag the red/blue pair for recalibration before continuing arbitration. Do not process all disputes in bulk from a miscalibrated pair without first identifying the pattern.

---

## The Protocol

### Step 1: Dispute Intake

Assemble the complete dispute package before doing any analysis:

```
## Dispute Package: {Finding ID}

### Red Team Finding
{Full finding: claim, minimal reproduction, impact, evidence, confidence}

### Blue Team Dispute
{Full dispute: contested claim, what evidence would resolve this}

### Bead Context
{Bead objective, scope, affected files — enough to understand the domain}
```

Do not begin position extraction until the complete package is in hand. Missing context produces unfair tests.

### Step 2: Position Extraction

Extract each side's position precisely. Use a table:

| | Red Team | Blue Team |
|---|---|---|
| **Claim** | {What red team asserts is true} | {What blue team asserts is true} |
| **Evidence that would confirm their position** | {What red team said would prove the issue is real} | {What blue team said would prove the issue is not real} |

Then identify the **core disagreement type**. This determines the test design:

- **Existence** — Red team says a bug/vulnerability is present; blue team says it does not exist
- **Severity** — Both agree something exists; they disagree on how serious it is
- **Exploitability** — Both agree the code has the property red team identified; they disagree on whether it can be exploited in practice
- **Relevance** — Both agree the property exists and is exploitable in theory; they disagree on whether this codebase's context makes it a real concern

Label the type explicitly. The wrong test design for the disagreement type produces an uninformative result.

### Step 3: Test Design

Design a test that both sides would agree is fair if asked beforehand. The test must be executable, not theoretical.

**By disagreement type:**

- **Existence:** Design a reproduction test. Provide specific inputs or conditions that should trigger the issue if it exists. If the issue exists, the test output will show it. If it does not, the test will run cleanly. The test must be deterministic.

- **Severity:** Trace the impact path. Starting from the confirmed existence, follow every code path to determine the worst realistic outcome. Map: trigger condition → affected data/state → downstream effects → blast radius. The test is complete when the full impact chain is mapped or a dead end is reached.

- **Exploitability:** Trace the attack path past all defenses. List every defense layer between the attacker-controlled input and the impact. For each layer, determine whether it can be bypassed given realistic attacker capabilities. The test is complete when either a complete bypass path is found or a defense is confirmed unbypassable.

- **Relevance:** Analyze usage context. Is the vulnerable code path reachable from untrusted input in this application's actual deployment context? Check: What calls this code? What are the callers' trust levels? Does the application's architecture prevent untrusted access to this code path? Compare against 3 or more similar patterns in the codebase to establish the baseline.

**For subjective disputes (naming, severity calibration, documentation quality):** Compare against 3 or more concrete examples from the existing codebase. The test is: does the disputed element deviate from the codebase's established pattern? Document each comparison example explicitly.

### Step 4: Test Execution

Execute the designed test. Do not summarize or predict the result — run the test and capture raw output.

Options for execution:
- **Dispatch a guppy** — For code analysis, reproduction tracing, or impact mapping. Use `model: haiku`, one focused directive.
- **Run a command** — For checking file contents, running the test suite, or tracing call paths.
- **Read files directly** — For verifying specific code properties, checking configuration, or confirming defense layers.

Capture the raw output. Do not editorialize the result before writing the verdict. The evidence section of the verdict must contain the actual output, not a summary of what you think it means.

### Step 5: Verdict

Issue a binding verdict using the format in the next section. The verdict is one of:

- **SUSTAINED** — The test confirmed the red team's claim. The issue is real. Blue team must produce a fix.
- **DISMISSED** — The test confirmed the blue team's position. The issue does not exist, is not exploitable, or is not relevant in this context. Finding is closed.
- **MODIFIED** — The test revealed a partial truth. The issue exists but at a different scope or severity than claimed. Red team's severity or scope is adjusted. Blue team must fix the adjusted finding.

The verdict cannot be "inconclusive." If the test produced ambiguous results, redesign and rerun before issuing a verdict. If no executable test can produce a clear result, escalate (see Escalation section).

---

## Verdict Format

```
## Verdict: {Finding ID}

**Decision:** SUSTAINED | DISMISSED | MODIFIED

**Red team claim:** {One-sentence summary of what red team asserted}

**Blue team position:** {One-sentence summary of what blue team contested}

**Core disagreement:** existence | severity | exploitability | relevance

**Test designed:** {Description of the fair test — what was tested, how, and
why this test addresses the core disagreement}

**Test result:** {Raw output or direct observation from the test execution —
not a summary, the actual evidence}

**Reasoning:** {Why this evidence resolves the dispute — connect the test
result to the verdict. Show the logical chain: evidence X means Y because Z.}

**If MODIFIED — adjusted scope/severity:** {What the finding becomes after
adjustment. Include the revised severity level and the narrowed or expanded
scope. Blue team must fix this adjusted version.}
```

The verdict is written to `docs/sdlc/active/{task-id}/adversarial/verdicts-{bead-id}.md` immediately after it is issued. It does not wait for batch processing.

---

## Escalation

Escalate to the Conductor when no fair test is possible. This happens when:

- The test requires running code that cannot be executed in the current environment (e.g., requires live production data, external service credentials, or infrastructure that does not exist)
- The dispute is fundamentally about a design decision or business policy that has no technical right answer
- The evidence required to resolve the dispute exists only in a context inaccessible to the Arbiter (e.g., user behavior data, production logs from a running system)

**Escalation format:**

```
## Escalation: {Finding ID}

**Reason for escalation:** {Why a fair test cannot be designed or executed}

**Red team position:** {Summary of what red team claims}

**Blue team position:** {Summary of what blue team contests}

**Why this is untestable:** {Specific obstacle — what would be needed that is
not available, and why it is not available}

**Recommendation (labeled as opinion, not verdict):** {The Arbiter's
non-binding read on which position is more likely correct, with reasoning.
This is an opinion to inform the Conductor's decision, not a verdict.}
```

Escalation is not a loophole. The Conductor must then make a decision. Disputes cannot remain permanently open.
