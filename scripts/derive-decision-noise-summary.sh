#!/bin/bash
# derive-decision-noise-summary.sh — Compute decision-noise-summary.yaml from review-passes.jsonl
# Usage: derive-decision-noise-summary.sh <task-id> <project-dir> [--status partial|final]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/decision-noise-lib.sh"

if ! python3 -c "import yaml" 2>/dev/null; then
  echo "ERROR: python3 with PyYAML is required. Install: pip3 install pyyaml" >&2
  exit 1
fi

TASK_ID="${1:?Usage: derive-decision-noise-summary.sh <task-id> <project-dir> [--status partial|final]}"
PROJECT_DIR="${2:?Usage: derive-decision-noise-summary.sh <task-id> <project-dir> [--status partial|final]}"
STATUS="${3:-partial}"
# Accept --status <value> or bare value
if [ "$STATUS" = "--status" ]; then
  STATUS="${4:-partial}"
fi

LEDGER="$PROJECT_DIR/docs/sdlc/decision-noise/review-passes.jsonl"
OUTPUT_DIR="$PROJECT_DIR/docs/sdlc/active/$TASK_ID"
OUTPUT="$OUTPUT_DIR/decision-noise-summary.yaml"
RULES_FILE="$SCRIPT_DIR/../references/decision-noise-rules.yaml"

[ -f "$LEDGER" ] || { echo "ERROR: review-passes.jsonl not found: $LEDGER" >&2; exit 1; }

case "$STATUS" in
  partial|final) ;;
  *) echo "ERROR: --status must be 'partial' or 'final', got: $STATUS" >&2; exit 1 ;;
esac

NOW=$(now_utc)

# Compute repeat_review_noise_index via shared lib function
NOISE_RESULT=$(compute_noise_index "$LEDGER" "$TASK_ID")

# Compute all remaining metrics in a single Python pass over the ledger
METRICS=$(python3 - "$TASK_ID" "$LEDGER" "$RULES_FILE" << 'PYEOF'
import json, math, sys, yaml

task_id     = sys.argv[1]
ledger_path = sys.argv[2]
rules_path  = sys.argv[3]

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

with open(rules_path) as rf:
    rules = yaml.safe_load(rf)
esc_rules            = rules.get('soft_escalation', {})
divergence_threshold = esc_rules.get('map_bucket_divergence', 2)
drift_threshold      = esc_rules.get('anchoring_drift_buckets', 2)

beads_reviewed = len(set(p.get('bead_id') for p in passes if p.get('bead_id')))
passes_total   = len(passes)

# Repeat-review groups (shared repeat_review_group_id)
groups = {}
for p in passes:
    gid = p.get('repeat_review_group_id')
    if gid:
        groups.setdefault(gid, []).append(p)

repeat_review_pairs = 0
for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) >= 2:
        repeat_review_pairs += 1

# weighted_verdict_agreement
agree_count = 0
pair_count  = 0
for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) >= 2:
        pair_count += 1
        d1 = blind[0].get('verdict', {}).get('decision')
        d2 = blind[1].get('verdict', {}).get('decision')
        if d1 and d2 and d1 == d2:
            agree_count += 1
weighted_verdict_agreement = round(agree_count / pair_count, 3) if pair_count > 0 else None

# map_convergence_score — inverse dispersion across passes for each bead
bead_passes = {}
for p in passes:
    bid = p.get('bead_id')
    if bid and 'map' in p:
        bead_passes.setdefault(bid, []).append(p['map'])

dims = ['evidence_strength', 'impact_severity', 'pattern_familiarity', 'decision_confidence']
bead_convergences = []
for bid, maps in bead_passes.items():
    if len(maps) < 2:
        bead_convergences.append(1.0)
        continue
    pair_dists = []
    for i in range(len(maps)):
        for j in range(i + 1, len(maps)):
            m1, m2 = maps[i], maps[j]
            b1 = m1.get('base_rate_frequency', {}).get('bucket', 3) if isinstance(m1.get('base_rate_frequency'), dict) else 3
            b2 = m2.get('base_rate_frequency', {}).get('bucket', 3) if isinstance(m2.get('base_rate_frequency'), dict) else 3
            sq = sum((m1.get(d, 3) - m2.get(d, 3))**2 for d in dims) + (b1 - b2)**2
            pair_dists.append(math.sqrt(sq))
    mean_dist = sum(pair_dists) / len(pair_dists)
    bead_convergences.append(round(1.0 / (1.0 + mean_dist), 3))
map_convergence_score = round(sum(bead_convergences) / len(bead_convergences), 3) if bead_convergences else None

# anchoring_drift_rate — exposed passes with 2+ bucket shift toward anchor
by_pass_id    = {p['review_pass_id']: p for p in passes if 'review_pass_id' in p}
exposed_passes = [p for p in passes if p.get('parent_review_pass_id')]
drift_count   = 0
for ep in exposed_passes:
    parent = by_pass_id.get(ep['parent_review_pass_id'])
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
            drift_count += 1
            break
