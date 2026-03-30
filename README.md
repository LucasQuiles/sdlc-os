# SDLC-OS: Multi-Agent SDLC Operating System

A Claude Code plugin that orchestrates software delivery through multi-agent workflows. Opus conducts, Sonnet executes, Haiku watches.

## Installation

```bash
# Clone into your Claude Code plugins directory
git clone git@github.com:LucasQuiles/sdlc-os.git ~/.claude/plugins/sdlc-os
```

Restart Claude Code. The plugin auto-discovers agents, skills, commands, and hooks.

## Quick Start

```
/sdlc "build a user authentication system"
```

This starts the full SDLC workflow: Frame → Scout → Architect → Execute → Synthesize.

For simpler tasks, the Conductor scales down automatically — trivial tasks skip straight to Execute.

## Commands

| Command | Purpose |
|---------|---------|
| `/sdlc "task"` | Start a new SDLC workflow |
| `/audit [scope]` | Run architectural fitness checks |
| `/refactor "scope"` | Refactor with behavioral equivalence proof |
| `/wave` | Check/advance SDLC phase |
| `/gate` | Lightweight health check on current phase |
| `/swarm "problem"` | Dispatch guppy swarm at a problem |
| `/adversarial` | Trigger adversarial quality sweep |
| `/normalize` | Assess project state, produce convention map, align existing work |
| `/gap-analysis [mode]` | Feature completeness analysis (finder or finisher mode) |
| `/feature-sweep [mode]` | Discover neglected/abandoned/incomplete features across codebase |
| `/stress` | Manually invoke barbell stress testing on the current task |

## Architecture

### Roles

| Role | Model | What It Does |
|------|-------|-------------|
| **Conductor** | Opus | Decomposes work, distributes to runners, synthesizes results |
| **Runners** | Sonnet | Execute atomic work units (investigate, design, implement, review) |
| **Guppies** | Haiku | Disposable micro-agents for breadth-first investigation |
| **Sentinel** | Haiku | Continuous patrol — verifies evidence, checks handoffs |
| **Oracle** | All three | Truth council — verifies claims are honest across all work |

### Agents (30)

**Runners:** sonnet-investigator, sonnet-designer, sonnet-implementer, sonnet-reviewer

**Sentinel:** haiku-evidence, haiku-verifier, haiku-handoff

**Oracle:** oracle-test-integrity (sonnet), oracle-behavioral-prover (haiku), oracle-adversarial-auditor (opus)

**AQS Red Team:** red-functionality, red-security, red-usability, red-resilience

**AQS Blue Team:** blue-functionality, blue-security, blue-usability, blue-resilience

**Arbiter:** arbiter (opus) — Kahneman adversarial collaboration for disputes

**Scouts/Detectors:** reuse-scout, drift-detector

**Consistency:** convention-scanner, convention-enforcer, normalizer, gap-analyst

**Feature Archaeology:** feature-finder, feature-finisher

**Quality:** losa-observer

**Micro:** guppy

### Phases

```
Phase 0: Normalize  — mandatory session entry, detect existing work
Phase 1: Frame      — clarify requirements, define done
Phase 2: Scout      — explore codebase, map conventions, find gaps
Phase 3: Architect  — choose approach, decompose into beads
Phase 4: Execute    — build with parallel runners + sentinel loop
Phase 5: Synthesize — merge results, verify whole, deliver
```

### Loop Mechanics

Every role loops against its own metric. Failures self-correct at the lowest level before escalating:

```
L0: Runner self-correction (3 attempts)
L1: Sentinel correction (2 cycles) — includes drift-detector + convention-enforcer
L2: Oracle audit (2 cycles) — VORP standard
L2.5: AQS adversarial (2 cycles) — red/blue/arbiter
L3-L5: Bead → Phase → Task escalation
```

### Hooks (10 scripts)

| Hook | Event | Behavior |
|------|-------|----------|
| validate-aqs-artifact.sh | PostToolUse | **Blocking** — AQS schema validation |
| guard-bead-status.sh | PostToolUse | **Blocking** — illegal status transitions |
| lint-domain-vocabulary.sh | PostToolUse | **Blocking** — non-canonical domains |
| validate-quality-budget.sh | PostToolUse | **Blocking** — quality-budget.yaml schema validation |
| check-naming-convention.sh | PreToolUse | **Advisory** — Convention Map naming check |
| validate-consistency-artifacts.sh | PostToolUse | **Advisory** — feature matrix + convention report schemas |
| validate-runner-output.sh | SubagentStop | **Advisory** — runner output structure + convention signals |
| validate-hazard-defense-ledger.sh | PostToolUse | **Blocking** — HDL schema validation |
| validate-stress-session.sh | PostToolUse | **Blocking** — stress session schema validation |
| validate-decision-noise-summary.sh | PostToolUse | **Advisory** — decision-noise-summary.yaml schema validation |

### References

| File | Purpose |
|------|---------|
| reuse-patterns.md | Canonical function/pattern registry |
| fitness-functions.md | Architectural fitness check catalog |
| convention-dimensions.md | Convention categories for scanning/enforcement |
| confidence-labels.md | Verified/Likely/Assumed/Unknown taxonomy |
| code-constitution.md | Living quality rules from adversarial findings |
| precedent-system.md | Arbiter verdict database (stare decisis) |
| quality-slos.md | Error budget policy with SLIs/SLOs |
| calibration-protocol.md | Drift monitoring and noise audits |
| adversarial-quality.md | AQS quick reference |
| artifact-templates.md | Wave artifact templates |

## Per-Project Artifacts

The plugin creates these files in target project repos:

| Artifact | Path | Purpose |
|----------|------|---------|
| Convention Map | `docs/sdlc/convention-map.md` | Project's naming/style/structure conventions |
| Feature Matrix | `docs/sdlc/feature-matrix.md` | Neglected feature tracking |
| SDLC State | `docs/sdlc/active/{task-id}/` | Workflow state, bead files, AQS reports |
| Quality Budget | `docs/sdlc/active/{task-id}/quality-budget.yaml` | Task-level metrics, phase gate enforcement |
| System Budget | `docs/sdlc/system-budget.jsonl` | Cross-task longitudinal ledger |
| System Budget Events | `docs/sdlc/system-budget-events.jsonl` | Late-arriving escape corrections |
| Hazard/Defense Ledger | `docs/sdlc/active/{task-id}/hazard-defense-ledger.yaml` | Phase B safety control, defense coverage tracking |
| System HDL | `docs/sdlc/system-hazard-defense.jsonl` | Cross-task UCA patterns, catch-layer distribution |
| System HDL Events | `docs/sdlc/system-hazard-defense-events.jsonl` | Late-arriving defense corrections |
| Stress Session | `docs/sdlc/active/{task-id}/stress-session.yaml` | Barbell stress testing, stressor application tracking |
| System Stress | `docs/sdlc/system-stress.jsonl` | Cross-task stress yield, clean streak tracking |
| System Stress Events | `docs/sdlc/system-stress-events.jsonl` | Stressor lifecycle events |
| Stressor Library | `references/stressor-library.yaml` | Persistent stressor catalog |
| Decision Noise Summary | `docs/sdlc/active/{task-id}/decision-noise-summary.yaml` | Per-task MAP scores, noise index, escalations — advisory |
| Review Passes | `docs/sdlc/decision-noise/review-passes.jsonl` | System-level append-only ledger of all review passes |

## Testing

```bash
cd ~/.claude/plugins/sdlc-os
bash hooks/tests/test-hooks.sh
```

Expected: 54/54 PASS.

## License

MIT
