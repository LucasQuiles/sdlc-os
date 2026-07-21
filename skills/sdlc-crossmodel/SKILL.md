---
name: sdlc-crossmodel
description: "Use when SDLC needs tmup/Codex cross-model adversarial review after AQS or before hardening."
---

# Cross-Model Adversarial Review

Supplement to the same-model AQS pipeline. Uses tmup to dispatch Codex CLI workers as cross-model adversarial agents — blind to Claude AQS findings — to surface systematic blind spots that same-model review cannot catch.

**Entry condition:** Post-AQS (bead at `proven`), FFT-14 returns FULL or TARGETED.
**Exit condition:** Normalized findings routed to blue teams / crossmodel-triage; bead status transition to `hardened` owned by Conductor.

---

## When Dispatched

- **Trigger:** Same-model AQS completes → Conductor evaluates FFT-14 → outcome is FULL or TARGETED
- **Position in pipeline:** After AQS structured exit block is emitted, before bead status → `hardened`
- **Conductor dispatches:** `crossmodel-supervisor` agent with bead context, FFT-14 outcome, AQS structured exit block

If FFT-14 returns SKIP, this skill does not run and the bead may proceed through the normal AQS path. If policy selects FULL or TARGETED but the runtime is unavailable, the outcome is `REQUIRED_UNAVAILABLE`: retain the bead at `proven`, record the failed requirement, and escalate to L3. Availability cannot rewrite a required review into SKIP.

---

## FFT-14 Input Contract

FFT-14 consumes the AQS structured exit block (5 fields) plus deterministic bead fields:

| Field | Source | Used by FFT-14 |
|---|---|---|
| `aqs_verdict` | AQS exit block | Cue 1: DEFERRED → ESCALATE_L3 |
| `arbiter_invoked` | AQS exit block | Cue 5: true → TARGETED |
| `residual_risk_per_domain` | AQS exit block | Cue 7: any domain >= MEDIUM → TARGETED |
| `dominant_residual_risk_domain` | AQS exit block | TARGETED domain selector |
| `turbulence_sum` | AQS exit block | Cue 6: > 3 → TARGETED |
| `runtime_receipt.observed_model` + captured `source_artifact` | AQS exit block | Required cross-model reference; missing, unknown, or hash/content mismatch → REQUIRED_UNAVAILABLE |
| `cynefin_domain` | Bead field | Cue 2: COMPLEX → FULL |
| `security_sensitive` | Bead field | Cue 2: true → FULL |
| Quality budget state | Conductor state | Cue 3: DEPLETED → FULL; Cue 4: WARNING → TARGETED |

See `references/fft-decision-trees.md` FFT-14 for the full decision tree. See `references/artifact-templates.md` for the AQS structured exit schema.

---

## Lifecycle (9 Steps)

```
1. PREFLIGHT  — crossmodel-preflight.sh
2. INIT       — tmup_init (session/DB only)
3. GRID       — crossmodel-grid-up.sh (tmux panes, TMUP_NO_TERMINAL=1)
4. BATCH      — tmup_task_batch (unique produces per worker)
5. DISPATCH   — tmup_dispatch per worker
6. MONITOR    — tmup_status + tmup_inbox + tmup_next_action (15s normal / 5s degraded)
7. COLLECT    — Read artifacts from docs/sdlc/active/{task-id}/crossmodel/
8. NORMALIZE  — crossmodel-verify-artifact.sh validation + finding normalization
9. TEARDOWN   — tmup_teardown + crossmodel-grid-down.sh
```

Steps 2 and 3 are separate: `tmup_init` creates the SQLite session/DB; `crossmodel-grid-up.sh` creates the tmux pane grid. Do not conflate them.

**Unsent-input detection:** If a worker has an active heartbeat but no checkpoint/finding/completion messages for >5 minutes after dispatch, suspect unsent input rather than a slow worker. Harvest the pane to check if the prompt appears in scrollback. If visible but unanswered, reprompt. If not visible, the send-keys delivery failed — reprompt with full prompt text. See crossmodel-supervisor "Pane Interaction Model" for the full recovery sequence.

---

## tmup Runtime Contract

