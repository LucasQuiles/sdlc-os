# Cross-Model Adversarial Review — Design Spec

**Date:** 2026-03-28
**Version:** 1.0
**Status:** Approved
**Plugin:** sdlc-os v8.1.0 → v9.0.0
**Dependency:** tmup plugin (transport/runtime infrastructure)

---

## 1. Problem

All SDLC-OS adversarial agents (4 red teams, 4 blue teams, 3 oracle tiers, sentinels) run on Claude model variants. Same-model review has a blind-spot ceiling — research shows individual models catch ~53% of known bugs, while cross-model adversarial debate raises detection to ~80% (source: Milvus blog, "AI Code Review Gets Better When Models Debate").

The system needs cross-model diversity without replacing the existing same-model AQS pipeline that already works.

## 2. Solution

Add `sdlc-crossmodel` — an adapter skill that uses tmup to dispatch Codex CLI workers as cross-model adversarial agents. Codex workers supplement (not replace) the existing Claude AQS pipeline.

**Three integration modes:**
- **Stage A (Red Team Supplement):** Codex investigator workers attack beads blind to Claude AQS findings. Findings route into existing Claude blue team defenders.
- **Stage B (Independent Review):** A Codex reviewer independently assesses the bead with no review artifacts from any prior stage. Findings route through a dedicated crossmodel-triage agent.
- **Selective Escalation:** FFT-14 determines which beads get cross-model review and at what intensity.

**Day-1 stance:** Advisory only. Cross-model findings feed into blue teams and triage but do not independently block bead advancement. The existing same-model AQS + blue team resolution remains the gating mechanism.

## 3. Architecture

### 3.1 New Components

| Component | Type | Model | Purpose |
|---|---|---|---|
| `skills/sdlc-crossmodel/SKILL.md` | Skill | — | Adapter lifecycle: init → batch → dispatch → monitor → collect → normalize → route → teardown |
| `agents/crossmodel-supervisor.md` | Agent | sonnet | Owns tmup session lifecycle, monitoring, retries, downgrade, artifact verification, fallback |
| `agents/crossmodel-triage.md` | Agent | haiku | Deduplicates Stage B findings against existing AQS results, escalates net-new findings |
| `references/fft-decision-trees.md` (FFT-14) | Reference update | — | Cross-model escalation routing |
| `scripts/crossmodel-preflight.sh` | Script | — | Platform/tmup/codex availability check |
| `scripts/crossmodel-grid-up.sh` | Script | — | tmux grid creation + pane verification. Must set `TMUP_NO_TERMINAL=1` to suppress tmup's auto-launch of GUI terminal emulators in autonomous SDLC path. |
| `scripts/crossmodel-grid-down.sh` | Script | — | tmux grid teardown + residue cleanup |
| `scripts/crossmodel-verify-artifact.sh` | Script | — | Artifact existence, schema, checksum validation |
| `scripts/crossmodel-health.sh` | Script | — | Session health computation from worker states |

### 3.2 tmup Dependency Contract

sdlc-crossmodel uses tmup as transport infrastructure only. It does NOT modify tmup internals.

**MCP tools used:**

| Tool | Purpose in sdlc-crossmodel | Notes |
|---|---|---|
| `tmup_init` | Create SQLite session/DB | Does NOT create tmux grid — grid-up.sh handles that |
| `tmup_task_batch` | Register worker tasks with unique `produces` artifact names | Required: unique artifact names per worker per tmup contract |
| `tmup_dispatch` | Launch Codex workers to grid panes | Launch failure → skip worker, no in-place retry |
| `tmup_status` | Primary heartbeat + stale-agent recovery trigger | Polled every 15s (normal) / 5s (degraded) |
| `tmup_inbox` | Check for blocker/finding messages from workers | Part of monitor loop |
| `tmup_next_action` | Synthesized recommendation | Advisory only, never sole monitor signal |
| `tmup_reprompt` | First recovery step for idle-but-alive workers | One reprompt attempt before timeout |
| `tmup_harvest` | Debug/timeout/forensics ONLY | Never the primary evidence path |
| `tmup_teardown` | Notify agents, log session end | Does NOT kill tmux — grid-down.sh handles that |

**Ground truth constraints from tmup:**
- `tmup_init` creates session/DB, not tmux grid (REFERENCE.md:10)
- `tmup_status` runs stale-agent recovery as side effect (tools/index.ts:345)
- `tmup_dispatch` launch failure has stranded-claim risk (dispatch-flow-trace.md:152)
- Artifact publication requires pre-registered `produces` names, unique per task (task-ops.ts:51, task-lifecycle.ts:149)
- One grid per project (FAQ.md:56) — serialize cross-model runs

