---
name: sdlc-status
description: "Display current SDLC workflow state — active phase, bead progress, sentinel alerts, and pending actions."
---

# SDLC Status

> **RUNTIME_DISPATCH_POLICY_V1 (normative):** Displayed runner and tier names are
> reported labels, not proof of runtime identity. Show requested and observed
> model data separately from accepted receipts; unknown remains unknown. Never
> render required work as completed from a role name, bead status, or file alone.

Display the current state of active SDLC workflows.

## What to Show

Read `docs/sdlc/active/*/state.md` and `docs/sdlc/active/*/beads/*.md` to render:

```
## SDLC: {task description}
**Phase:** {current phase} | **Complexity:** {trivial/moderate/complex}
**Started:** {timestamp}

### Bead Progress
| ID | Type | Status | Runner | Sentinel | AQS |
|----|------|--------|--------|----------|-----|
| {id} | implement | hardened | sonnet-implementer | clean | 2 domains, 0 findings |
| {id} | implement | verified | sonnet-implementer | clean | pending |
| {id} | implement | running | sonnet-implementer | watching | — |
| {id} | investigate | pending | unassigned | — | — |

Status flow: `pending → running → submitted → verified → proven → hardened → merged`
(Clear beads skip AQS: `proven → merged` directly)

### AQS Summary (non-trivial beads)
- **Domains tested:** {e.g., security, functionality, usability, resilience}
- **Findings count:** {N accepted / N rebutted / N disputed}
- **Arbiter verdicts:** {N binding verdicts issued}
- **Residual risk:** {none / documented}

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
