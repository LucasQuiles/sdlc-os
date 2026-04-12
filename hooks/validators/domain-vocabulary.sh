#!/bin/bash
# validate_domain_vocabulary — sourceable validator function
# Args: $1 = content (full file content as string)
# Returns 0 for pass, 2 for block.

validate_domain_vocabulary() {
  local CONTENT="$1"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  local ERRORS=""

  # Check for non-canonical AQS domain names
  # Canonical: functionality, security, usability, resilience
  # Common drift: correctness, robustness, performance, reliability
  local BAD_DOMAIN
  for BAD_DOMAIN in "correctness" "robustness" "performance" "reliability"; do
    if echo "$CONTENT" | grep -iE "(domain|domains tested|domains activated).*\b${BAD_DOMAIN}\b" > /dev/null 2>&1; then
      ERRORS="${ERRORS}Non-canonical domain name '${BAD_DOMAIN}' detected. Canonical AQS domains: functionality | security | usability | resilience\n"
    fi
  done

  # Check for non-canonical confidence labels
  local BAD_LABEL
  for BAD_LABEL in "Probable" "Certain" "Uncertain" "Possible" "Confirmed"; do
    if echo "$CONTENT" | grep -E "\*\*Confidence:\*\*.*\b${BAD_LABEL}\b" > /dev/null 2>&1; then
      ERRORS="${ERRORS}Non-canonical confidence label '${BAD_LABEL}'. Use: Verified | Likely | Assumed | Unknown\n"
    fi
  done

  # Check for non-canonical verdict labels in AQS reports
  if echo "$CONTENT" | grep -q "Adversarial Quality Report\|AQS Report"; then
    local BAD_VERDICT
    for BAD_VERDICT in "PASSED" "FAILED" "APPROVED" "REJECTED" "CLEAN" "DIRTY"; do
      if echo "$CONTENT" | grep -E "\b${BAD_VERDICT}\b" > /dev/null 2>&1; then
        ERRORS="${ERRORS}Non-canonical AQS report verdict '${BAD_VERDICT}'. Use: HARDENED | PARTIALLY_HARDENED | DEFERRED\n"
      fi
    done
  fi

  if [[ -n "$ERRORS" ]]; then
    echo -e "Domain vocabulary lint failed:\n${ERRORS}\nFix vocabulary to use canonical terms." >&2
    return 2
  fi

  return 0
}
