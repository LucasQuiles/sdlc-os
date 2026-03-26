# Enforcement Hooks v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3 advisory enforcement hooks (PreToolUse naming check, PostToolUse artifact validation, SubagentStop runner output validation) with a shared library, 11 test fixtures, and a refactor of guard-bead-status.sh to use the shared lib.

**Architecture:** Three event-aligned bash scripts source a shared `hooks/lib/common.sh` for path canonicalization, warning formatting, vendor filtering, and Convention Map parsing. All new hooks are advisory (always exit 0, emit `HOOK_WARNING:` on stderr). Existing blocking hooks are unchanged. Convention Map uses explicit `**Convention:**` + `**Scope:**` fields for machine-parseable lookup.

**Tech Stack:** Bash, jq, grep/sed for parsing. Claude Code plugin hook system (PreToolUse, PostToolUse, SubagentStop events).

**Spec:** `docs/superpowers/specs/2026-03-25-enforcement-hooks-v2-design.md`

---

## File Structure

| File | Responsibility | New/Modified |
|------|---------------|-------------|
| `hooks/lib/common.sh` | Shared functions: canonicalize_path, emit_warning, is_vendor_path, read_convention_map_patterns, get_repo_root | New |
| `hooks/scripts/check-naming-convention.sh` | PreToolUse advisory: filename convention check against Convention Map | New |
| `hooks/scripts/validate-consistency-artifacts.sh` | PostToolUse advisory: feature matrix + convention report schema validation | New |
| `hooks/scripts/validate-runner-output.sh` | SubagentStop advisory: runner output structure, convention signals, reuse compliance | New |
| `hooks/scripts/guard-bead-status.sh` | Refactor: replace inline canonicalization with `source common.sh` | Modified |
| `hooks/hooks.json` | Register PreToolUse and SubagentStop events | Modified |
| `agents/convention-scanner.md` | Update output template: `**Pattern:**` → `**Convention:**` + `**Scope:**` | Modified |
| `hooks/tests/test-hooks.sh` | Add `run_test_advisory` function + 11 new test cases | Modified |
| `hooks/tests/fixtures/*.json` | 11 new fixture files | New (11 files) |

---

### Task 1: Update convention-scanner output template

**Files:**
- Modify: `agents/convention-scanner.md:108-150`

The scanner's output template currently uses `**Pattern:**` with free-form text. The hooks need `**Convention:**` (fixed keyword) + `**Scope:**` (directory list) for machine parsing.

- [ ] **Step 1: Replace the output template in convention-scanner.md**

In `agents/convention-scanner.md`, find the template section (lines 110-150) and replace the dimension format from:

```markdown
### [Dimension Name]
- **Pattern:** [description of dominant pattern]
- **Confidence:** [label, e.g., Verified 5/5]
- **Evidence:**
  - `path/to/file.ts:42` — [symbol or line excerpt]
  - `path/to/other.ts:17` — [symbol or line excerpt]
- **Notes:** [optional — transition hints, constitution overrides, etc.]
```

To:

```markdown
### [Dimension Name]
- **Convention:** [keyword from fixed vocabulary: kebab-case | PascalCase | camelCase | snake_case | UPPER_SNAKE_CASE]
- **Scope:** [comma-separated directory prefixes this convention applies to, e.g., lib/storage/, lib/utils/]
- **Confidence:** [label, e.g., Verified 5/5]
- **Evidence:**
  - `path/to/file.ts:42` — [symbol or line excerpt]
  - `path/to/other.ts:17` — [symbol or line excerpt]
- **Notes:** [optional — transition hints, constitution overrides, etc.]
```

- [ ] **Step 2: Verify the change**

Run: `grep -n "Convention:" agents/convention-scanner.md`

Expected: At least one line showing `**Convention:**` in the template section.

Run: `grep -n "Pattern:" agents/convention-scanner.md`

Expected: Zero matches (the old `**Pattern:**` field should be gone from the template).

- [ ] **Step 3: Commit**

```bash
git add agents/convention-scanner.md
git commit -m "feat: update convention-scanner output to use Convention: + Scope: fields

Replace free-form **Pattern:** with machine-parseable **Convention:**
(fixed keyword vocabulary) and **Scope:** (directory list) fields.
Prerequisite for enforcement hooks Convention Map parsing."
```

---

### Task 2: Create shared library `hooks/lib/common.sh`