Treat tmup configuration as live runtime data, not documentation constants. Before dispatch, inspect the installed tmup runtime, live `tools/list` schema, and selected policy. Model-explicit lanes require a live-catalog validation receipt; the MCP cross-model path rejects explicit pins because it cannot carry that receipt. With `model: auto`, record catalog status as not applicable and require post-launch observed-model attestation. Requested and observed configuration remain separate; unknown cannot satisfy a required-model gate.

Every required task is created with `role_required: true`, `evidence_required: true`, `model_requirement: cross_model`, and the same-model AQS runtime's **observed** model as `reference_model`. If the reference model was not observed, the cross-model requirement is inconclusive and escalates instead of inferring a model from an agent or role name.

`tmup_dispatch` must return a launch receipt containing the task, agent, role, selector, requested model, observed model (initially `unknown` is allowed), observation source, fallback provenance, attempt ID, and launch status. Retain that receipt in the session journal. Attest the observed model only from a live runtime observation with `tmup_attempt_attest`; a selector label or configured default is not observation. The attestation source must persist into the terminal receipt and exactly match the journal's model-observation source. On resume, obtain and validate a new receipt rather than assuming the prior configuration was reapplied.

---

## Stage A — Red Team Supplement

**FULL:** 4 Codex investigator workers, one per AQS domain (functionality, security, usability, resilience).

**TARGETED:** 1 Codex investigator for `dominant_residual_risk_domain` only.

Each investigator receives:
- Bead code (post-AQS current state) + bead spec
- Domain-specific probe prompt from `domain-attack-libraries.md`
- **NEVER Claude AQS findings** — anti-anchoring requirement; investigators must form independent judgments

Stage A normalized findings → Conductor routes to existing blue-team defenders (blue-functionality, blue-security, etc.). Blue teams process these identically to Claude-originated red team findings.

---

## Stage B — Independent Review

**Both FULL and TARGETED:** 1 Codex reviewer worker.

The reviewer receives:
- Bead code + bead spec (objective, scope, acceptance criteria)
- **NEVER AQS findings, sentinel notes, or any Claude review artifacts** — full independence required
- Domain token: `independent`

Stage B normalized findings → Conductor routes to `crossmodel-triage` agent for deduplication against existing AQS results. Net-new findings escalated; already-caught findings logged only.

---

## Worker Artifact Contract

Each worker declares a unique `produces` artifact name at batch creation:

| Worker | Produces name | File path |
|---|---|---|
| Stage A per domain | `{bead-id}-stage-a-{domain}-findings` | `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-codex-a-{domain}-investigator.md` |
| Stage B reviewer | `{bead-id}-stage-b-independent-review-findings` | `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-codex-b-independent-reviewer.md` |

**Worker communication protocol:** tmup injects its installed worker baseline. Cross-model dispatch prompts add the mission-specific delta (blindness constraints, artifact contract, checkpoint cadence, and domain focus). Workers are expected to:
1. Call `tmup-cli heartbeat` every 2-3 minutes
2. Call `tmup-cli checkpoint` for progress updates (at least 1 within first 2 minutes)
3. Call `tmup-cli message --to lead --type finding` for interim findings
4. Write the findings file to the artifact path
5. Send a checkpoint that the artifact is ready for supervisor review; do not represent the required task as complete before the evidence review is accepted

**Internal teams:** Use only roles present in the live catalog and only where delegation is permitted by the current runtime policy. Do not infer model, effort, or capability from a tier or role name. Leaf workers do not delegate.

**Supervision pattern:** The supervisor manages these panes with the harvest → evaluate → reprompt loop. Keep live lane context warm and prefer reprompting the same pane over dispatching a replacement worker.

File existence and worker self-report are not completion. The supervisor verifies the artifact, adds the evidence packet with `tmup_evidence_add`, accepts it with `tmup_evidence_review`, and then calls `tmup_complete`. It subsequently reads `tmup_status` with `verbose: true` and persists the matching terminal receipt. A required role is complete only when the receipt has `terminal_status: succeeded`, the observed-model policy passes, and its accepted evidence and validated artifact match the registered task.

`crossmodel-verify-artifact.sh` validates each artifact after collection. On re-verification after repair, use `--expected-checksum`. See spec Section 5.5 for the full artifact format and verification outcome table (VALID / MALFORMED / MISSING / NO_EVIDENCE).

---

## Resilience & Recovery

Reference `agents/crossmodel-supervisor.md` for full R&R protocol. Summary:

