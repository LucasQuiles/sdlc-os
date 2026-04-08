---
task-id: decision-noise-controls-20260330
description: "Implement Decision-Noise Controls — Phase 3b. MAP scoring, repeat-review noise, natural-frequency claims, anchoring-drift detection. Advisory-only v1."
profile: BUILD
complexity: complicated
current-phase: complete
spec: docs/specs/2026-03-30-decision-noise-controls-design.md
plan: docs/specs/2026-03-30-decision-noise-controls-plan.md
created-at: "2026-03-30T04:00:00Z"
rollout-discipline:
  wave-1: "Tasks 1-4 (contract + capture + derivation + hook) — land and verify before integration"
  wave-2: "Task 5 (orchestrate + adversarial + arbitration integration) — after wave-1 review"
  wave-3: "Tasks 6-7 (reporting surfaces + docs) — v1 scope only, no cue-calibration"
  wave-4: "Task 8 (verification)"
---

# Task State: decision-noise-controls-20260330

## Bead Manifest

| Bead | Type | Status | Deps | Plan Task | Wave |
|------|------|--------|------|-----------|------|
| B01-contract | implement | merged | — | Task 1 | 1 |
| B02-capture | implement | merged | B01 | Task 2 | 1 |
| B03-derivation | implement | merged | B01 | Task 3 | 1 |
| B04-hook | implement | merged | — | Task 4 | 1 |
| B05-integration | implement | merged | B01-B04 | Task 5 | 2 |
| B06-reporting | implement | merged | B05 | Task 6 | 3 |
| B07-docs | implement | merged | B04,B06 | Task 7 | 3 |
| B08-verify | verify | merged | ALL | Task 8 | 4 |
