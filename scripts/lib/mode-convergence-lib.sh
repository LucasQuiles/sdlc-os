#!/bin/bash
# mode-convergence-lib.sh — Shared helpers for mode & convergence signals
set -euo pipefail

# PyYAML dependency guard
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: PyYAML is required. Install with: pip install pyyaml" >&2
  exit 1
fi

# Classify one SRK signal. Returns: skill_based | rule_based | knowledge_based
# Usage: classify_signal "turbulence_sum_per_bead" 0.5 <rules_file>
classify_signal() {
  local signal="$1" value="$2" rules="$3"
  python3 -c "
import yaml, sys
with open(sys.argv[3]) as f:
    rules = yaml.safe_load(f)
thresholds = rules['srk_thresholds'][sys.argv[1]]
val = float(sys.argv[2])
skill_max = thresholds.get('skill_max')
skill_min = thresholds.get('skill_min')
knowledge_min = thresholds.get('knowledge_min')
knowledge_max = thresholds.get('knowledge_max')

if skill_max is not None and (val < skill_max or (skill_max == 0 and val == 0)):
    print('skill_based')
elif skill_min is not None and val > skill_min:
    print('skill_based')
elif knowledge_min is not None and val > knowledge_min:
    print('knowledge_based')
elif knowledge_max is not None and val < knowledge_max:
    print('knowledge_based')
else:
    print('rule_based')
" "$signal" "$value" "$rules"
}

# Classify execution mode from 4 signals. Returns JSON: {classification, confidence}
# Usage: classify_execution_mode turb_per_bead zero_turb_rate latency_p95 escalation_count <rules_file>
classify_execution_mode() {
  local tpb="$1" ztr="$2" lat="$3" esc="$4" rules="$5"
  python3 -c "
import yaml, sys, json
with open(sys.argv[5]) as f:
    rules = yaml.safe_load(f)
t = rules['srk_thresholds']

def classify(signal, val):
    th = t[signal]
    skill_max = th.get('skill_max')
    skill_min = th.get('skill_min')
    knowledge_min = th.get('knowledge_min')
    knowledge_max = th.get('knowledge_max')
    if skill_max is not None and (val < skill_max or (skill_max == 0 and val == 0)): return 'skill_based'
    if skill_min is not None and val > skill_min: return 'skill_based'
    if knowledge_min is not None and val > knowledge_min: return 'knowledge_based'
    if knowledge_max is not None and val < knowledge_max: return 'knowledge_based'
    return 'rule_based'

votes = [
    classify('turbulence_sum_per_bead', float(sys.argv[1])),
    classify('zero_turbulence_rate', float(sys.argv[2])),
    classify('review_latency_p95_s', float(sys.argv[3])),
    classify('escalation_count', float(sys.argv[4])),
]

from collections import Counter
counts = Counter(votes)
winner, win_count = counts.most_common(1)[0]
if win_count == 4:
    conf = 'high'
elif win_count == 3:
    conf = 'medium'
else:
    winner = 'rule_based'
    conf = 'low'

print(json.dumps({'classification': winner, 'confidence': conf}))
" "$tpb" "$ztr" "$lat" "$esc" "$rules"
}

# Compute severity_trend between two cycles
# Usage: compute_severity_trend '["P2","P3"]' '["P1","P3"]' <rules_file>
compute_severity_trend() {
  local prev_severities="$1" curr_severities="$2" rules="$3"
  python3 -c "
import yaml, sys, json
with open(sys.argv[3]) as f:
    rules = yaml.safe_load(f)
ordinal = rules['convergence']['severity_ordinal']

prev = json.loads(sys.argv[1])
curr = json.loads(sys.argv[2])

if not prev:
    print('stable')
    sys.exit(0)

max_prev = max(ordinal.get(s, 0) for s in prev) if prev else 0
max_curr = max(ordinal.get(s, 0) for s in curr) if curr else 0

if max_curr > max_prev:
    print('escalating')
elif max_curr < max_prev:
    print('declining')
else:
    print('stable')
" "$prev_severities" "$curr_severities" "$rules"
}

# Compute Shannon entropy of finding categories
# Usage: compute_entropy '["security","security","functionality"]'
compute_entropy() {
  local categories="$1"
  python3 -c "
import json, math, sys
from collections import Counter
cats = json.loads(sys.argv[1])
if not cats:
    print('0.0')
    sys.exit(0)
counts = Counter(cats)
total = len(cats)
entropy = -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)
print(f'{entropy:.3f}')
" "$categories"
}

# Compute full convergence signal from cycle data
# Usage: compute_convergence_signal new_findings repeated_findings severity_trend entropy_estimate original_budget current_cycle <rules_file>
# IMPORTANT: original_budget is the INITIAL budget, not the current (possibly extended) budget.
# This prevents runaway extensions past 2x the original.
compute_convergence_signal() {
  local new="$1" repeated="$2" sev_trend="$3" entropy="$4" original_budget="$5" cycle="$6" rules="$7"
  python3 -c "
import yaml, sys, json
with open(sys.argv[7]) as f:
    rules = yaml.safe_load(f)
c = rules['convergence']
rec = rules['convergence_recommendations']
max_mult = rules.get('max_budget_multiplier', 2)

new_f = int(sys.argv[1])
repeated_f = int(sys.argv[2])
sev_trend = sys.argv[3]
entropy = float(sys.argv[4])
original_budget = int(sys.argv[5])  # INITIAL budget, not current
cycle = int(sys.argv[6])

total = new_f + repeated_f
evidence_rate = new_f / total if total > 0 else 0.0

if evidence_rate >= c['evidence_rate_converging'] and sev_trend != 'escalating':
    state = 'converging'
elif sev_trend == 'escalating':
    state = 'diverging'
elif evidence_rate < c['evidence_rate_stable'] and entropy < c['entropy_stuck_threshold']:
    state = 'stuck'  # low evidence + low entropy = same issues repeating, loop is stuck
elif evidence_rate < c['evidence_rate_stable'] and sev_trend == 'stable':
    state = 'stable'  # low evidence + diverse categories = genuinely exhausted search space
else:
    state = 'stuck'

if state == 'converging':
    recommendation = rec['converging']
elif state == 'stable':
    recommendation = rec['stable']
elif state == 'diverging':
    recommendation = rec['diverging']
elif state == 'stuck':
    if cycle < original_budget * max_mult:
        recommendation = rec['stuck_within_budget']
    else:
        recommendation = rec['stuck_over_budget']

print(json.dumps({
    'cycle': cycle,
    'new_findings': new_f,
    'repeated_findings': repeated_f,
    'evidence_rate': round(evidence_rate, 3),
    'severity_trend': sev_trend,
    'entropy_estimate': float(sys.argv[4]),
    'convergence_state': state,
    'recommendation': recommendation
}))
" "$new" "$repeated" "$sev_trend" "$entropy" "$original_budget" "$cycle" "$rules"
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
