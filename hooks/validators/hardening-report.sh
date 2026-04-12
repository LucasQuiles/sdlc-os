#!/bin/bash
# validate_hardening_report — sourceable validator function
# Args: $1 = content (full file content as string)
# Returns 0 for pass, 2 for block.

validate_hardening_report() {
  local CONTENT="$1"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  # Required sections in hardening report
  local MISSING=()

  local section
  for section in \
    "Observability Profile" \
    "Premortem Analysis" \
    "Pre-Clean Results" \
    "Instrumentation Summary" \
    "Edge Case Tests Generated" \
    "Red Team Findings" \
    "Post-Clean Results" \
    "WYSIATI Coverage Sweep" \
    "Evidence Ledger" \
    "Verdict"; do
    if ! echo "$CONTENT" | grep -q "^## ${section}"; then
      MISSING+=("$section")
    fi
  done

  if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Hardening report is missing required sections:" >&2
    for section in "${MISSING[@]}"; do
      echo "  - ## ${section}" >&2
    done
    echo "" >&2
    echo "All hardening reports must include these sections per the Phase 4.5 spec." >&2
    echo "See docs/specs/2026-03-26-reliability-hardening-phase-design.md for the required format." >&2
    return 2
  fi

  # Check evidence ledger has content (not just a header)
  local LEDGER_LINES
  LEDGER_LINES=$(echo "$CONTENT" | sed -n '/^## Evidence Ledger/,/^## /p' | wc -l)
  if [[ "$LEDGER_LINES" -lt 3 ]]; then
    echo "Evidence Ledger section is empty. Every hardening report must include at least one hypothesis with confidence transitions." >&2
    return 2
  fi

  # Check WYSIATI sweep has content
  local WYSIATI_LINES
  WYSIATI_LINES=$(echo "$CONTENT" | sed -n '/^## WYSIATI Coverage Sweep/,/^## /p' | wc -l)
  if [[ "$WYSIATI_LINES" -lt 3 ]]; then
    echo "WYSIATI Coverage Sweep section is empty. Must include file coverage counts and any gaps flagged as Unknown." >&2
    return 2
  fi

  # Check verdict section has status
  if ! echo "$CONTENT" | grep -q "reliability-proven\|escalated"; then
    echo "Verdict section must include a status of 'reliability-proven' or 'escalated'." >&2
    return 2
  fi

  return 0
}
