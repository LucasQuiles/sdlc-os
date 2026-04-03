#!/usr/bin/env bash
set -euo pipefail

# V-02: Worker round-trip — session 1 creates task, session 2 claims + completes
SCRIPT_NAME="V-02 worker-roundtrip"
TMPDIR_BASE=$(mktemp -d "/tmp/v02-XXXXXX")
trap 'rm -rf "$TMPDIR_BASE"' EXIT

echo "=== $SCRIPT_NAME ==="
echo "Testing: two separate claude -p sessions can coordinate via tmup"

PLUGIN_DIR="/home/q/.claude/plugins/tmup"
WORK_DIR="$TMPDIR_BASE/workspace"
mkdir -p "$WORK_DIR"

# Session 1: init + create a task
echo "--- Session 1: init + create task ---"
OUT1=$(claude -p \
  --plugin-dir "$PLUGIN_DIR" \
  --model haiku \
  --max-budget-usd 0.50 \
  --permission-mode bypassPermissions \
  "Call tmup_init with session_dir '$WORK_DIR' and project_name 'v02test'. Then call tmup_task_create with title 'roundtrip-test-task' and description 'validate worker roundtrip'. Output the task ID." \
  2>/dev/null) || true

echo "$OUT1" | tail -10

# Session 2: claim + complete the task
echo "--- Session 2: claim + complete task ---"
OUT2=$(claude -p \
  --plugin-dir "$PLUGIN_DIR" \
  --model haiku \
  --max-budget-usd 0.50 \
  --permission-mode bypassPermissions \
  "Call tmup_init with session_dir '$WORK_DIR' and project_name 'v02test'. Then call tmup_status to see tasks. Find the task titled 'roundtrip-test-task', claim it with tmup_claim, then complete it with tmup_complete. Output the final status." \
  2>/dev/null) || true

echo "$OUT2" | tail -10

# Verify round-trip: look for completion indicators
if echo "$OUT2" | grep -qiE '(complete|done|finished|success)'; then
  echo "PASS"
else
  echo "FAIL — round-trip not confirmed"
  exit 1
fi
