# Standards Checklist

Curated checks from industry standards, organized by enforcement domain. Maintained by `standards-curator` agent. Each check maps to a specific standard, CWE where applicable, and the SDLC-OS agent that enforces it.

**Standards library:** `/Users/q/LAB/Research/Standards/`
**Last refreshed:** 2026-03-28

---

## Security Checks

Source: OWASP Top 10 Web, OWASP API Security, OWASP LLM Top 10, SANS Top 25, CWE

| ID | Check | Standard | CWE | Enforced By | Severity |
|----|-------|----------|-----|-------------|----------|
| SEC-001 | No SQL/NoSQL injection vectors (parameterized queries only) | OWASP A03:2021 | CWE-89 | red-security | CRITICAL |
| SEC-002 | No XSS vectors (output encoding, CSP) | OWASP A03:2021 | CWE-79 | red-security | CRITICAL |
| SEC-003 | No hardcoded credentials, API keys, or secrets | OWASP A07:2021 | CWE-798 | red-security, safety-constraints-guardian | CRITICAL |
| SEC-004 | No path traversal (validate and sanitize file paths) | OWASP A01:2021 | CWE-22 | red-security | HIGH |
| SEC-005 | No insecure deserialization | OWASP A08:2021 | CWE-502 | red-security | HIGH |
| SEC-006 | Authentication on all protected endpoints | OWASP A07:2021 | CWE-306 | red-security | CRITICAL |
| SEC-007 | Authorization checks (RBAC/ABAC) on all state-changing operations | OWASP A01:2021 | CWE-862 | red-security | CRITICAL |
| SEC-008 | Input validation at system boundaries | OWASP A03:2021 | CWE-20 | red-security | HIGH |
| SEC-009 | Cryptographic algorithms current (no MD5, SHA-1 for security) | OWASP A02:2021 | CWE-327 | red-security | HIGH |
| SEC-010 | Error messages do not expose internal details | OWASP A09:2021 | CWE-209 | red-security | MEDIUM |

### LLM-Specific Security (Meta)

Source: OWASP LLM Top 10 2025

| ID | Check | OWASP LLM | Enforced By | Severity |
|----|-------|-----------|-------------|----------|
| LLM-001 | Agent prompts delimit instructions from external content | LLM01 | llm-self-security | HIGH |
| LLM-002 | Agent outputs treated as untrusted by downstream consumers | LLM05 | llm-self-security | HIGH |
| LLM-003 | Agents operate within declared scope (least privilege) | LLM06 | llm-self-security | HIGH |
| LLM-004 | Loop budgets enforced, no unbounded agent dispatch | LLM10 | llm-self-security | HIGH |
| LLM-005 | Cross-agent independence maintained (anti-anchoring) | LLM06 | llm-self-security | MEDIUM |
| LLM-006 | System prompt content not leaked in agent output | LLM07 | llm-self-security | MEDIUM |

---

## Reliability Checks

Source: CISQ Reliability (ISO/IEC 5055), SRE

| ID | Check | Standard | CWE | Enforced By | Severity |
|----|-------|----------|-----|-------------|----------|
| REL-001 | No null pointer dereferences without guards | CISQ Reliability | CWE-476 | drift-detector | HIGH |
| REL-002 | Return values checked (no silent failures) | CISQ Reliability | CWE-252 | drift-detector | HIGH |
| REL-003 | Resources released after use (no leaks) | CISQ Reliability | CWE-404 | drift-detector | HIGH |
| REL-004 | No empty catch blocks (exceptions handled or re-thrown) | CISQ Reliability | CWE-391 | drift-detector | MEDIUM |
| REL-005 | No unreachable code / dead code paths | CISQ Reliability | CWE-561 | simplicity-auditor | MEDIUM |
| REL-006 | Loop termination conditions present | CISQ Reliability | CWE-835 | drift-detector | HIGH |
| REL-007 | Error boundaries at system edges | SRE | — | error-hardener | HIGH |
| REL-008 | Graceful degradation paths for external dependencies | SRE, Chaos Engineering | — | error-hardener | MEDIUM |

---

## Performance Checks

Source: CISQ Performance Efficiency, SRE, Observability Methods

| ID | Check | Standard | CWE | Enforced By | Severity |
|----|-------|----------|-----|-------------|----------|
| PERF-001 | No database queries inside loops (N+1 pattern) | CISQ Performance | CWE-1060 | drift-detector | HIGH |
| PERF-002 | No expensive I/O operations inside tight loops | CISQ Performance | CWE-1050 | drift-detector | HIGH |
| PERF-003 | Pagination for unbounded query results | CISQ Performance | CWE-1049 | drift-detector | MEDIUM |
| PERF-004 | String concatenation in loops uses builder/buffer | CISQ Performance | CWE-1046 | drift-detector | LOW |
| PERF-005 | Async operations not blocking event loops | CISQ Performance | — | drift-detector | HIGH |

