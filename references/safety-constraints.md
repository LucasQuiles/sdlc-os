# Safety Constraints Registry

System-wide invariants maintained by safety-constraints-guardian.
Violations are BLOCKING during L1 sentinel.

---

## Universal Constraints (apply to all beads)

- **SC-001:** Auth checks must precede data access
- **SC-002:** All external calls must have explicit timeouts
- **SC-003:** User input must be validated before reaching business logic
- **SC-004:** Error handlers must not swallow errors silently
- **SC-005:** Secrets must not appear in logs or error messages

---

## Project-Specific Constraints (discovered during Scout)

{populated per project}

---

## Constraint Lifecycle

- **ACTIVE:** enforced during L1
- **SUSPENDED:** temporarily disabled with documented reason
- **RETIRED:** no longer applicable, with retirement rationale

| Constraint | Status | Notes |
|---|---|---|
| SC-001 | ACTIVE | LLM-reasoning check — L1 sentinel only; probabilistic on L0-only beads |
| SC-002 | ACTIVE | LLM-reasoning check — L1 sentinel only; probabilistic on L0-only beads |
| SC-003 | ACTIVE | LLM-reasoning check — L1 sentinel only; probabilistic on L0-only beads |
| SC-004 | ACTIVE | Deterministic check — also enforced via validate-safety-constraints.sh hook (advisory) |
| SC-005 | ACTIVE | Deterministic check — also enforced via validate-safety-constraints.sh hook (advisory) |

---

## Enforcement Notes

**Deterministic vs LLM-reasoning split:**

SC-004 and SC-005 can be expressed as grep/AST patterns and are enforced two ways:
1. `validate-safety-constraints.sh` hook — PostToolUse advisory on all source file writes (exit 0 with stderr warning; always-on, always-advisory)
2. safety-constraints-guardian during L1 sentinel — blocking enforcement with full bead context

SC-001, SC-002, SC-003 require semantic analysis and are only enforced during L1 by the safety-constraints-guardian. For L0-only beads (CLEAR + not security_sensitive, healthy budget), these constraints are checked post-merge by the LOSA observer's sampling — probabilistically enforced, not universally enforced. This gap is accepted in exchange for speed on L0-only beads.

**Guardian independence:** The safety-constraints-guardian runs its own checks independently during L1. It does NOT consume hook output — it re-runs the same deterministic checks directly on the bead's changed files plus adds LLM-reasoning checks. No transport-path dependency between hooks and agents.
