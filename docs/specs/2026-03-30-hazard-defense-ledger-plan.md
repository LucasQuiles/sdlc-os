# Hazard/Defense Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make STPA safety analysis a first-class, machine-readable Phase B artifact — the Hazard/Defense Ledger — that links hazards, UCAs, defenses, and catch points into an auditable control loop.

**Architecture:** Two canonical artifacts (task YAML + system JSONL), structured intermediate from safety-analyst (stpa-analysis.yaml), seeding/derivation/append scripts with shared lib, validation hook, bead field projections replacing Phase B placeholders, and phase gate enforcement for COMPLEX/security-sensitive work.

**Tech Stack:** YAML (schemas), JSONL (system ledger), Bash (scripts, hooks, tests), Markdown (docs)

**Spec:** `docs/specs/2026-03-29-hazard-defense-ledger-design.md`

---

### Task 1: Create shared hazard-defense library

**Files:**
- Create: `scripts/lib/hazard-defense-lib.sh`

- [ ] **Step 1: Create the shared library**

Write `scripts/lib/hazard-defense-lib.sh`:

```bash
#!/bin/bash
# hazard-defense-lib.sh — Shared helpers for hazard/defense ledger operations
set -euo pipefail

# Generate HDL record ID from bead_id, control action index, UCA index
# Usage: hdl_record_id "B03" 1 2
hdl_record_id() {
  local bead_id="$1" ca_idx="$2" uca_idx="$3"
  echo "HDL-${bead_id}-CA${ca_idx}-UCA${uca_idx}"
}

# Count records by status in a ledger YAML file
# Usage: count_records_by_status "ledger.yaml" "caught"
count_records_by_status() {
  local file="$1" status="$2"
  grep -c "status: ${status}" "$file" 2>/dev/null || echo 0
}

# Count records with non-empty intended_defenses
# Usage: count_records_with_defense "ledger.yaml"
count_records_with_defense() {
  local file="$1"
  # Records where intended_defenses has at least one "- layer:" entry
  local total
  total=$(grep -c "^    - id:" "$file" 2>/dev/null || echo 0)
  local without
  without=$(count_records_without_defense "$file")
  echo $((total - without))
}

# Count records with empty intended_defenses
count_records_without_defense() {
  local file="$1"
  # A record without defense has "intended_defenses: []" or no "- layer:" between
  # its intended_defenses: and actual_catch_point:
  python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
count = 0
for r in data.get('records', []):
    if not r.get('intended_defenses'):
        count += 1
print(count)
" "$file" 2>/dev/null || echo 0
}

# Compute coverage_state from summary fields
# Usage: compute_coverage_state without_defense escapes_at_close residual_high open_count
compute_coverage_state() {
  local without="$1" escapes="$2" high_risk="$3" open="$4"
  if [ "$without" -gt 0 ] && [ "$high_risk" -gt 0 ]; then echo "depleted"; return; fi
  if [ "$without" -gt 0 ] || [ "$escapes" -gt 0 ]; then echo "warning"; return; fi
  if [ "$open" -gt 0 ]; then echo "warning"; return; fi
  echo "healthy"
}

# Derive full summary from ledger records (requires python3 + PyYAML)
# Usage: derive_hdl_summary "ledger.yaml"
derive_hdl_summary() {
  local file="$1"
  python3 -c "
import yaml, sys, json
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
records = data.get('records', [])
beads = set(r['bead_id'] for r in records)
total = len(records)
with_def = sum(1 for r in records if r.get('intended_defenses'))
without_def = total - with_def
high_risk = sum(1 for r in records if r.get('residual_risk') == 'high')
escaped = sum(1 for r in records if r.get('status') == 'escaped')
open_count = sum(1 for r in records if r.get('status') == 'open')
if without_def > 0 and high_risk > 0:
    state = 'depleted'
elif without_def > 0 or escaped > 0:
    state = 'warning'
elif open_count > 0:
    state = 'warning'
else:
    state = 'healthy'
print(json.dumps({
    'qualifying_beads': len(beads),
    'records_total': total,
    'records_with_defense': with_def,
    'records_without_defense': without_def,
    'residual_high_risk': high_risk,
    'escapes_known_at_close': escaped,
    'coverage_state': state
}))
" "$file"
}

# Format current UTC timestamp as ISO 8601
now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
```

