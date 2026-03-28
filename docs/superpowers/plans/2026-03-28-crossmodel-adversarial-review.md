# Cross-Model Adversarial Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-model adversarial review to the SDLC-OS pipeline using tmup/Codex workers, with FFT-14 routing, resilient session management, and advisory-only day-1 stance.

**Architecture:** New `sdlc-crossmodel` adapter skill dispatches Codex CLI workers through tmup MCP tools. FFT-14 routes beads to FULL (5 workers) or TARGETED (2 workers) cross-model review post-AQS/pre-hardened. A crossmodel-supervisor agent owns session lifecycle with circuit breakers and fallback ladder. Stage A findings feed existing blue teams; Stage B findings go through crossmodel-triage.

**Tech Stack:** Bash scripts (deterministic ops), Markdown agents/skills (Claude plugin format), tmup MCP tools (transport), Codex CLI (cross-model workers)

**Spec:** `docs/specs/2026-03-28-crossmodel-adversarial-review-design.md`

**Residual risk to verify early:** Task 1 Step 7 validates that `crossmodel-grid-down.sh --force` actually deregisters from tmup's `registry.json`. If it doesn't, the retry path in Section 6.2 of the spec is broken.

---

## File Map

### New Files (Create)

| File | Responsibility |
|---|---|
| `scripts/crossmodel-preflight.sh` | Platform/tmup/codex availability check |
| `scripts/crossmodel-grid-up.sh` | tmux grid creation with TMUP_NO_TERMINAL=1 |
| `scripts/crossmodel-grid-down.sh` | Grid teardown + `--force` registry deregistration |
| `scripts/crossmodel-verify-artifact.sh` | Artifact existence, schema, checksum validation |
| `scripts/crossmodel-health.sh` | Session health from worker states |
| `agents/crossmodel-supervisor.md` | tmup session lifecycle, retries, fallback, artifact verification |
| `agents/crossmodel-triage.md` | Stage B finding deduplication against AQS results |
| `skills/sdlc-crossmodel/SKILL.md` | Adapter lifecycle: preflight → init → batch → dispatch → monitor → collect → normalize → route → teardown |

### Existing Files (Modify)

| File | Change |
|---|---|
| `references/fft-decision-trees.md` | Add FFT-14 cross_model_escalation |
| `references/artifact-templates.md` | Add AQS structured exit schema (5 fields) |
| `skills/sdlc-adversarial/SKILL.md` | Structured AQS exit block + hardened gate for FFT-14 |
| `skills/sdlc-orchestrate/SKILL.md` | FFT-14 evaluation point + supervisor dispatch + quick-ref table |
| `skills/sdlc-evolve/SKILL.md` | Cross-model review in Evolve cycles |
| `.claude-plugin/plugin.json` | Version → 9.0.0 |
| `docs/HANDOFF.md` | Layer 9, updated counts |

---

### Task 1: Deterministic Scripts (Foundation)

**Files:**
- Create: `scripts/crossmodel-preflight.sh`
- Create: `scripts/crossmodel-grid-up.sh`
- Create: `scripts/crossmodel-grid-down.sh`
- Create: `scripts/crossmodel-verify-artifact.sh`
- Create: `scripts/crossmodel-health.sh`

These scripts are the deterministic foundation. Everything else depends on them. Per FFT-08: binary checks go to scripts, not LLM agents.

- [ ] **Step 1: Create crossmodel-preflight.sh**

