---
name: stress
description: "Manually invoke barbell stress testing on the current task"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
---

Manually trigger stress testing for the current SDLC task.

1. Read the current task's `quality-budget.yaml` and `hazard-defense-ledger.yaml` (if exists)
2. Run `scripts/select-stressors.sh` to select applicable stressors from `references/stressor-library.yaml`
3. Create `stress-session.yaml` with `sampling_reason: manual`
4. Present selected stressors and sampling rationale to user for approval
5. On approval, apply stressors during the next AQS/hardening cycle
6. After completion, run `scripts/harvest-stressors.sh` and `scripts/update-stressor-library.sh`

Use this when you want to proactively stress-test work that FFT-15 would otherwise skip.
