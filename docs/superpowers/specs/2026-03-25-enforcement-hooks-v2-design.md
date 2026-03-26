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
| Enforcement mode | **Advisory (non-blocking)** — all hooks exit 0, emit `HOOK_WARNING:` on stderr | Avoids false-positive frustration; agents see warnings and act on them |
| Script split | **3 scripts by event type** + shared lib | One per event boundary (PreToolUse, PostToolUse, SubagentStop); shared lib for DRY |
| Convention Map parsing | **Markdown SSOT with stable markers** | No JSON sidecar; stable table headers (`\| Directory \|`) make bash parsing deterministic |
| Scope filtering | **Mapped dirs + known source dirs** for naming; vendor paths always skipped | Reduces noise while catching real issues |
| Error handling | **Trap/fallback to exit 0** on parse errors | Advisory guarantee — even malformed input never blocks |

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

**`read_convention_map_section(section_name)`**
Parse `docs/sdlc/convention-map.md` for a `### {section_name}` table. Reads lines from the header until the next `###` or EOF, filtering for table data rows (lines starting with `|` that aren't the header separator `|---|`). Returns rows as lines on stdout. Returns empty if map doesn't exist or section not found.

**`get_repo_root()`**
Canonicalized repo root via `git rev-parse --show-toplevel` + `canonicalize_path`.

### Advisory Guarantee

All scripts that source `common.sh` get a trap installed:

```bash
trap 'exit 0' ERR
set -uo pipefail  # Note: -e intentionally omitted; trap handles errors
```

This ensures that even on parse errors, malformed JSON, or missing files, the hook exits 0 with no output rather than blocking.

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
4. Parse File Naming section from Convention Map via read_convention_map_section
5. Extract file's directory and basename
6. Look up directory in Convention Map table:
   a. FOUND → check basename against recorded convention via regex:
      - kebab-case: ^[a-z][a-z0-9]*(-[a-z0-9]+)*\.[a-z]+$
      - PascalCase: ^[A-Z][a-zA-Z0-9]*\.[a-z]+$
      - camelCase: ^[a-z][a-zA-Z0-9]*\.[a-z]+$
      - snake_case: ^[a-z][a-z0-9]*(_[a-z0-9]+)*\.[a-z]+$
      If mismatch → emit_warning "File naming violation — {file} uses {detected} but {directory} convention is {expected}"
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

Routes to the correct validator by file path and content:

| Pattern | Validator |
|---------|-----------|
| `docs/sdlc/feature-matrix.md` | Feature Matrix schema |
| Content contains `## Convention Enforcement Report` | Convention Report schema |
| Neither matches | exit 0 (skip) |

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

  local stderr_output
  stderr_output=$(cat "$fixture_file" | bash "$hook_script" 2>&1 1>/dev/null || true)
  local actual_exit=$?

  # Advisory hooks must always exit 0
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

For `read_convention_map_section` to parse reliably, the Convention Map must follow this format:

```markdown
### File Naming
| Directory | Convention | Evidence | Confidence |
|-----------|-----------|----------|------------|
| lib/storage/ | kebab-case-storage.ts | payments-storage.ts, users-storage.ts | Verified (5/5 files) |
```

The contract:
1. Section headers are `### {Dimension Name}` (exact match after `### `)
2. Tables start with a header row containing `| Directory |` (for File Naming) or the relevant first column name
3. Separator row `|---|` immediately follows the header
4. Data rows follow the separator, one per line starting with `|`
5. Section ends at the next `###` heading or EOF

The `convention-scanner` agent already produces this format. This contract is documented here so both the scanner and the hook parser agree on the structure.

---

## Implementation Order

1. `hooks/lib/common.sh` — shared library (no dependencies)
2. `hooks/scripts/check-naming-convention.sh` — PreToolUse hook (depends on common.sh)
3. `hooks/scripts/validate-consistency-artifacts.sh` — PostToolUse hook (depends on common.sh)
4. `hooks/scripts/validate-runner-output.sh` — SubagentStop hook (depends on common.sh)
5. Refactor `hooks/scripts/guard-bead-status.sh` — source common.sh (depends on step 1)
6. Update `hooks/hooks.json` — register new hooks
7. Create 11 test fixtures
8. Update `hooks/tests/test-hooks.sh` — add `run_test_advisory` + 11 new test cases
9. Run full test suite — verify 32/32 pass (21 existing + 11 new)