**State machine:** `READY → RUNNING → COMPLETE`, with non-success paths to `DEGRADED`, `BLOCKED`, and `REQUIRED_UNAVAILABLE`.

**Retry budget:**

| Operation | Budget | On exhaustion |
|---|---|---|
| Preflight | 1 retry (2 attempts) | REQUIRED_UNAVAILABLE; L3 escalation |
| Fresh session (init + grid) | 1 retry | REQUIRED_UNAVAILABLE; L3 escalation |
| Worker launch (in-place) | 0 | One replacement attempt; retain failed receipt |
| Replacement worker | 1 | BLOCKED; L3 escalation |
| Idle worker reprompt | 1 | Timeout worker |
| Malformed artifact repair | 1 | NO_EVIDENCE; required task remains incomplete |

**Fallback ladder:**
```
FULL (5 workers) → TARGETED (2 workers) → REVIEWER_ONLY (1 worker) → BLOCKED
```

Scope reduction is an explicit degraded policy decision, not successful execution of omitted roles. A same-model-only result cannot satisfy a cross-model-required gate.

**Circuit breakers** — open on ANY of:
1. 2 session-start failures
2. 2 worker launch failures
3. More than 1 NO_EVIDENCE result across expected artifacts
4. 2 stale-agent recovery events in one session
5. Stage B reviewer unavailable after one replacement attempt
6. Artifact verification fails twice for the same artifact

**Session journal:** `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-session.json` — written after each significant state transition.

---

## Error Handling

From spec Section 6.5:

| Failure | Response |
|---|---|
| Preflight fails | Retry once. If still unavailable → REQUIRED_UNAVAILABLE, retain bead at `proven`, escalate L3 |
| `tmup_init` fails | Retain receipt/error, retry once, then REQUIRED_UNAVAILABLE |
| `crossmodel-grid-up.sh` fails | `crossmodel-grid-down.sh --force` (deregisters from tmup registry + kills tmux residue) → retry `tmup_init` with `xm-{bead-id}-r1`. If retry fails → REQUIRED_UNAVAILABLE |
| Worker launch fails | Mark `unavailable`, retain the attempt receipt, use the one replacement budget; exhaustion blocks the parent gate |
| Worker idle | `tmup_harvest` → evaluate lane state → `tmup_reprompt` once, then timeout |
| Worker timeout (>10min) | `tmup_harvest` for supervision + forensics, mark TIMED_OUT, optional resume or one replacement; exhaustion blocks |
| Worker reports completion without accepted artifact | INCONCLUSIVE / NO_EVIDENCE; do not call `tmup_complete` |
| Artifact malformed | One repair request, then NO_EVIDENCE; required task remains incomplete |
| `crossmodel-grid-down.sh` fails | Warning only, note residue in session journal |
| `tmup_status` shows stale agent | Logged — recovery runs as side effect of `tmup_status` |

---

## Integrity Rules

From spec Section 6.6:

- **Finding content is advisory; required execution is not** — the Conductor may rebut findings, but cannot mark a required review satisfied without accepted evidence and a successful terminal receipt
- **Only the Conductor changes bead status** — never update bead status from within this skill
- **Stage A workers never receive Claude AQS findings** — anti-anchoring is non-negotiable
- **Stage B reviewer never receives any review artifacts** — full independence required
- **Only normalized findings enter blue-team or triage flow** — raw Codex output is untrusted until verified
- **Missing artifact = NO_EVIDENCE, never "clean"** — absence of artifact is not absence of findings
- **All worker outputs must publish unique pre-registered artifacts** — required by tmup contract
- **Unavailable, skipped, inconclusive, and completed are distinct states** — none of the first three satisfies a required role
- **Requested and observed models remain separate** — a role name, selector, or configured default is not an observed-model receipt
- **Cross-model never writes bead status directly**

---

## tmup MCP Tool Usage

