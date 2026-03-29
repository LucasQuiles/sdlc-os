# Duplicate Analysis — Agent Files

_Generated: 2026-03-27_
_Analyst: crossmodel-adversarial-review task_
_Scope: All 45 agent markdown files in `agents/`_
_Method: Full read of every agent; extraction of role, chain of command, output format, and constraints sections; cross-agent comparison_

---

## Executive Summary

Three distinct duplication problems were found across the 45 agents:

1. **Category 1 (Duplicated Instructions):** Seven instruction clusters appear in 3–14 agents with same intent, different wording. The highest-value targets for consolidation are the blue-team operating model (5 agents), the red-team attack operating model (4 agents), and the Duty of Candor + Constitution Compliance pair (5 blue agents each).

2. **Category 2 (Overlapping Roles):** Four agent pairs have substantial role overlap. Two pairs are HIGH confidence true redundancy candidates; two are MEDIUM confidence scope adjacency cases.

3. **Category 3 (Duplicated Output Formats):** Three output format families share near-identical table structures across multiple agents.

Total duplicate clusters: **14** (7 HIGH, 4 MEDIUM, 3 structural).

---

## Category 1: Duplicated Instructions

### DI-001 — "Only the Conductor changes bead status"

**Confidence: HIGH**

**Agents involved:**
- `crossmodel-supervisor.md` (Integrity Rules section): "Only Conductor changes bead status — never update bead status yourself"
- `crossmodel-triage.md` (Chain of Command + Constraints): "You never modify bead status" (×2 — stated in both sections)
- `safety-analyst.md` (implicit — all instructions route through Conductor)
- `losa-observer.md` (Constraints): "You have NO authority to block, revert, or modify beads"

**Quoted overlapping text:**
- `crossmodel-supervisor.md`: "Only the Conductor routes." and "Only Conductor changes bead status — never update bead status yourself"
- `crossmodel-triage.md`: "You never modify bead status" (Constraints, line 72) and "You never modify bead status" (Chain of Command, line 22)

**What's duplicated:** The constraint that routing and bead-status changes are reserved exclusively for the Conductor. Each agent in the cross-model pipeline restates this from scratch.

**Recommendation: CONSOLIDATE**
Move to a shared reference file (e.g., `references/conductor-authority.md`) containing canonical wording. Each agent can cite the reference rather than restate it. The intra-agent duplication in `crossmodel-triage.md` (stated in two different sections) should be resolved immediately regardless.

---

### DI-002 — Blue Team Duty of Candor

**Confidence: HIGH**

**Agents involved (all 5 blue defenders):**
- `blue-functionality.md` (Constraints): "Duty of candor: When generating a fix or rebuttal, proactively disclose areas of uncertainty you encountered. If you noticed something suspicious outside the scope of the current finding, flag it as a disclosure note. This is not a finding — it is an honest signal to the Conductor."
- `blue-resilience.md` (Constraints): Identical text
- `blue-security.md` (Constraints): Identical text
- `blue-usability.md` (Constraints): Identical text
- `blue-reliability-engineering.md` (Constraints): "Duty of candor: Disclose areas of uncertainty. If you notice something suspicious outside the finding scope, flag it as a disclosure note." (slightly shortened but same intent)

**Quoted overlapping text (verbatim across 4 of 5):**
> "Duty of candor: When generating a fix or rebuttal, proactively disclose areas of uncertainty you encountered. If you noticed something suspicious outside the scope of the current finding, flag it as a disclosure note. This is not a finding — it is an honest signal to the Conductor."

**What's duplicated:** Word-for-word identical constraint across 4 agents; paraphrased in the 5th.

**Recommendation: CONSOLIDATE**
The five blue defenders share a common base operating model. A `blue-team-base.md` reference (or a shared constraints block cited in each agent) would eliminate this. This duplication is maintenance-risky: if the Duty of Candor definition evolves, all 5 files must be updated in sync.

---

### DI-003 — Blue Team Constitution Compliance Constraint

