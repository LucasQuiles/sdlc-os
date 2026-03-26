---
name: gap-analysis
description: "Run feature gap analysis — Finder mode maps what exists vs what's needed, Finisher mode verifies delivery completeness"
arguments:
  - name: mode
    description: "finder | finisher — defaults to auto-detect (Finisher if merged beads exist, Finder otherwise)"
    required: false
---

Run gap analysis using the `sdlc-os:sdlc-gap-analysis` skill.

1. Auto-detect mode if not specified (Finisher if SDLC artifacts with merged beads exist, Finder otherwise)
2. Collect truth sources (mission brief, external spec, codebase state, precedent system)
3. Dispatch gap-analyst in the selected mode
4. For large scope in Finder mode, gap-analyst may swarm guppies (one per requirement)
5. Produce Completeness Map (Finder) or Delivery Completeness + Closing Checklist (Finisher)
6. Present results to Conductor for next action
