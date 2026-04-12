#!/bin/bash
# validate-decision-trace.sh — thin shim; logic lives in hooks/validators/decision-trace.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/decision-trace.sh"

if ! command -v jq &>/dev/null; then
  echo '{"error": "jq is required but not found"}' >&2
  exit 2
fi

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/beads/.*\.md$ ]]; then
  exit 0
fi

if [[ "$FILE_PATH" =~ -decision-trace\.md$ ]]; then
  exit 0
fi

if [[ "$FILE_PATH" =~ -aqs\.md$ ]] || [[ "$FILE_PATH" =~ hardening-report\.md$ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
if [[ -z "$CONTENT" ]]; then
  exit 0
fi

validate_decision_trace "$FILE_PATH" "$CONTENT"
exit $?