**Files:**
- Create: `hooks/lib/common.sh`

- [ ] **Step 1: Create the lib directory and common.sh**

Write `hooks/lib/common.sh`:

```bash
#!/bin/bash
# SDLC-OS Hook Shared Library
# Source this file from hook scripts for shared utilities.
# Advisory scripts: call set -uo pipefail (no -e), handle errors explicitly, end with exit 0.
# Blocking scripts: call set -euo pipefail, use exit 2 for violations.

# --- Path Canonicalization ---

canonicalize_path() {
  local path="$1"
  if [[ -z "$path" ]]; then
    echo ""
    return
  fi
  # Try realpath first (resolves symlinks)
  if command -v realpath &> /dev/null; then
    local resolved
    resolved=$(realpath "$path" 2>/dev/null) && { echo "$resolved"; return; }
  fi
  # Fallback: resolve directory part via cd + pwd -P, keep basename
  if [[ "$path" == /* ]]; then
    local dir base
    dir=$(dirname "$path")
    base=$(basename "$path")
    local resolved_dir
    resolved_dir=$(cd "$dir" 2>/dev/null && pwd -P) && { echo "${resolved_dir}/${base}"; return; }
  fi
  # Last resort: return as-is
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
    # New dimension section resets state
    if [[ "$line" =~ ^###[[:space:]] ]]; then
      # Flush previous section if both fields were found
      if [[ -n "$current_convention" ]] && [[ -n "$current_scope" ]]; then
        # Split scope by comma, emit one pair per directory
        local IFS=','
        local dir
        for dir in $current_scope; do
          dir=$(echo "$dir" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
          # Strip trailing slash for consistent matching
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

    # Extract Convention: value (must be from fixed vocabulary)
    if [[ "$line" =~ ^-[[:space:]]\*\*Convention:\*\*[[:space:]]*(.*) ]]; then
      local value="${BASH_REMATCH[1]}"
      # Validate against fixed vocabulary
      case "$value" in
        kebab-case|PascalCase|camelCase|snake_case|UPPER_SNAKE_CASE)
          current_convention="$value"
          ;;
      esac
      continue
    fi

    # Extract Scope: value
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

# Known multi-dot suffixes to strip before checking the stem
KNOWN_SUFFIXES=".test.ts .test.tsx .spec.ts .spec.tsx .d.ts .stories.tsx .module.css .module.scss .config.ts .config.js .test.js .spec.js .stories.js"

# Files that always pass (no warning)
SPECIAL_FILENAMES="index.ts index.js index.tsx index.d.ts README.md CHANGELOG.md LICENSE"

extract_stem() {
  local filename="$1"

  # Check special filenames
  local special
  for special in $SPECIAL_FILENAMES; do
    if [[ "$filename" == "$special" ]]; then
      echo ""  # Empty = skip check
      return
    fi
  done

  # Skip dotfiles
  if [[ "$filename" == .* ]]; then
    echo ""
    return
  fi

  # Strip known multi-dot suffixes
  local suffix
  for suffix in $KNOWN_SUFFIXES; do
    if [[ "$filename" == *"$suffix" ]]; then
      echo "${filename%"$suffix"}"
      return
    fi
  done

  # Default: strip final extension
  echo "${filename%.*}"
}

check_convention() {
  local stem="$1"
  local expected="$2"

  if [[ -z "$stem" ]]; then
    return 0  # Skip (special file)
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
```

