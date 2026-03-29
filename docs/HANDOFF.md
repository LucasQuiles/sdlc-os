# SDLC-OS Plugin — Handoff Document

**Date:** 2026-03-27
**Plugin version:** 9.0.0
**Location:** `~/.claude/plugins/sdlc-os/`
**Git:** 4 commits on `main`

---

## What This Is

A multi-agent SDLC orchestration system for Claude Code. The Conductor (Opus) decomposes tasks into atomic beads, dispatches Sonnet runners in parallel, Haiku sentinels patrol continuously, an Oracle council verifies claims, and adversarial red/blue teams probe for defects. Every Conductor decision is routed through Fast-and-Frugal Decision Trees (Gigerenzer). A safety control layer (Leveson/Reason/Dekker) monitors system integrity.

## Current State (v9.0.0)

| Component | Count |
|-----------|-------|
| Agents | 45 |
| Skills | 15 |
| Hook scripts | 9 |
| Reference docs | 21 |
| Cross-model scripts | 5 |
| Commands | 11 |
| Research docs | 10 (4,898 lines) |
| Design specs | 8 |
| Implementation plans | 4 |

### Commit History (This Session)

| Commit | Version | What |
|--------|---------|------|
| `8032d04` | v5.0.0 | Phase 4.5 Reliability Hardening — 5 agents, 1 skill, 1 hook |
| `b5575d2` | v6.0.0 | FFT Decision Architecture — 12 FFTs, 4 profiles, Evolve skill, HRO constraints |
| `33d0df3` | v7.0.0 | Safety Control Layer — 4 agents, 15 mechanisms, STPA model |
| _pending_ | v8.0.0 | Reliability Telemetry (Phase C) — 3 agents, 3 references, 3 skill updates |

### Architecture Layers (Bottom to Top)

```
Layer 9: Cross-Model Adversarial Review (v9.0.0)
  FFT-14 escalation, tmup/Codex workers, crossmodel-supervisor, advisory day-1
  Cross-model debate (Milvus 53%→80%), tmup DAG coordination, circuit breakers, fallback ladder

Layer 8: Standards Enforcement (v8.1.0)
  LLM self-security (OWASP LLM Top 10), standards curation from /Research/Standards
  OWASP, CISQ, CWE, CERT, SRE, SOLID, Clean Architecture, Testing Standards

Layer 7: Reliability Telemetry (Phase C — v8.0.0)
  March of Nines reliability ledger, common/special cause classification, slopacolypse defense
  Karpathy (March of Nines, Slopacolypse), Deming (SPC, Funnel Rules, PDSA)

Layer 6: Safety Control (Phase B — v7.0.0)
  STPA control structure, 15 safety mechanisms, 4 safety agents
  Leveson (STAMP), Reason (Swiss Cheese), Dekker (Drift)

Layer 5: FFT Decision Architecture (Phase A — v6.0.0)
  12 Fast-and-Frugal Trees, decision traces, 4 task profiles
  Gigerenzer, Meadows, Deming, Taleb, Weick, Klein, Kahneman, Karpathy, Brooks

Layer 4: Reliability Hardening (Phase 4.5 — v5.0.0)
  Per-bead observability, error handling, edge cases, red/blue reliability probing
  Kahneman (System 1/2, WYSIATI, premortem), Karpathy (H-E-E, hard constraints), Yegge (NDI, GUPP)

Layer 3: Adversarial Quality System (AQS — v4.0.0, pre-session)
  4 red teams, 4 blue teams, arbiter, Kahneman adversarial collaboration

Layer 2: Loop Hierarchy (v3.0.0, pre-session)
  L0-L6 fractal correction loops, calibration protocol, noise audits

Layer 1: Core Orchestration (v1.0.0, pre-session)
  Conductor/Runner/Sentinel/Oracle/Guppy, Cynefin routing, bead system
```

---

## Key Files to Read First

