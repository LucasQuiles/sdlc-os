# SDLC-OS Enforcement Hooks v2 — Design Spec

**Date:** 2026-03-25
**Status:** Approved (pending implementation)
**Plugin:** sdlc-os v4+
**Scope:** 3 new hook scripts, 1 shared library, 11 test fixtures, 2 updated files

---

## Problem Statement

The SDLC-OS plugin has 6 new agents (convention-scanner, convention-enforcer, normalizer, gap-analyst, feature-finder, feature-finisher) that expect certain artifacts and conventions to be maintained. The existing 3 hooks only enforce AQS artifact schemas, bead status transitions, and domain vocabulary. There is no enforcement at the PreToolUse boundary (before files are written), no validation of the new consistency artifacts (feature matrix, convention reports), and no output validation when runners complete.

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Enforcement mode | **Advisory (non-blocking) for NEW hooks only** — new hooks exit 0, emit `HOOK_WARNING:` on stderr. Existing blocking hooks (AQS validator, bead guard, vocab linter) retain their exit 2 behavior. | Avoids false-positive frustration for new enforcement while preserving existing strict guards |
| Script split | **3 scripts by event type** + shared lib | One per event boundary (PreToolUse, PostToolUse, SubagentStop); shared lib for DRY |
| Convention Map parsing | **Markdown SSOT with stable markers** | No JSON sidecar; stable table headers (`\| Directory \|`) make bash parsing deterministic |
| Scope filtering | **Mapped dirs + known source dirs** for naming; vendor paths always skipped | Reduces noise while catching real issues |
| Error handling | **Trap/fallback to exit 0 in advisory scripts only** — common.sh provides `install_advisory_trap` function that new scripts call explicitly. Existing blocking scripts do NOT call it. | Advisory guarantee for new hooks; existing blocking semantics unchanged |

---

## Architecture

```
hooks/
├── hooks.json                              # Updated — adds PreToolUse + SubagentStop
├── lib/
│   └── common.sh                           # Shared utilities
├── scripts/
│   ├── check-naming-convention.sh          # NEW — PreToolUse on Write
│   ├── validate-consistency-artifacts.sh   # NEW — PostToolUse on Write|Edit
│   ├── validate-runner-output.sh           # NEW — SubagentStop
│   ├── guard-bead-status.sh               # UPDATED — sources lib/common.sh
│   ├── validate-aqs-artifact.sh           # Unchanged
│   └── lint-domain-vocabulary.sh          # Unchanged
└── tests/
    ├── test-hooks.sh                       # Updated — 11 new test cases
    └── fixtures/
        ├── ...existing 18 fixtures...
        └── ...11 new fixtures...
```

---

## Shared Library: `hooks/lib/common.sh`

Sourced by all new scripts and refactored into `guard-bead-status.sh`.

### Functions

**`canonicalize_path(path)`**
Resolve symlinks via `realpath` with `pwd -P` fallback. Extracted from the symlink fix in `guard-bead-status.sh` (commit `226dbb7`).

**`emit_warning(message)`**
Output `HOOK_WARNING: ${message}` to stderr. Always return 0. This is the single warning format all hooks use — agents parse for the `HOOK_WARNING:` prefix.

**`is_vendor_path(path)`**
Return 0 (true) if path matches skip patterns: `node_modules/`, `dist/`, `build/`, `.git/`, `__pycache__/`, `.next/`, `vendor/`, `.cache/`. Called early in every hook to short-circuit.

**`read_convention_map_patterns()`**
Parse ALL dimension sections from the Convention Map. The scanner produces bullet-format sections with explicit machine-parseable fields:
```
### File Naming
- **Convention:** kebab-case
- **Scope:** lib/storage/, lib/utils/
- **Confidence:** Verified 5/5
- **Evidence:**
  - `lib/storage/payments-storage.ts`
```
The function:
1. Reads `docs/sdlc/convention-map.md`
2. For each `### {Dimension}` section, extracts `**Convention:**` and `**Scope:**` values
3. Returns a list of `scope_directory|convention_keyword` pairs (one per line)
4. Convention keywords are from a fixed vocabulary: `kebab-case`, `PascalCase`, `camelCase`, `snake_case`, `UPPER_SNAKE_CASE`
5. Returns empty if map doesn't exist or no parseable entries found

Used by the naming hook to build the directory→convention lookup table.

**`get_repo_root()`**
Canonicalized repo root via `git rev-parse --show-toplevel` + `canonicalize_path`.

