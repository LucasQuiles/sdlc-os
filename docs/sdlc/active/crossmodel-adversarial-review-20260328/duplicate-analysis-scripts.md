# Duplicate & Contradiction Analysis: scripts/*.sh + hooks/scripts/*.sh

Analyzed: 5 crossmodel scripts + 9 hook scripts + 1 shared lib (15 files total).
Date: 2026-03-28

---

## Executive Summary

- **5 duplicate patterns** found across script groups, 3 at HIGH confidence.
- **2 contradictory patterns** found that differ in ways that could cause real bugs.
- `hooks/lib/common.sh` already provides path helpers — but no JSON helpers, no content-extraction helpers, and zero crossmodel scripts source it at all.
- A `scripts/lib/common.sh` does not exist. All five crossmodel scripts inline their own helpers independently.

---

## Duplicated Patterns

---

### DUP-001 — `jq`-with-grep-fallback for extracting a single field from stdin JSON

**Confidence: HIGH**

**Scripts affected:**
- `hooks/scripts/guard-bead-status.sh` (line 10)
- `hooks/scripts/lint-domain-vocabulary.sh` (line 10)
- `hooks/scripts/validate-aqs-artifact.sh` (line 12)
- `hooks/scripts/validate-consistency-artifacts.sh` (line 10)
- `hooks/scripts/validate-decision-trace.sh` (line 10)
- `hooks/scripts/validate-hardening-report.sh` (line 10)
- `hooks/scripts/validate-runner-output.sh` (line 11–14)
- `hooks/scripts/validate-safety-constraints.sh` (line 11)
- `hooks/scripts/check-naming-convention.sh` (line 10–13)

**What's duplicated:**

Every hook script opens with a near-identical block to extract `FILE_PATH` from `$INPUT`:

```bash
# Variant A — blocking scripts (no error handler):
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Variant B — advisory scripts (with error handler and emit_warning):
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
  emit_warning "...: failed to parse hook input JSON — skipping"
  exit 0
}
```

`validate-runner-output.sh` uses a slightly different field set (`.agent_name // .subagent_name // empty`) but the structural idiom is identical.

None of these have a grep fallback for this particular extraction — they all require `jq`. If `jq` is absent, Variant A silently sets `FILE_PATH=""` and passes through; Variant B emits a warning. This is an inconsistency within the group (see CON-001 below).

**What could be extracted:**

```bash
# Proposed: hooks/lib/common.sh
# read_hook_input_field FIELD [--advisory HOOK_NAME]
# Reads from stdin, extracts .tool_input.FIELD // empty via jq.
# With --advisory: on jq failure, emits warning and exits 0.
# Without --advisory: on jq failure, silent (returns empty string).
read_hook_input_field() { ... }
```

**Recommendation: EXTRACT to `hooks/lib/common.sh`**

---

### DUP-002 — Content extraction pattern (tool_input.content → fallback to disk read)

**Confidence: HIGH**

**Scripts affected:**
- `hooks/scripts/guard-bead-status.sh` (lines 22–25)
- `hooks/scripts/validate-aqs-artifact.sh` (lines 24–31)
- `hooks/scripts/validate-consistency-artifacts.sh` (lines 19–23, 62–68, 74–79)
- `hooks/scripts/validate-decision-trace.sh` (lines 31–34)
- `hooks/scripts/validate-hardening-report.sh` (lines 21–24)
- `hooks/scripts/validate-safety-constraints.sh` (lines 26–29)
- `hooks/scripts/lint-domain-vocabulary.sh` (lines 17–20)

**What's duplicated:**

All seven scripts that need file content use the same two-step pattern:

```bash
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
if [[ -z "$CONTENT" ]] && [[ -f "$FILE_PATH" ]]; then
  CONTENT=$(cat "$FILE_PATH")
fi
```

`validate-consistency-artifacts.sh` repeats this pattern **three times** within the same script (lines 19–23 for feature-matrix, lines 62–68 and 74–79 for convention report), which is the worst instance.

The only variation is in error-handling discipline:
- Most scripts use bare `cat "$FILE_PATH"` (will hard-fail on read error under `set -euo pipefail`).
- `validate-consistency-artifacts.sh` uses `cat "$FILE_PATH" 2>/dev/null) || true` (resilient).

This inconsistency means the same notional operation can silently pass or hard-fail depending on which script you're in.

**What could be extracted:**

