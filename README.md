# SDLC-OS

A Claude Code plugin that turns software delivery into a multi-agent workflow. Opus conducts. Sonnet executes. Haiku watches. Nobody trusts anybody — that's the point.

## What This Is

A structured software development lifecycle that runs inside Claude Code. Instead of one model doing everything and hoping for the best, SDLC-OS decomposes work across specialized agents with built-in adversarial review, drift detection, and continuous verification.

The premise: an AI that reviews its own work finds nothing wrong with it. An AI that reviews *someone else's* work is considerably more honest. So every piece of work gets built by one agent and reviewed by a different one, with a third watching both of them.

## Installation

```bash
git clone git@github.com:LucasQuiles/sdlc-os.git ~/.claude/plugins/sdlc-os
```

Restart Claude Code. The plugin auto-discovers agents, skills, commands, and hooks.

## Quick Start

```
/sdlc "build a user authentication system"
```

This kicks off the full workflow: normalize existing state, frame requirements, scout the codebase, architect the approach, execute in parallel, synthesize the results. For trivial tasks, it scales down automatically — not everything needs six phases.

## Commands

| Command | What It Does |
|---------|-------------|
| `/sdlc "task"` | Start a full SDLC workflow |
| `/refactor "scope"` | Refactor with continuous behavioral equivalence proof |
| `/audit` | Run architectural fitness checks (DRY, SSOT, SoC, conventions) |
| `/adversarial` | Trigger red team/blue team quality sweep |
| `/swarm "problem"` | Throw a swarm of disposable micro-agents at a problem |
| `/normalize` | Assess project state and produce a convention map |
| `/gap-analysis` | Map what exists vs what's needed (or verify delivery completeness) |
| `/feature-sweep` | Find neglected, incomplete, and abandoned features across the codebase |
| `/gate` | Quick health check on the current phase |
| `/wave` | Check or advance SDLC phase |

## How It Works

### Roles

| Role | Model | Job |
|------|-------|-----|
| **Conductor** | Opus | Decomposes work, distributes to runners, synthesizes results |
| **Runners** | Sonnet | Execute atomic work units — investigate, design, implement, review |
| **Guppies** | Haiku | Disposable micro-agents for breadth-first investigation. One question, one answer, done. |
| **Sentinel** | Haiku | Continuous patrol. Verifies evidence, checks handoffs, catches drift. |
| **Oracle** | Mixed | Truth council. Three agents that independently verify claims are honest. |

### Phases

```
0  Normalize   detect existing work, map conventions, avoid clobbering in-progress state
1  Frame       clarify requirements, define done, identify unknowns
2  Scout       explore codebase, find reusable code, map architecture
3  Architect   choose approach, decompose into atomic work units ("beads")
4  Execute     parallel runners + sentinel loop + adversarial review
5  Synthesize  merge results, verify the whole, deliver
```

### The Loop System

Every role loops against its own metric. Failures self-correct at the lowest level before escalating:

```
L0  Runner self-correction          3 attempts before escalating
L1  Sentinel correction             drift-detector + convention-enforcer
L2  Oracle audit                    three independent verification agents
L2.5  Adversarial quality (AQS)    red team attacks, blue team defends, arbiter resolves disputes
L3-L5  Bead -> Phase -> Task        structural escalation when loops exhaust their budget
```

The red team (functionality, security, usability, resilience specialists) attacks completed work. The blue team defends it. If they disagree, the arbiter runs a Kahneman adversarial collaboration protocol to produce a binding verdict. Every finding gets minimized to its smallest reproducible case before anyone acts on it.

### Agents (30)

**Runners:** sonnet-investigator, sonnet-designer, sonnet-implementer, sonnet-reviewer

**Sentinel:** haiku-evidence, haiku-verifier, haiku-handoff

**Oracle:** oracle-test-integrity, oracle-behavioral-prover, oracle-adversarial-auditor

**Red Team:** red-functionality, red-security, red-usability, red-resilience

**Blue Team:** blue-functionality, blue-security, blue-usability, blue-resilience

**Arbiter:** arbiter (Kahneman adversarial collaboration for disputes)

**Infrastructure:** reuse-scout, drift-detector, convention-scanner, convention-enforcer, normalizer, gap-analyst, feature-finder, feature-finisher, losa-observer, guppy

### Hooks (12)

Validation scripts that run on tool use events. Some block (you can't proceed until the artifact is valid), some advise (flag the issue but don't stop work).

Blocking: AQS artifact schema, bead status transitions, domain vocabulary, quality budget schema, hazard-defense ledger, stress session schema.

Advisory: naming conventions, consistency artifacts, runner output structure, decision noise, mode convergence, phase transitions.

## Per-Project Artifacts

SDLC-OS creates tracking files in the target project:

| Artifact | Purpose |
|----------|---------|
| Convention Map | Project naming, style, and structure conventions |
| Feature Matrix | Neglected feature tracking |
| Quality Budget | Per-task metrics and phase gate enforcement |
| Hazard-Defense Ledger | Safety controls and defense coverage |
| Stress Session | Barbell stress testing results |
| System Ledgers | Cross-task longitudinal data (JSONL append-only) |

These live in `docs/sdlc/` in the target repo. The plugin manages them; you read them when curious about what happened.

## Testing

```bash
cd ~/.claude/plugins/sdlc-os
bash hooks/tests/test-hooks.sh    # 62 tests
```

## Why

Most AI coding workflows are optimistic: generate code, run tests, ship if green. This works until it doesn't — and when it doesn't, the failure mode is subtle. Tests pass but behavior is wrong. Code works but drifts from conventions. Reviews approve because the reviewer is the same model that wrote the code.

SDLC-OS is pessimistic by design. It assumes every claim is wrong until independently verified, every piece of code has drifted until the detector says otherwise, and every review is theatrical until the oracle confirms it examined real evidence. This is slower. It catches more.

Whether the tradeoff is worth it depends on how much you trust a single model to be honest about its own work.

## License

MIT