```bash
#!/bin/bash
set -euo pipefail

# crossmodel-preflight.sh — Verify all prerequisites for cross-model review
# Exit 0 = ready, Exit 2 = not ready (with reason on stderr)

CHECKS_PASSED=0
CHECKS_TOTAL=5

check() {
  local name="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "{\"check\": \"$name\", \"status\": \"FAIL\"}" >&2
    echo "PREFLIGHT_FAIL: $name" >&2
    exit 2
  fi
}

# 1. tmux available
check "tmux_available" "command -v tmux"

# 2. codex CLI available
check "codex_available" "command -v codex"

# 3. tmup MCP reachable (check if plugin dir exists and MCP server entry point exists)
TMUP_ROOT="${TMUP_PLUGIN_ROOT:-$HOME/.claude/plugins/tmup}"
check "tmup_mcp_reachable" "test -f '$TMUP_ROOT/mcp-server/src/index.ts' || test -f '$TMUP_ROOT/mcp-server/dist/index.js'"

# 4. Artifact path writable
TASK_DIR="${1:-}"
if [ -n "$TASK_DIR" ]; then
  CROSSMODEL_DIR="$TASK_DIR/crossmodel"
  mkdir -p "$CROSSMODEL_DIR" 2>/dev/null || true
  check "artifact_path_writable" "test -w '$CROSSMODEL_DIR'"
else
  check "artifact_path_writable" "true"
fi

# 5. No conflicting active cross-model session
TMUP_STATE_DIR="${HOME}/.local/state/tmup"
if [ -d "$TMUP_STATE_DIR" ]; then
  ACTIVE_XM=$(find "$TMUP_STATE_DIR" -maxdepth 1 -name "xm-*" -type d 2>/dev/null | head -1)
  if [ -n "$ACTIVE_XM" ]; then
    # Check if session is actually alive (tmux session exists)
    SESSION_NAME=$(basename "$ACTIVE_XM")
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
      echo "PREFLIGHT_FAIL: conflicting_session ($SESSION_NAME)" >&2
      exit 2
    fi
    # Dead session residue — not a conflict
  fi
fi
CHECKS_PASSED=$((CHECKS_PASSED + 1))

echo "{\"status\": \"READY\", \"checks_passed\": $CHECKS_PASSED, \"checks_total\": $CHECKS_TOTAL}"
exit 0
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/crossmodel-preflight.sh`

- [ ] **Step 3: Create crossmodel-grid-up.sh**

```bash
#!/bin/bash
set -euo pipefail

# crossmodel-grid-up.sh — Create tmux grid for cross-model review
# Args: --session-name NAME --panes N
# Exit 0 = grid ready, Exit 2 = grid creation failed

SESSION_NAME=""
PANE_COUNT=2

while [[ $# -gt 0 ]]; do
  case $1 in
    --session-name) SESSION_NAME="$2"; shift 2 ;;
    --panes) PANE_COUNT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SESSION_NAME" ]; then
  echo "GRID_UP_FAIL: --session-name required" >&2
  exit 2
fi

# Suppress GUI terminal auto-launch (tmup grid-setup.sh checks this)
export TMUP_NO_TERMINAL=1

# Determine grid layout from pane count
if [ "$PANE_COUNT" -le 2 ]; then
  ROWS=1; COLS="$PANE_COUNT"
elif [ "$PANE_COUNT" -le 4 ]; then
  ROWS=1; COLS="$PANE_COUNT"
else
  ROWS=2; COLS=$(( (PANE_COUNT + 1) / 2 ))
fi

# Create tmux session
tmux new-session -d -s "$SESSION_NAME" -x 240 -y 55 2>/dev/null || {
  echo "GRID_UP_FAIL: tmux new-session failed" >&2
  exit 2
}

# Split panes
TOTAL_PANES=1
TARGET_PANES=$((ROWS * COLS))

# Create rows
for ((r=1; r<ROWS; r++)); do
  tmux split-window -t "${SESSION_NAME}:0" -v
  TOTAL_PANES=$((TOTAL_PANES + 1))
done

# Create columns in each row
for ((r=0; r<ROWS; r++)); do
  for ((c=1; c<COLS; c++)); do
    tmux split-window -t "${SESSION_NAME}:0.${r}" -h
    TOTAL_PANES=$((TOTAL_PANES + 1))
  done
done

# Even layout
tmux select-layout -t "${SESSION_NAME}:0" tiled

# Set minimal prompt in each pane
for ((p=0; p<TARGET_PANES; p++)); do
  tmux send-keys -t "${SESSION_NAME}:0.${p}" "PS1='xm \$ '; clear" Enter
done

# Verify pane count
ACTUAL_PANES=$(tmux list-panes -t "${SESSION_NAME}:0" 2>/dev/null | wc -l | tr -d ' ')
if [ "$ACTUAL_PANES" -lt "$PANE_COUNT" ]; then
  echo "GRID_UP_FAIL: expected $PANE_COUNT panes, got $ACTUAL_PANES" >&2
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  exit 2
fi

echo "{\"status\": \"UP\", \"session\": \"$SESSION_NAME\", \"panes\": $ACTUAL_PANES}"
exit 0
```

