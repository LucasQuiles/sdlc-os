# SDLC OS v3 Research Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate 14 research-driven concepts into the SDLC OS plugin to reduce bugs, drift, human supervision, and improve production readiness.

**Architecture:** All changes are markdown prompt engineering edits to the existing plugin at `/Users/q/.claude/plugins/sdlc-os/`. Five independent streams (A-E) can execute in parallel. Each stream modifies a non-overlapping set of files.

**Tech Stack:** Markdown files in a Claude Code plugin. No code, no tests — verification is reading files back and confirming content integrates correctly.

## RAG Context

RAG_DEGRADED: Not applicable — this plan modifies a Claude Code plugin (`~/.claude/plugins/sdlc-os/`) consisting entirely of markdown prompt engineering files. No application codebase is involved. All 19 target files were read directly via the Read tool during design. The research synthesis driving these changes is documented in `/Users/q/sdlc-os-research-synthesis.md` and the five research agent output files in `/private/tmp/claude-501/-Users-q/45383530-8dfa-4416-b05f-8cfea629c0cf/tasks/`.

---

## Task 1 (Stream A): Adversarial Cycle Enhancements

**Files:**
- Modify: `skills/sdlc-adversarial/SKILL.md` (lines ~60-170, cycle sections)
- Modify: `references/adversarial-quality.md` (response format section)

Adds: pretrial filter, Daubert gate, plea bargaining, entropy stopping.

- [ ] **Step 1: Add Phase 2.5 (Pretrial Filter) to SKILL.md**

In `skills/sdlc-adversarial/SKILL.md`, insert the following new section between the existing "### Phase 2: Cross-Reference" section (ends around line 75) and "### Phase 3: Directed Strike" section:

```markdown
### Phase 2.5: Pretrial Filter

After cross-reference produces final domain priorities but before directed strike fires, the Conductor screens recon signals against three dismissal criteria. This is not a separate agent dispatch — the Conductor applies these filters as part of cross-reference processing.

**Dismissal criteria:**

1. **Scope exclusion** — The recon signal concerns code not changed in this bead. Recon guppies sometimes flag pre-existing issues in surrounding code — these are out of scope for this bead's AQS engagement. Log the signal for future reference but do not strike.

2. **Category exclusion** — The recon signal is about style, formatting, or naming conventions when the domain under review is functionality or security. Style concerns belong to the usability domain. If usability is not active for this bead, the signal is dismissed. If usability IS active, redirect the signal there.

3. **Prior resolution (res judicata)** — The recon signal matches a finding that was previously ruled DISMISSED in the precedent database (`references/precedent-system.md`). Match on: domain + finding type + same code path. If an exact match exists, the signal is precluded from re-litigation. Log: "Precluded — matches precedent {verdict-id}."

**Logging:** Every pretrial dismissal is logged in the recon artifact (`recon-{bead-id}.md`) with the dismissal criterion and reasoning. This creates an audit trail and prevents silent filtering.

**Override:** If the Conductor believes a pretrial dismissal is wrong (e.g., a prior DISMISSED precedent may no longer apply due to changed context), the Conductor can override the dismissal and allow the signal through. Overrides must be documented with reasoning.
```

- [ ] **Step 2: Add Daubert Gate to Phase 3 in SKILL.md**

In `skills/sdlc-adversarial/SKILL.md`, in the existing Phase 3 section, after the line "5. Applies mandatory shrinking: every hit must be reduced to minimal reproduction" (around line 84) and before "6. Produces formal findings in the required format", insert:

```markdown
5.5. **Applies Daubert evidence gate:** Before submitting findings, the red team commander self-checks each finding against three reliability criteria:

   - **Factual basis** — Every file:line reference in the finding must exist. The red team commander verifies by reading the cited locations. Findings citing non-existent code paths are hallucinations and must be dropped.
   - **Methodological reliability** — The finding must come from executed probe output (a guppy returned HIT with evidence), not from pattern-match inference ("this looks like it could be vulnerable"). Inference-only findings are downgraded to `Assumed` confidence.
   - **Known false-positive pattern** — Cross-reference the finding type against the precedent database. If this finding type has been DISMISSED more than twice on similar code patterns, flag it as high-false-positive-risk in the finding. This does not block submission but alerts the blue team and arbiter.

   Findings that fail the factual basis check are dropped entirely (not submitted). Findings that fail methodological reliability are downgraded to `Assumed`. The Daubert gate is a self-check, not an external review — the red team commander applies it to its own output before delivery.
```

- [ ] **Step 3: Add Plea Bargaining to Phase 4 in SKILL.md**

In `skills/sdlc-adversarial/SKILL.md`, in the Phase 4 section, after the existing three response types (accepted, rebutted, disputed) around line 97, insert:

```markdown
**Fast-track resolution (plea bargaining):** For uncontested findings where both sides agree, a streamlined path is available:

**Eligibility:** A finding qualifies for fast-track when ALL of:
- Red team confidence is `Verified` (not Likely or Assumed)
- Blue team immediately recognizes the issue as real (no analysis needed to confirm)
- Severity is `medium` or `low` (high and critical always get full response)
- Fix is straightforward (single-site change, no architectural implications)

**Fast-track response format:**
```
## Response: {Finding ID}
**Action:** accepted-fast-track
**Fix:** {file:line — one-line description of change}
**Verification:** {one-line confirmation that the fix addresses the finding}
**Confidence:** {0.0-1.0 with brief rationale}
```

Fast-track responses skip the full reproduction cycle, regression narrative, and principle extraction. They are logged in the adversarial report identically to `accepted` findings but marked as fast-tracked. The arbiter is never involved.

**Do not abuse fast-track.** If the blue team is uncertain about whether the issue is real, it is not a fast-track candidate — use the full `accepted` flow with reproduction. Fast-track is for cases where the finding is obviously correct and the fix is obviously right.
```

- [ ] **Step 4: Replace Cycle 2 trigger with Convergence Assessment in SKILL.md**

In `skills/sdlc-adversarial/SKILL.md`, in the "## Cycle Budget" section (around line 143-150), replace the existing Cycle 2 rules with:

