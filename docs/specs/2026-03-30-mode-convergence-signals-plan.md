# Mode & Convergence Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make loop control information-aware, escalation reasons structured, and execution mode observable — operational at the loop level, non-phase-gating at the task level.

**Architecture:** Externalized rules (SRK thresholds, convergence derivation, escalation enum), shared computation library, per-task summary YAML, system JSONL ledger, convergence-aware loop budgets, evidence-rate AQS stopping.

**Tech Stack:** YAML (rules, summaries), JSONL (system ledger), Bash + Python3 (scripts), Markdown (docs)

**Spec:** `docs/specs/2026-03-30-mode-convergence-signals-design.md`

**Slice order:** Contract → Computation → Artifacts → Integration → Reporting

**Deferred:** Budget-policy experimentation beyond spec minimums, automated decomposition from escalation patterns, phase-transition gating.

---

### Task 1: Define the contract — rules file, schema docs

**Files:**
- Create: `references/mode-convergence-rules.yaml`
- Create: `references/mode-convergence-schema.md`

- [ ] **Step 1: Create the rules file**

Write `references/mode-convergence-rules.yaml`:

```yaml
# Mode & Convergence Rules — externalized thresholds and derivation parameters
schema_version: 1

# Escalation reason categories (structured enum)
escalation_reasons:
  - ambiguity
  - coupling
  - statefulness
  - concurrency
  - reviewer_overload
  - missing_precedent
  - domain_gap
  - tooling_limitation
  - decomposition_error
  - context_exhaustion

# SRK classification thresholds
# Rule-based boundaries are INCLUSIVE (>= and <=)
# Skill-based and knowledge-based use strict inequalities
srk_thresholds:
  turbulence_sum_per_bead:
    skill_max: 1.0        # < 1.0 = skill-based
    knowledge_min: 3.0    # > 3.0 = knowledge-based
    # >= 1.0 AND <= 3.0 = rule-based
  zero_turbulence_rate:
    skill_min: 0.80       # > 0.80 = skill-based
    knowledge_max: 0.50   # < 0.50 = knowledge-based
    # >= 0.50 AND <= 0.80 = rule-based
  review_latency_p95_s:
    skill_max: 60         # < 60 = skill-based
    knowledge_min: 300    # > 300 = knowledge-based
    # >= 60 AND <= 300 = rule-based
  escalation_count:
    skill_max: 0          # == 0 = skill-based
    knowledge_min: 2      # > 2 = knowledge-based
    # >= 1 AND <= 2 = rule-based

# SRK confidence derivation
srk_confidence:
  unanimous: high         # 4 signals agree
  supermajority: medium   # 3 signals agree (3-1)
  split: low              # 2-2 tie (resolved to rule_based)

# Convergence signal parameters
convergence:
  evidence_rate_converging: 0.50   # >= this = new evidence still arriving
  evidence_rate_stable: 0.20      # < this = findings are repetitive
  entropy_stuck_threshold: 1.0    # < this = findings cluster in 1-2 categories
  severity_ordinal:
    P4: 1
    P3: 2
    P2: 3
    P1: 4

# Convergence recommendations
convergence_recommendations:
  converging: continue
  stable: stop_early
  diverging: change_approach
  stuck_within_budget: extend_budget   # if budget < 2x original
  stuck_over_budget: change_approach   # if budget >= 2x original

# Budget extension limit
max_budget_multiplier: 2
```

- [ ] **Step 2: Create schema docs**

Write `references/mode-convergence-schema.md` from the design spec. Include:
- Escalation reason enum (10 categories with descriptions)
- Convergence signal schema (all fields: cycle, new_findings, repeated_findings, evidence_rate, severity_trend, entropy_estimate, convergence_state, recommendation)
- severity_trend derivation (max severity ordinal comparison between cycles, P4=1..P1=4)
- convergence_state derivation (4 states with entropy wired in: stuck requires low entropy + low evidence_rate)
- entropy_estimate computation (Shannon entropy over finding category distribution)
- Execution mode schema (SRK classification + signals + confidence)
- SRK classification rules with explicit boundary semantics
- Confidence derivation (unanimous/supermajority/split)
- Per-task mode-convergence-summary.yaml schema
- System ledger JSONL schema
- Integration points (loop system, AQS, orchestrate)

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/mode-convergence-rules.yaml references/mode-convergence-schema.md
git commit -m "feat: add mode-convergence contract — rules and schema

