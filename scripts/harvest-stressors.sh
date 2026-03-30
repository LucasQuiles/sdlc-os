#!/bin/bash
# harvest-stressors.sh — Extract new stressor candidates from a stress session
# Usage: harvest-stressors.sh <task-dir>
#
# Reads stress-session.yaml and extracts findings that don't match existing
# stressors. Proposes new stressor entries with lindy_status: provisional.
# Outputs candidate YAML to stdout for Conductor review.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/stressor-lib.sh"

# PyYAML dependency guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: harvest-stressors.sh <task-dir>}"
SESSION_FILE="$TASK_DIR/stress-session.yaml"
LIBRARY_PATH="${2:-}"

[ -d "$TASK_DIR" ] || { echo "ERROR: task-dir not found: $TASK_DIR" >&2; exit 1; }
[ -f "$SESSION_FILE" ] || { echo "ERROR: stress-session.yaml not found in $TASK_DIR" >&2; exit 1; }

# Locate stressor library: use arg, or search relative to plugin root
if [ -z "$LIBRARY_PATH" ]; then
  PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  LIBRARY_PATH="$PLUGIN_ROOT/references/stressor-library.yaml"
fi

python3 - "$SESSION_FILE" "$LIBRARY_PATH" <<'PYEOF'
import sys, yaml, re, os
from datetime import datetime, timezone

session_path, library_path = sys.argv[1], sys.argv[2]

with open(session_path) as f:
    session = yaml.safe_load(f)

# Load existing stressor IDs to avoid duplicates
existing_ids = set()
existing_names = set()
if os.path.isfile(library_path):
    with open(library_path) as f:
        lib = yaml.safe_load(f)
    for s in (lib.get('stressors') or []):
        existing_ids.add(s.get('id', ''))
        existing_names.add(s.get('name', '').lower().strip())

task_id = session.get('task_id', '')
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# Find the next STR-NNN id
max_num = 0
for sid in existing_ids:
    m = re.match(r'STR-(\d+)', sid)
    if m:
        max_num = max(max_num, int(m.group(1)))

candidates = []
candidate_counter = max_num + 1

# Inspect stressors_applied for caught findings with no existing stressor match
for app in (session.get('stressors_applied') or []):
    stressor_id = app.get('stressor_id', '')
    result = app.get('result', '')
    notes = app.get('notes', '')
    bead_id = app.get('bead_id', '')
    target = app.get('target', '')
    finding_ref = app.get('finding_ref', '')

    # Only harvest from ad-hoc entries (STR-NEW-*) or caught findings not in library
    is_ad_hoc = stressor_id.startswith('STR-NEW') or stressor_id not in existing_ids
    is_caught = result == 'caught'

    if not (is_ad_hoc and is_caught):
        continue

    # Build candidate name from target
    candidate_name = target.lower().strip() if target else notes[:60].lower().strip()
    if candidate_name in existing_names:
        continue

    new_id = f'STR-{candidate_counter:03d}'
    candidate_counter += 1

    candidate = {
        'id': new_id,
        'name': target if target else notes[:60],
        'category': 'context_gap',  # Conductor should reclassify
        'source': {
            'type': 'aqs_finding',
            'task_id': task_id,
            'artifact_ref': finding_ref or stressor_id,
        },
        'description': notes if notes else f'Finding from stress session on {bead_id}: {target}',
        'probe_template': f'Verify that {{{{target}}}} handles: {target}',
        'applicable_when': {
            'cynefin': [],   # Conductor should fill from bead context
            'tags': [],
        },
        'severity': 'medium',  # Conductor should validate
        'times_applied': 0,
        'times_caught': 0,
        'catch_rate': None,
        'first_harvested': now,
        'last_applied': None,
        'lindy_status': 'provisional',
        '_harvest_note': f'Harvested from {task_id} session. Review category, severity, applicable_when, and probe_template before committing.',
    }
    candidates.append(candidate)
    existing_names.add(candidate_name)

# Also check harvest.new_stressors for any already flagged by the Conductor
flagged_new = session.get('harvest', {}).get('new_stressors') or []
subtraction = session.get('subtraction_log') or []
sub_candidates = session.get('harvest', {}).get('subtraction_candidates') or []

output = {
    'source_task_id': task_id,
    'harvested_at': now,
    'session_summary': session.get('summary', {}),
    'candidate_stressors': candidates,
    'candidate_count': len(candidates),
    'flagged_by_conductor': flagged_new,
    'subtraction_candidates': sub_candidates,
    'subtraction_log_entries': len(subtraction),
    'instructions': (
        'Review candidate_stressors. For each: '
        '(1) Verify category matches the failure mode class. '
        '(2) Set applicable_when.cynefin and tags. '
        '(3) Refine probe_template to be reusable. '
        '(4) Adjust severity. '
        'Then append approved entries to references/stressor-library.yaml '
        'and run update-stressor-library.sh.'
    ),
}

print(yaml.dump(output, default_flow_style=False, sort_keys=False))
PYEOF