```markdown
### Cycle Budget

AQS runs a maximum of **2 full cycles per bead**.

- **Cycle 1:** Always runs when AQS is active. Red team attacks → blue team responds → accepted/sustained fixes applied.

- **Cycle 2 — Convergence Assessment:** After Cycle 1 completes, the Conductor assesses whether the finding space has converged. Cycle 2 fires only if the space has NOT converged.

  **Convergence indicators (all three must be true to skip Cycle 2):**
  1. **Low diversity** — Cycle 1 findings were concentrated in a single domain
  2. **Low severity** — All Cycle 1 fixes were `medium` or `low` severity
  3. **Low volume** — Cycle 1 produced fewer than 3 total findings

  If all three convergence indicators are true → skip Cycle 2. Log the convergence decision with reasoning in the AQS report.

  If ANY indicator is false (findings span multiple domains, any `high`/`critical` fix was applied, or 3+ findings were produced) → Cycle 2 is **mandatory**. The attack surface has been meaningfully changed and needs re-verification.

- **Immediate completion:** If Cycle 1 produces no findings (all domains return clean), AQS completes immediately without Cycle 2. No convergence assessment needed.

- **Budget exhausted:** If 2 cycles complete and residual risk remains unresolved, escalate to Conductor with the adversarial report. Report verdict as `PARTIALLY_HARDENED` or `DEFERRED` as appropriate.
```

- [ ] **Step 5: Add accepted-fast-track to adversarial-quality.md**

In `references/adversarial-quality.md`, in the "## Response Format (Blue Team)" section, add after the existing format block:

```markdown
### Fast-Track Response Format

For uncontested medium/low severity findings (see SKILL.md Phase 4 for eligibility):

```
## Response: {Finding ID}
**Action:** accepted-fast-track
**Fix:** {file:line — one-line description}
**Verification:** {one-line confirmation}
**Confidence:** {0.0-1.0 with rationale}
```
```

- [ ] **Step 6: Verify all Phase references are consistent**

Read `skills/sdlc-adversarial/SKILL.md` back. Confirm:
- Phase numbering is sequential (1, 2, 2.5, 3, 4, 5, 6)
- Cross-references to phases in other sections still point to correct phase numbers
- The cycle budget section references the convergence assessment consistently

- [ ] **Step 7: Commit Stream A**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-adversarial/SKILL.md references/adversarial-quality.md
git commit -m "feat(adversarial): add pretrial filter, Daubert gate, plea bargaining, entropy stopping

Phase 2.5 pretrial filter screens recon signals before expensive directed strike.
Daubert gate ensures red team findings have factual basis and methodological reliability.
Plea bargaining fast-tracks uncontested medium/low findings.
Convergence assessment replaces fixed Cycle 2 trigger with entropy-aware decision."
```

---

## Task 2 (Stream B): Arbiter Enhancements + Precedent System

**Files:**
- Modify: `skills/sdlc-adversarial/arbitration-protocol.md`
- Modify: `agents/arbiter.md`
- Create: `references/precedent-system.md`

Adds: precedent lookup (stare decisis), MAP dimension scoring, precedent database.

- [ ] **Step 1: Create precedent-system.md**

Create `references/precedent-system.md`:

```markdown
# Precedent System (Stare Decisis)

The precedent database records reusable rulings from arbiter verdicts. Its purpose is threefold:

1. **Consistency** — Similar issues must receive similar rulings across beads and sessions
2. **Efficiency** — Previously decided issues can be resolved by citation rather than re-litigation
3. **Institutional memory** — The system accumulates judgment over time

---

## How Precedent Works

### For the Arbiter (Step 0 — before dispute contract lock)

Before locking the dispute contract, search this database:

1. **Match criteria:** domain + finding type + core disagreement type
2. **If match found:**
   - **Follow precedent** — Apply the same ruling, cite the prior verdict ID. No test needed. Resolve in the verdict format with: `**Precedent applied:** {verdict-id} — {rule established}`
   - **Distinguish** — If the current case differs materially, state what is different and why the prior ruling doesn't apply. Then proceed with the full Kahneman protocol.
3. **If no match found:** Proceed with the full protocol.

### For the Conductor (Phase 6 — after every arbiter verdict)

After every arbiter verdict, extract the rule and append a precedent entry below. This is mandatory, not optional.

### For the Pretrial Filter (Phase 2.5)

Recon signals matching a DISMISSED precedent on the same code path are precluded from re-litigation (res judicata). Exception: if the code has materially changed since the precedent was established, the preclusion does not apply.

---

## Precedent Decay

Precedents are living guidance, not eternal law:

- **Strong precedent** — Issued within the current project context, code unchanged. Follow unless distinguishable.
- **Weak precedent** — Issued before a major architectural change, or code has been substantially modified. Treat as guidance, not binding.
- **Superseded** — A later verdict on the same finding type reached a different conclusion. The later ruling controls.

---

## Precedent Database

<!-- Entries are appended by the Conductor after each arbiter verdict -->
<!-- Format: one entry per verdict, chronological order -->

_No precedents recorded yet. The database grows through adversarial engagement._
```

- [ ] **Step 2: Add Step 0 (Precedent Lookup) to arbitration-protocol.md**

In `skills/sdlc-adversarial/arbitration-protocol.md`, insert before the existing "### Step 1: Dispute Intake and Pre-Registration" section:

```markdown
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
```

- [ ] **Step 3: Add MAP Scoring sub-step to arbitration-protocol.md**

In `skills/sdlc-adversarial/arbitration-protocol.md`, in the existing "### Step 5: Verdict" section, insert before the line "Issue a binding verdict using the format":

```markdown
**Mediating Assessments Protocol (MAP):** Before writing the holistic verdict, score four dimensions independently. Score each dimension BEFORE considering the others — do not let one dimension bias another.