### If You're Implementing Phase C
1. `docs/specs/2026-03-26-fft-decision-architecture-design.md` — Section 7 (Phase C attachment points, lines 775-813)
2. `docs/research/2026-03-26-reconciled-delta.md` — The 55 net-new concepts with priority ratings
3. `docs/research/2026-03-26-karpathy-gap-analysis.md` — March of Nines, deterministic routing, slopacolypse defense
4. `docs/research/2026-03-26-deming-weick-gigerenzer-deep-research.md` — Common/special cause, control charts, PDSA

### If You're Understanding the System
1. `skills/sdlc-orchestrate/SKILL.md` — The main orchestration skill (how everything fits together)
2. `references/fft-decision-trees.md` — All 12 FFTs (single source of truth for routing)
3. `references/stpa-control-structure.md` — System-level control structure model
4. `skills/sdlc-loop/SKILL.md` — The L0-L6 loop hierarchy

### If You're Modifying Agents
1. Read any existing agent in `agents/` for the frontmatter format: `name`, `description` (double-quoted), `model` (haiku|sonnet|opus)
2. `references/anti-patterns.md` — 8 named anti-patterns the system guards against
3. `references/safety-constraints.md` — Invariants all agents must respect

---

## Phased Roadmap

### Phase A: FFT Decision Architecture — DONE (v6.0.0)

12 Fast-and-Frugal Trees replacing all Conductor prose routing. Decision traces as a new information flow (Meadows Level 6). 4 task profiles (Build/Investigate/Repair/Evolve). 5 Weick HRO structural constraints. Evolve skill for system self-improvement.

**Spec:** `docs/specs/2026-03-26-fft-decision-architecture-design.md` (959 lines)
**Plan:** `docs/superpowers/plans/2026-03-26-fft-decision-architecture.md` (1,178 lines)

### Phase B: Safety Control Layer — DONE (v7.0.0)

STPA control structure with 6 interfaces and process models. 15 safety mechanisms (L1-L5 Leveson, R1-R5 Reason, D1-D5 Dekker). 4 new agents. Latent condition tracing, resident pathogen registry, success library.

**Spec:** `docs/specs/2026-03-26-safety-control-layer-design.md` (619 lines)

### Phase C: Reliability Telemetry — DONE (v8.0.0)

Three capabilities that measure the backbone:

**C1. March of Nines Reliability Ledger (Karpathy)**
- Aggregate turbulence fields across tasks → per-step first-pass success rates
- L0 first-pass rate, L1 approval rate, L2 proof rate, L2.5 hardening rate
- Bottleneck identification: invest improvement effort where reliability is lowest
- Attaches to: bead `turbulence` field + decision traces
- Source: `docs/research/2026-03-26-karpathy-gap-analysis.md`, thinkers-lab `netnew-005`

**C2. Common/Special Cause Classification (Deming)**
- Before any corrective action from calibration or noise audit, classify the signal
- Common cause (system-wide) → fix prompts, rubrics, temperature. Do NOT adjust individual agents.
- Special cause (specific agent) → fix that agent's configuration
- Deming Funnel Rule 1: stable process → do NOT adjust. Tampering is worse than inaction.
- Control charts: only intervene when signals appear outside control limits
- Attaches to: calibration protocol noise audit
- Source: `docs/research/2026-03-26-deming-weick-gigerenzer-deep-research.md` line 702

**C3. Slopacolypse Defense / Simplicity Audit (Karpathy)**
- After runner submission, before full sentinel verification
- Compare solution complexity (LOC, abstractions, dependencies, nesting) against problem complexity (spec scope, domain)
- Flag disproportionate ratio: dead code, premature generalization, factory patterns wrapping single functions
- Attaches to: L1 Sentinel loop
- Source: `docs/research/2026-03-26-karpathy-gap-analysis.md`, thinkers-lab `netnew-004`

**Design tradeoff to preserve:** L0-only paths intentionally accept probabilistic enforcement for LLM-only safety constraints. Advisory hooks provide early warning; LOSA catches violations post-merge. This is by design (spec Section 7).

---

## Research Corpus

### Local Research (docs/research/)