| Tool | Purpose | Does NOT |
|---|---|---|
| `tmup_init` | Create SQLite session/DB | Create tmux grid — `crossmodel-grid-up.sh` does that |
| `tmup_task_batch` | Register required role/model/evidence policy and unique `produces` names | Launch workers — `tmup_dispatch` does that |
| `tmup_dispatch` | Launch or resume workers and atomically create an attempt receipt | Prove the observed model or terminal success |
| `tmup_attempt_attest` | Record model observed from the live runtime | Infer a model from selector or role metadata |
| `tmup_evidence_add` / `tmup_evidence_review` | Register and accept verified evidence for the matching attempt | Accept missing or malformed output |
| `tmup_complete` | Complete a task after tmup enforces its declared receipt/evidence/model policy | Turn unavailable or inconclusive into success |
| `tmup_status` with `verbose: true` | Return heartbeat state and running/terminal receipts | Let task status substitute for a matching receipt |
| `tmup_inbox` | Check for blocker/finding messages from workers | Replace `tmup_status` in monitor loop |
| `tmup_next_action` | Synthesized recommendation | Override human judgment — advisory only |
| `tmup_reprompt` | Primary way to continue or redirect an existing live lane | Replace timeout for unresponsive workers |
| `tmup_harvest` | Observe pane state before reprompt / timeout / replacement decisions | Serve as primary findings evidence path |
| `tmup_teardown` | Notify agents, log session end | Kill tmux — `crossmodel-grid-down.sh` does that |

### Session Control Model

Workers dispatched via `tmup_dispatch` are persistent interactive Codex sessions, not one-shot commands. The pane hosts a live codex process from dispatch until exit.

| Tool | Session role | What it is NOT |
|---|---|---|
| `tmup_dispatch` | Start or resume a persistent interactive session in a pane and return a new attempt receipt | Not a fire-and-forget exec call or proof that prior runtime settings were reapplied |
| `tmup_reprompt` | Send follow-up text to an idle or queueable session via send-keys | Not a new command or process launch |
| `tmup_harvest` | Read pane scrollback — observation only | Not a communication channel to the worker |

Do not run `codex exec`, Bash commands, or any direct shell interaction in worker panes. All follow-up text into the worker's pane goes through `tmup_reprompt`. Structured inter-agent messaging uses `tmup_send_message` / `tmup_inbox` separately. Reuse the existing lane whenever it still holds relevant context; replacement workers are a fallback, not the normal control path.

---

## Deterministic Scripts

| Script | Role |
|---|---|
| `crossmodel-preflight.sh` | Verify environment: tmup MCP reachable, codex in PATH, tmux available, artifact path writable, no conflicting session |
| `crossmodel-grid-up.sh` | Create tmux panes for workers; set `TMUP_NO_TERMINAL=1` to suppress GUI terminal launch; synchronize installed role definitions before declaring the grid ready (this does not authorize leaf delegation) |
| `crossmodel-grid-down.sh` | Tear down tmux grid + clean residue. `--force`: also deregisters session from tmup registry (`registry.json`) to prevent reattachment on retry |
| `crossmodel-verify-artifact.sh` | Validate artifact: existence, path, size, required headings, findings table, checksum. `--expected-checksum` flag on re-verification |
| `crossmodel-health.sh` | Fail-closed parent gate over policy, required tasks, terminal receipts, observed models, accepted evidence, and validated artifacts |

---

## Grid Lifecycle

**On-demand:** Grid is created when FFT-14 triggers FULL or TARGETED. Torn down after findings are collected. No persistent grid.

**Serialized:** One cross-model session per project at a time (tmup constraint: one grid per project). If a bead reaches FFT-14 while another bead's session is active, queue it.

---

## Advancement Stance

Finding content remains advisory and routes through normal blue-team and triage channels. Execution of a policy-required review is a hard gate: `crossmodel-health.sh` must return `gate_status: satisfied` and `advance_allowed: true` before the Conductor transitions the bead to `hardened`. Only an explicit FFT-14 `SKIP` decision produces `not_applicable`; infrastructure failure or worker loss does not.

---

## References

- `docs/specs/2026-03-28-crossmodel-adversarial-review-design.md` — historical design rationale only; its day-one fallback and advancement rules are non-normative
- `agents/crossmodel-supervisor.md` — session controller: state machine, retry budget, circuit breakers, fallback ladder
- `agents/crossmodel-triage.md` — Stage B finding deduplication and escalation
- `references/fft-decision-trees.md` — FFT-14 definition
- `references/artifact-templates.md` — AQS structured exit schema + worker artifact format
- `domain-attack-libraries.md` — domain-specific probe prompts for Stage A investigators
