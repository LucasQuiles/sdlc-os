---
task-id: "consistency-agents-20260325"
description: "Implement SDLC consistency agents — 4 new agents, 2 skills, 2 commands, 1 reference file, 3 skill updates"
current-phase:
  number: 5
  name: "Complete"
complexity: complicated
cynefin: complicated
team-roster:
  - role: Conductor
    model: opus
  - role: Runners
    model: sonnet
  - role: Sentinel
    model: haiku
created-at: "2026-03-25T21:00:00Z"
spec: "docs/superpowers/specs/2026-03-25-sdlc-consistency-agents-design.md"
plan: "docs/superpowers/plans/2026-03-25-sdlc-consistency-agents.md"
decisions:
  - phase: 0
    decision: "Skip Normalize — clean SDLC entry, no prior artifacts for this task"
    rationale: "Session started fresh, spec and plan created in this session"
    timestamp: "2026-03-25T21:00:00Z"
  - phase: 1-3
    decision: "Skip Frame/Scout/Architect — spec and plan already exist"
    rationale: "Brainstorming produced approved spec, writing-plans produced 13-task plan"
    timestamp: "2026-03-25T21:00:00Z"
---

# Task State: consistency-agents-20260325

_Managed by Conductor. Updated at each phase transition._

## Bead Waves

**Wave A (parallel — no dependencies):** B1-ref, B2-scanner, B3-enforcer, B4-normalizer, B5-gap-analyst
**Wave B (parallel — depends on Wave A):** B6-skill-normalize, B7-skill-gap, B8-cmd-normalize, B9-cmd-gap
**Wave C (parallel — depends on Wave B):** B10-orchestrate, B11-fitness, B12-loop
**Wave D (serial — depends on all):** B13-verify
