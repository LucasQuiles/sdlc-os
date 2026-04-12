#!/bin/bash
# validate-decision-noise-summary.sh — thin shim; logic lives in hooks/validators/decision-noise.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/decision-noise.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

if [[ "$file_path" != *"decision-noise-summary.yaml" ]]; then
  exit 0
fi

validate_decision_noise "$file_path"
exit $?
