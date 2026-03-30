---
name: sdlc-crossmodel
description: "Cross-model adversarial review using tmup/Codex workers. Dispatched by the Conductor when FFT-14 triggers FULL or TARGETED cross-model escalation post-AQS, pre-hardened. Manages on-demand tmux grid lifecycle, Codex worker dispatch, artifact collection, and finding normalization. Advisory-only day 1."
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

If FFT-14 returns SKIP or SKIP_UNAVAILABLE, this skill does not run. Bead proceeds directly to `hardened` via normal AQS path.

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

Cross-model workers inherit tmup's current interactive Codex worker contract automatically:

- Root pane workers launch on `gpt-5.4`
- `model_context_window=1050000`
- `model_auto_compact_token_limit=750000`
- `model_reasoning_effort=high`
- `model_reasoning_summary=low`
- `plan_mode_reasoning_effort=xhigh`
- `model_verbosity=low`
- `service_tier=fast`
- `tool_output_token_limit=50000`
- `web_search=live`
- `history.persistence=save-all`
- `features.undo=true`
- `shell_environment_policy.inherit=all`
- `features.shell_snapshot=true`
- `features.enable_request_compression=true`
- `tui.notifications=true`
- `background_terminal_max_timeout=600000`
- `agents.max_threads=6`
- `agents.max_depth=2`
- `agents.job_max_runtime_seconds=3600`

Tiered tmup subagents are available inside each pane:

- `tmup-tier1` — `gpt-5.3-codex`
- `tmup-tier2` — `gpt-5.2-codex`
- `crossmodel-grid-up.sh` syncs these definitions into `~/.codex/agents/` before declaring the grid ready

Resumed workers keep the same contract. `tmup_dispatch` with `resume_session_id` reapplies the configured model, context, compaction, approval, sandbox, and subagent-cap settings on resume.

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

**Worker communication protocol:** tmup already injects the baseline worker contract: runtime settings, lane discipline, tmux input model, process context, quality posture, internal teams, and tmup-cli command reference. Cross-model dispatch prompts should add only the mission-specific delta (blindness constraints, artifact contract, checkpoint cadence, and domain focus). Workers are expected to:
1. Call `tmup-cli heartbeat` every 2-3 minutes
2. Call `tmup-cli checkpoint` for progress updates (at least 1 within first 2 minutes)
3. Call `tmup-cli message --to lead --type finding` for interim findings
4. Write the findings file to the artifact path
5. Call `tmup-cli complete "summary" --artifact {name}:{path}` to register the artifact and signal completion

**Internal teams:** Cross-model workers should use tmup's tiered internal teams when the work decomposes cleanly. Root workers may spawn `tmup-tier1`; tier-1 workers may spawn `tmup-tier2` for narrow leaf tasks. Do not spawn unnamed/raw agents.

**Supervision pattern:** The supervisor manages these panes with the harvest → evaluate → reprompt loop. Keep live lane context warm and prefer reprompting the same pane over dispatching a replacement worker.

The `tmup-cli complete --artifact` call is the **authoritative completion signal** — not file existence. It registers the artifact checksum in tmup's database. The supervisor uses `tmup_status` to detect completion, not filesystem polling.

`crossmodel-verify-artifact.sh` validates each artifact after collection. On re-verification after repair, use `--expected-checksum`. See spec Section 5.5 for the full artifact format and verification outcome table (VALID / MALFORMED / MISSING / NO_EVIDENCE).

---

## Resilience & Recovery

Reference `agents/crossmodel-supervisor.md` for full R&R protocol. Summary:

**State machine:** `READY → RUNNING → COMPLETE`, with degraded paths to `DEGRADED` and `FALLBACK_CLAUDE_ONLY`.

**Retry budget:**

| Operation | Budget | On exhaustion |
|---|---|---|
| Preflight | 1 retry (2 attempts) | DISABLED |
| Fresh session (init + grid) | 1 retry | DISABLED for this bead |
| Worker launch (in-place) | 0 | Skip worker, continue |
| Replacement worker | 1 | Accept loss, continue |
| Idle worker reprompt | 1 | Timeout worker |
| Malformed artifact repair | 1 | NO_EVIDENCE |

**Fallback ladder:**
```
FULL (5 workers) → TARGETED (2 workers) → REVIEWER_ONLY (1 worker) → CLAUDE_ONLY
```

CLAUDE_ONLY is always valid — cross-model is an enhancer, not a prerequisite.

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
| Preflight fails | Retry once. If still fails → DISABLED, log SKIP_UNAVAILABLE |
| `tmup_init` fails | Log, DISABLED for this bead, Claude-only |
| `crossmodel-grid-up.sh` fails | `crossmodel-grid-down.sh --force` (deregisters from tmup registry + kills tmux residue) → retry `tmup_init` with `xm-{bead-id}-r1`. If retry fails → DISABLED |
| Worker launch fails | Mark unavailable, skip, continue surviving workers |
| Worker idle | `tmup_harvest` → evaluate lane state → `tmup_reprompt` once, then timeout |
| Worker timeout (>10min) | `tmup_harvest` for supervision + forensics, mark TIMED_OUT, optional resume or one replacement |
| Worker completes without artifact | NO_EVIDENCE (not clean) |
| Artifact malformed | One repair request, then NO_EVIDENCE |
| `crossmodel-grid-down.sh` fails | Warning only, note residue in session journal |
| `tmup_status` shows stale agent | Logged — recovery runs as side effect of `tmup_status` |

