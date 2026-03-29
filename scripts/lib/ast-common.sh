#!/bin/bash
# ast-common.sh — Shared library for AST analysis scripts
# Source this file from scripts that perform eslint-based AST checks.
#
# Operationalizes AST tier from references/deterministic-checks.md
# Requires: npx, eslint (invoked via npx)

# --- Preflight ---

# check_eslint_available: Verify npx is present and eslint is reachable via npx.
# Sets ESLINT_TS_PARSER_AVAILABLE=1 if @typescript-eslint/parser is loadable.
# Returns 0 if ready, 1 if unavailable.
check_eslint_available() {
  if ! command -v npx &>/dev/null; then
    echo '{"status": "UNAVAILABLE", "reason": "npx not found"}' >&2
    return 1
  fi

  # Verify eslint is actually resolvable (fast probe via --version)
  if ! npx --no eslint --version &>/dev/null 2>&1; then
    echo '{"status": "UNAVAILABLE", "reason": "eslint not found via npx — install eslint"}' >&2
    return 1
  fi

  # Probe for TypeScript parser availability (best-effort, no failure on absence)
  ESLINT_TS_PARSER_AVAILABLE=0
  if npx --no eslint --no-eslintrc --parser @typescript-eslint/parser --rule '{}' /dev/null &>/dev/null 2>&1; then
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

  # Run eslint and capture output + exit code
  local eslint_out
  local eslint_exit=0
  eslint_out=$(npx --no eslint \
    --no-eslintrc \
    "${parser_args[@]}" \
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