| File | Lines | Content |
|------|-------|---------|
| `kahneman-gap-analysis.md` | 228 | 31 concepts: 13 embedded, 5 partial, 13 gaps |
| `kahneman-reliability-research.md` | 391 | Adversarial collaboration, System 1/2, noise, WYSIATI, prospect theory |
| `karpathy-gap-analysis.md` | 228 | 38 concepts: 19 embedded, 6 partial, 13 gaps |
| `karpathy-reliability-research.md` | 305 | Recipe for Training NNs, Software 2.0/3.0, Tesla data engine |
| `yegge-gap-analysis.md` | 284 | 37 concepts: 16 embedded, 5 partial, 16 gaps |
| `yegge-gastown-deep-research.md` | 278 | MEOW stack, GUPP, NDI, Refinery, Deacon, Wasteland |
| `additional-thinkers-research.md` | 372 | 35+ concepts from Taleb, Deming, Meadows, Leveson, Dekker, Reason, Klein, Weick, Gigerenzer, Simon, March, Brooks, Surowiecki, Sterman, + AI research |
| `reconciled-delta.md` | 494 | Deduplicated delta: 16 HIGH, 25 MEDIUM, 14 LOW net-new |
| `deming-weick-gigerenzer-deep-research.md` | 758 | 10 foundational principles, FFT routing, PDSA integration |
| `safety-science-trifecta.md` | 838 | 14 prioritized mechanisms from Dekker + Reason + Leveson |

### Deep Research Specs

| File | Lines | Content |
|------|-------|---------|
| `docs/specs/2026-03-26-meadows-leverage-points-sdlc-mapping.md` | 729 | All 12 leverage points, 8 system archetypes, force multiplier estimates |

### Pinecone Index: thinkers-lab

**2,146 records** across 10 namespaces. Use `mcp__pinecone__search-records` with namespace specified (NOT empty string — use specific namespace name).

| Namespace | Records | Best For |
|-----------|---------|----------|
| `research` | 1,956 | Bulk research content |
| `sdlc-mappings` | 30 | Thinker concepts → specific SDLC mechanisms (MOST USEFUL for design) |
| `methods` | 14 | Actionable methods (FFT, STPA, Pre-mortem, Noise Audit, etc.) |
| `scenarios` | 20 | Multi-thinker analysis of real-world problems |
| `anti-patterns` | 25 | Named failure modes with detection/mitigation |
| `net-new` | 15 | HIGH-priority concepts not yet in the system |
| `connections` | 26 | Thinker-to-thinker relationships (complementary, debate, lineage) |
| `synthesis` | 20 | Cross-thinker synthesis |
| `debates` | 15 | Intellectual tensions between thinkers |
| `code-refs` | 25 | Code-level references |

### Pre-Existing Research

| File | Lines | Content |
|------|-------|---------|
| `docs/specs/2026-03-25-aqs-v2-research-synthesis.md` | 424 | Original research synthesis: 32 concepts from 16+ sources |

---

## Conventions

### Agent File Format
```yaml
---
name: kebab-case-name
description: "Double-quoted description"
model: haiku|sonnet|opus
---

System prompt in markdown...
```

### Skill File Format
```yaml
---
name: kebab-case-name
description: "Double-quoted description"
---

Skill content in markdown...
```

### Hook Pattern
- Shebang: `#!/bin/bash`
- `set -euo pipefail`
- Read stdin: `INPUT=$(cat)` then `jq` to extract
- Exit 0 = pass/advisory, Exit 2 = blocking validation error
- Use `${CLAUDE_PLUGIN_ROOT}` for paths in hooks.json

### Bead Format (Extended)
```markdown
# Bead: {id}
**Status:** pending | running | submitted | verified | proven | hardened | reliability-proven | merged | blocked | stuck | escalated
**Type:** investigate | design | implement | verify | review | evolve
**Profile:** BUILD | INVESTIGATE | REPAIR | EVOLVE
**Runner:** [agent name]
**Dependencies:** [bead IDs]
**Scope:** [files]
**Input:** [context]
**Output:** [expected]
**Sentinel notes:** []
**Cynefin domain:** clear | complicated | complex | chaotic | confusion
**Security sensitive:** true | false
**Complexity source:** essential | accidental
**Decision trace:** [path to {bead-id}-decision-trace.md]
**Deterministic checks:** [list]
**Control actions:** [STPA — for COMPLEX/security-sensitive]
**Unsafe control actions:** [UCAs — for COMPLEX/security-sensitive]
**Latent condition trace:** [after accepted findings]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Assumptions:** []
**Safe-to-fail:** [rollback plan]
**Confidence:** [0.0-1.0]
```

