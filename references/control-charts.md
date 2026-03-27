# Control Charts and Statistical Process Control

Reference for applying SPC within SDLC-OS calibration, noise audits, fitness functions, and reliability ledger interpretation. Use in conjunction with `agents/variation-classifier.md`.

---

## Control Chart Construction

To construct a control chart for any SDLC-OS metric:

1. Collect N measurements (minimum 5; ideally 10+)
2. Compute mean: x̄ = (Σxᵢ) / N
3. Compute standard deviation: σ = √(Σ(xᵢ − x̄)² / N)
4. Set limits:
   - Upper Control Limit (UCL) = x̄ + 3σ
   - Lower Control Limit (LCL) = x̄ − 3σ
   - Upper Warning Limit (UWL) = x̄ + 2σ
   - Lower Warning Limit (LWL) = x̄ − 2σ
   - Upper 1σ band = x̄ + 1σ
   - Lower 1σ band = x̄ − 1σ
5. Plot measurements in time order with all six reference lines
6. Apply Western Electric rules to detect non-random patterns

Control limits describe the voice of the process — what the system will produce when operating normally. Specification limits (targets, thresholds) are separate and must not be confused with control limits.

---

## Western Electric Rules

Apply to consecutive measurements in time order. A single triggered rule classifies the signal as SPECIAL CAUSE.

| Rule | Description | What It Signals |
|------|-------------|-----------------|
| 1 | 1 point beyond 3σ (outside UCL or LCL) | Obvious special cause — large sudden shift or spike |
| 2 | 2 of 3 consecutive points beyond 2σ on the same side of mean | Subtle shift — process level has moved |
| 3 | 4 of 5 consecutive points beyond 1σ on the same side of mean | Gradual drift — slow creep away from center |
| 4 | 8 consecutive points on the same side of mean (any magnitude) | Sustained shift — process mean has changed |

**Evaluation notes:**
- Rules 2, 3, and 4 require same-side consistency — points alternating above and below do not trigger these rules even if magnitudes are large
- Evaluate all four rules on every new measurement; any single trigger is sufficient for SPECIAL CAUSE classification
- Do not require multiple rules to trigger before acting on a special cause

---

## Deming Funnel Rules

The Funnel Rules describe four ways to respond to process output. Only Rule 1 is correct for common-cause variation. Rules 2, 3, and 4 are always wrong and always increase variation.

| Rule | Description | Result |
|------|-------------|--------|
| 1 | Leave the process alone — take no action | Stable — CORRECT response to common cause |
| 2 | Adjust based on the last result (aim at where last marble landed) | Doubles variation — ALWAYS WRONG |
| 3 | Adjust based on cumulative error from target (aim at mirror of last landing) | Increases variation without bound — ALWAYS WRONG |
| 4 | Apply someone else's adjustment to your process (copy the last position) | Random walk — ALWAYS WRONG |

**Key insight (Red Bead Experiment):** Workers (agents) performing a stable process cannot improve outcomes through effort or intent. The system produces what the system is designed to produce. Improvement requires changing the system — and only Rule 1 (leave alone) applies when the system is in control.

---

## SDLC-OS Application

| Metric | Where Measured | Common Cause Fix | Special Cause Fix |
|--------|---------------|-----------------|------------------|
| Detection rate (calibration) | `references/calibration-protocol.md` | Improve planted defect diversity; add rubric examples; vary defect types across severity levels | Fix specific agent prompt that missed the defect; review context window at time of failure |
| Noise overlap % (noise audit) | `references/calibration-protocol.md` | Standardize rubrics across agents; add anchored examples with scores; reduce ambiguous language in rubric | Reset specific agent context; investigate bead ordering effects; check for prompt injection in noisy input |
| Fitness scores | `references/fitness-functions.md` | Review fitness function thresholds for calibration drift; update examples in fitness definitions | Fix specific rule that is miscalibrated; check if a recent architecture change invalidated a rule |
| L0/L1/L2 rates (reliability ledger) | `references/reliability-ledger.md` | Improve system-wide prompts and bead specs; review FFT-09 SKIP usage patterns | Fix specific runner or sentinel prompt that produced the anomalous result; investigate input conditions |

---

## Minimum Data Requirements

- Require ≥ 5 historical measurements to compute meaningful control limits
- With 3–4 measurements, use moving range chart: estimate σ ≈ R̄ / d2, where R̄ = average of successive absolute differences and d2 = 1.128 (for subgroup size 2)
- With fewer than 3 measurements, report "insufficient data" — do not classify
- Treat first 5 measurements as provisional limits; recalculate and stabilize limits as data accumulates to 10+
- When limits are provisional, bias toward COMMON CAUSE classification to avoid premature tampering; require Rule 1 violation (point beyond 3σ) as minimum threshold for SPECIAL CAUSE with provisional limits

---

## Source

- Deming, W.E.: System of Profound Knowledge (SoPK) — Knowledge of Variation
- Western Electric Company: Statistical Quality Control Handbook (1956)
- thinkers-lab namespace: antipattern-1 (Tampering), methods/781821076d04250f (Red Bead Experiment)
