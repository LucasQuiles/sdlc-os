# Bead: P3-01
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** none
**Scope:** `colony/state-ledger.ts`, `colony/state-ledger.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase3-20260404/beads/P3-01-decision-trace.md
**Deterministic checks:** npx vitest run colony/state-ledger.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Implement state ledger CRUD operations for the coordinated rehydration flow. The state_ledger table exists (Phase 1) but has no TypeScript operations for update/read/rehydrate. The Conductor needs these to assemble state packets at session start.

## Approach
1. `updateLedger(workstreamId, fields)` — partial update of any ledger field (active_beads, hotspots, linked_findings, decision_anchors, etc.)
2. `getLedger(workstreamId)` — read full ledger row, return typed StateLedgerRow
3. `rehydrateStatePacket(workstreamId)` — orchestrated rehydration: read ledger + resolve linked artifacts + read latest journal entries + return assembled state packet
4. All operations use try/catch with ColonyDbError (G6 pattern)
5. Tests: create workstream, update fields, verify rehydration assembles complete packet
