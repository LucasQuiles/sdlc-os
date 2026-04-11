#!/bin/bash
set -euo pipefail

# ast-checks.sh — Deterministic AST analysis via eslint rules
# Operationalizes AST tier from references/deterministic-checks.md
#
# Usage (CLI): ast-checks.sh [--check CHECK_ID] FILE...
# Usage (hook): ast-checks.sh [--check CHECK_ID]   (reads file_path from stdin JSON)
#   --check MAINT-001  cyclomatic complexity only
#   --check REL-005    dead code / unreachable code only
#   --check MAINT-003  god class / file length only
#   --check PERF-001   loop analysis (async-in-loop proxy) only
#   --check ALL        all checks (default)
#
# When no FILE args are given, reads hook JSON from stdin using
# read_hook_stdin's 2s alarm guard and
# extracts .tool_input.file_path. If stdin is empty or no file path, exits 0
# with SKIP — safe for both hook and CLI invocation.
#
# Requires: bash 3.2+, jq (for hook mode only). eslint is resolved from the
# target file's ancestor node_modules/.bin or from PATH — see ast-common.sh.
# Supports: .ts, .tsx, .js, .jsx files (others skipped silently)
#
# Exit 0 + JSON on stdout = results or diagnostic:
#   {"status":"CLEAN",...}        — no findings
#   {"status":"FINDINGS",...}     — lint findings to report
#   {"status":"SKIP",...}         — no analyzable files in input
#   {"status":"UNAVAILABLE",...}  — eslint missing or incompatible (fail-open)
# Exit 2 = invocation/argument error only (reserved for unrecoverable CLI misuse)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/ast-common.sh"

# --- Argument Parsing ---

CHECK_ID="ALL"
FILES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      shift
      if [[ $# -eq 0 ]]; then
        echo '{"status": "UNAVAILABLE", "reason": "--check requires a value"}' >&2
        exit 2
      fi
      CHECK_ID="$1"
      shift
      ;;
    --)
      shift
      FILES+=("$@")
      break
      ;;
    -*)
      echo "{\"status\": \"UNAVAILABLE\", \"reason\": \"unknown option: $1\"}" >&2
      exit 2
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# Validate check ID
case "$CHECK_ID" in
  MAINT-001|REL-005|MAINT-003|PERF-001|ALL) ;;
  *)
    printf '{"status": "UNAVAILABLE", "reason": "unknown check: %s — valid: MAINT-001, REL-005, MAINT-003, PERF-001, ALL"}\n' "$CHECK_ID" >&2
    exit 2
    ;;
esac

# --- Hook Mode: if no FILE args, try reading file_path from stdin JSON ---
#
# Consumer contract: distinguish three cases when no FILE args are provided:
#   (a) Hook-mode plumbing broken (missing common.sh, jq, or perl) → UNAVAILABLE
#   (b) Stdin has valid JSON with a file_path → use it (falls through to filter)
#   (c) Stdin is empty or JSON has no file_path → SKIP (caller passed unrelated event)
# Only (a) should be UNAVAILABLE — (b) and (c) continue to the filter, which may
# then SKIP on non-analyzable extensions.

