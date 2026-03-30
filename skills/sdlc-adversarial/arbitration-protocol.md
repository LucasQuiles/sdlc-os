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

## Blind-First MAP Protocol

The arbiter produces a MAP vector on every pre-synthesis pass — before disputes are filed — using the blind-first protocol below.

1. Arbiter receives bead evidence and decision trace metadata (blind — no prior verdicts or peer findings)
2. Arbiter produces MAP vector (evidence_strength, impact_severity, base_rate_frequency, pattern_familiarity, decision_confidence) + provisional verdict
3. System records blind pass via `scripts/record-review-pass.sh` with `exposure_mode: blind_first`
4. System reveals precedent pack (if available)
5. Arbiter may revise assessment — revision recorded as a NEW pass with `parent_review_pass_id` pointing to the blind pass, `exposure_mode: precedent_exposed`, and `precedent_match_delta` capturing the shift

---

## The Protocol

### Step 0: Precedent Lookup

Before engaging the full Kahneman protocol, check for prior rulings on substantially similar disputes.

1. Search `references/precedent-system.md` for entries matching: domain + finding type + core disagreement type
2. **Match found — Follow or Distinguish:**
   - If the current dispute is substantially similar to the precedent: apply the same ruling. Issue a verdict citing the precedent. Format: `**Precedent applied:** {verdict-id} — {rule established}`. No test design, no execution needed. This resolves the dispute immediately.
   - If the current dispute differs materially: document what is different (`**Precedent distinguished:** {verdict-id} — differs because {reason}`). Proceed to Step 1.
3. **No match found:** Proceed to Step 1.

**What constitutes "substantially similar":**
- Same domain (e.g., both security findings)
- Same finding type (e.g., both about missing input validation)
- Same core disagreement (e.g., both existence disputes)
- Similar code context (e.g., both involve REST endpoints handling user input)

**What justifies distinguishing:**
- Different deployment context (e.g., internal tool vs. public-facing API)
- Different trust boundary (e.g., authenticated users vs. anonymous)
- Code has been architecturally restructured since precedent was set
- The precedent's reasoning relied on a defense that no longer exists

### Step 1: Dispute Intake and Pre-Registration

Assemble the complete dispute package AND lock the dispute contract before doing any analysis:

```
## Dispute Contract: {Finding ID}

### Red Team Finding
{Full finding: claim, minimal reproduction, impact, evidence, confidence}

### Blue Team Dispute
{Full dispute: contested claim, what evidence would resolve this}

### Pre-Registered Commitments

**Red team — "what would change my mind":**
{Specific observable outcome that, if produced, would cause red team to withdraw the finding}

**Blue team — "what would change my mind":**
{Specific observable outcome that, if produced, would cause blue team to accept the finding}

**Pass/fail criterion (agreed before test runs):**
{Unambiguous statement: "If X is observed, the finding is sustained. If Y is observed, the finding is dismissed."}

**Timebox:**
{Maximum time/token budget for this arbitration — default: one guppy dispatch + one file read. Complex disputes may get two rounds.}

**Precedent applied:** {verdict-id and rule — or "None (no matching precedent)"}
**Precedent distinguished:** {verdict-id and reason — or "N/A"}

### Bead Context
{Bead objective, scope, affected files — enough to understand the domain}
```

The pre-registered commitments are locked before the test is designed. Neither side may revise their "what would change my mind" after seeing the test result. This prevents post-hoc rationalization.

**Timebox enforcement:** The arbiter owns the evidence bundle and the clock. If the timebox expires without a clear result, the arbiter issues the best verdict available from evidence collected so far — it does not extend indefinitely. Deadlines reduce hindsight drift (Mellers protocol).

Do not begin position extraction until the complete contract is locked. Missing commitments produce unfair or unresolvable arbitration.

### Step 2: Position Extraction

Extract each side's position precisely. Use a table:

| | Red Team | Blue Team |
|---|---|---|
| **Claim** | {What red team asserts is true} | {What blue team asserts is true} |
| **What would change their mind** | {Pre-registered from contract} | {Pre-registered from contract} |
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

