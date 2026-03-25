---
name: sdlc
description: "Start a new Multi-Agent SDLC workflow"
arguments:
  - name: task
    description: "Task description (what needs to be done)"
    required: true
---

Start a new SDLC workflow using the `sdlc-os:sdlc-orchestrate` skill.

1. Create task ID from description (slugified + timestamp)
2. Create `docs/sdlc/active/{task-id}/state.md` with initial metadata
3. Create `docs/sdlc/active/{task-id}/beads/` directory
4. Assess complexity (trivial / moderate / complex)
5. Begin Phase 1 (Frame) or skip to Execute for trivial tasks
