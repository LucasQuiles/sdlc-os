#!/bin/bash
set -euo pipefail

DISPATCH="$HOME/LAB/sdlc-os/hooks/sdlc-dispatch.sh"
ITERATIONS=10
TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT

mkdir -p "$TMPROOT/node_modules"
printf 'x = 1\n' > "$TMPROOT/bench.py"
printf 'const x = 1;\n' > "$TMPROOT/bench.ts"
printf '# Hello\n' > "$TMPROOT/README.md"
printf '{}\n' > "$TMPROOT/package.json"

benchmark() {
  local label="$1" payload="$2"
  local total_ms=0
  for ((i=0; i<ITERATIONS; i++)); do
    local start_ns end_ns elapsed_ms
    start_ns=$(date +%s%N)
    echo "$payload" | bash "$DISPATCH" > /dev/null 2>&1 || true
    end_ns=$(date +%s%N)
    elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
    total_ms=$((total_ms + elapsed_ms))
  done
  local avg_ms=$((total_ms / ITERATIONS))
  printf "%-40s avg=%dms (total=%dms over %d runs)\n" "$label" "$avg_ms" "$total_ms" "$ITERATIONS"
}

echo "=== sdlc-dispatch.sh benchmark ==="

benchmark "vendor path (fast exit)" \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/node_modules/foo.ts","content":"x"}}'

benchmark ".md outside SDLC (no validators)" \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/README.md","content":"# Hello"}}'

benchmark ".json (no validators)" \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/package.json","content":"{}"}}'

benchmark ".py (safety-constraints only)" \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/bench.py","content":"x = 1"}}'

benchmark ".ts (3 validators)" \
  '{"tool_name":"Write","tool_input":{"file_path":"'"$TMPROOT"'/bench.ts","content":"const x = 1;"}}'

echo ""
echo "Target: vendor/md/json < 20ms, .py < 40ms, .ts < 60ms"
echo "Baseline (old 15-hook fan-out on .md): ~203ms"
