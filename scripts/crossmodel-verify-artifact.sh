#!/bin/bash
# Cross-Model Adversarial Review — Artifact Verifier
# Validates a cross-model review artifact file.
# Args: --path FILE [--project-dir DIR] [--max-size BYTES]
# Exit 0 + JSON with status field. Status values:
#   VALID | MISSING | MALFORMED | OVERSIZED | PATH_VIOLATION | STALE | EMPTY

set -euo pipefail

# --- Arg parsing ---

ARTIFACT_PATH=""
PROJECT_DIR=""
MAX_SIZE=102400  # 100 KB default

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      ARTIFACT_PATH="${2:-}"
      shift 2
      ;;
    --project-dir)
      PROJECT_DIR="${2:-}"
      shift 2
      ;;
    --max-size)
      MAX_SIZE="${2:-}"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ARTIFACT_PATH" ]]; then
  printf 'Missing required argument: --path\n' >&2
  exit 2
fi

# --- Helper: emit result ---

emit_result() {
  local status="$1"
  local detail="${2:-}"
  local checksum="${3:-}"
  printf '{"status":"%s","path":"%s","detail":"%s","sha256":"%s"}\n' \
    "$status" "$ARTIFACT_PATH" "$detail" "$checksum"
}

# --- Check 1: File exists ---

if [[ ! -f "$ARTIFACT_PATH" ]]; then
  emit_result "MISSING" "File does not exist: ${ARTIFACT_PATH}"
  exit 0
fi

# --- Check 2: Path traversal / within project dir ---

if [[ -n "$PROJECT_DIR" ]]; then
  # Resolve both paths to absolute form
  CANON_ARTIFACT=""
  CANON_PROJECT=""

  if command -v realpath &> /dev/null; then
    CANON_ARTIFACT=$(realpath "$ARTIFACT_PATH" 2>/dev/null || echo "$ARTIFACT_PATH")
    CANON_PROJECT=$(realpath "$PROJECT_DIR" 2>/dev/null || echo "$PROJECT_DIR")
  else
    CANON_ARTIFACT=$(cd "$(dirname "$ARTIFACT_PATH")" 2>/dev/null && pwd)/$(basename "$ARTIFACT_PATH")
    CANON_PROJECT=$(cd "$PROJECT_DIR" 2>/dev/null && pwd)
  fi

  # Ensure the artifact path starts with the project dir
  if [[ "${CANON_ARTIFACT#"${CANON_PROJECT}/"}" == "$CANON_ARTIFACT" ]]; then
    emit_result "PATH_VIOLATION" "Artifact is outside project directory. artifact=${CANON_ARTIFACT} project=${CANON_PROJECT}"
    exit 0
  fi
fi

# --- Check 3: File size ---

FILE_SIZE=0
if command -v stat &> /dev/null; then
  # macOS stat vs GNU stat
  FILE_SIZE=$(stat -f%z "$ARTIFACT_PATH" 2>/dev/null || stat -c%s "$ARTIFACT_PATH" 2>/dev/null || echo "0")
else
  FILE_SIZE=$(wc -c < "$ARTIFACT_PATH" 2>/dev/null | tr -d ' ' || echo "0")
fi

if [[ "$FILE_SIZE" -gt "$MAX_SIZE" ]]; then
  emit_result "OVERSIZED" "File size ${FILE_SIZE} bytes exceeds limit ${MAX_SIZE} bytes"
  exit 0
fi

# --- Check 4: Not empty ---

if [[ "$FILE_SIZE" -eq 0 ]]; then
  emit_result "EMPTY" "File is empty"
  exit 0
fi

CONTENT=$(cat "$ARTIFACT_PATH")

if [[ -z "${CONTENT// /}" ]]; then
  emit_result "EMPTY" "File contains only whitespace"
  exit 0
fi

# --- Check 5: Required headings ---

MALFORMED_REASON=""

# Required top-level heading
if ! printf '%s\n' "$CONTENT" | grep -q "^## Cross-Model Review:"; then
  MALFORMED_REASON="Missing required heading: '## Cross-Model Review:'"
fi

# Required subsections
if [[ -z "$MALFORMED_REASON" ]]; then
  if ! printf '%s\n' "$CONTENT" | grep -q "^### Findings"; then
    MALFORMED_REASON="Missing required heading: '### Findings'"
  fi
fi

if [[ -z "$MALFORMED_REASON" ]]; then
  if ! printf '%s\n' "$CONTENT" | grep -q "^### Summary"; then
    MALFORMED_REASON="Missing required heading: '### Summary'"
  fi
fi

# --- Check 6: Findings table header row ---

if [[ -z "$MALFORMED_REASON" ]]; then
  if ! printf '%s\n' "$CONTENT" | grep -q "| # | Severity |"; then
    MALFORMED_REASON="Missing findings table header row: '| # | Severity |'"
  fi
fi

if [[ -n "$MALFORMED_REASON" ]]; then
  emit_result "MALFORMED" "$MALFORMED_REASON"
  exit 0
fi

# --- Compute SHA-256 checksum ---

CHECKSUM=""
if command -v sha256sum &> /dev/null; then
  CHECKSUM=$(sha256sum "$ARTIFACT_PATH" | awk '{print $1}')
elif command -v shasum &> /dev/null; then
  CHECKSUM=$(shasum -a 256 "$ARTIFACT_PATH" | awk '{print $1}')
else
  CHECKSUM="unavailable"
fi

# --- All checks passed ---

emit_result "VALID" "" "$CHECKSUM"