- [ ] **Step 4: Create crossmodel-grid-down.sh**

```bash
#!/bin/bash
set -euo pipefail

# crossmodel-grid-down.sh — Tear down tmux grid + optional registry deregistration
# Args: --session-name NAME [--force]
# --force: also deregister from tmup registry to prevent reattachment on retry
# Exit 0 = clean, Exit 1 = warning (residue left)

SESSION_NAME=""
FORCE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --session-name) SESSION_NAME="$2"; shift 2 ;;
    --force) FORCE=true; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SESSION_NAME" ]; then
  echo "GRID_DOWN_FAIL: --session-name required" >&2
  exit 2
fi

# Kill tmux session
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
fi

# Force deregistration from tmup registry
if [ "$FORCE" = true ]; then
  REGISTRY="${HOME}/.local/state/tmup/registry.json"
  if [ -f "$REGISTRY" ]; then
    # Remove the session entry by session name
    # tmup registry maps project_dir -> session_id
    # We need to remove any entry whose value matches our session name
    TEMP=$(mktemp)
    if command -v jq >/dev/null 2>&1; then
      jq --arg name "$SESSION_NAME" 'to_entries | map(select(.value != $name)) | from_entries' "$REGISTRY" > "$TEMP" 2>/dev/null && mv "$TEMP" "$REGISTRY"
    else
      # Fallback: remove line containing session name (less precise but functional)
      grep -v "$SESSION_NAME" "$REGISTRY" > "$TEMP" 2>/dev/null && mv "$TEMP" "$REGISTRY" || true
    fi
  fi

  # Remove session state directory
  SESSION_DIR="${HOME}/.local/state/tmup/${SESSION_NAME}"
  if [ -d "$SESSION_DIR" ]; then
    rm -rf "$SESSION_DIR"
  fi

  # Clear current-session pointer if it points to this session
  CURRENT="${HOME}/.local/state/tmup/current-session"
  if [ -f "$CURRENT" ] && grep -q "$SESSION_NAME" "$CURRENT" 2>/dev/null; then
    rm -f "$CURRENT"
  fi
fi

# Verify cleanup
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "{\"status\": \"WARNING\", \"residue\": \"tmux session still exists\"}"
  exit 1
fi

echo "{\"status\": \"DOWN\", \"force\": $FORCE}"
exit 0
```

- [ ] **Step 5: Create crossmodel-verify-artifact.sh**