---

## Maintainability Checks

Source: CISQ Maintainability, SOLID, Clean Architecture

| ID | Check | Standard | CWE | Enforced By | Severity |
|----|-------|----------|-----|-------------|----------|
| MAINT-001 | Cyclomatic complexity <= 15 per function | CISQ, quality-slos | CWE-1121 | simplicity-auditor | BLOCKING (per SLO) |
| MAINT-002 | No circular dependencies | CISQ | CWE-1047 | drift-detector | BLOCKING |
| MAINT-003 | No God classes (> 500 lines or > 20 methods) | CISQ | CWE-1080 | simplicity-auditor | WARNING |
| MAINT-004 | No duplicated logic blocks (3+ near-identical) | CISQ, DRY | CWE-1041 | drift-detector, simplicity-auditor | WARNING |
| MAINT-005 | Single Responsibility (one reason to change per module) | SOLID | — | drift-detector | MEDIUM |
| MAINT-006 | Dependency Inversion (depend on abstractions at boundaries) | SOLID, Clean Architecture | — | drift-detector | MEDIUM |
| MAINT-007 | Architectural layer boundaries respected | Clean Architecture | CWE-1101 | drift-detector | HIGH |

---

## Testing Checks

Source: Testing Standards (Test Pyramid, ISTQB, Mutation Testing)

| ID | Check | Standard | Enforced By | Severity |
|----|-------|----------|-------------|----------|
| TEST-001 | Test coverage does not decrease (delta >= 0) | quality-slos | oracle-test-integrity | BLOCKING (per SLO) |
| TEST-002 | No vacuous assertions (expect(true).toBe(true)) | VORP | oracle-test-integrity | BLOCKING |
| TEST-003 | Edge cases tested (boundary values, empty inputs, null) | ISTQB BVA | oracle-test-integrity | HIGH |
| TEST-004 | Error paths tested (not just happy path) | ISTQB | oracle-behavioral-prover | HIGH |
| TEST-005 | Integration tests for component boundaries | Test Pyramid | oracle-behavioral-prover | MEDIUM |
| TEST-006 | Tests are deterministic (no flaky tests) | Testing Standards | oracle-behavioral-prover | HIGH |

---

## Observability Checks

Source: Observability Methods (Golden Signals, RED, USE), SRE

| ID | Check | Standard | Enforced By | Severity |
|----|-------|----------|-------------|----------|
| OBS-001 | Structured logging with correlation IDs | Observability Methods | observability-engineer | HIGH |
| OBS-002 | Error logging includes context (not just message) | Observability Methods | observability-engineer | MEDIUM |
| OBS-003 | External calls instrumented with timing | SRE, RED method | observability-engineer | MEDIUM |
| OBS-004 | Health check endpoints for services | SRE | observability-engineer | HIGH |

---

## How to Use This Checklist

### For drift-detector (L1 — runtime)

Consult REL-*, PERF-*, and MAINT-002/005/006/007 during post-submission analysis. Include check IDs in findings for traceability. See `agents/drift-detector.md` "Standards-Mapped Checks" section.

### For red-security (AQS — runtime)

Use SEC-001 through SEC-010 as CWE-mapped attack vector targets during the TARGET step. Include check IDs and CWE numbers in findings. See `agents/red-security.md` TARGET section.

### For safety-constraints-guardian (L1 — runtime)

Universal constraints SC-001 through SC-005 are backed by SEC-003 through SEC-010 and REL-007/008. Standards-derived additions from Evolve use `STD-NNN` identifiers. See `agents/safety-constraints-guardian.md` Constraint Registry.

### For llm-self-security (Synthesize — runtime)

LLM-001 through LLM-006 are the meta-security checks. See `agents/llm-self-security.md`.

### For standards-curator (Evolve — curation)

Compare this checklist against the full Standards library at `/Users/q/LAB/Research/Standards/`. Propose additions when new standards or versions are released.

### For the Conductor (task planning)

Read the project-specific standards profile at `docs/sdlc/active/{task-id}/standards-profile.md` (produced by standards-curator during Scout) to determine which sections apply. Reference the profile path in runner context packets.

---

## Applicability Matrix

| Check Domain | All Projects | Web Apps | APIs | Libraries | CLI Tools | Multi-Agent |
|---|---|---|---|---|---|---|
| SEC-001 to SEC-010 | Partial | Full | Full | Partial | Partial | Partial |
| LLM-001 to LLM-006 | — | — | — | — | — | Full |
| REL-001 to REL-008 | Full | Full | Full | Full | Full | Full |
| PERF-001 to PERF-005 | Partial | Full | Full | Partial | Partial | Partial |
| MAINT-001 to MAINT-007 | Full | Full | Full | Full | Full | Full |
| TEST-001 to TEST-006 | Full | Full | Full | Full | Full | Full |
| OBS-001 to OBS-004 | Partial | Full | Full | — | — | Partial |
