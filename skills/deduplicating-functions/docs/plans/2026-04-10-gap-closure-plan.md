# Gap Closure Plan: Manual-Semantic Boundaries, Shell Parity, and Portability

**Goal:** Close the remaining non-blocking product gaps in `deduplicating-functions` after the documentation-accuracy cleanup, without regressing determinism or the 415-test baseline.

**Current truth:**
- The classical pipeline is real, deterministic, and fully tested.
- Manual LSP enrichment and manual semantic/LLM review are supported workflows, but not automated runner phases.
- `run_pipeline.py` is ahead of `scripts/orchestrate.sh` on evaluation support.
- Phase 3 reporting still depends on `bash` + `jq`.

**Working directory:** `/Users/q/.claude/plugins/sdlc-os/skills/deduplicating-functions`

---

## Gap Inventory

| ID | Gap | Current status | Desired end state |
|----|-----|----------------|-------------------|
| GC-001 | `orchestrate.sh` lacks `--eval-corpus` parity with `run_pipeline.py` | Missing | Shell runner can execute Phase 4 evaluation against a supplied corpus |
| GC-002 | Phase 3 report still depends on `bash` + `jq` | Partial portability | Python report generator replaces shell dependency, with equivalent output coverage |
| GC-003 | Semantic/LLM follow-up is manual only | Honest but manual | Explicit product decision: keep manual by design, or build a structured automation bridge |
| GC-004 | `--threshold` is merge-only, not detector-global | Honest but limited | Explicit product decision: keep merge-only, or add detector threshold plumbing with precise semantics |

---

## Phase 0: Normalize

- Preserve the current contract: deterministic outputs, strict gating, and manual semantic follow-up are intentional unless explicitly expanded.
- Treat `run_pipeline.py` as the behavior reference for evaluation support.
- Treat the current checked-in output baseline as sensitive: any score/count drift requires deliberate refresh and explanation.

## Phase 1: Frame

### Done Criteria

- `GC-001`: `scripts/orchestrate.sh` accepts `--eval-corpus`, runs `evaluate.py`, and reports precision/recall/F1 consistently with `run_pipeline.py`.
- `GC-002`: a Python report generator can fully replace `generate-report-enhanced.sh` for the standard report path, with test coverage for stable output shape.
- `GC-003`: either:
  - docs/help text explicitly freeze semantic follow-up as manual, or
  - a real automation bridge exists with bounded, testable inputs/outputs.
- `GC-004`: either:
  - the merge-only threshold contract remains explicit everywhere, or
  - detector thresholds become configurable via a new, clearly named interface.

### Non-Goals

- Do not make the automated pipeline depend on remote services or non-deterministic LLM output.
- Do not blur manual enrichment into an implied built-in pipeline phase.

---

## Phase 2: Scout

### Existing building blocks

- `run_pipeline.py`: reference implementation for strict gating and evaluation flow.
- `scripts/evaluate.py`: already computes evaluation metrics and JSON output.
- `scripts/generate-report-enhanced.sh`: current behavior source for Phase 3 output.
- `tests/test_pipeline_strict.py`: existing end-to-end runner contract tests.
- `output/README.md` and checked-in baseline: current reproducibility anchor.

### Constraints

- Report generation currently includes timestamped output; portability work must preserve honest determinism language.
- Shell and Python runner parity should avoid duplicating business logic in incompatible ways.

---

## Phase 3: Architect

### Bead 1: Shell Evaluation Parity (`GC-001`)

**Scope**
- Modify `scripts/orchestrate.sh`
- Add/extend tests that exercise shell evaluation flow

**Work**
1. Add `--eval-corpus PATH` parsing and help text.
2. Add a Phase 4 evaluation step after merge/report.
3. Reuse `scripts/evaluate.py` and log metrics from the correct schema path.
4. Define behavior when evaluation is requested but output prerequisites are missing.

**Evidence**
- New shell-runner tests covering success and missing-corpus failure paths.
- Manual verification command in the plan notes.

### Bead 2: Python Report Generator (`GC-002`)

**Scope**
- Create `scripts/generate-report.py`
- Update `run_pipeline.py` and optionally `orchestrate.sh` to prefer it
- Add tests for report content and output shape

**Work**
1. Extract the current report contract from `generate-report-enhanced.sh`.
2. Reimplement the contract in Python with stable ordering.
3. Keep the shell script temporarily as compatibility fallback.
4. Update docs/install guidance once parity is proven.

**Evidence**
- Golden-style report tests against representative merged output.
- Verification that the Python generator removes the `jq`/`bash` dependency from the default path.

### Bead 3: Semantic Automation Decision Record (`GC-003`)

**Scope**
- Docs + possibly a design note, not code by default

**Work**
1. Decide whether semantic review stays manual by design.
2. If yes, codify that as an ADR-style note and stop describing it as an omitted automation gap.
3. If no, define a bounded automation bridge:
   - category input artifact
   - execution hook
   - output schema
   - failure semantics

**Evidence**
- A written decision file or approved implementation plan.

### Bead 4: Threshold Semantics Decision Record (`GC-004`)

**Scope**
- CLI/docs or follow-on implementation plan

**Work**
1. Decide whether `--threshold` should remain merge-only.
2. If global detector tuning is desired, introduce a new interface instead of overloading the current flag.
3. Specify detector coverage, defaults, and compatibility behavior.

**Evidence**
- Either explicit documentation freeze, or a follow-on threshold-plumbing plan with tests.

---

## Phase 4: Execute

### Recommended order

1. Bead 1 (`GC-001`) because it is a clear shell-parity gap.
2. Bead 3 (`GC-003`) to settle whether semantic automation is actually in scope.
3. Bead 4 (`GC-004`) to settle threshold semantics before changing CLI behavior.
4. Bead 2 (`GC-002`) last, because it is the largest code movement and touches output contracts.

### Verification loop per bead

1. Add or update focused tests first.
2. Implement the minimal change.
3. Run focused tests.
4. Run the full suite.
5. If merged output or report artifacts drift, refresh them in an isolated commit with explicit rationale.

---

## Phase 5: Synthesize

Before calling the gap set complete:

- `pytest tests -q --tb=line` stays green.
- Any CLI/help text changes match actual behavior.
- Manual-only workflows are clearly labeled manual.
- Portability claims match the true dependency surface.
- Baseline/report drift is either absent or deliberately refreshed and explained.