```bash
#!/bin/bash
set -euo pipefail

# crossmodel-verify-artifact.sh — Validate a cross-model review artifact
# Args: --path FILE [--project-dir DIR] [--max-size BYTES]
# Exit 0 + JSON = result. VALID, MISSING, MALFORMED, OVERSIZED, PATH_VIOLATION, STALE, EMPTY

ARTIFACT_PATH=""
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
MAX_SIZE=102400  # 100KB default

while [[ $# -gt 0 ]]; do
  case $1 in
    --path) ARTIFACT_PATH="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --max-size) MAX_SIZE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$ARTIFACT_PATH" ]; then
  echo "{\"status\": \"MISSING\", \"reason\": \"no path provided\"}"
  exit 0
fi

# Check existence
if [ ! -f "$ARTIFACT_PATH" ]; then
  echo "{\"status\": \"MISSING\", \"path\": \"$ARTIFACT_PATH\"}"
  exit 0
fi

# Check path is within project directory (no traversal)
REAL_ARTIFACT=$(realpath "$ARTIFACT_PATH")
REAL_PROJECT=$(realpath "$PROJECT_DIR")
case "$REAL_ARTIFACT" in
  "$REAL_PROJECT"/*) ;; # OK
  *) echo "{\"status\": \"PATH_VIOLATION\", \"path\": \"$ARTIFACT_PATH\", \"project\": \"$PROJECT_DIR\"}"
     exit 0 ;;
esac

# Check size
FILE_SIZE=$(wc -c < "$ARTIFACT_PATH" | tr -d ' ')
if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
  echo "{\"status\": \"OVERSIZED\", \"size\": $FILE_SIZE, \"max\": $MAX_SIZE}"
  exit 0
fi

# Check empty
if [ "$FILE_SIZE" -eq 0 ]; then
  echo "{\"status\": \"EMPTY\", \"path\": \"$ARTIFACT_PATH\"}"
  exit 0
fi

# Check required headings
REQUIRED_HEADINGS=("## Cross-Model Review:" "### Findings" "### Summary")
for heading in "${REQUIRED_HEADINGS[@]}"; do
  if ! grep -q "$heading" "$ARTIFACT_PATH" 2>/dev/null; then
    echo "{\"status\": \"MALFORMED\", \"reason\": \"missing heading: $heading\"}"
    exit 0
  fi
done

# Check findings table has at least a header row
if ! grep -q "| # | Severity |" "$ARTIFACT_PATH" 2>/dev/null; then
  echo "{\"status\": \"MALFORMED\", \"reason\": \"missing findings table header\"}"
  exit 0
fi

# Compute checksum
CHECKSUM=$(shasum -a 256 "$ARTIFACT_PATH" | cut -d' ' -f1)

echo "{\"status\": \"VALID\", \"path\": \"$ARTIFACT_PATH\", \"size\": $FILE_SIZE, \"checksum\": \"$CHECKSUM\"}"
exit 0
```

- [ ] **Step 6: Create crossmodel-health.sh**

```bash
#!/bin/bash
set -euo pipefail

# crossmodel-health.sh — Compute session health from worker states
# Args: --session-journal PATH
# Exit 0 + JSON = health assessment

JOURNAL_PATH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --session-journal) JOURNAL_PATH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$JOURNAL_PATH" ] || [ ! -f "$JOURNAL_PATH" ]; then
  echo "{\"health\": \"UNKNOWN\", \"reason\": \"no session journal\"}"
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "{\"health\": \"UNKNOWN\", \"reason\": \"jq not available\"}"
  exit 0
fi

# Extract worker states
TOTAL=$(jq '.worker_tasks | length' "$JOURNAL_PATH" 2>/dev/null || echo 0)
COMPLETED=$(jq '[.worker_tasks[] | select(.status == "completed")] | length' "$JOURNAL_PATH" 2>/dev/null || echo 0)
FAILED=$(jq '[.worker_tasks[] | select(.status == "failed" or .status == "timed_out")] | length' "$JOURNAL_PATH" 2>/dev/null || echo 0)
NO_EVIDENCE=$(jq '[.worker_tasks[] | select(.status == "no_evidence")] | length' "$JOURNAL_PATH" 2>/dev/null || echo 0)
VALID_ARTIFACTS=$(jq '.validated_artifacts | length' "$JOURNAL_PATH" 2>/dev/null || echo 0)
BREAKER=$(jq -r '.breaker_open // false' "$JOURNAL_PATH" 2>/dev/null || echo false)

# Compute health
HEALTH="RUNNING"
if [ "$BREAKER" = "true" ]; then
  HEALTH="FALLBACK_CLAUDE_ONLY"
elif [ "$NO_EVIDENCE" -gt 1 ]; then
  HEALTH="DEGRADED"
elif [ "$FAILED" -gt 1 ]; then
  HEALTH="DEGRADED"
elif [ "$TOTAL" -gt 0 ] && [ "$COMPLETED" -eq "$TOTAL" ]; then
  HEALTH="COMPLETE"
fi

echo "{\"health\": \"$HEALTH\", \"total\": $TOTAL, \"completed\": $COMPLETED, \"failed\": $FAILED, \"no_evidence\": $NO_EVIDENCE, \"valid_artifacts\": $VALID_ARTIFACTS, \"breaker\": $BREAKER}"
exit 0
```

- [ ] **Step 7: Make all scripts executable and verify grid-down --force**