**Mediating Assessments Protocol (MAP):** Before writing the holistic verdict, score four dimensions independently. Score each dimension BEFORE considering the others — do not let one dimension bias another.

| Dimension | What it measures | 1 | 3 | 5 |
|-----------|-----------------|---|---|---|
| **Evidence strength** | How concrete is the red team's demonstration? | Theoretical only — no code trace | Partial trace — some code paths verified | Full reproduction — end-to-end demonstration |
| **Impact severity** | If real, how bad is the consequence? | Cosmetic — no functional effect | Degraded functionality — some users affected | Data loss, security breach, or service outage |
| **Fix proportionality** | Is the cost of fixing proportional to the risk? | Massive refactor for minor issue | Moderate effort for moderate risk | Simple targeted fix for significant risk |
| **Confidence in test** | How informative was the designed test? | Ambiguous — result could mean either | Suggestive — leans one way but not conclusive | Deterministic — clear pass/fail with unambiguous meaning |

Record scores in the verdict. These scores inform but do not mechanically determine the verdict — they structure reasoning and prevent halo effects where one strong dimension biases assessment of others.

Issue a binding verdict using the format in the next section. The verdict is one of:

- **SUSTAINED** — The test confirmed the red team's claim. The issue is real. Blue team must produce a fix.
- **DISMISSED** — The test confirmed the blue team's position. The issue does not exist, is not exploitable, or is not relevant in this context. Finding is closed.
- **MODIFIED** — The test revealed a partial truth. The issue exists but at a different scope or severity than claimed. Red team's severity or scope is adjusted. Blue team must fix the adjusted finding.

**Inconclusive results:** If the test produces ambiguous results that do not clearly match either side's pre-registered pass/fail criterion:

1. The arbiter declares **INCONCLUSIVE** (not a final verdict — a procedural state)
2. Each side gets **one additional experiment proposal** — a single follow-up test they believe would resolve the ambiguity
3. The arbiter selects the more informative proposal (or combines elements of both) and runs it
4. After the follow-up test, the arbiter **must** issue a binding verdict (SUSTAINED / DISMISSED / MODIFIED) — a second INCONCLUSIVE is not permitted
5. If the follow-up also fails to resolve: issue the best verdict from available evidence + document residual uncertainty in the verdict's reasoning field

This two-round maximum prevents infinite arbitration loops while acknowledging that adversarial collaboration outcomes are often "integration and deeper understanding" rather than a clean winner (Kahneman-Klein collaboration pattern). The goal is to narrow the disagreement, not necessarily eliminate it.

---

## Verdict Format

```
## Verdict: {Finding ID}

**Decision:** SUSTAINED | DISMISSED | MODIFIED

**Dispute contract locked:** {timestamp}
**Timebox:** {budget used} of {budget allocated}

**Red team claim:** {One-sentence summary of what red team asserted}
**Red team pre-commitment:** {What they said would change their mind}

**Blue team position:** {One-sentence summary of what blue team contested}
**Blue team pre-commitment:** {What they said would change their mind}

**Core disagreement:** existence | severity | exploitability | relevance

**Test designed:** {Description of the fair test — what was tested, how, and
why this test addresses the core disagreement}

**Test result:** {Raw output or direct observation from the test execution —
not a summary, the actual evidence}

**Follow-up round (if needed):**
- Proposed by: {red | blue | arbiter}
- Test: {what was run}
- Result: {evidence}

**Reasoning:** {Why this evidence resolves the dispute — connect the test
result to the pre-registered pass/fail criterion and each side's
pre-commitment. Show the logical chain: evidence X means Y because Z.}

**Residual uncertainty:** {Any remaining ambiguity after verdict — "None" if
clean resolution, or specific description of what remains unknown}

**If MODIFIED — adjusted scope/severity:** {What the finding becomes after
adjustment. Include the revised severity level and the narrowed or expanded
scope. Blue team must fix this adjusted version.}

**Dimension scores:**
- Evidence strength: {1-5}
- Impact severity: {1-5}
- Fix proportionality: {1-5}
- Confidence in test: {1-5}

**Precedent rule established:** {One reusable sentence — the principle this verdict establishes for future similar disputes}
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
