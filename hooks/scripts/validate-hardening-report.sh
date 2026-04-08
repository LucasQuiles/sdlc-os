#!/bin/bash
# Hardening Report Schema Validator
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/beads/*/hardening-report.md
# Validates that hardening reports contain all required sections
# Exit 0 = valid, Exit 2 = invalid (blocks with feedback to Claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

INPUT=$(timeout 2s cat || true)
if [ -z "$INPUT" ]; then exit 0; fi
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only validate hardening report files
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ hardening-report\.md$ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Required sections in hardening report
MISSING=()

check_section() {
  local section="$1"
  if ! echo "$CONTENT" | grep -q "^## ${section}"; then
    MISSING+=("$section")
  fi
}

check_section "Observability Profile"
check_section "Premortem Analysis"
check_section "Pre-Clean Results"
check_section "Instrumentation Summary"
check_section "Edge Case Tests Generated"
check_section "Red Team Findings"
check_section "Post-Clean Results"
check_section "WYSIATI Coverage Sweep"
check_section "Evidence Ledger"
check_section "Verdict"

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "Hardening report is missing required sections:" >&2
  for section in "${MISSING[@]}"; do
    echo "  - ## ${section}" >&2
  done
  echo "" >&2
  echo "All hardening reports must include these sections per the Phase 4.5 spec." >&2
  echo "See docs/specs/2026-03-26-reliability-hardening-phase-design.md for the required format." >&2
  exit 2
fi

# Check evidence ledger has content (not just a header)
LEDGER_LINES=$(echo "$CONTENT" | sed -n '/^## Evidence Ledger/,/^## /p' | wc -l)
if [[ "$LEDGER_LINES" -lt 3 ]]; then
  echo "Evidence Ledger section is empty. Every hardening report must include at least one hypothesis with confidence transitions." >&2
  exit 2
fi

# Check WYSIATI sweep has content
WYSIATI_LINES=$(echo "$CONTENT" | sed -n '/^## WYSIATI Coverage Sweep/,/^## /p' | wc -l)
if [[ "$WYSIATI_LINES" -lt 3 ]]; then
  echo "WYSIATI Coverage Sweep section is empty. Must include file coverage counts and any gaps flagged as Unknown." >&2
  exit 2
fi

# Check verdict section has status
if ! echo "$CONTENT" | grep -q "reliability-proven\|escalated"; then
  echo "Verdict section must include a status of 'reliability-proven' or 'escalated'." >&2
  exit 2
fi

exit 0