Run:
```bash
chmod +x scripts/crossmodel-preflight.sh scripts/crossmodel-grid-up.sh scripts/crossmodel-grid-down.sh scripts/crossmodel-verify-artifact.sh scripts/crossmodel-health.sh
```

**Critical verification — test the retry path assumption:**
```bash
# Create a test tmup session
cd ~/.claude/plugins/sdlc-os
# Verify registry.json exists and note its contents
cat ~/.local/state/tmup/registry.json 2>/dev/null || echo "No registry"

# Test --force deregistration on a non-existent session (should not error)
bash scripts/crossmodel-grid-down.sh --session-name xm-test-r0 --force
echo "Exit code: $?"
```

Expected: exit 0, `{"status": "DOWN", "force": true}`. If tmup registry.json has a different structure than expected, fix the jq filter in crossmodel-grid-down.sh before proceeding.

- [ ] **Step 8: Commit**

```bash
git add scripts/crossmodel-preflight.sh scripts/crossmodel-grid-up.sh scripts/crossmodel-grid-down.sh scripts/crossmodel-verify-artifact.sh scripts/crossmodel-health.sh
git commit -m "feat: add cross-model deterministic scripts — preflight, grid, artifact, health"
```

---

### Task 2: AQS Structured Exit Schema

**Files:**
- Modify: `references/artifact-templates.md` (append AQS exit block)
- Modify: `skills/sdlc-adversarial/SKILL.md` (add structured exit output)

FFT-14 needs machine-readable fields from AQS output. Currently AQS produces prose. This task adds the structured schema.

- [ ] **Step 1: Read current AQS artifact template**

Run: `grep -n "verdict\|Residual Risk\|AQS.*exit\|## AQS" references/artifact-templates.md`

Identify the exact location of the current AQS exit format.

- [ ] **Step 2: Add structured exit schema to artifact-templates.md**

Append after the existing AQS artifact section:

```markdown
### AQS Structured Exit Block

Machine-readable fields emitted alongside the prose AQS report. Consumed by FFT-14 (cross-model escalation).

```yaml
aqs_exit:
  aqs_verdict: HARDENED | PARTIALLY_HARDENED | DEFERRED
  arbiter_invoked: true | false
  residual_risk_per_domain:
    functionality: NONE | LOW | MEDIUM | HIGH
    security: NONE | LOW | MEDIUM | HIGH
    usability: NONE | LOW | MEDIUM | HIGH
    resilience: NONE | LOW | MEDIUM | HIGH
  dominant_residual_risk_domain: functionality | security | usability | resilience
  turbulence_sum: <integer>
```

**Field definitions:**
- `aqs_verdict`: Final AQS determination. HARDENED = clean or all findings resolved. PARTIALLY_HARDENED = residual risk documented. DEFERRED = blocked, escalate to L3.
- `arbiter_invoked`: True if the arbiter agent was dispatched during any AQS cycle on this bead.
- `residual_risk_per_domain`: Per-domain risk after blue team resolution. NONE = no findings or all resolved. LOW/MEDIUM/HIGH = accepted findings with documented residual risk.
- `dominant_residual_risk_domain`: Domain with highest residual risk. Tie-break order: security > functionality > resilience > usability.
- `turbulence_sum`: Sum of bead turbulence fields (L0 + L1 + L2 + L2.5 + L2.75).
```

- [ ] **Step 3: Read current AQS SKILL.md exit section**

Run: `grep -n "hardened\|exit\|verdict\|Residual" skills/sdlc-adversarial/SKILL.md | head -20`

Identify the AQS completion/exit section.

- [ ] **Step 4: Add structured exit output to AQS SKILL.md**

Find the AQS completion section (where bead status transitions to hardened) and add before the transition:

```markdown
### Structured AQS Exit (FFT-14 Input)

Before transitioning the bead to `hardened`, emit the structured exit block:

```yaml
aqs_exit:
  aqs_verdict: {HARDENED | PARTIALLY_HARDENED | DEFERRED}
  arbiter_invoked: {true | false}
  residual_risk_per_domain:
    functionality: {NONE | LOW | MEDIUM | HIGH}
    security: {NONE | LOW | MEDIUM | HIGH}
    usability: {NONE | LOW | MEDIUM | HIGH}
    resilience: {NONE | LOW | MEDIUM | HIGH}
  dominant_residual_risk_domain: {domain with highest risk, tie-break: security > functionality > resilience > usability}
  turbulence_sum: {integer from bead turbulence field}
