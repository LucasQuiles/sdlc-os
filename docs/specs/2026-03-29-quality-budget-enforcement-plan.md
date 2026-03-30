# Quality Budget Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Quality Budget a machine-readable, derivation-first, schema-validated artifact that gates SDLC phase transitions and feeds longitudinal analysis.

**Architecture:** Two YAML/JSONL artifacts (task budget + system ledger), externalized threshold rules, shared shell library for derivation, PostToolUse validation hook, and updates to 16 existing files to replace the old free-text quality-budget.md contract.

**Tech Stack:** YAML (schemas), JSONL (system ledger), Bash (derivation scripts, hooks, tests), Markdown (documentation)

**Spec:** `docs/specs/2026-03-29-quality-budget-enforcement-design.md`

---

### Task 1: Add bead timestamp prerequisites to artifact-templates.md

**Files:**
- Modify: `references/artifact-templates.md:99-122` (bead template)

The derivation engine needs structured timestamps to compute review latency and actual duration. These fields must exist in the bead template before anything else.

- [ ] **Step 1: Add timestamp fields to the bead template**

In `references/artifact-templates.md`, find the bead template block (around line 99-122). After the line:

```
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
```

Insert three new fields:

```
**Dispatched at:** ""
**Review started at:** ""
**Completed at:** ""
```

All timestamps are UTC ISO 8601 format (e.g., `2026-03-29T14:22:00Z`). Populated by the Conductor at each lifecycle transition.

- [ ] **Step 2: Add quality-budget.yaml to the task artifact contract**

In the same file, find the state.md template section (around lines 6-37). After the closing `---` of the state template, add a note:

```markdown
### Task Artifacts

Each task directory contains these machine-readable artifacts:

| Artifact | File | Created | Required |
|----------|------|---------|----------|
| Task state | `state.md` | Phase 1 (Frame) | Yes |
| Quality budget | `quality-budget.yaml` | Phase 4 (Execute) | Yes — gates Synthesize and Complete |
| Standards profile | `standards-profile.md` | Phase 2 (Scout) | If standards apply |
| Observability profile | `observability-profile.md` | Phase 2 (Scout) | If observability applies |
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/artifact-templates.md
git commit -m "feat: add bead timestamps and quality-budget.yaml to artifact contract

Adds dispatched_at, review_started_at, completed_at to bead template.
Adds quality-budget.yaml to task artifact contract as required artifact."
```

---

### Task 2: Create threshold rules file

**Files:**
- Create: `references/quality-budget-rules.yaml`

- [ ] **Step 1: Create the rules file**

Write `references/quality-budget-rules.yaml`:

```yaml
# Quality Budget Rules — externalized thresholds for budget_state derivation
# Recalibrate here without touching historical artifacts.
schema_version: 1

# complexity_weight = (clear*0 + complicated*0.5 + complex*1.0 + chaotic*1.5) / total_beads
complexity_thresholds:
  - max_weight: 0.2    # mostly clear
    healthy_floor: 0.90
    depleted_floor: 0.60
  - max_weight: 0.5    # mixed
    healthy_floor: 0.75
    depleted_floor: 0.50
  - max_weight: 0.8    # mostly complex
    healthy_floor: 0.60
    depleted_floor: 0.35
  - max_weight: 999    # extreme
    healthy_floor: 0.50
    depleted_floor: 0.25

# Hard-stop invariants: budget_state CANNOT be healthy if ANY are true
# Evaluated against sli_readings and beads fields in quality-budget.yaml
hard_stops:
  - field: sli_readings.lint_clean
    operator: "=="
    value: false
  - field: sli_readings.types_clean
    operator: "=="
    value: false
  - field: sli_readings.critical_findings
    operator: ">"
    value: 0
  - field: beads.stuck
    operator: ">"
    value: 0
  - compound:
      - field: beads.blocked
        operator: ">"
        value: 0
      - field: beads.wip_age_max_s
        operator: ">"
        value: 3600

# v1 gating metrics (budget_state depends on these)
gating_metrics:
  - zero_turbulence_rate
  - escapes.known_at_close
  - hard_stops
  - turbulence_sum_per_bead

# v1 observed-only metrics (recorded but not gated)
observed_metrics:
  - queue_depth_peak
  - buffer_hits
  - wip_age_max_s
  - review_latency_avg_s
  - review_latency_p95_s
  - review_pass_rate

# System budget rolling window
system_rolling_window:
  tasks: 10
  max_days: 30

# System budget_state thresholds
system_thresholds:
  healthy:
    min_zero_turbulence_rate: 0.70
    max_escapes_last_3: 0
  depleted:
    max_zero_turbulence_rate: 0.50
    max_escapes_last_3: 1
    max_high_turbulence_tasks: 2  # tasks with turbulence_sum > 6 * beads
```

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/quality-budget-rules.yaml
git commit -m "feat: add quality budget threshold rules file