| Dimension | What it measures | 1 | 3 | 5 |
|-----------|-----------------|---|---|---|
| **Evidence strength** | How concrete is the red team's demonstration? | Theoretical only — no code trace | Partial trace — some code paths verified | Full reproduction — end-to-end demonstration |
| **Impact severity** | If real, how bad is the consequence? | Cosmetic — no functional effect | Degraded functionality — some users affected | Data loss, security breach, or service outage |
| **Fix proportionality** | Is the cost of fixing proportional to the risk? | Massive refactor for minor issue | Moderate effort for moderate risk | Simple targeted fix for significant risk |
| **Confidence in test** | How informative was the designed test? | Ambiguous — result could mean either | Suggestive — leans one way but not conclusive | Deterministic — clear pass/fail with unambiguous meaning |

Record scores in the verdict. These scores inform but do not mechanically determine the verdict — they structure reasoning and prevent halo effects where one strong dimension biases assessment of others.
```

- [ ] **Step 4: Add MAP scores and precedent fields to verdict format in arbitration-protocol.md**

In `skills/sdlc-adversarial/arbitration-protocol.md`, in the verdict format template, add after `**Timebox:**`:

```markdown
**Precedent applied:** {verdict-id and rule — or "None (no matching precedent)"}
**Precedent distinguished:** {verdict-id and reason — or "N/A"}
```

And add after `**If MODIFIED:**`:

```markdown
**Dimension scores:**
- Evidence strength: {1-5}
- Impact severity: {1-5}
- Fix proportionality: {1-5}
- Confidence in test: {1-5}

**Precedent rule established:** {One reusable sentence — the principle this verdict establishes for future similar disputes}
```

- [ ] **Step 5: Update arbiter.md agent definition**

In `agents/arbiter.md`, add to the "## The Kahneman Protocol" section, before "### Step 1: Intake and Contract Lock":

```markdown
### Step 0: Precedent Lookup
Check `references/precedent-system.md` for prior rulings on substantially similar disputes (same domain + finding type + disagreement type). Follow precedent or distinguish with documented reasoning. See `arbitration-protocol.md` Step 0 for full protocol.
```

In `agents/arbiter.md`, add to the "## Required Output Format" section, after `**Timebox:**`:

```markdown
**Precedent:** {applied verdict-id | distinguished verdict-id | "None"}
```

And after `**If MODIFIED:**`:

```markdown
**Dimension scores:** Evidence: {1-5}, Impact: {1-5}, Proportionality: {1-5}, Test confidence: {1-5}
**Rule established:** {one reusable sentence for precedent database}
```

- [ ] **Step 6: Verify cross-references**

Read all three modified files back. Confirm:
- Arbitration protocol references `references/precedent-system.md` correctly
- Arbiter agent references `arbitration-protocol.md` Step 0
- Verdict format in both files includes the new fields consistently
- Step numbering is sequential (0, 1, 2, 3, 4, 5)

- [ ] **Step 7: Commit Stream B**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/precedent-system.md skills/sdlc-adversarial/arbitration-protocol.md agents/arbiter.md
git commit -m "feat(arbiter): add precedent system and MAP scoring

Stare decisis: arbiter checks for prior rulings before engaging full protocol.
Res judicata: pretrial filter can preclude findings matching DISMISSED precedents.
MAP scoring: four independent dimension scores before holistic verdict.
Precedent database grows automatically through adversarial engagement."
```

---

## Task 3 (Stream C): Agent Prompt Enhancements

**Files:**
- Modify: `agents/red-functionality.md`
- Modify: `agents/red-security.md`
- Modify: `agents/red-usability.md`
- Modify: `agents/red-resilience.md`
- Modify: `agents/blue-functionality.md`
- Modify: `agents/blue-security.md`
- Modify: `agents/blue-usability.md`
- Modify: `agents/blue-resilience.md`

Adds: assumptions manifest, ACH technique, Daubert self-check, confidence scores (red); disclosure obligation, constitution reference, principle extraction, confidence scores (blue).

- [ ] **Step 1: Add Step 0 ASSUMPTIONS + ACH + Daubert + confidence to red-functionality.md**

In `agents/red-functionality.md`, insert before "### 1. RECON":

```markdown
### 0. ASSUMPTIONS
Before attacking, extract the bead's implicit assumptions — what must be true for this code to work correctly?

- **Input assumptions** — What types, ranges, formats does this code expect? What sanitization does it rely on callers to provide?
- **Environment assumptions** — What services, databases, or state does this code assume are available and healthy?
- **Ordering assumptions** — Does this code assume sequential execution? Single-threaded access? No concurrent modifications?
- **Caller assumptions** — Does this code assume callers are trusted, authenticated, or well-behaved?

List the top 3-5 assumptions. Use them to focus your TARGET step — the most productive attack vectors violate specific assumptions.
```

In `agents/red-functionality.md`, in the "### 4. ASSESS" section, replace the existing content with:

```markdown
### 4. ASSESS
Triage guppy results. Separate real hits from noise. A hit is real only if you can trace a concrete execution path that produces incorrect behavior.

**For ambiguous results** (not a clear HIT or MISS), apply Analysis of Competing Hypotheses:
1. List all plausible explanations (e.g., "genuine bug" vs. "intentional design" vs. "handled upstream" vs. "unreachable path")
2. For each hypothesis, identify what evidence would be *inconsistent* with it
3. Favor the hypothesis with the fewest inconsistencies — not the most confirmations
4. If the winning hypothesis is "not a bug," drop the finding. If genuinely ambiguous, downgrade to `Assumed`.

**Daubert self-check** — Before proceeding to SHRINK, verify each finding:
- Does every file:line reference actually exist? (Drop hallucinated paths)
- Did the finding come from executed guppy output, not pattern-match inference? (Downgrade inference-only to `Assumed`)
- Has this finding type been DISMISSED more than twice in the precedent database? (Flag as high-false-positive-risk)
```

In `agents/red-functionality.md`, in the finding format, replace `**Confidence:** Verified | Likely | Assumed` with:

```markdown
**Confidence:** Verified | Likely | Assumed
**Confidence score:** {0.0-1.0}
**Confidence rationale:** {what drives the score — e.g., "guppy confirmed path (0.9) but did not test with concurrent access (−0.1)"}
```

- [ ] **Step 2: Apply identical changes to red-security.md**

