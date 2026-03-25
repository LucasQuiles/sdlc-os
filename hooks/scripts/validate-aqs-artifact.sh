#!/bin/bash
# AQS Artifact Schema Validator
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/adversarial/*
# Exit 0 = valid, Exit 2 = invalid (blocks with feedback to Claude)

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only validate AQS artifacts
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Match AQS artifact paths
if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/adversarial/ ]] && [[ ! "$FILE_PATH" =~ -aqs\.md$ ]]; then
  exit 0
fi

CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
if [[ -z "$CONTENT" ]]; then
  # Edit tool — read the file to get current content
  if [[ -f "$FILE_PATH" ]]; then
    CONTENT=$(cat "$FILE_PATH")
  else
    exit 0
  fi
fi

ERRORS=""

# Detect artifact type from filename and content
if [[ "$FILE_PATH" =~ findings- ]]; then
  # RED TEAM FINDINGS — validate required fields per finding
  # Required: Domain, Severity, Claim, Minimal reproduction, Impact, Evidence, Confidence

  FINDING_COUNT=$(echo "$CONTENT" | grep -c "^## Finding:" || true)
  if [[ "$FINDING_COUNT" -gt 0 ]]; then
    # Check each required field exists at least once
    for FIELD in "Domain:" "Severity:" "Claim:" "Minimal reproduction:" "Impact:" "Evidence:" "Confidence:"; do
      FIELD_COUNT=$(echo "$CONTENT" | grep -c "\*\*${FIELD}\*\*" || true)
      if [[ "$FIELD_COUNT" -lt "$FINDING_COUNT" ]]; then
        ERRORS="${ERRORS}Finding missing required field: ${FIELD} (found ${FIELD_COUNT} of ${FINDING_COUNT} findings)\n"
      fi
    done

    # Validate domain vocabulary
    if echo "$CONTENT" | grep -qiE '\*\*Domain:\*\*.*\b(correctness|robustness|performance)\b'; then
      ERRORS="${ERRORS}Non-canonical domain name detected. Use: functionality | security | usability | resilience\n"
    fi

    # Validate severity vocabulary
    if echo "$CONTENT" | grep -qiE '\*\*Severity:\*\*' && ! echo "$CONTENT" | grep -qE '\*\*Severity:\*\*.*(critical|high|medium|low)'; then
      ERRORS="${ERRORS}Invalid severity. Use: critical | high | medium | low\n"
    fi

    # Validate confidence vocabulary
    if echo "$CONTENT" | grep -qiE '\*\*Confidence:\*\*' && ! echo "$CONTENT" | grep -qE '\*\*Confidence:\*\*.*(Verified|Likely|Assumed)'; then
      ERRORS="${ERRORS}Invalid confidence label. Use: Verified | Likely | Assumed\n"
    fi
  fi

elif [[ "$FILE_PATH" =~ responses- ]]; then
  # BLUE TEAM RESPONSES — validate required fields

  RESPONSE_COUNT=$(echo "$CONTENT" | grep -c "^## Response:" || true)
  if [[ "$RESPONSE_COUNT" -gt 0 ]]; then
    # Check action field
    ACTION_COUNT=$(echo "$CONTENT" | grep -c "\*\*Action:\*\*" || true)
    if [[ "$ACTION_COUNT" -lt "$RESPONSE_COUNT" ]]; then
      ERRORS="${ERRORS}Response missing required field: Action (found ${ACTION_COUNT} of ${RESPONSE_COUNT} responses)\n"
    fi

    # Check accepted responses have defensive iteration fields
    ACCEPTED_COUNT=$(echo "$CONTENT" | grep -c "accepted" || true)
    if [[ "$ACCEPTED_COUNT" -gt 0 ]]; then
      for FIELD in "Pre-fix reproduction:" "Post-fix reproduction:" "Regression check:" "Fix:"; do
        if ! echo "$CONTENT" | grep -q "${FIELD}\|pre-fix repro\|Pre-fix repro\|Gap confirmed:\|Problem confirmed:\|Attack reproduction:\|Pre-fix reproduction:"; then
          # Only error if there are accepted findings and the field pattern is completely missing
          if echo "$CONTENT" | grep -q "\*\*Action:\*\* accepted"; then
            FIELD_FOUND=$(echo "$CONTENT" | grep -c "${FIELD}" || true)
            if [[ "$FIELD_FOUND" -eq 0 ]] && [[ "$FIELD" == "Fix:" ]]; then
              ERRORS="${ERRORS}Accepted response missing required field: ${FIELD}\n"
            fi
          fi
        fi
      done

      # Check for defensive iteration pattern (any variant)
      if echo "$CONTENT" | grep -q "\*\*Action:\*\* accepted"; then
        HAS_PRE=$(echo "$CONTENT" | grep -cE "(Pre-fix reproduction|Gap confirmed|Problem confirmed|Reproduce the)" || true)
        HAS_POST=$(echo "$CONTENT" | grep -cE "(Post-fix reproduction|Fix verified|Improvement verified|Re-trace)" || true)
        HAS_REGRESSION=$(echo "$CONTENT" | grep -cE "(Regression check|Adjacency check|adjacent)" || true)

        if [[ "$HAS_PRE" -eq 0 ]]; then
          ERRORS="${ERRORS}Accepted response missing defensive iteration: pre-fix reproduction step\n"
        fi
        if [[ "$HAS_POST" -eq 0 ]]; then
          ERRORS="${ERRORS}Accepted response missing defensive iteration: post-fix verification step\n"
        fi
        if [[ "$HAS_REGRESSION" -eq 0 ]]; then
          ERRORS="${ERRORS}Accepted response missing defensive iteration: regression/adjacency check step\n"
        fi
      fi
    fi
  fi

elif [[ "$FILE_PATH" =~ verdicts- ]]; then
  # ARBITER VERDICTS — validate required fields

  VERDICT_COUNT=$(echo "$CONTENT" | grep -c "^## Verdict:" || true)
  if [[ "$VERDICT_COUNT" -gt 0 ]]; then
    for FIELD in "Decision:" "Red team claim:" "Blue team position:" "Test designed:" "Test result:" "Reasoning:"; do
      FIELD_COUNT=$(echo "$CONTENT" | grep -c "\*\*${FIELD}\*\*" || true)
      if [[ "$FIELD_COUNT" -lt "$VERDICT_COUNT" ]]; then
        ERRORS="${ERRORS}Verdict missing required field: ${FIELD}\n"
      fi
    done

    # Check for pre-registration fields (new Kahneman protocol)
    for FIELD in "Dispute contract locked:" "Red team pre-commitment:" "Blue team pre-commitment:" "Residual uncertainty:"; do
      if ! echo "$CONTENT" | grep -q "\*\*${FIELD}\*\*"; then
        ERRORS="${ERRORS}Verdict missing Kahneman protocol field: ${FIELD}\n"
      fi
    done

    # Validate decision vocabulary
    if echo "$CONTENT" | grep -qE '\*\*Decision:\*\*' && ! echo "$CONTENT" | grep -qE '\*\*Decision:\*\*.*(SUSTAINED|DISMISSED|MODIFIED)'; then
      ERRORS="${ERRORS}Invalid verdict decision. Use: SUSTAINED | DISMISSED | MODIFIED\n"
    fi
  fi

elif [[ "$FILE_PATH" =~ -aqs\.md$ ]]; then
  # AQS REPORT — validate required sections

  if echo "$CONTENT" | grep -q "Adversarial Quality Report"; then
    for SECTION in "Engagement Summary" "Findings" "Hardening Changes" "Belief Update" "Residual Risk" "Verdict"; do
      if ! echo "$CONTENT" | grep -q "### ${SECTION}\|## ${SECTION}"; then
        ERRORS="${ERRORS}AQS report missing required section: ${SECTION}\n"
      fi
    done

    # Validate report verdict vocabulary
    if echo "$CONTENT" | grep -qE '^\*\*\[?HARDENED|PARTIALLY_HARDENED|DEFERRED'; then
      : # Valid
    elif echo "$CONTENT" | grep -q "### Verdict\|## Verdict"; then
      if ! echo "$CONTENT" | grep -qE 'HARDENED|PARTIALLY_HARDENED|DEFERRED'; then
        ERRORS="${ERRORS}AQS report verdict must be: HARDENED | PARTIALLY_HARDENED | DEFERRED\n"
      fi
    fi
  fi

elif [[ "$FILE_PATH" =~ recon- ]]; then
  # RECON RESULTS — validate signal format

  PROBE_COUNT=$(echo "$CONTENT" | grep -cE "(SIGNAL|NO_SIGNAL)" || true)
  if [[ "$PROBE_COUNT" -eq 0 ]] && echo "$CONTENT" | grep -qi "recon"; then
    ERRORS="${ERRORS}Recon results must contain SIGNAL or NO_SIGNAL responses\n"
  fi
fi

# Output result
if [[ -n "$ERRORS" ]]; then
  echo -e "AQS Schema Validation Failed for $(basename "$FILE_PATH"):\n${ERRORS}\nFix these issues and retry the write." >&2
  exit 2
else
  exit 0
fi
