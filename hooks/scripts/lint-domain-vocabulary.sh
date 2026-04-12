#!/bin/bash
# lint-domain-vocabulary.sh — thin shim; logic lives in hooks/validators/domain-vocabulary.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/domain-vocabulary.sh"

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]] || [[ ! "$FILE_PATH" =~ docs/sdlc/active/ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
if [[ -z "$CONTENT" ]]; then
  exit 0
fi

validate_domain_vocabulary "$CONTENT"
exit $?
