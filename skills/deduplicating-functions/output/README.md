# Baseline Output Sample

This directory contains a checked-in sample output from the 11-detector
pipeline, used as a baseline for regression comparison and as a
reference for the output format.

## Prerequisites

The pipeline uses `sys.executable` (the interpreter that launched
`run_pipeline.py`). To reproduce the baseline exactly, that interpreter
must satisfy:

- **Python 3.10+** (scripts use PEP 604 `X | Y` typing syntax, softened
  by `from __future__ import annotations` but some libraries still require 3.10+)
- **`rapidfuzz`** (`detect-fuzzy-names.py`, `detect-signature-match.py`)
- **`datasketch`** (`detect-lsh-ast.py`)
- **`node` with `ts-morph` in `node_modules/`** (for `extract-functions-ast-ts.mjs`,
  only needed when source tree contains TS/JS files)
- **`bash` + `jq`** (only for `orchestrate.sh` and `generate-report-enhanced.sh`;
  `run_pipeline.py` does not require either)

macOS note: `/Library/Developer/CommandLineTools/usr/bin/python3` is
Python 3.9 and does not have these packages. Use a Python 3.10+ installed
via Homebrew or pyenv. Verify with:

```bash
python3 --version  # must be >= 3.10
python3 -c "import rapidfuzz, datasketch"  # must not raise
node --version  # only needed if source has TS/JS files
```

Install dependencies:

```bash
pip3 install -r requirements.txt
npm install  # only needed for TS/JS AST extraction
```

## Reproduction

From the repo root:

```bash
# Preserve README before wiping
cp output/README.md /tmp/output-readme.md
rm -rf output/
python3 run_pipeline.py scripts/ -o output/ --strict
rm output/pipeline.log  # machine-specific absolute paths
cp /tmp/output-readme.md output/README.md
```

The `--strict` flag causes the pipeline to exit non-zero if any
pipeline phase fails to execute cleanly:

- **Phase 0 (extract)**: extractor script missing, `node` missing
  from PATH (for TS extraction), or extractor exits non-zero / does
  not write its output file.
- **Phase 1 (detect)**: any of the 11 detectors exits non-zero
  (missing dependency, crash, etc.).
- **Phase 2 (merge)**: `merge-signals.py` exits non-zero or produces
  no output file.
- **Phase 3 (report)**: `generate-report-enhanced.sh` exits non-zero,
  produces no output, or is missing.
- **Phase 4 (evaluate, if `--eval-corpus` given)**: `evaluate.py`
  exits non-zero or produces no output.

Note: an extractor that successfully runs but produces a catalog
with zero functions is NOT a strict failure — that's a legitimate
"nothing to extract" result (e.g. `scripts/` contains no `.ts`
files so `catalog-ast-ts.json` is an empty array). The gate is
"did the phase run cleanly", not "did it find data".

Use `--skip-ast` or `--skip-ts` to intentionally omit extractors
in strict mode without tripping the failure check.

## Source

- **Corpus**: `scripts/` (the skill's own Python source — 14 files, ~140 functions)
- **Rationale**: Repo-local, deterministic, stable. Dogfooding the duplicate
  detector on its own source surfaces real consolidation opportunities.

## Contents

| File | Description |
|------|-------------|
| `extract/catalog-*.json` | Function catalogs from regex + AST extraction |
| `detect/*-results.json` | Output from each of the 11 detectors |
| `merge/merged-results.json` | Unified multi-signal merge with confidence scoring |
| `duplicates-report.md` | Human-readable markdown report |

## Summary at time of refresh

- Total pairs: 4888
- HIGH confidence: 1796
- MEDIUM confidence: 3077
- LOW confidence: 15
- All 11 detectors produced non-empty results

Catalog: 164 functions (148 Python + 16 TypeScript from `.mjs` files).

External dependencies reduced: the pipeline runner (`run_pipeline.py`)
no longer requires `jq` for catalog merging or `bash` for regex
extraction (Phase 0) or detection (Phase 1) or merging (Phase 2).
Phase 3 (report generation) still uses `bash` + `jq` via
`generate-report-enhanced.sh`. A fully pure-Python report generator
would eliminate the last shell dependency.

## Determinism

All 11 detectors and the merge pipeline are process-stable: two runs
against the same corpus produce byte-identical output for every JSON
artifact (extract catalogs, per-detector results, merged results).

The following files contain wall-clock timestamps and are NOT
byte-identical across runs:

- `pipeline.log` — every log line starts with `HH:MM:SS`.
- `duplicates-report.md` — contains `Generated: YYYY-MM-DD HH:MM`
  stamped by `generate-report-enhanced.sh`.

Previously, `detect-winnowing` used Python's randomized `hash()`,
`detect-lsh-ast` depended on dict/set iteration order, and
`detect-pdg-semantic` also used randomized `hash()` — all three
varied across runs. Those are now fixed at the detector level; the
remaining variance is only in the two report/log files above.
