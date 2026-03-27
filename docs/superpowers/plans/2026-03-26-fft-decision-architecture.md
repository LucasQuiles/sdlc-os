# FFT Decision Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Conductor's prose-driven holistic judgment with 12 explicit Fast-and-Frugal Decision Trees, add task profiles (Build/Investigate/Repair/Evolve), extend the bead spec with decision traces and turbulence tracking, add HRO structural constraints, and create the Evolve skill for system self-improvement.

**Architecture:** All changes are markdown prompt engineering edits to the sdlc-os plugin. 6 new files created, 6 existing files modified. The FFT reference document is the single source of truth for all 12 trees — other files reference it rather than duplicating tree definitions. The decision trace is a flat file alongside bead files in `beads/`.

**Tech Stack:** Markdown files in a Claude Code plugin. Bash hook script. No application code.

**Spec:** `docs/specs/2026-03-26-fft-decision-architecture-design.md`

---

## File Structure

### New Files (6)
- `references/fft-decision-trees.md` — All 12 FFTs, single source of truth for agent consumption
- `references/deterministic-checks.md` — Catalog of checks routable to scripts (FFT-08)
- `references/anti-patterns.md` — Named anti-patterns each FFT guards against
- `hooks/scripts/validate-decision-trace.sh` — Decision trace schema validator
- `skills/sdlc-evolve/SKILL.md` — Evolve profile execution playbook
- `commands/evolve.md` — Slash command invoking sdlc-evolve skill

### Modified Files (6)
- `skills/sdlc-orchestrate/SKILL.md` — FFT references, task profiles, bead spec, HRO constraints
- `skills/sdlc-adversarial/scaling-heuristics.md` — Replace signal checklists with FFT format
- `skills/sdlc-loop/SKILL.md` — FFT-05/07/08, turbulence tracking
- `hooks/hooks.json` — Register new hook
- `hooks/scripts/guard-bead-status.sh` — Add evolve type + status flow
- `.claude-plugin/plugin.json` — Bump to 6.0.0

---

### Task 1: Create FFT Decision Trees Reference

**Files:**
- Create: `references/fft-decision-trees.md`

This is the single source of truth. All 12 FFTs live here. Other files reference this document.

- [ ] **Step 1: Create the reference file**

Read the CORRECTED spec (`docs/specs/2026-03-26-fft-decision-architecture-design.md`) and extract Section 1 (all 12 FFTs). The spec has already been patched with these critical corrections — do NOT use any earlier draft:

- FFT-05 includes Cues 1-2 for CHAOTIC (L0 only) and CONFUSION (BLOCKED) before any depth assignment
- FFT-10 Cue 2 checks `security_sensitive == false` before classifying as ACCIDENTAL (security-sensitive config stays ESSENTIAL)
- FFT-11 Cue 2 checks `security_sensitive == false` before assigning 0 guppies

Write the reference file with this format — copy each FFT section COMPLETELY (metadata + code block + trace log):

```markdown
# FFT Decision Trees

All 12 Fast-and-Frugal Trees for Conductor routing decisions. This is the single source of truth — all skills and agents reference this file.

**Structure:** Each FFT has ordered cues (most diagnostic first), binary exits at each node, one traversal path logged per decision. Based on Gigerenzer's ecological rationality: match strategy complexity to environment structure.

---

## FFT-01: Task Profile Classification
{copy from spec lines 62-86 — include Replaces, Anti-pattern, Source, full code block, Trace log}

## FFT-02: Cynefin Domain Classification
{copy from spec lines 88-122}

## FFT-03: AQS Domain Activation
{copy from spec lines 124-153}

## FFT-04: Phase Configuration
{copy from spec lines 155-216}

## FFT-05: Loop Depth
{copy from spec lines 218-256}

## FFT-06: AQS Convergence
{copy from spec lines 258-286}

## FFT-07: Escalation Strategy
{copy from spec lines 288-319}

## FFT-08: Deterministic vs LLM Check Routing
{copy from spec lines 321-346}

## FFT-09: Hardening Skip Decision
{copy from spec lines 348-372}

## FFT-10: Complexity Source Classification
{copy from spec lines 374-402}

## FFT-11: Budget Allocation
{copy from spec lines 404-430}

## FFT-12: Parallelization Safety
{copy from spec lines 432-456}
```

Read the spec, extract each FFT section completely (including the Replaces, Anti-pattern guarded, Source metadata, the full code block with all cues, and the Trace log line), and write it to the reference file.

- [ ] **Step 2: Verify all 12 FFTs present**

Run: `grep -c "^## FFT-" /Users/q/.claude/plugins/sdlc-os/references/fft-decision-trees.md`
Expected: `12`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/fft-decision-trees.md
git commit -m "feat(references): add FFT decision trees — single source of truth for 12 Conductor routing FFTs"
```

---

### Task 2: Create Deterministic Checks Catalog

**Files:**
- Create: `references/deterministic-checks.md`

- [ ] **Step 1: Create the catalog**

```markdown
# Deterministic Checks Catalog

Checks that MUST be routed to shell scripts (p=1.0), not LLM agents (p<1.0). Used by FFT-08 to classify each verification check.

**Principle:** Every LLM call removed from the pipeline improves end-to-end reliability (Karpathy March of Nines). Deterministic questions get deterministic tools.

**Anti-pattern guarded:** Garbage In, Gospel Out (Sterman) — do not use probabilistic reasoning for questions with known, computable answers.

---

## Classification Rules

| Routing | Criteria | Reliability |
|---------|----------|-------------|
| DETERMINISTIC | Binary pass/fail answerable by running a command | p=1.0 |
| LLM_AGENT | Requires reading code and reasoning about behavior, architecture, or intent | p<1.0 |

