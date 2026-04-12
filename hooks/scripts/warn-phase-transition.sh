#!/bin/bash
# warn-phase-transition.sh — thin shim; logic lives in hooks/validators/phase-transition.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/phase-transition.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

[[ "$file_path" == */state.md ]] || exit 0

validate_phase_transition "$file_path" ""
exit 0
