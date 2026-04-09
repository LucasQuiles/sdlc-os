# Bead: E2E-03
**Status:** pending
**Type:** design
**Runner:** unassigned
**Dependencies:** none
**Scope:** WhatSoup colony spec §21
**Cynefin domain:** clear
**Security sensitive:** false
**Complexity source:** accidental
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-e2e-20260404/beads/E2E-03-decision-trace.md
**Deterministic checks:** grep -c 'Open Questions' docs/superpowers/specs/2026-04-04-colony-orchestration-design.md  # in WhatSoup repo
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Resolve or explicitly defer the 5 open questions in spec §21 with rationale.

## Questions
1. Local model triage — answer: defer to post-proving-slice. Start with direct Conductor spawning.
2. Merge coordination timing — answer: defer. Scope-isolated workers first. Monitor conflict rate.
3. Discovery budget calibration — answer: 20% cap is the starting point. Track discovery-to-execution ratio. Adjust based on signal quality.
4. Cross-workstream learning — answer: defer. Single-workstream first. Risk of contamination from different codebases.
5. Brick cold start — answer: resolved by Phase 1 bootstrap (cold-start uses minimal state packet, no Brick required).