anchoring_drift_rate = round(drift_count / len(exposed_passes), 3) if exposed_passes else None

# natural_frequency_coverage
all_judgments = [pj for p in passes for pj in p.get('probability_judgments', [])]
backed        = [pj for pj in all_judgments if pj.get('hits') is not None]
natural_frequency_coverage = round(len(backed) / len(all_judgments), 3) if all_judgments else None

# high_severity_unbacked_claims
high_severity_unbacked = sum(
    1 for p in passes
    for pj in p.get('probability_judgments', [])
    if pj.get('severity') == 'high'
    and pj.get('hits') is None
    and (p.get('map', {}).get('base_rate_frequency') or {}).get('reference_class_state') == 'available'
)

# spot_check_coverage_rate
eligible_beads = set(p['bead_id'] for p in passes if p.get('arbiter_group_id') and p.get('bead_id'))
spot_checked   = set(p['bead_id'] for p in passes if p.get('repeat_review_group_id') and p.get('bead_id'))
spot_check_coverage_rate = (
    round(len(spot_checked & eligible_beads) / len(eligible_beads), 3)
    if eligible_beads else None
)

# Escalation counts
esc_verdict_flips     = 0
esc_map_divergence    = 0
esc_anchoring_drift   = 0
esc_unbacked_high_sev = high_severity_unbacked

for gid, members in groups.items():
    blind = [m for m in members if m.get('exposure_mode') == 'blind_first']
    if len(blind) < 2:
        continue
    p1, p2 = blind[0], blind[1]
    m1, m2 = p1.get('map', {}), p2.get('map', {})
    if p1.get('verdict', {}).get('decision') != p2.get('verdict', {}).get('decision'):
        esc_verdict_flips += 1
    for dim in ['evidence_strength', 'impact_severity']:
        if abs(m1.get(dim, 3) - m2.get(dim, 3)) >= divergence_threshold:
            esc_map_divergence += 1
            break

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
            esc_anchoring_drift += 1
            break

result = {
    'beads_reviewed':               beads_reviewed,
    'passes_total':                 passes_total,
    'repeat_review_pairs':          repeat_review_pairs,
    'weighted_verdict_agreement':   weighted_verdict_agreement,
    'map_convergence_score':        map_convergence_score,
    'anchoring_drift_rate':         anchoring_drift_rate,
    'natural_frequency_coverage':   natural_frequency_coverage,
    'high_severity_unbacked_claims': high_severity_unbacked,
    'spot_check_coverage_rate':     spot_check_coverage_rate,
    'esc_verdict_flips':            esc_verdict_flips,
    'esc_map_divergence':           esc_map_divergence,
    'esc_anchoring_drift':          esc_anchoring_drift,
    'esc_unbacked_high_sev':        esc_unbacked_high_sev,
}
print(json.dumps(result))
PYEOF
)

# Extract noise_index from shared-lib result
NOISE_INDEX=$(echo "$NOISE_RESULT" | python3 -c "import json,sys; r=json.load(sys.stdin); v=r.get('noise_index'); print('null' if v is None else v)")

mkdir -p "$OUTPUT_DIR"

echo "$METRICS" | python3 - "$NOISE_INDEX" "$TASK_ID" "$STATUS" "$NOW" "$OUTPUT" << 'PYEOF'
import json, yaml, sys

metrics_raw = json.loads(sys.stdin.read())
noise_index_raw = sys.argv[1]
task_id = sys.argv[2]
status = sys.argv[3]
now = sys.argv[4]
output_path = sys.argv[5]

ni = None if noise_index_raw == 'null' else float(noise_index_raw)

data = {
    'schema_version':  1,
    'task_id':         task_id,
    'artifact_status': status,
    'derived_at':      now,

    'beads_reviewed':      metrics_raw['beads_reviewed'],
    'passes_total':        metrics_raw['passes_total'],
    'repeat_review_pairs': metrics_raw['repeat_review_pairs'],

    'metrics': {
        'repeat_review_noise_index':     ni,
        'weighted_verdict_agreement':    metrics_raw['weighted_verdict_agreement'],
        'map_convergence_score':         metrics_raw['map_convergence_score'],
        'anchoring_drift_rate':          metrics_raw['anchoring_drift_rate'],
        'natural_frequency_coverage':    metrics_raw['natural_frequency_coverage'],
        'high_severity_unbacked_claims': metrics_raw['high_severity_unbacked_claims'],
        'spot_check_coverage_rate':      metrics_raw['spot_check_coverage_rate'],
    },

    'escalations': {
        'verdict_flips':          metrics_raw['esc_verdict_flips'],
        'map_divergence_2plus':   metrics_raw['esc_map_divergence'],
        'anchoring_drift_2plus':  metrics_raw['esc_anchoring_drift'],
        'unbacked_high_severity': metrics_raw['esc_unbacked_high_sev'],
    },
}

with open(output_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"Derived {output_path}")
print(f"  passes={data['passes_total']}  beads={data['beads_reviewed']}  noise_index={data['metrics']['repeat_review_noise_index']}  status={status}")
PYEOF
