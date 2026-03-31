#!/bin/bash
# decision-noise-lib.sh — Shared helpers for decision-noise controls
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/sdlc-common.sh"

# Generate unique review pass ID
# Usage: generate_review_pass_id
generate_review_pass_id() {
  echo "rp_$(date -u +%Y%m%d_%H%M%S)_$(head -c4 /dev/urandom | xxd -p)"
}

# Compute MAP vector Euclidean distance between two passes
# Usage: map_distance '{"evidence_strength":4,...}' '{"evidence_strength":2,...}'
map_distance() {
  local map1="$1" map2="$2"
  printf '%s\n%s\n' "$map1" "$map2" | python3 -c "
import json, math, sys
lines = sys.stdin.read().strip().split('\n')
m1 = json.loads(lines[0])
m2 = json.loads(lines[1])
dims = ['evidence_strength', 'impact_severity', 'pattern_familiarity', 'decision_confidence']
b1 = m1.get('base_rate_frequency', {}).get('bucket', 3)
b2 = m2.get('base_rate_frequency', {}).get('bucket', 3)
vals = [(m1.get(d, 3) - m2.get(d, 3))**2 for d in dims] + [(b1 - b2)**2]
print(f'{math.sqrt(sum(vals)):.3f}')
"
}

# Check if a review_pass_id already exists in the ledger (idempotent guard)
# Pre-checks with grep before Python parsing to avoid full-file scan when the
# pass_id is not present at all (fast path: grep miss → skip Python entirely).
# Usage: pass_exists "review-passes.jsonl" "rp_20260330_001"
pass_exists() {
  local ledger="$1" pass_id="$2"
  [ -f "$ledger" ] || return 1
  # Fast path: if grep finds no candidate lines, the pass cannot exist
  grep -qF "\"$pass_id\"" "$ledger" || return 1
  # Slow path: grep found a candidate; confirm via proper JSON parse
  python3 -c "
import json, sys
target = sys.argv[1]
with open(sys.argv[2]) as f:
    for line in f:
        try:
            r = json.loads(line.strip())
            if r.get('review_pass_id') == target:
                sys.exit(0)
        except json.JSONDecodeError:
            continue
sys.exit(1)
" "$pass_id" "$ledger"
}

# Append a review pass record (with idempotent guard)
# Usage: append_review_pass "review-passes.jsonl" '{"review_pass_id":"rp_001",...}'
append_review_pass() {
  local ledger="$1" record="$2"
  local pass_id
  pass_id=$(echo "$record" | python3 -c "import json,sys; print(json.load(sys.stdin)['review_pass_id'])")
  if pass_exists "$ledger" "$pass_id"; then
    echo "SKIP: review_pass_id $pass_id already exists (idempotent)" >&2
    return 0
  fi
  mkdir -p "$(dirname "$ledger")"
  echo "$record" >> "$ledger"
}

# Detect soft escalation conditions between two paired passes
# Usage: detect_escalations '{"map":{...},"verdict":{...}}' '{"map":{...},"verdict":{...}}' <rules_file>
detect_escalations() {
  local pass1="$1" pass2="$2" rules="$3"
  printf '%s\n%s\n' "$pass1" "$pass2" | python3 -c "
import json, sys, yaml

lines = sys.stdin.read().strip().split('\n')
p1 = json.loads(lines[0])
p2 = json.loads(lines[1])

with open(sys.argv[1]) as rf:
    rules = yaml.safe_load(rf)
esc_rules = rules.get('soft_escalation', {})
divergence_threshold = esc_rules.get('map_bucket_divergence', 2)
drift_threshold = esc_rules.get('anchoring_drift_buckets', 2)

escalations = []

if esc_rules.get('verdict_flip', True):
    if p1.get('verdict',{}).get('decision') != p2.get('verdict',{}).get('decision'):
        escalations.append('verdict_flip')

m1 = p1.get('map', {}); m2 = p2.get('map', {})
for dim in ['evidence_strength', 'impact_severity']:
    if abs(m1.get(dim, 3) - m2.get(dim, 3)) >= divergence_threshold:
        escalations.append(f'map_divergence_{dim}')

if esc_rules.get('unbacked_high_severity', True):
    for pj in p2.get('probability_judgments', []):
        if pj.get('severity') == 'high' and pj.get('hits') is None:
            brf = m2.get('base_rate_frequency', {})
            if brf.get('reference_class_state') == 'available':
                escalations.append('unbacked_high_severity')

if p2.get('parent_review_pass_id') and p2.get('anchor_map_targets_seen'):
    anchor = p2['anchor_map_targets_seen'][0] if p2['anchor_map_targets_seen'] else {}
    for dim in ['evidence_strength', 'impact_severity', 'pattern_familiarity']:
        blind_val = m1.get(dim, 3)
        exposed_val = m2.get(dim, 3)
        anchor_val = anchor.get(dim, 3) if isinstance(anchor, dict) else 3
        if abs(exposed_val - anchor_val) < abs(blind_val - anchor_val) and abs(exposed_val - blind_val) >= drift_threshold:
            escalations.append(f'anchoring_drift_{dim}')

print(json.dumps(escalations))
" "$rules"
}

# Compute noise index across a set of paired passes
# Pre-filters the ledger with grep before Python parsing, reducing Python work
# from O(total_ledger) to O(task_records).
# Usage: compute_noise_index "review-passes.jsonl" "task_id"
compute_noise_index() {
  local ledger="$1" task_id="$2"
  # Pre-filter: grep for the task_id VALUE (not key:value pair) to handle both
  # compact JSON ("task_id":"x") and spaced JSON ("task_id": "x") from json.dumps.
  { [ -f "$ledger" ] && grep -F "\"$task_id\"" "$ledger"; } 2>/dev/null | python3 -c "
import json, math, sys

passes = []
for line in sys.stdin:
    try:
        r = json.loads(line.strip())
        if r.get('task_id') == '$task_id':
            passes.append(r)
    except json.JSONDecodeError:
        continue

# Find repeat-review pairs
groups = {}
for p in passes:
    gid = p.get('repeat_review_group_id')
    if gid:
        groups.setdefault(gid, []).append(p)

if not groups:
    print(json.dumps({'noise_index': None, 'pairs': 0}))
    sys.exit(0)

distances = []
dims = ['evidence_strength', 'impact_severity', 'pattern_familiarity', 'decision_confidence']
for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) >= 2:
        m1, m2 = blind[0]['map'], blind[1]['map']
        d = math.sqrt(sum((m1.get(d,3)-m2.get(d,3))**2 for d in dims) +
            (m1.get('base_rate_frequency',{}).get('bucket',3)-m2.get('base_rate_frequency',{}).get('bucket',3))**2)
        distances.append(d)

avg = sum(distances)/len(distances) if distances else None
print(json.dumps({'noise_index': round(avg,3) if avg else None, 'pairs': len(distances)}))
"
}

# now_utc() provided by sdlc-common.sh