```bash
# Proposed: hooks/lib/common.sh
# read_tool_content INPUT FILE_PATH
# Prints content from tool_input.content, falling back to disk read.
# Always safe — never hard-fails.
read_tool_content() {
  local input="$1"
  local file_path="$2"
  local content
  content=$(printf '%s' "$input" | jq -r '.tool_input.content // empty' 2>/dev/null || true)
  if [[ -z "$content" ]] && [[ -f "$file_path" ]]; then
    content=$(cat "$file_path" 2>/dev/null || true)
  fi
  printf '%s' "$content"
}
```

**Recommendation: EXTRACT to `hooks/lib/common.sh`**

---

### DUP-003 — Session name injection guard (alphanumeric/hyphen/underscore validation)

**Confidence: HIGH**

**Scripts affected:**
- `scripts/crossmodel-grid-down.sh` (lines 38–42)
- `scripts/crossmodel-grid-up.sh` (lines 36–40)

**What's duplicated:**

Both scripts contain an identical block:

```bash
# crossmodel-grid-down.sh lines 38–42:
if [[ "$SESSION_NAME" =~ [^a-zA-Z0-9_-] ]]; then
  printf 'GRID_DOWN_FAIL: session name contains invalid characters: %s\n' "$SESSION_NAME" >&2
  exit 2
fi

# crossmodel-grid-up.sh lines 36–40:
if [[ "$SESSION_NAME" =~ [^a-zA-Z0-9_-] ]]; then
  printf 'GRID_UP_FAIL: session name contains invalid characters: %s\n' "$SESSION_NAME" >&2
  exit 2
fi
```

The regex is identical. The only difference is the prefix in the error message (`GRID_DOWN_FAIL` vs `GRID_UP_FAIL`). Both scripts also validate that `--session-name` is non-empty immediately before this check.

`crossmodel-preflight.sh` searches for conflicting sessions but does NOT validate the session name format — creating a gap where a malformed name could pass preflight but then fail grid-up.

**What could be extracted:**

```bash
# Proposed: scripts/lib/common.sh (new file)
# validate_session_name NAME CONTEXT
# CONTEXT is used in the error prefix (e.g. "GRID_DOWN_FAIL", "GRID_UP_FAIL")
validate_session_name() {
  local name="$1"
  local context="${2:-FAIL}"
  if [[ -z "$name" ]]; then
    printf 'Missing required session name\n' >&2
    exit 2
  fi
  if [[ "$name" =~ [^a-zA-Z0-9_-] ]]; then
    printf '%s: session name contains invalid characters: %s\n' "$context" "$name" >&2
    exit 2
  fi
}
```

**Recommendation: EXTRACT to a new `scripts/lib/common.sh`**

---

### DUP-004 — `realpath`-with-fallback path canonicalization

**Confidence: MEDIUM**

**Scripts affected:**
- `hooks/lib/common.sh` — `canonicalize_path()` function (lines 9–27)
- `scripts/crossmodel-verify-artifact.sh` (lines 70–77)

**What's duplicated:**

`common.sh` defines `canonicalize_path()` which uses `realpath` with a `cd`/`pwd -P` fallback. `crossmodel-verify-artifact.sh` inlines an equivalent pattern without sourcing `common.sh`:

```bash
# crossmodel-verify-artifact.sh lines 70–77 (inline, not using common.sh):
if command -v realpath &> /dev/null; then
  CANON_ARTIFACT=$(realpath "$ARTIFACT_PATH" 2>/dev/null || echo "$ARTIFACT_PATH")
  CANON_PROJECT=$(realpath "$PROJECT_DIR" 2>/dev/null || echo "$PROJECT_DIR")
else
  CANON_ARTIFACT=$(cd "$(dirname "$ARTIFACT_PATH")" 2>/dev/null && pwd)/$(basename "$ARTIFACT_PATH")
  CANON_PROJECT=$(cd "$PROJECT_DIR" 2>/dev/null && pwd)
fi
```

The difference: `common.sh`'s version uses `pwd -P` (resolves symlinks); `verify-artifact.sh`'s fallback uses plain `pwd` (does not resolve symlinks). This means the containment check on line 80 (`${CANON_ARTIFACT#"${CANON_PROJECT}/"}`) could give a false "PATH_VIOLATION" if the artifact path includes a symlink component that `PROJECT_DIR` does not.

All five crossmodel scripts are entirely standalone — none source `hooks/lib/common.sh` or each other. There is no `scripts/lib/` at all.

