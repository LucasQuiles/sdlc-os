# Task: Cross-Model Adversarial Review (v9.0.0)

**ID:** crossmodel-adversarial-review-20260328
**Created:** 2026-03-28
**Profile:** BUILD
**Phase:** Execute
**Status:** active
**Complexity:** COMPLEX
**Plugin version at start:** v8.1.0

## Objective

Add cross-model adversarial review to the SDLC-OS pipeline using tmup/Codex workers as genuinely independent reviewers. FFT-14 routing, Stage A (red team supplement) + Stage B (independent review), resilient session management with circuit breakers and fallback ladder. Advisory-only day 1.

## Spec

`docs/specs/2026-03-28-crossmodel-adversarial-review-design.md`

## Plan

`docs/superpowers/plans/2026-03-28-crossmodel-adversarial-review.md`

## Success Criteria

- [ ] Any tmup failure degrades gracefully without blocking the main bead path
- [ ] Every valid Codex finding is traceable to a structured artifact
- [ ] Every invalid/missing artifact is explicitly classified (NO_EVIDENCE, MALFORMED, etc.)
- [ ] Every retry and fallback is logged in session journal + decision trace
- [ ] No infinite retry loops
- [ ] No ambiguous "clean" result without evidence
- [ ] Stage A workers never see Claude AQS findings
- [ ] Stage B reviewer never sees any review artifacts
- [ ] Cross-model findings only enter the system through normalization + triage
- [ ] FFT-14 decision recorded in bead decision trace
- [ ] Serialized cross-model sessions per project (no grid races)
- [ ] Day-1: advisory only, not blocking

## Beads

| Bead | Type | Status | Scope | Dependencies |
|------|------|--------|-------|-------------|
| B1-scripts | implement | submitted | scripts/crossmodel-*.sh | none |
| B2-aqs-schema | implement | running | references/artifact-templates.md, skills/sdlc-adversarial/SKILL.md | none |
| B3-fft14 | implement | running | references/fft-decision-trees.md | none |
| B4-agents | implement | running | agents/crossmodel-supervisor.md, agents/crossmodel-triage.md | none |
| B5-skill | implement | pending | skills/sdlc-crossmodel/SKILL.md | B2, B3, B4 |
| B6-wiring | implement | pending | skills/sdlc-orchestrate/SKILL.md, skills/sdlc-evolve/SKILL.md | B3, B5 |
| B7-release | implement | pending | plugin.json, docs/HANDOFF.md | all |

## Turbulence

| Bead | L0 | L1 | L2 | L2.5 | L2.75 |
|------|----|----|----|----|-----|
| B1-scripts | 0 | 0 | 0 | 0 | 0 |
| B2-aqs-schema | 0 | 0 | 0 | 0 | 0 |
| B3-fft14 | 0 | 0 | 0 | 0 | 0 |
| B4-agents | 0 | 0 | 0 | 0 | 0 |
| B5-skill | 0 | 0 | 0 | 0 | 0 |
| B6-wiring | 0 | 0 | 0 | 0 | 0 |
| B7-release | 0 | 0 | 0 | 0 | 0 |

## Phase Log

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Normalize | DONE | Clean state, spec + plan already exist |
| 1. Frame | SKIPPED | Spec exists: docs/specs/2026-03-28-crossmodel-adversarial-review-design.md |
| 2. Scout | SKIPPED | Plan exists: docs/superpowers/plans/2026-03-28-crossmodel-adversarial-review.md |
| 3. Architect | SKIPPED | Bead decomposition in plan (7 beads) |
| 4. Execute | IN PROGRESS | Wave 1: B1-B4 parallel (independent). Wave 2: B5-B6 (dependent). Wave 3: B7. |
| 4.5. Harden | PENDING | |
| 5. Synthesize | PENDING | llm-self-security auto-triggers (agent/skill/hook files modified) |

## Quality Budget

Inherited from prior task: healthy (all SLOs met).

## Decision Trace

FFT-01 → BUILD (new feature, code changes)
FFT-02 → COMPLEX (multi-system, high risk, tmup integration, new pipeline stage)
FFT-10 → ESSENTIAL (novel multi-agent coordination, not boilerplate)
