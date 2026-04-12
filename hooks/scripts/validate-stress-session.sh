#!/bin/bash
# validate-stress-session.sh — thin shim; logic lives in hooks/validators/stress-session.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/stress-session.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

if [[ "$file_path" != *"stress-session.yaml" ]]; then
  exit 0
fi

validate_stress_session "$file_path"
exit $?
