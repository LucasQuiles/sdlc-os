#!/bin/bash
# validate-mode-convergence-summary.sh — thin shim; logic lives in hooks/validators/mode-convergence.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/mode-convergence.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

if [[ "$file_path" != *"mode-convergence-summary.yaml" ]]; then
  exit 0
fi

validate_mode_convergence "$file_path"
exit $?
