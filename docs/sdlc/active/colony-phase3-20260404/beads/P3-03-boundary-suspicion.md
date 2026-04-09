# Bead: P3-03
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** none
**Scope:** `colony/boundary-detector.ts`, `colony/boundary-detector.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase3-20260404/beads/P3-03-decision-trace.md
**Deterministic checks:** npx vitest run colony/boundary-detector.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Implement boundary suspicion detection per spec §3.2 and §9.4. When an agent discovers something that may cross a mission boundary, the system creates an exploratory issue rather than autonomous action.

## Approach
Implement `BoundaryDetector` class:
1. `classifyFinding(finding, missionScope)` — returns one of:
   - `in_scope` — finding's affected_scope is within the active mission
   - `adjacent` — finding is near but not within scope (same package/module parent)
   - `boundary_crossing` — finding is in a different domain/package
   - `novel` — finding pattern not seen before in operational memory
2. `shouldAutoPromote(classification)` — `in_scope` → yes, all others → no (route to exploratory)
3. Scope matching uses the mission's `scope_region` from the state ledger (e.g., `src/runtimes/` means anything under that path is in-scope)
4. Tests: in-scope file detected, adjacent file flagged, boundary crossing creates exploratory finding, novel pattern deferred
