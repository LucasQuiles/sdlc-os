#!/bin/bash
# select-stressors.sh — Select applicable stressors for a task
# Usage: select-stressors.sh <task-dir> <stressor-library-path>
#
# Reads quality-budget.yaml, hazard-defense-ledger.yaml (if exists), and the
# stressor library. Matches stressors by cynefin domain and tags using
# python3+PyYAML. Prefers established over provisional. Outputs selected
# stressor+bead pairs as YAML to stdout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/stressor-lib.sh"

# PyYAML dependency guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_DIR="${1:?Usage: select-stressors.sh <task-dir> <stressor-library-path>}"
LIBRARY_PATH="${2:?Usage: select-stressors.sh <task-dir> <stressor-library-path>}"
BUDGET_FILE="$TASK_DIR/quality-budget.yaml"
HDL_FILE="$TASK_DIR/hazard-defense-ledger.yaml"

[ -d "$TASK_DIR" ] || { echo "ERROR: task-dir not found: $TASK_DIR" >&2; exit 1; }
[ -f "$BUDGET_FILE" ] || { echo "ERROR: quality-budget.yaml not found in $TASK_DIR" >&2; exit 1; }
[ -f "$LIBRARY_PATH" ] || { echo "ERROR: stressor library not found: $LIBRARY_PATH" >&2; exit 1; }

python3 - "$TASK_DIR" "$BUDGET_FILE" "$LIBRARY_PATH" "$HDL_FILE" <<'PYEOF'
import sys, yaml, json, os

task_dir, budget_path, library_path, hdl_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(budget_path) as f:
    budget = yaml.safe_load(f)

with open(library_path) as f:
    lib = yaml.safe_load(f)

# Collect HDL open UCAs if ledger exists
hdl_open_ucas = []
if os.path.isfile(hdl_path):
    with open(hdl_path) as f:
        hdl = yaml.safe_load(f)
    for record in (hdl.get('records') or []):
        acp = record.get('actual_catch_point', {})
        defense = record.get('defense', {})
        # Open UCA = no defense or catch_point is escaped
        if not defense.get('controls') or acp.get('layer') == 'escaped':
            uca = record.get('unsafe_control_action', {})
            hdl_open_ucas.append({
                'record_id': record.get('id', ''),
                'category': uca.get('category', ''),
                'scenario': uca.get('scenario', ''),
            })

# Collect beads from beads/ directory
beads_dir = os.path.join(task_dir, 'beads')
beads = []
if os.path.isdir(beads_dir):
    for fname in sorted(os.listdir(beads_dir)):
        if not fname.endswith('.md'):
            continue
        bead_id = fname[:-3]
        bead_path = os.path.join(beads_dir, fname)
        cynefin = ''
        tags = []
        with open(bead_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('Cynefin domain:') or line.startswith('**Cynefin domain:**'):
                    cynefin = line.split(':', 1)[-1].strip().strip('*').strip().lower()
                if line.startswith('Tags:') or line.startswith('**Tags:**'):
                    raw = line.split(':', 1)[-1].strip().strip('*').strip()
                    tags = [t.strip() for t in raw.split(',') if t.strip()]
        if cynefin:
            beads.append({'id': bead_id, 'cynefin': cynefin, 'tags': tags})

if not beads:
    # Fall back to cynefin_mix from budget
    cynefin_mix = budget.get('cynefin_mix', {})
    dominant = max(cynefin_mix, key=lambda k: cynefin_mix.get(k, 0)) if cynefin_mix else 'complicated'
    beads = [{'id': 'default', 'cynefin': dominant, 'tags': []}]

stressors = lib.get('stressors') or []
selected = []

for bead in beads:
    bead_cynefin = bead['cynefin']
    bead_tags = set(bead['tags'])
    matched = []

    for s in stressors:
        if s.get('lindy_status') == 'retired':
            continue
        aw = s.get('applicable_when', {})
        cynefin_list = aw.get('cynefin') or []
        tag_list = aw.get('tags') or []
        cynefin_match = not cynefin_list or bead_cynefin in cynefin_list
        tag_match = not tag_list or bool(bead_tags & set(tag_list))
        if cynefin_match and tag_match:
            matched.append(s)

    # Sort: established first, then provisional
    matched.sort(key=lambda s: (0 if s.get('lindy_status') == 'established' else 1))

    # Ensure at least one provisional is included if available
    has_provisional = any(s.get('lindy_status') == 'provisional' for s in matched)
    final = matched

    for s in final:
        selected.append({
            'stressor_id': s['id'],
            'stressor_name': s['name'],
            'bead_id': bead['id'],
            'lindy_status': s.get('lindy_status'),
            'severity': s.get('severity'),
            'probe_template': s.get('probe_template', ''),
            'applicable_when': s.get('applicable_when', {}),
        })

output = {
    'task_id': budget.get('task_id', os.path.basename(task_dir)),
    'generated_at': __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'quality_budget_state': budget.get('budget_state'),
    'hdl_open_ucas_count': len(hdl_open_ucas),
    'selected_count': len(selected),
    'selected': selected,
    'hdl_derived_stressor_candidates': [
        {
            'record_id': u['record_id'],
            'category': u['category'],
            'scenario_excerpt': u['scenario'][:80],
            'note': 'Open UCA — no defense coverage. Consider harvesting as stressor.',
        }
        for u in hdl_open_ucas
    ],
}

print(yaml.dump(output, default_flow_style=False, sort_keys=False))
PYEOF