---

## Integrity Rules

From spec Section 6.6:

- **Advisory only (day 1)** — findings do not independently block bead advancement
- **Only the Conductor changes bead status** — never update bead status from within this skill
- **Stage A workers never receive Claude AQS findings** — anti-anchoring is non-negotiable
- **Stage B reviewer never receives any review artifacts** — full independence required
- **Only normalized findings enter blue-team or triage flow** — raw Codex output is untrusted until verified
- **Missing artifact = NO_EVIDENCE, never "clean"** — absence of artifact is not absence of findings
- **All worker outputs must publish unique pre-registered artifacts** — required by tmup contract
- **Cross-model never writes bead status directly**

---

## tmup MCP Tool Usage

| Tool | Purpose | Does NOT |
|---|---|---|
| `tmup_init` | Create SQLite session/DB | Create tmux grid — `crossmodel-grid-up.sh` does that |
| `tmup_task_batch` | Register all worker tasks with unique `produces` names | Launch workers — `tmup_dispatch` does that |
| `tmup_dispatch` | Launch or resume Codex workers to grid panes under the tmup runtime contract | Retry on failure — mark skipped and continue |
| `tmup_status` | Primary heartbeat + stale-agent recovery trigger | Serve as sole monitoring signal |
| `tmup_inbox` | Check for blocker/finding messages from workers | Replace `tmup_status` in monitor loop |
| `tmup_next_action` | Synthesized recommendation | Override human judgment — advisory only |
| `tmup_reprompt` | Primary way to continue or redirect an existing live lane | Replace timeout for unresponsive workers |
| `tmup_harvest` | Observe pane state before reprompt / timeout / replacement decisions | Serve as primary findings evidence path |
| `tmup_teardown` | Notify agents, log session end | Kill tmux — `crossmodel-grid-down.sh` does that |

### Session Control Model

Workers dispatched via `tmup_dispatch` are persistent interactive Codex sessions, not one-shot commands. The pane hosts a live codex process from dispatch until exit.

| Tool | Session role | What it is NOT |
|---|---|---|
| `tmup_dispatch` | Start or resume a persistent interactive session in a pane; resumes now reapply the same tmup runtime contract | Not a fire-and-forget exec call |
| `tmup_reprompt` | Send follow-up text to an idle or queueable session via send-keys | Not a new command or process launch |
| `tmup_harvest` | Read pane scrollback — observation only | Not a communication channel to the worker |

Do not run `codex exec`, Bash commands, or any direct shell interaction in worker panes. All follow-up text into the worker's pane goes through `tmup_reprompt`. Structured inter-agent messaging uses `tmup_send_message` / `tmup_inbox` separately. Reuse the existing lane whenever it still holds relevant context; replacement workers are a fallback, not the normal control path.

---

## Deterministic Scripts

| Script | Role |
|---|---|
| `crossmodel-preflight.sh` | Verify environment: tmup MCP reachable, codex in PATH, tmux available, artifact path writable, no conflicting session |
| `crossmodel-grid-up.sh` | Create tmux panes for all workers; set `TMUP_NO_TERMINAL=1` to suppress GUI terminal launch in autonomous SDLC path; sync tmup tiered agents before declaring the grid ready |
| `crossmodel-grid-down.sh` | Tear down tmux grid + clean residue. `--force`: also deregisters session from tmup registry (`registry.json`) to prevent reattachment on retry |
| `crossmodel-verify-artifact.sh` | Validate artifact: existence, path, size, required headings, findings table, checksum. `--expected-checksum` flag on re-verification |
| `crossmodel-health.sh` | Compute session health state from worker statuses for circuit breaker evaluation |

---

## Grid Lifecycle

**On-demand:** Grid is created when FFT-14 triggers FULL or TARGETED. Torn down after findings are collected. No persistent grid.

**Serialized:** One cross-model session per project at a time (tmup constraint: one grid per project). If a bead reaches FFT-14 while another bead's session is active, queue it.

---

## Day-1 Stance

Advisory only. Cross-model findings do not independently block bead advancement. The existing same-model AQS + blue team resolution is the gating mechanism. Cross-model is an enhancer layered on top.

This stance is enforced structurally: the Conductor gates `hardened` transition — not the crossmodel-supervisor. Cross-model findings route through normal blue-team and triage channels before any resolution affects bead status.

---

## References

- `docs/specs/2026-03-28-crossmodel-adversarial-review-design.md` — full design spec (sections 5, 6, 7)
- `agents/crossmodel-supervisor.md` — session controller: state machine, retry budget, circuit breakers, fallback ladder
- `agents/crossmodel-triage.md` — Stage B finding deduplication and escalation
- `references/fft-decision-trees.md` — FFT-14 definition
- `references/artifact-templates.md` — AQS structured exit schema + worker artifact format
- `domain-attack-libraries.md` — domain-specific probe prompts for Stage A investigators
