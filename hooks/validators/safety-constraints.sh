#!/bin/bash
# validate_safety_constraints — sourceable validator function
# Args: $1 = file_path, $2 = content
# Returns 0 always (WARN/advisory). Emits warnings to stderr.

validate_safety_constraints() {
  local FILE_PATH="$1"
  local CONTENT="$2"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  local WARNINGS=()

  # SC-004: Bare catch/except blocks

  if echo "$CONTENT" | grep -qE 'catch\s*(\([^)]*\))?\s*\{\s*\}'; then
    WARNINGS+=("SC-004: Empty catch block detected — error handler swallows exception silently. Add logging, rethrowing, or meaningful error handling.")
  fi

  if echo "$CONTENT" | grep -qE 'catch\s*(\([^)]*\))?\s*\{\s*//[^\n]*\s*\}' || \
     printf '%s\n' "$CONTENT" | awk '/catch[[:space:]]*(\([^)]*\))?[[:space:]]*\{[[:space:]]*\/\*.*\*\/[[:space:]]*\}/ { found=1; exit } END { exit(found ? 0 : 1) }'; then
    WARNINGS+=("SC-004: Catch block contains only a comment — this swallows the exception. Add logging or rethrowing.")
  fi

  if echo "$CONTENT" | grep -qE '^\s*except(\s+\w+)?:\s*$'; then
    if echo "$CONTENT" | grep -A1 -E '^\s*except(\s+\w+)?:\s*$' | grep -qE '^\s*pass\s*$'; then
      WARNINGS+=("SC-004: Python bare except/pass detected — exception is swallowed silently. Add logging or re-raise.")
    fi
  fi

  # SC-005: Secrets near log statements
  local SECRET_PATTERN='(password|secret|token|api_key|apikey|credential|private_key|auth_key|access_key)\s*='
  local LOG_PATTERN='(log\.|logger\.|console\.log|console\.error|console\.warn|print\(|printf\(|logging\.|System\.out\.print|NSLog\()'

  local HAS_SECRETS HAS_LOGGING
  HAS_SECRETS=$(echo "$CONTENT" | grep -iE "$SECRET_PATTERN" | wc -l || true)
  HAS_LOGGING=$(echo "$CONTENT" | grep -iE "$LOG_PATTERN" | wc -l || true)

  if [[ "$HAS_SECRETS" -gt 0 ]] && [[ "$HAS_LOGGING" -gt 0 ]]; then
    local SECRET_LINES LOG_LINES
    SECRET_LINES=$(echo "$CONTENT" | grep -inE "$SECRET_PATTERN" | cut -d: -f1 || true)
    LOG_LINES=$(echo "$CONTENT" | grep -inE "$LOG_PATTERN" | cut -d: -f1 || true)

    local PROXIMITY_HIT=false
    local sline lline DIFF
    for sline in $SECRET_LINES; do
      for lline in $LOG_LINES; do
        DIFF=$(( sline - lline ))
        if [[ $DIFF -lt 0 ]]; then DIFF=$(( -DIFF )); fi
        if [[ $DIFF -le 10 ]]; then
          PROXIMITY_HIT=true
          break 2
        fi
      done
    done

    if [[ "$PROXIMITY_HIT" == "true" ]]; then
      WARNINGS+=("SC-005: Secret-like variable assignment found within 10 lines of a log statement. Verify secrets are not written to logs. If the value is masked (e.g., '[REDACTED]'), this warning can be ignored.")
    fi
  fi

  if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "[safety-constraints] Advisory warnings for ${FILE_PATH}:" >&2
    local warning
    for warning in "${WARNINGS[@]}"; do
      echo "  WARNING: ${warning}" >&2
    done
    echo "" >&2
    echo "  These are advisory only. Blocking enforcement occurs during L1 sentinel (safety-constraints-guardian)." >&2
    echo "  See references/safety-constraints.md for constraint definitions." >&2
  fi

  return 0
}
