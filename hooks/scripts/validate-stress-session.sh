#!/bin/bash
# validate-stress-session.sh — PostToolUse hook: validates stress-session.yaml on Write/Edit
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

input=$(read_hook_stdin) || exit 0
file_path=$(read_hook_file_path "$input")

# Only trigger on stress-session.yaml writes
if [[ "$file_path" != *"stress-session.yaml" ]]; then
  exit 0
fi

if [[ ! -f "$file_path" ]]; then
  echo "stress-session.yaml written but file not found at $file_path" >&2
  exit 2
fi

# Validate: YAML parse
_has_pyyaml=false
if command -v python3 &>/dev/null && python3 -c "import yaml" 2>/dev/null; then
  _has_pyyaml=true
fi

if [[ "$_has_pyyaml" == "true" ]]; then
  if ! python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"stress-session.yaml is not valid YAML"}' >&2
    exit 2
  fi
else
  if ! grep -qE '^[a-z_]+:' "$file_path" 2>/dev/null; then
    echo '{"decision":"deny","reason":"stress-session.yaml has no recognizable YAML keys"}' >&2
    exit 2
  fi
fi

# Validate: required top-level fields
for field in "schema_version:" "task_id:" "artifact_status:" "sampling_reason:"; do
  if ! grep -q "^${field}" "$file_path"; then
    echo "{\"decision\":\"deny\",\"reason\":\"stress-session.yaml missing required field: $field\"}" >&2
    exit 2
  fi
done

# Validate: artifact_status enum
STATUS=$(grep "^artifact_status:" "$file_path" | sed 's/artifact_status: *//')
case "$STATUS" in
  planned|active|final) ;;
  *) echo '{"decision":"deny","reason":"artifact_status must be planned, active, or final"}' >&2; exit 2 ;;
esac

# Validate: sampling_reason enum
REASON=$(grep "^sampling_reason:" "$file_path" | sed 's/sampling_reason: *//')
case "$REASON" in
  consequence_sensitive|budget_warning|random_sample|anti_turkey|budget_depleted|hormetic|manual) ;;
  *) echo '{"decision":"deny","reason":"sampling_reason must be consequence_sensitive, budget_warning, random_sample, anti_turkey, budget_depleted, hormetic, or manual"}' >&2; exit 2 ;;
esac

# Validate: required sections
for section in "selection:" "stressors_applied:" "harvest:" "subtraction_log:" "summary:"; do
  if ! grep -q "^${section}" "$file_path"; then
    echo "{\"decision\":\"deny\",\"reason\":\"stress-session.yaml missing required section: $section\"}" >&2
    exit 2
  fi
done

exit 0
