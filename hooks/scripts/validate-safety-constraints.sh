#!/bin/bash
# validate-safety-constraints.sh — thin shim; logic lives in hooks/validators/safety-constraints.sh
# Advisory: always exits 0.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/safety-constraints.sh"

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

case "$FILE_PATH" in
  *.md|*.json|*.yaml|*.yml|*.txt|*.toml|*.ini|*.cfg|*.conf|*.lock|*.sum)
    exit 0
    ;;
esac

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
if [[ -z "$CONTENT" ]]; then
  exit 0
fi

validate_safety_constraints "$FILE_PATH" "$CONTENT"
exit 0