## 4. FFT-14: Cross-Model Escalation

**Trigger point:** Post-AQS, pre-hardened. Same-model AQS completes → Conductor evaluates FFT-14 → if FULL/TARGETED: cross-model review runs → blue-team/triage resolves findings → then bead transitions to `hardened`.

```
FFT-14: cross_model_escalation

  Evaluated: after same-model AQS completes, BEFORE bead status → hardened
  Anti-pattern guarded: Single-Model Blind Spot — same model family
    cannot catch its own systematic failure modes

  Cue 0: Is tmup available and fully operational?
    (crossmodel-preflight.sh: MCP reachable + codex in PATH + tmux
     available + writable artifact path + no conflicting session)
    → NO  → SKIP_UNAVAILABLE
             Log: "tmup unavailable: {specific failure}, continuing Claude-only path"
    → YES → continue

  Cue 1: Is the AQS verdict DEFERRED?
    → YES → ESCALATE_L3 (no cross-model — bead stays at proven,
             escalates to Conductor per AQS protocol)
    → NO  → continue

  Cue 2: Is the bead COMPLEX domain or security_sensitive?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 3: Is the quality budget DEPLETED?
    → YES → FULL CROSS-MODEL (4 domain investigators + 1 reviewer)
    → NO  → continue

  Cue 4: Is the quality budget WARNING?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 5: Was the arbiter invoked on this bead during AQS?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 6: Is the bead turbulence sum > 3?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Cue 7: Does the AQS report show residual risk >= MEDIUM?
    → YES → TARGETED CROSS-MODEL (1 domain investigator + 1 reviewer)
    → NO  → continue

  Default → SKIP CROSS-MODEL
```

**Structured AQS inputs for FFT-14:**

| Field | Type | Source |
|---|---|---|
| `aqs_verdict` | enum: `HARDENED` \| `PARTIALLY_HARDENED` \| `DEFERRED` | AQS exit status |
| `arbiter_invoked` | boolean | True if arbiter dispatched on this bead |
| `residual_risk_per_domain` | map: `{functionality: NONE\|LOW\|MED\|HIGH, security: ..., usability: ..., resilience: ...}` | Per-domain residual risk from AQS report |
| `dominant_residual_risk_domain` | enum: `functionality` \| `security` \| `usability` \| `resilience` | Domain with highest residual risk (tie-break: security > functionality > resilience > usability) |
| `turbulence_sum` | integer | Sum of bead turbulence fields (L0+L1+L2+L2.5+L2.75) |

Plus existing deterministic bead fields: `cynefin_domain`, `security_sensitive`, quality budget state.

**AQS schema update required:** The AQS exit artifact (`skills/sdlc-adversarial/SKILL.md` and `references/artifact-templates.md`) must emit these structured fields as a machine-readable block, not just prose. This is an explicit implementation requirement — see Section 7.2.

**Outcomes:**
- **FULL:** 5 Codex workers (4 domain investigators + 1 independent reviewer)
- **TARGETED:** 2 Codex workers (1 investigator for `dominant_residual_risk_domain` + 1 independent reviewer)

**TARGETED worker selection:** The domain investigator is chosen from `dominant_residual_risk_domain`. Maps: functionality → investigator with functionality probe prompt, security → investigator with security probe prompt, usability → investigator with usability probe prompt, resilience → investigator with resilience probe prompt. Tie-break order: security > functionality > resilience > usability (security wins ties because its failure modes are highest-consequence).

## 5. sdlc-crossmodel Skill — Adapter Lifecycle

### 5.1 Lifecycle

```
1. PREFLIGHT  — crossmodel-preflight.sh (platform, tmup, codex, paths)
2. INIT       — tmup_init (SQLite session/DB)
               + crossmodel-grid-up.sh (tmux panes + verification)
3. BATCH      — tmup_task_batch (create tasks with unique produces names)
4. DISPATCH   — tmup_dispatch × N workers (to grid panes)
5. MONITOR    — tmup_status + tmup_inbox + tmup_next_action loop
6. COLLECT    — Read completed task artifacts from
               docs/sdlc/active/{task-id}/crossmodel/{bead-id}-codex-*.md
7. NORMALIZE  — Validate artifact structure, map to SDLC finding format
8. ROUTE      — Stage A findings → existing blue teams
               Stage B findings → crossmodel-triage agent
9. TEARDOWN   — tmup_teardown (notify agents, log session end)
               + crossmodel-grid-down.sh (kill tmux, clean residue)
```

