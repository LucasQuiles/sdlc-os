# Bead: E2E-01
**Status:** pending
**Type:** verify
**Runner:** unassigned
**Dependencies:** none
**Scope:** `colony/e2e-colony-loop.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-e2e-20260404/beads/E2E-01-decision-trace.md
**Deterministic checks:** npx vitest run colony/e2e-colony-loop.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
E2E test that exercises the full colony data flow without requiring a live tmux grid. Simulates the complete protocol: bootstrap → workstream creation → event emission → finding lifecycle → backpressure detection → state rehydration → journal continuity.

## What to test
1. Bootstrap colony → create workstream → verify cold start state
2. Simulate worker completion: insert bead_completed event → verify events.db has it
3. Bridge simulation: append event to events-inbox.jsonl → Deacon ingest → verify in DB
4. Finding lifecycle: create in-scope finding → auto-promote → verify pattern match increments usage
5. Discovery: simulate adjacent file inspection → verify findings created with correct classification
6. Backpressure: insert 3 retry events for same bead → evaluateBackpressure → verify stuck_task signal + pause action
7. Rehydration: update ledger → write journal → rehydrateStatePacket → verify complete packet
8. Cross-module: finding promotion creates event → event captured in backpressure scan
