---
name: sdlc-fitness
description: "Architectural fitness function runner. Automated checks that validate DRY, SSOT, SoC, convention adherence, and structural health. Integrates with the loop system — BLOCKING scores trigger L1 corrections."
---

# Architectural Fitness Functions

Fitness functions are automated checks that validate architectural properties ([continuous-architecture.org](https://continuous-architecture.org/practices/fitness-functions/)). They run like tests but check structure, not behavior. When they fail, the architecture has drifted.

## Fitness Dimensions

| Dimension | What It Checks | Tools Used |
|-----------|---------------|------------|
| **DRY** | No duplicated logic across files | Pinecone semantic search, jscpd, grep |
| **SSOT** | Constants/config defined in one place | LSP workspaceSymbol, grep for literals |
| **SoC** | Each file has one concern | LSP documentSymbol, file path conventions |
| **Conventions** | Naming, structure, style match Convention Map + established patterns | convention-enforcer report + pattern matching against reuse-patterns.md |
| **Boundaries** | Import graph respects layers | LSP incomingCalls/outgoingCalls |
| **Coverage** | New code has tests | File existence checks, VORP audit |

## When to Run

| Trigger | Scope | Depth |
|---------|-------|-------|
| Per-bead (L1 sentinel loop) | Changed files only | Drift detector (quick) |
| Per-phase (after Execute) | All beads in phase | Full fitness report |
| On-demand (`/audit`) | User-specified scope | Full fitness report |

## How to Run

### Quick Check (per-bead)
Dispatch `drift-detector` (sonnet) + `convention-enforcer` (sonnet) with runner output. Drift-detector produces DRY/SSOT/SoC/Boundaries scores. Convention-enforcer produces Conventions score from Convention Map audit.

### Full Report (per-phase or on-demand)
1. Swarm guppies — one per fitness dimension per file group
2. Dispatch drift-detector for deep analysis on flagged areas
3. Aggregate into fitness report

### Fitness Report Format

```markdown
## Fitness Report

| Dimension | Score | Status | Issues |
|-----------|-------|--------|--------|
| DRY | 90/100 | PASS | — |
| SSOT | 100/100 | PASS | — |
| SoC | 65/100 | WARNING | route.ts:80 has SQL |
| Conventions | 85/100 | PASS | — |
| Boundaries | 70/100 | WARNING | circular dep in hooks/ |
| Coverage | 40/100 | BLOCKING | 3 functions untested |

**Overall: 75/100**
**Verdict: WARNING — 1 blocking issue**
```

## Scoring Thresholds

| Score | Status | Loop Action |
|-------|--------|-------------|
| > 80 | PASS | Advance |
| 60-80 | WARNING | Note in bead, proceed |
| < 60 | BLOCKING | Trigger L1 correction — runner must fix |

## Integration with Loop Mechanics

- Fitness score < 60 on any dimension → L1 sentinel correction with specific findings
- Fitness score < 60 after L1 correction → L3 escalation to Conductor
- Conductor may: re-decompose bead, provide more context, or accept the debt explicitly

## Fitness Check Catalog

See `references/fitness-functions.md` for the full catalog of specific checks and their pass conditions.
