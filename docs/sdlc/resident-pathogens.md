# Resident Pathogen Registry

Persistent cross-task accumulation of latent conditions, grouped by upstream layer.
Maintained by latent-condition-tracer (Haiku). Updated after every accepted finding.

**Purpose (Reason Swiss Cheese model):** Defenses have holes. Pathogens are the latent conditions that enlarge those holes. Tracking them across tasks reveals systemic weaknesses invisible to per-task analysis. GROWING pathogens automatically generate Evolve beads — auto-rule generation targets the layer with the most pathogens.

---

## Registry

| Layer | Pathogen Type | Count | Last Seen | Trend |
|-------|---------------|-------|-----------|-------|
| — | — | — | — | — |

*Registry is empty. Populated by latent-condition-tracer after accepted AQS or Phase 4.5 findings.*

---

## Layer Reference

Latent conditions are classified by which upstream layer should have caught the finding:

| Layer Code | Layer Name |
|---|---|
| L0 Runner | Prompt gap, spec ambiguity, missing context |
| L1 Sentinel | Drift-detector blind spot, convention gap |
| L2 Oracle | VORP check missed this claim type |
| L2.5 AQS | Attack library gap, domain selection miss |
| L2.75 Hardening | Observability gap, error handling gap |
| Convention Map | Unmapped pattern |
| Code Constitution | Missing rule |
| Safety Constraints | Missing constraint |
| Hook/Guard | Validator didn't catch this pattern |

## Trend Key

| Trend | Meaning |
|---|---|
| GROWING | Count increasing across recent tasks — generates Evolve bead |
| STABLE | Count flat — monitor |
| SHRINKING | Count decreasing — remediation working |
| RESOLVED | No longer observed — candidate for retirement |