## Deterministic Check Catalog

| Check | Command | Output | Category |
|-------|---------|--------|----------|
| TypeScript type check | `npx tsc --noEmit` | exit 0/1 | compilation |
| ESLint | `npx eslint {files}` | exit 0/1 + error count | linting |
| Python type check | `mypy {files}` | exit 0/1 | compilation |
| Python lint | `ruff check {files}` | exit 0/1 | linting |
| Go vet | `go vet ./...` | exit 0/1 | compilation |
| Test suite | `npm test` / `pytest` / `go test` | exit 0/1 + pass count | testing |
| File exists | `test -f {path}` | exit 0/1 | existence |
| Import cycle detection | `madge --circular {entry}` | exit 0/1 + cycle list | structural |
| Schema validation | `ajv validate -s {schema} -d {data}` | exit 0/1 | conformance |
| Coverage threshold | `coverage report --fail-under={N}` | exit 0/1 | coverage |
| Secret pattern scan | `gitleaks detect --source {path}` | exit 0/1 | security |
| License header check | `grep -l "Copyright" {files}` | match/no-match | compliance |
| JSON/YAML validity | `jq . {file}` / `python -c "import yaml; yaml.safe_load(open('{file}'))"` | exit 0/1 | syntax |
| Dependency audit | `npm audit --audit-level=critical` | exit 0/1 | security |
| Git conflict markers | `grep -r "<<<<<<" {files}` | match/no-match | structural |

## Adding New Checks

When adding a new verification check to the pipeline:
1. Ask FFT-08: "Is this answerable by running a command with binary pass/fail?"
2. If YES → add to this catalog with command and category
3. If NO → route to LLM_AGENT
4. Classification is reviewed during Evolve cycles
```

Write this to `/Users/q/.claude/plugins/sdlc-os/references/deterministic-checks.md`.

- [ ] **Step 2: Verify**

Run: `head -5 /Users/q/.claude/plugins/sdlc-os/references/deterministic-checks.md`
Expected: `# Deterministic Checks Catalog`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/deterministic-checks.md
git commit -m "feat(references): add deterministic checks catalog for FFT-08 routing"
```

---

### Task 3: Create Anti-Patterns Reference

**Files:**
- Create: `references/anti-patterns.md`

- [ ] **Step 1: Create the reference file**

```markdown
# Anti-Patterns Reference

Named anti-patterns that the FFT Decision Architecture guards against. Each FFT explicitly targets one or more anti-patterns. Sourced from the thinkers-lab research index.

---

## Tampering
**Source:** W. Edwards Deming (Funnel Experiment)
**Mechanism:** Reacting to common-cause variation as if it were special-cause, adjusting a stable process in response to normal noise. Every well-intentioned correction compounds the previous error.
**FFT guard:** FFT-06 (AQS Convergence) — Cue 3 invokes Deming Rule 1: stable process, do not adjust.
**Detect it:** Process adjustments after every bad outcome without checking whether the defect was a statistical outlier or a genuine shift.
**What to do instead:** Use control charts. Only intervene when signals appear outside control limits.

## Normalization of Deviance
**Source:** Sidney Dekker (Drift Into Failure)
**Mechanism:** Gradual acceptance of degraded standards because repeated departures from protocol have not yet caused disaster. Each small deviation is rationalized as acceptable.
**FFT guard:** Evolve profile deviance normalization check — trend analysis on Clear classification rate, fast-track rate, scrutiny skip rate.
**Detect it:** "That's just how it works here." Undocumented workarounds everyone knows about. Procedures on paper that aren't followed.
**What to do instead:** Periodically compare current practice against original design standards, not against recent practice. Use fresh eyes.

## Oversimplification
**Source:** Karl Weick (Managing the Unexpected)
**Mechanism:** Premature categorization that closes off further inquiry and channels response down a single track.
**FFT guard:** FFT-02 (Cynefin) forces explicit classification with documented cue traversal. The decision trace makes the classification auditable.
**Detect it:** Issue labeled within minutes without challenge. Investigation stopped at first plausible explanation.
**What to do instead:** Keep multiple hypotheses alive. Seek diverse interpretations before converging.

## Parameter Obsession
**Source:** Donella Meadows (Thinking in Systems)
**Mechanism:** Concentrating change efforts on numerical parameters while leaving underlying structure unchanged. Parameters are the lowest-leverage intervention.
**FFT guard:** FFT-03 (AQS Domains) uses binary activation. FFT-10 (Complexity Source) routes essential vs accidental differently rather than tuning scrutiny levels.
**Detect it:** Third iteration of tuning the same thresholds. Running debate about parameter values for months.
**What to do instead:** Map the leverage hierarchy. Ask: is there a structural change that would make this parameter irrelevant?

## Over-Engineering for Safety
**Source:** Nassim Nicholas Taleb (Antifragile)
**Mechanism:** System so thoroughly insulated from stressors that it loses adaptive capacity. Protection becomes a source of brittleness.
**FFT guard:** FFT-05 (Loop Depth) and FFT-09 (Hardening Skip) allow Clear beads to skip deep verification. Not everything needs maximum scrutiny.
**Detect it:** System has never experienced a failure. All variance designed out. Chaos engineering rejected as "too risky."
**What to do instead:** Apply hormetic stress — controlled, graduated exposure to stressors.

## Analysis Paralysis
**Source:** Gerd Gigerenzer (Risk Savvy)
**Mechanism:** Search for more information exceeds the point of diminishing returns. Complex models overfit to noise in uncertain environments.
**FFT guard:** FFT-01 (Task Profile) and FFT-04 (Phase Config) skip unnecessary phases. Investigate and Repair profiles don't analyze what doesn't need analyzing.
**Detect it:** Meetings end with requests for more data. Deadlines pass while analysis continues.
**What to do instead:** Match decision strategy to environment. Use fast-and-frugal heuristics under uncertainty.

