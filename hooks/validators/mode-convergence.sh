#!/bin/bash
# validate_mode_convergence — sourceable validator function
# Args: $1 = file_path (absolute path to mode-convergence-summary.yaml on disk)
# Returns 0 for pass, 2 for block.

validate_mode_convergence() {
  local file_path="$1"

  if [[ ! -f "$file_path" ]]; then
    echo "mode-convergence-summary.yaml written but file not found at $file_path" >&2
    return 2
  fi

  # Validate: YAML parse
  local _has_pyyaml=false
  if command -v python3 &>/dev/null && python3 -c "import yaml" 2>/dev/null; then
    _has_pyyaml=true
  fi

  if [[ "$_has_pyyaml" == "true" ]]; then
    if ! python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$file_path" 2>/dev/null; then
      echo '{"decision":"deny","reason":"mode-convergence-summary.yaml is not valid YAML"}' >&2
      return 2
    fi
  else
    if ! grep -qE '^[a-z_]+:' "$file_path" 2>/dev/null; then
      echo '{"decision":"deny","reason":"mode-convergence-summary.yaml has no recognizable YAML keys"}' >&2
      return 2
    fi
  fi

  # Validate: required top-level fields
  local field
  for field in "schema_version:" "task_id:" "artifact_status:"; do
    if ! grep -q "^${field}" "$file_path"; then
      echo "{\"decision\":\"deny\",\"reason\":\"mode-convergence-summary.yaml missing required field: $field\"}" >&2
      return 2
    fi
  done

  # Validate: artifact_status enum
  local STATUS
  STATUS=$(grep "^artifact_status:" "$file_path" | sed 's/artifact_status: *//' | sed 's/^["'"'"']\(.*\)["'"'"']$/\1/')
  case "$STATUS" in
    partial|final) ;;
    *) echo '{"decision":"deny","reason":"artifact_status must be partial or final"}' >&2; return 2 ;;
  esac

  # Validate: required sections
  local section
  for section in "execution_mode:" "summary:"; do
    if ! grep -q "^${section}" "$file_path"; then
      echo "{\"decision\":\"deny\",\"reason\":\"mode-convergence-summary.yaml missing required section: $section\"}" >&2
      return 2
    fi
  done

  return 0
}