- [ ] **Step 2: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/lib/hazard-defense-lib.sh
git add scripts/lib/hazard-defense-lib.sh
git commit -m "feat: add shared hazard-defense ledger library

Helpers for record ID generation, status counting, defense coverage
computation, summary derivation (python3+PyYAML), and coverage_state."
```

---

### Task 2: Create seeding script

**Files:**
- Create: `scripts/seed-hazard-defense-ledger.sh`

- [ ] **Step 1: Create the seeding script**

Write `scripts/seed-hazard-defense-ledger.sh`. This script reads `stpa-analysis.yaml` (the structured output from safety-analyst) and produces `hazard-defense-ledger.yaml` with one record per bead + control_action + UCA.

```bash
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
```

- [ ] **Step 2: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/seed-hazard-defense-ledger.sh
git add scripts/seed-hazard-defense-ledger.sh
git commit -m "feat: add hazard-defense ledger seeding script

Reads stpa-analysis.yaml (safety-analyst structured output) and
produces hazard-defense-ledger.yaml with one record per bead +
control_action + UCA combination."
```

---

### Task 3: Create summary derivation and system append scripts

**Files:**
- Create: `scripts/derive-hazard-defense-summary.sh`
- Create: `scripts/append-system-hazard-defense.sh`

- [ ] **Step 1: Create the summary derivation script**

Write `scripts/derive-hazard-defense-summary.sh`:

```bash
#!/bin/bash
# derive-hazard-defense-summary.sh — Recompute summary fields from ledger records
# Usage: derive-hazard-defense-summary.sh <task-dir> [--status active|final]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hazard-defense-lib.sh"

TASK_DIR="${1:?Usage: derive-hazard-defense-summary.sh <task-dir> [--status active|final]}"
STATUS="${3:-active}"
LEDGER="$TASK_DIR/hazard-defense-ledger.yaml"

[ -f "$LEDGER" ] || { echo "ERROR: hazard-defense-ledger.yaml not found" >&2; exit 1; }

NOW=$(now_utc)
SUMMARY_JSON=$(derive_hdl_summary "$LEDGER")

# Update the ledger in place using python3
python3 -c "
import yaml, sys, json

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

summary = json.loads(sys.argv[2])
data['summary'] = summary
data['artifact_status'] = sys.argv[3]
data['derived_at'] = sys.argv[4]
data['last_updated'] = sys.argv[4]

with open(sys.argv[1], 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Summary: {summary[\"records_total\"]} records, coverage: {summary[\"coverage_state\"]}')
" "$LEDGER" "$SUMMARY_JSON" "$STATUS" "$NOW"
```

- [ ] **Step 2: Create the system append script**

Write `scripts/append-system-hazard-defense.sh`:

