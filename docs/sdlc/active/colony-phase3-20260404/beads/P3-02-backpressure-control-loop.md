# Bead: P3-02
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** [P3-01]
**Scope:** `colony/backpressure.ts`, `colony/backpressure.test.ts`
**Cynefin domain:** complicated
**Security sensitive:** false
**Complexity source:** essential
**Profile:** BUILD
**Decision trace:** docs/sdlc/active/colony-phase3-20260404/beads/P3-02-decision-trace.md
**Deterministic checks:** npx vitest run colony/backpressure.test.ts
**Turbulence:** {L0: 0, L1: 0, L2: 0, L2.5: 0, L2.75: 0}

## Objective
Implement backpressure as a control loop per spec §15. Backpressure signals (stuck tasks, retries, oscillations, rising escalation rate) trigger concrete responses — not just logging.

## Approach
Implement `BackpressureController` class that:
1. `evaluateSignals(workstreamId)` — query events.db for backpressure indicators:
   - Stuck tasks: same bead retried 3+ times without new evidence → pause retries, escalate
   - Oscillating state: bead bounced 3+ times → freeze bead, create diagnostic finding
   - Rising escalation rate: >50% findings escalating → slow promotion, increase Brick depth
   - Queue starvation: no pending work >30min + idle agents → trigger DISCOVER
   - Low-confidence accumulation: >10 open findings below 0.5 → trigger clustering pass
   - Review loop disagreement: 3+ reviewer rejections → escalate to higher tier
2. `getResponse(signal)` — return the concrete action for each signal type
3. Each response is a structured action object the Conductor or Deacon can execute
4. Tests for each signal/threshold/response pair from spec §15 table
