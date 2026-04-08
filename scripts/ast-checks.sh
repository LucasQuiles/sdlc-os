#!/bin/bash
set -euo pipefail

# ast-checks.sh — Deterministic AST analysis via eslint rules
# Operationalizes AST tier from references/deterministic-checks.md
#
# Usage: ast-checks.sh [--check CHECK_ID] FILE...
#   --check MAINT-001  cyclomatic complexity only
#   --check REL-005    dead code / unreachable code only
#   --check MAINT-003  god class / file length only
#   --check PERF-001   loop analysis (async-in-loop proxy) only
#   --check ALL        all checks (default)
#
# Requires: npx, eslint (invoked via npx)
# Supports: .ts, .tsx, .js, .jsx files (others skipped silently)
#
# Exit 0 + JSON = results (may include findings)
# Exit 2 = tool unavailable or invocation error

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

# --- Preflight ---

if ! check_eslint_available; then
  exit 2
fi

# --- File Filtering ---

# POSIX-compatible alternative to mapfile (bash 4+ only, macOS ships 3.2)
ANALYZABLE=()
while IFS= read -r line; do
  ANALYZABLE+=("$line")
done < <(filter_analyzable_files "${FILES[@]+"${FILES[@]}"}")

if [[ ${#ANALYZABLE[@]} -eq 0 ]]; then
  printf '{"status": "SKIP", "reason": "no analyzable files"}\n'
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