- [ ] **Step 2: Make it non-executable (it's sourced, not run directly)**

Run: `ls -la hooks/lib/common.sh`

Expected: File exists. It should NOT be executable (no `chmod +x`) since it's sourced, not run directly.

- [ ] **Step 3: Commit**

```bash
git add hooks/lib/common.sh
git commit -m "feat: add hooks/lib/common.sh shared library

Shared utilities for all hook scripts: canonicalize_path, emit_warning,
is_vendor_path, read_convention_map_patterns, get_repo_root,
extract_stem, check_convention, detect_convention."
```

---

### Task 3: Create `check-naming-convention.sh` (PreToolUse)

**Files:**
- Create: `hooks/scripts/check-naming-convention.sh`

- [ ] **Step 1: Create the script**

Write `hooks/scripts/check-naming-convention.sh`:

```bash
#!/bin/bash
# Convention Map Naming Check (PreToolUse on Write)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr for violations.
# Checks if new file names match the Convention Map's recorded conventions.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

# Parse hook input
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
  emit_warning "check-naming-convention: failed to parse hook input JSON — skipping"
  exit 0
}

# Skip if no file path or vendor path
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if is_vendor_path "$FILE_PATH"; then
  exit 0
fi

# Skip if inside __tests__/ or __mocks__/ (framework conventions override)
if [[ "$FILE_PATH" == *"__tests__/"* ]] || [[ "$FILE_PATH" == *"__mocks__/"* ]]; then
  exit 0
fi

# Check if Convention Map exists
REPO_ROOT=$(get_repo_root)
CONVENTION_MAP="${REPO_ROOT}/docs/sdlc/convention-map.md"
if [[ ! -f "$CONVENTION_MAP" ]]; then
  exit 0
fi

# Build lookup from Convention Map
PATTERNS=$(read_convention_map_patterns)
if [[ -z "$PATTERNS" ]]; then
  exit 0
fi

# Extract directory and filename
FILE_DIR=$(dirname "$FILE_PATH")
FILE_NAME=$(basename "$FILE_PATH")

# Extract stem (strips known suffixes)
STEM=$(extract_stem "$FILE_NAME")
if [[ -z "$STEM" ]]; then
  exit 0  # Special file, skip
fi

# Find longest matching directory prefix in the Convention Map
MATCHED_CONVENTION=""
MATCHED_DIR=""
LONGEST_MATCH=0

while IFS= read -r pair; do
  MAP_DIR="${pair%%|*}"
  MAP_CONV="${pair##*|}"

  # Check if file's directory contains or ends with the map directory
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
  # Check stem against expected convention
  if ! check_convention "$STEM" "$MATCHED_CONVENTION"; then
    DETECTED=$(detect_convention "$STEM")
    emit_warning "File naming violation — ${FILE_NAME} stem '${STEM}' uses ${DETECTED} but ${MATCHED_DIR}/ convention is ${MATCHED_CONVENTION}. See docs/sdlc/convention-map.md."
  fi
else
  # Not in Convention Map — check if it's a known source directory
  if is_known_source_dir "$FILE_DIR"; then
    emit_warning "Unmapped source directory — ${FILE_DIR} has no Convention Map entry. Consider running /normalize."
  fi
fi

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/check-naming-convention.sh
```

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/check-naming-convention.sh
git commit -m "feat: add check-naming-convention.sh PreToolUse hook

Advisory naming convention check against Convention Map. Strips
multi-dot suffixes, handles special files, warns on mismatches
and unmapped source directories. Always exits 0."
```

---

### Task 4: Create `validate-consistency-artifacts.sh` (PostToolUse)

**Files:**
- Create: `hooks/scripts/validate-consistency-artifacts.sh`

- [ ] **Step 1: Create the script**

Write `hooks/scripts/validate-consistency-artifacts.sh`:

```bash
#!/bin/bash
# Consistency Artifact Validator (PostToolUse on Write|Edit)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr for schema violations.
# Validates: feature-matrix.md rows, convention enforcement report structure.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

# Parse hook input
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
  emit_warning "validate-consistency-artifacts: failed to parse hook input JSON — skipping"
  exit 0
}

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# --- Path Routing ---

# Priority 1: Feature Matrix by path
if [[ "$FILE_PATH" == *"feature-matrix.md" ]]; then
  # Get content: from tool_input.content (Write) or read from disk (Edit)
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
  if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
    CONTENT=$(cat "$FILE_PATH" 2>/dev/null) || true
  fi
  if [[ -z "$CONTENT" ]]; then
    exit 0
  fi

  # Validate feature matrix rows
  # Find lines in the Findings table (start with | FF- or | <something>)
  TABLE_ROWS=$(echo "$CONTENT" | grep -E '^\|[[:space:]]*FF-' 2>/dev/null || true)

  if [[ -z "$TABLE_ROWS" ]]; then
    exit 0  # No data rows yet (template only)
  fi

  VALID_SEVERITIES="CRITICAL|HIGH|MEDIUM|LOW"
  VALID_STATUSES="DISCOVERED|TRIAGED|RESOLVED|DEFERRED|WONT_FIX"

  while IFS= read -r row; do
    # Split by | and trim whitespace from each field
    ID=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
    SEVERITY=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $8); print $8}')
    STATUS=$(echo "$row" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $9); print $9}')

    # Validate ID format (anchored)
    if [[ -n "$ID" ]] && [[ ! "$ID" =~ ^FF-[0-9]+$ ]]; then
      emit_warning "Feature matrix row has invalid ID format: '${ID}' (expected FF-NNN)"
      continue
    fi

    # Validate severity (anchored, exact match)
    if [[ -n "$SEVERITY" ]] && [[ ! "$SEVERITY" =~ ^($VALID_SEVERITIES)$ ]]; then
      emit_warning "Feature matrix row ${ID} has invalid severity: '${SEVERITY}' (expected CRITICAL|HIGH|MEDIUM|LOW)"
    fi

    # Validate status (anchored, exact match)
    if [[ -n "$STATUS" ]] && [[ ! "$STATUS" =~ ^($VALID_STATUSES)$ ]]; then
      emit_warning "Feature matrix row ${ID} has invalid status: '${STATUS}' (expected DISCOVERED|TRIAGED|RESOLVED|DEFERRED|WONT_FIX)"
    fi
  done <<< "$TABLE_ROWS"

  exit 0
