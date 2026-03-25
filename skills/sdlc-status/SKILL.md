---
name: sdlc-status
description: "Display current SDLC workflow state — active phase, bead progress, sentinel alerts, and pending actions."
---

# SDLC Status

Display the current state of active SDLC workflows.

## What to Show

Read `docs/sdlc/active/*/state.md` and `docs/sdlc/active/*/beads/*.md` to render:

```
## SDLC: {task description}
**Phase:** {current phase} | **Complexity:** {trivial/moderate/complex}
**Started:** {timestamp}

### Bead Progress
| ID | Type | Status | Runner | Sentinel |
|----|------|--------|--------|----------|
| {id} | implement | verified | sonnet-implementer | clean |
| {id} | implement | running | sonnet-implementer | watching |
| {id} | investigate | pending | unassigned | — |

### Sentinel Alerts
- {any active flags from sentinel — or "No active alerts"}

### Next Action
{What should happen next — specific and actionable}
```

## If No Active Workflow

```
No active SDLC workflow. Use `/sdlc "task description"` to start one.
```

## Multiple Active Workflows

List all with one-line summaries. Let user choose which to inspect.