### 5.2 Grid Lifecycle

**On-demand:** Grid is created when FFT-14 triggers FULL or TARGETED. Torn down after findings are collected. No persistent grid.

**Serialized:** One cross-model session per project at a time. If a bead reaches FFT-14 while another bead's cross-model session is active, queue it.

### 5.3 Stage A — Red Team Supplement

For FULL: 4 Codex investigator workers, one per AQS domain. Each receives:
- Bead code (post-AQS, current state)
- Domain-specific probe prompt derived from `domain-attack-libraries.md`
- NO Claude AQS findings (anti-anchoring — Codex attacks blind)

For TARGETED: 1 Codex investigator for the highest-residual-risk domain only.

Harvested findings formatted as standard red team findings → fed into existing blue team defenders. Blue teams do not know whether findings originated from Claude red teams or Codex.

### 5.4 Stage B — Independent Review

1 Codex reviewer worker receives:
- Bead code
- Bead spec (objective, scope, acceptance criteria)
- NO AQS findings, NO sentinel notes, NO Claude review artifacts

Reviewer produces independent assessment → goes to `crossmodel-triage` agent for deduplication against existing AQS results and L1 corrections.

### 5.5 Worker Artifact Contract

Each worker task declares a unique `produces` artifact name at batch creation:
- `{bead-id}-stage-a-{domain}-findings` (e.g., `bead-17-stage-a-security-findings`)
- `{bead-id}-stage-b-review-findings`

Workers write structured markdown to `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-codex-{stage}-{domain}-{role}.md` and call `tmup-cli complete` with the matching artifact registration.

**Artifact format:**

```markdown
## Cross-Model Review: {bead-id}

**Reviewer:** codex-{role} ({domain if applicable})
**Stage:** A (red supplement) | B (independent review)
**Bead:** {bead-id}
**Files examined:** {list}

### Findings

| # | Severity | Category | File:Line | Finding | Evidence |
|---|----------|----------|-----------|---------|----------|
| 1 | HIGH | {category} | {location} | {description} | {evidence} |

### Summary

**Finding count:** {N} ({high} HIGH, {medium} MEDIUM, {low} LOW)
**Confidence:** {0.0-1.0} — {rationale}
```

**Artifact verification (crossmodel-verify-artifact.sh):**

| Check | Outcome |
|---|---|
| File exists at expected path | VALID / MISSING |
| Path within project directory | VALID / PATH_VIOLATION |
| Size below limit | VALID / OVERSIZED |
| Required headings present | VALID / MALFORMED |
| Findings table parseable | VALID / MALFORMED |
| Checksum stable | VALID / STALE |

MALFORMED gets one repair attempt. MISSING / STALE / EMPTY = NO_EVIDENCE (counted against session health).

### 5.6 Finding Flowback

**Stage A findings:**
1. Normalized to standard red team finding format
2. Fed into existing blue team defenders (blue-functionality, blue-security, blue-usability, blue-resilience)
3. Blue teams process exactly as they would Claude-originated findings
4. Disputes → arbiter as usual

**Stage B findings:**
1. `crossmodel-triage` agent deduplicates against existing AQS results
2. Net-new findings escalated as HIGH priority corrections through normal L1 loop
3. Already-caught findings logged but not re-processed

## 6. Resilience & Recovery

### 6.1 Crossmodel-Supervisor

A sonnet-class agent that owns the full tmup session lifecycle for one bead's cross-model review.

**State machine:**

```
READY → RUNNING → COMPLETE
  ↓        ↓
DISABLED  DEGRADED → FALLBACK_CLAUDE_ONLY
```

| Transition | Trigger |
|---|---|
| READY → RUNNING | Successful preflight + init + grid-up |
| READY → DISABLED | Unrecoverable preflight/platform failure (2 attempts) |
| RUNNING → DEGRADED | Worker loss, timeout, missing artifact, partial session failure |
| RUNNING → COMPLETE | All expected artifacts validated or formally excluded |
| DEGRADED → FALLBACK_CLAUDE_ONLY | Retry budget exhausted or circuit breaker tripped |
| DEGRADED → COMPLETE | Surviving workers produced valid artifacts |

**Session journal:** `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-session.json`