fi

# Priority 2: Convention Report by path
if [[ "$FILE_PATH" == *"convention-report"* ]] || [[ "$FILE_PATH" == *"-convention-report.md" ]]; then
  # Route to convention report validation (below)
  :
else
  # Priority 3: Convention Report by content marker
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
  if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
    CONTENT=$(cat "$FILE_PATH" 2>/dev/null) || true
  fi
  if [[ -z "$CONTENT" ]] || ! echo "$CONTENT" | grep -q "## Convention Enforcement Report"; then
    exit 0  # Not a consistency artifact
  fi
fi

# --- Convention Report Validation ---

# Get content if not already loaded
if [[ -z "${CONTENT:-}" ]]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
  if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
    CONTENT=$(cat "$FILE_PATH" 2>/dev/null) || true
  fi
fi

if [[ -z "${CONTENT:-}" ]]; then
  exit 0
fi

# Check required sections
if ! echo "$CONTENT" | grep -q "### Violations Found"; then
  emit_warning "Convention report missing required section: ### Violations Found"
fi

if ! echo "$CONTENT" | grep -q "### Verdict"; then
  emit_warning "Convention report missing required section: ### Verdict"
else
  # Validate verdict value
  VERDICT=$(echo "$CONTENT" | sed -n '/^### Verdict/,/^###/p' | grep -oE '(CLEAN|VIOLATIONS|CONVENTION_DRIFT)' | head -1)
  if [[ -z "$VERDICT" ]]; then
    emit_warning "Convention report ### Verdict section present but no valid verdict value found (expected CLEAN|VIOLATIONS|CONVENTION_DRIFT)"
  fi
fi

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/validate-consistency-artifacts.sh
```

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/validate-consistency-artifacts.sh
git commit -m "feat: add validate-consistency-artifacts.sh PostToolUse hook

Advisory validation for feature-matrix.md (ID format, severity enum,
status enum per row) and convention enforcement reports (required
sections, verdict values). Always exits 0."
```

---

### Task 5: Create `validate-runner-output.sh` (SubagentStop)

**Files:**
- Create: `hooks/scripts/validate-runner-output.sh`

- [ ] **Step 1: Create the script**

Write `hooks/scripts/validate-runner-output.sh`:

