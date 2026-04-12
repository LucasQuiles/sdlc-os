#!/bin/bash
# validate_decision_trace — sourceable validator function
# Args: $1 = file_path, $2 = content
# Returns 0 for pass, 2 for block.

validate_decision_trace() {
  local file_path="$1"
  local CONTENT="$2"

  if [[ -z "$CONTENT" ]]; then
    return 0
  fi

  if ! command -v jq &>/dev/null; then
    echo '{"error": "jq is required but not found"}' >&2
    return 2
  fi

  # --- Bead field checks ---
  local MISSING=()

  if ! echo "$CONTENT" | grep -q '^\*\*Profile:\*\*'; then
    MISSING+=("Profile (must be BUILD|INVESTIGATE|REPAIR|EVOLVE)")
  fi

  if ! echo "$CONTENT" | grep -q '^\*\*Security sensitive:\*\*'; then
    MISSING+=("Security sensitive (must be true|false)")
  fi

  if ! echo "$CONTENT" | grep -q '^\*\*Complexity source:\*\*'; then
    MISSING+=("Complexity source (must be essential|accidental)")
  fi

  if ! echo "$CONTENT" | grep -q '^\*\*Decision trace:\*\*'; then
    MISSING+=("Decision trace (must contain path to trace file)")
  fi

  if ! echo "$CONTENT" | grep -q '^\*\*Deterministic checks:\*\*'; then
    MISSING+=("Deterministic checks (list of checks routed to scripts)")
  fi

  if ! echo "$CONTENT" | grep -q '^\*\*Turbulence:\*\*'; then
    MISSING+=("Turbulence (loop cycle counts)")
  fi

  if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Bead is missing required FFT fields:" >&2
    local field
    for field in "${MISSING[@]}"; do
      echo "  - ${field}" >&2
    done
    echo "" >&2
    echo "All beads must include FFT decision backbone fields." >&2
    echo "See references/fft-decision-trees.md for the full FFT specification." >&2
    return 2
  fi

  # --- Phase B field enforcement ---
  local CYNEFIN_DOMAIN SECURITY_SENSITIVE PHASE_B_STATUS
  CYNEFIN_DOMAIN=$(echo "$CONTENT" | sed -n 's/^\*\*Cynefin domain:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
  SECURITY_SENSITIVE=$(echo "$CONTENT" | sed -n 's/^\*\*Security sensitive:\*\*[[:space:]]*\([a-z]*\).*/\1/p' | head -1 || true)
  PHASE_B_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

  local PHASE_B_REQUIRED=false
  if [[ "$CYNEFIN_DOMAIN" == "complex" ]] || [[ "$SECURITY_SENSITIVE" == "true" ]]; then
    PHASE_B_REQUIRED=true
  fi

  if [[ "$PHASE_B_REQUIRED" == "true" ]] && [[ -n "$PHASE_B_STATUS" ]] && [[ "$PHASE_B_STATUS" != "pending" ]] && [[ "$PHASE_B_STATUS" != "submitted" ]]; then
    local TASK_DIR BEAD_ID HDL_FILE
    TASK_DIR=$(dirname "$(dirname "$file_path")")
    HDL_FILE="$TASK_DIR/hazard-defense-ledger.yaml"
    BEAD_ID=$(basename "$file_path" .md)
    if [[ -f "$HDL_FILE" ]]; then
      if ! grep -q "bead_id: ${BEAD_ID}" "$HDL_FILE" 2>/dev/null; then
        echo "HOOK_WARNING: Phase B: hazard-defense-ledger.yaml exists but has no records for bead $BEAD_ID" >&2
      fi
    else
      echo "HOOK_WARNING: Phase B: hazard-defense-ledger.yaml not found for STPA-required bead $BEAD_ID" >&2
    fi
  fi

  # --- Trace artifact checks (run only when status transitions past pending) ---
  local CURRENT_STATUS
  CURRENT_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

  if [[ -n "$CURRENT_STATUS" ]] && [[ "$CURRENT_STATUS" != "pending" ]]; then
    local TRACE_PATH
    TRACE_PATH=$(echo "$CONTENT" | sed -n 's/^\*\*Decision trace:\*\*[[:space:]]*\(.*\)/\1/p' | head -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)

    if [[ -z "$TRACE_PATH" ]] || [[ "$TRACE_PATH" == "[]" ]] || [[ "$TRACE_PATH" == "none" ]]; then
      echo "Bead has advanced past 'pending' but Decision trace path is empty." >&2
      echo "A decision trace must be written before a bead can advance." >&2
      return 2
    fi

    local RESOLVED_PATH="$TRACE_PATH"
    if [[ ! "$TRACE_PATH" =~ ^/ ]] && command -v git &> /dev/null; then
      local REPO_ROOT
      REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
      if [[ -n "$REPO_ROOT" ]]; then
        RESOLVED_PATH="$REPO_ROOT/$TRACE_PATH"
      fi
    fi

    if [[ ! -f "$RESOLVED_PATH" ]]; then
      echo "Bead has advanced past 'pending' but decision trace file does not exist:" >&2
      echo "  Expected: $TRACE_PATH" >&2
      echo "  Resolved: $RESOLVED_PATH" >&2
      echo "" >&2
      echo "The decision trace must be written BEFORE the bead advances past pending." >&2
      echo "See references/fft-decision-trees.md for the trace format." >&2
      return 2
    fi

    if ! grep -q "## FFT-01" "$RESOLVED_PATH" || ! grep -q "## FFT-02" "$RESOLVED_PATH"; then
      echo "Decision trace exists but is missing required FFT sections." >&2
      echo "Trace must contain at least ## FFT-01 and ## FFT-02 headers." >&2
      return 2
    fi

    if ! grep -q '\*\*Decision:\*\*' "$RESOLVED_PATH"; then
      echo "Decision trace exists but contains no **Decision:** entries." >&2
      echo "FFT traversals must record their decisions." >&2
      return 2
    fi
  fi

  return 0
}
