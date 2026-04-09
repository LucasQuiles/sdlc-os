#!/bin/bash
# Convention Map Naming Check (PreToolUse on Write)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr for violations.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

INPUT=$(read_hook_stdin)
FILE_PATH=$(read_hook_file_path "$INPUT")

if [[ -z "$FILE_PATH" ]]; then exit 0; fi
if is_vendor_path "$FILE_PATH"; then exit 0; fi
if [[ "$FILE_PATH" == *"__tests__/"* ]] || [[ "$FILE_PATH" == *"__mocks__/"* ]]; then exit 0; fi

REPO_ROOT=$(get_repo_root)
CONVENTION_MAP="${REPO_ROOT}/docs/sdlc/convention-map.md"
if [[ ! -f "$CONVENTION_MAP" ]]; then exit 0; fi

PATTERNS=$(read_convention_map_patterns)
if [[ -z "$PATTERNS" ]]; then exit 0; fi

FILE_DIR=$(dirname "$FILE_PATH")
FILE_NAME=$(basename "$FILE_PATH")
STEM=$(extract_stem "$FILE_NAME")
if [[ -z "$STEM" ]]; then exit 0; fi

MATCHED_CONVENTION=""
MATCHED_DIR=""
LONGEST_MATCH=0

while IFS= read -r pair; do
  MAP_DIR="${pair%%|*}"
  MAP_CONV="${pair##*|}"
  if [[ "$FILE_DIR" == *"$MAP_DIR"* ]]; then
    local_len=${#MAP_DIR}
    if [[ "$local_len" -gt "$LONGEST_MATCH" ]]; then
      LONGEST_MATCH=$local_len
      MATCHED_CONVENTION="$MAP_CONV"
      MATCHED_DIR="$MAP_DIR"
    fi
  fi
done <<< "$PATTERNS"

if [[ -n "$MATCHED_CONVENTION" ]]; then
  if ! check_convention "$STEM" "$MATCHED_CONVENTION"; then
    DETECTED=$(detect_convention "$STEM")
    emit_warning "File naming violation — ${FILE_NAME} stem '${STEM}' uses ${DETECTED} but ${MATCHED_DIR}/ convention is ${MATCHED_CONVENTION}. See docs/sdlc/convention-map.md."
  fi
else
  if is_known_source_dir "$FILE_DIR"; then
    emit_warning "Unmapped source directory — ${FILE_DIR} has no Convention Map entry. Consider running /normalize."
  fi
fi

exit 0
