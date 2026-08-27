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
import uuid
from concurrent.futures import ThreadPoolExecutor

from safety import (
    DEFAULT_LOCK_PATH,
    acquire_pipeline_lock,
    check_output_capacity,
    check_preflight,
)
from pipeline_runtime import (
    AbortInProgress,
    CensusOutcome,
    IdentityUnproven,
    ManagedRunPublisher,
    ProcessIdentity,
    SpawnCoordinator,
)

__all__ = [
    "AbortInProgress",
    "CensusOutcome",
    "IdentityUnproven",
    "ManagedRunPublisher",
    "ProcessIdentity",
    "SpawnCoordinator",
    "main",
]

PYTHON = sys.executable  # Use the same interpreter that launched this script

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(BASE, "scripts")


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run(cmd, label="", check=True, log_file=None):
    log(f"  Running: {label or ' '.join(str(c) for c in cmd[:3])}")
    if _COORDINATOR is None:
        raise RuntimeError("spawn coordinator is not initialized")
    if log_file:
        with open(log_file, "a") as lf:
            result = _COORDINATOR.run(
                cmd, stderr=lf, stdout=subprocess.PIPE, text=True,
                timeout=_COMMAND_TIMEOUT_S)
    else:
        result = _COORDINATOR.run(
            cmd, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True,
            timeout=_COMMAND_TIMEOUT_S)
    if check and result.returncode != 0:
        log(f"  WARNING: {label} exited {result.returncode}")
    return result


def _strict_gate(phase: str, message: str, strict: bool, log_file: str = "") -> bool:
    """Log an error and exit 2 if strict mode is active.

    Strict mode is the default; callers pass ``strict=False`` to opt into
    permissive behavior via the --permissive flag.
    """
    log(f"  ERROR: {message}")
    if strict:
        suffix = f" See {log_file}" if log_file else ""
        log(f"ERROR: strict mode: {phase} failed.{suffix}")
        sys.exit(2)
    return True


# Maximum detector parallelism regardless of CPU count. Each detector can
# use multi-GB RSS, so this intentionally flattens on large machines.
# Adjust here (one place) if per-detector RSS drops in Phase 2/3 of the
# OOM safety work.
MAX_DETECTOR_JOBS = 4
MAX_DETECTOR_TIMEOUT_S = 300


def _resolve_detector_timeout() -> int:
    """Allow tests/operators to lower, but never raise, the detector wall cap."""
    raw = os.environ.get("DEDUP_DETECTOR_TIMEOUT_S", "").strip()
    if not raw:
        return MAX_DETECTOR_TIMEOUT_S
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(
            "DEDUP_DETECTOR_TIMEOUT_S must be a finite positive integer") from None
    if value <= 0 or value > MAX_DETECTOR_TIMEOUT_S:
        raise ValueError(
            "DEDUP_DETECTOR_TIMEOUT_S must be between 1 and the immutable "
            f"hard cap {MAX_DETECTOR_TIMEOUT_S}")
    return value


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
        if cli_jobs > MAX_DETECTOR_JOBS:
            raise ValueError(
                f"jobs={cli_jobs} exceeds immutable hard cap {MAX_DETECTOR_JOBS}")
        return cli_jobs
    env = os.environ.get("SDLC_OS_DETECTOR_JOBS", "").strip()
    if env.isdigit() and int(env) > 0:
        if int(env) > MAX_DETECTOR_JOBS:
            raise ValueError(
                f"SDLC_OS_DETECTOR_JOBS exceeds immutable hard cap {MAX_DETECTOR_JOBS}")
        return int(env)
    return _default_jobs()


