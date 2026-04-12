#!/bin/bash
# validate_eslint_disable — sourceable validator function
# Args: $1 = file_path, $2 = content
# Returns 0 for pass, 2 for block.
# Requires common.sh to be already sourced (for get_repo_root, is_vendor_path).

validate_eslint_disable() {
  local FILE_PATH="$1"
  local CONTENT="$2"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  # Find all eslint-disable lines
  local DISABLE_LINES
  DISABLE_LINES=$(echo "$CONTENT" | grep -n "eslint-disable" 2>/dev/null || true)

  if [[ -z "$DISABLE_LINES" ]]; then
    return 0
  fi

  # Load allowlist if it exists
  local ALLOWLIST_FILE=""
  local REPO_ROOT
  REPO_ROOT=$(get_repo_root)
  if [[ -n "$REPO_ROOT" ]]; then
    local ACTIVE_DIR="$REPO_ROOT/docs/sdlc/active"
    if [[ -n "${SDLC_TASK_ID:-}" ]]; then
      ALLOWLIST_FILE="$ACTIVE_DIR/$SDLC_TASK_ID/suppression-allowlist.md"
      [[ -f "$ALLOWLIST_FILE" ]] || ALLOWLIST_FILE=""
    else
      local CANDIDATES CANDIDATE_COUNT
      CANDIDATES=$(find "$ACTIVE_DIR" -name "suppression-allowlist.md" -type f 2>/dev/null || true)
      CANDIDATE_COUNT=$(echo "$CANDIDATES" | grep -c . 2>/dev/null || echo 0)
      if [[ "$CANDIDATE_COUNT" -eq 1 ]]; then
        ALLOWLIST_FILE="$CANDIDATES"
      fi
    fi
  fi

  local ERRORS=""

  while IFS= read -r line; do
    local LINE_NUM LINE_CONTENT
    LINE_NUM=$(echo "$line" | cut -d: -f1)
    LINE_CONTENT=$(echo "$line" | cut -d: -f2-)

    # Skip eslint-enable lines
    if echo "$LINE_CONTENT" | grep -q "eslint-enable"; then
      continue
    fi

    # Score 2-3: structured format with tracking/expiry
    if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,};\s*(tracked in |expires )"; then
      continue
    fi

    # Score 1: has -- separator and reason but missing tracking/expiry
    if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,}"; then
      continue
    fi

    # Bare suppression (score 0). Check allowlist.
    if [[ -n "$ALLOWLIST_FILE" ]] && [[ -f "$ALLOWLIST_FILE" ]]; then
      local NORMALIZED CONTEXT_START CONTEXT_END CONTEXT_LINES CONTEXT_HASH FINGERPRINT
      NORMALIZED=$(echo "$LINE_CONTENT" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
      CONTEXT_START=$((LINE_NUM > 1 ? LINE_NUM - 1 : 1))
      CONTEXT_END=$((LINE_NUM + 1))
      CONTEXT_LINES=$(echo "$CONTENT" | sed -n "${CONTEXT_START},${CONTEXT_END}p" 2>/dev/null || true)
      CONTEXT_HASH=$(echo "$CONTEXT_LINES" | shasum -a 256 | cut -d' ' -f1)
      FINGERPRINT=$(echo "${FILE_PATH}${NORMALIZED}${CONTEXT_HASH}" | shasum -a 256 | cut -d' ' -f1)

      if grep -q "$FINGERPRINT" "$ALLOWLIST_FILE" 2>/dev/null; then
        continue
      fi
    fi

    # Bare suppression not in allowlist — BLOCK
    ERRORS="${ERRORS}Line ${LINE_NUM}: Bare eslint-disable without justification. Required format:\n"
    ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; tracked in <DEBT-ID>\n"
    ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; expires <YYYY-MM-DD>\n\n"

  done <<< "$DISABLE_LINES"

  if [[ -n "$ERRORS" ]]; then
    echo "HOOK_ERROR: eslint-disable justification required" >&2
    echo -e "$ERRORS" >&2
    return 2
  fi

  return 0
}