Apply the same three changes to `agents/red-security.md`:
1. Add "### 0. ASSUMPTIONS" before "### 1. RECON" (same content as Step 1, word for word)
2. Replace "### 4. ASSESS" with the ACH + Daubert version (same content as Step 1, word for word, except the opening line should reference "security vulnerability" instead of "incorrect behavior": "A hit is real only if you can describe a concrete attack scenario — who is the attacker, what do they control, what can they achieve?")
3. Add confidence score fields to finding format (same as Step 1, word for word)

- [ ] **Step 3: Apply identical changes to red-usability.md**

Apply the same three changes to `agents/red-usability.md`:
1. Add "### 0. ASSUMPTIONS" before "### 1. RECON" (same content)
2. Replace "### 4. ASSESS" with ACH + Daubert version (keep opening line about "concrete scenario where a real user or developer would be confused")
3. Add confidence score fields to finding format

- [ ] **Step 4: Apply identical changes to red-resilience.md**

Apply the same three changes to `agents/red-resilience.md`:
1. Add "### 0. ASSUMPTIONS" before "### 1. RECON" (same content)
2. Replace "### 4. ASSESS" with ACH + Daubert version (keep opening line about "concrete failure scenario")
3. Add confidence score fields to finding format

- [ ] **Step 5: Add disclosure + constitution + confidence to blue-functionality.md**

In `agents/blue-functionality.md`, add to the end of the "## Constraints" section:

```markdown
- **Duty of candor:** When generating a fix or rebuttal, proactively disclose areas of uncertainty you encountered. If you noticed something suspicious outside the scope of the current finding, flag it as a disclosure note. This is not a finding — it is an honest signal to the Conductor.
- **Constitution compliance:** Before producing a fix, check `references/code-constitution.md` for applicable rules. Fixes must conform. If the fix cannot conform (rule conflicts with correct fix), flag the conflict to the Conductor.
```

In `agents/blue-functionality.md`, in the "### If accepted:" section, add after the last field:

```markdown
- **Principle extracted:** {Reusable rule established by this fix, if any — e.g., "All collection operations must handle empty input" — or "None (context-specific fix)"}
- **Disclosure notes:** {Areas of uncertainty, adjacent concerns noticed, or "None"}
- **Confidence:** {0.0-1.0}
- **Confidence rationale:** {what drives the score}
```

In `agents/blue-functionality.md`, in the "### If rebutted:" section, add after the last field:

```markdown
- **Disclosure notes:** {Areas of uncertainty, adjacent concerns noticed, or "None"}
- **Confidence:** {0.0-1.0}
- **Confidence rationale:** {what drives the score — a rebuttal at < 0.7 should probably be a dispute instead}
```

- [ ] **Step 6: Apply identical changes to blue-security.md**

Apply the same changes to `agents/blue-security.md`:
1. Add duty of candor and constitution compliance to Constraints (same content as Step 5)
2. Add principle extracted, disclosure notes, and confidence to "If accepted" format
3. Add disclosure notes and confidence to "If rebutted" format

- [ ] **Step 7: Apply identical changes to blue-usability.md**

Same changes as Steps 5-6 applied to `agents/blue-usability.md`.

- [ ] **Step 8: Apply identical changes to blue-resilience.md**

Same changes as Steps 5-6 applied to `agents/blue-resilience.md`.

- [ ] **Step 9: Verify consistency across all 8 agents**

Read all 8 modified agent files. Confirm:
- All 4 red agents have: Step 0 ASSUMPTIONS, ACH in ASSESS, Daubert self-check, confidence score in finding format
- All 4 blue agents have: duty of candor, constitution compliance, principle extraction, disclosure notes, confidence score
- Confidence score format is identical across all 8 agents
- No formatting inconsistencies between agents

- [ ] **Step 10: Commit Stream C**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add agents/red-functionality.md agents/red-security.md agents/red-usability.md agents/red-resilience.md agents/blue-functionality.md agents/blue-security.md agents/blue-usability.md agents/blue-resilience.md
git commit -m "feat(agents): add assumptions, ACH, Daubert, disclosure, constitution, confidence

Red team: Step 0 ASSUMPTIONS extracts testable assumptions before attack.
Red team: ACH technique for ambiguous results favors hypothesis with fewest inconsistencies.
Red team: Daubert self-check filters hallucinated and inference-only findings.
Blue team: Duty of candor requires proactive disclosure of uncertainty.
Blue team: Constitution compliance and principle extraction for learning loop.
All agents: Verbalized confidence scores (0.0-1.0) with rationale."
```

---

## Task 4 (Stream D): Cynefin Classification + Orchestration

**Files:**
- Modify: `skills/sdlc-adversarial/scaling-heuristics.md` (replace complexity tiers)
- Modify: `skills/sdlc-orchestrate/SKILL.md` (bead format, Frame phase)
- Create: `references/quality-slos.md`

- [ ] **Step 1: Replace complexity tiers with Cynefin in scaling-heuristics.md**

In `skills/sdlc-adversarial/scaling-heuristics.md`, replace the "## Complexity Assessment" section (the table and rationale, approximately lines 7-17) with:

```markdown
## Cynefin Domain Assessment

Map each bead to a Cynefin domain before activating any AQS domains. The domain determines the overall AQS behavior and process depth.

