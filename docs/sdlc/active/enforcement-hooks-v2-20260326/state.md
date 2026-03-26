---
task-id: "enforcement-hooks-v2-20260326"
description: "Implement enforcement hooks v2 — 3 advisory scripts, shared library, scanner update, guard refactor, 11 fixtures, tests"
current-phase:
  number: 4
  name: "Execute"
complexity: complicated
cynefin: complicated
team-roster:
  - role: Conductor
    model: opus
  - role: Runners
    model: sonnet
  - role: Sentinel
    model: haiku
created-at: "2026-03-26T00:00:00Z"
spec: "docs/superpowers/specs/2026-03-25-enforcement-hooks-v2-design.md"
plan: "docs/superpowers/plans/2026-03-26-enforcement-hooks-v2.md"
decisions:
  - phase: 0
    decision: "No-op — clean entry, prior task completed"
    timestamp: "2026-03-26T00:00:00Z"
  - phase: 1-3
    decision: "Skip — spec and plan created in this session"
    timestamp: "2026-03-26T00:00:00Z"
---

# Task State: enforcement-hooks-v2-20260326

## Bead Waves

**Wave A (parallel):** B1-scanner-template, B2-common-lib
**Wave B (parallel, depends A):** B3-naming-hook, B4-artifact-hook, B5-runner-hook, B6-guard-refactor
**Wave C (parallel, depends B):** B7-hooks-json, B8-fixtures, B9-test-runner
**Wave D (serial, depends C):** B10-verify
