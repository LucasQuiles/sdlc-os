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