### Advisory Script Pattern (explicit control flow, no ERR trap)

Advisory scripts use explicit control flow with a guaranteed `exit 0` at the end. No `trap 'exit 0' ERR` — that hides useful failures and makes debugging impossible. Instead:

1. Do NOT use `set -e` (no errexit — handle errors explicitly)
2. Use `set -uo pipefail` (catch unset vars and pipe failures for debugging)
3. Wrap risky operations in `if/then` or `|| true` explicitly at the call site
4. If a parse error or unexpected state occurs, `emit_warning` describing the issue and continue
5. Script ends with `exit 0` unconditionally

**Advisory script template:**
```bash
#!/bin/bash
set -uo pipefail

source "$(dirname "$0")/../lib/common.sh"

# Parse input — if jq fails, warn and exit clean
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
  emit_warning "Failed to parse hook input JSON — skipping"
  exit 0
}

# ... check logic with explicit error handling ...

exit 0
```

**Existing blocking scripts** source common.sh for utilities and keep their own `set -euo pipefail` + `exit 2` behavior unchanged:
```bash
#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"
# ... blocking logic, exit 2 on violation ...
```

This keeps advisory hooks debuggable (warnings on unexpected states instead of silent swallowing) while guaranteeing they never block.

---

## Hook 1: `check-naming-convention.sh`

**Event:** PreToolUse on Write
**Timeout:** 5 seconds
**Exit:** Always 0

### Logic

```
1. Parse file_path from hook input JSON (jq -r '.tool_input.file_path // empty')
2. If empty or is_vendor_path → exit 0 (silent skip)
3. Check if docs/sdlc/convention-map.md exists → if not, exit 0 (no map = no enforcement)
4. Build directory→convention lookup via read_convention_map_patterns
   (returns lines of "scope_directory|convention_keyword" pairs)
5. Extract file's directory and basename
6. Match file's directory against lookup (longest prefix match):
   a. FOUND → strip known suffixes first, then check stem against convention regex:
      **Suffix stripping:** Remove known multi-dot suffixes before checking the stem:
      `.test.ts`, `.test.tsx`, `.spec.ts`, `.spec.tsx`, `.d.ts`, `.stories.tsx`,
      `.module.css`, `.module.scss`, `.config.ts`, `.config.js`
      If none match, strip the final `.ext` only.
      The CHECK applies to the remaining stem (e.g., `payments-storage` from `payments-storage.test.ts`).

      **Stem regexes (anchored):**
      - kebab-case: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`
      - PascalCase: `^[A-Z][a-zA-Z0-9]*$`
      - camelCase: `^[a-z][a-zA-Z0-9]*$`
      - snake_case: `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`

      **Special cases that always pass (no warning):**
      - `index.ts`, `index.js`, `index.d.ts` — universal entry point convention
      - `README.md`, `CHANGELOG.md`, `LICENSE` — standard repo files
      - Files starting with `.` (dotfiles) — config conventions vary
      - `__tests__/`, `__mocks__/` directory contents — framework conventions override project conventions

      If mismatch → emit_warning "File naming violation — {file} stem '{stem}' uses {detected} but {directory} convention is {expected}"
   b. NOT FOUND but directory is a known source directory (lib/, app/, components/,
      src/, hooks/, services/, pages/, routes/, api/) →
      emit_warning "Unmapped source directory — {directory} has no Convention Map entry. Consider running /normalize."
   c. NOT FOUND and not a source directory → exit 0 (silent skip)
```

### Convention Detection

To determine what casing a filename uses, test against the regex patterns above in order. First match wins. If no match (unusual filename), report as "non-standard".

---

## Hook 2: `validate-consistency-artifacts.sh`

**Event:** PostToolUse on Write|Edit
**Timeout:** 10 seconds
**Exit:** Always 0

### Path Routing

Routes to the correct validator by file path first, then content fallback:

| Priority | Pattern | Validator |
|----------|---------|-----------|
| 1 | `file_path` ends with `feature-matrix.md` | Feature Matrix schema |
| 2 | `file_path` contains `convention-report` or ends with `-convention-report.md` | Convention Report schema |
| 3 | Content (from `tool_input.content` for Write, or read from disk for Edit) contains `## Convention Enforcement Report` | Convention Report schema |
| 4 | Neither matches | exit 0 (skip) |

**Edit event handling:** For Edit tool calls, `tool_input.content` may be absent (Edit provides `old_string`/`new_string` instead). In this case, read the file from disk at `file_path` to check content markers. If the file doesn't exist yet or can't be read, fall back to path-only routing.

