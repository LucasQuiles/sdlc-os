# Quality SLOs and Error Budget Policy

Quality governance for agent-generated code. The Conductor tracks these indicators during Phase 5 (Synthesize) and applies the error budget policy to subsequent tasks.

---

## Quality SLIs (Service Level Indicators)

| SLI | How Measured | Notes |
|-----|-------------|-------|
| **Lint pass rate** | % of generated code passing all configured lint rules on first submission | Measured per bead at L0 |
| **Type safety rate** | % of generated code passing type checker on first run | Measured per bead at L0 |
| **Test coverage delta** | Net change in test coverage from each bead | Must not decrease — measured during Sentinel check |
| **Cognitive complexity** | Maximum per-function cognitive complexity in changed code | Measured via fitness functions |
| **AQS critical finding rate** | Critical/high findings per task | Measured during AQS engagement |

---

## Quality SLOs (Service Level Objectives)

| SLI | Target | Rationale |
|-----|--------|-----------|
| Lint pass rate | >= 95% | Agents should produce clean code by default |
| Type safety rate | >= 98% | Type errors indicate fundamental misunderstanding |
| Test coverage delta | >= 0 | Never decrease coverage — new code must bring its own tests |
| Cognitive complexity | <= 15 per function | Beyond 15, code becomes hard for both humans and LLMs to reason about |
| AQS critical finding rate | < 1 per task | More than 1 critical finding per task indicates systemic generation issues |
| Feedback channel health | >= 80% channels GREEN | All sensors/guards functioning; measured via safety-analyst probe-based health check per L3 mechanism; checked each Evolve cycle and post-L3-escalation |
| stress_yield | Stress session catch rate | >= 0.10 per stressed task | Stressor library effectiveness |
| clean_streak_length | Consecutive tasks with zero escapes | Monitor (no SLO — anti-turkey signal) | Turkey problem early warning |
| repeat_review_noise_index | Average MAP distance across repeat-review pairs | < 2.0 | Decision consistency |
| natural_frequency_coverage | Share of high-severity claims with frequency backing | >= 0.80 | Calibration quality |
| spot_check_coverage_rate | Repeat-reviewed beads / eligible beads | >= sampling target | Noise measurement completeness |

---

## Error Budget Policy

The error budget is the gap between target and 100%. When budget is healthy, the system can move faster. When depleted, the system must slow down.

### Budget Healthy (all SLOs met for last 3 tasks)
- Clear-domain beads auto-merge without Sentinel (L0 → merge)
- Complicated-domain beads may skip Cycle 2 even if convergence assessment says otherwise
- Conductor can batch LOSA observations (sample every 3rd bead instead of every bead)

### Budget Warning (1 SLO breached in last 3 tasks)
- All beads get Sentinel review regardless of Cynefin domain
- Conductor logs which SLO is at risk and investigates root cause
- No process relaxations allowed

### Budget Depleted (2+ SLOs breached in last 3 tasks)
- All beads get full AQS engagement regardless of Cynefin domain (even Clear beads)
- Conductor must address root cause before new feature work proceeds
- Constitution review triggered — check if existing rules cover the failure pattern
- LOSA sampling rate increased to 50%

### Budget Tracking

The Conductor maintains a running budget state in the task's active directory:

## Quality Budget Artifact

The quality budget is now a machine-readable YAML artifact. See:
- **Schema:** `references/quality-budget-schema.md`
- **Rules:** `references/quality-budget-rules.yaml`
- **Location:** `docs/sdlc/active/{task-id}/quality-budget.yaml`
- **System ledger:** `docs/sdlc/system-budget.jsonl`

Derivation: `scripts/derive-quality-budget.sh`. The old markdown format (`quality-budget.md`) is superseded.
