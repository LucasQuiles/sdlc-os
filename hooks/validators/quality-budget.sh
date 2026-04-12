#!/bin/bash
# validate_quality_budget — sourceable validator function
# Args: $1 = file_path (absolute path to quality-budget.yaml on disk)
# Returns 0 for pass, 2 for block.

validate_quality_budget() {
  local file_path="$1"

  if [[ ! -f "$file_path" ]]; then
    echo "quality-budget.yaml written but file not found at $file_path" >&2
    return 2
  fi

  # Validate: must parse as valid YAML
  local _has_pyyaml=false
  if command -v python3 &>/dev/null && python3 -c "import yaml" 2>/dev/null; then
    _has_pyyaml=true
  fi

  if [[ "$_has_pyyaml" == "true" ]]; then
    if ! python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$file_path" 2>/dev/null; then
      echo '{"decision":"deny","reason":"quality-budget.yaml is not valid YAML"}' >&2
      return 2
    fi
  else
    if ! grep -qE '^[a-z_]+:' "$file_path" 2>/dev/null; then
      echo '{"decision":"deny","reason":"quality-budget.yaml has no recognizable YAML keys"}' >&2
      return 2
    fi
  fi

  # Validate: must contain schema_version
  if ! grep -q "^schema_version:" "$file_path"; then
    echo '{"decision":"deny","reason":"quality-budget.yaml missing schema_version field"}' >&2
    return 2
  fi

  # Validate: must contain task_id
  if ! grep -q "^task_id:" "$file_path"; then
    echo '{"decision":"deny","reason":"quality-budget.yaml missing task_id field"}' >&2
    return 2
  fi

  # Validate: must contain artifact_status
  if ! grep -q "^artifact_status:" "$file_path"; then
    echo '{"decision":"deny","reason":"quality-budget.yaml missing artifact_status field"}' >&2
    return 2
  fi

  # Validate: artifact_status must be valid
  local STATUS
  STATUS=$(grep "^artifact_status:" "$file_path" | sed 's/artifact_status: *//')
  case "$STATUS" in
    partial|ready|final) ;;
    *) echo '{"decision":"deny","reason":"artifact_status must be partial, ready, or final"}' >&2; return 2 ;;
  esac

  # Validate: required sections exist
  local section
  for section in "cynefin_mix:" "beads:" "corrections:" "metrics:" "timing:" "escapes:"; do
    if ! grep -q "^${section}" "$file_path"; then
      echo "{\"decision\":\"deny\",\"reason\":\"quality-budget.yaml missing required section: $section\"}" >&2
      return 2
    fi
  done

  return 0
}