### Feature Matrix Validation

Parse the `## Findings` table. For each data row:

- **ID format:** Must match `^FF-[0-9]+$` (anchored regex). Warn if not.
- **Severity:** Must be exactly one of: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Warn if not.
- **Status:** Must be exactly one of: `DISCOVERED`, `TRIAGED`, `RESOLVED`, `DEFERRED`, `WONT_FIX`. Warn if not.
- **Required columns present:** ID, Signal, Category, Location, Description, Severity, Status must all be non-empty. Warn on empty required fields.

Emit one warning per invalid row, not per invalid field (avoid warning storms).

### Convention Report Validation

Check for required sections:

- `### Violations Found` — must exist and contain a table (at least a header row with `| # |`)
- `### Verdict` — must exist
- Verdict value must be one of: `CLEAN`, `VIOLATIONS`, `CONVENTION_DRIFT` (anchored match)

Emit one warning per missing section.

---

## Hook 3: `validate-runner-output.sh`

**Event:** SubagentStop
**Timeout:** 15 seconds
**Exit:** Always 0

### Payload Check

The SubagentStop hook input may include different fields than PostToolUse. The script must:

1. Attempt to parse agent name and output text from the input JSON
2. If parsing fails or fields are missing → `emit_warning "SubagentStop payload missing expected fields — skipping validation"` and exit 0
3. If agent name does NOT match `runner-*` pattern → exit 0 (skip sentinels, guppies, scouts, etc.)

### Three Check Layers

**Layer 1: Structural checks**

Runner output must contain at least one of these section headers (varies by bead type):
- `## Implementation Summary`
- `## Investigation Summary` / `## Objective`
- `## Design Summary` / `## Problem Statement`

