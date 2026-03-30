#!/bin/bash
# append-system-hazard-defense.sh — Append completed task HDL to system ledger
# Usage: append-system-hazard-defense.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hazard-defense-lib.sh"

TASK_DIR="${1:?Usage: append-system-hazard-defense.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-hazard-defense.sh <task-dir> <project-dir>}"
LEDGER="$TASK_DIR/hazard-defense-ledger.yaml"
SYSTEM_LEDGER="$PROJECT_DIR/docs/sdlc/system-hazard-defense.jsonl"

[ -f "$LEDGER" ] || { echo "ERROR: hazard-defense-ledger.yaml not found" >&2; exit 1; }

# Build JSONL entry from final ledger
python3 -c "
import yaml, sys, json
from collections import Counter

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

if data.get('artifact_status') != 'final':
    print(f'ERROR: artifact_status is {data.get(\"artifact_status\")}, must be final', file=sys.stderr)
    sys.exit(1)

records = data.get('records', [])
catch_dist = Counter()
uca_fingerprints = []
for r in records:
    cp = r.get('actual_catch_point', {})
    layer = cp.get('layer') or 'not_tested'
    catch_dist[layer] += 1
    # UCA fingerprint: category + first 40 chars of scenario
    uca = r.get('unsafe_control_action', {})
    fp = f'{uca.get(\"category\", \"unknown\")}:{uca.get(\"scenario\", \"\")[:40]}'
    uca_fingerprints.append(fp)

# Find repeated fingerprints
fp_counts = Counter(uca_fingerprints)
repeated = [fp for fp, count in fp_counts.items() if count > 1]

entry = {
    'task_id': data['task_id'],
    'date': data['derived_at'],
    'qualifying_beads': data['summary']['qualifying_beads'],
    'records_total': data['summary']['records_total'],
    'records_with_defense': data['summary']['records_with_defense'],
    'records_without_defense': data['summary']['records_without_defense'],
    'catch_layer_distribution': dict(catch_dist),
    'escapes_at_close': data['summary']['escapes_known_at_close'],
    'residual_high_risk': data['summary']['residual_high_risk'],
    'repeated_uca_fingerprints': repeated,
    'coverage_state': data['summary']['coverage_state'],
}

print(json.dumps(entry, separators=(',', ':')))
" "$LEDGER" >> "$SYSTEM_LEDGER"

echo "Appended $(basename "$TASK_DIR") to system-hazard-defense.jsonl"