```bash
#!/bin/bash
# append-system-hazard-defense.sh — Append completed task HDL to system ledger
# Usage: append-system-hazard-defense.sh <task-dir> <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hazard-defense-lib.sh"

TASK_DIR="${1:?Usage: append-system-hazard-defense.sh <task-dir> <project-dir>}"
PROJECT_DIR="${2:?Usage: append-system-hazard-defense.sh <task-dir> <project-dir>}"
LEDGER="$TASK_DIR/hazard-defense-ledger.yaml"
SYSTEM_LEDGER="$PROJECT_DIR/docs/sdlc/system-hazard-defense.jsonl"

[ -f "$LEDGER" ] || { echo "ERROR: hazard-defense-ledger.yaml not found" >&2; exit 1; }

# Build JSONL entry from final ledger
python3 -c "
import yaml, sys, json
from collections import Counter

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

if data.get('artifact_status') != 'final':
    print(f'ERROR: artifact_status is {data.get(\"artifact_status\")}, must be final', file=sys.stderr)
    sys.exit(1)

records = data.get('records', [])
catch_dist = Counter()
uca_fingerprints = []
for r in records:
    cp = r.get('actual_catch_point', {})
    layer = cp.get('layer') or 'not_tested'
    catch_dist[layer] += 1
    # UCA fingerprint: category + first 40 chars of scenario
    uca = r.get('unsafe_control_action', {})
    fp = f'{uca.get(\"category\", \"unknown\")}:{uca.get(\"scenario\", \"\")[:40]}'
    uca_fingerprints.append(fp)

# Find repeated fingerprints
fp_counts = Counter(uca_fingerprints)
repeated = [fp for fp, count in fp_counts.items() if count > 1]

entry = {
    'task_id': data['task_id'],
    'date': data['derived_at'],
    'qualifying_beads': data['summary']['qualifying_beads'],
    'records_total': data['summary']['records_total'],
    'records_with_defense': data['summary']['records_with_defense'],
    'records_without_defense': data['summary']['records_without_defense'],
    'catch_layer_distribution': dict(catch_dist),
    'escapes_at_close': data['summary']['escapes_known_at_close'],
    'residual_high_risk': data['summary']['residual_high_risk'],
    'repeated_uca_fingerprints': repeated,
    'coverage_state': data['summary']['coverage_state'],
}

print(json.dumps(entry, separators=(',', ':')))
" "$LEDGER" >> "$SYSTEM_LEDGER"

echo "Appended $(basename "$TASK_DIR") to system-hazard-defense.jsonl"
```

- [ ] **Step 3: Make executable and commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
chmod +x scripts/derive-hazard-defense-summary.sh scripts/append-system-hazard-defense.sh
git add scripts/derive-hazard-defense-summary.sh scripts/append-system-hazard-defense.sh
git commit -m "feat: add HDL summary derivation and system append scripts

derive-hazard-defense-summary.sh recomputes summary from records.
append-system-hazard-defense.sh builds JSONL with catch-layer
distribution and UCA fingerprints for longitudinal analysis."
```

---

### Task 4: Create schema documentation

**Files:**
- Create: `references/hazard-defense-schema.md`

- [ ] **Step 1: Create the schema doc**

Write `references/hazard-defense-schema.md` reproducing the canonical schema from the design spec (Section "Schema"). Include:
- Task ledger YAML schema with all fields
- safety-analyst output contract (`stpa-analysis.yaml` schema)
- Canonical unit of record definition
- coverage_state derivation algorithm
- System ledger JSONL schema + events schema
- Phase gate requirements (seeded → active → final)
- Bead projection rules

The content is fully specified in `docs/specs/2026-03-29-hazard-defense-ledger-design.md`. This file IS the schema definition.

- [ ] **Step 2: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/hazard-defense-schema.md
git commit -m "docs: add hazard-defense ledger schema reference

Canonical schema for task ledger (YAML), stpa-analysis intermediate
(YAML), system ledger (JSONL), events (JSONL), coverage_state
derivation, phase gates, and bead projection rules."
```

---

### Task 5: Create validation hook + tests + fixtures

**Files:**
- Create: `hooks/scripts/validate-hazard-defense-ledger.sh`
- Create: `hooks/tests/fixtures/hdl-valid/hazard-defense-ledger.yaml`
- Create: `hooks/tests/fixtures/hdl-missing/hazard-defense-ledger.yaml`
- Create: `hooks/tests/fixtures/hdl-malformed/hazard-defense-ledger.yaml`
- Modify: `hooks/hooks.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create the validation hook**

Write `hooks/scripts/validate-hazard-defense-ledger.sh`:

```bash
#!/bin/bash
# validate-hazard-defense-ledger.sh — PostToolUse hook: validates HDL on Write/Edit
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only trigger on hazard-defense-ledger.yaml writes
if [[ "$file_path" != *"hazard-defense-ledger.yaml" ]]; then
  exit 0
fi

