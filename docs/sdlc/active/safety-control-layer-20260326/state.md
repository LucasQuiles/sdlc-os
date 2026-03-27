# Task: Safety Control Layer (Phase B)

**Task ID:** safety-control-layer-20260326
**Created:** 2026-03-26
**Status:** Execute
**Complexity:** Moderate (19 implementation steps, 9 new files + 10 modified files)
**Spec:** `docs/specs/2026-03-26-safety-control-layer-design.md`
**Depends on:** Phase A (FFT Decision Architecture, v6.0.0)

## Mission Brief

Add a safety control layer grounded in Leveson (STAMP/STPA), Reason (Swiss Cheese), and Dekker (Drift Into Failure). 4 new agents, 15 safety mechanisms, STPA control structure model, safety constraints registry, resident pathogen registry, success library.

## Success Criteria

- 4 new agent files with correct frontmatter
- 4 new reference/artifact files
- 1 new hook script (validate-safety-constraints.sh)
- validate-decision-trace.sh updated with Phase B enforcement
- sdlc-orchestrate, sdlc-loop, sdlc-evolve, sdlc-adversarial updated
- All 5 Blue Team agents + LOSA observer updated
- quality-slos.md updated with feedback channel health SLI
- Hook test fixtures added
- All bash scripts pass syntax check
- hooks.json valid JSON
- plugin.json at 7.0.0

## Phase History

- Phases 0-3: Skipped — spec and plan exist
- Phase 4 (Execute): **ACTIVE**

## Quality Budget

- Status: healthy

## Design Tradeoff (Residual Risk)

L0-only paths intentionally accept probabilistic enforcement for LLM-only safety constraints. Advisory hooks provide early warning; LOSA observer catches violations post-merge. This is a speed/safety tradeoff gated by healthy quality budget.
