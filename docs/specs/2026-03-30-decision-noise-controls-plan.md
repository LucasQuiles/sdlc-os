# Decision-Noise Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add MAP-style dimension scoring, repeat-review noise measurement, natural-frequency probability claims, and anchoring-drift detection to the AQS review stack — advisory-only, no hard gates in v1.

**Architecture:** System-level append-only review-passes JSONL with idempotent writes, per-task derived summary YAML, externalized rules, blind-first → precedent-exposed two-pass anti-anchoring protocol, soft escalation signals.

**Tech Stack:** JSONL (canonical ledger), YAML (rules, per-task summary), Bash + Python3/PyYAML (scripts), Markdown (docs)

**Spec:** `docs/specs/2026-03-30-decision-noise-controls-design.md`

**Slice order:** Contract → Capture → Derivation → Reporting → Verification

**Deferred:** Hard gates, broad red/blue MAP integration, full cue-validation backfill, reference class database.

---

### Task 1: Define the contract — rules, schema docs, shared library

**Files:**
- Create: `references/decision-noise-rules.yaml`
- Create: `references/decision-noise-schema.md`
- Create: `scripts/lib/decision-noise-lib.sh`

- [ ] **Step 1: Create the rules file**

Write `references/decision-noise-rules.yaml`:

```yaml
# Decision-Noise Rules — externalized thresholds and sampling rates
schema_version: 1

# MAP scale
map_scale:
  min: 1
  max: 5
  dimensions:
    - evidence_strength
    - impact_severity
    - base_rate_frequency
    - pattern_familiarity
    - decision_confidence
  post_exposure_dimensions:
    - precedent_match_delta  # -5 to +5, null on blind passes

# Reference class states
reference_class_states:
  - available             # class exists with >= 5 samples
  - insufficient_history  # class exists with < 5 samples
  - not_applicable        # no meaningful reference class

# Repeat-review sampling rates
repeat_review_sampling:
  complex_aqs: 0.20       # 20% of complex beads with AQS
  complicated_aqs: 0.10   # 10% of complicated beads with AQS
  clear: 0.00             # incident-triggered only
  minimum_per_task: 1     # when any complex bead exists

# Soft escalation thresholds
soft_escalation:
  verdict_flip: true                  # blind pair produces different decision class
  map_bucket_divergence: 2            # evidence_strength or impact_severity differs by N+ buckets
  anchoring_drift_buckets: 2          # post-exposure MAP shifts N+ toward anchor target
  unbacked_high_severity: true        # high-severity + reference_class_state: available + no hits/sample
  # NOT triggered for insufficient_history or not_applicable

# Review stages
review_stages:
  - arbiter_pre_synthesis
  - red_team
  - blue_team
  - repeat_blind
  - repeat_exposed

# Exposure modes
exposure_modes:
  - blind_first
  - precedent_exposed
  - peer_exposed
  - full_context

# Verdict decisions
verdict_decisions:
  - escalate
  - accept
  - dismiss
  - defer

# Severity levels
severity_levels:
  - P1
  - P2
  - P3
  - P4
```

- [ ] **Step 2: Create the schema docs**

Write `references/decision-noise-schema.md` from the design spec. Include:
- Review pass JSONL record schema (all fields including lineage: schema_version, parent_review_pass_id, supersedes_review_pass_id)
- Append-only invariants (immutable records, idempotent write key, lineage rules)
- MAP vector definition (5 blind dimensions + 1 post-exposure delta)
- reference_class_state enum with null-path rules
- Per-task decision-noise-summary.yaml schema
- Noise events JSONL schema
- Anti-anchoring protocol (blind-first → exposed)
- Soft escalation conditions with computable definitions
- Derived metrics definitions with formulas

- [ ] **Step 3: Create the shared library**

Write `scripts/lib/decision-noise-lib.sh`:

