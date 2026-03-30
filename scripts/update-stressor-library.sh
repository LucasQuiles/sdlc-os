#!/bin/bash
# update-stressor-library.sh — Update stressor library after a stress session
# Usage: update-stressor-library.sh <task-dir> <stressor-library-path> <project-dir>
#
# Reads stress-session.yaml results. Updates times_applied, times_caught,
# catch_rate, last_applied for each stressor used. Evaluates Lindy lifecycle
# transitions. Emits events to system-stress-events.jsonl for promotions,
# retirements, and significant (>20%) catch_rate changes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/stressor-lib.sh"

# PyYAML dependency guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: update-stressor-library.sh <task-dir> <stressor-library-path> <project-dir>}"
LIBRARY_PATH="${2:?Usage: update-stressor-library.sh <task-dir> <stressor-library-path> <project-dir>}"
PROJECT_DIR="${3:?Usage: update-stressor-library.sh <task-dir> <stressor-library-path> <project-dir>}"
SESSION_FILE="$TASK_DIR/stress-session.yaml"
EVENTS_LEDGER="$PROJECT_DIR/docs/sdlc/system-stress-events.jsonl"

[ -d "$TASK_DIR" ] || { echo "ERROR: task-dir not found: $TASK_DIR" >&2; exit 1; }
[ -f "$SESSION_FILE" ] || { echo "ERROR: stress-session.yaml not found in $TASK_DIR" >&2; exit 1; }
[ -f "$LIBRARY_PATH" ] || { echo "ERROR: stressor library not found: $LIBRARY_PATH" >&2; exit 1; }

mkdir -p "$(dirname "$EVENTS_LEDGER")"

python3 - "$SESSION_FILE" "$LIBRARY_PATH" "$EVENTS_LEDGER" <<'PYEOF'
import sys, yaml, json, os
from datetime import datetime, timezone

session_path, library_path, events_path = sys.argv[1], sys.argv[2], sys.argv[3]

with open(session_path) as f:
    session = yaml.safe_load(f)

with open(library_path) as f:
    lib = yaml.safe_load(f)

task_id = session.get('task_id', '')
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

stressors = lib.get('stressors') or []
stressor_map = {s['id']: s for s in stressors}

events = []
updated_ids = []

for app in (session.get('stressors_applied') or []):
    stressor_id = app.get('stressor_id', '')
    result = app.get('result', '')

    # Only update stressors that exist in the library (skip ad-hoc STR-NEW-*)
    if stressor_id not in stressor_map:
        continue
    if result == 'not_applicable':
        continue

    s = stressor_map[stressor_id]

    # Snapshot previous catch_rate for delta check
    prev_catch_rate = s.get('catch_rate')
    prev_status = s.get('lindy_status', 'provisional')

    # Update counters
    s['times_applied'] = (s.get('times_applied') or 0) + 1
    if result == 'caught':
        s['times_caught'] = (s.get('times_caught') or 0) + 1
    s['last_applied'] = now

    # Recompute catch_rate
    ta = s['times_applied']
    tc = s.get('times_caught', 0)
    s['catch_rate'] = round(tc / ta, 4) if ta > 0 else None

    new_catch_rate = s['catch_rate']

    # Evaluate Lindy lifecycle transitions
    status = s.get('lindy_status', 'provisional')
    new_status = status

    if status == 'provisional':
        if ta >= 3 and new_catch_rate is not None and new_catch_rate > 0:
            new_status = 'established'
        elif ta >= 5 and (new_catch_rate is None or new_catch_rate == 0.0):
            new_status = 'retired'

    elif status == 'established':
        # Retire established stressors: 10+ applications AND last 5 all misses
        # We approximate "last 5 all misses" by checking if ta >= 10 and
        # the number of catches in the last 5 applications is zero.
        # Since we don't store per-application history here, we use a conservative
        # heuristic: ta >= 10 AND times_caught/times_applied == 0 over the tail.
        # The full last-5-misses check requires application history — approximate
        # with: times_caught hasn't changed in the last 5 applications.
        # Since we only have aggregate data, use: ta >= 10 AND catch_rate == 0
        if ta >= 10 and (new_catch_rate is None or new_catch_rate == 0.0):
            new_status = 'retired'

    if new_status != status:
        s['lindy_status'] = new_status
        event_type = 'promotion' if new_status == 'established' else 'retirement'
        events.append({
            'stressor_id': stressor_id,
            'event': event_type,
            'date': now,
            'details': f'{status} -> {new_status} after {ta} applications (catch_rate={new_catch_rate})',
            'task_id': task_id,
        })
        print(f"  {event_type.upper()}: {stressor_id} ({status} -> {new_status})", file=sys.stderr)

    # Emit catch_rate_update if > 20% delta
    if (prev_catch_rate is not None and new_catch_rate is not None
            and abs(new_catch_rate - prev_catch_rate) > 0.20):
        events.append({
            'stressor_id': stressor_id,
            'event': 'catch_rate_update',
            'date': now,
            'details': f'catch_rate changed from {prev_catch_rate} to {new_catch_rate} (delta={round(abs(new_catch_rate - prev_catch_rate), 4)})',
            'task_id': task_id,
        })
        print(f"  CATCH_RATE_UPDATE: {stressor_id} ({prev_catch_rate} -> {new_catch_rate})", file=sys.stderr)

    updated_ids.append(stressor_id)

# Write updated library back
lib['last_updated'] = now
lib['stressors'] = stressors  # mutated in place via stressor_map
with open(library_path, 'w') as f:
    yaml.dump(lib, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

# Append events to system-stress-events.jsonl
if events:
    with open(events_path, 'a') as f:
        for event in events:
            f.write(json.dumps(event, separators=(',', ':')) + '\n')

print(f"Updated {len(updated_ids)} stressor(s) in library: {', '.join(updated_ids) or 'none'}", file=sys.stderr)
print(f"Emitted {len(events)} event(s) to system-stress-events.jsonl", file=sys.stderr)
print(f"Library updated: {library_path}")
PYEOF
