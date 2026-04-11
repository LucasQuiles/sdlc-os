#!/bin/bash
# AQS Artifact Schema Validator
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/adversarial/*
# Exit 0 = valid, Exit 2 = invalid (blocks with feedback to Claude)
#
# Validates per-block (each ## Finding / ## Response independently),
# not aggregate counts. Portable — no grep -P.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

if ! command -v jq &>/dev/null; then
  echo '{"error": "jq is required but not found"}' >&2
  exit 2
fi

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only validate AQS artifacts
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Match AQS artifact paths
if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/adversarial/ ]] && [[ ! "$FILE_PATH" =~ -aqs\.md$ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
if [[ -z "$CONTENT" ]]; then
  exit 0
fi

ERRORS=""

# Helper: split content into blocks by ## header, validate each independently
validate_finding_block() {
  local block="$1"
  local block_num="$2"
  local block_id="$3"

  for field in "Domain:" "Severity:" "Claim:" "Minimal reproduction:" "Impact:" "Evidence:" "Confidence:"; do
    if ! echo "$block" | grep -q "\*\*${field}\*\*"; then
      ERRORS="${ERRORS}Finding #${block_num} (${block_id}) missing required field: ${field}\n"
    fi
  done

  # Validate domain vocabulary
  local domain_line
  domain_line=$(echo "$block" | grep "\*\*Domain:\*\*" || true)
  if [[ -n "$domain_line" ]]; then
    if echo "$domain_line" | grep -qiE '\b(correctness|robustness|performance)\b'; then
      ERRORS="${ERRORS}Finding #${block_num}: non-canonical domain. Use: functionality | security | usability | resilience\n"
    fi
  fi

  # Validate severity
  local severity_line
  severity_line=$(echo "$block" | grep "\*\*Severity:\*\*" || true)
  if [[ -n "$severity_line" ]]; then
    if ! echo "$severity_line" | grep -qE '(critical|high|medium|low)'; then
      ERRORS="${ERRORS}Finding #${block_num}: invalid severity. Use: critical | high | medium | low\n"
    fi
  fi

  # Validate confidence
  local confidence_line
  confidence_line=$(echo "$block" | grep "\*\*Confidence:\*\*" || true)
  if [[ -n "$confidence_line" ]]; then
    if ! echo "$confidence_line" | grep -qE '(Verified|Likely|Assumed|Unknown)'; then
      ERRORS="${ERRORS}Finding #${block_num}: invalid confidence. Use: Verified | Likely | Assumed | Unknown\n"
    fi
  fi
}

validate_response_block() {
  local block="$1"
  local block_num="$2"
  local block_id="$3"

  # Check Action field
  if ! echo "$block" | grep -q "\*\*Action:\*\*"; then
    ERRORS="${ERRORS}Response #${block_num} (${block_id}) missing required field: Action\n"
    return
  fi

  # If accepted, check defensive iteration fields
  if echo "$block" | grep -q "\*\*Action:\*\* accepted"; then
    local has_fix has_pre has_post has_regression
    has_fix=$(echo "$block" | grep -c "\*\*Fix:\*\*" || true)
    has_pre=$(echo "$block" | grep -cE "(Pre-fix reproduction|Gap confirmed|Problem confirmed|Pre-fix repro)" || true)
    has_post=$(echo "$block" | grep -cE "(Post-fix reproduction|Fix verified|Improvement verified|Post-fix repro)" || true)
    has_regression=$(echo "$block" | grep -cE "(Regression check|Adjacency check)" || true)

    [[ "$has_fix" -eq 0 ]] && ERRORS="${ERRORS}Response #${block_num} (${block_id}) accepted but missing: Fix\n"
    [[ "$has_pre" -eq 0 ]] && ERRORS="${ERRORS}Response #${block_num} (${block_id}) accepted but missing: pre-fix reproduction\n"
    [[ "$has_post" -eq 0 ]] && ERRORS="${ERRORS}Response #${block_num} (${block_id}) accepted but missing: post-fix verification\n"
    [[ "$has_regression" -eq 0 ]] && ERRORS="${ERRORS}Response #${block_num} (${block_id}) accepted but missing: regression/adjacency check\n"
  fi

  # If rebutted, check evidence
  if echo "$block" | grep -q "\*\*Action:\*\* rebutted"; then
    if ! echo "$block" | grep -q "\*\*Evidence:\*\*\|\*\*Reasoning:\*\*"; then
      ERRORS="${ERRORS}Response #${block_num} (${block_id}) rebutted but missing: Reasoning or Evidence\n"
    fi
  fi

  # If disputed, check contested claim and proposed test
  if echo "$block" | grep -q "\*\*Action:\*\* disputed"; then
    if ! echo "$block" | grep -q "\*\*Contested claim:\*\*"; then
      ERRORS="${ERRORS}Response #${block_num} (${block_id}) disputed but missing: Contested claim\n"
    fi
    if ! echo "$block" | grep -q "\*\*Proposed test:\*\*"; then
      ERRORS="${ERRORS}Response #${block_num} (${block_id}) disputed but missing: Proposed test\n"
    fi
  fi
}

validate_verdict_block() {
  local block="$1"
  local block_num="$2"
  local block_id="$3"

  for field in "Decision:" "Red team claim:" "Blue team position:" "Test designed:" "Test result:" "Reasoning:" "Dispute contract locked:" "Red team pre-commitment:" "Blue team pre-commitment:" "Residual uncertainty:"; do
    if ! echo "$block" | grep -q "\*\*${field}\*\*"; then
      ERRORS="${ERRORS}Verdict #${block_num} (${block_id}) missing required field: ${field}\n"
    fi
  done

  # Validate decision vocabulary
  local decision_line
  decision_line=$(echo "$block" | grep "\*\*Decision:\*\*" || true)
  if [[ -n "$decision_line" ]]; then
    if ! echo "$decision_line" | grep -qE '(SUSTAINED|DISMISSED|MODIFIED)'; then
      ERRORS="${ERRORS}Verdict #${block_num}: invalid decision. Use: SUSTAINED | DISMISSED | MODIFIED\n"
    fi
  fi
}

# Generic block splitter — calls a validation function per block
process_blocks() {
  local content="$1"
  local header_pattern="$2"
  local validator="$3"

  local block_num=0
  local in_block=false
  local current_block=""
  local block_id=""

  while IFS= read -r line; do
    if echo "$line" | grep -q "^## ${header_pattern}"; then
      if [[ "$in_block" == "true" ]] && [[ -n "$current_block" ]]; then
        block_num=$((block_num + 1))
        "$validator" "$current_block" "$block_num" "$block_id"
      fi
      in_block=true
      current_block="$line"
      block_id=$(echo "$line" | sed "s/^## ${header_pattern}[[:space:]]*//" | head -1)
    elif [[ "$in_block" == "true" ]]; then
      current_block="${current_block}
