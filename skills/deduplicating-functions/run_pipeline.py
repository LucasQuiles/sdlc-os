#!/usr/bin/env python3
"""Integration regression runner for duplicate function detection skill."""
from __future__ import annotations

import argparse
import os
import sys
import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from safety import acquire_pipeline_lock, check_preflight, DEFAULT_LOCK_PATH

PYTHON = sys.executable  # Use the same interpreter that launched this script

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(BASE, "scripts")


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run(cmd, label="", check=True, log_file=None):
    log(f"  Running: {label or ' '.join(str(c) for c in cmd[:3])}")
    if log_file:
        with open(log_file, "a") as lf:
            result = subprocess.run(cmd, stderr=lf, stdout=subprocess.PIPE, text=True)
    else:
        result = subprocess.run(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
    if check and result.returncode != 0:
        log(f"  WARNING: {label} exited {result.returncode}")
    return result


def _strict_gate(phase: str, message: str, strict: bool, log_file: str = "") -> None:
    """Log an error and exit 2 if strict mode is active.

    Strict mode is the default; callers pass ``strict=False`` to opt into
    permissive behavior via the --permissive flag.
    """
    log(f"  ERROR: {message}")
    if strict:
        suffix = f" See {log_file}" if log_file else ""
        log(f"ERROR: strict mode: {phase} failed.{suffix}")
        sys.exit(2)


# Maximum detector parallelism regardless of CPU count. Each detector can
# use multi-GB RSS, so this intentionally flattens on large machines.
# Adjust here (one place) if per-detector RSS drops in Phase 2/3 of the
# OOM safety work.
MAX_DETECTOR_JOBS = 4


def _default_jobs() -> int:
    """Conservative default: half the CPU count, capped at MAX_DETECTOR_JOBS.

    Each detector can use multi-GB RSS, so the cap is intentionally
    conservative even on large machines. Override with --jobs N or
    SDLC_OS_DETECTOR_JOBS=N.
    """
    cpu = os.cpu_count() or 4
    return max(1, min(MAX_DETECTOR_JOBS, cpu // 2))


def _resolve_jobs(cli_jobs: int | None) -> int:
    """Resolve the effective jobs cap. CLI > env > default."""
    if cli_jobs and cli_jobs > 0:
        return cli_jobs
    env = os.environ.get("SDLC_OS_DETECTOR_JOBS", "").strip()
    if env.isdigit() and int(env) > 0:
        return int(env)
    return _default_jobs()


def parse_args():
    p = argparse.ArgumentParser(description="Run the full duplicate detection pipeline")
    p.add_argument("source", nargs="?", default=None,
                   help="Source directory to analyze (omit when using --from-corpus)")
    p.add_argument("-o", "--output-dir", default=os.path.join(BASE, "output"),
                   help="Output directory (default: ./output)")
    p.add_argument("--skip-ast", action="store_true", help="Skip AST extraction")
    p.add_argument("--skip-ts", action="store_true", help="Skip TypeScript AST extraction")
    p.add_argument("--eval-corpus", help="Ground truth corpus for precision/recall evaluation")
    p.add_argument("--from-corpus", metavar="CORPUS_JSON",
                   help="Skip Phase 0 (extract) and use the 'functions' array from this "
                        "corpus file directly as the catalog. Typically paired with "
                        "--eval-corpus pointing at the same file for end-to-end P/R/F1.")
    p.add_argument("-c", "--context", type=int, default=15, help="Lines of context for regex")
    p.add_argument("--strict", action="store_true",
                   help="Kept for backward compatibility. As of the strict-by-default "
                        "change, strict mode is the default — this flag is a no-op but "
                        "is still accepted so existing callers do not break.")
    p.add_argument("--permissive", action="store_true",
                   help="Opt in to the old tolerant behavior: log warnings on phase "
                        "failures (extract, detect, merge, report, evaluate) and exit 0 "
                        "anyway. Use only for scripted sweeps over many trees where "
                        "one broken tree should not halt the batch.")
    p.add_argument("--lock-file", default=DEFAULT_LOCK_PATH,
                   help=f"Path to the cross-process lock file (default: {DEFAULT_LOCK_PATH}). "
                        "Two run_pipeline.py invocations sharing this path are mutually exclusive.")
    p.add_argument("--wait", action="store_true",
                   help="Block waiting for the lock instead of failing fast on conflict.")
    p.add_argument("--jobs", type=int, default=None,
                   help="Maximum concurrent detector processes. "
                        "Default: min(4, cpu_count//2). Override via "
                        "SDLC_OS_DETECTOR_JOBS env var.")
    p.add_argument("--ignore-preflight", action="store_true",
                   help="Bypass the memory pressure preflight check. "
                        "Use only when you know the system has headroom.")
    p.add_argument("--suppress", nargs="*",
                   default=["selfcontained_wrappers", "storage_error_factories", "crud_boilerplate"],
                   help="Noise suppression rules (default: selfcontained_wrappers storage_error_factories crud_boilerplate)")
    p.add_argument("--actionable-only", action="store_true",
                   help="Emit only Type 1/2 HIGH confidence pairs after suppression")
    return p.parse_args()


def main():
    args = parse_args()
    if not args.source and not args.from_corpus:
        print("Error: either positional source directory or --from-corpus is required",
              file=sys.stderr)
        sys.exit(2)
    # Strict-by-default: any phase failure exits non-zero unless the
    # caller explicitly opts into permissive mode. --strict is still
    # accepted (no-op) for backward compat. If both are passed,
    # --permissive wins because it is the explicit opt-in — but we
    # log a warning so the surprising combination is visible.
    if args.strict and args.permissive:
        log("  WARNING: --strict is a no-op (strict is the default); "
            "--permissive takes effect. Drop --strict to silence this.")
    strict_mode = not args.permissive
    src = os.path.abspath(args.source) if args.source else None
    out = os.path.abspath(args.output_dir)
    extract_dir = os.path.join(out, "extract")
    detect_dir = os.path.join(out, "detect")
    merge_dir = os.path.join(out, "merge")
    log_file = os.path.join(out, "pipeline.log")

    if args.from_corpus:
        if not os.path.isfile(args.from_corpus):
            print(f"Error: --from-corpus file not found: {args.from_corpus}", file=sys.stderr)
            sys.exit(1)
    elif src and not os.path.isdir(src):
        print(f"Error: source directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    # ── Acquire pipeline lock ────────────────────────────────────────
    # NB: lock_fd must stay in scope for the rest of main(). Do NOT close
    # it — process exit releases the flock automatically. A refactor that
    # removes "unused" local variables will drop the lock.
    try:
        lock_fd = acquire_pipeline_lock(args.lock_file, wait=args.wait)
    except BlockingIOError:
        # Best-effort holder-pid diagnostic. The read can race with the
        # holder's own ftruncate+write, yielding an empty string; that is
        # cosmetic — the lock-conflict error still fires below.
        holder = ""
        try:
            with open(args.lock_file) as f:
                holder = f" (held by pid {f.read().strip()})"
        except OSError:
            pass
        log(f"ERROR: another run_pipeline.py is already running{holder}. "
            f"Use --wait to block, or pick a different --lock-file.")
        sys.exit(1)

    # ── Memory preflight check ───────────────────────────────────────
    if not args.ignore_preflight:
        ok, reason = check_preflight()
        if ok:
            # Distinguish a real healthy probe from a fail-open "skipped:"
            # result. A skipped probe means the safeguard is absent — the
            # pipeline still proceeds, but the log line must make that
            # visible so it doesn't look like a normal healthy run.
            if reason.startswith("skipped:"):
                log(f"  WARNING Preflight SKIPPED: {reason}")
                log("           Memory pressure probe did not run; "
                    "safeguard is absent. Proceed with care.")
            else:
                log(f"  Preflight OK: {reason}")
        else:
            log(f"ERROR: preflight refused launch: {reason}")
            log(f"       Free memory before retrying, or pass --ignore-preflight "
                f"to bypass (not recommended).")
            sys.exit(1)
    else:
        log("  Preflight: bypassed via --ignore-preflight")

    # ── Setup ────────────────────────────────────────────────────────
    if os.path.exists(out):
        shutil.rmtree(out)
    for d in [extract_dir, detect_dir, merge_dir]:
        os.makedirs(d, exist_ok=True)
    open(log_file, "w").close()

    # ── Phase 0: EXTRACT ─────────────────────────────────────────────
    log("=== Phase 0: EXTRACT ===")

    catalog_files = []
    extract_failures: list[str] = []

    def _record_extract(label: str, exit_code: int, out_file: str) -> None:
        """Record a failure if the extractor exited non-zero or produced no output."""
        if exit_code != 0 or not os.path.exists(out_file):
            extract_failures.append(f"{label} (exit={exit_code}, output={'missing' if not os.path.exists(out_file) else 'present'})")

    if args.from_corpus:
        # Corpus mode: load functions directly from the corpus JSON
        # and skip all three extractors. This enables end-to-end evaluation
        # where the detectors run on the same functions listed in --eval-corpus.
        log(f"  Loading functions from corpus: {args.from_corpus}")
        with open(args.from_corpus) as f:
            corpus_data = json.load(f)
        corpus_functions = corpus_data.get("functions", [])
        catalog_corpus = os.path.join(extract_dir, "catalog-corpus.json")
        with open(catalog_corpus, "w") as f:
            json.dump(corpus_functions, f, indent=2)
        catalog_files.append(catalog_corpus)
        log(f"  Loaded {len(corpus_functions)} functions from corpus")
    else:
        # 0a: Regex extraction (Python implementation — no bash/grep -P needed)
        regex_script = os.path.join(SCRIPTS, "extract-functions-regex.py")
        catalog_regex = os.path.join(extract_dir, "catalog-regex.json")
        if os.path.exists(regex_script):
            r = run([PYTHON, regex_script, "-o", catalog_regex, "-c", str(args.context), src],
                    label="regex-extraction", check=False, log_file=log_file)
            _record_extract("regex-extraction", r.returncode, catalog_regex)
            if os.path.exists(catalog_regex):
                catalog_files.append(catalog_regex)
        else:
            extract_failures.append("regex-extraction (script not found)")

    # 0b: Python AST extraction (skipped in corpus mode)
    if not args.from_corpus and not args.skip_ast:
        ast_py_script = os.path.join(SCRIPTS, "extract-functions-ast-py.py")
        catalog_ast_py = os.path.join(extract_dir, "catalog-ast-py.json")
        if os.path.exists(ast_py_script):
            r = run([PYTHON, ast_py_script, "-o", catalog_ast_py, src],
                    label="ast-py-extraction", check=False, log_file=log_file)
            _record_extract("ast-py-extraction", r.returncode, catalog_ast_py)
            if os.path.exists(catalog_ast_py):
                catalog_files.append(catalog_ast_py)
        else:
            extract_failures.append("ast-py-extraction (script not found)")

    # 0c: TypeScript AST extraction (skipped in corpus mode)
    # Only attempt when the source tree actually contains TS/JS files.
    # This prevents strict mode (the default) from failing on pure Python
    # repos that don't have node installed.
    has_ts_files = False
    if not args.from_corpus and not args.skip_ast and not args.skip_ts and src:
        for root, _, files in os.walk(src):
            if any(
                any(f.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"))
                for f in files
            ):
                has_ts_files = True
                break

    if has_ts_files:
        ast_ts_script = os.path.join(SCRIPTS, "extract-functions-ast-ts.mjs")
        catalog_ast_ts = os.path.join(extract_dir, "catalog-ast-ts.json")
        if not os.path.exists(ast_ts_script):
            extract_failures.append("ast-ts-extraction (script not found)")
        elif not shutil.which("node"):
            extract_failures.append("ast-ts-extraction (node not on PATH)")
        else:
            r = run(["node", ast_ts_script, src, "--output", catalog_ast_ts],
                    label="ast-ts-extraction", check=False, log_file=log_file)
            _record_extract("ast-ts-extraction", r.returncode, catalog_ast_ts)
            if os.path.exists(catalog_ast_ts):
                catalog_files.append(catalog_ast_ts)

    # Merge catalogs — pure Python, no jq dependency
    catalog_unified = os.path.join(extract_dir, "catalog-unified.json")

    if len(catalog_files) == 0:
        with open(catalog_unified, "w") as f:
            json.dump([], f)
    elif len(catalog_files) == 1:
        shutil.copy(catalog_files[0], catalog_unified)
    else:
        # Load all catalogs
        all_entries: list[dict] = []
        for cf in catalog_files:
            with open(cf) as f:
                try:
                    all_entries.extend(json.load(f))
                except json.JSONDecodeError as e:
                    log(f"  WARNING: failed to parse {cf}: {e}")

        # Deduplicate by (file, name, line). When multiple extractors
        # produce the same function, prefer the entry with richer data
        # (AST fingerprint, token sequence, params, etc.).
        by_key: dict[str, dict] = {}
        for entry in all_entries:
            key = f"{entry.get('file', '')}:{entry.get('name', '')}:{entry.get('line', 0)}"
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = entry
            else:
                # Merge: fill in null/empty fields from the new entry
                for k, v in entry.items():
                    if v is not None and v != "" and (existing.get(k) is None or existing.get(k) == ""):
                        existing[k] = v

        merged_catalog = sorted(by_key.values(), key=lambda e: (e.get("file", ""), e.get("line", 0)))
        with open(catalog_unified, "w") as f:
            json.dump(merged_catalog, f, indent=2)

    count = 0
    if os.path.exists(catalog_unified):
        with open(catalog_unified) as f:
            try:
                count = len(json.load(f))
            except json.JSONDecodeError as e:
                log(f"  WARNING: unified catalog parse error: {e}")
    log(f"  Extracted {count} functions into unified catalog")

    if extract_failures:
        log(f"  Extraction issues ({len(extract_failures)}):")
        for msg in extract_failures:
            log(f"    - {msg}")
        if strict_mode:
            log(f"ERROR: strict mode: {len(extract_failures)} extraction step(s) failed or skipped.")
            log(f"       Use --skip-ast or --skip-ts to intentionally omit extractors.")
            sys.exit(2)

    # ── Phase 1: DETECT ──────────────────────────────────────────────
    log("=== Phase 1: DETECT ===")

    detectors = [
        ("detect-fuzzy-names.py",       "fuzzy-name-results.json",       "fuzzy-name"),
        ("detect-signature-match.py",   "signature-match-results.json",  "signature-match"),
        ("detect-token-clones.py",      "token-clone-results.json",      "token-clone"),
        ("detect-ast-similarity.py",    "ast-similarity-results.json",   "ast-similarity"),
        ("detect-metric-similarity.py", "metric-similarity-results.json", "metric-similarity"),
        ("detect-tfidf-index.py",       "tfidf-index-results.json",      "tfidf-index"),
        ("detect-winnowing.py",         "winnowing-results.json",        "winnowing"),
        ("detect-lsh-ast.py",           "lsh-ast-results.json",          "lsh-ast"),
        ("detect-bag-of-ast.py",        "bag-of-ast-results.json",       "bag-of-ast"),
        ("detect-pdg-semantic.py",      "pdg-semantic-results.json",     "pdg-semantic"),
        ("detect-code-embedding.py",    "code-embedding-results.json",   "code-embedding"),
    ]

    max_jobs = _resolve_jobs(args.jobs)
    log(f"  Detector concurrency cap: {max_jobs} parallel jobs")

    def _run_one_detector(script_path: str, out_file: str, label: str) -> tuple[str, str, int]:
        """Run a single detector subprocess and return (label, out_file, returncode)."""
        # NB: pipeline.log is opened by every worker thread concurrently
        # with max_jobs active workers. stderr from different detectors
        # can interleave here when writes exceed PIPE_BUF. The byte
        # determinism tests cover the structured log lines written by
        # log() on the main thread, not this fd. If readable per-detector
        # stderr matters, future work should write to temp files and
        # concatenate in collect-order.
        with open(log_file, "a") as lf:
            cp = subprocess.run(
                [PYTHON, script_path, catalog_unified, "-o", out_file],
                stderr=lf, stdout=subprocess.PIPE,
            )
        return label, out_file, cp.returncode

    # Submit all runnable detectors to a bounded executor.
    # We submit in detector-list order; results are collected in the
    # same order so log output stays deterministic across runs.
    skipped = 0
    futures_by_label: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=max_jobs) as ex:
        for script_name, out_name, label in detectors:
            script = os.path.join(SCRIPTS, script_name)
            out_file = os.path.join(detect_dir, out_name)
            if not os.path.exists(script):
                skipped += 1
                log(f"  SKIP {label}: script not found")
                continue
            log(f"  Submitting {label}...")
            assert label not in futures_by_label, (
                f"Duplicate detector label {label!r}: detectors list has a "
                f"copy-paste collision. Fix the detectors table above."
            )
            futures_by_label[label] = ex.submit(
                _run_one_detector, script, out_file, label
            )

        # Collect in detector-list order to preserve deterministic log lines
        failures = 0
        for _, _, label in detectors:
            fut = futures_by_label.get(label)
            if fut is None:
                continue
            try:
                label_out, out_file, rc = fut.result()
            except Exception as exc:
                # A worker raised something we did not anticipate — count it
                # as a detector failure so the pipeline still emits
                # "Detection complete" and the strict-mode gate still fires.
                failures += 1
                log(f"  ERROR: {label} raised {type(exc).__name__}: {exc}")
                continue
            if rc != 0:
                failures += 1
                log(f"  WARNING: {label_out} failed (exit {rc})")
            else:
                n = 0
                if os.path.exists(out_file):
                    with open(out_file) as f:
                        try:
                            n = len(json.load(f))
                        except json.JSONDecodeError as e:
                            log(f"  WARNING: {label_out} output parse error: {e}")
                log(f"  {label_out}: {n} candidate pairs")

    log(f"  Detection complete ({failures} failures, {skipped} skipped)")

    if strict_mode and (failures > 0 or skipped > 0):
        log(f"ERROR: strict mode: {failures} detector(s) failed, {skipped} skipped. See {log_file}")
        sys.exit(2)

    # ── Phase 2: MERGE ───────────────────────────────────────────────
    log("=== Phase 2: MERGE ===")

    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    merged_out = os.path.join(merge_dir, "merged-results.json")
    merge_cmd = [PYTHON, merge_script, detect_dir, "-o", merged_out, "--include-summary"]
    if args.suppress:
        merge_cmd += ["--suppress"] + args.suppress
    if args.actionable_only:
        merge_cmd += ["--actionable-only"]
    merge_result = run(
        merge_cmd,
        label="merge-signals", check=False, log_file=log_file
    )
    if merge_result.returncode != 0:
        _strict_gate("merge phase", f"merge-signals exited {merge_result.returncode}", strict_mode, log_file)
    elif not os.path.exists(merged_out):
        _strict_gate("merge phase", "merge-signals produced no output", strict_mode)

    if os.path.exists(merged_out):
        with open(merged_out) as f:
            merged = json.load(f)
        summary = merged.get("summary", {})
        total = summary.get("total_pairs", 0)
        by_conf = summary.get("by_confidence", {})
        log(f"  {total} pairs: {by_conf.get('HIGH', 0)} HIGH, "
            f"{by_conf.get('MEDIUM', 0)} MEDIUM, {by_conf.get('LOW', 0)} LOW")

    # ── Phase 3: REPORT ──────────────────────────────────────────────
    log("=== Phase 3: REPORT ===")

    report_script = os.path.join(SCRIPTS, "generate-report-enhanced.sh")
    report_out = os.path.join(out, "duplicates-report.md")
    if os.path.exists(report_script):
        report_result = run(["bash", report_script, merged_out, report_out],
                            label="generate-report", check=False, log_file=log_file)
        if report_result.returncode != 0:
            _strict_gate("report phase", f"generate-report exited {report_result.returncode}", strict_mode, log_file)
        elif not os.path.exists(report_out):
            _strict_gate("report phase", "generate-report produced no output", strict_mode)
        else:
            log(f"  Report: {report_out}")
    else:
        _strict_gate("report phase", f"report generator missing at {report_script}", strict_mode)

    # ── Phase 4: EVALUATE (optional) ─────────────────────────────────
    if args.eval_corpus:
        log("=== Phase 4: EVALUATE ===")
        eval_script = os.path.join(SCRIPTS, "evaluate.py")
        eval_out = os.path.join(out, "evaluation.json")
        if not os.path.exists(eval_script):
            _strict_gate("evaluate phase", f"evaluate.py not found at {eval_script}", strict_mode)
        elif not os.path.exists(merged_out):
            _strict_gate("evaluate phase", f"merged results not found at {merged_out}", strict_mode)
        else:
            eval_result = run(
                [PYTHON, eval_script,
                 "--results", merged_out,
                 "--corpus", args.eval_corpus,
                 "-o", eval_out],
                label="evaluate", check=False, log_file=log_file
            )
            if eval_result.returncode != 0:
                _strict_gate("evaluate phase", f"evaluate exited {eval_result.returncode}", strict_mode)
            if os.path.exists(eval_out):
                with open(eval_out) as f:
                    ev = json.load(f)
                overall = ev.get("overall", ev)
                p = overall.get("precision", 0)
                r = overall.get("recall", 0)
                f1 = overall.get("f1", 0)
                log(f"  Precision: {p:.3f}  Recall: {r:.3f}  F1: {f1:.3f}")
            else:
                _strict_gate("evaluate phase", "evaluation produced no output", strict_mode)

    log("=== COMPLETE ===")
    log(f"Results: {merged_out}")


if __name__ == "__main__":
    main()
