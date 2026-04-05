# Task: Colony Orchestration — Phase 2: Cross-Model + Review + Discovery

**ID:** colony-phase2-20260404
**Created:** 2026-04-04
**Status:** complete
**Profile:** BUILD
**Complexity:** complicated
**Cynefin:** complicated
**Parent task:** Colony Orchestration spec (WhatSoup)

## Objective
Wire the cross-model collaboration protocol, conductor journal consumption in real Conductor sessions, Brick preprocessing integration, and the DISCOVER session type. Phase 1 built the modules — Phase 2 connects them into a working colony loop.

## Success Criteria
1. Cross-model dispatch works — Claude worker produces, Codex worker reviews (or vice versa)
2. Conductor journal is read at session start and written at session end
3. Brick `brick_preprocess` is called on at least one EVALUATE path
4. DISCOVER session type works in conductor-prompt.md
5. Review loop completes: Model A → Model B review → findings route back
6. All Phase 1 tests still pass (79 baseline)
7. New integration tests for cross-model handoff

## Scope
- `sdlc-os/colony/conductor-prompt.md` — add journal protocol, DISCOVER instructions
- `sdlc-os/skills/sdlc-orchestrate/colony-mode.md` — update bead-context.md protocol for cross-model
- `sdlc-os/colony/bridge.ts` — emit typed events to events.db on bead status change
- New: cross-model review loop integration test

## Phase Log
| Phase | Started | Status |
|-------|---------|--------|
| Normalize | 2026-04-04 | complete |
| Frame | 2026-04-04 | complete (from spec §6 + §7) |
| Architect | 2026-04-04 | complete (6 beads) |
| Execute | 2026-04-04 | complete (6 beads, 5 commits, 173 tests) |
| Synthesize | 2026-04-04 | complete (all verified) |