## Narrative Fallacy
**Source:** Nassim Nicholas Taleb (The Black Swan)
**Mechanism:** Constructing post-hoc causal stories that make random or multi-causal events appear inevitable. The story crowds out genuine understanding.
**FFT guard:** FFT-07 (Escalation) checks for systemic patterns (Cue 1: same error 3+ times) before constructing a single-cause narrative.
**Detect it:** Post-incident review produces a linear causal chain ending in a single root cause. Everyone feels the situation is fully understood.
**What to do instead:** Accept that complex failures are multi-causal. Use contributing factor analysis, not root cause analysis.

## Garbage In, Gospel Out
**Source:** John Sterman (Business Dynamics)
**Mechanism:** Model outputs treated as authoritative truth without scrutinizing assumptions and data feeding the model.
**FFT guard:** FFT-08 (Check Routing) routes deterministic questions to deterministic tools. Don't ask an LLM whether types pass — run the type checker.
**Detect it:** Decisions justified by "the model says" without discussing assumptions. Sensitivity analysis absent.
**What to do instead:** Treat model outputs as structured hypotheses. Run sensitivity analysis. Surface boundary conditions.
```

Write this to `/Users/q/.claude/plugins/sdlc-os/references/anti-patterns.md`.

- [ ] **Step 2: Verify**

Run: `grep -c "^## " /Users/q/.claude/plugins/sdlc-os/references/anti-patterns.md`
Expected: `8`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add references/anti-patterns.md
git commit -m "feat(references): add anti-patterns reference — 8 named patterns guarded by FFTs"
```

---

### Task 4: Create Decision Trace Validation Hook

**Files:**
- Create: `hooks/scripts/validate-decision-trace.sh`
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Create the hook script**

Read the spec Section 8 (lines 817-840) for the full validation requirements. Create the script:

```bash
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
```

Write this to `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-decision-trace.sh`.

- [ ] **Step 2: Make executable**

Run: `chmod +x /Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-decision-trace.sh`

- [ ] **Step 3: Verify syntax**

Run: `bash -n /Users/q/.claude/plugins/sdlc-os/hooks/scripts/validate-decision-trace.sh`
Expected: No output (valid syntax)

- [ ] **Step 4: Register in hooks.json**

Read `/Users/q/.claude/plugins/sdlc-os/hooks/hooks.json`. In the `PostToolUse[0].hooks` array, after the last existing entry (validate-hardening-report.sh), add:

```json
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-decision-trace.sh\"",
            "timeout": 10
          }
```

- [ ] **Step 5: Verify hooks.json is valid JSON**

Run: `cat /Users/q/.claude/plugins/sdlc-os/hooks/hooks.json | jq '.hooks.PostToolUse[0].hooks | length'`
Expected: `6` (currently 5 PostToolUse hooks; adding 1 makes 6)

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/validate-decision-trace.sh hooks/hooks.json
git commit -m "feat(hooks): add validate-decision-trace.sh — enforces FFT fields and trace artifact"
```

---

### Task 5: Create sdlc-evolve Skill

**Files:**
- Create: `skills/sdlc-evolve/SKILL.md`

- [ ] **Step 1: Create skill directory and file**

Read the spec Section 4 EVOLVE profile (lines 638-651) and Section 9 (lines 841-845) for the full Evolve specification. Create:

```markdown
---
name: sdlc-evolve
description: "System self-improvement mode. Dispatches evolution beads for auto-rule generation from repeated findings, constitution staleness checks, calibration parameter tuning via Deming PDSA, precedent coherence audits, and deviance normalization monitoring. Triggered automatically when quality budget reaches WARNING, every 20th task, or manually via /evolve."
---

# SDLC Evolve: System Self-Improvement

The Evolve profile maintains and improves the SDLC system itself. No user-facing code changes. All beads are type `evolve` with status flow `pending → running → submitted → verified → merged`.

**Entry condition:** Quality budget at WARNING or DEPLETED, every 20th task, or manual `/evolve` command.
**Exit condition:** System health report produced with evolution outcomes.

## When This Fires

- **Automatic:** Quality budget reaches WARNING or DEPLETED with no user task pending (FFT-01 Cue 3)
- **Periodic:** Every 20th task, the Conductor checks whether an Evolve cycle is due
- **Manual:** User runs `/evolve`

## Phase Configuration (from FFT-04 Cue 3)

- Frame: SKIP
- Scout: SKIP
- Architect: SKIP
- Execute: evolution beads (5 types below)
- AQS: SKIP
- Harden: SKIP
- Synthesize: SYSTEM_REPORT
- Loop depth: L0 only

## The 5 Evolution Bead Types

### 1. Auto-Rule Generation

Scan the precedent database for findings that appeared 3+ times across tasks within the same domain and finding type.

**Protocol:**
1. Query precedent database: group by (domain, finding_type)
2. For each group with count >= 3: draft a candidate constitution rule
3. Present candidates to Conductor for approval (NOT auto-apply)
4. Approved rules are added to `references/code-constitution.md`
5. Log: which rules were proposed, which approved, which rejected with reason

**Anti-pattern guard:** Constitution Staleness (Taleb Lindy Effect) — new rules are provisional. They earn trust through external validation over time, not through volume of agent-generated findings.

### 2. Constitution Staleness Check

For each existing constitution rule, audit its health.