Externalized thresholds, hard-stops, gating vs observed metrics,
and system rolling window config. Recalibrable without touching
historical artifacts."
```

---

### Task 3: Create quality budget schema documentation

**Files:**
- Create: `references/quality-budget-schema.md`

- [ ] **Step 1: Create the schema doc**

Write `references/quality-budget-schema.md` with the full schema from the design spec Section 3 (Final). Include:
- Task budget YAML schema with all fields, types, and comments
- Field derivation sources table (which field comes from which bead/state data)
- Metric denominator definitions (zero_turbulence_rate, review_pass_rate eligibility)
- budget_state derivation algorithm (complexity_weight → threshold lookup → hard-stops → state)
- System budget JSONL schema
- System budget events JSONL schema
- Phase gate requirements (ready for Synthesize, final for Complete)

The content is fully specified in `docs/specs/2026-03-29-quality-budget-enforcement-design.md` under the "Schema" section. Reproduce it here as the canonical reference, not a copy — this file IS the schema definition.

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/quality-budget-schema.md
git commit -m "docs: add quality budget schema reference

Canonical schema definition for task budget (YAML), system budget
(JSONL), events ledger (JSONL), metric denominators, and derivation
algorithm."
```

---

### Task 4: Create shared quality budget library

**Files:**
- Create: `scripts/lib/quality-budget-lib.sh`

- [ ] **Step 1: Create the shared library**

Write `scripts/lib/quality-budget-lib.sh`:

```bash
#!/bin/bash
# quality-budget-lib.sh — Shared helpers for quality budget derivation
# Sourced by derive-quality-budget.sh and append-system-budget.sh

set -euo pipefail

# Parse YAML frontmatter from a bead file, extract a field value
# Usage: bead_field "beads/B01.md" "Turbulence"
bead_field() {
  local file="$1" field="$2"
  grep "^\*\*${field}:\*\*" "$file" | sed "s/\*\*${field}:\*\* *//" | sed 's/^"\(.*\)"$/\1/'
}

# Parse turbulence from bead format: {L0: N, L1: N, L2: N, L2.5: N, L2.75: N}
# Returns space-separated: L0 L1 L2 L2_5 L2_75
parse_turbulence() {
  local raw="$1"
  echo "$raw" | sed 's/[{}]//g' | sed 's/L0: *//; s/L1: *//; s/L2: *//; s/L2\.5: *//; s/L2\.75: *//' | tr ',' ' '
}

# Count beads by status from state.md bead table
# Usage: count_beads_by_status "state.md" "completed"
count_beads_by_status() {
  local state_file="$1" status="$2"
  grep -c "| *${status} *|" "$state_file" 2>/dev/null || echo 0
}

# Compute complexity_weight from cynefin_mix
# Usage: complexity_weight clear complicated complex chaotic
complexity_weight() {
  local clear="${1:-0}" complicated="${2:-0}" complex="${3:-0}" chaotic="${4:-0}"
  local total=$((clear + complicated + complex + chaotic))
  if [ "$total" -eq 0 ]; then echo "0.0"; return; fi
  # weight = (clear*0 + complicated*0.5 + complex*1.0 + chaotic*1.5) / total
  echo "scale=2; ($complicated * 0.5 + $complex * 1.0 + $chaotic * 1.5) / $total" | bc
}

# Lookup threshold from rules file given complexity_weight
# Usage: lookup_threshold "rules.yaml" "0.42" "healthy_floor"
lookup_threshold() {
  local rules_file="$1" weight="$2" field="$3"
  # Parse YAML thresholds (simple grep-based for shell compatibility)
  local prev_max="0" result=""
  while IFS= read -r line; do
    if echo "$line" | grep -q "max_weight:"; then
      local max_w
      max_w=$(echo "$line" | sed 's/.*max_weight: *//')
      if [ "$(echo "$weight <= $max_w" | bc)" -eq 1 ] && [ -z "$result" ]; then
        result=$(grep -A2 "max_weight: *${max_w}" "$rules_file" | grep "${field}:" | sed "s/.*${field}: *//")
      fi
    fi
  done < <(grep -A3 "max_weight:" "$rules_file")
  echo "${result:-0.50}"
}

# Compute budget_state from metrics + rules
# Usage: compute_budget_state zero_turb_rate escapes_at_close turb_sum completed healthy_floor depleted_floor
compute_budget_state() {
  local ztr="$1" escapes="$2" turb_sum="$3" completed="$4" healthy_floor="$5" depleted_floor="$6"

  # Depleted conditions
  if [ "$(echo "$ztr < $depleted_floor" | bc)" -eq 1 ]; then echo "depleted"; return; fi
  if [ "$escapes" -gt 1 ]; then echo "depleted"; return; fi
  if [ "$completed" -gt 0 ] && [ "$(echo "$turb_sum > 6 * $completed" | bc)" -eq 1 ]; then echo "depleted"; return; fi

  # Healthy conditions
  if [ "$(echo "$ztr >= $healthy_floor" | bc)" -eq 1 ] && [ "$escapes" -eq 0 ]; then echo "healthy"; return; fi

  # Default
  echo "warning"
}

# Check hard-stop invariants. Returns "true" if any hard-stop is triggered.
# Usage: check_hard_stops lint_clean types_clean critical_findings stuck blocked wip_age_max_s
check_hard_stops() {
  local lint="$1" types="$2" critical="$3" stuck="$4" blocked="$5" wip_age="$6"
  if [ "$lint" = "false" ]; then echo "true"; return; fi
  if [ "$types" = "false" ]; then echo "true"; return; fi
  if [ "$critical" -gt 0 ] 2>/dev/null; then echo "true"; return; fi
  if [ "$stuck" -gt 0 ] 2>/dev/null; then echo "true"; return; fi
  if [ "$blocked" -gt 0 ] 2>/dev/null && [ "$wip_age" -gt 3600 ] 2>/dev/null; then echo "true"; return; fi
  echo "false"
}

# Format current UTC timestamp as ISO 8601
now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/lib/quality-budget-lib.sh
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/lib/quality-budget-lib.sh
git commit -m "feat: add shared quality budget library

Helpers for bead field parsing, turbulence extraction, complexity
weight computation, threshold lookup, budget_state derivation, and
hard-stop invariant checks."
```