```bash
#!/bin/bash
# decision-noise-lib.sh — Shared helpers for decision-noise controls
set -euo pipefail

# Generate unique review pass ID
# Usage: generate_review_pass_id
generate_review_pass_id() {
  echo "rp_$(date -u +%Y%m%d_%H%M%S)_$(head -c4 /dev/urandom | xxd -p)"
}

# Compute MAP vector Euclidean distance between two passes
# Usage: map_distance '{"evidence_strength":4,...}' '{"evidence_strength":2,...}'
map_distance() {
  local map1="$1" map2="$2"
  python3 -c "
import json, math
m1 = json.loads('''$map1''')
m2 = json.loads('''$map2''')
dims = ['evidence_strength', 'impact_severity', 'pattern_familiarity', 'decision_confidence']
# base_rate_frequency uses bucket field
b1 = m1.get('base_rate_frequency', {}).get('bucket', 3)
b2 = m2.get('base_rate_frequency', {}).get('bucket', 3)
vals = [(m1.get(d, 3) - m2.get(d, 3))**2 for d in dims] + [(b1 - b2)**2]
print(f'{math.sqrt(sum(vals)):.3f}')
"
}

# Check if a review_pass_id already exists in the ledger (idempotent guard)
# Uses python3 JSON parsing — not grep — to handle any whitespace formatting
# Usage: pass_exists "review-passes.jsonl" "rp_20260330_001"
pass_exists() {
  local ledger="$1" pass_id="$2"
  [ -f "$ledger" ] || return 1
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
  python3 -c "
import json, sys, yaml

p1 = json.loads('''$pass1''')
p2 = json.loads('''$pass2''')

# Read thresholds from rules file (not hardcoded)
with open('$rules') as rf:
    rules = yaml.safe_load(rf)
esc_rules = rules.get('soft_escalation', {})
divergence_threshold = esc_rules.get('map_bucket_divergence', 2)
drift_threshold = esc_rules.get('anchoring_drift_buckets', 2)

escalations = []

# Verdict flip
if esc_rules.get('verdict_flip', True):
    if p1.get('verdict',{}).get('decision') != p2.get('verdict',{}).get('decision'):
        escalations.append('verdict_flip')

# MAP bucket divergence (threshold from rules)
m1 = p1.get('map', {}); m2 = p2.get('map', {})
for dim in ['evidence_strength', 'impact_severity']:
    if abs(m1.get(dim, 3) - m2.get(dim, 3)) >= divergence_threshold:
        escalations.append(f'map_divergence_{dim}')

# Unbacked high-severity claims (available reference class but no hits/sample)
if esc_rules.get('unbacked_high_severity', True):
    for pj in p2.get('probability_judgments', []):
        if pj.get('severity') == 'high' and pj.get('hits') is None:
            # Only escalate if a reference class is available but not used
            brf = m2.get('base_rate_frequency', {})
            if brf.get('reference_class_state') == 'available':
                escalations.append('unbacked_high_severity')

# Anchoring drift (post-exposure shift toward anchor)
if p2.get('parent_review_pass_id') and p2.get('anchor_map_targets_seen'):
    anchor = p2['anchor_map_targets_seen'][0] if p2['anchor_map_targets_seen'] else {}
    for dim in ['evidence_strength', 'impact_severity', 'pattern_familiarity']:
        blind_val = m1.get(dim, 3)
        exposed_val = m2.get(dim, 3)
        anchor_val = anchor.get(dim, 3) if isinstance(anchor, dict) else 3
        # Drift toward anchor?
        if abs(exposed_val - anchor_val) < abs(blind_val - anchor_val) and abs(exposed_val - blind_val) >= drift_threshold:
            escalations.append(f'anchoring_drift_{dim}')

print(json.dumps(escalations))
"
}

# Compute noise index across a set of paired passes
# Usage: compute_noise_index "review-passes.jsonl" "task_id"
compute_noise_index() {
  local ledger="$1" task_id="$2"
  python3 -c "
import json, math, sys

passes = []
with open('$ledger') as f:
    for line in f:
        r = json.loads(line.strip())
        if r.get('task_id') == '$task_id':
            passes.append(r)

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

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
```

Make executable: `chmod +x scripts/lib/decision-noise-lib.sh`

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/decision-noise-rules.yaml references/decision-noise-schema.md scripts/lib/decision-noise-lib.sh
git commit -m "feat: add decision-noise contract — rules, schema, shared library

