#!/bin/bash
# evaluate-escalations.sh — Evaluate decision-noise escalation signals and emit advisory
# Usage: evaluate-escalations.sh <task-id> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/decision-noise-lib.sh"

if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_ID="${1:?Usage: evaluate-escalations.sh <task-id> <project-dir>}"
PROJECT_DIR="${2:?Usage: evaluate-escalations.sh <task-id> <project-dir>}"

LEDGER="$PROJECT_DIR/docs/sdlc/decision-noise/review-passes.jsonl"
RULES_FILE="$SCRIPT_DIR/../references/decision-noise-rules.yaml"

[ -f "$LEDGER" ] || { echo "ERROR: review-passes.jsonl not found: $LEDGER" >&2; exit 1; }
[ -f "$RULES_FILE" ] || { echo "ERROR: decision-noise-rules.yaml not found: $RULES_FILE" >&2; exit 1; }

python3 << PYEOF
import json, sys, yaml

task_id     = "$TASK_ID"
ledger_path = "$LEDGER"
rules_path  = "$RULES_FILE"

# Load rules — thresholds sourced from file, never hardcoded
with open(rules_path) as rf:
    rules = yaml.safe_load(rf)
esc_rules            = rules.get('soft_escalation', {})
divergence_threshold = esc_rules.get('map_bucket_divergence', 2)
drift_threshold      = esc_rules.get('anchoring_drift_buckets', 2)

# Load all passes for this task
passes = []
with open(ledger_path) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get('task_id') == task_id:
            passes.append(r)

# Index passes by review_pass_id for lineage lookups
by_pass_id = {p['review_pass_id']: p for p in passes if 'review_pass_id' in p}

# --- Repeat-review pairs: shared repeat_review_group_id, both blind_first ---
groups = {}
for p in passes:
    gid = p.get('repeat_review_group_id')
    if gid:
        groups.setdefault(gid, []).append(p)

# --- Blind→exposed lineage pairs: parent_review_pass_id present ---
exposed_passes = [p for p in passes if p.get('parent_review_pass_id')]

# 1. Verdict flips — blind pairs with differing verdict decisions
verdict_flips = 0
for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) < 2:
        continue
    p1, p2 = blind[0], blind[1]
    d1 = p1.get('verdict', {}).get('decision')
    d2 = p2.get('verdict', {}).get('decision')
    if d1 and d2 and d1 != d2:
        verdict_flips += 1

# 2. MAP bucket divergence — evidence_strength or impact_severity differ by N+ buckets
#    (threshold: soft_escalation.map_bucket_divergence)
map_divergence = 0
for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) < 2:
        continue
    p1, p2 = blind[0], blind[1]
    m1, m2 = p1.get('map', {}), p2.get('map', {})
    for dim in ['evidence_strength', 'impact_severity']:
        if abs(m1.get(dim, 3) - m2.get(dim, 3)) >= divergence_threshold:
            map_divergence += 1
            break

# 3. Anchoring drift — exposed pass shifts N+ buckets toward anchor target
#    (threshold: soft_escalation.anchoring_drift_buckets)
anchoring_drift = 0
for ep in exposed_passes:
    parent = by_pass_id.get(ep.get('parent_review_pass_id', ''))
    if not parent:
        continue
    m_blind   = parent.get('map', {})
    m_exposed = ep.get('map', {})
    anchors   = ep.get('anchor_map_targets_seen', [])
    anchor    = anchors[0] if anchors and isinstance(anchors[0], dict) else {}
    for dim in ['evidence_strength', 'impact_severity', 'pattern_familiarity']:
        blind_val   = m_blind.get(dim, 3)
        exposed_val = m_exposed.get(dim, 3)
        anchor_val  = anchor.get(dim, 3)
        if (abs(exposed_val - anchor_val) < abs(blind_val - anchor_val) and
                abs(exposed_val - blind_val) >= drift_threshold):
            anchoring_drift += 1
            break

# 4. Unbacked high-severity claims — only when reference_class_state: available but hits is null
unbacked_high_sev = 0
for p in passes:
    brf_state = (p.get('map', {}).get('base_rate_frequency') or {}).get('reference_class_state')
    if brf_state != 'available':
        continue
    for pj in p.get('probability_judgments', []):
        if pj.get('severity') == 'high' and pj.get('hits') is None:
            unbacked_high_sev += 1

# --- Recommendation logic ---
if verdict_flips > 0 or (map_divergence > 0 and anchoring_drift > 0):
    recommendation = "re-review recommended"
elif map_divergence > 0 or anchoring_drift > 0 or unbacked_high_sev > 0:
    recommendation = "second arbiter pass recommended"
else:
    recommendation = "no action"

# --- Output advisory ---
print(f"=== Decision-Noise Escalation Advisory: {task_id} ===")
print(f"Verdict flips: {verdict_flips}")
print(f"MAP divergence ({divergence_threshold}+ buckets): {map_divergence}")
print(f"Anchoring drift ({drift_threshold}+ toward anchor): {anchoring_drift}")
print(f"Unbacked high-severity claims: {unbacked_high_sev}")
print(f"Recommendation: {recommendation}")
PYEOF