**Recommendation: EXTRACT — have `crossmodel-verify-artifact.sh` source a `scripts/lib/common.sh` that exposes `canonicalize_path`, or accept a dependency on `hooks/lib/common.sh` for the path helpers.**

---

### DUP-005 — SHA-256 checksum: `sha256sum`-or-`shasum` fallback

**Confidence: MEDIUM**

**Scripts affected:**
- `scripts/crossmodel-verify-artifact.sh` (lines 152–159)

**Context:**

This pattern appears in only one script today, but it is a canonical "macOS vs Linux" portability idiom that is highly likely to be needed by any future script that validates artifact integrity. The pattern:

```bash
if command -v sha256sum &> /dev/null; then
  CHECKSUM=$(sha256sum "$ARTIFACT_PATH" | awk '{print $1}')
elif command -v shasum &> /dev/null; then
  CHECKSUM=$(shasum -a 256 "$ARTIFACT_PATH" | awk '{print $1}')
else
  CHECKSUM="unavailable"
fi
```

This is not yet duplicated, but it is a prime extraction candidate for a `scripts/lib/common.sh` given the crossmodel artifact pipeline will likely compute checksums in multiple places (e.g., session journal could record expected checksums per worker output).

**Recommendation: EXTRACT proactively to `scripts/lib/common.sh`**

---

## Contradictory Patterns

---

### CON-001 — Inconsistent `jq`-absence handling across hook scripts

**Confidence: HIGH**

**Scripts affected (advisory mode — sources common.sh):**
- `hooks/scripts/check-naming-convention.sh`
- `hooks/scripts/validate-consistency-artifacts.sh`
- `hooks/scripts/validate-runner-output.sh`

**Scripts affected (blocking mode — no common.sh, no fallback):**
- `hooks/scripts/guard-bead-status.sh`
- `hooks/scripts/lint-domain-vocabulary.sh`
- `hooks/scripts/validate-aqs-artifact.sh`
- `hooks/scripts/validate-decision-trace.sh`
- `hooks/scripts/validate-hardening-report.sh`
- `hooks/scripts/validate-safety-constraints.sh`

**The contradiction:**

Advisory scripts wrap the `jq` call with `2>/dev/null || { emit_warning "...: failed to parse hook input — skipping"; exit 0; }`. Blocking scripts do not — they pipe through `jq` without any guard.

Under `set -euo pipefail`, if `jq` is absent, `$(echo "$INPUT" | jq -r '...')` will fail and the script will exit with a non-zero code — which is `exit 1` or `exit 2` depending on shell behavior, not a controlled `exit 0`. For blocking hooks (exit 2 = block), this means **a missing `jq` binary silently blocks every Write/Edit operation** with a confusing non-message. The user sees a hook failure but no actionable reason.

```bash
# validate-aqs-artifact.sh line 12 — will hard-fail silently on jq-absent machine:
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# check-naming-convention.sh line 10–13 — gracefully skips on jq-absent machine:
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || {
  emit_warning "check-naming-convention: failed to parse hook input JSON — skipping"
  exit 0
}
```

**Why this can cause bugs:**

The blocking scripts have no documented precondition that `jq` must be present. If a developer installs the plugin in a minimal environment (common in CI), all `Write`/`Edit` calls will be blocked with no explanation.

`crossmodel-health.sh` handles this correctly — it wraps the entire jq path with `if command -v jq &> /dev/null; then ... else ... fi`. The hook scripts have no equivalent guard.

**Recommendation: STANDARDIZE — all hook scripts should check for jq at the top and either emit a warning + exit 0 (advisory) or fail with a clear message (blocking). A `require_jq` helper in `hooks/lib/common.sh` would enforce this.**

---

### CON-002 — `cat` hard-fail vs `cat ... || true` for disk fallback reads

**Confidence: MEDIUM**

**Scripts affected:**
- `guard-bead-status.sh` line 24: `CONTENT=$(cat "$FILE_PATH")`
- `validate-decision-trace.sh` line 33: `CONTENT=$(cat "$FILE_PATH")`
- `validate-hardening-report.sh` line 22: `CONTENT=$(cat "$FILE_PATH")`
- `validate-safety-constraints.sh` line 28: `CONTENT=$(cat "$FILE_PATH")`
- `validate-aqs-artifact.sh` line 28: `CONTENT=$(cat "$FILE_PATH")`

vs.

- `validate-consistency-artifacts.sh` lines 21, 64, 77: `CONTENT=$(cat "$FILE_PATH" 2>/dev/null) || true`