Externalized rules (sampling rates, MAP scale, escalation thresholds).
Schema docs (review pass JSONL, lineage, MAP vector, anti-anchoring,
noise events). Shared lib (MAP distance, idempotent append, escalation
detection, noise index computation)."
```

---

### Task 2: Implement capture — record-review-pass script

**Files:**
- Create: `scripts/record-review-pass.sh`

- [ ] **Step 1: Create the record script**

Write `scripts/record-review-pass.sh`. Takes a JSON record on stdin or as argument. Validates required fields (schema_version, review_pass_id, task_id, bead_id, review_stage, exposure_mode, map). Enforces idempotent append via `append_review_pass` from the shared lib. Creates the ledger directory if needed.

```bash
#!/bin/bash
# record-review-pass.sh — Append one review pass to the canonical ledger
# Usage: echo '<json>' | record-review-pass.sh <project-dir>
#    or: record-review-pass.sh <project-dir> '<json>'
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/decision-noise-lib.sh"

PROJECT_DIR="${1:?Usage: record-review-pass.sh <project-dir> [json]}"
LEDGER="$PROJECT_DIR/docs/sdlc/decision-noise/review-passes.jsonl"

# Read record from argument or stdin
if [ -n "${2:-}" ]; then
  RECORD="$2"
else
  RECORD=$(cat)
fi

# Validate required fields
python3 -c "
import json, sys
r = json.loads('''$RECORD''')
required = ['schema_version', 'review_pass_id', 'task_id', 'bead_id', 'review_stage', 'exposure_mode', 'map']
missing = [f for f in required if f not in r or r[f] is None]
if missing:
    print(f'ERROR: Missing required fields: {missing}', file=sys.stderr)
    sys.exit(1)
# Validate MAP has required dimensions
map_fields = r.get('map', {})
map_required = ['evidence_strength', 'impact_severity', 'base_rate_frequency', 'pattern_familiarity', 'decision_confidence']
map_missing = [f for f in map_required if f not in map_fields]
if map_missing:
    print(f'ERROR: MAP missing dimensions: {map_missing}', file=sys.stderr)
    sys.exit(1)
"

append_review_pass "$LEDGER" "$RECORD"
echo "Recorded review pass to $LEDGER"
```

Make executable.

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/record-review-pass.sh
git add scripts/record-review-pass.sh
git commit -m "feat: add review pass capture script with idempotent append

Validates required fields and MAP dimensions. Enforces idempotent
write key on review_pass_id. Creates ledger directory on first write."
```

---

### Task 3: Implement derivation — summary and escalation scripts

**Files:**
- Create: `scripts/derive-decision-noise-summary.sh`
- Create: `scripts/evaluate-escalations.sh`

- [ ] **Step 1: Create the summary derivation script**

Write `scripts/derive-decision-noise-summary.sh`. Takes `<task-id>` and `<project-dir>`. Reads review-passes.jsonl, filters by task_id, computes all metrics (noise_index, verdict_agreement, map_convergence, anchoring_drift, natural_frequency_coverage, spot_check_coverage, escalation counts). Writes `docs/sdlc/active/{task-id}/decision-noise-summary.yaml`.

Uses python3+PyYAML. Sources decision-noise-lib.sh. Add PyYAML guard.

- [ ] **Step 2: Create the escalation evaluation script**

Write `scripts/evaluate-escalations.sh`. Takes `<task-id>` and `<project-dir>`. Reads review-passes.jsonl, finds repeat-review pairs and blind→exposed lineage pairs, runs `detect_escalations` from the shared lib, outputs advisory report to stdout.

Advisory output format:
```
=== Decision-Noise Escalation Advisory: {task-id} ===
Verdict flips: N
MAP divergence (2+ buckets): N
Anchoring drift (2+ toward anchor): N
Unbacked high-severity claims: N
Recommendation: {no action | second arbiter pass recommended | re-review recommended}
```

- [ ] **Step 3: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/derive-decision-noise-summary.sh scripts/evaluate-escalations.sh
git add scripts/derive-decision-noise-summary.sh scripts/evaluate-escalations.sh
git commit -m "feat: add decision-noise summary derivation and escalation evaluation

