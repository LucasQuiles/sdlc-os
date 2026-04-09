# Bead: P2-03
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P2-02]
**Scope:** `colony/conductor-prompt.md`, `colony/brick-hooks.ts`, `colony/brick-hooks.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase2-20260404/beads/P2-03-decision-trace.md
**Deterministic checks:** npx vitest run colony/brick-hooks.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Wire Brick `brick_preprocess` into the EVALUATE path. When the Conductor evaluates a completed bead, Brick preprocesses the worker's diff/output/logs and returns a distilled artifact the Conductor uses for evaluation.

## Approach
1. Create `colony/brick-hooks.ts` — a thin wrapper that calls `brick_preprocess` MCP tool with:
   - task_class: 'diff_review'
   - format_hint: 'diff'
   - intent_key: 'flag_risks'
   - content: the bead-output.md + git diff from the worker's clone
2. Returns: distilled summary with flagged risks, decisions, uncertainties
3. Add to conductor-prompt.md EVALUATE section: before calling bridge, call Brick preprocessing on the worker output. Use the distilled result to inform evaluation quality.
4. Handle Brick unavailability gracefully — if the MCP tool fails, continue evaluation without enrichment (degraded mode per spec §16.1)
5. Test: mock brick_preprocess response, verify the hook extracts and formats correctly

## Output
- New `colony/brick-hooks.ts` with preprocessForEvaluation()
- New `colony/brick-hooks.test.ts`
- Modified `colony/conductor-prompt.md` EVALUATE section