```bash
#!/bin/bash
# Runner Output Validator (SubagentStop)
# Advisory: always exits 0. Emits HOOK_WARNING on stderr.
# Checks: structural completeness, convention signals, reuse compliance.
# Only fires for agents named "runner-*".

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

# Parse hook input — SubagentStop payload may differ from PostToolUse
INPUT=$(cat)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .subagent_name // empty' 2>/dev/null) || {
  emit_warning "validate-runner-output: failed to parse hook input JSON — skipping"
  exit 0
}

# Only validate runner agents
if [[ -z "$AGENT_NAME" ]] || [[ ! "$AGENT_NAME" == runner-* ]]; then
  exit 0
fi

# Get the runner's output text
OUTPUT_TEXT=$(echo "$INPUT" | jq -r '.output // .result // empty' 2>/dev/null)
if [[ -z "$OUTPUT_TEXT" ]]; then
  emit_warning "SubagentStop payload for ${AGENT_NAME} missing output text — skipping validation"
  exit 0
fi

# --- Layer 1: Structural Checks ---

# Must have at least one summary section
HAS_SUMMARY=false
for header in "## Implementation Summary" "## Investigation Summary" "## Objective" "## Design Summary" "## Problem Statement"; do
  if echo "$OUTPUT_TEXT" | grep -qF "$header"; then
    HAS_SUMMARY=true
    break
  fi
done

if [[ "$HAS_SUMMARY" == "false" ]]; then
  emit_warning "Runner ${AGENT_NAME} output missing required section — no Implementation/Investigation/Design Summary found"
fi

# Must have a status
HAS_STATUS=false
if echo "$OUTPUT_TEXT" | grep -qE '(^## Status|^\*\*Status:\*\*)'; then
  # Check status value
  STATUS_VALUE=$(echo "$OUTPUT_TEXT" | grep -oE '(DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED)' | head -1)
  if [[ -n "$STATUS_VALUE" ]]; then
    HAS_STATUS=true
  fi
fi

if [[ "$HAS_STATUS" == "false" ]]; then
  emit_warning "Runner ${AGENT_NAME} output missing Status (expected DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED)"
fi

# --- Layer 2: Convention Signals ---

# Check for known anti-patterns in code blocks within the output
# Math.random() (should use generateId)
if echo "$OUTPUT_TEXT" | grep -q 'Math\.random()'; then
  # Only warn if not in a test context
  if ! echo "$OUTPUT_TEXT" | grep -B2 'Math\.random()' | grep -qi 'test\|spec\|mock'; then
    emit_warning "Convention signal in ${AGENT_NAME} — Math.random() found, canonical source is lib/utils/id-generator.ts"
  fi
fi

# throw new Error( in storage paths (should use StorageError)
if echo "$OUTPUT_TEXT" | grep -q 'throw new Error('; then
  if echo "$OUTPUT_TEXT" | grep -B5 'throw new Error(' | grep -qi 'storage'; then
    emit_warning "Convention signal in ${AGENT_NAME} — raw Error throw in storage context, canonical source is StorageError"
  fi
fi

# alert( or from 'sonner' (should use safeToast)
if echo "$OUTPUT_TEXT" | grep -qE "(alert\(|from 'sonner'|from \"sonner\")"; then
  emit_warning "Convention signal in ${AGENT_NAME} — raw notification pattern, canonical source is safeToast"
fi

# --- Layer 3: Reuse Compliance ---

if echo "$OUTPUT_TEXT" | grep -qF "## Reuse Report"; then
  # Check if Created New items have justification
  CREATED_NEW_SECTION=$(echo "$OUTPUT_TEXT" | sed -n '/### Created New/,/^###/p')
  if [[ -n "$CREATED_NEW_SECTION" ]]; then
    # Check for empty Created New items (lines with just "- " and nothing after)
    EMPTY_ITEMS=$(echo "$CREATED_NEW_SECTION" | grep -cE '^-[[:space:]]*$' 2>/dev/null || echo "0")
    if [[ "$EMPTY_ITEMS" -gt 0 ]]; then
      emit_warning "Reuse compliance in ${AGENT_NAME} — ${EMPTY_ITEMS} Created New items lack justification"
    fi
  fi

  # Cross-reference with Existing Solutions if present
  if echo "$OUTPUT_TEXT" | grep -qF "## Existing Solutions"; then
    # Extract EXACT_MATCH items
    EXACT_MATCHES=$(echo "$OUTPUT_TEXT" | sed -n '/## Existing Solutions/,/^##/p' | grep "EXACT_MATCH" || true)
    if [[ -n "$EXACT_MATCHES" ]] && [[ -n "$CREATED_NEW_SECTION" ]]; then
      # For each exact match, check if the function name appears in Created New
      while IFS= read -r match_line; do
        # Extract function name (first column after |)
        FUNC_NAME=$(echo "$match_line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
        if [[ -n "$FUNC_NAME" ]] && echo "$CREATED_NEW_SECTION" | grep -qF "$FUNC_NAME"; then
          LOCATION=$(echo "$match_line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')
          emit_warning "Reuse compliance in ${AGENT_NAME} — runner created ${FUNC_NAME} but reuse-scout found EXACT_MATCH at ${LOCATION}"
        fi
      done <<< "$EXACT_MATCHES"
    fi
  fi
fi

exit 0
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hooks/scripts/validate-runner-output.sh
```

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/validate-runner-output.sh
git commit -m "feat: add validate-runner-output.sh SubagentStop hook

