#!/bin/bash
# validate_phase_transition — sourceable validator function
# Args: $1 = file_path, $2 = content (unused, state.md read from disk)
# Returns 0 always (WARN/advisory). Emits HOOK_WARNING to stderr.

validate_phase_transition() {
  local file_path="$1"
  # $2 = content (not used — state.md is read from disk for frontmatter parse)

  local TASK_DIR
  TASK_DIR=$(dirname "$file_path")
  local PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

  local CURRENT_PHASE
  CURRENT_PHASE=$(sed -n '/^---$/,/^---$/{ s/^current-phase: *//p; }' "$file_path" 2>/dev/null | head -1)

  local PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
  local GATE_SCRIPT="$PLUGIN_ROOT/scripts/check-sdlc-gates.sh"

  case "$CURRENT_PHASE" in
    synthesize|complete)
      if [ -x "$GATE_SCRIPT" ]; then
        if ! bash "$GATE_SCRIPT" "$TASK_DIR" "$CURRENT_PHASE" --project-dir "$PROJECT_DIR" 2>/dev/null; then
          echo "HOOK_WARNING: current-phase set to '$CURRENT_PHASE' but gate check failed. Run: bash scripts/run-${CURRENT_PHASE}-gates.sh $TASK_DIR $PROJECT_DIR" >&2
        fi
      else
        echo "HOOK_WARNING: current-phase set to '$CURRENT_PHASE' but gate script not found: $GATE_SCRIPT" >&2
      fi
      ;;
  esac

  return 0
}
