# Bead: P3-04
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P3-03]
**Scope:** `colony/discovery.ts`, `colony/discovery.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase3-20260404/beads/P3-04-decision-trace.md
**Deterministic checks:** npx vitest run colony/discovery.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Implement completion-triggered adjacency discovery per spec §3.4. When a bead completes, inspect neighboring code for issues. Create findings (using boundary detector to classify as in_scope vs exploratory).

## Approach
Implement `DiscoveryEngine`:
1. `inspectAdjacent(completedBeadScope, missionScope)` — given the files a bead touched, identify adjacent files (same directory, same module, imported-by/imports relationships)
2. `generateDiscoveryChecks(adjacentFiles)` — return a list of check directives:
   - Lint/format issues (can be detected by examining file)
   - Dead exports (exported but not imported anywhere)
   - Missing tests (source file exists, test file doesn't)
   - Type safety gaps (any-casts in adjacent files)
3. Each check returns a finding candidate with evidence, confidence, and affected_scope
4. Findings are classified via BoundaryDetector before creation
5. Tests: adjacent file identification, check generation, boundary classification integration