---

### Task 5: Create derivation script

**Files:**
- Create: `scripts/derive-quality-budget.sh`

- [ ] **Step 1: Create the derivation script**

Write `scripts/derive-quality-budget.sh`. This script:
1. Reads bead files from `docs/sdlc/active/{task-id}/beads/B*.md`
2. Reads `state.md` for bead counts and status
3. Aggregates turbulence, computes metrics, looks up thresholds
4. Produces/updates `quality-budget.yaml`

```bash
#!/bin/bash
# derive-quality-budget.sh — Derive quality-budget.yaml from bead traces
# Usage: derive-quality-budget.sh <task-dir> [--status partial|ready|final]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/quality-budget-lib.sh"

TASK_DIR="${1:?Usage: derive-quality-budget.sh <task-dir> [--status partial|ready|final]}"
STATUS="${3:-partial}"
RULES_FILE="$SCRIPT_DIR/../references/quality-budget-rules.yaml"
OUTPUT="$TASK_DIR/quality-budget.yaml"
STATE_FILE="$TASK_DIR/state.md"
BEADS_DIR="$TASK_DIR/beads"

[ -d "$TASK_DIR" ] || { echo "ERROR: Task directory not found: $TASK_DIR" >&2; exit 1; }
[ -f "$STATE_FILE" ] || { echo "ERROR: state.md not found in $TASK_DIR" >&2; exit 1; }

TASK_ID=$(basename "$TASK_DIR")

# --- Count beads by status ---
TOTAL=0 COMPLETED=0 WIP=0 STUCK=0 BLOCKED=0
CLEAR=0 COMPLICATED=0 COMPLEX=0 CHAOTIC=0
L0=0 L1=0 L2=0 L2_5=0 L2_75=0
ZERO_TURB=0
LATENCIES=""
WIP_AGES=""

for bead in "$BEADS_DIR"/B*.md; do
  [ -f "$bead" ] || continue
  TOTAL=$((TOTAL + 1))

  status=$(bead_field "$bead" "Status")
  case "$status" in
    merged|hardened|reliability-proven|verified|proven) COMPLETED=$((COMPLETED + 1)) ;;
    running|submitted) WIP=$((WIP + 1)) ;;
    stuck) STUCK=$((STUCK + 1)) ;;
    blocked) BLOCKED=$((BLOCKED + 1)) ;;
  esac

  cynefin=$(bead_field "$bead" "Cynefin domain")
  case "$cynefin" in
    clear) CLEAR=$((CLEAR + 1)) ;;
    complicated) COMPLICATED=$((COMPLICATED + 1)) ;;
    complex) COMPLEX=$((COMPLEX + 1)) ;;
    chaotic) CHAOTIC=$((CHAOTIC + 1)) ;;
  esac

  turb_raw=$(bead_field "$bead" "Turbulence")
  if [ -n "$turb_raw" ]; then
    read -r tL0 tL1 tL2 tL2_5 tL2_75 <<< "$(parse_turbulence "$turb_raw")"
    L0=$((L0 + ${tL0:-0}))
    L1=$((L1 + ${tL1:-0}))
    L2=$((L2 + ${tL2:-0}))
    L2_5=$((L2_5 + ${tL2_5:-0}))
    L2_75=$((L2_75 + ${tL2_75:-0}))
    bead_turb=$(( ${tL0:-0} + ${tL1:-0} + ${tL2:-0} + ${tL2_5:-0} + ${tL2_75:-0} ))
    if [ "$bead_turb" -eq 0 ] && echo "$status" | grep -qE "merged|hardened|reliability-proven|verified|proven"; then
      ZERO_TURB=$((ZERO_TURB + 1))
    fi
  fi
done

TURB_SUM=$((L0 + L1 + L2 + L2_5 + L2_75))

# Find max turbulence bead
MAX_TURB=0 MAX_BEAD="null"
for bead in "$BEADS_DIR"/B*.md; do
  [ -f "$bead" ] || continue
  turb_raw=$(bead_field "$bead" "Turbulence")
  if [ -n "$turb_raw" ]; then
    read -r tL0 tL1 tL2 tL2_5 tL2_75 <<< "$(parse_turbulence "$turb_raw")"
    bt=$(( ${tL0:-0} + ${tL1:-0} + ${tL2:-0} + ${tL2_5:-0} + ${tL2_75:-0} ))
    if [ "$bt" -gt "$MAX_TURB" ]; then
      MAX_TURB=$bt
      MAX_BEAD=$(basename "$bead" .md)
    fi
  fi
done

# --- Compute metrics ---
if [ "$COMPLETED" -gt 0 ]; then
  ZTR=$(echo "scale=2; $ZERO_TURB / $COMPLETED" | bc)
  TSPR=$(echo "scale=2; $TURB_SUM / $COMPLETED" | bc)
else
  ZTR="0.0"
  TSPR="null"
fi

CW=$(complexity_weight "$CLEAR" "$COMPLICATED" "$COMPLEX" "$CHAOTIC")

# --- Derive budget_state (only if ready or final) ---
if [ "$STATUS" != "partial" ]; then
  HF=$(lookup_threshold "$RULES_FILE" "$CW" "healthy_floor")
  DF=$(lookup_threshold "$RULES_FILE" "$CW" "depleted_floor")
  BUDGET_STATE=$(compute_budget_state "$ZTR" "0" "$TURB_SUM" "$COMPLETED" "$HF" "$DF")
else
  BUDGET_STATE="null"
fi

NOW=$(now_utc)

# --- Write YAML ---
cat > "$OUTPUT" <<YAML
schema_version: 1
task_id: "$TASK_ID"
artifact_status: $STATUS
budget_state: $BUDGET_STATE
derived_at: "$NOW"
last_updated: "$NOW"

cynefin_mix:
  clear: $CLEAR
  complicated: $COMPLICATED
  complex: $COMPLEX
  chaotic: $CHAOTIC
complexity_weight: $CW

beads:
  total: $TOTAL
  completed: $COMPLETED
  wip: $WIP
  stuck: $STUCK
  blocked: $BLOCKED
  wip_age_max_s: 0

corrections:
  L0: $L0
  L1: $L1
  L2: $L2
  L2_5: $L2_5
  L2_75: $L2_75

turbulence_sum: $TURB_SUM
turbulence_max_bead: $MAX_BEAD

metrics:
  zero_turbulence_rate: $ZTR
  turbulence_sum_per_bead: $TSPR
  review_pass_rate: 0.0
  queue_depth_peak: 0
  buffer_hits: 0
  review_latency_avg_s: 0
  review_latency_p95_s: 0

timing:
  estimate_s: null
  actual_s: null

sli_readings:
  lint_clean: null
  types_clean: null
  test_coverage_delta: null
  complexity_delta: null
  critical_findings: null

escapes:
  known_at_close: 0

overrides: []
notes: ""
YAML

echo "Derived quality-budget.yaml for $TASK_ID (status: $STATUS, budget: $BUDGET_STATE)"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/derive-quality-budget.sh
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/derive-quality-budget.sh
git commit -m "feat: add quality budget derivation script

Reads bead traces and state.md, aggregates turbulence, computes
zero_turbulence_rate, looks up complexity-aware thresholds, and
produces quality-budget.yaml."
```