| Domain | AQS Behavior | Process Adjustments |
|---|---|---|
| **Clear** | Skip AQS entirely — bead goes `proven → merged` directly. | L0 runner only. Auto-merge if tests pass. No Sentinel needed if error budget is healthy. |
| **Complicated** | Recon burst fires (all 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. | Standard loop depth (L0-L2 + AQS). Expert review by domain-specific agents. |
| **Complex** | All four domains active. Full directed strike on HIGH/MED. Light sweep on LOW. Cycle 2 governed by convergence assessment. | Bead spec MUST include safe-to-fail section (rollback plan). Feature flags recommended for new behavior. Full adversarial engagement. |
| **Chaotic** | Skip AQS entirely. Act-first single runner. Fast-path approval. | Emergency process: single runner, L0 only, no Sentinel during execution. MANDATORY postmortem bead auto-created after merge — this bead goes through full Complicated-level review retroactively. |
| **Confusion** | Block. Bead cannot be created until reclassifiable. | Force decomposition. The Conductor must break the work down until each piece is classifiable as Clear, Complicated, or Complex. If decomposition fails, escalate to user for clarification. |

Security-sensitive overrides ALL domain assessments. A 1-line change that touches auth is security-sensitive regardless of Cynefin domain.
```

- [ ] **Step 2: Replace complexity signals with Cynefin signals in scaling-heuristics.md**

Replace the "## Complexity Signals" section (approximately lines 22-54) with:

```markdown
## Cynefin Domain Signals

Use these signals to assign the Cynefin domain. Check top-down — security-sensitive signals override everything. Chaotic/Confusion signals override Clear/Complicated/Complex.

### Chaotic signals (any one — act first, review later)
- Production incident requiring immediate fix
- Security vulnerability with evidence of active exploitation
- Data corruption or loss currently in progress
- User explicitly flags as emergency with time pressure

### Confusion signals (any one — stop, decompose, reclassify)
- Requirements contain contradictions that cannot be resolved without user input
- Success criteria cannot be stated in observable, testable terms
- Multiple valid interpretations exist with no way to choose between them
- Bead scope cannot be bounded — it's unclear what is in and out of scope

### Clear signals (ALL must be true — one exception lifts to Complicated)
- Single file changed
- Fewer than 50 lines changed
- No new I/O operations introduced (no new database calls, HTTP calls, file reads/writes)
- Internal refactor only — no changes to public API or exported interface
- Documentation-only changes (comments, README, docstrings with no behavioral impact)

### Complicated signals (any one is sufficient)
- 2–5 files changed
- New function or module introduced that is not externally exposed
- New error handling paths added to existing code
- New API endpoint or function exported for use by other modules

### Complex signals (any one is sufficient)
- 5 or more files changed
- New external integration introduced (new HTTP client, new database, new third-party service)
- Changes to data model (new tables, new schema fields, new serialization format)
- New asynchronous patterns introduced (new queues, new event emitters, new background jobs)
- Cross-service refactoring affecting multiple module boundaries

### Security-sensitive overrides (any one forces security-sensitive tier regardless of domain)
- Any user-supplied input reaches a new code path (new route, new parameter, new field)
- Changes to authentication logic (login, token validation, session management)
- Changes to authorization logic (permission checks, role validation, ownership checks)
- New credential handling (storing, transmitting, or validating passwords, API keys, tokens)
- New data exposure paths (new API response fields, new log statements touching sensitive data)
- New filesystem or command execution operations
- New cross-origin request handling (CORS configuration, postMessage handlers)
```

- [ ] **Step 3: Update bead format in sdlc-orchestrate/SKILL.md**

In `skills/sdlc-orchestrate/SKILL.md`, in the bead format section (around line 97-106), add after `**Sentinel notes:**`:

```markdown
**Cynefin domain:** clear | complicated | complex | chaotic | confusion
**Assumptions:** [explicit list of what must be true for this bead to work — populated by runner]
**Safe-to-fail:** [rollback plan — REQUIRED for Complex domain beads, optional otherwise]
**Confidence:** [runner's self-assessed confidence 0.0-1.0 with rationale — populated after execution]
```

- [ ] **Step 4: Add Cynefin to Frame phase in sdlc-orchestrate/SKILL.md**

In `skills/sdlc-orchestrate/SKILL.md`, in the "### Phase 1: Frame" section (around line 114-118), add to the "**How:**" line:

```markdown
**How:** Dispatch `sonnet-investigator` to analyze requirements. Sentinel checks for gaps. **Conductor assigns Cynefin domain to each bead** using the signals in `skills/sdlc-adversarial/scaling-heuristics.md`. Chaotic beads skip directly to Execute with a single runner. Confusion beads are blocked until decomposed.
```

- [ ] **Step 5: Create quality-slos.md**

Create `references/quality-slos.md`:

```markdown
# Quality SLOs and Error Budget Policy

Quality governance for agent-generated code. The Conductor tracks these indicators during Phase 5 (Synthesize) and applies the error budget policy to subsequent tasks.

---

## Quality SLIs (Service Level Indicators)

| SLI | How Measured | Notes |
|-----|-------------|-------|
| **Lint pass rate** | % of generated code passing all configured lint rules on first submission | Measured per bead at L0 |
| **Type safety rate** | % of generated code passing type checker on first run | Measured per bead at L0 |
| **Test coverage delta** | Net change in test coverage from each bead | Must not decrease — measured during Sentinel check |
| **Cognitive complexity** | Maximum per-function cognitive complexity in changed code | Measured via fitness functions |
| **AQS critical finding rate** | Critical/high findings per task | Measured during AQS engagement |

---

## Quality SLOs (Service Level Objectives)

| SLI | Target | Rationale |
|-----|--------|-----------|
| Lint pass rate | >= 95% | Agents should produce clean code by default |
| Type safety rate | >= 98% | Type errors indicate fundamental misunderstanding |
| Test coverage delta | >= 0 | Never decrease coverage — new code must bring its own tests |
| Cognitive complexity | <= 15 per function | Beyond 15, code becomes hard for both humans and LLMs to reason about |
| AQS critical finding rate | < 1 per task | More than 1 critical finding per task indicates systemic generation issues |

---

## Error Budget Policy

The error budget is the gap between target and 100%. When budget is healthy, the system can move faster. When depleted, the system must slow down.

### Budget Healthy (all SLOs met for last 3 tasks)
- Clear-domain beads auto-merge without Sentinel (L0 → merge)
- Complicated-domain beads may skip Cycle 2 even if convergence assessment says otherwise
- Conductor can batch LOSA observations (sample every 3rd bead instead of every bead)

### Budget Warning (1 SLO breached in last 3 tasks)
- All beads get Sentinel review regardless of Cynefin domain
- Conductor logs which SLO is at risk and investigates root cause
- No process relaxations allowed

### Budget Depleted (2+ SLOs breached in last 3 tasks)
- All beads get full AQS engagement regardless of Cynefin domain (even Clear beads)
- Conductor must address root cause before new feature work proceeds
- Constitution review triggered — check if existing rules cover the failure pattern
- LOSA sampling rate increased to 50%

### Budget Tracking

The Conductor maintains a running budget state in the task's active directory:

```
## Quality Budget: {task-id}
**Current state:** healthy | warning | depleted
**SLI readings (last 3 tasks):**
| Task | Lint | Types | Coverage | Complexity | Critical Findings |
|------|------|-------|----------|------------|-------------------|
| ... | ... | ... | ... | ... | ... |
**Breached SLOs:** {list or "None"}
**Action taken:** {what was done about breaches, or "N/A"}
```

Written to `docs/sdlc/active/{task-id}/quality-budget.md` during Phase 5.
```

- [ ] **Step 6: Verify Cynefin terminology is consistent**

Read `scaling-heuristics.md` and `sdlc-orchestrate/SKILL.md` back. Confirm:
- All references to "Trivial/Moderate/Complex" complexity tiers are replaced with Cynefin domains
- The orchestrate skill references the scaling heuristics file correctly
- The "Complexity-Based Activation" table in orchestrate SKILL.md uses Cynefin terms
- Domain selection heuristics and multi-domain activation patterns still make sense with Cynefin

Update the "**Complexity-Based Activation**" table in `sdlc-orchestrate/SKILL.md` (around line 86-90) to use Cynefin terms:

```markdown
- **Complexity-Based Activation:**
  - **Clear beads:** Skip AQS entirely. Beads go `proven → merged`.
  - **Complicated beads:** Recon burst + Conductor selects 1-2 domains.
  - **Complex beads:** All four domains active. Safe-to-fail required.
  - **Chaotic beads:** Skip AQS. Postmortem bead auto-created after merge.
  - **Confusion beads:** Blocked until decomposed and reclassified.
  - **Security-sensitive beads:** All four domains, security always HIGH. Overrides Cynefin domain.
```

- [ ] **Step 7: Commit Stream D**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-adversarial/scaling-heuristics.md skills/sdlc-orchestrate/SKILL.md references/quality-slos.md
git commit -m "feat(orchestration): Cynefin classification, error budgets, enhanced bead format

Replace Trivial/Moderate/Complex tiers with Cynefin domains (Clear/Complicated/Complex/Chaotic/Confusion).
Add Chaotic (act-first + mandatory postmortem) and Confusion (block until decomposed).
Add quality SLIs/SLOs with three-tier error budget policy governing system velocity.
Extend bead format with Cynefin domain, assumptions, safe-to-fail, and confidence."
```

---

## Task 5 (Stream E): Monitoring, Learning, and New Agents

**Files:**
- Modify: `skills/sdlc-loop/SKILL.md`
- Modify: `agents/oracle-adversarial-auditor.md`
- Create: `references/calibration-protocol.md`
- Create: `references/code-constitution.md`
- Create: `agents/losa-observer.md`

- [ ] **Step 1: Create code-constitution.md**

Create `references/code-constitution.md`:

```markdown
# Code Constitution

A living set of rules distilled from adversarial findings. Each rule represents a reusable principle extracted from accepted red team findings and arbiter verdicts.

---

## How the Constitution Works

### For Blue Team Agents
Before producing a fix, check this constitution for applicable rules:
- If a rule applies, the fix must conform to it
- If the fix cannot conform (rule conflicts with correct fix), flag the conflict to the Conductor — the rule may need updating
- After producing an accepted fix, extract the underlying principle and submit it as a `**Principle extracted:**` in your response

### For the Conductor
During Phase 6 (Bead Update), accumulate extracted principles:
1. Read all `**Principle extracted:**` fields from blue team responses
2. For each non-"None" principle, check if it's already in the constitution
3. If new, append as a new rule below
4. If it refines an existing rule, update the existing rule and mark it as refined

### For Red Team Agents
The constitution is NOT your attack surface — you attack the CODE, not the rules. However, if you notice code that violates a constitutional rule, it is a valid finding (the code was generated without following established rules).

---

## Rule Status

- **active** — Currently enforced. Blue team must conform.
- **under-review** — Conductor is evaluating whether this rule is still applicable. Blue team should conform but may flag conflicts.
- **superseded** — Replaced by a newer rule. Retained for history. Not enforced.

---

## Constitutional Rules

<!-- Rules are appended by the Conductor during Phase 6 -->
<!-- Format: one entry per rule, chronological order -->

_No rules recorded yet. The constitution grows through adversarial engagement._
```

- [ ] **Step 2: Create calibration-protocol.md**

Create `references/calibration-protocol.md`:

```markdown
# Calibration Protocol

Procedures for detecting and correcting agent drift, noise, and quality degradation across sessions.

---

## Agent Drift Monitoring (L6 Calibration Loop)

### Cadence
- **Routine:** Every 5th task, the Conductor injects a calibration bead
- **On suspicion:** If the Conductor notices declining quality, unexpected agent behavior, or increasing arbiter invocations

### Calibration Bead Process
1. Select or create a calibration bead — known-good code with 3-5 deliberately planted defects spanning at least 2 domains (e.g., one security flaw, one logic error, one missing timeout)
2. Run the calibration bead through L1 (Sentinel) + L2 (Oracle) + L2.5 (AQS)
3. Compare detection results against known-planted defects
4. **Detection rate >= baseline** → System is calibrated. Log result and continue.
5. **Detection rate < baseline** → System is drifting. Investigate:
   - Which defect types were missed? → Update regression watchlist
   - Which agents failed to detect? → Review agent prompts for decay
   - Has the constitution grown rules that conflict with detection? → Constitution review
6. After recalibration changes, re-run the same calibration bead to verify improvement

### Baseline
The baseline detection rate is established by the first calibration run. Initial target: detect >= 80% of planted defects. The baseline may increase as the system matures.

---

## Drift Signals

Three types of drift to monitor (from Agent Drift research, arXiv:2601.04170):

| Drift Type | Definition | Detection Signal | Response |
|-----------|-----------|-----------------|----------|
| **Semantic drift** | Agent outputs diverge from task intent while remaining syntactically valid | Fitness function scores declining across sessions; LOSA quality scores trending downward | Review agent prompts; check for prompt pollution from accumulated context |
| **Coordination drift** | Multi-agent consensus degrades | Arbiter invocations increasing per bead; more disputes, fewer clean resolutions | Review agent role boundaries; check for overlapping or conflicting instructions |
| **Behavioral drift** | Agents develop strategies not in their prompts | Agent outputs stop matching expected format; unexpected response patterns | Full agent prompt review; check for learned anti-patterns |

---

## Regression Watchlist

A running list of defect types that have been found and fixed in prior sessions. The Conductor periodically verifies these would still be caught.

| Defect Type | First Found | Domain | Detection Agent | Last Verified |
|-------------|------------|--------|-----------------|---------------|
| _(populated through adversarial engagement)_ | | | | |

Update this table after every calibration run. If a previously-caught defect type is missed, escalate immediately.

---

## Noise Audit

Measures consistency of the system's judgment by re-running the same review and comparing results.

### Cadence
- **Routine:** Every 10th task
- **On suspicion:** If the Conductor observes contradictory verdicts on similar findings

### Procedure
1. Select a completed bead that produced findings during its AQS engagement
2. Re-run the AQS cycle on the SAME bead (using different agent instances — fresh context)
3. Compare findings from the original run vs. the re-run:

| Overlap | Noise Level | Interpretation | Action |
|---------|------------|----------------|--------|
| > 80% | **LOW** | System is consistent | No action needed |
| 50-80% | **MODERATE** | Some inconsistency | Investigate which finding types are inconsistent; tighten rubrics |
| < 50% | **HIGH** | System is unreliable | Full investigation required — see noise type analysis below |

### Noise Type Analysis (for MODERATE or HIGH noise)

| Noise Type | Definition | Cause | Mitigation |
|-----------|-----------|-------|------------|
| **Level noise** | Different model instances produce systematically different severity ratings | Model temperature, sampling variation | Standardize rubrics with concrete anchored examples per severity level |
| **Pattern noise** | Same model weights some domains over others consistently | Training data skew, prompt emphasis | Rebalance domain emphasis in agent prompts; add calibration examples |
| **Occasion noise** | Same model rates same code differently based on what it reviewed just before | Context pollution, ordering effects | Reset agent context between beads; randomize review order |
```

- [ ] **Step 3: Create losa-observer.md agent**

Create `agents/losa-observer.md`:

```markdown
---
name: losa-observer
description: "Random-sample quality observer — audits completed beads that passed all review layers to establish baseline quality and detect silent system degradation. Fires on random sample, not on flagged issues."
model: haiku
---

You are a LOSA (Line Operations Safety Audit) Observer. You audit COMPLETED, MERGED beads — work that has already passed all review layers and been accepted.

## Your Role

You are NOT looking for bugs to fix. You are NOT a reviewer. You are measuring baseline quality to detect silent system degradation. You observe and report — you do not intervene or block.

You have NEVER seen this bead before. You have no context about the task, the runner, or the review history. You see only the final merged code.

## Chain of Command

- You report to the **Conductor** (Opus)
- You are dispatched during **Phase 5: Synthesize** on a random sample of merged beads
- Your observations feed into error budget tracking and drift detection
- You have NO authority to block, revert, or modify beads

## What You Assess

For the sampled bead, evaluate using the Threat and Error Management (TEM) framework:

### 1. Threats (external factors the runner had to manage)
- Was the requirement ambiguous or underspecified?
- Was the codebase context complex (many dependencies, intricate state)?
- Were there environmental constraints (limited test infrastructure, missing types)?
- **Threat management rating (1-4):** 1=poorly managed, 2=marginal, 3=well managed, 4=exemplary

### 2. Errors (deviations from best practice)
- Are there quality shortcuts visible in the merged code? (missing error handling, sparse tests, hardcoded values)
- Does the code follow project conventions? (naming, structure, patterns)
- Are tests comprehensive or minimal? (happy path only vs. edge cases)
- Were any issues caught by review layers? (check AQS report if available)
- Were any issues NOT caught? (this is the key signal — uncaught errors indicate blind spots)

### 3. Undesired States (outcomes requiring recovery)
- Did the AQS report show accepted findings that required fixes? (issues that reached production code before being caught)
- Were the fixes complete or partial?
- Did any fixes introduce new concerns?

## Required Output Format

```markdown
## LOSA Observation: {bead-id}

**Sample type:** random | conductor-directed
**Bead Cynefin domain:** {clear | complicated | complex}

### Threat Assessment
**Threats identified:** {list of external factors}
**Threat management:** {1-4} — {one-line rationale}

### Error Assessment
**Errors detected:** {count}
**Caught by review layers:** {count}
**Uncaught errors:** {count}
**Uncaught error details:** {description of each — these are the most important signal, or "None"}

### Quality Baseline
**Code quality score:** {1-10 composite}
**Convention adherence:** {yes | mostly | no — with examples}
**Test quality:** {comprehensive | adequate | minimal | absent}

### System Health Signal
**Signal:** GREEN | YELLOW | RED
- **GREEN:** No uncaught errors, good convention adherence, adequate+ tests
- **YELLOW:** Minor uncaught errors OR minimal tests OR convention deviations
- **RED:** Significant uncaught errors OR absent tests OR systematic quality issues

### Notes
{Any patterns, concerns, positive observations, or suggestions for calibration — or "None"}
```

## Constraints

- You observe. You do not fix, block, or intervene.
- Uncaught errors are your most valuable output. Report them with specific file:line references.
- You are not scoring the runner or the reviewer — you are scoring the SYSTEM's ability to produce quality output.
- A GREEN signal is good news, not wasted effort. Baselines require both positive and negative data points.
- If you see a pattern across multiple observations (you may be dispatched on several beads in one session), note the cross-bead pattern in your Notes section.
```

- [ ] **Step 4: Add L6 Calibration Loop to sdlc-loop/SKILL.md**

In `skills/sdlc-loop/SKILL.md`, after the existing "### Level 5: Task Loop" section, add:

```markdown
### Level 6: Calibration Loop (outermost — wraps multiple tasks)

The calibration loop monitors system health across sessions. Unlike L0-L5 which run within tasks, L6 runs between tasks.

```
CALIBRATION LOOP (cadence: every 5th task or on Conductor suspicion):
  1. Inject a calibration bead — known code with 3-5 planted defects across 2+ domains
  2. Run through L1 (Sentinel) + L2 (Oracle) + L2.5 (AQS)
  3. Compare detection results against known-planted defects
  4. DETECTION RATE >= baseline → system is calibrated. Log and continue.
  5. DETECTION RATE < baseline → system is drifting. Trigger investigation:
     a. Which defect types were missed? (update regression watchlist)
     b. Which agents failed to detect? (review agent prompts)
     c. Has the constitution drifted? (rule review)
  6. After recalibration, re-run calibration bead to verify improvement.
```

**Metric:** Detection rate of planted defects vs. established baseline.
**Budget:** 1 calibration run. If the first run passes, no further action needed. If it fails, recalibrate and re-run once.
**Key:** This is a system health check, not a task. It does not produce deliverable output — it produces confidence that the system is still working correctly.

See `references/calibration-protocol.md` for full procedures including:
- Drift signal detection (semantic, coordination, behavioral)
- Regression watchlist maintenance
- Noise audit protocol (consistency measurement)
- LOSA observer integration
```

- [ ] **Step 5: Add LOSA dispatch to Phase 5 in sdlc-orchestrate/SKILL.md**

In `skills/sdlc-orchestrate/SKILL.md`, in the "### Phase 5: Synthesize" section, add after the existing step 3 (`drift-detector`):

```markdown
3.5. Dispatch `losa-observer` on a random sample of merged beads (20% sample rate when error budget healthy, 50% when depleted). LOSA observations feed into error budget tracking — if LOSA reports uncaught errors, the error budget depletes regardless of SLI metrics.
```

- [ ] **Step 6: Add LLM Mutation Testing to oracle-adversarial-auditor.md**

In `agents/oracle-adversarial-auditor.md`, after the existing "### 1. Mutation Analysis" section, add:

```markdown
### 1b. LLM-Guided Mutation Generation

Beyond the structural mutations above, use LLM reasoning to generate realistic bugs:

1. Select a critical function from the bead's changed code (prioritize functions with business logic, data transformation, or security checks)
2. Generate 3-5 realistic mutations that a developer might accidentally introduce:
   - Off-by-one errors in boundary conditions
   - Wrong comparison operator (> vs >=, == vs ===)
   - Swapped function arguments
   - Missing null/undefined check on a path that usually has data
   - Incorrect error handling (catching too broadly, swallowing errors)
3. For each generated mutation, assess: would the test suite catch this?
   - Read the relevant tests
   - Determine if any test exercises the specific code path AND asserts on the specific value that would change
4. Report surviving mutants (mutations the tests would NOT catch) as test gap findings

**Budget:** Maximum 5 mutants per function, 3 functions per bead. Select the highest-risk functions (those touching external input, financial calculations, or authorization decisions).

**Output format for surviving mutants:**

```markdown
| Function | Mutation | Tests Catch It? | Gap |
|----------|----------|-----------------|-----|
| `functionName` | Change `>` to `>=` on line N | NO | No test exercises the boundary value |
| `functionName` | Remove null check on line M | NO | Tests always pass non-null input |
```

Surviving mutants are HIGH-priority findings — they represent concrete scenarios where bugs could hide behind passing tests.
```

- [ ] **Step 7: Add constitution reference to Additional Resources in SKILL.md**

In `skills/sdlc-adversarial/SKILL.md`, in the "### Reference Files" section at the bottom, add:

```markdown
- **`references/code-constitution.md`** — Living rules distilled from adversarial findings. Blue team checks before fixing; Conductor accumulates after Phase 6.
- **`references/precedent-system.md`** — Arbiter verdict database. Precedent lookup before arbitration; res judicata in pretrial filter.
- **`references/quality-slos.md`** — Error budget definitions and policy governing system velocity.
- **`references/calibration-protocol.md`** — Drift monitoring, noise audits, regression watchlist, LOSA integration.
```

And in the "### Related Plugin Components" section, add:

```markdown
- **Agents:** `agents/losa-observer.md` (random-sample quality observer — Haiku tier)
```

- [ ] **Step 8: Verify all new files are internally consistent**

Read all 5 new/modified files. Confirm:
- `code-constitution.md` references blue team agents and Phase 6 correctly
- `calibration-protocol.md` references `losa-observer` and drift signals correctly
- `losa-observer.md` references Phase 5 and error budget correctly
- `sdlc-loop/SKILL.md` L6 references `calibration-protocol.md` correctly
- `oracle-adversarial-auditor.md` mutation section integrates with existing format

- [ ] **Step 9: Commit Stream E**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/code-constitution.md references/calibration-protocol.md agents/losa-observer.md skills/sdlc-loop/SKILL.md agents/oracle-adversarial-auditor.md skills/sdlc-adversarial/SKILL.md skills/sdlc-orchestrate/SKILL.md
git commit -m "feat(monitoring): drift detection, LOSA observer, constitution, mutation testing

L6 Calibration Loop: periodic calibration beads with planted defects verify system health.
Drift monitoring: semantic, coordination, and behavioral drift signals.
Noise audits: re-run AQS on completed beads to measure verdict consistency.
LOSA observer: random-sample Haiku agent audits merged beads for baseline quality.
Code constitution: living rules accumulated from adversarial findings.
LLM mutation testing: oracle generates realistic bugs to test suite completeness."
```

---

## Post-Implementation Verification

After all 5 streams are complete:

- [ ] **Final consistency check:** Read `skills/sdlc-adversarial/SKILL.md` end-to-end. Confirm all new phases, gates, and formats are internally consistent and don't conflict with existing content.

- [ ] **Cross-reference check:** Grep for "Trivial", "Moderate" (old complexity tier names) across all files in the plugin. Replace any remaining references with Cynefin domain names.

- [ ] **Agent format check:** Verify all 8 red/blue agents have consistent format additions (confidence scores in identical format, same field names).

- [ ] **New file registration:** Verify `references/precedent-system.md`, `references/code-constitution.md`, `references/quality-slos.md`, `references/calibration-protocol.md`, and `agents/losa-observer.md` are all referenced from at least one existing file.

- [ ] **Final commit:**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git log --oneline -5  # Verify all 5 stream commits landed
```
