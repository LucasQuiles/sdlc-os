#!/bin/bash
set -euo pipefail
input=$(timeout 2s cat || true)
if [ -z "$input" ]; then exit 0; fi
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

[[ "$file_path" == */state.md ]] || exit 0

TASK_DIR=$(dirname "$file_path")
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

CURRENT_PHASE=$(sed -n '/^---$/,/^---$/{ s/^current-phase: *//p; }' "$file_path" 2>/dev/null | head -1)

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE_SCRIPT="$PLUGIN_ROOT/scripts/check-sdlc-gates.sh"

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
exit 0
