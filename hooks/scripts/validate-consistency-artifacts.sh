#!/bin/bash
# validate-consistency-artifacts.sh — thin shim; logic lives in hooks/validators/consistency.sh
# Advisory: always exits 0.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/consistency.sh"

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]]; then exit 0; fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

validate_consistency "$FILE_PATH" "$CONTENT"
exit 0