```json
{
  "bead_id": "string",
  "fft14_outcome": "FULL | TARGETED",
  "mode": "FULL | TARGETED | DEGRADED | FALLBACK_CLAUDE_ONLY",
  "session_id": "tmup session ID",
  "grid_status": "UP | DOWN | FAILED",
  "worker_tasks": [
    {
      "task_id": "tmup task ID",
      "role": "investigator | reviewer",
      "domain": "functionality | security | usability | resilience | null",
      "stage": "A | B",
      "pane_index": 0,
      "status": "dispatched | completed | timed_out | failed | no_evidence",
      "artifact_name": "unique produces name",
      "artifact_path": "path or null",
      "artifact_status": "VALID | MALFORMED | MISSING | STALE | EMPTY"
    }
  ],
  "expected_artifacts": ["list of registered produces names"],
  "validated_artifacts": ["list of verified artifact paths"],
  "failures": ["list of failure descriptions"],
  "retry_counts": {
    "preflight": 0,
    "session": 0,
    "workers": {}
  },
  "health_state": "READY | RUNNING | DEGRADED | FALLBACK_CLAUDE_ONLY | COMPLETE | DISABLED",
  "breaker_open": false,
  "fallback_level": "FULL | TARGETED | REVIEWER_ONLY | CLAUDE_ONLY",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp or null"
}
```

### 6.2 Retry Budget

| Operation | Budget | On exhaustion |
|---|---|---|
| Preflight | 1 retry (2 attempts total) | DISABLED |
| Fresh session (init + grid) | 1 retry with unique session_name `xm-{bead-id}-{retry}` to avoid reattach | DISABLED for this bead |
| Worker launch (in-place) | 0 | Skip worker, continue |
| Replacement worker | 1 | Accept loss, continue |
| Idle worker reprompt | 1 | Timeout worker |
| Malformed artifact repair | 1 | NO_EVIDENCE |

No unbounded retries permitted.

### 6.3 Fallback Ladder

```
FULL (5 workers) → TARGETED (2 workers) → REVIEWER_ONLY (1 worker) → CLAUDE_ONLY
```

- If any Stage A domain worker fails, preserve surviving workers and continue.
- If independent reviewer fails, Stage A findings may still proceed.
- If session health falls below threshold, downgrade one level.
- CLAUDE_ONLY is always valid — cross-model is an enhancer, not a prerequisite.

### 6.4 Circuit Breakers

Open the breaker for the bead if ANY of these occur:

- 2 session-start failures
- 2 worker launch failures
- More than 1 NO_EVIDENCE worker
- 2 stale-agent recovery events in one bead session
- Stage B reviewer unavailable after replacement attempt
- Artifact verification fails twice for the same worker

On breaker open:
1. Stop new Codex dispatches
2. Collect any valid finished artifacts
3. Write degraded outcome to session journal and decision trace
4. Continue Claude-only path

### 6.5 Error Handling Table

| Failure | Response |
|---|---|
| Preflight fails | Retry once. If still fails → DISABLED, log SKIP_UNAVAILABLE |
| `tmup_init` fails | Log, DISABLED for this bead, Claude-only |
| `crossmodel-grid-up.sh` fails | `tmup_teardown` to clean session. For retry: call `tmup_init` with an explicit unique `session_name` (e.g., `xm-{bead-id}-{retry-count}`) to avoid reattaching the poisoned session via tmup's canonical project-dir lookup. If retry also fails → DISABLED |
| Worker launch fails | Mark worker unavailable, skip, continue surviving workers |
| Worker idle | `tmup_reprompt` once, then timeout |
| Worker timeout (>10min) | `tmup_harvest` for forensics, mark TIMED_OUT, optional replacement once |
| Worker completes without artifact | NO_EVIDENCE (not clean) |
| Artifact malformed | One repair request, then NO_EVIDENCE |
| `crossmodel-grid-down.sh` fails | Warning only, leave residue note in session journal |
| tmup_status shows stale agent | Logged — recovery runs as side effect, adapter does not depend on it |

### 6.6 Integrity Rules

- Cross-model review is advisory on day 1
- Only the Conductor changes bead status (proven, hardened, reliability-proven)
- Stage A workers never receive Claude AQS findings
- Stage B reviewer never receives AQS, sentinel, or Claude review artifacts
- Only normalized findings enter blue-team or triage flow — no raw Codex output
- Missing artifact = NO_EVIDENCE, never "clean"
- All worker outputs must publish unique pre-registered artifacts
- Cross-model never writes bead status directly

