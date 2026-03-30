#!/bin/bash
# record-review-pass.sh — Append one review pass to the canonical ledger
# Usage: echo '<json>' | record-review-pass.sh <project-dir>
#    or: record-review-pass.sh <project-dir> '<json>'
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/decision-noise-lib.sh"

# PyYAML dependency guard (required by decision-noise-lib.sh's detect_escalations)
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: PyYAML is required. Install with: pip3 install pyyaml" >&2
  exit 1
fi

PROJECT_DIR="${1:?Usage: record-review-pass.sh <project-dir> [json]}"
LEDGER="$PROJECT_DIR/docs/sdlc/decision-noise/review-passes.jsonl"

# Read record from argument or stdin
if [ -n "${2:-}" ]; then
  RECORD="$2"
else
  RECORD=$(cat)
fi

# Validate required fields
python3 -c "
import json, sys
try:
    r = json.loads(sys.argv[1])
except json.JSONDecodeError as e:
    print(f'ERROR: Invalid JSON: {e}', file=sys.stderr)
    sys.exit(1)
required = ['schema_version', 'review_pass_id', 'task_id', 'bead_id', 'review_stage', 'exposure_mode', 'map']
missing = [f for f in required if f not in r or r[f] is None]
if missing:
    print(f'ERROR: Missing required fields: {missing}', file=sys.stderr)
    sys.exit(1)
# Validate MAP has required dimensions
map_fields = r.get('map', {})
map_required = ['evidence_strength', 'impact_severity', 'base_rate_frequency', 'pattern_familiarity', 'decision_confidence']
map_missing = [f for f in map_required if f not in map_fields]
if map_missing:
    print(f'ERROR: MAP missing dimensions: {map_missing}', file=sys.stderr)
    sys.exit(1)
" "$RECORD"

append_review_pass "$LEDGER" "$RECORD"
echo "Recorded review pass to $LEDGER"
