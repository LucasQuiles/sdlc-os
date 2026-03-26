---
name: feature-sweep
description: "Run neglected-feature discovery and closure triage across the codebase"
arguments:
  - name: mode
    description: "finder | finisher | full (default full)"
    required: false
---

Run feature sweep using the `sdlc-os:sdlc-feature-sweep` skill.

1. Select mode (`full` when not provided)
2. In `finder` or `full`, dispatch `feature-finder` and update `docs/sdlc/feature-matrix.md`
3. In `finisher` or `full`, dispatch `feature-finisher` to triage unresolved findings
4. Return a prioritized summary of `CRITICAL` and `HIGH` findings with recommended next actions