---

### Task 6: Create system budget append script

**Files:**
- Create: `scripts/append-system-budget.sh`

- [ ] **Step 1: Create the append script**

Write `scripts/append-system-budget.sh`:

```bash
#!/bin/bash
# append-system-budget.sh — Append completed task to system-budget.jsonl
# Usage: append-system-budget.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/quality-budget-lib.sh"

TASK_DIR="${1:?Usage: append-system-budget.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-budget.sh <task-dir> <project-dir>}"
BUDGET_FILE="$TASK_DIR/quality-budget.yaml"
LEDGER="$PROJECT_DIR/docs/sdlc/system-budget.jsonl"

[ -f "$BUDGET_FILE" ] || { echo "ERROR: quality-budget.yaml not found" >&2; exit 1; }

# Simple YAML field extractor (works for flat fields)
yf() { grep "^${1}:" "$BUDGET_FILE" | sed "s/^${1}: *//" | sed 's/"//g'; }
yf_nested() { grep "^  ${1}:" "$BUDGET_FILE" | sed "s/^  ${1}: *//" | sed 's/"//g'; }

TASK_ID=$(yf "task_id")
STATUS=$(yf "artifact_status")

if [ "$STATUS" != "final" ]; then
  echo "ERROR: artifact_status is '$STATUS', must be 'final' to append to system ledger" >&2
  exit 1
fi

# Build JSONL entry
ENTRY=$(cat <<JSON
{"task_id":"$TASK_ID","date":"$(yf "derived_at")","beads":$(yf_nested "total"),"cynefin_mix":{"clear":$(yf_nested "clear"),"complicated":$(yf_nested "complicated"),"complex":$(yf_nested "complex"),"chaotic":$(yf_nested "chaotic")},"complexity_weight":$(yf "complexity_weight"),"turbulence_sum":$(yf "turbulence_sum"),"zero_turbulence_rate":$(yf_nested "zero_turbulence_rate"),"review_pass_rate":$(yf_nested "review_pass_rate"),"L0":$(yf_nested "L0"),"L1":$(yf_nested "L1"),"L2":$(yf_nested "L2"),"L2_5":$(yf_nested "L2_5"),"L2_75":$(yf_nested "L2_75"),"escapes_at_close":$(yf_nested "known_at_close"),"estimate_s":$(yf_nested "estimate_s"),"actual_s":$(yf_nested "actual_s"),"latency_avg_s":$(yf_nested "review_latency_avg_s"),"latency_p95_s":$(yf_nested "review_latency_p95_s"),"queue_peak":$(yf_nested "queue_depth_peak"),"buffer_hits":$(yf_nested "buffer_hits"),"budget_state":"$(yf "budget_state")"}
JSON
)

mkdir -p "$(dirname "$LEDGER")"
echo "$ENTRY" >> "$LEDGER"
echo "Appended $TASK_ID to system-budget.jsonl"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/append-system-budget.sh
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add scripts/append-system-budget.sh
git commit -m "feat: add system budget append script

Reads final quality-budget.yaml and appends one JSONL entry to
docs/sdlc/system-budget.jsonl for longitudinal analysis."
```

