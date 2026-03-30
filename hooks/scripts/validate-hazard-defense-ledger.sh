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
