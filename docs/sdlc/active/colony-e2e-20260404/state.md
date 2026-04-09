# Task: Colony E2E Smoke Test + Handoff Cleanup

**ID:** colony-e2e-20260404
**Created:** 2026-04-04
**Status:** active
**Profile:** BUILD
**Complexity:** complicated
**Cynefin:** complicated

## Objective
End-to-end integration test that exercises the full colony protocol with real tmup session + tmux grid. Plus housekeeping: update WhatSoup handoff doc and resolve spec open questions.

## Success Criteria
1. E2E test: bootstrap → tmup_init → dispatch worker → worker completes → bridge emits event → events ingested → Conductor can rehydrate state
2. WhatSoup handoff doc updated reflecting all session work
3. Spec open questions addressed or explicitly deferred with rationale

## Phase Log
| Phase | Started | Status |
|-------|---------|--------|
| Normalize | 2026-04-04 | complete |
| Architect | 2026-04-04 | complete (3 beads) |
| Execute | 2026-04-04 | active |