AND must contain:
- `## Status` or a `**Status:**` line with one of: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`

Warn on missing sections: `HOOK_WARNING: Runner output missing required section — no Implementation/Investigation/Design Summary found`

**Layer 2: Convention signals**

If `docs/sdlc/convention-map.md` exists:
- Scan for filenames in "Files changed" / "Files Created" sections → check against Convention Map (same logic as Hook 1 but applied to reported filenames, not the Write target)

Scan for known anti-patterns from `references/fitness-functions.md`:
- `Math.random()` in non-test code paths → warn "Convention signal — Math.random() found, canonical source is lib/utils/id-generator.ts"
- `throw new Error(` in storage-layer file paths → warn "Convention signal — raw Error throw, canonical source is StorageError"
- `alert(` or `from 'sonner'` → warn "Convention signal — raw notification, canonical source is safeToast"

These are heuristic grep checks on the runner's output text, not AST analysis. False positives are acceptable since they're advisory.

**Layer 3: Reuse compliance**

If runner output contains `## Reuse Report`:
- Check that `### Created New` items each have text after them (not empty)
- If runner output also contains `## Existing Solutions` (from reuse-scout injection):
  - Extract items classified as `EXACT_MATCH` from the Existing Solutions section
  - Check if any of those items appear in the `### Created New` section
  - If match → `HOOK_WARNING: Reuse compliance — runner created new code for {item} but reuse-scout found EXACT_MATCH at {location}`

---

## Updated hooks.json

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

---

## Refactor: guard-bead-status.sh

Replace the inline path canonicalization logic (lines 47-60) with:

```bash
source "$(dirname "$0")/../lib/common.sh"

# ... existing logic ...

if [[ -n "$REPO_ROOT" ]]; then
  CANON_ROOT=$(canonicalize_path "$REPO_ROOT")
  if [[ "$FILE_PATH" == /* ]]; then
    CANON_FILE=$(canonicalize_path "$FILE_PATH")
  fi
  # ... rest of relative path derivation using CANON_ROOT/CANON_FILE ...
fi
```

This removes ~20 lines of inline canonicalization and replaces with a 2-line call to the shared function.

---

## Test Coverage

### New Fixtures (11)

| Fixture | Script | Expected | Assertion |
|---------|--------|----------|-----------|
| `naming-valid-create.json` | check-naming-convention | exit 0 | No HOOK_WARNING on stderr |
| `naming-violation-create.json` | check-naming-convention | exit 0 | stderr contains "File naming violation" |
| `naming-unmapped-dir.json` | check-naming-convention | exit 0 | stderr contains "Unmapped source directory" |
| `naming-vendor-skip.json` | check-naming-convention | exit 0 | No HOOK_WARNING on stderr |
| `artifact-valid-matrix.json` | validate-consistency-artifacts | exit 0 | No HOOK_WARNING |
| `artifact-invalid-matrix.json` | validate-consistency-artifacts | exit 0 | stderr contains "HOOK_WARNING" |
| `artifact-valid-convention-report.json` | validate-consistency-artifacts | exit 0 | No HOOK_WARNING |
| `artifact-invalid-convention-report.json` | validate-consistency-artifacts | exit 0 | stderr contains "HOOK_WARNING" |
| `runner-output-valid.json` | validate-runner-output | exit 0 | No HOOK_WARNING |
| `runner-output-missing-sections.json` | validate-runner-output | exit 0 | stderr contains "missing required section" |
| `runner-output-convention-signal.json` | validate-runner-output | exit 0 | stderr contains "Convention signal" |

### Test Runner Updates

The `run_test` function needs a variant that checks stderr content:

```bash
run_test_advisory() {
  local test_name="$1"
  local hook_script="$2"
  local fixture_file="$3"
  local expect_warning="$4"  # "yes" or "no"

  # Capture exit code AND stderr separately — don't mask with || true
  local actual_exit=0
  local stderr_output
  stderr_output=$(cat "$fixture_file" | bash "$hook_script" 2>&1 1>/dev/null) || actual_exit=$?

  # Advisory hooks must ALWAYS exit 0 — a non-zero exit is a test failure
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

### Existing Tests

All 21 existing tests continue to pass unchanged. The `guard-bead-status.sh` refactor to use `common.sh` must produce identical behavior — verified by the existing fixture tests + symlink integration tests.

---

## Convention Map Stable Markers Contract

The `convention-scanner` agent produces bullet-format sections with explicit machine-parseable fields. For `read_convention_map_patterns` to parse reliably, the Convention Map must use `**Convention:**` and `**Scope:**` fields (not free-form prose in `**Pattern:**`):

```markdown
### File Naming
- **Convention:** kebab-case
- **Scope:** lib/storage/, lib/utils/, lib/services/
- **Confidence:** Verified 5/5
- **Evidence:**
  - `lib/storage/payments-storage.ts`
  - `lib/storage/users-storage.ts`
- **Notes:** optional

### Function/Variable Naming
- **Convention:** camelCase
- **Scope:** lib/
- **Confidence:** Verified 8/8
- **Evidence:**
  - `generateId()` in lib/utils/id-generator.ts

### Component Structure
- **Convention:** PascalCase
- **Scope:** components/, app/
- **Confidence:** Verified 12/12
- **Evidence:**
  - `components/UserProfile.tsx`
```

The contract:
1. Section headers are `### {Dimension Name}` (exact match after `### `)
2. **`Convention:`** field is REQUIRED — must be one of the fixed vocabulary keywords: `kebab-case`, `PascalCase`, `camelCase`, `snake_case`, `UPPER_SNAKE_CASE`. This is what hooks match against. No free-form text.
3. **`Scope:`** field is REQUIRED — comma-separated list of directory prefixes this convention applies to. Trailing `/` optional. This is what hooks use for directory lookup.
4. `Confidence:` and `Evidence:` are informational — hooks do not parse them
5. Section ends at the next `###` heading, `---` separator, or EOF
6. The `## Inconsistencies` section at the bottom may use table format for conflicts — this is the only table in the map

**Convention-scanner update required:** The scanner agent's output template must be updated to produce `**Convention:**` and `**Scope:**` fields instead of the current `**Pattern:**` free-form text. This is a prerequisite for the hooks to work reliably.

---

## Implementation Order

1. Update `agents/convention-scanner.md` — change output template from `**Pattern:**` to `**Convention:**` + `**Scope:**` fields (prerequisite for hooks)
2. `hooks/lib/common.sh` — shared library (no dependencies)
3. `hooks/scripts/check-naming-convention.sh` — PreToolUse hook (depends on common.sh + scanner update)
4. `hooks/scripts/validate-consistency-artifacts.sh` — PostToolUse hook (depends on common.sh)
5. `hooks/scripts/validate-runner-output.sh` — SubagentStop hook (depends on common.sh)
6. Refactor `hooks/scripts/guard-bead-status.sh` — source common.sh for canonicalize_path (depends on step 2)
7. Update `hooks/hooks.json` — register new hooks
8. Create 11 test fixtures
9. Update `hooks/tests/test-hooks.sh` — add `run_test_advisory` + 11 new test cases
10. Run full test suite — verify 32/32 pass (21 existing + 11 new)