---

### Task 7: Create validation hook + tests + fixtures

**Files:**
- Create: `hooks/scripts/validate-quality-budget.sh`
- Create: `hooks/tests/fixtures/quality-budget-valid.yaml`
- Create: `hooks/tests/fixtures/quality-budget-missing-fields.yaml`
- Create: `hooks/tests/fixtures/quality-budget-malformed.yaml`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create the validation hook script**

Write `hooks/scripts/validate-quality-budget.sh`:

```bash
#!/bin/bash
# validate-quality-budget.sh — PostToolUse hook: validates quality-budget.yaml on Write/Edit
set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only trigger on quality-budget.yaml writes
if [[ "$file_path" != *"quality-budget.yaml" ]]; then
  exit 0
fi

if [[ ! -f "$file_path" ]]; then
  echo "quality-budget.yaml written but file not found at $file_path" >&2
  exit 2
fi

# Validate: must contain schema_version
if ! grep -q "^schema_version:" "$file_path"; then
  echo '{"decision":"deny","reason":"quality-budget.yaml missing schema_version field"}' >&2
  exit 2
fi

# Validate: must contain task_id
if ! grep -q "^task_id:" "$file_path"; then
  echo '{"decision":"deny","reason":"quality-budget.yaml missing task_id field"}' >&2
  exit 2
fi

# Validate: must contain artifact_status
if ! grep -q "^artifact_status:" "$file_path"; then
  echo '{"decision":"deny","reason":"quality-budget.yaml missing artifact_status field"}' >&2
  exit 2
fi

# Validate: artifact_status must be valid
STATUS=$(grep "^artifact_status:" "$file_path" | sed 's/artifact_status: *//')
case "$STATUS" in
  partial|ready|final) ;;
  *) echo '{"decision":"deny","reason":"artifact_status must be partial, ready, or final"}' >&2; exit 2 ;;
esac

# Validate: required sections exist
for section in "cynefin_mix:" "beads:" "corrections:" "metrics:" "timing:" "escapes:"; do
  if ! grep -q "^${section}" "$file_path"; then
    echo "{\"decision\":\"deny\",\"reason\":\"quality-budget.yaml missing required section: $section\"}" >&2
    exit 2
  fi
done

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/validate-quality-budget.sh
```

- [ ] **Step 3: Create test fixtures**

Write `hooks/tests/fixtures/quality-budget-valid.yaml`:
```yaml
schema_version: 1
task_id: "test-task-001"
artifact_status: ready
budget_state: healthy
derived_at: "2026-03-29T14:00:00Z"
last_updated: "2026-03-29T14:00:00Z"
cynefin_mix:
  clear: 2
  complicated: 1
  complex: 0
  chaotic: 0
complexity_weight: 0.17
beads:
  total: 3
  completed: 3
  wip: 0
  stuck: 0
  blocked: 0
  wip_age_max_s: 0
corrections:
  L0: 1
  L1: 0
  L2: 0
  L2_5: 0
  L2_75: 0
turbulence_sum: 1
turbulence_max_bead: B01
metrics:
  zero_turbulence_rate: 0.67
  turbulence_sum_per_bead: 0.33
  review_pass_rate: 1.0
  queue_depth_peak: 2
  buffer_hits: 0
  review_latency_avg_s: 30
  review_latency_p95_s: 45
timing:
  estimate_s: null
  actual_s: null
sli_readings:
  lint_clean: null
  types_clean: null
  test_coverage_delta: null
  complexity_delta: null
  critical_findings: null
escapes:
  known_at_close: 0
overrides: []
notes: ""
```

Write `hooks/tests/fixtures/quality-budget-missing-fields.yaml`:
```yaml
schema_version: 1
task_id: "test-task-002"
# Missing: artifact_status, cynefin_mix, beads, corrections, metrics, timing, escapes
budget_state: healthy
```

Write `hooks/tests/fixtures/quality-budget-malformed.yaml`:
```
this is not valid yaml: [
  unclosed bracket
schema_version 1
```

- [ ] **Step 4: Add hook to hooks.json**

In `hooks/hooks.json`, find the `"PostToolUse"` array. Add a new entry at the end of the PostToolUse list:

```json
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-quality-budget.sh",
          "timeout": 10
        }
      ]
    }
```

- [ ] **Step 5: Add test cases to test-hooks.sh**

In `hooks/tests/test-hooks.sh`, before the final summary line, add:

```bash
# --- Quality Budget Validation ---
echo '{"tool_name":"Write","tool_input":{"file_path":"'"$(pwd)/hooks/tests/fixtures/quality-budget-valid.yaml"'"}}' | bash hooks/scripts/validate-quality-budget.sh && pass "quality-budget: valid file passes" || fail "quality-budget: valid file passes"

echo '{"tool_name":"Write","tool_input":{"file_path":"'"$(pwd)/hooks/tests/fixtures/quality-budget-missing-fields.yaml"'"}}' | bash hooks/scripts/validate-quality-budget.sh 2>/dev/null && fail "quality-budget: missing fields rejected" || pass "quality-budget: missing fields rejected"

echo '{"tool_name":"Write","tool_input":{"file_path":"'"$(pwd)/hooks/tests/fixtures/quality-budget-malformed.yaml"'"}}' | bash hooks/scripts/validate-quality-budget.sh 2>/dev/null && fail "quality-budget: malformed YAML rejected" || pass "quality-budget: malformed YAML rejected"

echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/not-quality-budget.txt"}}' | bash hooks/scripts/validate-quality-budget.sh && pass "quality-budget: non-budget file ignored" || fail "quality-budget: non-budget file ignored"
```

Update the expected test count in the summary line (currently 32, add 4 → 36).

- [ ] **Step 6: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: 36/36 PASS (or whatever the new total is).

- [ ] **Step 7: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-quality-budget.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/quality-budget-valid.yaml hooks/tests/fixtures/quality-budget-missing-fields.yaml hooks/tests/fixtures/quality-budget-malformed.yaml
git commit -m "feat: add quality budget validation hook with tests

PostToolUse hook validates quality-budget.yaml structure on Write/Edit.
Checks schema_version, task_id, artifact_status, and required sections.
4 test cases with 3 fixtures."
```

---

### Task 8: Update orchestrate SKILL.md — references, gates, derivation trigger

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md:135, :230, :396`

- [ ] **Step 1: Update line 135 — resume protocol**

Replace:
```
quality-budget.md (if exists)
```
With:
```
quality-budget.yaml (if exists)
```

- [ ] **Step 2: Update line 396 — artifact inventory**

Replace:
```
- `quality-budget.md` — SLI/SLO tracking (created during Synthesize, read during subsequent tasks)
```
With:
```
- `quality-budget.yaml` — Machine-readable quality budget (created during Execute as `partial`, promoted to `ready` before Synthesize, `final` after Synthesize). Schema: `references/quality-budget-schema.md`. Rules: `references/quality-budget-rules.yaml`.
- `system-budget.jsonl` — Append-only system-level ledger (one entry per completed task, written during Complete)
- `system-budget-events.jsonl` — Late-arriving corrections to system ledger (escape confirmations from LOSA)
```

- [ ] **Step 3: Add Synthesize gate**

Find the Synthesize phase description (search for "Synthesize" or "Phase 5"). Add before the existing Synthesize instructions:

```markdown
**Synthesize gate:** Before entering Synthesize, run `scripts/derive-quality-budget.sh <task-dir> --status ready`. Verify: quality-budget.yaml exists, artifact_status is `ready`, all derived fields non-null (except estimate_s and sli_readings). If gate fails, report missing fields and re-derive.
```

- [ ] **Step 4: Add Complete gate**

Find the Complete/handoff phase description. Add:

```markdown
**Complete gate:** Before marking task complete, verify quality-budget.yaml has artifact_status `final`, sli_readings fully populated, budget_state computed with hard-stops applied. Run `scripts/append-system-budget.sh <task-dir> <project-dir>` to append to the system ledger.
```

- [ ] **Step 5: Add derivation trigger**

In the Execute phase description (around the bead completion handling), add:

```markdown
**Budget derivation:** After each bead status change (completion, stuck, blocked), run `scripts/derive-quality-budget.sh <task-dir> --status partial` to update the task's quality-budget.yaml with current metrics.
```

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat: wire quality budget into orchestrate lifecycle

Replace quality-budget.md with quality-budget.yaml. Add Synthesize
gate (artifact_status: ready), Complete gate (artifact_status: final),
derivation trigger after each bead status change, and system ledger
append on Complete."
```

---

### Task 9: Update gate SKILL.md

**Files:**
- Modify: `skills/sdlc-gate/SKILL.md`

- [ ] **Step 1: Add quality budget awareness to gate checklist**

After the existing "Readiness Checklist" section, add:

```markdown
### Quality Budget
- Does `quality-budget.yaml` exist in the task directory?
- Is `artifact_status` appropriate for the current transition? (`ready` for Synthesize, `final` for Complete)
- Are any hard-stop invariants triggered? (Check `references/quality-budget-rules.yaml`)
- Is `budget_state` computed and non-null?
- If `budget_state` is `depleted`: flag for user attention before proceeding.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-gate/SKILL.md
git commit -m "feat: add quality budget checks to /gate health check

Gate now checks quality-budget.yaml existence, artifact_status,
hard-stop invariants, and budget_state."
```

---

### Task 10: Update reference files — quality-slos.md, reliability-ledger.md, fft-decision-trees.md

**Files:**
- Modify: `references/quality-slos.md:57-67`
- Modify: `references/reliability-ledger.md:7-9`
- Modify: `references/fft-decision-trees.md` (FFT-01:26-30, FFT-04:151-159, FFT-05:182-188)

- [ ] **Step 1: Replace old template in quality-slos.md**

Replace lines 57-67 (the markdown template block and the "Written to" line) with:

```markdown
## Quality Budget Artifact

