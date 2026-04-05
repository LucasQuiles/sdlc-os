# Bead: P3-06
**Status:** pending
**Type:** verify
**Runner:** unassigned
**Dependencies:** [P3-01, P3-02, P3-03, P3-04, P3-05]
**Scope:** full colony test suite
**Cynefin domain:** clear
**Security sensitive:** false
**Complexity source:** accidental
**Profile:** BUILD
**Decision trace:** /home/q/LAB/sdlc-os/docs/sdlc/active/colony-phase3-20260404/beads/P3-06-decision-trace.md
**Deterministic checks:** npx vitest run colony/; python -m pytest colony/deacon_test.py
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Integration verification for Phase 3. All new modules interoperate, all Phase 1+2 tests still pass.

## Checks
1. State ledger rehydration assembles a complete packet
2. Backpressure controller detects stuck patterns from real event data
3. Boundary detector classifies in-scope vs exploratory correctly
4. Discovery engine generates findings from adjacent files
5. Promotion with pattern matching works end-to-end
6. All 173+ tests pass
