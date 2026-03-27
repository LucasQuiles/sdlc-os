# Bead: bead-new-files
**Status:** verified
**Type:** implement
**Profile:** BUILD
**Runner:** runner-new-files
**Dependencies:** []
**Scope:** references/fft-decision-trees.md, references/deterministic-checks.md, references/anti-patterns.md, hooks/scripts/validate-decision-trace.sh, skills/sdlc-evolve/SKILL.md, commands/evolve.md, hooks/hooks.json
**Input:** Plan tasks 1-6 from docs/superpowers/plans/2026-03-26-fft-decision-architecture.md
**Output:** 6 new files created + hooks.json updated
**Sentinel notes:** []
**Cynefin domain:** clear
**Security sensitive:** false
**Complexity source:** accidental
**Decision trace:** [pending — will be created with bead]
**Deterministic checks:** [bash -n on hook script, jq on hooks.json]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Assumptions:** Plan tasks 1-6 have exact file content. Hook pattern matches existing hooks.
**Safe-to-fail:** Delete created files, revert hooks.json
**Confidence:** pending