### 6.7 Monitoring Loop

Every 15s in normal mode, 5s in degraded mode:

1. `tmup_status` — heartbeat + stale-agent recovery trigger
2. `tmup_inbox` — blocker/finding messages
3. `tmup_next_action` — recommendation (advisory only)

Optional recovery actions:
- `tmup_reprompt` for idle-but-alive workers
- `tmup_harvest` for timeout/debug/forensics ONLY

## 7. Orchestration Integration

### 7.1 Pipeline Position

```
Runner submits → L1 Sentinel → L2 Oracle → same-model AQS →
  FFT-14 evaluates → [if FULL/TARGETED:
    crossmodel-supervisor owns session →
    Codex workers attack/review →
    harvest artifacts →
    Stage A → blue teams →
    Stage B → crossmodel-triage →
    resolve all findings] →
  bead status → hardened →
  Phase 4.5 Harden
```

### 7.2 Skill Updates Required

| File | Change |
|---|---|
| `skills/sdlc-orchestrate/SKILL.md` | Add FFT-14 evaluation between AQS and hardened transition. Add crossmodel-supervisor dispatch. Update quick-reference table. |
| `skills/sdlc-adversarial/SKILL.md` | (1) Document that hardened transition is gated by FFT-14 when cross-model is active. (2) Add structured AQS exit block emitting `aqs_verdict`, `arbiter_invoked`, `residual_risk_per_domain`, `dominant_residual_risk_domain`, `turbulence_sum` as machine-readable fields — not just prose. |
| `references/artifact-templates.md` | Add AQS structured exit schema with the five deterministic fields FFT-14 consumes. |
| `skills/sdlc-evolve/SKILL.md` | Add cross-model review to every Evolve cycle (Codex reviews system changes). |
| `references/fft-decision-trees.md` | Add FFT-14 definition. |

### 7.3 tmup Role Mapping

| tmup Role | SDLC-OS Function | Stage |
|---|---|---|
| investigator | Domain-specific red team probing | A |
| reviewer | Independent blind review | B |
| tester | Oracle/VORP claim challenge (future, not v1) | — |
| implementer | Not used in cross-model review | — |

## 8. New Components Summary

| Component | Files |
|---|---|
| Skill | `skills/sdlc-crossmodel/SKILL.md` |
| Agents | `agents/crossmodel-supervisor.md`, `agents/crossmodel-triage.md` |
| Reference update | `references/fft-decision-trees.md` (FFT-14) |
| Scripts | `scripts/crossmodel-preflight.sh`, `scripts/crossmodel-grid-up.sh`, `scripts/crossmodel-grid-down.sh`, `scripts/crossmodel-verify-artifact.sh`, `scripts/crossmodel-health.sh` |
| Artifact template | `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-codex-{stage}-{domain}-{role}.md` |
| Session journal | `docs/sdlc/active/{task-id}/crossmodel/{bead-id}-session.json` |

## 9. Acceptance Criteria

- [ ] Any tmup failure degrades gracefully without blocking the main bead path
- [ ] Every valid Codex finding is traceable to a structured artifact
- [ ] Every invalid/missing artifact is explicitly classified (NO_EVIDENCE, MALFORMED, etc.)
- [ ] Every retry and fallback is logged in session journal + decision trace
- [ ] No infinite retry loops
- [ ] No ambiguous "clean" result without evidence
- [ ] Stage A workers never see Claude AQS findings
- [ ] Stage B reviewer never sees any review artifacts
- [ ] Cross-model findings only enter the system through normalization + triage
- [ ] FFT-14 decision recorded in bead decision trace
- [ ] Serialized cross-model sessions per project (no grid races)
- [ ] Day-1: advisory only, not blocking

## 10. Version Target

Plugin version: 9.0.0 (Layer 9: Cross-Model Adversarial Review)

## 11. Sources

- Milvus blog: "AI Code Review Gets Better When Models Debate" — 53% → 80% detection with adversarial debate
- alecnielsen/adversarial-review — 4-phase Claude + Codex debate protocol
- dsifry/metaswarm — cross-model review where "the writer is always reviewed by a different AI model"
- tmup plugin architecture — SQLite WAL DAG, dispatch/harvest, Codex session management
- OWASP LLM Top 10 2025 — LLM06 Excessive Agency, cross-agent scope principles
- Agentmaxxing (vibecoding.app) — practical ceiling: 5-7 concurrent agents
- GitHub Agent HQ — official Claude + Codex multi-agent preview
