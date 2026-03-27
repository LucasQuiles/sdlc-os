# STPA Control Structure — SDLC-OS

System-level STAMP control structure for the SDLC-OS. Reference for agent consumption.
Maintained per Phase B Safety Control Layer design (2026-03-26).

---

## Control Structure Map

```
EXTERNAL GOVERNANCE
┌──────────────────────────────────────────────────────────────┐
│  User                                                        │
│  Task requests, approvals, overrides, /evolve                │
│  Process model: intent, priorities, quality expectations      │
└──────────────────────────┬───────────────────────────────────┘
                           │ Interface 1
PRIMARY CONTROLLER         ▼
┌──────────────────────────────────────────────────────────────┐
│  Conductor (Opus)                                            │
│  FFT routing, bead dispatch, synthesis, escalation           │
│  Process model: task intent, bead graph, FFT decisions,      │
│    quality budget, active profiles, Cynefin assignments      │
└──┬──────────┬──────────┬──────────┬──────────────────────────┘
   │          │          │          │
   │ Interface 2 (Conductor → Subcontrollers)
   ▼          ▼          ▼          ▼
SUBCONTROLLERS
┌────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────────┐
│Delivery│ │Adversarl │ │Reliability│ │Safety                │
│        │ │          │ │           │ │                      │
│runners │ │red cmds  │ │reliability│ │safety-analyst        │
│(Sonnet)│ │blue defs │ │-conductor │ │safety-constraints-   │
│        │ │arbiter   │ │(Sonnet)   │ │  guardian             │
│        │ │(Son/Opus)│ │           │ │process-drift-monitor │
│        │ │          │ │           │ │latent-condition-     │
│        │ │          │ │           │ │  tracer              │
│        │ │          │ │           │ │(Haiku/Sonnet)        │
├────────┤ ├──────────┤ ├───────────┤ ├──────────────────────┤
│Process │ │Process   │ │Process    │ │Process model:        │
│model:  │ │model:    │ │model:     │ │constraints registry, │
│bead    │ │active    │ │observ.    │ │resident pathogen     │
│spec,   │ │domains,  │ │profile,   │ │registry, channel     │
│context │ │precedent │ │hardening  │ │health model,         │
│packet, │ │context,  │ │state,     │ │deviance baselines,   │
│reuse   │ │expected  │ │premortem  │ │UCA catalog           │
│report  │ │attack    │ │gaps       │ │                      │
│        │ │surface   │ │           │ │                      │
└───┬────┘ └───┬──────┘ └────┬──────┘ └──────┬───────────────┘
    │          │             │               │
    │ Interface 3 (Subcontrollers → Actuators/Guards)
    ▼          ▼             ▼               ▼
ACTUATORS
┌──────────────────────────────────────────────────────────────┐
│  Write/Edit/Bash, deterministic scripts (FFT-08),            │
│  guppy probes, artifact writes                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
GUARDS (can block or redirect — not pure sensors)              │
┌──────────────────────────────────────────────────────────────┐
│  Hook validators: guard-bead-status, validate-decision-trace,│
│  validate-hardening-report, validate-aqs-artifact,           │
│  lint-domain-vocabulary, check-naming-convention,             │
│  validate-consistency-artifacts, validate-runner-output       │
│  Deterministic checks: type-check, lint, test suite,         │
│  schema validation, secret scan (from FFT-08 catalog)        │
└──────────────────────────┬───────────────────────────────────┘
                           │ Interface 4 (Actuators/Guards → Controlled Processes)
                           ▼
CONTROLLED PROCESSES
┌──────────────────────────┬───────────────────────────────────┐
│  Product/Code            │  Orchestration/State              │
│  source files            │  beads + decision traces          │
│  tests                   │  quality budget                   │
│  configs                 │  precedent DB                     │
│  APIs                    │  code constitution                │
│  dependencies            │  convention map                   │
│                          │  safety registries (NEW)          │
│                          │  resident pathogen registry (NEW) │
└──────────────────────────┴───────────────────────────────────┘

SENSORS (feedback to Controllers)
┌────────┐┌──────┐┌────┐┌───────────┐
│Sentinel││Oracle││LOSA││Calibration│
│(Haiku) ││Councl││    ││Loop (L6)  │
└────────┘└──────┘└────┘└───────────┘

TELEMETRY ARTIFACTS (outputs of Safety subcontroller agents)
┌─────────────────┐┌──────────────────┐┌─────────────────────┐
│Drift reports    ││Latent trace      ││Feedback channel     │
│(from process-   ││reports (from     ││health alerts (from  │
│drift-monitor)   ││latent-condition- ││safety-analyst +     │
│                 ││tracer)           ││process-drift-monitor│
└─────────────────┘└──────────────────┘└─────────────────────┘

Interface 5: Sensors/Guards → Controllers
Interface 6: Calibration/Drift/Safety → Evolve/Conductor (meta-feedback)
```