Summary script computes noise index, agreement, convergence, drift,
frequency coverage from review-passes.jsonl. Escalation script detects
verdict flips, MAP divergence, anchoring drift, unbacked claims."
```

---

### Task 4: Add validation hook + tests + fixtures

**Files:**
- Create: `hooks/scripts/validate-decision-noise-summary.sh`
- Create: `hooks/tests/fixtures/dn-valid/decision-noise-summary.yaml`
- Create: `hooks/tests/fixtures/dn-missing/decision-noise-summary.yaml`
- Create: `hooks/tests/fixtures/dn-malformed/decision-noise-summary.yaml`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create validation hook**

PostToolUse hook for `decision-noise-summary.yaml`. Validates YAML parse, required fields (schema_version, task_id, artifact_status), artifact_status enum (partial|final), required sections (metrics, escalations). Make executable.

- [ ] **Step 2: Create fixtures**

Valid fixture with all metrics populated. Missing fixture with only schema_version + task_id. Malformed fixture.

- [ ] **Step 3: Update hooks.json and test-hooks.sh**

Add PostToolUse entry. Add 4 tests using temp-file + run_test pattern. Update test count.

- [ ] **Step 4: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (54/54).

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-decision-noise-summary.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/dn-valid/decision-noise-summary.yaml hooks/tests/fixtures/dn-missing/decision-noise-summary.yaml hooks/tests/fixtures/dn-malformed/decision-noise-summary.yaml
git commit -m "feat: add decision-noise summary validation hook with tests

PostToolUse hook validates decision-noise-summary.yaml structure.
4 test cases with 3 fixtures."
```

---

### Task 5: Wire into orchestrate and adversarial — capture integration

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`
- Modify: `skills/sdlc-adversarial/SKILL.md`
- Modify: `skills/sdlc-adversarial/arbitration-protocol.md`

- [ ] **Step 1: Update orchestrate SKILL.md**

Add repeat-review sampling during AQS phase: "After AQS domain probes complete, evaluate repeat-review sampling per `references/decision-noise-rules.yaml`. For sampled beads, dispatch a second blind pass with `review_stage: repeat_blind` and `exposure_mode: blind_first`, sharing a `repeat_review_group_id` with the original `arbiter_pre_synthesis` pass. Both passes recorded via `scripts/record-review-pass.sh`."

Add to Synthesize: "Run `scripts/derive-decision-noise-summary.sh` and `scripts/evaluate-escalations.sh`. Include escalation advisory in delivery summary."

Add noise artifacts to inventory: `decision-noise-summary.yaml`, `review-passes.jsonl`. (`noise-events.jsonl` deferred to v2 — no producer in v1.)

- [ ] **Step 2: Update adversarial SKILL.md**

Add MAP vector requirement: "Every arbiter pre-synthesis pass MUST produce a structured MAP vector (5 blind dimensions + verdict). The arbiter receives bead evidence and decision trace but NOT prior verdicts or peer findings (blind-first protocol). MAP vector is recorded via `scripts/record-review-pass.sh` before the arbiter sees precedent packs."

Add repeat-review dispatch: "For sampled beads, a second arbiter pass is dispatched with `review_stage: repeat_blind` and `exposure_mode: blind_first`, sharing a `repeat_review_group_id` with the original blind pass. The second pass sees the same evidence but NOT the first pass's verdict. The stage distinguishes it from the original arbiter_pre_synthesis pass; the exposure_mode confirms it was blind."

- [ ] **Step 3: Update arbitration-protocol.md**

Update the arbiter verdict format to include MAP vector output. Add the blind-first → precedent-exposed two-pass flow:
1. Arbiter receives bead evidence (blind)
2. Produces MAP vector + provisional verdict
3. System records blind pass via `record-review-pass.sh`
4. System reveals precedent pack
5. Arbiter may revise (recorded as new pass with `parent_review_pass_id`)

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md skills/sdlc-adversarial/SKILL.md skills/sdlc-adversarial/arbitration-protocol.md
git commit -m "feat: wire MAP scoring and repeat-review into AQS pipeline

Arbiter pre-synthesis produces blind MAP vector before seeing precedents.
Repeat-review sampling dispatches second blind pass for sampled beads.
Orchestrate derives noise summary in Synthesize. Advisory escalations
included in delivery summary."
```

---

### Task 6: Wire into gate, evolve, quality-slos, and agents

**Files:**
- Modify: `skills/sdlc-gate/SKILL.md`
- Modify: `skills/sdlc-evolve/SKILL.md`
- Modify: `references/quality-slos.md`
- Modify: `references/calibration-protocol.md`
- Modify: `agents/process-drift-monitor.md`

- [ ] **Step 1: Update gate SKILL.md**

