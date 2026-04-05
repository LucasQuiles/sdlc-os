# Bead: P2-04
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P2-01, P2-02]
**Scope:** `colony/conductor-prompt.md`, `skills/sdlc-orchestrate/colony-mode.md`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** /home/q/LAB/sdlc-os/docs/sdlc/active/colony-phase2-20260404/beads/P2-04-decision-trace.md
**Deterministic checks:** grep -n 'cross-model\|review.loop\|worker_type' colony/conductor-prompt.md
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Define the cross-model review loop protocol in conductor-prompt.md and colony-mode.md. When a bead is authored by Claude, the review bead should be dispatched to Codex (and vice versa). The orchestrator mediates via artifact handoff, not model-to-model chat.

## Approach
1. Add to conductor-prompt.md EVALUATE section: after L0 completion, when dispatching L1 (sentinel):
   - If the L0 worker was `claude_code`, dispatch L1 review to `codex` worker_type
   - If the L0 worker was `codex`, dispatch L1 review to `claude_code` worker_type
   - Log the cross-model assignment in the journal entry
2. Update colony-mode.md bead-context.md protocol: add `prior_worker_type` field so the reviewing worker knows which model authored the code
3. Add to DISPATCH logic: worker_type selection based on bead complexity AND cross-model alternation for review beads
4. Document the dynamic role assignment rule: "reviewer is not always the same model as author" per spec §6.2

## Output
- Modified `colony/conductor-prompt.md` with cross-model review protocol
- Modified `skills/sdlc-orchestrate/colony-mode.md` with updated bead-context.md fields
