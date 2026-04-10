#!/bin/bash
# ast-common.sh — Shared library for AST analysis scripts
# Source this file from scripts that perform eslint-based AST checks.
#
# Operationalizes AST tier from references/deterministic-checks.md
# Requires: eslint (resolved from target file's ancestor node_modules/.bin or PATH)

# --- Preflight ---

# find_eslint_for_file: Locate an eslint binary to use for a given file.
# Walks upward from the file's directory looking for node_modules/.bin/eslint.
# Falls back to a globally-installed `eslint` if present in PATH.
# Prints the absolute path to eslint on success, empty string on failure.
# Never auto-installs (no network calls, no first-run surprises).
find_eslint_for_file() {
  local file="$1"
  local dir
  dir="$(cd "$(dirname "$file")" 2>/dev/null && pwd)" || return 0

  # Walk upward looking for node_modules/.bin/eslint
  while [[ "$dir" != "/" && -n "$dir" ]]; do
    if [[ -x "$dir/node_modules/.bin/eslint" ]]; then
      echo "$dir/node_modules/.bin/eslint"
      return 0
    fi
    dir="$(dirname "$dir")"
  done

  # Fall back to PATH (global install)
  if command -v eslint &>/dev/null; then
    command -v eslint
    return 0
  fi

  # Not found — caller must fail-open
}

# check_eslint_available: Quick check that at least one eslint is locatable for the
# given file. Also detects eslint version — the current rule-injection invocation
# path (--no-eslintrc + --parser + --rule) was deprecated in eslint 9+ flat config.
# Returns 0 if ready (v8 or earlier with TS parser), 1 otherwise.
# Sets ESLINT_BIN, ESLINT_MAJOR_VERSION, and ESLINT_TS_PARSER_AVAILABLE.
check_eslint_available() {
  local probe_file="${1:-}"
  ESLINT_BIN=""
  ESLINT_MAJOR_VERSION=""
  ESLINT_TS_PARSER_AVAILABLE=0

  if [[ -n "$probe_file" ]]; then
    ESLINT_BIN="$(find_eslint_for_file "$probe_file")"
  fi

  if [[ -z "$ESLINT_BIN" ]]; then
    echo '{"status": "UNAVAILABLE", "reason": "eslint not found in local node_modules or PATH"}' >&2
    return 1
  fi

  # Detect eslint major version
  local version_output
  version_output=$("$ESLINT_BIN" --version 2>/dev/null | head -1 | tr -d 'v')
  ESLINT_MAJOR_VERSION="${version_output%%.*}"

  # eslint 9+ uses flat config (eslint.config.js) and removed --no-eslintrc / --parser
  # flags. The current rule-injection code path is incompatible with v9+. Fail-open
  # with a clear diagnostic so hook-latency reports surface this.
  if [[ -n "$ESLINT_MAJOR_VERSION" ]] && (( ESLINT_MAJOR_VERSION >= 9 )); then
    echo "{\"status\": \"UNAVAILABLE\", \"reason\": \"eslint ${version_output} uses flat config — --no-eslintrc/--parser CLI flags removed. AST hook needs rewrite for eslint 9+.\"}" >&2
    return 1
  fi

  # Probe the TS parser — best-effort (v8 path only)
  if "$ESLINT_BIN" --no-eslintrc --parser @typescript-eslint/parser --rule '{}' /dev/null &>/dev/null 2>&1; then
    ESLINT_TS_PARSER_AVAILABLE=1
  fi

  return 0
}

# --- File Filtering ---

# filter_analyzable_files: Print only .ts/.tsx/.js/.jsx paths from the given list.
# Usage: filter_analyzable_files file1 file2 ...
# Prints one path per line to stdout.
filter_analyzable_files() {
  local f
  for f in "$@"; do
    case "$f" in
      *.ts|*.tsx|*.js|*.jsx) echo "$f" ;;
    esac
  done
}

# --- ESLint Runner ---

# run_eslint_check: Run eslint with given rules against given files.
# Usage: run_eslint_check CHECK_ID RULES_JSON FILE...
# Prints parsed SDLC findings JSON to stdout.
# Returns 0 always (errors are captured in JSON output).
#
# Output format on findings:
#   {"status":"FINDINGS","check":"X","findings":[...]}
# Output format on clean:
#   {"status":"CLEAN","check":"X","files_checked":N}
# Output format on tool error:
#   {"status":"UNAVAILABLE","check":"X","reason":"..."}
run_eslint_check() {
  local check_id="$1"
  local rules_json="$2"
  shift 2
  local files=("$@")
  local file_count=${#files[@]}

  if [[ $file_count -eq 0 ]]; then
    printf '{"status":"SKIP","check":"%s","reason":"no files"}\n' "$check_id"
    return 0
  fi

  # Build parser args if TypeScript parser is available
  local parser_args=()
  if [[ "${ESLINT_TS_PARSER_AVAILABLE:-0}" == "1" ]]; then
    parser_args=(--parser @typescript-eslint/parser)
  fi

  # ESLINT_BIN is set by check_eslint_available; if unset or empty, fail-open.
  if [[ -z "${ESLINT_BIN:-}" ]]; then
    printf '{"status":"UNAVAILABLE","check":"%s","reason":"eslint binary not located"}\n' "$check_id"
    return 0
  fi

  # Run eslint and capture output + exit code.
  # parser_args expansion is guarded via ${arr[@]+"${arr[@]}"} for set -u safety on bash 3.2.
  local eslint_out
  local eslint_exit=0
  eslint_out=$("$ESLINT_BIN" \
    --no-eslintrc \
    ${parser_args[@]+"${parser_args[@]}"} \
    --rule "$rules_json" \
    --format json \
    "${files[@]}" 2>/dev/null) || eslint_exit=$?

  # eslint exits 1 on lint errors (expected), 2 on fatal error (unexpected)
  if [[ $eslint_exit -eq 2 ]]; then
    # Fatal error — degrade gracefully
    local err_msg
    err_msg=$(printf '%s' "$eslint_out" | head -1 | tr -d '"\\')
    printf '{"status":"UNAVAILABLE","check":"%s","reason":"eslint fatal error: %s"}\n' \
      "$check_id" "${err_msg:-unknown}"
    return 0
  fi

  # Parse JSON output and reformat to SDLC finding format
  if ! command -v node &>/dev/null; then
    printf '{"status":"UNAVAILABLE","check":"%s","reason":"node not found — cannot parse eslint JSON"}\n' "$check_id"
    return 0
  fi

  # Use node to parse eslint JSON and emit SDLC format
  local parsed
  parsed=$(node --input-type=module <<EOF 2>/dev/null
const raw = ${eslint_out:-[]};
const findings = [];
for (const fileResult of raw) {
  for (const msg of fileResult.messages) {
    if (msg.severity > 0) {
      findings.push({
        file: fileResult.filePath,
        line: msg.line || 0,
        rule: msg.ruleId || "unknown",
        message: msg.message,
        severity: msg.severity === 2 ? "BLOCKING" : "WARNING"
      });
    }
  }
}
if (findings.length > 0) {
  process.stdout.write(JSON.stringify({
    status: "FINDINGS",
    check: "${check_id}",
    findings
  }));
} else {
  process.stdout.write(JSON.stringify({
    status: "CLEAN",
    check: "${check_id}",
    files_checked: ${file_count}
  }));
}
EOF
)

  if [[ -z "$parsed" ]]; then
    printf '{"status":"UNAVAILABLE","check":"%s","reason":"failed to parse eslint output"}\n' "$check_id"
    return 0
  fi

  printf '%s\n' "$parsed"
}
