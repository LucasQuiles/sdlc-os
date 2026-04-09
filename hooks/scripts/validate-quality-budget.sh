#!/bin/bash
# validate-quality-budget.sh — PostToolUse hook: validates quality-budget.yaml on Write/Edit
set -euo pipefail

source "$(dirname "$0")/../lib/common.sh"

input=$(read_hook_stdin) || exit 0
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

# Validate: must parse as valid YAML
# Try python3+PyYAML first; if unavailable, fall back to structural grep checks.
_has_pyyaml=false
if command -v python3 &>/dev/null && python3 -c "import yaml" 2>/dev/null; then
  _has_pyyaml=true
fi

if [[ "$_has_pyyaml" == "true" ]]; then
  if ! python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"quality-budget.yaml is not valid YAML"}' >&2
    exit 2
  fi
else
  # Fallback: check for basic YAML structure (colon-separated key-value lines)
  # This catches obvious corruption but not all parse errors
  if ! grep -qE '^[a-z_]+:' "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"quality-budget.yaml has no recognizable YAML keys"}' >&2
    exit 2
  fi
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
