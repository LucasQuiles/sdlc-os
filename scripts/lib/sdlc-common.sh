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

# classify_task_lanes <task-dir> <task-id> <project-dir>
# Sets global variables: HAS_BEADS, IS_STPA, IS_AQS, IS_STRESSED
classify_task_lanes() {
  local task_dir="$1" task_id="$2" project_dir="$3"
  HAS_BEADS=false; IS_STPA=false; IS_AQS=false; IS_STRESSED=false

  # Artifact-first classification
  # Each line uses || true to prevent set -e from killing the function on false conditions
  [ -f "$task_dir/hazard-defense-ledger.yaml" ] && IS_STPA=true || true
  [ -f "$task_dir/stress-session.yaml" ] && IS_STRESSED=true || true
  # AQS: artifact-only, NO bead-domain fallback (AQS can be skipped for Chaotic/Clear/ACCIDENTAL)
  [ -f "$task_dir/decision-noise-summary.yaml" ] && IS_AQS=true || true
  grep -qF "\"$task_id\"" "$project_dir/docs/sdlc/decision-noise/review-passes.jsonl" 2>/dev/null && IS_AQS=true || true

  # Bead metadata fallback (handles bold markdown)
  if [ -d "$task_dir/beads" ] && ls "$task_dir/beads/"*.md &>/dev/null; then
    HAS_BEADS=true
    if [ "$IS_STPA" = false ]; then
      grep -rlq "\*\*Cynefin domain:\*\*.*complex\|\*\*Security sensitive:\*\*.*true" "$task_dir/beads/" 2>/dev/null && IS_STPA=true || true
    fi
    # NO bead fallback for IS_AQS — artifact-only
  fi
}