```

This block is consumed by FFT-14 (cross-model escalation). If cross-model review is active, the `hardened` transition is gated by FFT-14 — the Conductor evaluates FFT-14 using these fields, and the bead only transitions to `hardened` after any cross-model findings are resolved.

See `references/artifact-templates.md` for field definitions.
```

- [ ] **Step 5: Commit**

```bash
git add references/artifact-templates.md skills/sdlc-adversarial/SKILL.md
git commit -m "feat: add AQS structured exit schema for FFT-14 consumption"
```

---

### Task 3: FFT-14 Decision Tree

**Files:**
- Modify: `references/fft-decision-trees.md` (append FFT-14)

- [ ] **Step 1: Read end of current FFT file**

Run: `tail -30 references/fft-decision-trees.md`

Identify where to append FFT-14 (after FFT-13 or the last existing FFT).

- [ ] **Step 2: Append FFT-14**

Add at the end of `references/fft-decision-trees.md`:

```markdown
---

## FFT-14: Cross-Model Escalation

**Replaces:** Implicit "always same-model AQS only" assumption
**Anti-pattern guarded:** Single-Model Blind Spot — same model family cannot catch its own systematic failure modes
**Source:** Cross-model adversarial review spec (2026-03-28), Milvus research (53% → 80% detection with debate)

```
FFT-14: cross_model_escalation

  Evaluated: after same-model AQS completes, BEFORE bead status → hardened
  Input: AQS structured exit block (aqs_exit)

  Cue 0: Is tmup available and fully operational?
    (crossmodel-preflight.sh: MCP reachable + codex in PATH + tmux
     available + writable artifact path + no conflicting session)
    → NO  → SKIP_UNAVAILABLE
             Log: "tmup unavailable: {specific failure}, continuing Claude-only path"
    → YES → continue

  Cue 1: Is aqs_exit.aqs_verdict == DEFERRED?
    → YES → ESCALATE_L3 (no cross-model — bead stays at proven,
             escalates to Conductor per AQS protocol)
    → NO  → continue

  Cue 2: Is the bead COMPLEX domain or security_sensitive?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 3: Is the quality budget DEPLETED?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 4: Is the quality budget WARNING?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 5: Is aqs_exit.arbiter_invoked == true?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 6: Is aqs_exit.turbulence_sum > 3?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 7: Is any aqs_exit.residual_risk_per_domain >= MEDIUM?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Default → SKIP CROSS-MODEL
```

**Outcomes:**
- **FULL:** 5 Codex workers (4 domain investigators + 1 independent reviewer). Grid: 2×3 layout.
- **TARGETED:** 2 Codex workers (1 investigator for `aqs_exit.dominant_residual_risk_domain` + 1 independent reviewer). Grid: 1×2 layout.
- **SKIP_UNAVAILABLE:** Log in decision trace, continue Claude-only. Not a failure.
- **SKIP:** No cross-model review needed.
```

- [ ] **Step 3: Commit**

```bash
git add references/fft-decision-trees.md
git commit -m "feat: add FFT-14 cross-model escalation decision tree"
```

---

### Task 4: Agent Definitions

**Files:**
- Create: `agents/crossmodel-supervisor.md`
- Create: `agents/crossmodel-triage.md`

- [ ] **Step 1: Read an existing sonnet agent for pattern**

Run: `head -5 agents/reliability-conductor.md`

Confirm frontmatter format: `name`, `description` (double-quoted), `model`.

- [ ] **Step 2: Create crossmodel-supervisor.md**

Write `agents/crossmodel-supervisor.md` — the sonnet-class agent that owns the full tmup session lifecycle for one bead's cross-model review. Include:

Frontmatter: `name: crossmodel-supervisor`, `model: sonnet`

