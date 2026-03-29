#!/bin/bash
# Decision Trace Validator
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/beads/*.md
# Validates that bead files contain required FFT fields and decision trace artifact
# Exit 0 = valid, Exit 2 = invalid (blocks with feedback to Claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

if ! command -v jq &>/dev/null; then
  echo '{"error": "jq is required but not found"}' >&2
  exit 2
fi

INPUT=$(cat)
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only validate bead files (not decision traces, AQS reports, or hardening reports)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ docs/sdlc/active/.*/beads/.*\.md$ ]]; then
  exit 0
fi

# Skip decision trace files themselves
if [[ "$FILE_PATH" =~ -decision-trace\.md$ ]]; then
  exit 0
fi

# Skip AQS and hardening report files
if [[ "$FILE_PATH" =~ -aqs\.md$ ]] || [[ "$FILE_PATH" =~ hardening-report\.md$ ]]; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# --- Bead field checks (run on every bead write) ---

MISSING=()

# Check Profile field
if ! echo "$CONTENT" | grep -q '^\*\*Profile:\*\*'; then
  MISSING+=("Profile (must be BUILD|INVESTIGATE|REPAIR|EVOLVE)")
fi

# Check Security sensitive field
if ! echo "$CONTENT" | grep -q '^\*\*Security sensitive:\*\*'; then
  MISSING+=("Security sensitive (must be true|false)")
fi

# Check Complexity source field
if ! echo "$CONTENT" | grep -q '^\*\*Complexity source:\*\*'; then
  MISSING+=("Complexity source (must be essential|accidental)")
fi

# Check Decision trace field
if ! echo "$CONTENT" | grep -q '^\*\*Decision trace:\*\*'; then
  MISSING+=("Decision trace (must contain path to trace file)")
fi

# Check Deterministic checks field
if ! echo "$CONTENT" | grep -q '^\*\*Deterministic checks:\*\*'; then
  MISSING+=("Deterministic checks (list of checks routed to scripts)")
fi

# Check Turbulence field
if ! echo "$CONTENT" | grep -q '^\*\*Turbulence:\*\*'; then
  MISSING+=("Turbulence (loop cycle counts)")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "Bead is missing required FFT fields:" >&2
  for field in "${MISSING[@]}"; do
    echo "  - ${field}" >&2
  done
  echo "" >&2
  echo "All beads must include FFT decision backbone fields." >&2
  echo "See references/fft-decision-trees.md for the full FFT specification." >&2
  exit 2
fi

# --- Phase B field enforcement (complex or security-sensitive beads) ---

CYNEFIN_DOMAIN=$(echo "$CONTENT" | sed -n 's/^\*\*Cynefin:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)
SECURITY_SENSITIVE=$(echo "$CONTENT" | sed -n 's/^\*\*Security sensitive:\*\*[[:space:]]*\([a-z]*\).*/\1/p' | head -1 || true)
PHASE_B_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

PHASE_B_REQUIRED=false
if [[ "$CYNEFIN_DOMAIN" == "complex" ]] || [[ "$SECURITY_SENSITIVE" == "true" ]]; then
  PHASE_B_REQUIRED=true
fi

if [[ "$PHASE_B_REQUIRED" == "true" ]] && [[ -n "$PHASE_B_STATUS" ]] && [[ "$PHASE_B_STATUS" != "pending" ]] && [[ "$PHASE_B_STATUS" != "submitted" ]]; then
  CONTROL_ACTIONS=$(echo "$CONTENT" | sed -n 's/^\*\*Control actions:\*\*[[:space:]]*\(.*\)/\1/p' | head -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)
  UNSAFE_CONTROL_ACTIONS=$(echo "$CONTENT" | sed -n 's/^\*\*Unsafe control actions:\*\*[[:space:]]*\(.*\)/\1/p' | head -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)

  PHASE_B_ERRORS=()

  if [[ -z "$CONTROL_ACTIONS" ]] || [[ "$CONTROL_ACTIONS" == "[]" ]] || [[ "$CONTROL_ACTIONS" == "Phase B" ]]; then
    PHASE_B_ERRORS+=("control_actions field is empty or unpopulated")
  fi

  if [[ -z "$UNSAFE_CONTROL_ACTIONS" ]] || [[ "$UNSAFE_CONTROL_ACTIONS" == "[]" ]] || [[ "$UNSAFE_CONTROL_ACTIONS" == "Phase B" ]]; then
    PHASE_B_ERRORS+=("unsafe_control_actions field is empty or unpopulated")
  fi

  if [[ ${#PHASE_B_ERRORS[@]} -gt 0 ]]; then
    echo "Bead is complex or security-sensitive but is missing required Phase B safety fields:" >&2
    for err in "${PHASE_B_ERRORS[@]}"; do
      echo "  - ${err}" >&2
    done
    echo "" >&2
    echo "For complex or security-sensitive beads, control_actions and unsafe_control_actions must be populated before advancing past 'submitted'." >&2
    exit 2
  fi
fi

# --- Trace artifact checks (run only when status transitions past pending) ---

CURRENT_STATUS=$(echo "$CONTENT" | sed -n 's/^\*\*Status:\*\*[[:space:]]*\([a-z_]*\).*/\1/p' | head -1 || true)

if [[ -n "$CURRENT_STATUS" ]] && [[ "$CURRENT_STATUS" != "pending" ]]; then
  # Extract the decision trace path
  TRACE_PATH=$(echo "$CONTENT" | sed -n 's/^\*\*Decision trace:\*\*[[:space:]]*\(.*\)/\1/p' | head -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)

  if [[ -z "$TRACE_PATH" ]] || [[ "$TRACE_PATH" == "[]" ]] || [[ "$TRACE_PATH" == "none" ]]; then
    echo "Bead has advanced past 'pending' but Decision trace path is empty." >&2
    echo "A decision trace must be written before a bead can advance." >&2
    exit 2
  fi

  # Check if trace file exists (resolve relative to repo root if needed)
  RESOLVED_PATH="$TRACE_PATH"
  if [[ ! "$TRACE_PATH" =~ ^/ ]] && command -v git &> /dev/null; then
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
    exit 2
  fi

  # Check trace has minimum viable structure
  if ! grep -q "## FFT-01" "$RESOLVED_PATH" || ! grep -q "## FFT-02" "$RESOLVED_PATH"; then
    echo "Decision trace exists but is missing required FFT sections." >&2
    echo "Trace must contain at least ## FFT-01 and ## FFT-02 headers." >&2
    exit 2
  fi

  if ! grep -q '\*\*Decision:\*\*' "$RESOLVED_PATH"; then
    echo "Decision trace exists but contains no **Decision:** entries." >&2
    echo "FFT traversals must record their decisions." >&2
    exit 2
  fi
fi

exit 0
