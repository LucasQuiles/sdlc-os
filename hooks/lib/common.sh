#!/bin/bash
# SDLC-OS Hook Shared Library
# Source this file from hook scripts for shared utilities.
# Advisory scripts: use set -uo pipefail (no -e), handle errors explicitly, end with exit 0.
# Blocking scripts: use set -euo pipefail, use exit 2 for violations.

# --- Path Canonicalization ---

canonicalize_path() {
  local path="$1"
  if [[ -z "$path" ]]; then
    echo ""
    return
  fi
  if command -v realpath &> /dev/null; then
    local resolved
    resolved=$(realpath "$path" 2>/dev/null) && { echo "$resolved"; return; }
  fi
  if [[ "$path" == /* ]]; then
    local dir base
    dir=$(dirname "$path")
    base=$(basename "$path")
    local resolved_dir
    resolved_dir=$(cd "$dir" 2>/dev/null && pwd -P) && { echo "${resolved_dir}/${base}"; return; }
  fi
  echo "$path"
}

get_repo_root() {
  local root
  if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null 2>&1; then
    root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [[ -n "$root" ]]; then
      canonicalize_path "$root"
      return
    fi
  fi
  echo ""
}

# --- Warning Output ---

emit_warning() {
  local message="$1"
  echo "HOOK_WARNING: ${message}" >&2
  return 0
}

# --- Scope Filtering ---

is_vendor_path() {
  local path="$1"
  case "$path" in
    */node_modules/*|*/dist/*|*/build/*|*/.git/*|*/__pycache__/*|*/.next/*|*/vendor/*|*/.cache/*|*/.turbo/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

KNOWN_SOURCE_DIRS="lib/ app/ components/ src/ hooks/ services/ pages/ routes/ api/"

is_known_source_dir() {
  local dir="$1"
  local known
  for known in $KNOWN_SOURCE_DIRS; do
    if [[ "$dir" == *"$known"* ]]; then
      return 0
    fi
  done
  return 1
}

# --- Convention Map Parsing ---

read_convention_map_patterns() {
  local map_file
  map_file="$(get_repo_root)/docs/sdlc/convention-map.md"
  if [[ ! -f "$map_file" ]]; then
    return
  fi

  local current_convention=""
  local current_scope=""

  while IFS= read -r line; do
    if [[ "$line" =~ ^###[[:space:]] ]]; then
      if [[ -n "$current_convention" ]] && [[ -n "$current_scope" ]]; then
        local IFS=','
        local dir
        for dir in $current_scope; do
          dir=$(echo "$dir" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
          dir="${dir%/}"
          if [[ -n "$dir" ]]; then
            echo "${dir}|${current_convention}"
          fi
        done
      fi
      current_convention=""
      current_scope=""
      continue
    fi

    if [[ "$line" =~ ^-[[:space:]]\*\*Convention:\*\*[[:space:]]*(.*) ]]; then
      local value="${BASH_REMATCH[1]}"
      case "$value" in
        kebab-case|PascalCase|camelCase|snake_case|UPPER_SNAKE_CASE)
          current_convention="$value"
          ;;
      esac
      continue
    fi

    if [[ "$line" =~ ^-[[:space:]]\*\*Scope:\*\*[[:space:]]*(.*) ]]; then
      current_scope="${BASH_REMATCH[1]}"
      continue
    fi
  done < "$map_file"

  # Flush final section
  if [[ -n "$current_convention" ]] && [[ -n "$current_scope" ]]; then
    local IFS=','
    local dir
    for dir in $current_scope; do
      dir=$(echo "$dir" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      dir="${dir%/}"
      if [[ -n "$dir" ]]; then
        echo "${dir}|${current_convention}"
      fi
    done
  fi
}

# --- Filename Convention Checking ---

KNOWN_SUFFIXES=".test.ts .test.tsx .spec.ts .spec.tsx .d.ts .stories.tsx .module.css .module.scss .config.ts .config.js .test.js .spec.js .stories.js"
SPECIAL_FILENAMES="index.ts index.js index.tsx index.d.ts README.md CHANGELOG.md LICENSE"

extract_stem() {
  local filename="$1"
  local special
  for special in $SPECIAL_FILENAMES; do
    if [[ "$filename" == "$special" ]]; then
      echo ""
      return
    fi
  done
  if [[ "$filename" == .* ]]; then
    echo ""
    return
  fi
  local suffix
  for suffix in $KNOWN_SUFFIXES; do
    if [[ "$filename" == *"$suffix" ]]; then
      echo "${filename%"$suffix"}"
      return
    fi
  done
  echo "${filename%.*}"
}

check_convention() {
  local stem="$1"
  local expected="$2"
  if [[ -z "$stem" ]]; then
    return 0
  fi
  case "$expected" in
    kebab-case)
      [[ "$stem" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ ]] && return 0
      ;;
    PascalCase)
      [[ "$stem" =~ ^[A-Z][a-zA-Z0-9]*$ ]] && return 0
      ;;
    camelCase)
      [[ "$stem" =~ ^[a-z][a-zA-Z0-9]*$ ]] && return 0
      ;;
    snake_case)
      [[ "$stem" =~ ^[a-z][a-z0-9]*(_[a-z0-9]+)*$ ]] && return 0
      ;;
    UPPER_SNAKE_CASE)
      [[ "$stem" =~ ^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$ ]] && return 0
      ;;
  esac
  return 1
}

detect_convention() {
  local stem="$1"
  if [[ "$stem" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ ]]; then echo "kebab-case"; return; fi
  if [[ "$stem" =~ ^[A-Z][a-zA-Z0-9]*$ ]]; then echo "PascalCase"; return; fi
  if [[ "$stem" =~ ^[a-z][a-zA-Z0-9]*$ ]]; then echo "camelCase"; return; fi
  if [[ "$stem" =~ ^[a-z][a-z0-9]*(_[a-z0-9]+)*$ ]]; then echo "snake_case"; return; fi
  if [[ "$stem" =~ ^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$ ]]; then echo "UPPER_SNAKE_CASE"; return; fi
  echo "non-standard"
}

# --- Hook Input Parsing ---

# read_hook_file_path: Extract .tool_input.file_path from hook JSON input.
# Usage: FILE_PATH=$(read_hook_file_path "$INPUT")
# Returns the path string, or empty string if not present or jq fails.
read_hook_file_path() {
  local input="$1"
  local path
  path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
    echo ""
    return
  }
  echo "$path"
}

# read_tool_content: Extract content from .tool_input.content, falling back to
# reading the file at file_path from disk (for Edit tool where content is absent).
# Usage: CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")
# Returns the content string, or empty string if unavailable.
read_tool_content() {
  local input="$1"
  local file_path="$2"
  local content
  content=$(echo "$input" | jq -r '.tool_input.content // empty' 2>/dev/null) || true
  if [[ -z "$content" ]] && [[ -n "$file_path" ]] && [[ -f "$file_path" ]]; then
    content=$(cat "$file_path" 2>/dev/null) || true
  fi
  echo "$content"
}

# --- Hook Stdin Reading ---

# read_hook_stdin: Read hook input from stdin with a timeout guard.
# Prevents indefinite hangs when stdin is empty or not connected.
# Usage: INPUT=$(read_hook_stdin)
# Returns stdin content, or exits 0 if stdin is empty.
read_hook_stdin() {
  local input
  input=$(timeout 2s cat || true)
  if [ -z "$input" ]; then
    exit 0
  fi
  echo "$input"
}