**Confidence: HIGH**

**Agents involved (all 5 blue defenders):**
- `blue-functionality.md`: "Constitution compliance: Before producing a fix, check `references/code-constitution.md` for applicable rules. Fixes must conform. If the fix cannot conform (rule conflicts with correct fix), flag the conflict to the Conductor."
- `blue-resilience.md`: Identical text
- `blue-security.md`: Identical text
- `blue-usability.md`: Identical text
- `blue-reliability-engineering.md`: "Constitution compliance: Check `references/code-constitution.md` for applicable rules. Fixes must conform." (shortened but identical intent)

**What's duplicated:** The same constitution-check gate before every fix, with identical escalation path.

**Recommendation: CONSOLIDATE**
Same reasoning as DI-002. This is a second word-for-word duplication across the same 5 agents. Both DI-002 and DI-003 together suggest the blue defender family needs a shared base that both constraints live in.

---

### DI-004 — Blue Team Output Format: "If accepted / rebutted / disputed" Triage Structure

**Confidence: HIGH**

**Agents involved (all 5 blue defenders):**
All five blue agents (`blue-functionality`, `blue-resilience`, `blue-security`, `blue-usability`, `blue-reliability-engineering`) define the same three-branch response structure:

```
## Response: {Finding ID}
**Action:** accepted | rebutted | disputed

### If accepted:
  [fields...]
### If rebutted:
  [fields...]
### If disputed:
  [fields...]
```

The top-level structure (Response heading, Action field, three branches, Confidence 0.0–1.0 field, Confidence rationale, Disclosure notes, Latent condition layer) is identical across all five. Only the domain-specific fields differ (e.g., "Pre-fix reproduction" in functionality vs. "Gap confirmed" in resilience).

**What's duplicated:** The entire scaffold of the blue-team output format — approximately 60–70% of the format content is identical across agents.

**Recommendation: CONSOLIDATE**
Define the base output format template once (in `references/blue-team-response-format.md` or the base agent spec). Each blue defender extends it with 3–5 domain-specific fields in the "accepted" branch. This also ensures the Latent Condition Layer selector (which appears in 4 of 5 blue defenders with the same layer list) stays consistent.

---

### DI-005 — Red Team ASSUMPTIONS + RECON + TARGET + FIRE + ASSESS + SHRINK + REPORT Operating Model

**Confidence: HIGH**

**Agents involved:**
- `red-functionality.md`
- `red-resilience.md`
- `red-security.md`
- `red-usability.md`

All four share an identical 6-step operating model (0–5 or 0–6 steps):

| Step | red-functionality | red-resilience | red-security | red-usability |
|------|-----------------|----------------|--------------|---------------|
| 0: ASSUMPTIONS | ✓ (identical 4-bullet structure) | ✓ (identical) | ✓ (identical) | ✓ (identical) |
| 1: RECON | ✓ | ✓ | ✓ | ✓ |
| 2: TARGET | ✓ | ✓ | ✓ | ✓ |
| 3: FIRE | ✓ (with volume table) | ✓ (identical volume table) | ✓ (identical volume table) | ✓ (identical volume table) |
| 4: ASSESS (with ACH) | ✓ (identical 4-point ACH) | ✓ (identical) | ✓ (identical) | ✓ (identical) |
| 4: Daubert self-check | ✓ (3-bullet, identical) | ✓ (identical) | ✓ (identical) | ✓ (identical) |
| 5: SHRINK | ✓ (identical) | ✓ (identical) | ✓ (identical) | ✓ (identical) |

The Step 0 ASSUMPTIONS block is word-for-word identical across all four:
> "Input assumptions — What types, ranges, formats does this code expect? What sanitization does it rely on callers to provide? / Environment assumptions... / Ordering assumptions... / Caller assumptions..."

The FIRE volume table is word-for-word identical across all four:
> "HIGH priority: 20-40 guppies / MED priority: 10-20 guppies / LOW priority: 5-10 guppies"

