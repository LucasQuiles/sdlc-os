# Bead: P2-05
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P2-02]
**Scope:** `colony/deacon.py`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase2-20260404/beads/P2-05-decision-trace.md
**Deterministic checks:** python -m pytest colony/deacon_test.py -v
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Wire the Deacon's maintenance loop to batch-ingest events from JSONL inbox files into events.db. Per spec §11.4 (write serialization), bridge and Brick write to JSONL inbox files. The Deacon is the single writer to events.db.

## Approach
1. In the Deacon's maintenance_cycle (60s timer), add inbox ingestion:
   - Read `events-inbox.jsonl` — parse each line as a TypedEvent JSON
   - Insert into events.db (INSERT OR IGNORE for idempotency)
   - Truncate the inbox file after successful ingest
   - Read `enrichment-inbox.jsonl` — same pattern for Brick outputs
2. Handle file-not-found gracefully (inbox doesn't exist = no events to ingest)
3. Handle malformed JSON lines (skip with warning, don't crash)
4. Add test verifying the batch ingest flow

## Output
- Modified `colony/deacon.py` with inbox ingestion in maintenance cycle
- All existing Deacon tests still pass
