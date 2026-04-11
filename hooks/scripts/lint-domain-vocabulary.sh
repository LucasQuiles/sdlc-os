#!/bin/bash
# Domain Vocabulary Linter
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*
# Catches non-canonical domain names before they persist
# Exit 0 = clean, Exit 2 = drift detected (feeds correction to Claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

load_hook_input_or_exit INPUT || exit 0
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only lint SDLC artifacts
if [[ -z "$FILE_PATH" ]] || [[ ! "$FILE_PATH" =~ docs/sdlc/active/ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

ERRORS=""

# Check for non-canonical AQS domain names
# Canonical: functionality, security, usability, resilience
# Common drift: correctness, robustness, performance, reliability, accessibility

for BAD_DOMAIN in "correctness" "robustness" "performance" "reliability"; do
  # Only flag in domain-context lines (not general prose)
  if echo "$CONTENT" | grep -iE "(domain|domains tested|domains activated).*\b${BAD_DOMAIN}\b" > /dev/null 2>&1; then
    ERRORS="${ERRORS}Non-canonical domain name '${BAD_DOMAIN}' detected. Canonical AQS domains: functionality | security | usability | resilience\n"
  fi
done

# Check for non-canonical confidence labels
for BAD_LABEL in "Probable" "Certain" "Uncertain" "Possible" "Confirmed"; do
  if echo "$CONTENT" | grep -E "\*\*Confidence:\*\*.*\b${BAD_LABEL}\b" > /dev/null 2>&1; then
    ERRORS="${ERRORS}Non-canonical confidence label '${BAD_LABEL}'. Use: Verified | Likely | Assumed | Unknown\n"
  fi
done

# Check for non-canonical verdict labels in AQS reports
if echo "$CONTENT" | grep -q "Adversarial Quality Report\|AQS Report"; then
  for BAD_VERDICT in "PASSED" "FAILED" "APPROVED" "REJECTED" "CLEAN" "DIRTY"; do
    if echo "$CONTENT" | grep -E "\b${BAD_VERDICT}\b" > /dev/null 2>&1; then
      ERRORS="${ERRORS}Non-canonical AQS report verdict '${BAD_VERDICT}'. Use: HARDENED | PARTIALLY_HARDENED | DEFERRED\n"
    fi
  done
fi

if [[ -n "$ERRORS" ]]; then
  echo -e "Domain vocabulary lint failed for $(basename "$FILE_PATH"):\n${ERRORS}\nFix vocabulary to use canonical terms." >&2
  exit 2
fi

exit 0