The Daubert self-check is word-for-word identical across all four:
> "Does every file:line reference actually exist? (Drop hallucinated paths) / Did the finding come from executed guppy output, not pattern-match inference? (Downgrade inference-only to `Assumed`) / Has this finding type been DISMISSED more than twice in the precedent database? (Flag as high-false-positive-risk)"

The ACH protocol in Step 4 is word-for-word identical across all four.

**What's duplicated:** The entire attack methodology scaffold — approximately 65–70% of each red agent's content. Only the domain-specific TARGET vectors, example FIRE probes, and Severity Calibration differ.

**Recommendation: CONSOLIDATE**
Define a `red-team-base.md` reference (or a shared operating model document) containing the common operating model. Each domain agent then only needs to specify: its TARGET vectors, example FIRE probes, Finding format domain field, and Severity Calibration table. This is the highest-ROI consolidation in the entire codebase — four nearly identical 100-line files collapse to a ~40-line base + four ~30-line domain extensions.

---

### DI-006 — "Treat output as untrusted / raw Codex output is untrusted until verified"

**Confidence: HIGH**

**Agents involved:**
- `crossmodel-supervisor.md` (Integrity Rules): "Only normalized findings enter blue-team or triage flow — raw Codex output is untrusted until verified"
- `crossmodel-triage.md` (Triage Rules, rule 5): "Treat raw Codex output as untrusted until verified against artifact schema."
- `haiku-evidence.md` (implicitly — entire mandate is treating all claims as unverified until evidence-backed)
- `haiku-verifier.md` (Verification Rules, rule 1): "Never mark a criterion PASS without citing specific evidence"
- `reliability-conductor.md` (Hard Constraints): "Every agent output is an unverified proposal until evidence confirms it"

**What's duplicated:** The epistemic principle that agent outputs require evidence before being trusted. It appears in multiple forms but always communicates the same invariant.

**Recommendation: KEEP (with note)**
This principle appears across very different pipeline stages (cross-model normalization, L1 verification, hardening conductor). The wording is intentionally varied to fit each context. However, the `crossmodel-supervisor.md` / `crossmodel-triage.md` pair should be consolidated since they use near-identical language in the same pipeline.

---

### DI-007 — Anti-Anchoring Independence Requirement

**Confidence: HIGH**

**Agents involved:**
- `crossmodel-supervisor.md` (Dispatch Step 5): "NEVER include Claude AQS findings — anti-anchoring requirement; Stage A workers must form independent judgments" and "NEVER include any review artifacts — Stage B must be fully independent"
- `crossmodel-supervisor.md` (Integrity Rules): "Stage A workers never see Claude AQS findings — anti-anchoring is non-negotiable"
- `llm-self-security.md` (Cross-Agent Scope Bleed): "Did any blue team agent receive information about red team attack strategy before producing its defense? (anti-anchoring violation)"
- `red-reliability-engineering.md` (Role): "Critical anti-anchoring rule (Kahneman): You receive the raw bead code and observability profile. You do NOT receive the Observability Engineer's or Error Hardener's self-assessment."
- `reliability-conductor.md` (Step 4): "NOT the Observability Engineer's or Error Hardener's self-assessment (Kahneman anti-anchoring)" and (Anti-Patterns): "Showing Blue Team self-assessment to Red Team (anchoring bias)"

**What's duplicated:** The Kahneman anti-anchoring rule — red agents must never receive prior review artifacts before forming independent judgments. Stated in both the dispatch protocol and the receiving agent's own instructions.

**Recommendation: KEEP (with note)**
Restating the anti-anchoring rule in both the dispatcher (`crossmodel-supervisor`, `reliability-conductor`) and the receiver (`red-reliability-engineering`) is intentional defense-in-depth — if either party forgets, the other catches it. This is a known safety-critical duplication. However, the intra-agent duplication within `crossmodel-supervisor.md` (stated in Step 5 and again in Integrity Rules) should be collapsed to one canonical location.

---

