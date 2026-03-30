# Hazard/Defense Ledger — Phase 2 of Cross-Cutting Thinker Enhancement

**Date:** 2026-03-29
**Status:** Stub — ready for brainstorming
**Roadmap position:** Phase 2 of 5 (Quality Budget [DONE] → **Hazard/Defense Ledger** → Stressor Harvesting → Decision-Noise Controls → Mode/Convergence Signals)
**Depends on:** Phase 1 (quality-budget.yaml, derivation scripts, system ledger pattern)

---

## Scoping Decisions (from user)

1. **Canonical artifact:** `hazard-defense-ledger.yaml` at task level, plus a longitudinal system ledger/events sink
2. **Unit of record:** hazard, unsafe_control_action, intended_defense, actual_catch_point, residual_risk, owner
3. **Derivation model:** Consume bead traces, AQS findings, LOSA confirmations, and completion gates — not free-text summaries
4. **Gate points:** Required for complex and security-sensitive work before Synthesize, finalized before Complete
5. **Outcome metrics:** Defense coverage, catch-layer distribution, late escapes by missing defense, repeated UCA patterns

## Thinker Connections

| Thinker | What Hazard/Defense Ledger operationalizes |
|---------|-------------------------------------------|
| **Leveson (STPA/STAMP)** | Unsafe control actions become first-class tracked records, not narrative annotations. Control action → UCA → defense → catch point is the STPA loop made auditable. |
| **Reason (Swiss Cheese)** | Defense layers become measurable: intended vs actual catch point reveals which cheese slices have holes. Defense coverage metric = slice integrity. |
| **Dekker (Drift/Just Culture)** | Repeated UCA patterns across tasks = normalization of deviance signal. Catch-layer distribution shifting outward = drift into failure. |
| **Deming** | Catch-layer distribution over time feeds control charts. Defense coverage is an SLI. |
| **Meadows** | Defense layers are system buffers. Buffer hits (escapes past intended defense) are stock-flow signals. |

---

## Next Step

Brainstorm this spec through the full design flow: schema design, derivation sources, gate enforcement, integration with existing STPA/safety artifacts, and implementation surface.