${line}"
    fi
  done <<< "$content"

  # Process last block
  if [[ "$in_block" == "true" ]] && [[ -n "$current_block" ]]; then
    block_num=$((block_num + 1))
    "$validator" "$current_block" "$block_num" "$block_id"
  fi
}

# Detect artifact type and validate
if [[ "$FILE_PATH" =~ findings- ]]; then
  process_blocks "$CONTENT" "Finding:" "validate_finding_block"

elif [[ "$FILE_PATH" =~ responses- ]]; then
  process_blocks "$CONTENT" "Response:" "validate_response_block"

elif [[ "$FILE_PATH" =~ verdicts- ]]; then
  process_blocks "$CONTENT" "Verdict:" "validate_verdict_block"

elif [[ "$FILE_PATH" =~ -aqs\.md$ ]]; then
  # AQS REPORT — validate required sections
  if echo "$CONTENT" | grep -q "Adversarial Quality Report"; then
    for SECTION in "Engagement Summary" "Findings" "Hardening Changes" "Belief Update" "Residual Risk" "Verdict"; do
      if ! echo "$CONTENT" | grep -q "### ${SECTION}\|## ${SECTION}"; then
        ERRORS="${ERRORS}AQS report missing required section: ${SECTION}\n"
      fi
    done

    if echo "$CONTENT" | grep -q "### Verdict\|## Verdict"; then
      if ! echo "$CONTENT" | grep -qE 'HARDENED|PARTIALLY_HARDENED|DEFERRED'; then
        ERRORS="${ERRORS}AQS report verdict must be: HARDENED | PARTIALLY_HARDENED | DEFERRED\n"
      fi
    fi
  fi

elif [[ "$FILE_PATH" =~ recon- ]]; then
  PROBE_COUNT=$(echo "$CONTENT" | grep -cE "(SIGNAL|NO_SIGNAL)" || true)
  if [[ "$PROBE_COUNT" -eq 0 ]] && echo "$CONTENT" | grep -qi "recon"; then
    ERRORS="${ERRORS}Recon results must contain SIGNAL or NO_SIGNAL responses\n"
  fi
fi

# Output result
if [[ -n "$ERRORS" ]]; then
  printf "AQS Schema Validation Failed for %s:\n%b\nFix these issues and retry the write.\n" "$(basename "$FILE_PATH")" "$ERRORS" >&2
  exit 2
else
  exit 0
fi
