#!/bin/bash
# validate_consistency — sourceable validator function
# Args: $1 = file_path, $2 = content
# Returns 0 always (WARN/advisory). Emits HOOK_WARNING to stderr.
# Requires common.sh to be already sourced (for emit_warning).

validate_consistency() {
  local FILE_PATH="$1"
  local CONTENT="$2"

  if [[ -z "$FILE_PATH" ]]; then
    return 0
  fi

  # --- Priority 1: Feature Matrix by path ---
  if [[ "$FILE_PATH" == *"feature-matrix.md" ]]; then
    if [[ -z "$CONTENT" ]]; then
      return 0
    fi

    local TABLE_ROWS
    TABLE_ROWS=$(echo "$CONTENT" | grep '^|' 2>/dev/null | grep -v '^| ID ' | grep -v '^|---' || true)
    if [[ -z "$TABLE_ROWS" ]]; then
      return 0
    fi

    local VALID_SEVERITIES="CRITICAL|HIGH|MEDIUM|LOW"
    local VALID_STATUSES="DISCOVERED|TRIAGED|RESOLVED|DEFERRED|WONT_FIX"

    while IFS= read -r row; do
      local ID SEVERITY STATUS
      ID=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
      SEVERITY=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $8); print $8}')
      STATUS=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $9); print $9}')

      if [[ -n "$ID" ]] && [[ ! "$ID" =~ ^FF-[0-9]+$ ]]; then
        emit_warning "Feature matrix row has invalid ID format: '${ID}' (expected FF-NNN)"
        continue
      fi
      if [[ -n "$SEVERITY" ]] && [[ ! "$SEVERITY" =~ ^($VALID_SEVERITIES)$ ]]; then
        emit_warning "Feature matrix row ${ID} has invalid severity: '${SEVERITY}'"
      fi
      if [[ -n "$STATUS" ]] && [[ ! "$STATUS" =~ ^($VALID_STATUSES)$ ]]; then
        emit_warning "Feature matrix row ${ID} has invalid status: '${STATUS}'"
      fi
    done <<< "$TABLE_ROWS"

    return 0
  fi

  # --- Priority 2: Convention Report by path ---
  local IS_CONVENTION_REPORT=false
  if [[ "$FILE_PATH" == *"convention-report"* ]] || [[ "$FILE_PATH" == *"-convention-report.md" ]]; then
    IS_CONVENTION_REPORT=true
  fi

  # --- Priority 3: Convention Report by content ---
  if [[ "$IS_CONVENTION_REPORT" == "false" ]]; then
    if [[ -n "$CONTENT" ]] && echo "$CONTENT" | grep -q "## Convention Enforcement Report"; then
      IS_CONVENTION_REPORT=true
    fi
  fi

  if [[ "$IS_CONVENTION_REPORT" == "false" ]]; then
    return 0
  fi

  # --- Convention Report Validation ---
  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  if ! echo "$CONTENT" | grep -q "### Violations Found"; then
    emit_warning "Convention report missing required section: ### Violations Found"
  fi

  if ! echo "$CONTENT" | grep -q "### Verdict"; then
    emit_warning "Convention report missing required section: ### Verdict"
  else
    local VERDICT
    VERDICT=$(echo "$CONTENT" | sed -n '/^### Verdict/,/^###/p' | grep -oE '(CLEAN|VIOLATIONS|CONVENTION_DRIFT)' | head -1)
    if [[ -z "$VERDICT" ]]; then
      emit_warning "Convention report ### Verdict present but no valid value (expected CLEAN|VIOLATIONS|CONVENTION_DRIFT)"
    fi
  fi

  return 0
}