if [[ ! -f "$file_path" ]]; then
  echo "hazard-defense-ledger.yaml written but file not found at $file_path" >&2
  exit 2
fi

# Validate: YAML parse
_has_pyyaml=false
if command -v python3 &>/dev/null && python3 -c "import yaml" 2>/dev/null; then
  _has_pyyaml=true
fi

if [[ "$_has_pyyaml" == "true" ]]; then
  if ! python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"hazard-defense-ledger.yaml is not valid YAML"}' >&2
    exit 2
  fi
else
  if ! grep -qE '^[a-z_]+:' "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"hazard-defense-ledger.yaml has no recognizable YAML keys"}' >&2
    exit 2
  fi
fi

# Validate: required top-level fields
for field in "schema_version:" "task_id:" "artifact_status:" "stpa_required:"; do
  if ! grep -q "^${field}" "$file_path"; then
    echo "{\"decision\":\"deny\",\"reason\":\"hazard-defense-ledger.yaml missing required field: $field\"}" >&2
    exit 2
  fi
done

# Validate: artifact_status
STATUS=$(grep "^artifact_status:" "$file_path" | sed 's/artifact_status: *//')
case "$STATUS" in
  seeded|active|final) ;;
  *) echo '{"decision":"deny","reason":"artifact_status must be seeded, active, or final"}' >&2; exit 2 ;;
esac

# Validate: required sections
for section in "summary:" "records:"; do
  if ! grep -q "^${section}" "$file_path"; then
    echo "{\"decision\":\"deny\",\"reason\":\"hazard-defense-ledger.yaml missing required section: $section\"}" >&2
    exit 2
  fi
done

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/validate-hazard-defense-ledger.sh
```

- [ ] **Step 3: Create test fixtures**

Write `hooks/tests/fixtures/hdl-valid/hazard-defense-ledger.yaml` — a minimal valid ledger with one record.

Write `hooks/tests/fixtures/hdl-missing/hazard-defense-ledger.yaml` — only `schema_version` and `task_id` (missing artifact_status, stpa_required, summary, records).

Write `hooks/tests/fixtures/hdl-malformed/hazard-defense-ledger.yaml` — invalid YAML.

- [ ] **Step 4: Add hook to hooks.json**

Add PostToolUse entry for `validate-hazard-defense-ledger.sh` with matcher `"Write|Edit"`, timeout 10.

- [ ] **Step 5: Add test cases to test-hooks.sh**

Use same temp-file + `run_test` pattern as quality budget tests. 4 tests: valid passes (exit 0), missing fields rejected (exit 2), malformed rejected (exit 2), non-ledger file ignored (exit 0).

Update expected test count.

- [ ] **Step 6: Run tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-hazard-defense-ledger.sh hooks/hooks.json hooks/tests/test-hooks.sh hooks/tests/fixtures/hdl-valid/hazard-defense-ledger.yaml hooks/tests/fixtures/hdl-missing/hazard-defense-ledger.yaml hooks/tests/fixtures/hdl-malformed/hazard-defense-ledger.yaml
git commit -m "feat: add hazard-defense ledger validation hook with tests

PostToolUse hook validates HDL structure on Write/Edit. YAML parse,
required fields (schema_version, task_id, artifact_status, stpa_required),
artifact_status enum, required sections (summary, records).
4 test cases with 3 fixtures."
```

---

### Task 6: Update safety-analyst agent with structured output contract

**Files:**
- Modify: `agents/safety-analyst.md:69-71`

- [ ] **Step 1: Read the current file**

Read `agents/safety-analyst.md` to understand the full output section.

- [ ] **Step 2: Update the output format**

Find the output section (around lines 69-71) that currently produces bead fields:
```
- `control_actions`: list of control actions identified in Step 1
- `unsafe_control_actions`: the UCA enumeration from Step 2
```

Replace with structured output contract:

```markdown
### Output

Produce a structured YAML artifact at `docs/sdlc/active/{task-id}/stpa-analysis.yaml`:

```yaml
schema_version: 1
task_id: "{task-id}"
beads_analyzed:
  - bead_id: "{bead-id}"
    cynefin_domain: "{domain}"
    security_sensitive: true | false
    control_actions:
      - interface: {N}
        controller: "{name}"
        action: "{what the controller does}"
        hazard: "{what can go wrong}"
        ucas:
          - category: not_provided | wrong_timing_or_order | stopped_too_soon | applied_too_long
            scenario: "{specific UCA scenario}"
            safety_constraint: "{SC-NNN or null}"
            suggested_defenses:
              - layer: L0 | L1 | L2 | L2_5 | L2_75
                mechanism: "{specific check or agent}"
```

This structured output is consumed by `scripts/seed-hazard-defense-ledger.sh` to create the canonical `hazard-defense-ledger.yaml`. Bead fields (`control_actions`, `unsafe_control_actions`) are then projected from the ledger as compact summaries.

Do NOT write free-text analysis. Produce the YAML artifact. Every control action must have at least one UCA. Every UCA must have a category from the STPA standard four.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add agents/safety-analyst.md
git commit -m "feat: update safety-analyst output to structured stpa-analysis.yaml

Replaces prose+bead-field output with machine-readable YAML contract.
One entry per bead with control actions, UCAs, safety constraints,
and suggested defenses. Consumed by seed-hazard-defense-ledger.sh."
```

---

### Task 7: Update orchestrate SKILL.md — Phase B placeholders, seeding, gates

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md:120-122, :195, :394, artifact list, Synthesize/Complete`

- [ ] **Step 1: Replace Phase B placeholders in bead schema**

Find lines 120-122:
```
**Control actions:** [Phase B — not yet populated]
**Unsafe control actions:** [Phase B — not yet populated]
**Latent condition trace:** [Phase B — not yet populated]
```

Replace with:
```
**Control actions:** [Projected from hazard-defense-ledger.yaml — distinct control_action values for this bead]
**Unsafe control actions:** [Projected from hazard-defense-ledger.yaml — UCA summaries: control_action — category — scenario]
**Latent condition trace:** [Projected from hazard-defense-ledger.yaml — See HDL-{bead-id}-* records]
```

- [ ] **Step 2: Add ledger seeding to Architect phase**

Find line 195 (safety-analyst dispatch). After the existing sentence, add:

```markdown
After safety-analyst produces `stpa-analysis.yaml`, run `scripts/seed-hazard-defense-ledger.sh <task-dir>` to create the seeded `hazard-defense-ledger.yaml`. Then project bead fields from the ledger: for each qualifying bead, update `Control actions`, `Unsafe control actions`, and `Latent condition trace` with compact summaries from the ledger records.
```

- [ ] **Step 3: Update REPAIR profile STPA note**

Find line 394 (REPAIR STPA note). After the existing sentence about populating bead fields, add:

```markdown
For REPAIR beads, safety-analyst also produces `stpa-analysis.yaml` and the seeding script creates the ledger in the same inline step.
```

- [ ] **Step 4: Add HDL to artifact list**

Find the artifact list (Scout Artifacts section). Add:

```markdown
- `hazard-defense-ledger.yaml` — Machine-readable Phase B artifact (created during Architect as `seeded`, enriched during Execute as `active`, finalized during Synthesize/Complete as `final`). Schema: `references/hazard-defense-schema.md`. Required for COMPLEX or security_sensitive beads.
- `stpa-analysis.yaml` — Structured intermediate from safety-analyst (created during Architect, consumed by seeding script)
- `system-hazard-defense.jsonl` — Append-only system-level HDL ledger (one entry per completed STPA-required task)
- `system-hazard-defense-events.jsonl` — Late-arriving HDL corrections
```

- [ ] **Step 5: Add HDL phase gates**

In the Synthesize section, add:

```markdown
**HDL Synthesize gate (STPA-required tasks only):** Before entering Synthesize, verify hazard-defense-ledger.yaml exists with artifact_status `active` or higher. No record may have status `open` unless explicitly justified with `accepted_residual` + non-empty notes. Run `scripts/derive-hazard-defense-summary.sh <task-dir> --status active`.
```

In the Complete section, add:

```markdown
**HDL Complete gate (STPA-required tasks only):** Before marking complete, verify artifact_status is `final`, every record has status in {caught, escaped, accepted_residual}, and summary.coverage_state is computed. Run `scripts/append-system-hazard-defense.sh <task-dir> <project-dir>`.
```

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat: wire hazard-defense ledger into orchestrate lifecycle

Replace Phase B placeholders with ledger projection rules. Add seeding
step after safety-analyst in Architect. Add REPAIR inline seeding.
Add HDL artifacts to inventory. Add Synthesize and Complete gates."
```

