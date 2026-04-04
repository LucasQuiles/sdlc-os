#!/bin/bash
# audit-metrics.sh -- Extract audit metrics from colony log files.
#
# Parses colony-sessions.log and colony-bridge.log for structured reporting.
# Usage: bash audit-metrics.sh [--sessions-log <path>] [--bridge-log <path>]

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSIONS_LOG="${SESSIONS_LOG:-${SCRIPT_DIR}/colony-sessions.log}"
BRIDGE_LOG="${BRIDGE_LOG:-${SCRIPT_DIR}/colony-bridge.log}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sessions-log) SESSIONS_LOG="$2"; shift 2;;
    --bridge-log)   BRIDGE_LOG="$2"; shift 2;;
    *)              echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

echo "========================================"
echo "Colony Audit Metrics Report"
echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "========================================"
echo ""

# ---------------------------------------------------------------------------
# Session metrics (colony-sessions.log)
# ---------------------------------------------------------------------------

echo "--- Session Metrics ---"

if [[ -f "$SESSIONS_LOG" ]]; then
  session_count="$(wc -l < "$SESSIONS_LOG" | tr -d ' ')"
  echo "Total sessions: ${session_count}"

  if [[ "$session_count" -gt 0 ]]; then
    # Extract costs and wall_clock using python for JSON parsing reliability
    python3 -c "
import json, sys

costs = []
wall_clocks = []
for line in open('${SESSIONS_LOG}'):
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        cost = data.get('total_cost_usd', 0)
        if isinstance(cost, (int, float)):
            costs.append(cost)
        wc = data.get('wall_clock_s', data.get('wall_clock', 0))
        if isinstance(wc, (int, float)) and wc > 0:
            wall_clocks.append(wc)
    except json.JSONDecodeError:
        continue

total_cost = sum(costs)
print(f'Total cost (USD): \${total_cost:.4f}')
if costs:
    print(f'Avg cost per session: \${total_cost / len(costs):.4f}')
if wall_clocks:
    avg_wc = sum(wall_clocks) / len(wall_clocks)
    print(f'Avg wall_clock (s): {avg_wc:.1f}')
    print(f'Total wall_clock (s): {sum(wall_clocks):.1f}')
else:
    print('Avg wall_clock: (not recorded)')
" 2>/dev/null || echo "  (parse error)"
  fi
else
  echo "  (no sessions log found at ${SESSIONS_LOG})"
fi

echo ""

# ---------------------------------------------------------------------------
# Bridge metrics (colony-bridge.log)
# ---------------------------------------------------------------------------

echo "--- Bridge Metrics ---"

if [[ -f "$BRIDGE_LOG" ]]; then
  bridge_count="$(wc -l < "$BRIDGE_LOG" | tr -d ' ')"
  echo "Total bridge actions: ${bridge_count}"

  if [[ "$bridge_count" -gt 0 ]]; then
    python3 -c "
import json, sys
from collections import Counter

actions = Counter()
elapsed_ms_vals = []
sc_col_hits = Counter()

for line in open('${BRIDGE_LOG}'):
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        action = data.get('action', 'unknown')
        actions[action] += 1
        elapsed = data.get('elapsed_ms', 0)
        if isinstance(elapsed, (int, float)) and elapsed > 0:
            elapsed_ms_vals.append(elapsed)
        # Count SC-COL constraint hits
        error = data.get('error', '')
        if isinstance(error, str):
            import re
            for m in re.finditer(r'SC-COL-\d+', error):
                sc_col_hits[m.group()] += 1
    except json.JSONDecodeError:
        continue

print('Actions by type:')
for action, count in sorted(actions.items()):
    print(f'  {action}: {count}')

if elapsed_ms_vals:
    avg_ms = sum(elapsed_ms_vals) / len(elapsed_ms_vals)
    print(f'Avg elapsed_ms: {avg_ms:.1f}')
    print(f'Max elapsed_ms: {max(elapsed_ms_vals):.1f}')
else:
    print('Avg elapsed_ms: (not recorded)')

if sc_col_hits:
    print('SC-COL constraint hits:')
    for sc, count in sorted(sc_col_hits.items()):
        print(f'  {sc}: {count}')
else:
    print('SC-COL constraint hits: 0')
" 2>/dev/null || echo "  (parse error)"
  fi
else
  echo "  (no bridge log found at ${BRIDGE_LOG})"
fi

# ---------------------------------------------------------------------------
# Per-Bead Cost, Completion Rate, Wall Clock Percentiles (spec 3.6)
# ---------------------------------------------------------------------------

echo "--- Per-Bead Cost & Completion ---"

if [[ -f "$SESSIONS_LOG" ]]; then
  python3 -c "
import json, sys
from collections import defaultdict

bead_costs = defaultdict(float)
dispatched = set()
merged = set()
wall_clocks = []

for line in open('${SESSIONS_LOG}'):
    line = line.strip()
    if not line: continue
    try:
        data = json.loads(line)
        bead_ids = data.get('bead_ids', [])
        cost = data.get('total_cost_usd', 0)
        st = data.get('session_type', '')
        wc = data.get('wall_clock_s', 0)
        if isinstance(wc, (int, float)) and wc > 0:
            wall_clocks.append(wc)
        if st == 'DISPATCH': dispatched.update(bead_ids)
        elif st == 'SYNTHESIZE': merged.update(bead_ids)
        if bead_ids and isinstance(cost, (int, float)):
            share = cost / len(bead_ids)
            for b in bead_ids:
                bead_costs[b] += share
    except: continue

if bead_costs:
    print('Per-bead costs:')
    for b, c in sorted(bead_costs.items(), key=lambda x: -x[1]):
        print(f'  {b}: \${c:.2f}')

rate = len(merged) / len(dispatched) if dispatched else 0
print(f'Completion rate: {rate:.1%} ({len(merged)}/{len(dispatched)})')

if wall_clocks:
    wall_clocks.sort()
    p50 = wall_clocks[len(wall_clocks)//2]
    p95 = wall_clocks[int(len(wall_clocks)*0.95)]
    print(f'Wall clock p50: {p50:.0f}s  p95: {p95:.0f}s')
" 2>/dev/null || echo "  (parse error)"
fi

echo ""
echo "--- End of Report ---"