if [[ ${#FILES[@]} -eq 0 ]]; then
  HOOK_LIB="${SCRIPT_DIR}/../hooks/lib/common.sh"

  if [[ ! -f "$HOOK_LIB" ]]; then
    printf '{"status":"UNAVAILABLE","reason":"hook-mode plumbing missing: %s not found"}\n' "$HOOK_LIB"
    exit 0
  fi
  if ! command -v jq &>/dev/null; then
    printf '{"status":"UNAVAILABLE","reason":"hook-mode plumbing missing: jq not in PATH"}\n'
    exit 0
  fi
  if ! command -v perl &>/dev/null; then
    printf '{"status":"UNAVAILABLE","reason":"hook-mode plumbing missing: perl not in PATH — required by read_hook_stdin"}\n'
    exit 0
  fi

  # shellcheck source=/dev/null
  source "$HOOK_LIB"

  # read_hook_stdin exits 1 on empty stdin — that is legitimately SKIP (case c),
  # not UNAVAILABLE. Exit 2 indicates the guard itself failed, which is
  # plumbing-broken UNAVAILABLE (case a).
  if HOOK_INPUT=$(read_hook_stdin 2>/dev/null); then
    HOOK_FILE=$(read_hook_file_path "$HOOK_INPUT")
    if [[ -n "$HOOK_FILE" ]]; then
      FILES+=("$HOOK_FILE")
    fi
    # If HOOK_FILE was empty, FILES stays empty and we fall through to SKIP —
    # this is case (c): caller passed a hook event with no file_path (correct).
  else
    hook_rc=$?
    if [[ "$hook_rc" -ge 2 ]]; then
      printf '{"status":"UNAVAILABLE","reason":"hook-mode stdin read failed"}\n'
      exit 0
    fi
  fi
  # If read_hook_stdin returned non-zero (empty stdin), FILES stays empty and
  # we fall through to SKIP — also case (c), also correct.
fi

# --- File Filtering (before preflight: bail fast on non-code files) ---

# POSIX-compatible alternative to mapfile (bash 4+ only, macOS ships 3.2)
ANALYZABLE=()
while IFS= read -r line; do
  ANALYZABLE+=("$line")
done < <(filter_analyzable_files "${FILES[@]+"${FILES[@]}"}")

if [[ ${#ANALYZABLE[@]} -eq 0 ]]; then
  printf '{"status": "SKIP", "reason": "no analyzable files"}\n'
  exit 0
fi

# --- Preflight (only reached if we have analyzable files) ---

# Pass the first analyzable file so check_eslint_available can locate a project-local
# eslint via node_modules walk. Fail-open (exit 0) if eslint is unavailable — this is
# a PostToolUse hook and should never block writes when the tool is missing.
#
# Consumer contract: UNAVAILABLE must be emitted on stdout as structured JSON
# (agents and deterministic-checks.md consume stdout). Capture the library's
# stderr diagnostic and re-emit on stdout before exiting.
UNAVAIL_DIAG=""
if ! UNAVAIL_DIAG=$(check_eslint_available "${ANALYZABLE[0]}" 2>&1 >/dev/null); then
  # The library wrote a JSON UNAVAILABLE line to stderr; bubble it to stdout.
  # Fall back to a generic message if capture failed or was empty.
  if [[ -n "$UNAVAIL_DIAG" ]]; then
    # Only the last line is the structured JSON — earlier lines may be warnings
    printf '%s\n' "$UNAVAIL_DIAG" | tail -1
  else
    printf '{"status":"UNAVAILABLE","reason":"eslint preflight failed (no diagnostic)"}\n'
  fi
  exit 0
fi

# --- Run Checks ---

# Thresholds sourced from:
#   MAINT-001: quality-slos.md — cognitive complexity <= 15
#   MAINT-003: standards-checklist.md — no god classes > 500 lines
#   max-lines-per-function threshold: 100 (practical boundary for reviewability)

run_maint_001() {
  run_eslint_check "MAINT-001" \
    '{"complexity": ["error", 15]}' \
    "${ANALYZABLE[@]}"
}

run_rel_005() {
  run_eslint_check "REL-005" \
    '{"no-unreachable": "error", "no-unused-vars": ["error", {"args": "after-used", "caughtErrors": "none"}]}' \
    "${ANALYZABLE[@]}"
}

run_maint_003() {
  run_eslint_check "MAINT-003" \
    '{"max-lines": ["error", 500], "max-lines-per-function": ["error", {"max": 100}]}' \
    "${ANALYZABLE[@]}"
}

run_perf_001() {
  run_eslint_check "PERF-001" \
    '{"no-await-in-loop": "error"}' \
    "${ANALYZABLE[@]}"
}

# --- Dispatch ---

case "$CHECK_ID" in
  MAINT-001)
    run_maint_001
    ;;
  REL-005)
    run_rel_005
    ;;
  MAINT-003)
    run_maint_003
    ;;
  PERF-001)
    run_perf_001
    ;;
  ALL)
    # Run all checks; emit one JSON object per line
    run_maint_001
    run_rel_005
    run_maint_003
    run_perf_001
    ;;
esac