Externalized SRK thresholds with explicit boundary semantics,
convergence derivation rules (evidence_rate + entropy + severity_trend),
escalation reason enum, confidence mapping, budget extension limits."
```

---

### Task 2: Create shared computation library

**Files:**
- Create: `scripts/lib/mode-convergence-lib.sh`

- [ ] **Step 1: Create the shared library**

Write `scripts/lib/mode-convergence-lib.sh` with helpers:

```bash
#!/bin/bash
# mode-convergence-lib.sh — Shared helpers for mode & convergence signals
set -euo pipefail

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

if skill_max is not None and val < skill_max:
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
    if skill_max is not None and val < skill_max: return 'skill_based'
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
# Usage: compute_convergence_signal new_findings repeated_findings severity_trend entropy_estimate cycle_budget current_cycle <rules_file>
compute_convergence_signal() {
  local new="$1" repeated="$2" sev_trend="$3" entropy="$4" budget="$5" cycle="$6" rules="$7"
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
budget = int(sys.argv[5])
cycle = int(sys.argv[6])

total = new_f + repeated_f
evidence_rate = new_f / total if total > 0 else 0.0

if evidence_rate >= c['evidence_rate_converging'] and sev_trend != 'escalating':
    state = 'converging'
elif evidence_rate < c['evidence_rate_stable'] and sev_trend == 'stable':
    state = 'stable'
elif sev_trend == 'escalating':
    state = 'diverging'
elif evidence_rate < c['evidence_rate_converging'] and entropy < c['entropy_stuck_threshold']:
    state = 'stuck'
else:
    state = 'stuck'

if state == 'converging':
    recommendation = rec['converging']
elif state == 'stable':
    recommendation = rec['stable']
elif state == 'diverging':
    recommendation = rec['diverging']
elif state == 'stuck':
    if cycle < budget * max_mult:
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
" "$new" "$repeated" "$sev_trend" "$entropy" "$budget" "$cycle" "$rules"
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
```

Make executable. Add PyYAML guard at top.

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/lib/mode-convergence-lib.sh
git add scripts/lib/mode-convergence-lib.sh
git commit -m "feat: add mode-convergence shared computation library

SRK classification (4-signal majority vote with boundary semantics),
severity_trend (ordinal comparison), Shannon entropy, convergence
signal (evidence_rate + entropy + severity_trend → state → recommendation)."
```

---

### Task 3: Create standalone classifier scripts

**Files:**
- Create: `scripts/classify-execution-mode.sh`
- Create: `scripts/compute-convergence-signal.sh`

- [ ] **Step 1: Create execution mode classifier**

Write `scripts/classify-execution-mode.sh`. Takes `<task-dir>` and reads `quality-budget.yaml` for the 4 SRK signals. Sources `mode-convergence-lib.sh`. Outputs JSON `{classification, confidence, signals}`. Add PyYAML guard.

- [ ] **Step 2: Create convergence signal computer**

Write `scripts/compute-convergence-signal.sh`. Takes cycle data as arguments (new_findings, repeated_findings, prev_severities_json, curr_severities_json, curr_categories_json, cycle_budget, current_cycle). Sources `mode-convergence-lib.sh`. Computes severity_trend, entropy, then full convergence signal. Outputs JSON. Add PyYAML guard.

- [ ] **Step 3: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/classify-execution-mode.sh scripts/compute-convergence-signal.sh
git add scripts/classify-execution-mode.sh scripts/compute-convergence-signal.sh
git commit -m "feat: add execution mode classifier and convergence signal computer

classify-execution-mode.sh reads quality-budget.yaml for SRK signals.
compute-convergence-signal.sh computes evidence_rate + entropy +
severity_trend → convergence_state → recommendation."
```

---

### Task 4: Create per-task summary derivation and system ledger append

**Files:**
- Create: `scripts/derive-mode-convergence-summary.sh`
- Create: `scripts/append-system-mode-convergence.sh`

- [ ] **Step 1: Create summary derivation script**

Write `scripts/derive-mode-convergence-summary.sh`. Takes `<task-dir>`. Reads quality-budget.yaml (for SRK signals), bead convergence history (from bead files or a collected convergence log), and escalation log. Produces `mode-convergence-summary.yaml` with: execution_mode, convergence_history, escalation_log, summary (total_escalations, reason_distribution, dominant_reason, early_stops, budget_extensions, approach_changes, mode_transitions).

Sources mode-convergence-lib.sh. Add PyYAML guard. Accepts `--status partial|final`.

- [ ] **Step 2: Create system ledger append**

Write `scripts/append-system-mode-convergence.sh`. Takes `<task-dir>` and `<project-dir>`. Reads final mode-convergence-summary.yaml, validates artifact_status is `final`, builds JSONL entry, appends to `docs/sdlc/system-mode-convergence.jsonl`.

Sources mode-convergence-lib.sh. Add PyYAML guard.

- [ ] **Step 3: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/derive-mode-convergence-summary.sh scripts/append-system-mode-convergence.sh
git add scripts/derive-mode-convergence-summary.sh scripts/append-system-mode-convergence.sh
git commit -m "feat: add mode-convergence summary derivation and system ledger append

Per-task summary from quality-budget SRK signals + convergence history
+ escalation log. System JSONL with convergence_yield and reason distribution."
```

---

### Task 5: Create validation hook + tests + fixtures

**Files:**
- Create: `hooks/scripts/validate-mode-convergence-summary.sh`
- Create: `hooks/tests/fixtures/mc-valid/mode-convergence-summary.yaml`
- Create: `hooks/tests/fixtures/mc-missing/mode-convergence-summary.yaml`
- Create: `hooks/tests/fixtures/mc-malformed/mode-convergence-summary.yaml`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create validation hook**

PostToolUse on `mode-convergence-summary.yaml`. Validates YAML parse, required fields (schema_version, task_id, artifact_status), artifact_status enum (partial|final), required sections (execution_mode, summary). Make executable.

- [ ] **Step 2: Create fixtures**

Valid fixture with execution_mode + convergence_history + escalation_log + summary. Missing fixture with only schema_version + task_id. Malformed fixture.

- [ ] **Step 3: Update hooks.json and test-hooks.sh**

Add PostToolUse entry. 4 test cases using temp-file + run_test pattern. Update test count.

- [ ] **Step 4: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: 58/58 PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-mode-convergence-summary.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/mc-valid/mode-convergence-summary.yaml hooks/tests/fixtures/mc-missing/mode-convergence-summary.yaml hooks/tests/fixtures/mc-malformed/mode-convergence-summary.yaml
git commit -m "feat: add mode-convergence summary validation hook with tests

PostToolUse hook validates mode-convergence-summary.yaml structure.
4 test cases with 3 fixtures."
```

---

### Task 6: Wire into loop system and AQS

**Files:**
- Modify: `skills/sdlc-loop/SKILL.md`
- Modify: `skills/sdlc-adversarial/SKILL.md:234-250`

- [ ] **Step 1: Update loop SKILL.md**

Add `escalation_reason` and `convergence_signal` to the correction signal format. Add convergence-aware budget handling:

```markdown
### Convergence-Aware Budget Handling

After each loop iteration, compute the convergence signal via `scripts/compute-convergence-signal.sh`. The recommendation modifies budget behavior:

- `continue` → proceed normally within existing budget
- `stop_early` → skip remaining budget iterations, advance bead (convergence detected — no value in continuing)
- `extend_budget` → add 1 cycle to remaining budget if total does not exceed 2x original budget (per `references/mode-convergence-rules.yaml:max_budget_multiplier`)
- `change_approach` → escalate to next loop level with structured `escalation_reason`

Every escalation MUST include an `escalation_reason` from the enum in `references/mode-convergence-rules.yaml`. The reason is recorded in the bead's escalation log and the task's mode-convergence-summary.yaml.
```

- [ ] **Step 2: Update adversarial convergence**

Replace the 3-indicator heuristic check (around lines 234-250) with convergence_signal computation:

```markdown
### AQS Convergence Assessment

After each AQS cycle, compute convergence signal:
1. Count `new_findings` (not seen in prior cycles) vs `repeated_findings` (restating prior content)
2. Compute `severity_trend` from max finding severity: compare current cycle max vs prior cycle max (ordinal: P4=1, P3=2, P2=3, P1=4)
3. Compute `entropy_estimate` over finding category distribution (Shannon entropy)
4. Run `scripts/compute-convergence-signal.sh` with cycle data

Act on recommendation:
- `stop_early` → skip remaining AQS cycles (findings are repetitive, no new information)
- `continue` → proceed to next cycle within budget
- `diverging` → mandatory next cycle regardless of budget (severity is escalating)
- `stuck` → if within 2x budget, extend; else escalate

The prior 3-indicator check (low diversity, low severity, low volume) is subsumed by this convergence signal.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-loop/SKILL.md skills/sdlc-adversarial/SKILL.md
git commit -m "feat: wire convergence signals into loop system and AQS

Loop corrections gain escalation_reason and convergence_signal.
Budget handler responds to stop_early/extend/change_approach.
AQS convergence replaces 3-indicator heuristic with evidence-rate
+ entropy + severity-trend computation."
```

---

### Task 7: Wire into orchestrate lifecycle

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

- [ ] **Step 1: Add execution mode classification**

In Execute phase, after bead completion handling, add:

```markdown
**Execution mode classification:** After Execute phase completes, run `scripts/classify-execution-mode.sh <task-dir>` to compute the Rasmussen SRK classification from quality-budget.yaml telemetry. Log mode transitions if classification changes during task.
```

- [ ] **Step 2: Add mode-convergence summary to Synthesize**

```markdown
**Mode-convergence summary:** Run `scripts/derive-mode-convergence-summary.sh <task-dir> --status final`. Include escalation reason distribution and convergence yield in delivery summary.
```

- [ ] **Step 3: Add mode-convergence artifacts to inventory**

```markdown
- `mode-convergence-summary.yaml` — Per-task execution mode, convergence history, escalation log (created during Synthesize). Schema: `references/mode-convergence-schema.md`.
- `system-mode-convergence.jsonl` — System-level mode/convergence ledger
```

- [ ] **Step 4: Add system ledger append to Complete**

```markdown
**Mode-convergence Complete:** Run `scripts/append-system-mode-convergence.sh <task-dir> <project-dir>`.
```

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat: wire mode-convergence into orchestrate lifecycle

SRK classification after Execute, summary derivation in Synthesize,
system ledger append on Complete, mode-convergence artifacts in inventory."
```

---

### Task 8: Update reporting surfaces and docs (read-only)

**Files:**
- Modify: `skills/sdlc-gate/SKILL.md`
- Modify: `skills/sdlc-evolve/SKILL.md`
- Modify: `references/quality-slos.md`
- Modify: `agents/process-drift-monitor.md`
- Modify: `skills/sdlc-normalize/SKILL.md`
- Modify: `references/artifact-templates.md`
- Modify: `README.md`

- [ ] **Step 1: Update gate — advisory checklist**

```markdown
### Mode & Convergence (advisory)
- Is execution mode classified? If `knowledge_based` with `confidence: high`, flag for Conductor attention.
- Does the escalation log show a dominant reason (3+ occurrences)? Flag: "Systematic issue — consider re-decomposition."
- Is convergence_yield low (< 0.10) across recent tasks? Flag: "Loops rarely stop early."
```

- [ ] **Step 2: Update evolve — escalation-reason awareness (read-only)**

Add: "When dispatching evolution beads, check `system-mode-convergence.jsonl` for dominant escalation reasons across tasks. Clustering of the same reason (e.g., `coupling` in 5+ tasks) signals that decomposition heuristics need improvement — prioritize decomposition review evolution beads."

**Deferred (v2):** Automated decomposition proposal based on escalation patterns.

- [ ] **Step 3: Update quality-slos**

```markdown
| convergence_yield | Early stops / total loop iterations | >= 0.20 | Loop efficiency — system knows when to stop |
| dominant_escalation_reason | Most frequent escalation reason | Monitor (no SLO) | Decomposition quality signal |
```

- [ ] **Step 4: Update process-drift-monitor**

Add: "Mode-transition detection from `system-mode-convergence.jsonl`: if tasks that start as `skill_based` frequently transition to `knowledge_based` during execution, decomposition may be underestimating complexity. Escalation-reason clustering: if the same reason dominates 5+ consecutive tasks, flag as systematic issue."

- [ ] **Step 5: Update normalize, artifact-templates, README**

- normalize: Add `mode-convergence-summary.yaml (if exists)` to resume list
- artifact-templates: Add to Task Artifacts table
- README: Add mode-convergence artifacts, update hook count (increment by 1), add hook to table, update test count to 58

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-gate/SKILL.md skills/sdlc-evolve/SKILL.md references/quality-slos.md agents/process-drift-monitor.md skills/sdlc-normalize/SKILL.md references/artifact-templates.md README.md
git commit -m "docs: wire mode-convergence into reporting surfaces

Advisory gate checklist, escalation-reason awareness in evolve (read-only),
convergence_yield SLI, drift-monitor mode-transition detection,
normalize/templates/README updates."
```

---

### Task 9: Final verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: 58/58 PASS.

- [ ] **Step 2: Verify all new files exist**

```bash
ls -la references/mode-convergence-rules.yaml references/mode-convergence-schema.md scripts/lib/mode-convergence-lib.sh scripts/classify-execution-mode.sh scripts/compute-convergence-signal.sh scripts/derive-mode-convergence-summary.sh scripts/append-system-mode-convergence.sh hooks/scripts/validate-mode-convergence-summary.sh hooks/tests/fixtures/mc-valid/mode-convergence-summary.yaml hooks/tests/fixtures/mc-missing/mode-convergence-summary.yaml hooks/tests/fixtures/mc-malformed/mode-convergence-summary.yaml
```

Expected: All 11 files exist.

- [ ] **Step 3: Test SRK classification**

```bash
cd /Users/q/.claude/plugins/sdlc-os
source scripts/lib/mode-convergence-lib.sh
# Skill-based: low turbulence, high ZTR, fast latency, zero escalations
RESULT=$(classify_execution_mode 0.3 0.90 25 0 references/mode-convergence-rules.yaml)
echo "Skill test: $RESULT"
# Expected: {"classification": "skill_based", "confidence": "high"}

# Knowledge-based: high turbulence, low ZTR, slow latency, many escalations
RESULT=$(classify_execution_mode 4.5 0.30 500 5 references/mode-convergence-rules.yaml)
echo "Knowledge test: $RESULT"
# Expected: {"classification": "knowledge_based", "confidence": "high"}

# Mixed: some signals skill, some knowledge → medium confidence
RESULT=$(classify_execution_mode 0.5 0.60 200 1 references/mode-convergence-rules.yaml)
echo "Mixed test: $RESULT"
# Expected: {"classification": "rule_based", "confidence": "..."}
```

- [ ] **Step 4: Test convergence signal**

```bash
# Converging: high evidence rate, not escalating
RESULT=$(compute_convergence_signal 5 1 stable 2.5 2 1 references/mode-convergence-rules.yaml)
echo "Converging: $RESULT"
# Expected: convergence_state: converging, recommendation: continue

# Stable: low evidence rate, stable severity
RESULT=$(compute_convergence_signal 1 8 stable 0.8 2 2 references/mode-convergence-rules.yaml)
echo "Stable: $RESULT"
# Expected: convergence_state: stable, recommendation: stop_early

# Diverging: escalating severity
RESULT=$(compute_convergence_signal 3 2 escalating 1.5 2 1 references/mode-convergence-rules.yaml)
echo "Diverging: $RESULT"
# Expected: convergence_state: diverging, recommendation: change_approach
```

- [ ] **Step 5: Spot-check integration points**

1. `skills/sdlc-loop/SKILL.md` — escalation_reason + convergence_signal in correction format, convergence-aware budget handling
2. `skills/sdlc-adversarial/SKILL.md` — evidence-rate convergence replaces 3-indicator heuristic
3. `skills/sdlc-orchestrate/SKILL.md` — SRK classification, summary derivation, system ledger append
4. `skills/sdlc-gate/SKILL.md` — advisory mode/convergence checklist
5. `README.md` — updated hook count, mode-convergence artifacts, test count 58

Report all findings with evidence.