Advisory runner output validation: structural checks (required summary
+ status sections), convention signals (Math.random, raw Error,
alert/sonner), reuse compliance (Created New justification,
EXACT_MATCH cross-reference). Always exits 0."
```

---

### Task 6: Refactor guard-bead-status.sh to use common.sh

**Files:**
- Modify: `hooks/scripts/guard-bead-status.sh:46-85`

- [ ] **Step 1: Replace inline canonicalization with common.sh source**

In `hooks/scripts/guard-bead-status.sh`, replace lines 46-85 (the canonicalization block) with:

```bash
# Normalize FILE_PATH to repo-relative for git show
source "$(dirname "$0")/../lib/common.sh"

REPO_ROOT=""
REL_PATH=""
if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -n "$REPO_ROOT" ]]; then
  CANON_ROOT=$(canonicalize_path "$REPO_ROOT")
  CANON_FILE=""
  if [[ "$FILE_PATH" == /* ]]; then
    CANON_FILE=$(canonicalize_path "$FILE_PATH")
  fi

  if [[ -n "$CANON_FILE" ]]; then
    REL_PATH="${CANON_FILE#"$CANON_ROOT"/}"
    # If stripping failed (path doesn't start with root), fall back to original
    if [[ "$REL_PATH" == "$CANON_FILE" ]]; then
      REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
    fi
  elif [[ "$FILE_PATH" == /* ]]; then
    REL_PATH="${FILE_PATH#"$REPO_ROOT"/}"
  else
    REL_PATH="$FILE_PATH"
  fi
fi
```

- [ ] **Step 2: Run existing tests to verify no regression**

```bash
bash hooks/tests/test-hooks.sh
```

Expected: `PASS: 21  FAIL: 0  TOTAL: 21  ALL TESTS PASSED`

The symlink integration tests specifically verify that the canonicalization still works correctly.

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/guard-bead-status.sh
git commit -m "refactor: guard-bead-status.sh sources hooks/lib/common.sh

Replace ~30 lines of inline canonicalization with canonicalize_path()
from shared library. Behavior unchanged — existing tests verify."
```

---

### Task 7: Update hooks.json

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Replace hooks.json with updated version**

Write `hooks/hooks.json`:

```json
{
  "description": "SDLC OS enforcement hooks — schema validation, status guards, vocabulary linting, convention enforcement, and runner output validation",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-naming-convention.sh\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-aqs-artifact.sh\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/guard-bead-status.sh\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/lint-domain-vocabulary.sh\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-consistency-artifacts.sh\"",
            "timeout": 10
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-runner-output.sh\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
jq . hooks/hooks.json > /dev/null
```

Expected: Exit 0 (valid JSON).

- [ ] **Step 3: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat: register PreToolUse and SubagentStop hooks in hooks.json

Add check-naming-convention (PreToolUse on Write),
validate-consistency-artifacts (PostToolUse on Write|Edit),
and validate-runner-output (SubagentStop on all agents)."
```

---

### Task 8: Create test fixtures (11 files)

**Files:**
- Create: 11 fixture JSON files in `hooks/tests/fixtures/`

- [ ] **Step 1: Create naming hook fixtures (4 files)**

Write `hooks/tests/fixtures/naming-valid-create.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "lib/storage/payments-storage.ts",
    "content": "export function getPayments() { return []; }"
  }
}
```

Write `hooks/tests/fixtures/naming-violation-create.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "lib/storage/userPayments.ts",
    "content": "export function getPayments() { return []; }"
  }
}
```

Write `hooks/tests/fixtures/naming-unmapped-dir.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "src/newmodule/helper.ts",
    "content": "export function help() {}"
  }
}
```

Write `hooks/tests/fixtures/naming-vendor-skip.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "node_modules/some-package/index.js",
    "content": "module.exports = {};"
  }
}
```

- [ ] **Step 2: Create artifact validation fixtures (4 files)**

Write `hooks/tests/fixtures/artifact-valid-matrix.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "docs/sdlc/feature-matrix.md",
    "content": "# Feature Matrix\n\n## Findings\n\n| ID | Signal | Category | Location | Description | Completion % | Severity | Status | Type | Effort | Recommendation | Dependencies | Found | Last Seen | Owner | Notes |\n|----|--------|----------|----------|-------------|--------------|----------|--------|------|--------|----------------|--------------|-------|-----------|-------|-------|\n| FF-001 | code | stub implementation | `lib/pay.ts:42` | Stub | 85 | CRITICAL | DISCOVERED | TBD | TBD | TBD | TBD | 2026-03-25 | 2026-03-25 | feature-finder | test |\n"
  }
}
```

Write `hooks/tests/fixtures/artifact-invalid-matrix.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "docs/sdlc/feature-matrix.md",
    "content": "# Feature Matrix\n\n## Findings\n\n| ID | Signal | Category | Location | Description | Completion % | Severity | Status | Type | Effort | Recommendation | Dependencies | Found | Last Seen | Owner | Notes |\n|----|--------|----------|----------|-------------|--------------|----------|--------|------|--------|----------------|--------------|-------|-----------|-------|-------|\n| BADID | code | stub | `lib/x.ts:1` | Bad | 50 | INVALID_SEV | BOGUS_STATUS | TBD | TBD | TBD | TBD | 2026-03-25 | 2026-03-25 | finder | bad row |\n"
  }
}
```

Write `hooks/tests/fixtures/artifact-valid-convention-report.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "docs/sdlc/active/test/beads/b1-convention-report.md",
    "content": "## Convention Enforcement Report: Bead b1\n\n### Violations Found\n\n| # | Severity | Dimension | Location | Violation | Convention | Fix |\n|---|----------|-----------|----------|-----------|------------|-----|\n\n### Verdict\nCLEAN\n"
  }
}
```

Write `hooks/tests/fixtures/artifact-invalid-convention-report.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "docs/sdlc/active/test/beads/b1-convention-report.md",
    "content": "## Convention Enforcement Report: Bead b1\n\nSome text but no required sections.\n"
  }
}
```

- [ ] **Step 3: Create runner output fixtures (3 files)**

Write `hooks/tests/fixtures/runner-output-valid.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "SubagentStop",
  "agent_name": "runner-b1",
  "output": "## Implementation Summary\n\nImplemented payment processing.\n\n## Files Changed\n- `lib/storage/payments-storage.ts`\n\n## Status\n**Status:** DONE\n\n## Reuse Report\n### Reused\n- formatCurrency from lib/utils/currency-utils.ts\n### Created New\n- processRefund — Justification: no existing refund logic\n"
}
```

Write `hooks/tests/fixtures/runner-output-missing-sections.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "SubagentStop",
  "agent_name": "runner-b2",
  "output": "I made some changes to the code.\n\nHere are the files I touched:\n- lib/storage/users-storage.ts\n"
}
```

Write `hooks/tests/fixtures/runner-output-convention-signal.json`:

```json
{
  "session_id": "test",
  "hook_event_name": "SubagentStop",
  "agent_name": "runner-b3",
  "output": "## Implementation Summary\n\nAdded user ID generation.\n\n## Files Changed\n- `lib/storage/users-storage.ts`\n\nCode:\n```typescript\nconst id = Math.random().toString(36);\n```\n\n## Status\n**Status:** DONE\n"
}
```

- [ ] **Step 4: Commit all fixtures**

```bash
git add hooks/tests/fixtures/naming-*.json hooks/tests/fixtures/artifact-*.json hooks/tests/fixtures/runner-output-*.json
git commit -m "test: add 11 fixtures for enforcement hooks v2

4 naming hook fixtures (valid, violation, unmapped dir, vendor skip),
4 artifact validation fixtures (valid/invalid matrix, valid/invalid report),
3 runner output fixtures (valid, missing sections, convention signal)."
```

---

### Task 9: Update test-hooks.sh with advisory test function + 11 new tests

**Files:**
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Add `run_test_advisory` function after the existing `run_test` function**

After the closing `}` of `run_test()` (around line 30), insert:

```bash
run_test_advisory() {
  local test_name="$1"
  local hook_script="$2"
  local fixture_file="$3"
  local expect_warning="$4"  # "yes" or "no"

  # Capture exit code AND stderr separately
  local actual_exit=0
  local stderr_output
  stderr_output=$(cat "$fixture_file" | bash "$hook_script" 2>&1 1>/dev/null) || actual_exit=$?

  # Advisory hooks must ALWAYS exit 0
  if [[ "$actual_exit" -ne 0 ]]; then
    echo "  FAIL: $test_name (advisory hook exited $actual_exit, must be 0)"
    FAIL=$((FAIL + 1))
    return
  fi

  if [[ "$expect_warning" == "yes" ]]; then
    if echo "$stderr_output" | grep -q "HOOK_WARNING:"; then
      echo "  PASS: $test_name (exit 0, warning emitted)"
      PASS=$((PASS + 1))
    else
      echo "  FAIL: $test_name (exit 0, but expected HOOK_WARNING not found)"
      FAIL=$((FAIL + 1))
    fi
  else
    if echo "$stderr_output" | grep -q "HOOK_WARNING:"; then
      echo "  FAIL: $test_name (exit 0, but unexpected HOOK_WARNING: $stderr_output)"
      FAIL=$((FAIL + 1))
    else
      echo "  PASS: $test_name (exit 0, no warning)"
      PASS=$((PASS + 1))
    fi
  fi
}
```

- [ ] **Step 2: Add naming convention hook tests**

Before the `=== Results ===` section, add:

```bash
echo ""
echo "=== Naming Convention Hook Tests (advisory) ==="

run_test_advisory "valid: kebab-case in mapped dir" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-valid-create.json" "no"

run_test_advisory "warning: camelCase in kebab-case dir" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-violation-create.json" "yes"

run_test_advisory "warning: unmapped source directory" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-unmapped-dir.json" "yes"

run_test_advisory "skip: vendor path (node_modules)" \
  "$HOOKS_DIR/check-naming-convention.sh" \
  "$FIXTURES_DIR/naming-vendor-skip.json" "no"
```

- [ ] **Step 3: Add artifact validation hook tests**

```bash
echo ""
echo "=== Consistency Artifact Validation Tests (advisory) ==="

run_test_advisory "valid: feature matrix with correct row" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-valid-matrix.json" "no"

run_test_advisory "warning: feature matrix with invalid ID/severity/status" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-invalid-matrix.json" "yes"

run_test_advisory "valid: convention report with required sections" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-valid-convention-report.json" "no"

run_test_advisory "warning: convention report missing sections" \
  "$HOOKS_DIR/validate-consistency-artifacts.sh" \
  "$FIXTURES_DIR/artifact-invalid-convention-report.json" "yes"
```

- [ ] **Step 4: Add runner output hook tests**

```bash
echo ""
echo "=== Runner Output Validation Tests (advisory) ==="

run_test_advisory "valid: runner output with all sections" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-valid.json" "no"

run_test_advisory "warning: runner output missing sections" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-missing-sections.json" "yes"

run_test_advisory "warning: runner output with convention signal" \
  "$HOOKS_DIR/validate-runner-output.sh" \
  "$FIXTURES_DIR/runner-output-convention-signal.json" "yes"
```

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test-hooks.sh
git commit -m "test: add run_test_advisory function + 11 advisory hook tests

Tests check both exit code (must be 0) and stderr content (HOOK_WARNING
presence/absence). Covers naming convention, artifact validation,
and runner output hooks."
```

---

### Task 10: Run full test suite and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run the full test suite**

```bash
bash hooks/tests/test-hooks.sh
```

Expected output should include all test sections:
- `=== Bead Status Guard Tests ===` (5 pass)
- `=== Bead Status Guard Integration Tests ===` (3 pass)
- `=== AQS Artifact Validator Tests ===` (5 pass)
- `=== Domain Vocabulary Linter Tests ===` (3 pass)
- `=== Naming Convention Hook Tests ===` (4 pass)
- `=== Consistency Artifact Validation Tests ===` (4 pass)
- `=== Runner Output Validation Tests ===` (3 pass)

Expected: `PASS: 32  FAIL: 0  TOTAL: 32  ALL TESTS PASSED`

Note: The naming convention tests (valid/violation) depend on a Convention Map existing at the repo root. If no Convention Map exists in the test environment, the naming check exits 0 silently (by design). The violation test fixture must be run in a context where a Convention Map with `lib/storage/` → `kebab-case` exists, OR the test should be adjusted to check that the hook correctly exits 0 (no-op) when no map exists. If tests fail due to missing Convention Map, create a test Convention Map in the integration test setup (similar to the symlink integration test pattern).

- [ ] **Step 2: If any tests fail, fix and re-run**

Fix the specific failure, commit the fix, then re-run the full suite until 32/32 pass.

- [ ] **Step 3: Final verification commit if needed**

```bash
git add -A
git commit -m "fix: address test failures from enforcement hooks v2

[describe specific fixes]"
```
