# Bead: bead-hook
**Status:** verified
**Type:** implement
**Runner:** runner-bead-hook
**Dependencies:** []
**Scope:** hooks/scripts/validate-hardening-report.sh, hooks/hooks.json
**Input:** Plan tasks 7-8 from docs/superpowers/plans/2026-03-26-reliability-hardening-phase.md
**Output:** Hook script (executable) and hooks.json updated with new entry
**Sentinel notes:** []
**Cynefin domain:** clear
**Assumptions:** Hook pattern matches existing validate-aqs-artifact.sh. hooks.json is valid JSON.
**Safe-to-fail:** Revert hooks.json from git, delete script
**Confidence:** pending
