# Bead: bead-hooks-version
**Status:** verified
**Type:** implement
**Profile:** BUILD
**Runner:** runner-hooks-version
**Dependencies:** [bead-orchestrate-updates, bead-scaling-loop]
**Scope:** hooks/scripts/guard-bead-status.sh, .claude-plugin/plugin.json
**Input:** Plan tasks 11, 12 from docs/superpowers/plans/2026-03-26-fft-decision-architecture.md
**Output:** guard-bead-status.sh with evolve type, plugin.json at 6.0.0
**Sentinel notes:** []
**Cynefin domain:** clear
**Security sensitive:** false
**Complexity source:** accidental
**Decision trace:** [pending]
**Deterministic checks:** [bash -n on guard script, jq on plugin.json]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Assumptions:** All prior beads complete
**Safe-to-fail:** Revert both files from git
**Confidence:** pending
