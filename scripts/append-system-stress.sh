#!/bin/bash
# append-system-stress.sh — Append completed stress session to system-stress.jsonl
# Usage: append-system-stress.sh <task-dir> <project-dir>
#
# Reads final stress-session.yaml, builds a JSONL entry, and appends it to
# docs/sdlc/system-stress.jsonl in the project directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/stressor-lib.sh"

# PyYAML dependency guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: append-system-stress.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-stress.sh <task-dir> <project-dir>}"
SESSION_FILE="$TASK_DIR/stress-session.yaml"
LEDGER="$PROJECT_DIR/docs/sdlc/system-stress.jsonl"

[ -d "$TASK_DIR" ] || { echo "ERROR: task-dir not found: $TASK_DIR" >&2; exit 1; }
[ -f "$SESSION_FILE" ] || { echo "ERROR: stress-session.yaml not found in $TASK_DIR" >&2; exit 1; }

mkdir -p "$(dirname "$LEDGER")"

python3 - "$SESSION_FILE" "$LEDGER" <<'PYEOF'
import sys, yaml, json
from datetime import datetime, timezone

session_path, ledger_path = sys.argv[1], sys.argv[2]

with open(session_path) as f:
    session = yaml.safe_load(f)

if session.get('artifact_status') != 'final':
    status = session.get('artifact_status')
    print(f"ERROR: artifact_status is '{status}', must be 'final' to append to system ledger", file=sys.stderr)
    sys.exit(1)

summary = session.get('summary', {})
selection = session.get('selection', {})
harvest = session.get('harvest', {})
task_id = session.get('task_id', '')
date = session.get('last_updated') or session.get('derived_at') or \
    datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

entry = {
    'task_id': task_id,
    'date': date,
    'sampling_reason': session.get('sampling_reason', ''),
    'stressors_applied': summary.get('stressors_applied', 0),
    'stressors_caught': summary.get('stressors_caught', 0),
    'stressors_held': summary.get('stressors_held', 0),
    'stress_yield': summary.get('stress_yield', 0.0),
    'new_stressors_harvested': summary.get('new_stressors_harvested', 0),
    'subtraction_candidates': summary.get('subtraction_candidates', 0),
    'clean_streak_at_sample': selection.get('clean_streak_length', 0),
    'quality_budget_state': selection.get('quality_budget_state', ''),
    'complexity_weight': selection.get('complexity_weight', 0.0),
    'sampling_seed': selection.get('sampling_seed', 0.0),
    'hdl_open_ucas': selection.get('hdl_open_ucas', 0),
}

with open(ledger_path, 'a') as f:
    f.write(json.dumps(entry, separators=(',', ':')) + '\n')

print(json.dumps(entry, separators=(',', ':')))
PYEOF

echo "Appended $TASK_DIR to system-stress.jsonl"
