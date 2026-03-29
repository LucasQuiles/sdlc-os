#!/bin/bash
# Safety Constraints Hook — Deterministic Subset
# Runs as PostToolUse hook on Write|Edit for source files
# Checks SC-005 (secrets near log statements) and SC-004 (bare catch/except blocks)
# Advisory mode only: always exits 0, writes warnings to stderr
# Blocking enforcement happens at agent level (safety-constraints-guardian during L1)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

INPUT=$(cat)
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only check source files (not markdown, json, yaml, etc.)
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Skip non-source files
case "$FILE_PATH" in
  *.md|*.json|*.yaml|*.yml|*.txt|*.toml|*.ini|*.cfg|*.conf|*.lock|*.sum)
    exit 0
    ;;
esac

# Get file content from tool input or from disk
CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

WARNINGS=()

# SC-004: Bare catch/except blocks (error handlers that swallow errors silently)
# Detect: empty catch blocks, catch with only comment, bare except: pass in Python

# Check for empty catch blocks: catch(...) {} or catch { }
if echo "$CONTENT" | grep -qE 'catch\s*(\([^)]*\))?\s*\{\s*\}'; then
  WARNINGS+=("SC-004: Empty catch block detected — error handler swallows exception silently. Add logging, rethrowing, or meaningful error handling.")
fi

# Check for catch blocks containing only a comment (// or /* comment */)
if echo "$CONTENT" | grep -qE 'catch\s*(\([^)]*\))?\s*\{\s*//[^\n]*\s*\}' || \
   echo "$CONTENT" | grep -qP 'catch\s*(\([^)]*\))?\s*\{\s*/\*.*?\*/\s*\}' 2>/dev/null; then
  WARNINGS+=("SC-004: Catch block contains only a comment — this swallows the exception. Add logging or rethrowing.")
fi

# Check for Python bare except: pass
if echo "$CONTENT" | grep -qE '^\s*except(\s+\w+)?:\s*$'; then
  # Look for a following 'pass' line
  if echo "$CONTENT" | grep -qE '^\s*except(\s+\w+)?:\s*$' && echo "$CONTENT" | grep -A1 -E '^\s*except(\s+\w+)?:\s*$' | grep -qE '^\s*pass\s*$'; then
    WARNINGS+=("SC-004: Python bare except/pass detected — exception is swallowed silently. Add logging or re-raise.")
  fi
fi

# SC-005: Secrets near log statements
# Check if secret-like variable names appear near logging calls in the same file

SECRET_PATTERN='(password|secret|token|api_key|apikey|credential|private_key|auth_key|access_key)\s*='
LOG_PATTERN='(log\.|logger\.|console\.log|console\.error|console\.warn|print\(|printf\(|logging\.|System\.out\.print|NSLog\()'

HAS_SECRETS=$(echo "$CONTENT" | grep -iE "$SECRET_PATTERN" | wc -l || true)
HAS_LOGGING=$(echo "$CONTENT" | grep -iE "$LOG_PATTERN" | wc -l || true)

if [[ "$HAS_SECRETS" -gt 0 ]] && [[ "$HAS_LOGGING" -gt 0 ]]; then
  # Both patterns present — check for proximity (within 10 lines of each other)
  # Extract line numbers for secrets and logging calls
  SECRET_LINES=$(echo "$CONTENT" | grep -inE "$SECRET_PATTERN" | cut -d: -f1 || true)
  LOG_LINES=$(echo "$CONTENT" | grep -inE "$LOG_PATTERN" | cut -d: -f1 || true)

  PROXIMITY_HIT=false
  for sline in $SECRET_LINES; do
    for lline in $LOG_LINES; do
      DIFF=$(( sline - lline ))
      if [[ $DIFF -lt 0 ]]; then DIFF=$(( -DIFF )); fi
      if [[ $DIFF -le 10 ]]; then
        PROXIMITY_HIT=true
        break 2
      fi
    done
  done

  if [[ "$PROXIMITY_HIT" == "true" ]]; then
    WARNINGS+=("SC-005: Secret-like variable assignment found within 10 lines of a log statement. Verify secrets are not written to logs. If the value is masked (e.g., '[REDACTED]'), this warning can be ignored.")
  fi
fi

# Output warnings to stderr (advisory — always exit 0)
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo "[safety-constraints] Advisory warnings for ${FILE_PATH}:" >&2
  for warning in "${WARNINGS[@]}"; do
    echo "  WARNING: ${warning}" >&2
  done
  echo "" >&2
  echo "  These are advisory only. Blocking enforcement occurs during L1 sentinel (safety-constraints-guardian)." >&2
  echo "  See references/safety-constraints.md for constraint definitions." >&2
fi

exit 0