### DI-008 — Confidence Labeling: Verified / Likely / Assumed / Unknown

**Confidence: HIGH**

**Agents involved:**
- `guppy.md`: "Confidence: [Verified | Likely | Assumed]" (3-level scale)
- `haiku-evidence.md`: "Label all conclusions with a confidence class: Verified / Likely / Assumed / Unknown" (4-level scale)
- `haiku-verifier.md`: "Label every finding with a confidence class: Verified / Likely / Assumed / Unknown"
- `haiku-handoff.md`: "Confidence: [Verified | Likely | Assumed | Unknown]"
- `sonnet-investigator.md`: "Label every claim: Verified | Likely | Assumed | Unknown"
- `reuse-scout.md`: "Confidence: [Verified | Likely | Assumed]"
- All red agents: "Confidence: Verified | Likely | Assumed" + confidence score 0.0–1.0
- All blue agents: "Confidence: {0.0-1.0}" (numeric only, no label)
- `gap-analyst.md`: "Confidence: HIGH / MEDIUM / LOW" (different scale)

**What's duplicated:** The confidence labeling system appears across ~14 agents but with two variant scales (3-level vs. 4-level) and one entirely different scale in `gap-analyst.md`. This inconsistency is more of a standards drift problem than a duplication problem.

**Recommendation: CONSOLIDATE**
The 4-level scale (Verified / Likely / Assumed / Unknown) from `haiku-evidence.md` should be the canonical standard. `guppy.md` and `reuse-scout.md` use a 3-level scale that omits Unknown. `gap-analyst.md` uses a completely different scale (HIGH/MEDIUM/LOW). Establish one scale in `references/` and have all agents cite it. The red agents' numeric 0.0–1.0 score can coexist as a refinement within Verified/Likely/Assumed.

---

## Category 2: Overlapping Roles

### OR-001 — `drift-detector` vs `simplicity-auditor`

**Confidence: HIGH**

**Role descriptions:**
- `drift-detector`: "Detects DRY violations, architectural drift, invariant breakage, and separation-of-concern violations in runner output. Uses LSP call hierarchy + Pinecone semantic search."
- `simplicity-auditor`: "Computes a simplicity coefficient (problem complexity / solution complexity) and flags disproportionate code. Dispatched in the L1 Sentinel loop after runner submission."

**Overlapping scope:**
Both run in the L1 sentinel loop. Both examine runner output after submission. Both can flag over-engineering:
- `drift-detector` detects "Pattern Drift" including "Different error handling than established pattern"
- `simplicity-auditor` detects "Copy-paste amplification," "Over-abstraction," and "Factory wrapping single function"

Both use LSP tools and grep on the same files. Both produce BLOCKING/WARNING/NOTE severity findings.

**Where they diverge:**
- `drift-detector` focuses on architectural boundaries, DRY violations with a canonical source, and SSOT. It requires knowing what the *correct* source is.
- `simplicity-auditor` focuses on problem/solution proportionality — it does not need a canonical source, only the bead spec complexity score.
- `drift-detector` has a Pinecone semantic search step; `simplicity-auditor` does not.
- `convention-enforcer.md` explicitly names this boundary: "Duplicate logic (DRY): No — forward to drift-detector."

**Assessment:** The roles are distinct but neighboring. The `simplicity-auditor` anti-pattern "Copy-paste amplification: 3+ near-identical code blocks differing only in variable names — extract shared function" overlaps directly with `drift-detector`'s DRY violation detection. A runner could receive BLOCKING findings from both agents for the same code block under different names.

**Recommendation: KEEP, but add coordination rule**
Add to `simplicity-auditor`: "If you detect copy-paste amplification, forward to `drift-detector` rather than issuing a separate finding. `drift-detector` owns DRY violations." Mirror this boundary in `drift-detector`'s anti-patterns. This prevents double-penalizing runners.

---

### OR-002 — `llm-self-security` vs `safety-constraints-guardian`

**Confidence: MEDIUM**

