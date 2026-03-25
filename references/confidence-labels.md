# Confidence Labels

Every substantive claim in wave artifacts must carry one of the four labels below. Labels communicate epistemic status clearly to all agents and human reviewers.

---

## The Four Labels

### Verified
Confirmed by evidence — tests pass, logs show, diff proves.

Use when you have direct, reproducible proof that is observable in the current context. A claim is Verified only when another agent or person could independently reproduce the same evidence and reach the same conclusion.

### Likely
Strong reasoning supports this, but it has not been independently confirmed.

Use when logic is sound — the chain of inference is valid and well-grounded — but no test, log, or diff backs it up in this context. The claim could be falsified by investigation.

### Assumed
Believed true based on convention, documentation, or past experience, but not checked in this context.

Use when you haven't looked but expect it to be true. Common for background facts, environmental conditions, or architectural properties that are standard but unverified here.

### Unknown
No basis for judgment.

Use when you genuinely don't know and have no reliable basis to estimate. This is not a failure — naming unknowns is essential for honest handoffs.

---

## Usage Rules

1. **Every substantive claim in wave artifacts must carry one of these labels.** Unlabeled claims will be treated as Assumed at review.

2. **Never present Likely, Assumed, or Unknown as Verified.** Upgrade requires evidence, not argument.

3. **When in doubt, use the lower confidence label.** It is safer to claim Assumed and be upgraded than to claim Verified and be contradicted.

4. **Confidence can be upgraded after evidence is collected, never before.** An agent may note "this will become Verified once tests pass" but must not apply Verified until that condition is met.

5. **Unknown is not a placeholder — it is a signal.** An open Unknown at a gate is a gate risk. Name it, assess its impact, and decide whether to accept, resolve, or escalate it.

---

## Label Quick Reference

| Label    | Evidence Required | When to Use |
|----------|-------------------|-------------|
| Verified | Yes — direct, reproducible | Tests passed, logs confirm, diff proves |
| Likely   | No — strong inference only | Sound reasoning, no independent confirmation |
| Assumed  | No — convention/docs/experience | Haven't checked, expect it to be true |
| Unknown  | N/A — no basis exists | Genuinely don't know |