Add advisory decision-noise checklist (after stress session checklist):
```markdown
### Decision Noise (AQS-engaged tasks, advisory)
- Does `decision-noise-summary.yaml` exist for tasks with AQS-engaged beads?
- Are any soft escalation conditions triggered? (Check escalations section)
- If verdict flips or MAP divergence detected: flag for Conductor attention (advisory, not blocking)
```

- [ ] **Step 2: Update evolve SKILL.md**

Add noise-awareness to evolve: "When dispatching evolution beads, check `review-passes.jsonl` for high repeat_review_noise_index or frequent verdict flips. These are signals that the review process needs calibration — prioritize precedent coherence audits and constitution staleness checks when noise is high."

**Deferred (v2):** Full cue-calibration evolution bead (consume heuristics fields + outcome events, compute cue precision, propose FFT reordering). This requires `noise-events.jsonl` which has no producer in v1.

- [ ] **Step 3: Update quality-slos.md**

Add three noise metrics:
```markdown
| repeat_review_noise_index | Average MAP distance across repeat-review pairs | < 2.0 | Decision consistency |
| natural_frequency_coverage | Share of high-severity claims with frequency backing | >= 0.80 | Calibration quality |
| spot_check_coverage_rate | Repeat-reviewed beads / eligible beads | >= sampling target | Noise measurement completeness |
```

- [ ] **Step 4: Update calibration-protocol.md**

Add: "Calibration beads with known answers can double as noise benchmarks: the distance between the reviewer's MAP vector and the 'correct' MAP vector measures calibration noise on a known-answer task."

- [ ] **Step 5: Update process-drift-monitor.md**

Add noise trend signal: "Read `review-passes.jsonl` for noise_index trend. Rising noise index across last 5 tasks = decision reliability degradation. Declining spot_check_coverage = measurement gap."

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-gate/SKILL.md skills/sdlc-evolve/SKILL.md references/quality-slos.md references/calibration-protocol.md agents/process-drift-monitor.md
git commit -m "feat: wire decision-noise into gate, evolve, SLOs, calibration, drift

Advisory noise checklist in gate. Cue-calibration evolution bead.
Noise SLIs (noise_index, frequency_coverage, spot_check_rate).
Calibration beads as noise benchmarks. Drift-monitor noise trend."
```

---

### Task 7: Update normalize, artifact-templates, and README

**Files:**
- Modify: `skills/sdlc-normalize/SKILL.md`
- Modify: `references/artifact-templates.md`
- Modify: `README.md`

- [ ] **Step 1: Update normalize**

Add `decision-noise-summary.yaml (if exists)` to resume artifact list.

- [ ] **Step 2: Update artifact-templates**

Add to Task Artifacts table:
```
| Decision noise summary | `decision-noise-summary.yaml` | Phase 5 (Synthesize) | If AQS-engaged — advisory |
```

- [ ] **Step 3: Update README**

Add artifacts: decision-noise-summary.yaml, review-passes.jsonl, noise-events.jsonl. Update hook count (increment by 1). Add validate-decision-noise-summary.sh to hook table. Update test count.

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-normalize/SKILL.md references/artifact-templates.md README.md
git commit -m "docs: update normalize, artifact-templates, README for decision-noise

Add decision-noise-summary.yaml to resume list and artifact table.
Add noise artifacts, hook, and metrics to README."
```

---

### Task 8: Final verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: 54/54 PASS.

- [ ] **Step 2: Verify all new files exist**

```bash
ls -la references/decision-noise-rules.yaml references/decision-noise-schema.md scripts/lib/decision-noise-lib.sh scripts/record-review-pass.sh scripts/derive-decision-noise-summary.sh scripts/evaluate-escalations.sh hooks/scripts/validate-decision-noise-summary.sh hooks/tests/fixtures/dn-valid/decision-noise-summary.yaml hooks/tests/fixtures/dn-missing/decision-noise-summary.yaml hooks/tests/fixtures/dn-malformed/decision-noise-summary.yaml
```

Expected: All 10 files exist.

- [ ] **Step 3: Test idempotent append**