The quality budget is now a machine-readable YAML artifact. See:
- **Schema:** `references/quality-budget-schema.md`
- **Rules:** `references/quality-budget-rules.yaml`
- **Location:** `docs/sdlc/active/{task-id}/quality-budget.yaml`
- **System ledger:** `docs/sdlc/system-budget.jsonl`

Derivation: `scripts/derive-quality-budget.sh`. The old markdown format (`quality-budget.md`) is superseded.
```

- [ ] **Step 2: Reconcile reliability-ledger.md**

Replace lines 7-9:
```
## Ledger Location

`docs/sdlc/reliability-ledger.md` — append-only, one entry per completed task.
```

With:
```
## Ledger Location

`docs/sdlc/reliability-ledger.md` — per-task first-pass rate analysis, one entry per completed task.

**Relationship to system budget:** The reliability ledger computes per-level first-pass rates from bead traces. The system budget (`docs/sdlc/system-budget.jsonl`) aggregates task-level metrics for longitudinal analysis. The derivation scripts (`scripts/derive-quality-budget.sh`, `scripts/append-system-budget.sh`) consume bead traces directly — the reliability ledger is a parallel analysis artifact, not a prerequisite for the system budget.
```

- [ ] **Step 3: Update FFT budget_state references**

In FFT-01 (around line 26-30), after:
```
  Cue 3: Is the quality budget at WARNING or DEPLETED with no user task pending?
```

Add a clarifying note:
```
    (Read budget_state from quality-budget.yaml in the most recent completed task, or from system-budget.jsonl rolling window)
```

In FFT-04 (around line 151-159), after:
```
  Cue 5: cynefin == CLEAR and budget == healthy?
```

Add:
```
    (budget == quality-budget.yaml:budget_state for current task, or system-budget.jsonl rolling state if no current task budget)
```

In FFT-05 (around line 182-188), same treatment for:
```
  Cue 3: cynefin == CLEAR and budget == healthy?
  Cue 4: cynefin == CLEAR and budget != healthy?
```

Add source clarification after each.

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/quality-slos.md references/reliability-ledger.md references/fft-decision-trees.md
git commit -m "docs: update quality-slos, reliability-ledger, and FFT references

Replace old markdown template with pointer to new schema. Reconcile
reliability-ledger as parallel analysis (not prerequisite). Add
budget_state source clarification to FFT-01/04/05."
```

---

### Task 11: Update agents — normalizer, reliability-ledger, process-drift-monitor, losa-observer, llm-self-security

**Files:**
- Modify: `agents/normalizer.md:61-64`
- Modify: `agents/reliability-ledger.md:22-58`
- Modify: `agents/process-drift-monitor.md:74-92`
- Modify: `agents/losa-observer.md`
- Modify: `agents/llm-self-security.md:83`

- [ ] **Step 1: Update normalizer.md**

In line 63, replace:
```
`quality-budget.md`
```
With:
```
`quality-budget.yaml`
```

- [ ] **Step 2: Update reliability-ledger agent**

In the computation section (around line 22), add a note after the turbulence field format:

```markdown
**Relationship to quality-budget.yaml:** This agent reads bead traces directly for per-level first-pass rate computation. It does NOT consume quality-budget.yaml as its input — the bead-level denominator data is essential for correct L1/L2/L2.5/L2.75 rates. The shared `scripts/lib/quality-budget-lib.sh` helper provides common parsing functions used by both this agent's logic and the derivation scripts.
```

- [ ] **Step 3: Update process-drift-monitor.md**

In the trend analysis section (around line 74), replace:
```
If a prior ledger exists at `docs/sdlc/reliability-ledger.md`:
- Compare current rates against the most recent entry
```
With:
```
If `docs/sdlc/system-budget.jsonl` exists:
- Parse the JSONL ledger for rolling window analysis (last 10 tasks or 30 days per `references/quality-budget-rules.yaml`)
- Compare current zero_turbulence_rate, review_pass_rate, and latency metrics against rolling averages
- Check `docs/sdlc/system-budget-events.jsonl` for retroactive escape confirmations

If `docs/sdlc/system-budget.jsonl` does not exist, fall back to `docs/sdlc/reliability-ledger.md`:
- Compare current rates against the most recent entry
```

- [ ] **Step 4: Update losa-observer.md**

In the constraints section, add:

```markdown
**Escape reporting:** When an uncaught error is discovered on a merged bead, append an event to `docs/sdlc/system-budget-events.jsonl`:
```jsonl
{"task_id":"<task>","event":"escape_confirmed","date":"<UTC ISO 8601>","escape_count":1,"source":"losa","finding_id":"<id>"}
```
This updates the retroactive escape record without modifying the immutable primary ledger.
```

- [ ] **Step 5: Update llm-self-security.md**

Replace any reference to `quality-budget.md` with `quality-budget.yaml`. In the dispatch proportionality check section (around line 83), ensure it reads:

```
Read bead turbulence fields from bead files in `docs/sdlc/active/{task-id}/beads/` and the task's `quality-budget.yaml`.
```

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add agents/normalizer.md agents/reliability-ledger.md agents/process-drift-monitor.md agents/losa-observer.md agents/llm-self-security.md
git commit -m "feat: wire quality budget into agent definitions

