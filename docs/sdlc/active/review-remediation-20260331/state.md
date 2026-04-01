---
task_id: review-remediation-20260331
title: "Fix all review findings from thinker-enhancement audit"
created: 2026-03-31T06:00:00Z
current-phase: frame
complexity: moderate
cynefin_domain: complicated
security_sensitive: true
description: >
  Address 2 critical, 7 important, and 5 undocumented issues found during
  the comprehensive review of the 69-commit thinker-enhancement work.
  Critical: invalid JSONL from bc bare decimals, shell-to-Python injection.
  Important: missing mkdir -p, stale spec, inconsistent arg parsing,
  hook consolidation, incomplete backfill, missing PyYAML guard,
  hardcoded thresholds. Plus 5 minor undocumented issues.
---

## Findings to Address

### Critical (2)
- C1: Invalid JSON in system-budget.jsonl — `bc` produces bare decimals
- C2: Shell-to-Python injection via triple-quote interpolation in decision-noise-lib.sh

### Important (7)
- I1: Missing `mkdir -p` in append-system-hazard-defense.sh and append-system-mode-convergence.sh
- I2: Design spec IS_AQS divergence — spec shows bead fallback, implementation is artifact-only
- I3: Inconsistent `--status` arg parsing in derive-hazard-defense-summary.sh
- I4: 7 separate PostToolUse hook matchers — consolidation opportunity
- I5: Backfill covers only quality-budget + mode-convergence
- I6: run-complete-gates.sh:54 missing PyYAML guard
- I7: update-stressor-library.sh hardcodes 4 Lindy thresholds from stressor-rules.yaml

### Undocumented (5)
- U1: warn-phase-transition.sh path wrong in handoff doc
- U2: mkdir -p failure mode — Python output silently lost in hazard-defense case
- U3: Backfill skips STPA-only tasks (no beads dir)
- U4: wip_beads fallback — mode-convergence bead count may silently be 0
- U5: Fixture schema drift — test fixtures use simplified field names
