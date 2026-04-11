#!/bin/bash
# Runner Output Validator (SubagentStop)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr.
# Only fires for agents named "runner-*".
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

load_hook_input_or_exit INPUT || exit 0
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .subagent_name // empty' 2>/dev/null) || {
  emit_warning "validate-runner-output: failed to parse hook input — skipping"
  exit 0
}

if [[ -z "$AGENT_NAME" ]] || [[ ! "$AGENT_NAME" == runner-* ]]; then exit 0; fi

OUTPUT_TEXT=$(echo "$INPUT" | jq -r '.output // .result // empty' 2>/dev/null)
if [[ -z "$OUTPUT_TEXT" ]]; then
  emit_warning "SubagentStop payload for ${AGENT_NAME} missing output text — skipping"
  exit 0
fi

# --- Layer 1: Structural Checks ---
HAS_SUMMARY=false
for header in "## Implementation Summary" "## Investigation Summary" "## Objective" "## Design Summary" "## Problem Statement"; do
  if echo "$OUTPUT_TEXT" | grep -qF "$header"; then
    HAS_SUMMARY=true
    break
  fi
done

if [[ "$HAS_SUMMARY" == "false" ]]; then
  emit_warning "Runner ${AGENT_NAME} output missing required section — no Implementation/Investigation/Design Summary found"
fi

HAS_STATUS=false
if echo "$OUTPUT_TEXT" | grep -qE '(^## Status|^\*\*Status:\*\*)'; then
  STATUS_VALUE=$(echo "$OUTPUT_TEXT" | grep -oE '(DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED)' | head -1)
  if [[ -n "$STATUS_VALUE" ]]; then
    HAS_STATUS=true
  fi
fi

if [[ "$HAS_STATUS" == "false" ]]; then
  emit_warning "Runner ${AGENT_NAME} output missing Status (expected DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED)"
fi

# --- Layer 2: Convention Signals ---
if echo "$OUTPUT_TEXT" | grep -q 'Math\.random()'; then
  if ! echo "$OUTPUT_TEXT" | grep -B2 'Math\.random()' | grep -qi 'test\|spec\|mock'; then
    emit_warning "Convention signal in ${AGENT_NAME} — Math.random() found, canonical source is lib/utils/id-generator.ts"
  fi
fi

if echo "$OUTPUT_TEXT" | grep -q 'throw new Error('; then
  if echo "$OUTPUT_TEXT" | grep -B5 'throw new Error(' | grep -qi 'storage'; then
    emit_warning "Convention signal in ${AGENT_NAME} — raw Error throw in storage context, canonical source is StorageError"
  fi
fi

if echo "$OUTPUT_TEXT" | grep -qE "(alert\(|from 'sonner'|from \"sonner\")"; then
  emit_warning "Convention signal in ${AGENT_NAME} — raw notification pattern, canonical source is safeToast"
fi

# --- Layer 3: Reuse Compliance ---
if echo "$OUTPUT_TEXT" | grep -qF "## Reuse Report"; then
  CREATED_NEW_SECTION=$(echo "$OUTPUT_TEXT" | sed -n '/### Created New/,/^###/p')
  if [[ -n "$CREATED_NEW_SECTION" ]]; then
    EMPTY_ITEMS=$(echo "$CREATED_NEW_SECTION" | grep -cE '^-[[:space:]]*$' 2>/dev/null || echo "0")
    if [[ "$EMPTY_ITEMS" -gt 0 ]]; then
      emit_warning "Reuse compliance in ${AGENT_NAME} — ${EMPTY_ITEMS} Created New items lack justification"
    fi
  fi

  if echo "$OUTPUT_TEXT" | grep -qF "## Existing Solutions"; then
    EXACT_MATCHES=$(echo "$OUTPUT_TEXT" | sed -n '/## Existing Solutions/,/^##/p' | grep "EXACT_MATCH" || true)
    if [[ -n "$EXACT_MATCHES" ]] && [[ -n "$CREATED_NEW_SECTION" ]]; then
      while IFS= read -r match_line; do
        FUNC_NAME=$(echo "$match_line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
        if [[ -n "$FUNC_NAME" ]] && echo "$CREATED_NEW_SECTION" | grep -qF "$FUNC_NAME"; then
          LOCATION=$(echo "$match_line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')
          emit_warning "Reuse compliance in ${AGENT_NAME} — runner created ${FUNC_NAME} but reuse-scout found EXACT_MATCH at ${LOCATION}"
        fi
      done <<< "$EXACT_MATCHES"
    fi
  fi
fi

exit 0