System prompt covering:
- Role: own tmup session lifecycle, worker dispatch/monitoring, artifact verification, retry/fallback decisions
- Chain of command: reports to Conductor, dispatches via tmup MCP tools, collects via artifact files
- State machine: READY → RUNNING → COMPLETE, with DEGRADED and FALLBACK_CLAUDE_ONLY branches, DISABLED on unrecoverable failure
- Session journal contract: write `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-session.json` with full schema from spec Section 6.1
- Lifecycle steps: PREFLIGHT → INIT → BATCH → DISPATCH → MONITOR → COLLECT → NORMALIZE → ROUTE → TEARDOWN
- Monitor loop: `tmup_status` + `tmup_inbox` + `tmup_next_action` every 15s (normal) / 5s (degraded)
- Retry budget: from spec Section 6.2
- Fallback ladder: FULL → TARGETED → REVIEWER_ONLY → CLAUDE_ONLY
- Circuit breakers: from spec Section 6.4
- Integrity rules: from spec Section 6.6
- Error handling table: from spec Section 6.5

- [ ] **Step 3: Create crossmodel-triage.md**

Write `agents/crossmodel-triage.md` — the haiku-class agent that deduplicates Stage B findings.

Frontmatter: `name: crossmodel-triage`, `model: haiku`

System prompt covering:
- Role: receive Stage B (independent review) findings from Codex, deduplicate against existing AQS results and L1 corrections
- Chain of command: reports to Conductor, receives normalized Codex findings, produces net-new finding list
- Input: Stage B artifact (markdown) + existing AQS report for the bead
- Deduplication logic: for each Codex finding, check if same file:line + same category already appears in AQS findings. If yes → "already caught" (logged, not re-processed). If no → "net-new" (escalated as HIGH priority through L1 loop)
- Output format: triage report listing each finding as DUPLICATE or NET_NEW with evidence for the classification
- Constraints: never modify bead status, never see Stage A findings (only Stage B), treat raw Codex output as untrusted

- [ ] **Step 4: Commit**

```bash
git add agents/crossmodel-supervisor.md agents/crossmodel-triage.md
git commit -m "feat: add crossmodel-supervisor and crossmodel-triage agents"
```

---

### Task 5: sdlc-crossmodel Skill

**Files:**
- Create: `skills/sdlc-crossmodel/SKILL.md`

- [ ] **Step 1: Read an existing skill for pattern**

Run: `head -10 skills/sdlc-harden/SKILL.md`

Confirm skill frontmatter format.

- [ ] **Step 2: Create SKILL.md**

Write `skills/sdlc-crossmodel/SKILL.md` with:

Frontmatter:
```yaml
---
name: sdlc-crossmodel
description: "Cross-model adversarial review using tmup/Codex workers. Dispatched by the Conductor when FFT-14 triggers FULL or TARGETED cross-model escalation post-AQS, pre-hardened."
---
```

Body covering the full adapter lifecycle from spec Section 5:
- When dispatched and by whom (Conductor, after FFT-14)
- FFT-14 input contract (structured AQS exit block)
- PREFLIGHT through TEARDOWN lifecycle (9 steps)
- Stage A: red team supplement (blind to Claude AQS, uses domain-attack-libraries.md prompts)
- Stage B: independent review (blind to all review artifacts)
- Worker artifact contract (unique `produces` names, file path template with {domain})
- Finding flowback (Stage A → blue teams, Stage B → crossmodel-triage)
- R&R: supervisor state machine, retry budget, fallback ladder, circuit breakers, monitoring loop
- Error handling table
- Integrity rules
- tmup MCP tool usage table (which tool for what, and what each tool does NOT do)
- Scripts table (which script for what binary check)

Reference the spec for the full contracts: `docs/specs/2026-03-28-crossmodel-adversarial-review-design.md`

- [ ] **Step 3: Commit**

```bash
git add skills/sdlc-crossmodel/SKILL.md
git commit -m "feat: add sdlc-crossmodel adapter skill"
```

---

