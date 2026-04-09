# Bead: P2-01
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** none
**Scope:** `colony/conductor-prompt.md`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase2-20260404/beads/P2-01-decision-trace.md
**Deterministic checks:** grep -n 'journal' colony/conductor-prompt.md
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Add journal read/write protocol to conductor-prompt.md. At session start, the Conductor reads the latest journal entries for context reconstruction. At session end, it writes a structured + narrative journal entry capturing decisions, dispatches, evaluations, and uncertainties.

## Approach
1. Add to Session Bootstrap Protocol (after step 4 tmup_inbox):
   - Step 5: Read conductor journal — query events.db for latest 3 entries for this workstream. Parse structured decisions and narrative. Use as context for current session decisions.
2. Add to each session type (DISPATCH, EVALUATE, SYNTHESIZE, RECOVER, DISCOVER) before "Exit":
   - Write journal entry with: beads dispatched/evaluated, decisions with evidence/alternatives/uncertainty, findings created/promoted/suppressed, next recommended actions, and narrative summary
3. Add DISCOVER session type section (currently missing from conductor-prompt.md)

## Output
- Modified `colony/conductor-prompt.md` with journal protocol + DISCOVER session
