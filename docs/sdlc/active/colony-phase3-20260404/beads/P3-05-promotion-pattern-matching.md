# Bead: P3-05
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P3-03]
**Scope:** `colony/finding-ops.ts`, `colony/finding-ops.test.ts`
**Cynefin domain:** clear
**Security sensitive:** false
**Complexity source:** accidental
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase3-20260404/beads/P3-05-decision-trace.md
**Deterministic checks:** npx vitest run colony/finding-ops.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Add remediation pattern matching to checkAutoPromotion. Phase 1 deferred this (G2 swarm finding). The remediation_patterns table has seed patterns from bootstrap. Now wire the match check.

## Approach
1. In `checkAutoPromotion()`, after the existing 4 checks, add:
   - Query remediation_patterns table for patterns matching the finding's characteristics
   - Match by: finding evidence keywords vs pattern description, affected_scope file type vs pattern type
   - If match found with pattern confidence >= 0.7: allow promotion
   - If no match found: check if workstream count < 10 (cold-start relaxation per spec §14.1) — if yes, allow anyway; if no, require machine adjudication
2. On successful promotion, increment the matched pattern's usage_count
3. Tests: pattern match promotes, no match on cold-start still promotes, no match on mature system blocks
