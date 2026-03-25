# Handoff Contract

Every wave transition in the SDLC OS pipeline must use this contract template. A handoff is not a status update — it is a structured transfer of accountability. The receiving wave must be able to begin work solely from the handoff document without asking follow-up questions. Vague, optimistic, or incomplete handoffs are rejected by Haiku before the next wave may begin.

The handoff separates four categories of knowledge that must never be merged: what was verified (evidence exists), what was intended (implemented but not confirmed), what was assumed (carried forward without verification), and what remains uncertain (known unknowns). Conflating these categories is the most common source of downstream defects.

---

## Handoff Template

```markdown
## Handoff: Wave N → Wave N+1

**Wave:** [name of the completing wave]
**Objective:** [what this wave aimed to accomplish — one sentence]
**Inputs consumed:** [list of prior artifacts used as inputs, with file paths]
**Work performed:** [factual summary of what was done — no editorializing]
**Artifact produced:** [file path of the artifact this wave emits]
**Evidence collected:** [list of specific findings, test results, or observations — cite sources]
**Open questions:** [unresolved items that the next wave must be aware of — if none, state "none"]
**Risks / caveats:** [items that could affect the next wave, each labeled with a confidence class]
**Adversarial quality:** [AQS engagement summary — domains tested, findings by status (accepted/rebutted/disputed with verdicts), hardening changes applied, residual risk. If AQS was skipped, state "Skipped — trivial complexity"]
**Confidence:** [Verified | Likely | Assumed | Unknown — one label per line item in Risks/caveats]
**Next action for:** [role] — [specific action the next wave or party must take]
```

---

## Confidence Labels

Every risk and caveat entry must carry one of the following labels:

- **Verified** — directly observed evidence supports this claim (file read, test run, output inspected)
- **Likely** — strong indirect evidence, consistent with observed behavior, but not directly confirmed
- **Assumed** — no supporting evidence; carried forward because it was not contradicted
- **Unknown** — the state of this item cannot be determined from available information

When an entry is marked Assumed or Unknown, the receiving wave must treat it as an active risk, not background noise.

---

## Validation Rules

The following rules are enforced by `haiku-handoff.md` before any wave transition is approved. A handoff that violates any rule is returned to the sending wave for revision.

### Rule 1: Reject Minimal Handoffs

A handoff is rejected if any field contains only a phrase equivalent to the following, with no supporting detail:

- "done"
- "looks good"
- "implemented"
- "fixed"
- "should work"
- "completed"
- "no issues"
- "all good"

These phrases are not findings. They are absences of information dressed as conclusions.

### Rule 2: Separate the Four Knowledge Categories

Every handoff must distinguish:

1. **Verified results** — outcomes confirmed by direct evidence (test output, file inspection, observed behavior). Must cite the evidence.
2. **Intended behavior** — what the implementation was designed to do, but has not been independently confirmed.
3. **Assumptions** — beliefs carried forward from prior waves or introduced during this wave without verification.
4. **Unresolved uncertainty** — items where the state is genuinely unknown and could affect the next wave.

Merging any two of these categories is a validation failure. Calling something "verified" when it is "intended" is a specific failure mode that Haiku is trained to catch.

### Rule 3: Minimum Quality Standard

Every handoff must answer all four of the following questions. If any question cannot be answered, the handoff must explicitly state why and what would be needed to answer it.

1. **What was attempted?** — The work performed, stated factually.
2. **What was found or changed?** — Specific files, functions, behaviors, or test results. No summaries without detail.
3. **How do we know?** — The evidence. If there is no evidence, this must be stated explicitly (and labeled Assumed or Unknown).
4. **What's uncertain?** — Open questions, unverified assumptions, and known gaps.
5. **What happens next?** — A specific action for a named party. Not "the next wave should review this" — name the wave, the agent, and the action.

### Rule 4: Evidence Must Be Citable

Claims in the "Evidence collected" field must reference a specific source: a file path, a test name and result, an observed output, or a direct quote from a prior artifact. General statements ("the tests pass") without specific test names and results are not evidence.

### Rule 5: Next Action Must Name a Party and an Action

The "Next action for" field must name:
- A specific role or agent (e.g., "sonnet-designer", "Wave 4", "user")
- A specific action (e.g., "evaluate Option B against the updated constraint from Wave 3 discovery, section: dependency deviations")

Generic instructions ("proceed with implementation", "review the findings") are rejected.

---

## Example: Compliant Handoff

```markdown
## Handoff: Wave 3 → Wave 4

**Wave:** Discover
**Objective:** Map all files, dependencies, and architecture relevant to the authentication module refactor.
**Inputs consumed:** `wave-02-mission-brief.md` (scope: auth module, constraints: must not change public API)
**Work performed:** Read 14 files in `src/auth/`, traced call graph from `AuthController.login()` through `TokenService` and `UserRepository`. Inventoried 3 external dependencies. Ran `npm ls` to confirm installed versions.
**Artifact produced:** `wave-03-discovery.md`
**Evidence collected:**
  - `src/auth/TokenService.ts` line 47: uses `jsonwebtoken@8.5.1` — Verified (read directly)
  - `src/auth/UserRepository.ts`: no pagination on `findAll()` — Verified (read directly)
  - `package.json` declares `jsonwebtoken: ^8.5.1` — Verified (read directly)
  - Session storage mechanism: uses Redis via `connect-redis` — Verified (read directly)
  - Test coverage for `TokenService`: 2 unit tests, neither covers token expiry edge case — Verified (read test files)
**Open questions:**
  - Does `AuthController` have downstream consumers outside `src/auth/`? Search returned 3 references in `src/api/` but their behavior under refactor is untested. (non-blocking but noted)
**Risks / caveats:**
  - `jsonwebtoken@8.5.1` has a known CVE patched in v9.0.0; upgrade may require API changes — Likely (CVE confirmed, API impact assumed)
  - Redis session store is configured via environment variable not present in `.env.example` — Assumed (not verified in all environments)
**Confidence:** Likely (CVE item), Assumed (Redis config item)
**Adversarial quality:** AQS engaged — security (HIGH), usability (MED). 3 findings: 2 accepted (parameterized auth query, stripped stack trace from error response), 1 rebutted (CORS config handled by middleware — verified at `src/middleware/cors.ts:12`). No residual risk.
**Next action for:** sonnet-designer — evaluate both refactor options against the `jsonwebtoken` version constraint; Option A (in-place refactor) may not be viable if v9 upgrade is required. See `wave-03-discovery.md` section: Dependency Deviations.
```

---

## Example: Non-Compliant Handoff (Rejected)

```markdown
## Handoff: Wave 3 → Wave 4

**Wave:** Discover
**Objective:** Explore the auth module.
**Inputs consumed:** mission brief
**Work performed:** Looked at the auth files. Everything seems straightforward.
**Artifact produced:** wave-03-discovery.md
**Evidence collected:** The code looks clean and well-organized.
**Open questions:** none
**Risks / caveats:** Should be fine.
**Confidence:** Verified
**Next action for:** Design wave — implement the solution.
```

Rejection reasons:
- "Everything seems straightforward" is not a finding — Assumed, not Verified
- "The code looks clean" is not evidence — no specific file, line, or observation cited
- "Should be fine" is not a risk assessment — no confidence label, no specific item
- "Confidence: Verified" contradicts the absence of any cited evidence
- "Implement the solution" is not a specific next action — no option, no constraint, no reference
