#!/bin/bash
# validate-hazard-defense-ledger.sh — thin shim; logic lives in hooks/validators/hazard-ledger.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../validators/hazard-ledger.sh"

load_hook_input_or_exit input || exit 0
file_path=$(read_hook_file_path "$input")

if [[ "$file_path" != *"hazard-defense-ledger.yaml" ]]; then
  exit 0
fi

validate_hazard_ledger "$file_path"
exit $?
