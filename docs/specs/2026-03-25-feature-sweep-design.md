# Feature Sweep Design (v1)

## Objective

Add codebase-wide feature archaeology and closure triage to recover neglected work, especially features that are 50%+ complete but unfinished, unwired, or undocumented.

## New Components

- Agent: `feature-finder` (sonnet)
- Agent: `feature-finisher` (sonnet)
- Skill: `sdlc-feature-sweep`
- Command: `/feature-sweep`
- Artifact: `docs/sdlc/feature-matrix.md`

## Matrix Model

Item-level rows with lifecycle:

`DISCOVERED -> TRIAGED -> RESOLVED | DEFERRED | WONT_FIX`

Required fields:

`ID, Signal, Category, Location, Description, Completion %, Severity, Status, Type, Effort, Recommendation, Dependencies, Found, Last Seen, Owner, Notes`

## Threshold Policy

Severity by completion estimate:

- `CRITICAL`: 85-100%
- `HIGH`: 50-84%
- `MEDIUM`: 20-49%
- `LOW`: 0-19%

Action rule:

- `Completion % >= 50`: finisher must produce concrete completion spec (files, missing wiring/behavior, tests, blockers)
- `< 50`: triage recommendation quality over implementation detail

## SDLC Integration

- Scout phase: dispatch `feature-finder`
- Synthesize phase: dispatch `feature-finisher`
- On-demand: `/feature-sweep --mode finder|finisher|full`

## Non-Goals

- No auto-bead creation
- No automatic code edits by finder/finisher
- No replacement of existing `gap-analyst` requirement-completeness workflow

## Hook Status

Symlinked absolute-path normalization in `guard-bead-status.sh` is fixed in `226dbb7`, with integration coverage in `hooks/tests/test-hooks.sh`.
