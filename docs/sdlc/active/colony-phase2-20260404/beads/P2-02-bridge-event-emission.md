# Bead: P2-02
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** none
**Scope:** `colony/bridge.ts`, `colony/bridge.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase2-20260404/beads/P2-02-decision-trace.md
**Deterministic checks:** npx vitest run colony/bridge.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Wire the bridge to emit typed events to events.db (or JSONL inbox per write serialization strategy) when bead status changes. Currently the bridge updates bead files and Git but does not emit events for the colony event system.

## Approach
1. Read `colony/bridge.ts` (434 lines) — find where bead status is updated
2. After each successful bead status change, append a typed event to `events-inbox.jsonl` (per spec §11.4 write serialization — bridge writes to JSONL, Deacon batch-ingests)
3. Event types to emit: `bead_completed` (on --completed), `bead_failed` (on --finding), `commit_created` (after git commit)
4. Each event includes: workstream_id (from bead file path), bead_id, timestamp, payload with status change details
5. Add tests verifying events are written to the inbox file

## Output
- Modified `colony/bridge.ts` with event emission
- New tests in `colony/bridge.test.ts`
- All existing 31 bridge tests still pass