---

## The 6 STPA Interfaces

| # | Interface | Direction | What Flows | UCAs Analyzed |
|---|---|---|---|---|
| 1 | User → Conductor | Control | Task requests, approvals, overrides | Vague request, premature approval, missing override |
| 2 | Conductor → Subcontrollers | Control | Bead dispatch, context packets, FFT decisions | Missing context, wrong Cynefin, anti-anchoring violation, stale process model |
| 3 | Subcontrollers → Actuators/Guards | Control | Tool calls, guppy probes, artifact writes | Wrong file targeted, incomplete probe, guard bypassed |
| 4 | Actuators/Guards → Controlled Processes | Action | Code mutations, state mutations, artifact creation | Write to wrong file, state corruption, guard false-block, guard missed-block |
| 5 | Sensors/Guards → Controllers | Feedback | Findings, verifications, drift signals, block/redirect | Feedback not provided (silent sensor), feedback too late (Sterman delay), false clean report |
| 6 | Calibration/Drift/Safety → Evolve/Conductor | Meta-feedback | System health, deviance trends, reliability data, pathogen accumulation | Calibration delayed too long, deviance signal ignored, pathogen registry stale |

---

## Process Models

Every controller maintains a process model — its understanding of the current state of what it controls. Unsafe control actions occur when the process model diverges from reality. Monitoring process model freshness is how STPA prevents accidents proactively.

| Controller | Process Model Contents | Staleness Risk |
|---|---|---|
| Conductor | Task intent, bead graph, FFT decisions, quality budget, active profiles | Intent drift if user changes mind mid-task; budget stale if not refreshed between beads |
| Delivery (runners) | Bead spec, context packet, reuse report | Context packet missing recent changes from parallel beads |
| Adversarial (red/blue) | Active domains, precedent context, expected attack surface | Precedent DB stale, attack library outdated, domain priorities from stale recon |
| Reliability | Observability profile, hardening state, premortem gaps | Observability profile from project scan may miss runtime-only frameworks |
| Safety | Constraints registry, resident pathogen registry, channel health model, deviance baselines, UCA catalog | Constraints not updated after architecture changes; baselines from different project phase |

The safety-analyst agent checks process model freshness at the start of every Phase 3 (Architect) for the Conductor's model. The process-drift-monitor checks all models during Evolve cycles.

---

## STPA Skip Rule (canonical)

STPA analysis and safety constraint enforcement apply when ANY of:
- `cynefin == COMPLEX`
- `security_sensitive == true`

STPA is skipped when BOTH of:
- `cynefin != COMPLEX` (i.e., CLEAR or COMPLICATED)
- AND `security_sensitive == false`

Note: `complexity_source` (ESSENTIAL/ACCIDENTAL) does NOT independently trigger STPA. It governs AQS scrutiny depth (FFT-10/FFT-11) but not safety analysis. A COMPLICATED+ESSENTIAL bead gets full AQS but no STPA.

ACCIDENTAL beads that are security-sensitive still get full STPA — `security_sensitive` overrides everything.
