#!/usr/bin/env bash
set -euo pipefail

# V-06: Two separate claude -p processes share a tmup DB
SCRIPT_NAME="V-06 shared-db"
TMPDIR_BASE=$(mktemp -d "/tmp/v06-XXXXXX")
trap 'rm -rf "$TMPDIR_BASE"' EXIT

echo "=== $SCRIPT_NAME ==="
echo "Testing: two claude -p processes share tmup state via same session_dir"

PLUGIN_DIR="/home/q/.claude/plugins/tmup"
WORK_DIR="$TMPDIR_BASE/workspace"
mkdir -p "$WORK_DIR"

# Process 1: init + create 2 tasks
echo "--- Process 1: init + create 2 tasks ---"
OUT1=$(claude -p \
  --plugin-dir "$PLUGIN_DIR" \
  --model haiku \
  --max-budget-usd 0.50 \
  --permission-mode bypassPermissions \
  "Call tmup_init with session_dir '$WORK_DIR' and project_name 'v06test'. Then call tmup_task_create twice: first with title 'task-alpha' description 'first task', then with title 'task-beta' description 'second task'. Then call tmup_status and output the number of tasks." \
  2>/dev/null) || true

echo "$OUT1" | tail -10

# Process 2: init same dir + read status
echo "--- Process 2: read status ---"
OUT2=$(claude -p \
  --plugin-dir "$PLUGIN_DIR" \
  --model haiku \
  --max-budget-usd 0.50 \
  --permission-mode bypassPermissions \
  "Call tmup_init with session_dir '$WORK_DIR' and project_name 'v06test'. Then call tmup_status. How many tasks exist? Output the exact count as a number." \
  2>/dev/null) || true

echo "$OUT2" | tail -10

# Check that process 2 sees 2 tasks
if echo "$OUT2" | grep -qE '(2|two)'; then
  echo "PASS"
else
  echo "FAIL — process 2 did not see 2 tasks"
  exit 1
fi