**Protocol:**
1. For each rule, check: how many findings generated by this rule were confirmed by evidence (test failure, runtime error, human review)?
2. Check: has the defect type this rule targets appeared in external sources (CVE databases, security advisories, language changelogs)?
3. Apply Lindy-weighted trust: older, externally-validated rules checked less frequently. Younger, internally-only-validated rules checked more aggressively.
4. Rules with declining confirmation rates and increasing agent-only confirmation: flag as staleness-vulnerable
5. Rules confirmed only by agent outputs and never by external ground truth: quarantine pending validation

### 3. Calibration Parameter Tuning (Deming PDSA)

Apply the Plan-Do-Study-Act cycle to system parameters.

**Protocol:**
1. **Plan:** Identify a parameter to tune (e.g., guppy count thresholds, recon burst size, convergence threshold). Hypothesis: "changing X from A to B will improve Y."
2. **Do:** Run the next calibration bead under the new parameter value
3. **Study:** Compare detection rate, false positive rate, and cycle count against baseline
4. **Act:** If improvement confirmed → adopt. If no improvement → abandon. If ambiguous → extend study.

**Anti-pattern guard:** Tampering (Deming) — only tune parameters when control charts show a genuine shift, not in response to single data points.

### 4. Precedent Coherence Audit

Check for contradicting precedents in the precedent database.

**Protocol:**
1. For each pair of precedents in the same (domain, finding_type) category: compare verdicts
2. If verdicts contradict (one SUSTAINED, one DISMISSED on materially similar cases): flag as inconsistency
3. For flagged inconsistencies: determine which precedent has stronger evidence and more recent validation
4. Recommend: retire the weaker precedent, or distinguish the cases if they are materially different

### 5. Deviance Normalization Check (Dekker)

Trend analysis on leading indicators of process drift.

**Protocol:**
1. Compute from decision traces over rolling 10-task window:
   - Clear classification rate (% of beads classified CLEAR by FFT-02)
   - Fast-track resolution rate (% of AQS findings resolved via plea bargaining)
   - Average loop depth (mean active loop layers per bead)
   - Scrutiny skip rate (% of beads where FFT-09 returned SKIP)
   - Budget "healthy" duration (tasks since last WARNING/DEPLETED)
2. No single metric triggers an alert
3. Co-trending of 3+ indicators in the deviance direction over sustained window → system-level review alert
4. Alert names the normalization pattern, not just individual metrics
5. Requires Conductor acknowledgment and documented response

**Anti-pattern guard:** Normalization of Deviance (Dekker) — each individual relaxation looks rational, but the aggregate trajectory erodes standards.

## Output Format

Phase 5 produces a system health report:

```markdown
# System Health Report: Evolve Cycle {N}

## Trigger
{automatic/periodic/manual} — {reason}

## Auto-Rule Generation
- Precedent groups with 3+ findings: {count}
- Candidate rules proposed: {count}
- Rules approved: {list}
- Rules rejected: {list with reasons}

## Constitution Staleness
- Rules audited: {count}
- Rules healthy: {count}
- Rules staleness-vulnerable: {list}
- Rules quarantined: {list}

## Calibration Tuning
- Parameters tuned: {list with PDSA outcomes}
- Parameters unchanged: {list with reasons}

## Precedent Coherence
- Precedent pairs audited: {count}
- Inconsistencies found: {count}
- Resolutions: {list}

## Deviance Normalization
- Indicators computed: {5 metrics with values and trend direction}
- Co-trending alert: {YES/NO}
- Pattern identified: {description or "none"}

## Overall Assessment
{Conductor summary of system health and recommended actions}
```

## Integration Points

- Decision traces (from Phase A FFT backbone) are the primary data source for all 5 evolution bead types
- Quality SLOs (`references/quality-slos.md`) define the WARNING/DEPLETED thresholds that trigger automatic Evolve
- Precedent system (`references/precedent-system.md`) is queried by auto-rule generation and coherence audit
- Code constitution (`references/code-constitution.md`) is the target for auto-rule additions
- Calibration protocol (`references/calibration-protocol.md`) is the target for parameter tuning outcomes
```

Write this to `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-evolve/SKILL.md`.

- [ ] **Step 2: Verify frontmatter**

Run: `head -4 /Users/q/.claude/plugins/sdlc-os/skills/sdlc-evolve/SKILL.md`
Expected: `---`, `name: sdlc-evolve`, `description: "..."`, `---`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-evolve/SKILL.md
git commit -m "feat(skills): add sdlc-evolve — system self-improvement with 5 evolution bead types"
```

---

### Task 6: Create /evolve Command

**Files:**
- Create: `commands/evolve.md`

- [ ] **Step 1: Check existing command format**

Run: `ls /Users/q/.claude/plugins/sdlc-os/commands/` to see existing command files. Read one to understand the format.

- [ ] **Step 2: Create the command file**

Follow the exact format of existing commands. The command should invoke the sdlc-evolve skill:

```markdown
---
name: evolve
description: Run system self-improvement — auto-rule generation, constitution staleness check, calibration tuning, precedent coherence audit, deviance normalization monitoring
---

Start an SDLC Evolve cycle using the `sdlc-os:sdlc-evolve` skill.

1. Set task profile to EVOLVE (FFT-01 Cue 3 override)
2. Create evolve beads for each of the 5 evolution types
3. Execute evolution beads (L0 only, no AQS, no hardening)
4. Produce system health report
```

Write this to `/Users/q/.claude/plugins/sdlc-os/commands/evolve.md`.

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add commands/evolve.md
git commit -m "feat(commands): add /evolve command invoking sdlc-evolve skill"
```

---

### Task 7: Update Bead Spec in sdlc-orchestrate

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

This task adds the new bead fields, task profile references, and updates the Work Units section.

- [ ] **Step 1: Read the current bead spec**

Read `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-orchestrate/SKILL.md` lines 86-117 to find the bead format.

- [ ] **Step 2: Update the bead format**

In the bead format block (the markdown template starting with `# Bead: {id}`), add the new fields from the spec Section 3 (lines 570-604). The new fields go after `**Cynefin domain:**` and before `**Assumptions:**`:

Add these lines after `**Cynefin domain:** clear | complicated | complex | chaotic | confusion`:
```
**Security sensitive:** true | false
**Complexity source:** essential | accidental
**Profile:** BUILD | INVESTIGATE | REPAIR | EVOLVE
**Decision trace:** [path to {bead-id}-decision-trace.md]
**Deterministic checks:** [list of checks routed to scripts per FFT-08]
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
**Control actions:** [Phase B — not yet populated]
**Unsafe control actions:** [Phase B — not yet populated]
**Latent condition trace:** [Phase B — not yet populated]
```

Also add `evolve` to the `**Type:**` line: `investigate | design | implement | verify | review | evolve`

Also update the `**Status:**` line to include recovery states if missing: `pending | running | submitted | verified | proven | hardened | reliability-proven | merged | blocked | stuck | escalated`

- [ ] **Step 3: Add FFT reference to Phase 1**

In Phase 1 (Frame) section, after the existing "Conductor assigns Cynefin domain" text, add:

```
**FFT routing:** The Conductor applies FFT-01 (Task Profile) and FFT-02 (Cynefin Domain) from `references/fft-decision-trees.md` to each bead. All FFT traversals are recorded in the bead's decision trace. See `references/fft-decision-trees.md` for the complete decision tree definitions.
```

- [ ] **Step 4: Add task profile section**

After the "Complexity Scaling" section and before "Recovery Patterns", insert a new section:

```markdown
## Task Profiles

The Conductor assigns a task profile via FFT-01 before any other routing. The profile determines which phases run and at what depth. See `references/fft-decision-trees.md` FFT-01 and FFT-04 for the full decision trees.

| Profile | When | Phases Active | AQS | Hardening | Bead Type |
|---------|------|---------------|-----|-----------|-----------|
| BUILD | Default — new features, enhancements | All | Per Cynefin | Per FFT-09 | implement |
| INVESTIGATE | Research, codebase understanding, no code changes | Frame + Heavy Scout + Read-Only Execute | SKIP | SKIP | investigate |
| REPAIR | Targeted bug fix, failing test, specific defect | Minimal Scout + Execute + Harden | Resilience only | Full | implement |
| EVOLVE | System self-improvement, quality budget recovery | Evolution beads only | SKIP | SKIP | evolve |

Evolve beads follow a shortened status flow: `pending → running → submitted → verified → merged` (skip proven/hardened/reliability-proven — no user code to verify adversarially).

See `sdlc-os:sdlc-evolve` for the full Evolve profile specification.
```

- [ ] **Step 5: Add automatic and periodic Evolve triggers to Phase 0**

In the Phase 0 (Normalize) section of `sdlc-orchestrate/SKILL.md`, after the existing depth detection bullet points, add:

```markdown
**Evolve auto-trigger check (runs during every Phase 0):**
- If quality budget is WARNING or DEPLETED AND no user task is pending → auto-set profile to EVOLVE via FFT-01 Cue 3
- If this is the Nth task where N mod 20 == 0 → schedule an Evolve cycle after the current task completes (do not interrupt the user's task; queue it)
- Evolve cycles triggered by budget WARNING are immediate (before user task). Periodic Evolve cycles are deferred (after user task).
- Manual `/evolve` always takes priority over queued periodic cycles.
```

- [ ] **Step 6: Verify the file is well-formed**

Run: `head -5 /Users/q/.claude/plugins/sdlc-os/skills/sdlc-orchestrate/SKILL.md`
Expected: Valid frontmatter

- [ ] **Step 6: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat(skills): extend bead spec with FFT fields, add task profiles to sdlc-orchestrate"
```

---

### Task 8: Update scaling-heuristics.md to FFT Format

**Files:**
- Modify: `skills/sdlc-adversarial/scaling-heuristics.md`

This task replaces the prose signal checklists with references to the FFT decision trees.

- [ ] **Step 1: Read the current file**

Read `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-adversarial/scaling-heuristics.md` fully.

- [ ] **Step 2: Replace Cynefin Domain Assessment section**

Replace the "Cynefin Domain Assessment" section (the table and the signal lists from lines ~7-67) with:

```markdown
## Cynefin Domain Assessment

Bead domain classification is performed via **FFT-02** from `references/fft-decision-trees.md`. The Conductor traverses the FFT and records the traversal in the bead's decision trace.

FFT-02 replaces the previous signal checklists with a single-cue binary decision tree. Key behaviors:
- Cue 3 absorbs the security-sensitive override — auth touch = Complex + security_sensitive immediately
- 90% of classifications resolve with one cue (Gigerenzer ecological rationality)
- The traversal is auditable via the decision trace

The domain-to-AQS behavior table remains unchanged:

