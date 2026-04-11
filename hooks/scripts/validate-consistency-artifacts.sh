#!/bin/bash
# Consistency Artifact Validator (PostToolUse on Write|Edit)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr for schema violations.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]]; then exit 0; fi

# --- Priority 1: Feature Matrix by path ---
if [[ "$FILE_PATH" == *"feature-matrix.md" ]]; then
  CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
  if [[ -z "$CONTENT" ]]; then exit 0; fi

  # Match all data rows in the Findings table (rows starting with | that aren't header or separator)
  # Use fixed-string grep to avoid | being treated as ERE alternation
  TABLE_ROWS=$(echo "$CONTENT" | grep '^|' 2>/dev/null | grep -v '^| ID ' | grep -v '^|---' || true)
  if [[ -z "$TABLE_ROWS" ]]; then exit 0; fi

  VALID_SEVERITIES="CRITICAL|HIGH|MEDIUM|LOW"
  VALID_STATUSES="DISCOVERED|TRIAGED|RESOLVED|DEFERRED|WONT_FIX"

  while IFS= read -r row; do
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

  exit 0
fi

# --- Priority 2: Convention Report by path ---
IS_CONVENTION_REPORT=false
if [[ "$FILE_PATH" == *"convention-report"* ]] || [[ "$FILE_PATH" == *"-convention-report.md" ]]; then
  IS_CONVENTION_REPORT=true
fi

# --- Priority 3: Convention Report by content ---
CONTENT=""
if [[ "$IS_CONVENTION_REPORT" == "false" ]]; then
  CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
  if [[ -n "$CONTENT" ]] && echo "$CONTENT" | grep -q "## Convention Enforcement Report"; then
    IS_CONVENTION_REPORT=true
  fi
fi

if [[ "$IS_CONVENTION_REPORT" == "false" ]]; then exit 0; fi

# --- Convention Report Validation ---
if [[ -z "$CONTENT" ]]; then
  CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
fi
if [[ -z "$CONTENT" ]]; then exit 0; fi

if ! echo "$CONTENT" | grep -q "### Violations Found"; then
  emit_warning "Convention report missing required section: ### Violations Found"
fi

if ! echo "$CONTENT" | grep -q "### Verdict"; then
  emit_warning "Convention report missing required section: ### Verdict"
else
  VERDICT=$(echo "$CONTENT" | sed -n '/^### Verdict/,/^###/p' | grep -oE '(CLEAN|VIOLATIONS|CONVENTION_DRIFT)' | head -1)
  if [[ -z "$VERDICT" ]]; then
    emit_warning "Convention report ### Verdict present but no valid value (expected CLEAN|VIOLATIONS|CONVENTION_DRIFT)"
  fi
fi

exit 0