```bash
mkdir -p /tmp/test-dn/docs/sdlc/decision-noise
RECORD='{"schema_version":1,"review_pass_id":"rp_test_001","task_id":"test","bead_id":"B01","decision_trace_id":"B01-dt","timestamp":"2026-03-30T00:00:00Z","review_stage":"arbiter_pre_synthesis","reviewer_role":"arbiter","reviewer_model":"opus","exposure_mode":"blind_first","exposure_order":0,"anchor_sources_seen":[],"anchor_verdicts_seen":[],"anchor_map_targets_seen":[],"precedent_pack_id":null,"repeat_review_group_id":null,"arbiter_group_id":"aqs_B01","parent_review_pass_id":null,"supersedes_review_pass_id":null,"map":{"evidence_strength":4,"impact_severity":3,"base_rate_frequency":{"bucket":3,"hits":null,"sample":null,"reference_class_id":null,"reference_class_state":"not_applicable"},"pattern_familiarity":4,"decision_confidence":3,"precedent_match_delta":null},"probability_judgments":[],"heuristics":{"top_cue":"FFT-02-complex","cue_vector":["FFT-02-complex"]},"verdict":{"decision":"accept","severity":"P3","confidence_bucket":3}}'

cd /Users/q/.claude/plugins/sdlc-os
echo "$RECORD" | bash scripts/record-review-pass.sh /tmp/test-dn
echo "$RECORD" | bash scripts/record-review-pass.sh /tmp/test-dn  # duplicate — should skip
wc -l /tmp/test-dn/docs/sdlc/decision-noise/review-passes.jsonl
```

Expected: 1 line (duplicate rejected). Output should show "SKIP: review_pass_id rp_test_001 already exists (idempotent)".

- [ ] **Step 4: Test blind→exposed linkage**

```bash
EXPOSED='{"schema_version":1,"review_pass_id":"rp_test_002","parent_review_pass_id":"rp_test_001","supersedes_review_pass_id":null,"task_id":"test","bead_id":"B01","decision_trace_id":"B01-dt","timestamp":"2026-03-30T00:01:00Z","review_stage":"repeat_exposed","reviewer_role":"arbiter","reviewer_model":"opus","exposure_mode":"precedent_exposed","exposure_order":1,"anchor_sources_seen":["precedent-pack-42"],"anchor_verdicts_seen":[{"decision":"escalate"}],"anchor_map_targets_seen":[{"evidence_strength":5,"impact_severity":5,"pattern_familiarity":5}],"precedent_pack_id":"pp-42","repeat_review_group_id":null,"arbiter_group_id":"aqs_B01","map":{"evidence_strength":5,"impact_severity":4,"base_rate_frequency":{"bucket":3,"hits":null,"sample":null,"reference_class_id":null,"reference_class_state":"not_applicable"},"pattern_familiarity":5,"decision_confidence":4,"precedent_match_delta":2},"probability_judgments":[],"heuristics":{"top_cue":"FFT-02-complex","cue_vector":["FFT-02-complex"]},"verdict":{"decision":"escalate","severity":"P2","confidence_bucket":4}}'

echo "$EXPOSED" | bash scripts/record-review-pass.sh /tmp/test-dn
wc -l /tmp/test-dn/docs/sdlc/decision-noise/review-passes.jsonl
python3 -c "
import json
with open('/tmp/test-dn/docs/sdlc/decision-noise/review-passes.jsonl') as f:
    records = [json.loads(l) for l in f]
exposed = [r for r in records if r['parent_review_pass_id'] == 'rp_test_001']
print(f'Linked passes: {len(exposed)}')
print(f'Exposure order: {exposed[0][\"exposure_order\"]}')
print(f'Anchoring drift delta: {exposed[0][\"map\"][\"precedent_match_delta\"]}')
"
```

Expected: 2 lines total. Linked passes: 1. Exposure order: 1. Anchoring drift delta: 2.

- [ ] **Step 5: Cleanup and spot-check**

```bash
rm -rf /tmp/test-dn
```

Spot-check:
1. `skills/sdlc-orchestrate/SKILL.md` — repeat-review sampling, noise summary derivation, noise artifacts
2. `skills/sdlc-adversarial/SKILL.md` — MAP vector requirement, blind-first protocol
3. `skills/sdlc-adversarial/arbitration-protocol.md` — MAP in verdict format, two-pass flow
4. `skills/sdlc-gate/SKILL.md` — advisory noise checklist
5. `README.md` — updated hook count, noise artifacts
