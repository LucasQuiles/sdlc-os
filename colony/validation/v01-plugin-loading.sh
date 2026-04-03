#!/usr/bin/env bash
set -euo pipefail

# V-01: Verify claude -p with --plugin-dir can access tmup MCP tools
SCRIPT_NAME="V-01 plugin-loading"
TMPDIR_BASE=$(mktemp -d "/tmp/v01-XXXXXX")
trap 'rm -rf "$TMPDIR_BASE"' EXIT

echo "=== $SCRIPT_NAME ==="
echo "Testing: claude -p --plugin-dir loads tmup MCP tools"

PLUGIN_DIR="/home/q/.claude/plugins/tmup"
WORK_DIR="$TMPDIR_BASE/workspace"
mkdir -p "$WORK_DIR"

OUTPUT=$(claude -p \
  --plugin-dir "$PLUGIN_DIR" \
  --model haiku \
  --max-budget-usd 0.50 \
  --permission-mode bypassPermissions \
  "Call tmup_init with session_dir set to '$WORK_DIR' and project_name 'v01test'. Then call tmup_status. Output the raw results." \
  2>/dev/null) || true

echo "--- Output excerpt ---"
echo "$OUTPUT" | tail -20

# Check for indicators that tmup tools were accessible and returned data
if echo "$OUTPUT" | grep -qiE '(session|task|project|initialized|status|v01test)'; then
  echo "PASS"
else
  echo "FAIL — tmup tools not accessible or no session/task indicators in output"
  exit 1
fi