**Role descriptions:**
- `llm-self-security`: "Audits the SDLC-OS workflow itself for prompt injection exposure, excessive agency, unbounded consumption, insecure output handling, and cross-agent scope bleed. Audits agents, hooks, commands, and orchestration."
- `safety-constraints-guardian`: "Maintains the Safety Constraints Registry — system-wide invariants that must hold across all beads. Validates bead outputs against constraints during L1 sentinel loop."

**Overlapping scope:**
- Both check security-related invariants
- Both can detect violations in the same bead output
- `llm-self-security` LLM06 (Excessive Agency) check: "Did any runner modify files in `agents/`, `hooks/`, `references/`, or `skills/` without explicit authorization?" — this is a scope-bleed check
- `safety-constraints-guardian` SC-001 through SC-005 cover auth, timeouts, input validation, error handling, secrets — these are OWASP-derived constraints that `llm-self-security` also audits (LLM01 prompt injection overlaps with SC-003/SC-005)

**Where they diverge:**
- `llm-self-security` audits the *system architecture* (agents, hooks, dispatch templates) — it is meta-security
- `safety-constraints-guardian` audits *user project code* changed by runners — it is object-level security
- `safety-constraints-guardian` is dispatched every bead (L1 loop); `llm-self-security` is dispatched during Synthesize and Evolve
- The two agents have different dispatch frequencies and different targets

**Assessment:** The overlap is real but the scope boundary is clear: one audits the system that runs beads, the other audits the code beads produce. The confusion arises because the description of `llm-self-security` could be read as covering user code security, which it explicitly does not: "You audit the SYSTEM, not the user's code. The red-security agent handles code security."

**Recommendation: KEEP, but strengthen the scope statement**
Add an explicit clarification to `llm-self-security`'s description that its scope is limited to the SDLC-OS system components (agents, hooks, commands, skills) and never extends to user project code. The current role description is clear but the description frontmatter could be more precise.

---

### OR-003 — `haiku-verifier` vs `convention-enforcer`

**Confidence: MEDIUM**

**Role descriptions:**
- `haiku-verifier`: "Acceptance Checker — confirm work meets stated success criteria. Regression Sentinel — check for side effects and breakage. Gate Guardian — validate readiness before wave transitions."
- `convention-enforcer`: "Convention compliance auditor — checks runner output against the project's Convention Map for naming violations, wrong file locations, styling drift, and structural inconsistencies."

**Overlapping scope:**
Both run after runner output and both can produce BLOCKING verdicts that prevent advancement. The `haiku-verifier` "Regressions Checked" section asks: "if a schema was changed, check all consumers" — which can overlap with `convention-enforcer`'s "Imports" and "Directory Structure" dimensions.

**Where they diverge:**
- `haiku-verifier` checks acceptance criteria and regressions (behavior)
- `convention-enforcer` checks naming, structure, and styling conventions (form)
- These are genuinely orthogonal: code can be conventionally correct but functionally wrong, or functionally correct but conventionally wrong.

**Assessment:** Low actual overlap. The two agents catch entirely different classes of defect. The only genuine overlap is that both can block the same bead — but this is correct behavior, not redundancy.

**Recommendation: KEEP**
The apparent overlap is superficial. No consolidation needed.

---

### OR-004 — `feature-finder` vs `gap-analyst` (Finder mode)

**Confidence: HIGH**

**Role descriptions:**
- `feature-finder`: "Codebase feature archaeologist — finds neglected, incomplete, unwired, undocumented, and abandoned feature work across code, structure, git history, and docs."
- `gap-analyst` (Finder mode): "Map what exists vs. what is needed before implementation begins. Every requirement must be classified so the team knows exactly which beads are needed."

**Overlapping scope:**
Both scan the codebase for missing or incomplete functionality. Both produce findings that feed into bead creation decisions. Both classify findings by completeness. The `feature-finder`'s signal categories (Code, Structural, Git, Documentation) and the `gap-analyst`'s scan process (workspaceSymbol, Grep, findReferences) overlap extensively.

