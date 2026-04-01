# Review Remediation Plan

**Task:** review-remediation-20260331
**Scope:** 14 findings from thinker-enhancement audit — all addressed

## Execution Order

### Wave 1: Data Integrity & Security (C2, C1, I6, I1)

**Task 1 — Decision-noise Python handoff fixes (C2)**
Files: `scripts/lib/decision-noise-lib.sh`, `scripts/derive-decision-noise-summary.sh`
- Replace all `'''$var'''` interpolation with stdin or sys.argv passing
- `map_distance()` lines 18-19: pass map1/map2 via stdin
- `detect_escalations()` lines 76-77: pass pass1/pass2 via stdin
- `derive-decision-noise-summary.sh` line 227: pass $METRICS without interpolation
- Verify: run existing hook tests (decision-noise section should still pass)

**Task 2 — Centralized bc normalization + JSONL repair (C1)**
Files: `scripts/lib/sdlc-common.sh`, `scripts/lib/quality-budget-lib.sh`, `scripts/lib/stressor-lib.sh`, `scripts/derive-quality-budget.sh`, `docs/sdlc/system-budget.jsonl`
- Add `json_decimal()` function to sdlc-common.sh that normalizes bc output (handles .25 → 0.25 and -.25 → -0.25)
- Replace bare `bc` calls in quality-budget-lib.sh `complexity_weight()` (line 39)
- Replace bare `bc` calls in stressor-lib.sh `compute_stress_yield()` (line 149)
- Replace bare `bc` calls in derive-quality-budget.sh (lines 91-92, ZTR and TSPR)
- Fix the 2 existing invalid JSONL entries in system-budget.jsonl
- Verify: `python3 -c "import json; [json.loads(l) for l in open('docs/sdlc/system-budget.jsonl')]"` succeeds

**Task 3 — Missing PyYAML guard (I6)**
Files: `scripts/run-complete-gates.sh`
- Add `check_pyyaml` call before the python3 block at line 54
- Source sdlc-common.sh if not already sourced (or inline the guard)
- Verify: hook tests still pass

**Task 4 — Missing mkdir -p (I1, U2)**
Files: `scripts/append-system-hazard-defense.sh`, `scripts/append-system-mode-convergence.sh`
- Add `mkdir -p "$(dirname "$LEDGER")"` before append line in both scripts
- This also fixes U2 (silent data loss when dir missing)
- Verify: idempotency guards still work

### Wave 2: Contract Consistency (I3, I7, I2, I5, U1)

**Task 5 — Consistent --status arg parsing (I3)**
Files: `scripts/derive-hazard-defense-summary.sh`
- Replace positional `$3` with shift/case parsing matching derive-decision-noise-summary.sh pattern
- Verify: calling with `--status active` and `--status final` both work

**Task 6 — Externalize Lindy thresholds (I7)**
Files: `scripts/update-stressor-library.sh`, `references/stressor-rules.yaml`
- Read thresholds from stressor-rules.yaml instead of hardcoding >= 3, >= 5, >= 10, > 0.20
- Pass rules file path as argument or resolve relative to script
- Verify: existing stressor hook tests pass

**Task 7 — Stale spec + handoff doc fixes (I2, U1)**
Files: `docs/specs/2026-03-30-telemetry-enforcement-design.md`, `docs/HANDOFF-2026-03-31-thinker-enhancements.md`
- Update design spec lines 71-73 to remove bead-domain fallback, match implementation
- Fix warn-phase-transition.sh path reference in handoff (scripts/ → hooks/scripts/)
- Add newly discovered issues to handoff known-issues section

**Task 8 — Extend backfill to all lanes (I5, U3)**
Files: `scripts/backfill-telemetry.sh`
- Add STPA (hazard-defense), stress, and decision-noise lane support
- Handle tasks with no beads dir (STPA-only tasks)
- Maintain idempotency (check before append, same pattern as existing lanes)
- Verify: re-run backfill, existing entries not duplicated

### Wave 3: Cleanup & Edge Cases (I4, U4, U5)

**Task 9 — Consolidate hook matchers (I4)**
Files: `hooks/hooks.json`
- Merge the 7 separate PostToolUse Write|Edit matcher groups into the existing group
- Maintain same script references, just consolidate the matcher entries
- Verify: 62/62 hook tests still pass

**Task 10 — wip_beads fallback + fixture drift (U4, U5)**
Files: `scripts/append-system-mode-convergence.sh`, `hooks/tests/fixtures/dn-valid/decision-noise-summary.yaml`, `hooks/tests/fixtures/mc-valid/mode-convergence-summary.yaml`
- Add explicit bead count resolution in mode-convergence append (prefer beads.total from quality-budget, then count beads/*.md, then wip_beads)
- Update test fixtures to use actual field names from derive scripts
- Verify: hook tests pass, mode-convergence append produces correct bead count

## Write Sets (for parallel subagents)

- **Set A (Tasks 1, 3):** decision-noise libs + run-complete-gates PyYAML guard
- **Set B (Tasks 2, 4):** budget/stress numeric normalization + append mkdir fixes
- **Set C (Tasks 5, 6, 7, 8):** contract consistency — arg parsing, thresholds, specs, backfill
- **Set D (Tasks 9, 10):** hook consolidation + edge case fixes

Sets A and B can run in parallel (Wave 1, no overlapping files).
Set C after A+B (Wave 2, touches backfill which depends on fixed append scripts).
Set D after C (Wave 3, touches hooks.json and fixtures).