| Domain | AQS Behavior | Process Adjustments |
|---|---|---|
| **Clear** | Skip AQS entirely — bead goes `proven → merged` directly. | L0 runner only. Auto-merge if tests pass. No Sentinel needed if error budget is healthy. |
| **Complicated** | Recon burst fires (all 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. | Standard loop depth (L0-L2 + AQS). Expert review by domain-specific agents. |
| **Complex** | All four domains active. Full directed strike on HIGH/MED. Light sweep on LOW. Cycle 2 governed by convergence assessment. | Bead spec MUST include safe-to-fail section (rollback plan). Feature flags recommended for new behavior. Full adversarial engagement. |
| **Chaotic** | Skip AQS entirely. Act-first single runner. Fast-path approval. | Emergency process: single runner, L0 only, no Sentinel during execution. MANDATORY postmortem bead auto-created after merge — this bead goes through full Complicated-level review retroactively. |
| **Confusion** | Block. Bead cannot be created until reclassifiable. | Force decomposition. The Conductor must break the work down until each piece is classifiable as Clear, Complicated, or Complex. If decomposition fails, escalate to user for clarification. |
```

- [ ] **Step 3: Replace Domain Selection Heuristics section**

Replace the "Domain Selection Heuristics" section (lines ~70-132) with:

```markdown
## Domain Selection and Priority

Domain activation and priority are determined via **FFT-03** from `references/fft-decision-trees.md`, applied per domain after the recon burst completes.

FFT-03 formalizes the cross-reference matrix:
- Conductor + Recon agree → HIGH (20-40 guppies)
- Recon only (Conductor blind spot) → MED (10-20 guppies) — the most important case
- Conductor only (unconfirmed intuition) → LOW (5-10 guppies)
- Neither → SKIP

The Multi-Domain Activation Patterns table remains as a reference for the Conductor's initial domain selection before recon:

| Bead Type | Functionality | Security | Usability | Resilience |
|---|---|---|---|---|
| New REST endpoint | HIGH | HIGH | HIGH | MED |
| Auth change | MED | HIGH | LOW | LOW |
| Database schema + query changes | HIGH | HIGH | LOW | HIGH |
| UI component | MED | LOW | HIGH | LOW |
| Background job / worker | HIGH | LOW | LOW | HIGH |
| Internal refactor (no API change) | HIGH | LOW | LOW | LOW |
| Config / infrastructure change | LOW | MED | LOW | MED |
| Third-party integration | MED | HIGH | MED | HIGH |
| Error handling improvement | LOW | LOW | MED | HIGH |
```

- [ ] **Step 4: Replace Cycle Budget section with FFT-06 reference**

Replace the "Cycle Budget" section (lines ~154-161) with:

```markdown
### Cycle Budget

Cycle 2 decision is determined via **FFT-06** from `references/fft-decision-trees.md`.

Key behaviors:
- Any CRITICAL finding in Cycle 1 → Cycle 2 MANDATORY. If bead was CLEAR, auto-escalate to COMPLICATED (Kahneman certainty effect — zero-to-one threshold).
- Any accepted fix that changed code → Cycle 2 fires (verify fix holds)
- Stable process with no findings → Cycle 2 SKIP (Deming Funnel Rule 1: do not adjust a stable process)

**Maximum 2 full cycles per bead.** After 2 cycles, unresolved findings escalate to Conductor.
```

- [ ] **Step 5: Replace Budget Management guppy table with FFT-11 reference**

Replace the "Guppy Budget by Priority" table (lines ~139-146) with:

```markdown
### Guppy Budget by Priority

Budget allocation follows **FFT-11** from `references/fft-decision-trees.md`, implementing Taleb's barbell strategy:

| Priority | Guppies | Barbell Position |
|---|---|---|
| **HIGH** | 20-40 | Maximum scrutiny (barbell extreme) |
| **MED** (recon blind spot) | 10-20 | Justified middle — recon surfaced something unexpected |
| **LOW** | 5-10 | Light sweep |
| **SKIP** or **ACCIDENTAL** (non-security) | 0 | Minimum scrutiny (barbell extreme) |

Note: security_sensitive == true overrides ACCIDENTAL → guppies are never zero for security-sensitive beads regardless of complexity source.
```

- [ ] **Step 6: Verify file is coherent**

Run: `head -5 /Users/q/.claude/plugins/sdlc-os/skills/sdlc-adversarial/scaling-heuristics.md`
Expected: `# AQS Scaling Heuristics`

- [ ] **Step 7: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-adversarial/scaling-heuristics.md
git commit -m "feat(skills): replace prose heuristics with FFT references in scaling-heuristics"
```

---

### Task 9: Update sdlc-loop with FFT-05, FFT-07, FFT-08, Turbulence

**Files:**
- Modify: `skills/sdlc-loop/SKILL.md`

- [ ] **Step 1: Read the current file**

Read `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-loop/SKILL.md` to find the recovery patterns section and the bead status extensions.

- [ ] **Step 2: Add FFT references to loop depth section**

Find the section describing loop depth per complexity. Add after it:

```markdown
### FFT-Driven Loop Depth

Loop depth assignment is formalized via **FFT-05** from `references/fft-decision-trees.md`. Key behaviors:
- CHAOTIC → L0 only (act-first, postmortem retroactively)
- CONFUSION → BLOCKED (must decompose first)
- CLEAR + healthy budget → L0 only
- CLEAR + unhealthy budget → L0 + L1
- COMPLICATED → L0 + L1 + L2 + L2.5
- COMPLEX or security_sensitive → L0 + L1 + L2 + L2.5 + L2.75 (full pipeline)
```

- [ ] **Step 3: Add FFT-07 reference to escalation section**

Find the recovery patterns / escalation section. Add:

```markdown
### FFT-Driven Escalation

Escalation strategy at L3+ is formalized via **FFT-07** from `references/fft-decision-trees.md`. Key behaviors:
- Same error 3+ times across beads → ROOT_CAUSE_ANALYSIS (Dekker: fix the context, not the runner)
- Already re-decomposed once → ESCALATE_TO_USER
- Runner reported NEEDS_CONTEXT → ENRICH_AND_REDISPATCH
- Sunk cost check: "If starting fresh, would I choose this design?" → If NO: REDESIGN_BEAD
```

- [ ] **Step 4: Add FFT-08 deterministic routing to L1 sentinel**

Find the L1 Sentinel section. Add:

```markdown
### Deterministic Check Routing (FFT-08)

Before dispatching LLM-based sentinel checks, the Conductor applies **FFT-08** from `references/fft-decision-trees.md` to classify each verification check. Checks answerable by running a command (type-check, lint, test, file-exists, schema validation) are routed to shell scripts, not LLM agents. See `references/deterministic-checks.md` for the full catalog.

This directly improves pipeline reliability: replacing a p=0.95 LLM step with a p=1.0 script step contributes multiplicative improvement to end-to-end reliability (Karpathy March of Nines).
```

- [ ] **Step 5: Add turbulence tracking to bead status extensions**

Find the bead status tracking section. Add:

```markdown
### Turbulence Tracking

Every bead tracks its loop cycle consumption in the `Turbulence` field:

```
**Turbulence:** {L0: 1, L1: 0, L2: 0, L2.5: 0, L2.75: 0}
```

The Turbulence field is updated after each loop level completes:
- L0: increment when runner self-corrects (each attempt counts)
- L1: increment when sentinel flags and correction cycle runs
- L2: increment when oracle flags and correction cycle runs
- L2.5: increment per AQS cycle
- L2.75: increment per Phase 4.5 hardening cycle

**Turbulence Score** = total cycles consumed / expected cycles for beads of this Cynefin domain. Score near 1.0 = normal. Score > 2.0 = high turbulence (Kahneman duration neglect countermeasure — makes correction history visible even after bead reaches "hardened" status).

High-turbulence beads are flagged in the Phase 5 delivery summary and may warrant additional monitoring in production.
```

- [ ] **Step 6: Verify**

Run: `grep -c "FFT-0" /Users/q/.claude/plugins/sdlc-os/skills/sdlc-loop/SKILL.md`
Expected: At least 4 (FFT-05, FFT-07, FFT-08 references)

- [ ] **Step 7: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-loop/SKILL.md
git commit -m "feat(skills): add FFT-05/07/08 references and turbulence tracking to sdlc-loop"
```

---

### Task 10: Add HRO Constraints to sdlc-orchestrate Phase 5

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

- [ ] **Step 1: Read Phase 5 section**

Read `/Users/q/.claude/plugins/sdlc-os/skills/sdlc-orchestrate/SKILL.md` lines 198-209 (Phase 5: Synthesize).

- [ ] **Step 2: Add HRO structural constraints**

After the existing Phase 5 steps (after `haiku-handoff` packages delivery summary), add:

```markdown
5. **HRO Structural Constraints** (Weick — non-negotiable):

   **5a. Preoccupation with failure:** Every all-clean bead (zero findings across ALL loop layers) gets a mandatory "Why was this clean?" note in the decision trace. Clean results are suspicious until explained.

   **5b. Reluctance to simplify:** The delivery summary MUST contain at least one uncertainty, unknown, or open question. If the summary contains zero unknowns, flag as "suspiciously clean — reluctance-to-simplify gate failed." The Conductor cannot deliver a summary with zero unknowns.

   **5c. Sensitivity to operations:** Every 3rd bead, the Conductor reads raw sentinel logs, not just summaries. Logged in decision trace.

   **5d. Deference to expertise:** When a domain-specialist agent flags a finding, the Conductor CANNOT dismiss it — it MUST proceed to the corresponding Blue Team regardless of Conductor judgment. Conductor disagreement is logged in the decision trace for retrospective analysis, not used as a filter. Applies to ALL specialist agents: `red-functionality`, `red-security`, `red-usability`, `red-resilience`, `red-reliability-engineering`, `observability-engineer`, `error-hardener`.
```

- [ ] **Step 3: Verify**

Run: `grep -c "HRO" /Users/q/.claude/plugins/sdlc-os/skills/sdlc-orchestrate/SKILL.md`
Expected: At least 1

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat(skills): add Weick HRO structural constraints to Phase 5 Synthesize"
```

---

### Task 10b: Wire FFT-10 and FFT-12 into sdlc-orchestrate

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

FFT-10 (Complexity Source) and FFT-12 (Parallelization Safety) need explicit integration — not just bead fields but runtime behavior.

- [ ] **Step 1: Add FFT-10 complexity source routing to Phase 3 Architect**

In the Phase 3 (Architect) section of `sdlc-orchestrate/SKILL.md`, after the existing "Choose an approach. Define the bead decomposition" content, add:

```markdown
**Complexity Source Classification (FFT-10):** For each bead in the manifest, the Conductor applies FFT-10 from `references/fft-decision-trees.md` to classify complexity as ESSENTIAL or ACCIDENTAL:

- **ESSENTIAL** (novel business logic, new state machines, new domain models): Full AQS + hardening. This is where real bugs live.
- **ACCIDENTAL** (framework boilerplate, config, migrations, build tooling): Skip AQS adversarial, run deterministic checks only (FFT-08). Simplify, don't scrutinize.
- **Security override:** If `security_sensitive == true`, classification is forced to ESSENTIAL regardless of content. Security-sensitive config/auth/CORS changes look "accidental" but carry real risk.
- **Refactoring:** Refactoring beads are classified ACCIDENTAL — behavioral equivalence proof is needed, not adversarial probing. Use `sdlc-os:sdlc-refactor` skill.

The classification is recorded in the bead's `Complexity source` field and the decision trace.
```

- [ ] **Step 2: Add FFT-12 parallelization rules**

In the "Parallelization Rules" section of `sdlc-orchestrate/SKILL.md`, replace the existing safe/must-serialize lists with:

```markdown
## Parallelization Rules

Parallelization is determined via **FFT-12** from `references/fft-decision-trees.md`:

- Beads modifying the same file → **SERIALIZE**
- Bead B depends on bead A's output (explicit dependency) → **SERIALIZE**
- Both beads are read-only (investigation, audit, evolve) → **PARALLELIZE**
- Default → **PARALLELIZE** (independent beads run in parallel)

**Conflict resolution** (unchanged):
When parallel beads produce conflicting changes, the Conductor:
1. Reads both outputs
2. Dispatches a fresh runner with both outputs + conflict description
3. The resolver produces a merged result
4. Sentinel verifies the merge
```

- [ ] **Step 3: Verify FFT-10 and FFT-12 are referenced**

Run: `grep -n "FFT-10\|FFT-12" /Users/q/.claude/plugins/sdlc-os/skills/sdlc-orchestrate/SKILL.md`
Expected: At least 2 matches (one per FFT)

- [ ] **Step 4: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat(skills): wire FFT-10 complexity source and FFT-12 parallelization into orchestrate"
```

---

### Task 11: Update guard-bead-status.sh for Evolve Type

**Files:**
- Modify: `hooks/scripts/guard-bead-status.sh`

- [ ] **Step 1: Read the current file**

Read `/Users/q/.claude/plugins/sdlc-os/hooks/scripts/guard-bead-status.sh` to find the `verified)` case.

- [ ] **Step 2: Update the verified transition to support evolve beads**

The current `verified)` case at line ~105 only allows `verified → proven`. Evolve beads need `verified → merged`. Since the hook reads bead file content, we need to check the bead's Type field.

Find the `verified)` case and replace it with:

```bash
  verified)
    # Check if this is an evolve bead (verified -> merged is valid for evolve beads)
    BEAD_TYPE=$(echo "$CONTENT" | sed -n 's/^\*\*Type:\*\*[[:space:]]*\([a-z]*\).*/\1/p' | head -1 || true)
    if [[ "$BEAD_TYPE" == "evolve" ]]; then
      [[ "$CURRENT_STATUS" =~ ^(proven|merged|blocked|stuck|escalated)$ ]] && VALID=true
    else
      [[ "$CURRENT_STATUS" =~ ^(proven|blocked|stuck|escalated)$ ]] && VALID=true
    fi
    ;;
```

- [ ] **Step 3: Update the comment block**

Update the canonical flow comment to mention evolve beads:

```bash
# Canonical status flow:
# pending -> running -> submitted -> verified -> proven -> hardened -> reliability-proven -> merged
# Also valid: blocked, stuck, escalated (from any state)
#
# Trivial beads may skip: proven -> merged (skipping hardened and reliability-proven)
# Beads may skip reliability: hardened -> merged (when Phase 4.5 is not active)
# Evolve beads: verified -> merged (no code to prove/harden)
# But verified -> merged is NEVER valid for non-evolve beads (must go through proven)
# And verified -> hardened is NEVER valid (must go through proven)
```

- [ ] **Step 4: Verify syntax**

Run: `bash -n /Users/q/.claude/plugins/sdlc-os/hooks/scripts/guard-bead-status.sh`
Expected: No output (valid syntax)

- [ ] **Step 5: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add hooks/scripts/guard-bead-status.sh
git commit -m "feat(hooks): add evolve bead type with verified->merged status flow"
```

---

### Task 12: Bump Plugin Version

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Update version**

In `.claude-plugin/plugin.json`, change `"version": "5.0.0"` to `"version": "6.0.0"`.

This is a major version bump: the FFT Decision Architecture adds a foundational decision backbone, 4 task profiles, extended bead spec, HRO constraints, and the Evolve skill.

- [ ] **Step 2: Verify JSON**

Run: `cat /Users/q/.claude/plugins/sdlc-os/.claude-plugin/plugin.json | jq .`
Expected: Valid JSON with `"version": "6.0.0"`

- [ ] **Step 3: Commit**

```bash
cd /Users/q/.claude/plugins/sdlc-os
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 6.0.0 for FFT Decision Architecture"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Plan Task |
|---|---|
| Section 1: 12 FFTs | Task 1 (fft-decision-trees.md) |
| Section 2: Decision Trace | Task 4 (hook validates trace) + Task 7 (bead spec adds trace field) |
| Section 3: Bead Spec Extension | Task 7 |
| Section 4: Task Profiles | Task 5 (Evolve skill) + Task 6 (/evolve command) + Task 7 (profiles in orchestrate) |
| Section 5: HRO Constraints | Task 10 |
| Section 6: Phase B Attachments | Task 7 (placeholder fields in bead spec) |
| Section 7: Phase C Attachments | Deferred — not in Phase A scope |
| Section 8: Hook Enforcement | Task 4 (validate-decision-trace.sh) + Task 11 (guard-bead-status.sh) |
| Section 9: sdlc-evolve Skill | Task 5 |
| Section 10: Files Changed | All tasks mapped |
| Section 11: Design Decisions | Flat files (Task 4 path format), /evolve (Task 6), L0 unchanged |
| Section 12: Implementation Sequence | Tasks 1-12 follow spec sequence |
| Anti-patterns | Task 3 (anti-patterns.md) |
| Deterministic checks | Task 2 (deterministic-checks.md) |
| FFT-08 in loop | Task 9 |
| FFT-10/FFT-12 in orchestrate | Task 10b (complexity source routing in Phase 3, parallelization rules replaced) |

### Placeholder Scan
- No TBDs or TODOs
- Phase B fields explicitly labeled as "Phase B — not yet populated" (intentional)
- All code blocks complete

### Type Consistency
- FFT numbering (01-12) consistent across Tasks 1, 7, 8, 9, 10
- Bead fields match between Task 7 (bead spec) and Task 4 (hook validation)
- Profile names (BUILD|INVESTIGATE|REPAIR|EVOLVE) consistent across Tasks 5, 6, 7
- Status flow for evolve beads consistent between Task 5 and Task 11
