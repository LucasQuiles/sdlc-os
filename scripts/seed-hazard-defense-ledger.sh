#!/bin/bash
# seed-hazard-defense-ledger.sh — Create seeded hazard-defense-ledger.yaml from stpa-analysis.yaml
# Usage: seed-hazard-defense-ledger.sh <task-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hazard-defense-lib.sh"

TASK_DIR="${1:?Usage: seed-hazard-defense-ledger.sh <task-dir>}"
STPA_FILE="$TASK_DIR/stpa-analysis.yaml"
OUTPUT="$TASK_DIR/hazard-defense-ledger.yaml"

[ -f "$STPA_FILE" ] || { echo "ERROR: stpa-analysis.yaml not found in $TASK_DIR" >&2; exit 1; }

TASK_ID=$(basename "$TASK_DIR")
NOW=$(now_utc)

# Use python3+PyYAML to parse stpa-analysis.yaml and generate ledger YAML
python3 -c "
import yaml, sys, json
from datetime import datetime

with open(sys.argv[1]) as f:
    stpa = yaml.safe_load(f)

task_id = stpa.get('task_id', sys.argv[2])
records = []
record_count = 0

for bead in stpa.get('beads_analyzed', []):
    bead_id = bead['bead_id']
    cynefin = bead.get('cynefin_domain', 'complex')
    security = bead.get('security_sensitive', False)
    ca_idx = 0
    for ca in bead.get('control_actions', []):
        ca_idx += 1
        uca_idx = 0
        for uca in ca.get('ucas', []):
            uca_idx += 1
            record_id = f'HDL-{bead_id}-CA{ca_idx}-UCA{uca_idx}'
            defenses = []
            for d in uca.get('suggested_defenses', []):
                defenses.append({'layer': d['layer'], 'mechanism': d['mechanism']})

            records.append({
                'id': record_id,
                'bead_id': bead_id,
                'cynefin_domain': cynefin,
                'security_sensitive': security,
                'interface': ca.get('interface', 0),
                'controller': ca.get('controller', ''),
                'control_action': ca.get('action', ''),
                'hazard': ca.get('hazard', ''),
                'unsafe_control_action': {
                    'category': uca.get('category', 'not_provided'),
                    'scenario': uca.get('scenario', ''),
                },
                'safety_constraint': uca.get('safety_constraint', None),
                'intended_defenses': defenses,
                'actual_catch_point': {
                    'layer': None,
                    'source': '',
                    'artifact_ref': '',
                    'finding_ref': None,
                },
                'latent_condition_trace': {
                    'source_layer': None,
                    'source_reason': '',
                    'artifact_ref': '',
                },
                'status': 'open',
                'residual_risk': 'medium',
                'owner': 'Conductor',
                'notes': '',
            })
            record_count += 1

beads_set = set(r['bead_id'] for r in records)
with_def = sum(1 for r in records if r['intended_defenses'])
without_def = record_count - with_def

ledger = {
    'schema_version': 1,
    'task_id': task_id,
    'artifact_status': 'seeded',
    'stpa_required': True,
    'derived_at': sys.argv[3],
    'last_updated': sys.argv[3],
    'summary': {
        'qualifying_beads': len(beads_set),
        'records_total': record_count,
        'records_with_defense': with_def,
        'records_without_defense': without_def,
        'residual_high_risk': 0,
        'escapes_known_at_close': 0,
        'coverage_state': 'warning' if without_def > 0 else 'healthy',
    },
    'records': records,
}

with open(sys.argv[4], 'w') as out:
    yaml.dump(ledger, out, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Seeded {record_count} records for {len(beads_set)} beads in {sys.argv[4]}')
" "$STPA_FILE" "$TASK_ID" "$NOW" "$OUTPUT"