**Where they diverge:**
- `feature-finder` discovers forgotten/abandoned work — it is archaeology (what was started but dropped)
- `gap-analyst` Finder mode maps requirements-to-implementation gaps — it is requirements tracing (what was promised but not built)
- `feature-finder` works from code signals (TODO, stubs, orphaned components) with no required requirements document
- `gap-analyst` requires a truth source (mission brief, external spec, or codebase inference) and classifies against requirements
- `feature-finder` writes to `docs/sdlc/feature-matrix.md`; `gap-analyst` produces a Finder Report

**Assessment:** The roles have different inputs (code signals vs. requirements) and different outputs (feature matrix vs. gap report), but a runner asked to "find what's incomplete in this codebase" would rationally use both. The dispatching question — "which one do I call?" — is not clearly answered by the system documentation.

**Recommendation: KEEP, but add dispatch guidance**
Add to both agents (or to the Conductor's dispatch protocol): `feature-finder` is dispatched when no requirements document exists and the goal is discovery-mode archaeology. `gap-analyst` Finder mode is dispatched when a requirements document exists and the goal is requirements traceability. Overlap is acceptable given different inputs; the dispatch trigger should be explicit.

---

## Category 3: Duplicated Output Formats

### OF-001 — Red Agent Finding Format

**Confidence: HIGH**

**Agents involved:**
- `red-functionality.md`, `red-resilience.md`, `red-security.md`, `red-usability.md`, `red-reliability-engineering.md`

All five use this near-identical finding scaffold:

```
## Finding: {ID}
**Domain:** [domain]
**Severity:** critical | high | medium | low
**Claim:** {One sentence}
**Minimal reproduction:** {specific scenario}
**Impact:** {what goes wrong}
**Evidence:** {file:line, traced path}
**Confidence:** Verified | Likely | Assumed
**Confidence score:** {0.0-1.0}
**Confidence rationale:** {what drives the score}
```

The only difference is the domain name and the exact wording of the "Minimal reproduction" label (e.g., "minimal reproduction" vs. "minimal failure scenario" vs. "minimal demonstration"). These are synonym variations, not structural differences.

**Recommendation: CONSOLIDATE**
Define one canonical finding format in `references/red-team-finding-format.md`. Each domain agent references it and specifies only its domain label. This ensures any future changes to the finding format (e.g., adding a "Standards ID" field) propagate automatically.

---

### OF-002 — Blue Agent Response Format (Latent Condition Layer Selector)

**Confidence: HIGH**

**Agents involved:**
- `blue-functionality.md`, `blue-resilience.md`, `blue-security.md`, `blue-usability.md`, `blue-reliability-engineering.md`

All five include this identical latent condition selector:

> "**Latent condition:** Which upstream layer should have caught this? (Select one: L0 Runner / L1 Sentinel / L2 Oracle / L2.5 AQS / L2.75 Hardening / Convention Map / Code Constitution / Safety Constraints / Hook-Guard / Other)"

This is word-for-word identical in 5 files.

**Recommendation: CONSOLIDATE**
This is the same layer taxonomy also used in `latent-condition-tracer.md`. The canonical list should live in one place (likely `references/layer-taxonomy.md` or inline in `latent-condition-tracer.md`) and be cited by the blue agents rather than repeated.

---

### OF-003 — Haiku Output Format Family (Evidence / Verify / Handoff)

**Confidence: MEDIUM**

**Agents involved:**
- `haiku-evidence.md` — Evidence Report format
- `haiku-verifier.md` — Verification Report format
- `haiku-handoff.md` — Handoff format

**Overlapping structure:**
All three haiku agents use a report-header block pattern:
```
## [Report Type]
**Wave:** [wave]
**Task ID:** [identifier]
**[Role]:** haiku-[role]
**[Scope/Inputs]:** [list]
```

All three require confidence labels on key items. All three have an explicit "Anti-Patterns" section with overlapping items (e.g., all three forbid "marking something correct without evidence").

**Where they diverge:**
The three reports serve different functions: Evidence captures artifacts, Verifier checks criteria, Handoff packages outputs. Their internal structures diverge significantly after the header block.

**Assessment:** The similarity is a family resemblance, not problematic duplication. The shared Anti-Patterns language ("Accepting a claim without tracing it to a specific, observable source" appears in all three) is intentional — these agents are designed as a coherent evidence-first triad.

**Recommendation: KEEP**
The overlap is intentional stylistic consistency. The anti-patterns are deliberately repeated to reinforce the same epistemic norms across three related agents.

---

## Consolidated Priority List

| ID | Description | Agents Affected | Recommendation | Priority |
|----|-------------|-----------------|----------------|----------|
| DI-005 | Red team full operating model (ASSUMPTIONS + RECON + TARGET + FIRE + ASSESS + SHRINK) | 4 red agents | CONSOLIDATE to red-team-base | HIGH |
| DI-004 | Blue team response format scaffold | 5 blue agents | CONSOLIDATE to blue-team-response-format | HIGH |
| DI-002 | Duty of Candor constraint | 5 blue agents | CONSOLIDATE to blue-team-base | HIGH |
| DI-003 | Constitution Compliance constraint | 5 blue agents | CONSOLIDATE to blue-team-base | HIGH |
| DI-008 | Confidence label scale inconsistency (3-level vs 4-level vs HIGH/MED/LOW) | ~14 agents | CONSOLIDATE canonical scale | HIGH |
| OF-001 | Red finding format | 5 red agents | CONSOLIDATE to references/red-team-finding-format.md | HIGH |
| OF-002 | Latent condition layer selector | 5 blue agents | CONSOLIDATE to references/layer-taxonomy.md | HIGH |
| DI-001 | "Only Conductor changes bead status" | 4 agents | CONSOLIDATE to references/conductor-authority.md | MEDIUM |
| DI-006 | "Treat output as untrusted" principle | crossmodel-supervisor + crossmodel-triage | CONSOLIDATE intra-pipeline pair | MEDIUM |
| DI-007 | Anti-anchoring rule stated in both dispatcher and receiver | 3 agents | KEEP (defense-in-depth) but collapse intra-supervisor duplicate | MEDIUM |
| OR-001 | drift-detector vs simplicity-auditor (copy-paste overlap) | 2 agents | KEEP + add coordination boundary rule | MEDIUM |
| OR-004 | feature-finder vs gap-analyst (Finder mode) | 2 agents | KEEP + add dispatch guidance | MEDIUM |
| OR-002 | llm-self-security vs safety-constraints-guardian | 2 agents | KEEP + strengthen scope statement | LOW |
| OF-003 | haiku evidence/verifier/handoff family | 3 agents | KEEP (intentional family design) | LOW |

---

## Implementation Notes

**Highest ROI change:** DI-005 (red team operating model) and DI-002+DI-003+DI-004 (blue team base). These 9 files together contain approximately 400 lines of duplicated content. A `red-team-base.md` reference + `blue-team-base.md` reference would reduce maintenance surface by ~60% for these agent families.

**Riskiest change:** DI-004 (blue team output format). The blue team response format is deeply embedded in the AQS pipeline parsing logic. Before consolidating, verify that downstream consumers (Conductor, arbiter, latent-condition-tracer) parse the format structurally rather than by text-matching specific phrasing. If format consolidation changes any field name or order, it must be tested against the full AQS cycle.

**Quick win (no risk):** DI-002 + DI-003 within `blue-reliability-engineering.md` can be aligned to match the exact wording of the other four blue agents immediately — the text is slightly shortened in that agent only, introducing a minor inconsistency.

**Quick win (no risk):** DI-001 intra-agent duplicate in `crossmodel-triage.md` — the phrase "You never modify bead status" appears in both the Chain of Command section and the Constraints section of the same file. Remove one occurrence.