### Task 6: Orchestration Wiring

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`
- Modify: `skills/sdlc-evolve/SKILL.md`

- [ ] **Step 1: Read AQS section in orchestrate skill**

Run: `grep -n "AQS\|hardened\|L2.5\|Phase 4.5" skills/sdlc-orchestrate/SKILL.md | head -15`

Find the exact point where AQS completes and bead transitions to hardened.

- [ ] **Step 2: Insert FFT-14 evaluation between AQS and hardened**

Find the line where AQS marks bead `hardened` and insert before it:

```markdown
   - **Cross-model escalation (FFT-14):** After same-model AQS completes, the Conductor evaluates FFT-14 from `references/fft-decision-trees.md` using the AQS structured exit block. If FFT-14 returns FULL or TARGETED: dispatch `crossmodel-supervisor` with bead context and FFT-14 outcome. The supervisor manages the full tmup session lifecycle (see `sdlc-os:sdlc-crossmodel`). Stage A findings route to existing blue team defenders. Stage B findings route to `crossmodel-triage`. All cross-model findings must be resolved before bead transitions to `hardened`. If FFT-14 returns SKIP or SKIP_UNAVAILABLE: proceed directly to `hardened`.
```

- [ ] **Step 3: Update quick-reference table**

Find the quick-reference table. Update the Execute row to add `+ crossmodel-supervisor (if FFT-14 triggers)` in the Runners column.

- [ ] **Step 4: Add cross-model to Evolve skill**

Read the current evolve steps:
Run: `grep -n "^### " skills/sdlc-evolve/SKILL.md`

Add after the last numbered step (currently 16):

```markdown
### 17. Cross-Model System Review

Dispatch `crossmodel-supervisor` with TARGETED mode to review the Evolve changes themselves. When the SDLC-OS modifies its own agents, hooks, or skills, a cross-model review provides genuinely independent verification that the changes are sound. Uses investigator role for the highest-risk domain of the Evolve changes + reviewer role for independent assessment.
```

- [ ] **Step 5: Commit**

```bash
git add skills/sdlc-orchestrate/SKILL.md skills/sdlc-evolve/SKILL.md
git commit -m "feat: wire FFT-14 + crossmodel-supervisor into orchestrate and evolve"
```

---

### Task 7: HANDOFF, Version Bump, Sync

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Bump version**

Edit `.claude-plugin/plugin.json`: change `"version": "8.1.0"` to `"version": "9.0.0"`

- [ ] **Step 2: Update HANDOFF**

Update `docs/HANDOFF.md`:
- Version: 9.0.0
- Agent count: 45 (43 + crossmodel-supervisor + crossmodel-triage)
- Reference docs: 19 (unchanged — FFT-14 is an update, not a new file)
- Skills: 15 (14 + sdlc-crossmodel)
- Add Layer 9 to architecture:
```
Layer 9: Cross-Model Adversarial Review (v9.0.0)
  FFT-14 escalation, tmup/Codex workers, crossmodel-supervisor, advisory day-1
  Cross-model debate (Milvus 53%→80%), tmup DAG coordination
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json docs/HANDOFF.md
git commit -m "feat: bump to v9.0.0 — Cross-Model Adversarial Review layer"
```

- [ ] **Step 4: Push and sync all machines**

```bash
git push origin main
ssh q@nucles.local 'cd ~/.claude/plugins/sdlc-os && git pull origin main'
ssh -i ~/.ssh/id_ed25519 andre@100.101.199.28 'wsl -u drew -- bash -c "cd ~/.claude/plugins/sdlc-os && git pull origin main"'
```

- [ ] **Step 5: Verify all machines match**

```bash
echo "=== MACLAB ===" && git log --oneline -1 && cat .claude-plugin/plugin.json | grep version
ssh q@nucles.local 'cd ~/.claude/plugins/sdlc-os && git log --oneline -1 && cat .claude-plugin/plugin.json | grep version'
ssh -i ~/.ssh/id_ed25519 andre@100.101.199.28 'wsl -u drew -- bash -c "cd ~/.claude/plugins/sdlc-os && git log --oneline -1 && cat .claude-plugin/plugin.json | grep version"'
```

Expected: All three show same commit hash, version 9.0.0.