### Decision Trace Location
`docs/sdlc/active/{task-id}/beads/{bead-id}-decision-trace.md` — flat alongside bead file, NOT in subdirectory.

---

## Critical Design Decisions

1. **Flat bead files** — no per-bead directories. Traces alongside beads as `{bead-id}-decision-trace.md`.
2. **FFTs are single source of truth** — `references/fft-decision-trees.md`. Other files reference, never duplicate.
3. **STPA skip rule** — applies when COMPLEX or security_sensitive. NOT triggered by ESSENTIAL alone.
4. **L0 budget stays at 3** — let-it-crash (Armstrong) deferred to Phase C pending telemetry data.
5. **Hook/agent separation** — hooks provide advisory signal (always), agents provide enforcement (when L1 active). No transport dependency.
6. **Evolve beads** — status flow `pending → running → submitted → verified → merged` (skip proven/hardened).
7. **Security-sensitive overrides ACCIDENTAL** — security-sensitive config/auth beads get full STPA regardless of complexity source.
8. **L0-only probabilistic enforcement** — CLEAR beads accept risk of missing LLM-only safety constraints. Quality budget healthy state is the precondition.

---

## What NOT to Change Without Understanding

- The 12 FFTs are deeply cross-referenced. Changing one FFT requires checking all downstream references.
- The STPA skip rule is canonical. Any change must propagate to: L1 mechanism, Section 4 table, hook enforcement, and the FFT-10 interaction.
- The bead status flow is enforced by `guard-bead-status.sh`. New statuses or transitions require hook updates.
- The `hooks.json` PostToolUse array order matters for performance — lightweight hooks first.
- Blue Team response format is now shared across 5 agents + the adversarial skill. Changes must propagate to all 6 locations.

---

## Theoretical Foundations

### Deeply Embedded (structural, not just referenced)
- **Gigerenzer** — FFTs for all routing, ecological rationality, adaptive toolbox
- **Meadows** — Leverage points (Level 5-6 intervention), system archetypes
- **Kahneman** — System 1/2, adversarial collaboration, noise audits, WYSIATI, certainty effect, premortem, MAP
- **Karpathy** — Hypothesis-experiment-evidence, hard constraints, one-variable-at-a-time, test-time compute
- **Yegge** — GUPP, NDI, Rule of Five, colony thesis, 40% health budget
- **Deming** — Anti-tampering (Funnel Rule 1), system over agents, PDSA
- **Taleb** — Barbell strategy, via negativa, Lindy Effect
- **Weick** — HRO five principles (structural constraints, not optional)
- **Dekker** — Local rationality, normalization of deviance detection, Safety-II
- **Reason** — Swiss cheese (loop hierarchy), latent condition tracing, just culture, safety culture components
- **Leveson** — STPA control analysis, unsafe control actions, process models, safety constraints
- **Klein** — RPD for familiar patterns (precedent fast-track)
- **Brooks** — Essence vs accident classification
- **Surowiecki** — Four conditions for wise crowds (multi-agent consensus verification)
- **Armstrong/Hewitt** — Supervision tree model (deferred let-it-crash to Phase C)

### Referenced But Not Yet Structural
- **Sterman** — System dynamics delays (delay budget concept in research)
- **Simon** — Bounded rationality, near-decomposability (theoretical grounding)
- **March** — Exploration vs exploitation (exploration budget in Evolve)
- **Lamport** — Formal state machine specification (lightweight version proposed for Complex beads)
- **Snowden** — Distributed cognition, narrative patterns (beyond Cynefin)
- **Helland** — Saga pattern for cross-bead coordination