**The contradiction:**

All five scripts in the first group run under `set -euo pipefail`. If `cat "$FILE_PATH"` fails (e.g., a race condition where the file is deleted between the `-f` guard and the `cat`), the script exits non-zero immediately. For blocking scripts, this means the `Write` operation is blocked. For advisory scripts, this is slightly less catastrophic but still wrong behavior.

`validate-consistency-artifacts.sh` suppresses the error with `|| true`, making it resilient to this race — but inconsistently so within the group.

**Note:** The `-f "$FILE_PATH"` guard immediately before the `cat` makes this race very unlikely in practice, but the inconsistency makes it harder to reason about and is a portability/correctness smell.

**Recommendation: STANDARDIZE — use `cat "$FILE_PATH" 2>/dev/null || true` universally in the disk fallback path. This is best enforced by extracting `read_tool_content` (see DUP-002).**

---

## Pattern Inventory (Non-Duplicated)

The following patterns appear in only one script and are correctly scoped there:

| Pattern | Location | Notes |
|---|---|---|
| `jq to_entries \| map(select) \| from_entries` for registry mutation | `crossmodel-grid-down.sh` | Unique to registry deregistration logic |
| `awk` sqrt geometry for grid layout | `crossmodel-grid-up.sh` | Grid-specific |
| `fail()` local helper emitting JSON + stderr + exit 2 | `crossmodel-preflight.sh` | Only preflight uses this idiom; other scripts use inline `printf` + `exit 2` |
| `process_blocks()` generic block splitter with callback | `validate-aqs-artifact.sh` | Complex enough that inlining in other scripts would be wrong |
| `check_section()` local array builder | `validate-hardening-report.sh` | Appropriate for single-script use |
| WARNINGS array + deferred output | `validate-safety-constraints.sh` | Advisory-mode pattern, not used in blocking scripts |
| `grep -c` for proximity detection | `validate-safety-constraints.sh` | SC-005 specific logic |
| `stat -f%z` vs `stat -c%s` macOS/Linux portability | `crossmodel-verify-artifact.sh` | Candidate for `scripts/lib/common.sh` if stat is needed elsewhere |

---

## Recommended Extraction Plan

### Phase 1 — `hooks/lib/common.sh` additions (3 new functions)

```bash
# 1. Standardized jq guard
require_jq() {
  # Usage: require_jq [--advisory HOOK_NAME]
  # With --advisory: emits warning and exits 0 if jq missing
  # Without: emits error to stderr and exits 2
}

# 2. Unified FILE_PATH extraction from stdin
read_hook_file_path() {
  # Wraps: INPUT=$(cat); FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
  # Returns both INPUT and FILE_PATH to caller via nameref or stdout
}

# 3. Unified content extraction (tool_input.content → disk fallback)
read_tool_content() {
  # Args: INPUT FILE_PATH
  # Returns content via stdout
  # Always resilient (never hard-fails)
}
```

### Phase 2 — new `scripts/lib/common.sh` (3 new functions)

```bash
# 1. Session name validation
validate_session_name() { ... }  # DUP-003

# 2. Shared canonicalize_path (sourced from or copied from hooks/lib/common.sh)
canonicalize_path() { ... }  # DUP-004

# 3. SHA-256 portability helper
compute_sha256() { ... }  # DUP-005
```

### Phase 3 — standardize existing hook scripts

Update 5 blocking hook scripts to use `require_jq` at top (CON-001).
Update 4 disk-fallback `cat` calls to use resilient form (CON-002).

---

## Files Referenced

- `/Users/q/.claude/plugins/sdlc-os/hooks/lib/common.sh`
- `/Users/q/.claude/plugins/sdlc-os/scripts/crossmodel-grid-down.sh`
- `/Users/q/.claude/plugins/sdlc-os/scripts/crossmodel-grid-up.sh`
- `/Users/q/.claude/plugins/sdlc-os/scripts/crossmodel-health.sh`
- `/Users/q/.claude/plugins/sdlc-os/scripts/crossmodel-preflight.sh`
- `/Users/q/.claude/plugins/sdlc-os/scripts/crossmodel-verify-artifact.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/check-naming-convention.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/guard-bead-status.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/lint-domain-vocabulary.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-aqs-artifact.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-consistency-artifacts.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-decision-trace.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-hardening-report.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-runner-output.sh`
- `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-safety-constraints.sh`
