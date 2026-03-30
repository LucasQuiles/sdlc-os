#!/bin/bash
# sdlc-common.sh — Shared helpers used across all SDLC-OS libraries
# Source this before domain-specific libs.
set -euo pipefail

# Format current UTC timestamp as ISO 8601
now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Count lines matching a pattern in a file
# Usage: count_by_pattern "file.txt" "pattern"
count_by_pattern() {
  local file="$1" pattern="$2"
  grep -c "$pattern" "$file" 2>/dev/null || echo 0
}

# PyYAML dependency guard — call before functions that need python3+PyYAML
# Usage: check_pyyaml || { echo "PyYAML required"; exit 1; }
# Returns 1 if missing (does NOT exit — callers decide behavior)
check_pyyaml() {
  python3 -c "import yaml" 2>/dev/null
}

# Validate a value against an allowed set. Returns 0 if valid, 1 if not.
# Usage: validate_enum "healthy" "healthy warning depleted"
validate_enum() {
  local value="$1" allowed="$2"
  for v in $allowed; do
    [[ "$v" == "$value" ]] && return 0
  done
  echo "ERROR: Invalid value '$value'. Allowed: $allowed" >&2
  return 1
}
