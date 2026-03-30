#!/bin/bash
# derive-mode-convergence-summary.sh — Derive mode-convergence-summary.yaml for a task
# Usage: derive-mode-convergence-summary.sh <task-dir> [--status partial|final]
#
# Reads:
#   <task-dir>/quality-budget.yaml        — SRK signal source
#   <task-dir>/convergence-history.yaml   — per-bead convergence logs (optional)
#   <task-dir>/escalation-log.yaml        — structured escalation records (optional)
# Produces:
#   <task-dir>/mode-convergence-summary.yaml
#
# v2 DEFERRAL: mode_transitions not computed (requires per-iteration snapshots). Set to 0.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PyYAML guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

source "$SCRIPT_DIR/lib/mode-convergence-lib.sh"

TASK_DIR="${1:?Usage: derive-mode-convergence-summary.sh <task-dir> [--status partial|final]}"
STATUS="${2:-partial}"
# Accept --status <value> or bare value
if [ "$STATUS" = "--status" ]; then
  STATUS="${3:-partial}"
fi

case "$STATUS" in
  partial|final) ;;
  *) echo "ERROR: --status must be 'partial' or 'final', got: $STATUS" >&2; exit 1 ;;
esac

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }

TASK_ID=$(basename "$TASK_DIR")
QB="$TASK_DIR/quality-budget.yaml"
CONV_HISTORY="$TASK_DIR/convergence-history.yaml"
ESC_LOG="$TASK_DIR/escalation-log.yaml"
OUTPUT="$TASK_DIR/mode-convergence-summary.yaml"
RULES_FILE="$SCRIPT_DIR/../references/mode-convergence-rules.yaml"

[ -f "$QB" ] || { echo "ERROR: quality-budget.yaml not found in $TASK_DIR" >&2; exit 1; }
[ -f "$RULES_FILE" ] || { echo "ERROR: mode-convergence-rules.yaml not found: $RULES_FILE" >&2; exit 1; }

# Extract beads.total separately from wip_beads (schema distinguishes them)
BEADS_TOTAL=$(python3 -c "import yaml,sys; qb=yaml.safe_load(open(sys.argv[1])); print(qb.get('beads',{}).get('total',0))" "$QB")

NOW=$(now_utc)

# --- Step 1: Classify execution mode from quality-budget.yaml SRK signals ---
MODE_JSON=$(python3 -c "
import yaml, sys, json
from collections import Counter

with open(sys.argv[1]) as f:
    qb = yaml.safe_load(f)
with open(sys.argv[2]) as f:
    rules = yaml.safe_load(f)

metrics     = qb.get('metrics', {})
corrections = qb.get('corrections', {})

tpb = float(metrics.get('turbulence_sum_per_bead', 0))
ztr = float(metrics.get('zero_turbulence_rate', 0))
lat = float(metrics.get('review_latency_p95_s', 0))
esc = int(corrections.get('L2', 0)) + int(corrections.get('L2_5', 0)) + int(corrections.get('L2_75', 0))

# Also need wip_beads from quality-budget
beads_total = qb.get('beads', {}).get('total', 0)

t = rules['srk_thresholds']

def classify(signal, val):
    th = t[signal]
    skill_max = th.get('skill_max')
    skill_min = th.get('skill_min')
    knowledge_min = th.get('knowledge_min')
    knowledge_max = th.get('knowledge_max')
    if skill_max is not None and (val < skill_max or (skill_max == 0 and val == 0)):
        return 'skill_based'
    if skill_min is not None and val > skill_min:
        return 'skill_based'
    if knowledge_min is not None and val > knowledge_min:
        return 'knowledge_based'
    if knowledge_max is not None and val < knowledge_max:
        return 'knowledge_based'
    return 'rule_based'

votes = [
    classify('turbulence_sum_per_bead', tpb),
    classify('zero_turbulence_rate', ztr),
    classify('review_latency_p95_s', lat),
    classify('escalation_count', esc),
]

counts = Counter(votes)
winner, win_count = counts.most_common(1)[0]
if win_count == 4:
    conf = 'high'
elif win_count == 3:
    conf = 'medium'
else:
    winner = 'rule_based'
    conf = 'low'

result = {
    'classification': winner,
    'confidence': conf,
    'signals': {
        'wip_beads': int(qb.get('beads', {}).get('wip', 0)),
        'turbulence_sum_per_bead': tpb,
        'review_latency_p95_s': lat,
        'zero_turbulence_rate': ztr,
        'escalation_count': esc,
    }
}
print(json.dumps(result))
" "$QB" "$RULES_FILE")

# --- Step 2: Load convergence history (optional) ---
CONV_JSON="[]"
if [ -f "$CONV_HISTORY" ]; then
  CONV_JSON=$(python3 -c "
import yaml, sys, json
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
history = data if isinstance(data, list) else data.get('convergence_history', [])
print(json.dumps(history))
" "$CONV_HISTORY")
fi

# --- Step 3: Load escalation log (optional) ---
ESC_JSON="[]"
if [ -f "$ESC_LOG" ]; then
  ESC_JSON=$(python3 -c "
import yaml, sys, json
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
log = data if isinstance(data, list) else data.get('escalation_log', [])
print(json.dumps(log))
" "$ESC_LOG")
fi

# --- Step 4: Derive summary stats and write output ---
python3 -c "
import yaml, sys, json
from collections import Counter

mode_json      = json.loads(sys.argv[1])
conv_history   = json.loads(sys.argv[2])
esc_log        = json.loads(sys.argv[3])
task_id        = sys.argv[4]
status         = sys.argv[5]
now            = sys.argv[6]
output_path    = sys.argv[7]

# Summary derivation from escalation log
total_escalations  = len(esc_log)
reason_distribution = {}
if esc_log:
    counts = Counter(e.get('reason') for e in esc_log if e.get('reason'))
    reason_distribution = dict(counts)

if reason_distribution:
    dominant_reason = max(reason_distribution, key=reason_distribution.get)
else:
    dominant_reason = None

# Convergence summary from convergence history cycles
early_stops       = 0
budget_extensions = 0
approach_changes  = 0

for bead_entry in conv_history:
    for cycle in bead_entry.get('cycles', []):
        rec = cycle.get('recommendation', '')
        if rec == 'stop_early':
            early_stops += 1
        elif rec == 'extend_budget':
            budget_extensions += 1
        elif rec == 'change_approach':
            approach_changes += 1

data = {
    'schema_version': 1,
    'task_id':        task_id,
    'artifact_status': status,
    'derived_at':     now,

    'execution_mode': {
        'classification': mode_json['classification'],
        'confidence':     mode_json['confidence'],
        'signals':        mode_json['signals'],
    },

    'convergence_history': conv_history,

    'escalation_log': esc_log,

    # beads_total separate from wip_beads for the system ledger
    '_beads_total': $BEADS_TOTAL,

    'summary': {
        'total_escalations':  total_escalations,
        'reason_distribution': reason_distribution,
        'dominant_reason':    dominant_reason,
        'early_stops':        early_stops,
        'budget_extensions':  budget_extensions,
        'approach_changes':   approach_changes,
        'mode_transitions':   0,  # deferred to v2 — requires per-iteration snapshots
    },
}

with open(output_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Derived {output_path}')
print(f'  mode={data[\"execution_mode\"][\"classification\"]} ({data[\"execution_mode\"][\"confidence\"]})'
      f'  escalations={total_escalations}'
      f'  early_stops={early_stops}'
      f'  status={status}')
" "$MODE_JSON" "$CONV_JSON" "$ESC_JSON" "$TASK_ID" "$STATUS" "$NOW" "$OUTPUT"