Update normalizer to resume from quality-budget.yaml. Clarify
reliability-ledger agent remains bead-driven. Wire process-drift-monitor
to system-budget.jsonl. Add escape reporting to losa-observer.
Update llm-self-security references."
```

---

### Task 12: Update skills — normalize, evolve

**Files:**
- Modify: `skills/sdlc-normalize/SKILL.md:64`
- Modify: `skills/sdlc-evolve/SKILL.md`

- [ ] **Step 1: Update normalize SKILL.md**

In line 64, replace:
```
`quality-budget.md`
```
With:
```
`quality-budget.yaml`
```

- [ ] **Step 2: Update evolve SKILL.md**

Find the evolution prioritization logic. Add a note that system-budget.jsonl is the preferred data source for evolution prioritization:

```markdown
**Data source for evolution prioritization:** When deciding which evolution bead types to dispatch, consult `docs/sdlc/system-budget.jsonl` for longitudinal metrics. Prioritize evolution beads that address the lowest-performing metrics in the rolling window (e.g., if zero_turbulence_rate is declining, prioritize auto-rule generation and calibration tuning).
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-normalize/SKILL.md skills/sdlc-evolve/SKILL.md
git commit -m "docs: update normalize and evolve skills for quality budget

Replace quality-budget.md with quality-budget.yaml in normalize.
Add system-budget.jsonl as evolution prioritization data source."
```

---

### Task 13: Update commands/sdlc.md and README.md

**Files:**
- Modify: `commands/sdlc.md`
- Modify: `README.md:124-132`

- [ ] **Step 1: Update commands/sdlc.md**

After the existing content (line 16), add:

```markdown
Each task produces a `quality-budget.yaml` artifact that tracks turbulence, corrections, and SLI readings. This artifact gates Synthesize and Complete phase transitions. See `references/quality-budget-schema.md` for the full schema.
```

- [ ] **Step 2: Update README.md artifact table**

In the Per-Project Artifacts table (around line 124-132), add two rows:

```markdown
| Quality Budget | `docs/sdlc/active/{task-id}/quality-budget.yaml` | Task-level metrics, phase gate enforcement |
| System Budget | `docs/sdlc/system-budget.jsonl` | Cross-task longitudinal ledger |
| System Budget Events | `docs/sdlc/system-budget-events.jsonl` | Late-arriving escape corrections |
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add commands/sdlc.md README.md
git commit -m "docs: update command and README with quality budget artifacts

Add quality-budget.yaml description to /sdlc command. Add system
budget artifacts to README per-project artifact table."
```

---

### Task 14: Final verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (including the 4 new quality budget tests).

- [ ] **Step 2: Verify no stale quality-budget.md references remain**

```bash
cd /Users/q/.claude/plugins/sdlc-os
grep -rn "quality-budget\.md" skills/ agents/ references/ hooks/ commands/ README.md
```

Expected: Zero matches. All references should now be `quality-budget.yaml`.

- [ ] **Step 3: Verify all new files exist**

```bash
ls -la references/quality-budget-rules.yaml references/quality-budget-schema.md scripts/lib/quality-budget-lib.sh scripts/derive-quality-budget.sh scripts/append-system-budget.sh hooks/scripts/validate-quality-budget.sh hooks/tests/fixtures/quality-budget-valid.yaml hooks/tests/fixtures/quality-budget-missing-fields.yaml hooks/tests/fixtures/quality-budget-malformed.yaml
```

Expected: All 9 files exist.

- [ ] **Step 4: Verify derivation script runs on a synthetic task**

```bash
mkdir -p /tmp/test-qb/beads
cat > /tmp/test-qb/state.md << 'EOF'
# Test Task State
| Bead | Status |
|------|--------|
| B01 | merged |
| B02 | merged |
EOF

cat > /tmp/test-qb/beads/B01.md << 'EOF'
**Status:** merged
**Cynefin domain:** clear
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Dispatched at:** "2026-03-29T10:00:00Z"
**Review started at:** "2026-03-29T10:05:00Z"
**Completed at:** "2026-03-29T10:10:00Z"
EOF

cat > /tmp/test-qb/beads/B02.md << 'EOF'
**Status:** merged
**Cynefin domain:** complicated
**Turbulence:** {L0: 1, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Dispatched at:** "2026-03-29T10:15:00Z"
**Review started at:** "2026-03-29T10:20:00Z"
**Completed at:** "2026-03-29T10:30:00Z"
EOF

cd /Users/q/.claude/plugins/sdlc-os && bash scripts/derive-quality-budget.sh /tmp/test-qb --status ready
cat /tmp/test-qb/quality-budget.yaml
```

Expected: YAML output with `zero_turbulence_rate: 0.50` (1 of 2 beads zero turbulence), `turbulence_sum: 1`, `complexity_weight: 0.25`, `artifact_status: ready`.

- [ ] **Step 5: Cleanup synthetic test**

```bash
rm -rf /tmp/test-qb
```

- [ ] **Step 6: Spot-check all modified files for consistency**

Read each of the 16 modified files and confirm:
- No stale `quality-budget.md` references
- New references point to `quality-budget.yaml`
- Gate logic mentions artifact_status: ready/final correctly
- System budget references point to `system-budget.jsonl`