def _positive_int(value: str) -> int:
    """argparse type for resource ceilings: finite positive integers only (I3)."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not an integer; ceilings must be finite positive integers") from None
    if n <= 0:
        raise argparse.ArgumentTypeError(
            f"{value!r}: ceilings must be finite positive integers (no unbounded setting exists)")
    return n


def _load_resource_policy_module():
    """Import scripts/lib/resource_policy.py by path (keeps run_pipeline.py's
    only sibling import `safety`, which the shim-runner tests stub)."""
    import importlib.util
    lib_dir = os.path.join(SCRIPTS, "lib")
    path = os.path.join(lib_dir, "resource_policy.py")
    if not os.path.exists(path):
        return None
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    spec = importlib.util.spec_from_file_location("dedup_resource_policy", path)
    mod = importlib.util.module_from_spec(spec)
    # dataclasses (3.12) resolves cls.__module__ through sys.modules — register first.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


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
    p.add_argument("--wait", action="store_true",
                   help=f"Block waiting for the canonical lock ({DEFAULT_LOCK_PATH}) "
                        "instead of failing fast on conflict.")
    p.add_argument("--jobs", type=int, default=None,
                   help="Maximum concurrent detector processes. "
                        "Default: min(4, cpu_count//2). Override via "
                        "SDLC_OS_DETECTOR_JOBS env var.")
    p.add_argument("--suppress", nargs="*",
                   default=["selfcontained_wrappers", "storage_error_factories", "crud_boilerplate"],
                   help="Noise suppression rules (default: selfcontained_wrappers storage_error_factories crud_boilerplate)")
    p.add_argument("--actionable-only", action="store_true",
                   help="Emit only Type 1/2 HIGH confidence pairs after suppression")
    # ── Finite resource policy (2026-08-22 incident: unbounded merge/report) ──
    rp = p.add_argument_group("resource policy (every ceiling is a finite positive integer)")
    rp.add_argument("--resource-policy", choices=("refuse", "truncate"), default="refuse",
                    help="On a ceiling breach: refuse (exit 3, nothing partial) or truncate "
                         "(keep top-ranked rows, record the drop). Default: %(default)s")
    rp.add_argument("--max-pairs", type=_positive_int, default=None,
                    help="Max pairs emitted by merge (default: policy default 200000)")
    rp.add_argument("--max-input-bytes", type=_positive_int, default=None,
                    help="Max total detector-output bytes accepted by merge (default 1 GiB)")
    rp.add_argument("--max-output-bytes", type=_positive_int, default=None,
                    help="Max pairs.jsonl bytes (default 1 GiB)")
    rp.add_argument("--max-legacy-json-bytes", type=_positive_int, default=None,
                    help="Write merge/merged-results.json only under this size (default 200 MiB)")
    rp.add_argument("--no-legacy-json", action="store_true",
                    help="Never write the legacy merged-results.json")
    rp.add_argument("--max-report-rows", type=_positive_int, default=None,
                    help="Rows per report section; omissions are stated (default 500)")
    rp.add_argument("--max-wall-seconds", type=_positive_int, default=None,
                    help="Whole-pipeline wall clock ceiling (default 1800)")
    rp.add_argument("--max-tree-rss-bytes", type=_positive_int, default=None,
                    help="Runner + all descendants sampled RSS ceiling (default 6 GiB)")
    return p.parse_args()


def _main_impl():
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
    semantic_failures: list[str] = []
    try:
        detector_timeout_s = _resolve_detector_timeout()
    except ValueError as exc:
        log(f"ERROR: {exc}")
        sys.exit(2)
    src = os.path.abspath(args.source) if args.source else None
    if ".." in os.path.expanduser(args.output_dir).split(os.sep):
        log("ERROR: managed output root contains a parent traversal")
        sys.exit(2)
    output_root = os.path.abspath(args.output_dir)
    if src is not None:
        source_identity = os.path.realpath(src)
        output_identity = os.path.realpath(output_root)
        common = os.path.commonpath((source_identity, output_identity))
        if common in {source_identity, output_identity}:
            log("ERROR: source and managed output root must not overlap")
            sys.exit(2)

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
        _lock_fd = acquire_pipeline_lock(DEFAULT_LOCK_PATH, wait=args.wait)
    except BlockingIOError:
        # Best-effort holder-pid diagnostic. The read can race with the
        # holder's own ftruncate+write, yielding an empty string; that is
        # cosmetic — the lock-conflict error still fires below.
        holder = ""
        try:
            with open(DEFAULT_LOCK_PATH) as f:
                holder = f" (held by pid {f.read().strip()})"
        except OSError:
            pass
        log(f"ERROR: another run_pipeline.py is already running{holder}. "
            "Use --wait to block; the canonical global lock is not overridable.")
        sys.exit(1)

    # ── Memory preflight check ───────────────────────────────────────
    ok, reason = check_preflight()
    if not ok:
        log(f"ERROR: preflight refused launch: {reason}")
        sys.exit(1)
    log(f"  Preflight OK: {reason}")

    # ── Resource policy, run record, process-tree watchdog ───────────
    global _FINALIZE
    global _COMMAND_TIMEOUT_S
    rpmod = _load_resource_policy_module()
    policy = None
    if rpmod is None:
        log("ERROR: resource policy module missing (scripts/lib/resource_policy.py): "
            "caps and the process-tree watchdog are unavailable")
        sys.exit(2)
    else:
        try:
            policy = rpmod.ResourcePolicy.defaults().with_overrides(
                mode=args.resource_policy, max_pairs=args.max_pairs,
                max_input_bytes=args.max_input_bytes, max_output_bytes=args.max_output_bytes,
                max_legacy_json_bytes=args.max_legacy_json_bytes,
                max_report_rows=args.max_report_rows, max_wall_seconds=args.max_wall_seconds,
                max_tree_rss_bytes=args.max_tree_rss_bytes)
        except rpmod.PolicyError as exc:
            log(f"ERROR: resource policy: {exc} (ceilings must be finite)")
            sys.exit(2)
        log(f"  Resource policy: mode={policy.mode} max_pairs={policy.max_pairs} "
            f"max_tree_rss={policy.max_tree_rss_bytes} max_wall={policy.max_wall_seconds}s")
        _COMMAND_TIMEOUT_S = policy.max_wall_seconds

    # ── Setup ────────────────────────────────────────────────────────
    capacity_ok, capacity_reason = check_output_capacity(output_root)
    if not capacity_ok:
        log(f"ERROR: output admission refused: {capacity_reason}")
        sys.exit(1)
    log(f"  Output admission OK: {capacity_reason}")
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex
    publisher = ManagedRunPublisher(output_root, run_id=run_id)
    try:
        out = str(publisher.begin())
    except (OSError, ValueError) as exc:
        log(f"ERROR: managed output admission failed: {exc}")
        sys.exit(2)
    extract_dir = os.path.join(out, "extract")
    detect_dir = os.path.join(out, "detect")
    merge_dir = os.path.join(out, "merge")
    log_file = os.path.join(out, "pipeline.log")
    for d in [extract_dir, detect_dir, merge_dir]:
        os.makedirs(d, exist_ok=True)
    open(log_file, "w").close()

    run_json = os.path.join(out, "run.json")
    record = rpmod.RunRecord.start(policy=policy, base_dir=BASE,
                                   extra={"tool": "run_pipeline",
                                          "managed_output_root": output_root,
                                          "managed_run_id": run_id,
                                          "published_relative_path": f"runs/{run_id}",
                                          "source": src, "from_corpus": args.from_corpus,
                                          "strict": strict_mode}) if rpmod else None
    abort_box: dict = {}
    global _COORDINATOR
    _COORDINATOR = SpawnCoordinator()
    watchdog = None
    if rpmod is not None:
        watchdog = rpmod.TreeWatchdog(
            root_pid=os.getpid(), max_tree_rss_bytes=policy.max_tree_rss_bytes,
            max_wall_seconds=policy.max_wall_seconds, interval_s=1.0,
            on_abort=lambda ev: abort_box.update(ev),
            cleanup_handler=lambda reason: _COORDINATOR.abort(reason),
            output_root=out,
            max_run_output_bytes=policy.max_run_output_bytes,
            max_tree_processes=policy.max_tree_processes)
        watchdog.start()

    def _peak() -> dict | None:
        if watchdog is None:
            return None
        if watchdog.samples == 0:
            return rpmod.sample_tree(os.getpid())
        return {"rss_bytes": watchdog.peak_tree_rss_bytes,
                "process_count": watchdog.peak_process_count,
                "samples": watchdog.samples, "footprint_bytes": None,
                "footprint_status": "unavailable"}

    def _artifacts() -> dict:
        return {
            "pipeline.log": log_file,
            "pairs.jsonl": os.path.join(merge_dir, "pairs.jsonl"),
            "summary.json": os.path.join(merge_dir, "summary.json"),
            "merged-results.json": os.path.join(merge_dir, "merged-results.json"),
            "duplicates-report.md": os.path.join(out, "duplicates-report.md"),
        }

    finalized: dict = {}

    def _finalize(outcome: str, **extra) -> None:
        """Write run.json exactly once; the first (most specific) outcome wins."""
        if record is None or finalized:
            return
        finalized["outcome"] = outcome
        if watchdog is not None:
            watchdog.stop()
        record.finish(outcome=outcome, artifacts=_artifacts(), peak=_peak(), **extra)
        for metadata in record.data.get("artifacts", {}).values():
            path = metadata.get("path") if isinstance(metadata, dict) else None
            if path and os.path.commonpath((out, path)) == out:
                metadata["path"] = os.path.relpath(path, out)
        try:
            record.write(run_json)
        except OSError as exc:
            log(f"  WARNING: could not write run.json: {exc}")
            try:
                publisher.mark_incomplete("run-record-write-failed")
            except OSError:
                pass
            raise
        if outcome == "complete":
            hashes = {
                name: data["sha256"]
                for name, data in record.data.get("artifacts", {}).items()
                if isinstance(data, dict) and data.get("sha256")
            }
            try:
                publisher.publish_complete(hashes)
            except Exception as exc:
                record.data["outcome"] = "publication_failed"
                record.note_error(f"latest pointer publication failed: {type(exc).__name__}")
                if publisher.work_path.is_dir():
                    record.write(run_json)
                raise
        else:
            publisher.mark_incomplete(outcome)

    def _check_abort(where: str) -> None:
        """Exit 3 with outcome resource_abort if the watchdog fired."""
        active_abort = (
            watchdog.aborted if watchdog is not None and watchdog.aborted is not None
            else abort_box
        )
        if active_abort:
            if watchdog is not None:
                active_abort = watchdog.wait_abort(5.0) or active_abort
            log(f"ERROR: RESOURCE_ABORT during {where}: {active_abort.get('reason')} "
                f"(peak tree RSS {active_abort.get('peak_tree_rss_bytes')} bytes; "
                f"signaled {active_abort.get('signaled_pids')})")
            _finalize("resource_abort", extra={"abort": dict(active_abort)})
            sys.exit(3)

    _FINALIZE = _finalize
    _check_abort("startup")

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
    if record is not None:
        record.note_phase("extract", {"functions": count, "failures": list(extract_failures)})

    if extract_failures:
        log(f"  Extraction issues ({len(extract_failures)}):")
        for msg in extract_failures:
            log(f"    - {msg}")
        if strict_mode:
            log(f"ERROR: strict mode: {len(extract_failures)} extraction step(s) failed or skipped.")
            log("       Use --skip-ast or --skip-ts to intentionally omit extractors.")
            sys.exit(2)
        semantic_failures.append("extract")

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

    _check_abort("extract phase")
    try:
        max_jobs = _resolve_jobs(args.jobs)
    except ValueError as exc:
        log(f"ERROR: {exc}")
        sys.exit(2)
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
        if abort_box:
            # 2026-08-24 red-team finding: the watchdog killed the first
            # detector wave, but futures still queued in the executor then
            # started fresh subprocesses. A worker that begins after the
            # abort latch is set must not spawn anything.
            return label, out_file, -1
        with open(log_file, "a") as lf:
            try:
                cp = _COORDINATOR.run(
                    [PYTHON, script_path, catalog_unified, "-o", out_file],
                    stderr=lf, stdout=subprocess.PIPE,
                    timeout=detector_timeout_s,
                )
                rc = cp.returncode
            except subprocess.TimeoutExpired:
                lf.write(
                    f"\n[{label}] TIMEOUT after {detector_timeout_s}s - counted as failure\n"
                )
                rc = 124
        return label, out_file, rc

    # Submit all runnable detectors to a bounded executor.
    # We submit in detector-list order; results are collected in the
    # same order so log output stays deterministic across runs.
    skipped = 0
    futures_by_label: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=max_jobs) as ex:
        for script_name, out_name, label in detectors:
            if abort_box:
                log("  ABORT: watchdog fired; not submitting remaining detectors")
                break
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
            if abort_box:
                # Cancel queued futures outright; already-running workers see
                # the abort latch at their next spawn point (guard above).
                cancelled = sum(
                    1 for f in futures_by_label.values() if f.cancel()
                )
                if cancelled:
                    log(f"  ABORT: cancelled {cancelled} queued detector(s)")
            fut = futures_by_label.get(label)
            if fut is None:
                continue
            if fut.cancelled():
                failures += 1
                log(f"  ABORTED: {label} cancelled before start (resource abort)")
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
            if rc == -1:
                failures += 1
                log(f"  ABORTED: {label_out} not started (resource abort)")
            elif rc != 0:
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
        if abort_box:
            ex.shutdown(wait=True, cancel_futures=True)

    log(f"  Detection complete ({failures} failures, {skipped} skipped)")
    _check_abort("detect phase")
    if record is not None:
        record.note_phase("detect", {"failures": failures, "skipped": skipped, "jobs": max_jobs})

    if strict_mode and (failures > 0 or skipped > 0):
        log(f"ERROR: strict mode: {failures} detector(s) failed, {skipped} skipped. See {log_file}")
        sys.exit(2)
    if not strict_mode and (failures > 0 or skipped > 0):
        semantic_failures.append("detect")

    # ── Phase 2: MERGE ───────────────────────────────────────────────
    log("=== Phase 2: MERGE ===")

    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    merged_out = os.path.join(merge_dir, "merged-results.json")
    pairs_out = os.path.join(merge_dir, "pairs.jsonl")
    summary_out = os.path.join(merge_dir, "summary.json")
    merge_cmd = [PYTHON, merge_script, detect_dir, "-o", merged_out, "--include-summary"]
    if args.suppress:
        merge_cmd += ["--suppress"] + args.suppress
    if args.actionable_only:
        merge_cmd += ["--actionable-only"]
    if policy is not None:
        merge_cmd += ["--resource-policy", policy.mode,
                      "--max-pairs", str(policy.max_pairs),
                      "--max-input-bytes", str(policy.max_input_bytes),
                      "--max-output-bytes", str(policy.max_output_bytes),
                      "--max-legacy-json-bytes", str(policy.max_legacy_json_bytes)]
    if args.no_legacy_json:
        merge_cmd.append("--no-legacy-json")
    merge_result = run(
        merge_cmd,
        label="merge-signals", check=False, log_file=log_file
    )
    _check_abort("merge phase")
    if merge_result.returncode == 3:
        detail = ""
        try:
            with open(os.path.join(merge_dir, "run.json")) as f:
                ref = json.load(f).get("refusal", {})
            detail = f"{ref.get('reason')}: {ref.get('detail')}"
        except (OSError, ValueError):
            detail = f"see {log_file}"
        log(f"ERROR: REFUSED_RESOURCE: merge-signals refused the run ({detail})")
        log("       Raise the ceiling explicitly or pass --resource-policy truncate.")
        _finalize("refused_resource", extra={"refusal": detail})
        sys.exit(3)
    if merge_result.returncode != 0:
        if _strict_gate("merge phase", f"merge-signals exited {merge_result.returncode}", strict_mode, log_file):
            semantic_failures.append("merge")
    elif not os.path.exists(pairs_out) or not os.path.exists(summary_out):
        if _strict_gate("merge phase", "merge-signals produced no pairs.jsonl/summary.json", strict_mode):
            semantic_failures.append("merge")

    summary = {}
    if os.path.exists(summary_out):
        # Only the small sidecar is read here — never the merged document itself
        # (a 2.05 GB json.load of it was half of the 2026-08-22 incident).
        with open(summary_out) as f:
            summary = json.load(f)
        total = summary.get("total_pairs", 0)
        by_conf = summary.get("by_confidence", {})
        log(f"  {total} pairs: {by_conf.get('HIGH', 0)} HIGH, "
            f"{by_conf.get('MEDIUM', 0)} MEDIUM, {by_conf.get('LOW', 0)} LOW")
        if summary.get("complete") is False:
            log(f"  TRUNCATED: {summary.get('truncation_reason')}; "
                f"{summary.get('pairs_dropped', 0)} pair(s) dropped (of {summary.get('candidates_total')})")
        if not os.path.exists(merged_out):
            log("  Legacy merged-results.json not written (above size ceiling or disabled); "
                "consumers must read pairs.jsonl")
    if record is not None:
        merge_counts = {}
        try:
            with open(os.path.join(merge_dir, "run.json")) as f:
                merge_counts = json.load(f).get("counts", {})
        except (OSError, ValueError):
            pass
        record.note_phase("merge", dict(merge_counts, exit_code=merge_result.returncode,
                                        truncated=summary.get("complete") is False))
        if summary.get("complete") is False:
            record.data["truncated"] = True
            record.data["truncation_reason"] = summary.get("truncation_reason")

    # ── Phase 3: REPORT ──────────────────────────────────────────────
    log("=== Phase 3: REPORT ===")

    report_script = os.path.join(SCRIPTS, "generate-report-enhanced.sh")
    report_out = os.path.join(out, "duplicates-report.md")
    if os.path.exists(report_script):
        report_cmd = ["bash", report_script, merge_dir, report_out]
        if policy is not None:
            report_cmd += ["--max-rows-per-section", str(policy.max_report_rows)]
        report_result = run(report_cmd, label="generate-report", check=False, log_file=log_file)
        _check_abort("report phase")
        if record is not None:
            record.note_phase("report", {"exit_code": report_result.returncode, "path": report_out})
        if report_result.returncode != 0:
            if _strict_gate("report phase", f"generate-report exited {report_result.returncode}", strict_mode, log_file):
                semantic_failures.append("report")
        elif not os.path.exists(report_out):
            if _strict_gate("report phase", "generate-report produced no output", strict_mode):
                semantic_failures.append("report")
        else:
            log(f"  Report: {report_out}")
    else:
        if _strict_gate("report phase", f"report generator missing at {report_script}", strict_mode):
            semantic_failures.append("report")

    # ── Phase 4: EVALUATE (optional) ─────────────────────────────────
    if args.eval_corpus:
        log("=== Phase 4: EVALUATE ===")
        eval_script = os.path.join(SCRIPTS, "evaluate.py")
        eval_out = os.path.join(out, "evaluation.json")
        if not os.path.exists(eval_script):
            if _strict_gate("evaluate phase", f"evaluate.py not found at {eval_script}", strict_mode):
                semantic_failures.append("evaluate")
        elif not os.path.exists(pairs_out):
            if _strict_gate("evaluate phase", f"merged results not found at {pairs_out}", strict_mode):
                semantic_failures.append("evaluate")
        else:
            eval_result = run(
                [PYTHON, eval_script,
                 "--results", merge_dir,
                 "--corpus", args.eval_corpus,
                 "-o", eval_out],
                label="evaluate", check=False, log_file=log_file
            )
            if eval_result.returncode != 0:
                if _strict_gate("evaluate phase", f"evaluate exited {eval_result.returncode}", strict_mode):
                    semantic_failures.append("evaluate")
            if os.path.exists(eval_out):
                with open(eval_out) as f:
                    ev = json.load(f)
                overall = ev.get("overall", ev)
                p = overall.get("precision", 0)
                r = overall.get("recall", 0)
                f1 = overall.get("f1", 0)
                log(f"  Precision: {p:.3f}  Recall: {r:.3f}  F1: {f1:.3f}")
            else:
                if _strict_gate("evaluate phase", "evaluation produced no output", strict_mode):
                    semantic_failures.append("evaluate")

    log("=== COMPLETE ===")
    log(f"Results: {pairs_out} (+ {summary_out}"
        f"{'; legacy ' + merged_out if os.path.exists(merged_out) else ''})")
    if semantic_failures:
        failures_seen = sorted(set(semantic_failures))
        log("  Permissive semantic failures retained as an incomplete run: "
            + ", ".join(failures_seen))
        _FINALIZE("semantic_incomplete", extra={"semantic_failures": failures_seen})
        _FINALIZE = None


_FINALIZE = None  # set by _main_impl once the run record exists
_COORDINATOR = None
_COMMAND_TIMEOUT_S = 1800


def main():
    """Run the pipeline; every exit path leaves a run.json with its outcome."""
    global _FINALIZE
    _FINALIZE = None
    try:
        _main_impl()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if _FINALIZE is not None and code not in (0, None):
            outcome = {2: "strict_failure", 3: "resource_limit"}.get(code, "error")
            try:
                _FINALIZE(outcome, extra={"exit_code": code})
            except Exception as exc:
                log(f"ERROR: failed to publish terminal run evidence: {exc}")
                raise SystemExit(125) from exc
        raise
    except BaseException as exc:
        if _FINALIZE is not None:
            try:
                outcome = (
                    "resource_limit"
                    if isinstance(exc, subprocess.TimeoutExpired)
                    else "internal_error"
                )
                _FINALIZE(
                    outcome,
                    extra={"error_type": type(exc).__name__,
                           "cleanup": "uncertain"},
                )
            except Exception as final_exc:
                log(f"ERROR: failed to publish internal-error evidence: {final_exc}")
                raise SystemExit(125) from final_exc
        raise
    else:
        if _FINALIZE is not None:
            _FINALIZE("complete")


if __name__ == "__main__":
    main()