---

### Task 8: Update remaining agents and references

**Files:**
- Modify: `agents/latent-condition-tracer.md:61`
- Modify: `agents/process-drift-monitor.md:113-115`
- Modify: `agents/losa-observer.md`
- Modify: `references/artifact-templates.md:30-32, task artifact table`
- Modify: `references/stpa-control-structure.md:4, telemetry section`

- [ ] **Step 1: Update latent-condition-tracer.md**

Find line 61:
```
Populate the bead's `latent_condition_trace` field with this classification.
```
Replace with:
```
Populate the matching record in `hazard-defense-ledger.yaml` with the latent condition trace (source_layer, source_reason, artifact_ref). Also update the bead's `Latent condition trace` field with a compact summary referencing the HDL record.
```

- [ ] **Step 2: Update process-drift-monitor.md**

Find lines 113-115 (Phase B field checks). Replace:
```
- `control_actions` / `unsafe_control_actions` on COMPLEX beads: always empty (safety-analyst not dispatched)
```
With:
```
- `hazard-defense-ledger.yaml` missing or stale for COMPLEX/security-sensitive tasks (safety-analyst not dispatched or seeding script not run)
- System HDL ledger (`docs/sdlc/system-hazard-defense.jsonl`): repeated UCA fingerprints across tasks = normalization of deviance signal
- Catch-layer distribution shifting outward (more L2.5+ catches, fewer L0/L1) = drift into failure
```

- [ ] **Step 3: Update losa-observer.md**

After the existing escape reporting section (which writes to system-budget-events.jsonl), add:

```markdown
**HDL escape reporting:** For STPA-required tasks, also append to `docs/sdlc/system-hazard-defense-events.jsonl`:
```jsonl
{"task_id":"<task>","event":"escape_confirmed","date":"<UTC ISO 8601>","record_id":"HDL-<bead>-<CA>-<UCA>","source":"losa","finding_id":"<id>"}
```
```

- [ ] **Step 4: Update artifact-templates.md Phase B placeholders**

Find lines 30-32:
```
**Control actions:** [Phase B — not yet populated]
**Unsafe control actions:** [Phase B — not yet populated]
**Latent condition trace:** [Phase B — not yet populated]
```
Replace with (same as orchestrate SKILL.md):
```
**Control actions:** [Projected from hazard-defense-ledger.yaml — distinct control_action values for this bead]
**Unsafe control actions:** [Projected from hazard-defense-ledger.yaml — UCA summaries: control_action — category — scenario]
**Latent condition trace:** [Projected from hazard-defense-ledger.yaml — See HDL-{bead-id}-* records]
```

Add to Task Artifacts table:
```
| Hazard/Defense Ledger | `hazard-defense-ledger.yaml` | Phase 3 (Architect) | COMPLEX or security_sensitive beads — gates Synthesize and Complete |
| STPA Analysis | `stpa-analysis.yaml` | Phase 3 (Architect) | Intermediate: consumed by seeding script |
```

- [ ] **Step 5: Update stpa-control-structure.md**

Find line 4:
```
Maintained per Phase B Safety Control Layer design (2026-03-26).
```
Replace with:
```
Maintained per Phase B Safety Control Layer. Canonical Phase B artifact: `hazard-defense-ledger.yaml` (see `references/hazard-defense-schema.md`).
```

