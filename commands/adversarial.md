---
name: adversarial
description: "Manually trigger an adversarial quality sweep on current code"
arguments:
  - name: scope
    description: "What to attack — 'all' for full sweep, a bead ID, or a file path"
    required: false
---

Run the Adversarial Quality System using the `sdlc-os:sdlc-adversarial` skill.

**If scope is provided:**
1. If scope is a bead ID: run AQS on that specific bead
2. If scope is a file path: create a temporary bead scoped to that file and run AQS
3. If scope is "all": run AQS on all `proven` but not-yet-hardened beads

**If no scope provided:**
1. Check for an active SDLC task with `proven` beads that are not yet `hardened`
2. If found: run AQS on the next unhardened bead
3. If not found: ask the user what to attack

**In all cases:**
1. Assess complexity using scaling heuristics
2. Run the full adversarial cycle (recon -> cross-reference -> strike -> defend -> arbitrate)
3. Produce the Adversarial Quality Report
4. Update bead status to `hardened`
