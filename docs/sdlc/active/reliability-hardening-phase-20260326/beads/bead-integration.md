# Bead: bead-integration
**Status:** verified
**Type:** implement
**Runner:** runner-bead-integration
**Dependencies:** [bead-agents, bead-skill]
**Scope:** hooks/scripts/guard-bead-status.sh, skills/sdlc-orchestrate/SKILL.md, .claude-plugin/plugin.json
**Input:** Plan tasks 9-11 from docs/superpowers/plans/2026-03-26-reliability-hardening-phase.md
**Output:** guard-bead-status.sh with reliability-proven, sdlc-orchestrate with Phase 4.5, plugin.json at 5.0.0
**Sentinel notes:** []
**Cynefin domain:** clear
**Assumptions:** Existing files match the line numbers in the plan. guard-bead-status.sh passes bash -n after edit.
**Safe-to-fail:** Revert all three files from git
**Confidence:** pending
