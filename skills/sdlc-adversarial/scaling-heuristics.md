# AQS Scaling Heuristics

Rules for when to activate AQS, which domains to select, how to allocate guppy budget, and when to abort. Applied by the Conductor during Phase 1.

---

## Cynefin Domain Assessment

Bead domain classification is performed via **FFT-02** from `references/fft-decision-trees.md`. The Conductor traverses the FFT and records the traversal in the bead's decision trace.

FFT-02 replaces the previous signal checklists with a single-cue binary decision tree. Key behaviors:
- Cue 3 absorbs the security-sensitive override — auth touch = Complex + security_sensitive immediately
- 90% of classifications resolve with one cue (Gigerenzer ecological rationality)
- The traversal is auditable via the decision trace

The domain-to-AQS behavior table remains unchanged:

| Domain | AQS Behavior | Process Adjustments |
|---|---|---|
| **Clear** | Skip AQS entirely — bead goes `proven → merged` directly. | L0 runner only. Auto-merge if tests pass. No Sentinel needed if error budget is healthy. |
| **Complicated** | Recon burst fires (all 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. | Standard loop depth (L0-L2 + AQS). Expert review by domain-specific agents. |
| **Complex** | All four domains active. Full directed strike on HIGH/MED. Light sweep on LOW. Cycle 2 governed by convergence assessment. | Bead spec MUST include safe-to-fail section (rollback plan). Feature flags recommended for new behavior. Full adversarial engagement. |
| **Chaotic** | Skip AQS entirely. Act-first single runner. Fast-path approval. | Emergency process: single runner, L0 only, no Sentinel during execution. MANDATORY postmortem bead auto-created after merge — this bead goes through full Complicated-level review retroactively. |
| **Confusion** | Block. Bead cannot be created until reclassifiable. | Force decomposition. The Conductor must break the work down until each piece is classifiable as Clear, Complicated, or Complex. If decomposition fails, escalate to user for clarification. |

---

## Domain Selection and Priority

Domain activation and priority are determined via **FFT-03** from `references/fft-decision-trees.md`, applied per domain after the recon burst completes.

FFT-03 formalizes the cross-reference matrix:
- Conductor + Recon agree → HIGH (20-40 guppies)
- Recon only (Conductor blind spot) → MED (10-20 guppies) — the most important case
- Conductor only (unconfirmed intuition) → LOW (5-10 guppies)
- Neither → SKIP

The Multi-Domain Activation Patterns table remains as a reference for the Conductor's initial domain selection before recon:

| Bead Type | Functionality | Security | Usability | Resilience |
|---|---|---|---|---|
| New REST endpoint | HIGH | HIGH | HIGH | MED |
| Auth change | MED | HIGH | LOW | LOW |
| Database schema + query changes | HIGH | HIGH | LOW | HIGH |
| UI component | MED | LOW | HIGH | LOW |
| Background job / worker | HIGH | LOW | LOW | HIGH |
| Internal refactor (no API change) | HIGH | LOW | LOW | LOW |
| Config / infrastructure change | LOW | MED | LOW | MED |
| Third-party integration | MED | HIGH | MED | HIGH |
| Error handling improvement | LOW | LOW | MED | HIGH |

---

## Budget Management

### Guppy Budget by Priority

Budget allocation follows **FFT-11** from `references/fft-decision-trees.md`, implementing Taleb's barbell strategy:

| Priority | Guppies | Barbell Position |
|---|---|---|
| **HIGH** | 20-40 | Maximum scrutiny (barbell extreme) |
| **MED** (recon blind spot) | 10-20 | Justified middle — recon surfaced something unexpected |
| **LOW** | 5-10 | Light sweep |
| **SKIP** or **ACCIDENTAL** (non-security) | 0 | Minimum scrutiny (barbell extreme) |

Note: security_sensitive == true overrides ACCIDENTAL → guppies are never zero for security-sensitive beads regardless of complexity source.

**FFT-15 stress override:** If FFT-15 returns FULL or TARGETED for this task, override the guppy budget to HIGH (20-40) regardless of the domain priority level. Stress-sampled tasks have already been identified as needing maximum scrutiny — do not let domain heuristics reduce the budget below HIGH.

### Arbiter Budget

**Maximum 3 arbiter invocations per bead.** If more than 3 findings reach `disputed` status, halt and recalibrate the red/blue pair before proceeding. See `arbitration-protocol.md` for the recalibration trigger.

Each arbiter invocation uses Opus. Budget accordingly — Opus invocations are expensive. The Conductor should note if a bead is consuming disproportionate arbiter budget and flag it.

### Cycle Budget

Cycle 2 decision is determined via **FFT-06** from `references/fft-decision-trees.md`.

Key behaviors:
- Any CRITICAL finding in Cycle 1 → Cycle 2 MANDATORY. If bead was CLEAR, auto-escalate to COMPLICATED (Kahneman certainty effect — zero-to-one threshold).
- Any accepted fix that changed code → Cycle 2 fires (verify fix holds)
- Stable process with no findings → Cycle 2 SKIP (Deming Funnel Rule 1: do not adjust a stable process)

**Maximum 2 full cycles per bead.** After 2 cycles, unresolved findings escalate to Conductor.

---

## Cross-Reference Decision Matrix

Applied after Phase 1 (Conductor selection + recon burst) completes. Determines final strike priority per domain.

```
for each domain in [functionality, security, usability, resilience]:

  conductor_selected = Conductor marked this domain as relevant
  recon_signal       = At least one recon guppy for this domain returned SIGNAL

  if conductor_selected AND recon_signal:
    priority = HIGH          # Both agree: most important — full strike
    strike_volume = 20-40 guppies

  elif (NOT conductor_selected) AND recon_signal:
    priority = MED           # Recon surfaced a blind spot — Conductor reconsiders
    strike_volume = 10-20 guppies
    note: "Recon overrode Conductor — review why this was missed in Phase 1"

  elif conductor_selected AND (NOT recon_signal):
    priority = LOW           # Conductor intuition not confirmed by recon — light sweep
    strike_volume = 5-10 guppies
    note: "If strike finds nothing, close domain as clean"

  elif (NOT conductor_selected) AND (NOT recon_signal):
    priority = SKIP
    strike_volume = 0
```

The `recon-only = MED` case is the most important. It catches Conductor blind spots. The Conductor must document why recon found a signal the Conductor missed — this is calibration feedback.

---

## When to Abort AQS

Stop the AQS cycle and close the domain or the entire engagement under these conditions:

**Domain-level abort:**
- The domain produced 0 guppy hits after a full strike (all guppies returned MISS or NO_SIGNAL). Close the domain as clean. Do not fire Cycle 2 for this domain.
- The domain is LOW priority and the light sweep produced 0 hits. Close immediately without escalating to full strike.

**Engagement-level abort:**
- **All-domain NO_SIGNAL confirmed:** All 8 recon guppies returned NO_SIGNAL and the Conductor independently assessed all domains as SKIP. AQS completes immediately without any strike. This is a valid and expected outcome for well-constructed beads.
- **Blocked by external dependencies:** The bead's code cannot be meaningfully analyzed without access to a running environment, production data, or external services that are not available. Document what was blocked and why, then close with `DEFERRED`.
- **Already human-reviewed:** The bead has already undergone a live security review, penetration test, or formal audit covering the same scope within the current sprint. AQS would be redundant. Document the existing review and close with `HARDENED` (crediting the external review). This requires Conductor verification — do not self-certify.

**Do not abort for:**
- Time pressure (AQS budget is fixed; if it is too expensive, adjust complexity tier thresholds, not individual engagements)
- Low confidence in findings (low-confidence findings should be downgraded to Assumed, not dropped)
- Red team frustration with blue team responses (that is what the Arbiter is for)
