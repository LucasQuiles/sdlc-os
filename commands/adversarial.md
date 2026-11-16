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
3. Produce the Adversarial Quality Report and structured AQS exit/runtime receipt while the bead remains `proven`
4. Evaluate FFT-14. The setting's live value is shown in the FFT-14 line of the `sdlc-os:sdlc-adversarial` skill; the health gate cross-checks the recorded value against the user settings. The setting is off by default. When off, record FULL/TARGETED as `skipped_by_setting`, run health (exit 3), and print `cross-model: skipped_by_setting (policy=<FULL|TARGETED>)` to the user and bead file. When on, review runs only in a proven visible read-only split pane or terminal window; `VISIBILITY_UNAVAILABLE` means REQUIRED_UNAVAILABLE. Require health `satisfied` for enabled review or `not_applicable` for explicit policy SKIP.
5. Update bead status to `hardened` only after step 4 succeeds. Otherwise retain `proven` and report the blocking or inconclusive role evidence.
