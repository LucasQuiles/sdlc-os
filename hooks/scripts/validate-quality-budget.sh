#!/bin/bash
# validate-quality-budget.sh — thin shim; logic lives in hooks/validators/quality-budget.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/quality-budget.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

if [[ "$file_path" != *"quality-budget.yaml" ]]; then
  exit 0
fi

validate_quality_budget "$file_path"
exit $?
