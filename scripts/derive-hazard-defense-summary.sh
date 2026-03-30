#!/bin/bash
# derive-hazard-defense-summary.sh — Recompute summary fields from ledger records
# Usage: derive-hazard-defense-summary.sh <task-dir> [--status active|final]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hazard-defense-lib.sh"

if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: derive-hazard-defense-summary.sh <task-dir> [--status active|final]}"
STATUS="${3:-active}"
LEDGER="$TASK_DIR/hazard-defense-ledger.yaml"

[ -f "$LEDGER" ] || { echo "ERROR: hazard-defense-ledger.yaml not found" >&2; exit 1; }

NOW=$(now_utc)
SUMMARY_JSON=$(derive_hdl_summary "$LEDGER")

# Update the ledger in place using python3
python3 -c "
import yaml, sys, json

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

summary = json.loads(sys.argv[2])
data['summary'] = summary
data['artifact_status'] = sys.argv[3]
data['derived_at'] = sys.argv[4]
data['last_updated'] = sys.argv[4]

with open(sys.argv[1], 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Summary: {summary[\"records_total\"]} records, coverage: {summary[\"coverage_state\"]}')
" "$LEDGER" "$SUMMARY_JSON" "$STATUS" "$NOW"
