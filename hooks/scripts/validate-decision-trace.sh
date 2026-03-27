#!/bin/bash
# Decision Trace Validator
# Runs as PostToolUse hook on Write|Edit targeting docs/sdlc/active/*/beads/*.md
# Validates that bead files contain required FFT fields and decision trace artifact
# Exit 0 = valid, Exit 2 = invalid (blocks with feedback to Claude)

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

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

CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
  CONTENT=$(cat "$FILE_PATH")
fi

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