In the telemetry section (around lines 88-94), add the HDL to the telemetry artifacts diagram:
```
│HDL ledger         │
│(from safety-      │
│analyst + seeding   │
│script)            │
```

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add agents/latent-condition-tracer.md agents/process-drift-monitor.md agents/losa-observer.md references/artifact-templates.md references/stpa-control-structure.md
git commit -m "feat: wire HDL into agents and references

Update latent-condition-tracer to write to ledger records.
Update process-drift-monitor with HDL staleness + drift checks.
Add HDL escape reporting to losa-observer. Replace Phase B
placeholders in artifact-templates. Add HDL to STPA control structure."
```

---

### Task 9: Update hooks, gate, adversarial, normalize, and docs

**Files:**
- Modify: `hooks/scripts/validate-decision-trace.sh:90-124`
- Modify: `skills/sdlc-gate/SKILL.md`
- Modify: `skills/sdlc-adversarial/SKILL.md:96`
- Modify: `skills/sdlc-normalize/SKILL.md:64`
- Modify: `README.md`

- [ ] **Step 1: Fix validate-decision-trace.sh**

Two changes:

**a)** Fix the Cynefin field-name bug at line 92. Replace:
```bash
CYNEFIN_DOMAIN=$(echo "$CONTENT" | sed -n 's/^\*\*Cynefin:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
```
With:
```bash
CYNEFIN_DOMAIN=$(echo "$CONTENT" | sed -n 's/^\*\*Cynefin domain:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
```

**b)** Update Phase B enforcement (lines 107-121). Replace the check for raw bead field presence with ledger record existence:
```bash
# Phase B: check hazard-defense-ledger.yaml has records for this bead
if [[ "$PHASE_B_REQUIRED" == "true" ]] && [[ -n "$PHASE_B_STATUS" ]] && [[ "$PHASE_B_STATUS" != "pending" ]] && [[ "$PHASE_B_STATUS" != "submitted" ]]; then
  TASK_DIR=$(dirname "$(dirname "$file_path")")
  HDL_FILE="$TASK_DIR/hazard-defense-ledger.yaml"
  BEAD_ID=$(basename "$file_path" .md)
  if [[ -f "$HDL_FILE" ]]; then
    if ! grep -q "bead_id: ${BEAD_ID}" "$HDL_FILE" 2>/dev/null; then
      echo "HOOK_WARNING: Phase B: hazard-defense-ledger.yaml exists but has no records for bead $BEAD_ID" >&2
    fi
  else
    echo "HOOK_WARNING: Phase B: hazard-defense-ledger.yaml not found for STPA-required bead $BEAD_ID" >&2
  fi
fi
```

- [ ] **Step 2: Update sdlc-gate/SKILL.md**

After the Quality Budget checklist added in Phase 1, add:

```markdown
### Hazard/Defense Ledger (STPA-required tasks only)
- Does `hazard-defense-ledger.yaml` exist for tasks with COMPLEX or security_sensitive beads?
- Is `artifact_status` appropriate? (`seeded` or higher for Execute, `active` for Synthesize, `final` for Complete)
- Are any records still `open`? (Must be resolved before Complete)
- Is `coverage_state` computed and non-depleted? If depleted, flag for user attention.
```

- [ ] **Step 3: Update sdlc-adversarial/SKILL.md**

Find line 96 (UCA probe selection). Replace:
```
For COMPLEX and security-sensitive beads, red team commanders also receive the bead's `unsafe_control_actions` list from the safety-analyst's STPA analysis.
```
With:
```
For COMPLEX and security-sensitive beads, red team commanders also receive the bead's UCA records from `hazard-defense-ledger.yaml`. Each HDL record with `status: open` and matching `bead_id` provides a systematic attack vector — probe each UCA scenario. When a red team probe catches a UCA-related issue, the Conductor updates the matching HDL record's `actual_catch_point` with the AQS layer and finding reference.
```

- [ ] **Step 4: Update sdlc-normalize/SKILL.md**

Find line 64 (resume artifact list). Add `hazard-defense-ledger.yaml` alongside the existing artifacts:

After `quality-budget.yaml`, add `hazard-defense-ledger.yaml (if exists)`.

- [ ] **Step 5: Update README.md**

Add to artifact table:
```
| Hazard/Defense Ledger | `docs/sdlc/active/{task-id}/hazard-defense-ledger.yaml` | Phase B safety control, defense coverage tracking |
| System HDL | `docs/sdlc/system-hazard-defense.jsonl` | Cross-task UCA patterns, catch-layer distribution |
| System HDL Events | `docs/sdlc/system-hazard-defense-events.jsonl` | Late-arriving defense corrections |
```

Update hook count (increment by 1) and add table row:
```
| validate-hazard-defense-ledger.sh | PostToolUse | **Blocking** — HDL schema validation |
```

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-decision-trace.sh skills/sdlc-gate/SKILL.md skills/sdlc-adversarial/SKILL.md skills/sdlc-normalize/SKILL.md README.md
git commit -m "feat: wire HDL into hooks, gate, adversarial, normalize, and docs

Fix Cynefin field-name bug in decision-trace hook. Update Phase B
enforcement to check ledger records per bead. Add HDL gate checklist.
Update AQS to read UCA probes from ledger. Add to normalize resume
list and README artifacts/hooks."
```

---

### Task 10: Final verification

- [ ] **Step 1: Run hook tests**

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests pass (previous + 4 new HDL tests).

- [ ] **Step 2: Verify no stale "Phase B — not yet populated" references**

```bash
grep -rn "Phase B — not yet populated" skills/ agents/ references/
```

Expected: Zero matches — all replaced with ledger projection rules.

- [ ] **Step 3: Verify all new files exist**

```bash
ls -la scripts/lib/hazard-defense-lib.sh scripts/seed-hazard-defense-ledger.sh scripts/derive-hazard-defense-summary.sh scripts/append-system-hazard-defense.sh references/hazard-defense-schema.md hooks/scripts/validate-hazard-defense-ledger.sh hooks/tests/fixtures/hdl-valid/hazard-defense-ledger.yaml hooks/tests/fixtures/hdl-missing/hazard-defense-ledger.yaml hooks/tests/fixtures/hdl-malformed/hazard-defense-ledger.yaml
```

Expected: All 9 files exist.

- [ ] **Step 4: Verify Cynefin field-name fix**

```bash
grep -n "Cynefin:" hooks/scripts/validate-decision-trace.sh
```

Expected: Only `Cynefin domain:` pattern, no bare `Cynefin:`.

- [ ] **Step 5: Verify seeding script with synthetic data**

```bash
mkdir -p /tmp/test-hdl

cat > /tmp/test-hdl/stpa-analysis.yaml << 'EOF'
schema_version: 1
task_id: test-hdl-001
beads_analyzed:
  - bead_id: B03
    cynefin_domain: complex
    security_sensitive: true
    control_actions:
      - interface: 4
        controller: Conductor
        action: dispatch state mutation
        hazard: state corruption across modal transitions
        ucas:
          - category: wrong_timing_or_order
            scenario: mutation applied before guard state committed
            safety_constraint: SC-003
            suggested_defenses:
              - layer: L0
                mechanism: runner invariant check
              - layer: L1
                mechanism: sentinel state-transition review
EOF

cd /Users/q/.claude/plugins/sdlc-os && bash scripts/seed-hazard-defense-ledger.sh /tmp/test-hdl
cat /tmp/test-hdl/hazard-defense-ledger.yaml
```

Expected: YAML with 1 record (HDL-B03-CA1-UCA1), artifact_status: seeded, 1 qualifying bead, 1 record with 2 intended defenses.

- [ ] **Step 6: Cleanup and spot-check**

```bash
rm -rf /tmp/test-hdl
```

Spot-check: orchestrate SKILL.md has projection rules (not "Phase B"), safety-analyst mentions stpa-analysis.yaml, adversarial reads from ledger, decision-trace hook uses `Cynefin domain:`.
