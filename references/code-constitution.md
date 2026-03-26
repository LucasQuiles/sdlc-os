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
