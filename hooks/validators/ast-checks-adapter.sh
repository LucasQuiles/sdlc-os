#!/bin/bash
# validate_ast_checks — sourceable adapter function
# Args: $1 = file_path
# Returns 0 always (WARN/advisory). Emits FINDINGS JSON to stdout.

validate_ast_checks() {
  local file_path="$1"
  local ast_checks_script
  ast_checks_script="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/ast-checks.sh"
  if [[ ! -x "$ast_checks_script" ]]; then
    return 0
  fi
  local output
  output=$(bash "$ast_checks_script" --check ALL -- "$file_path" 2>/dev/null) || true
  if [[ -z "$output" ]]; then
    return 0
  fi
  local line status
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    status=$(printf '%s' "$line" | jq -r '.status // "SKIP"' 2>/dev/null) || status="SKIP"
    case "$status" in
      FINDINGS) printf '%s\n' "$line" ;;
      CLEAN|SKIP|UNAVAILABLE) ;;
    esac
  done <<< "$output"
  return 0
}
