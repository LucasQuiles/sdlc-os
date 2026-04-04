# Colony Runtime — Deferred Items

Items cut or deferred from Phase 2 by council review. Each has a principled reason, the dissenting opinion, and the trigger condition for re-evaluation.

---

## Cut (Not Planned)

### Wisps (Ephemeral DB-Only Beads)
**What:** Beads that exist only in tmup DB, not in Git. Burned after execution.
**Why Cut:** Violates SC-COL-29 (bridge MUST stage specific bead file via git add). Bridge safety contract requires Git commits for audit trail and crash recovery (spec §3.3 step 6). Forking the bridge into Git and non-Git paths doubles the attack surface.
**Dissent:** Simplicity auditor rated 2/5 (optimization). Gas Town uses Wisps for high-velocity orchestration overhead.
**Re-evaluate When:** If colony throughput exceeds 100 beads/hour and Git commit overhead becomes measurable bottleneck. Requires bridge refactor with a Wisp-specific code path and new safety constraints for non-Git recovery.
**Council Source:** Adversarial auditor CRITICAL finding — "Wisps bypass Git by design. SC-COL-29 and SC-COL-30 REQUIRE Git commits."

### Clear Bead Fast Path (Skip Conductor Eval)
**What:** Trivial beads skip Conductor evaluation, advancing directly via deterministic bridge checks only.
**Why Cut:** Undermines the L0-L1-L2 correction loop design. The bridge validates output structure (size + sentinel) but cannot evaluate semantic quality. Skipping Conductor eval means trusting worker self-assessment — which is precisely what the quality loop exists to prevent.
**Dissent:** Spec §8 claims "saves ~$3/bead" for clear beads. Karpathy deterministic-routing principle (NE-6) supports routing clear beads to cheaper checks.
**Re-evaluate When:** If a deterministic acceptance-criteria checker can be built (not LLM-based) that verifies semantic output quality for clear-domain beads. This would be a bridge-level function, not a Conductor skip.
**Council Source:** Adversarial auditor CRITICAL — "A worker marks itself complete on a clear bead, nobody checks, bridge advances status. Bug ships."

### PDSA Watchdog (Probe-Before-Restart)
**What:** Deming-style Plan-Do-Study-Act improvement cycle in the watchdog.
**Why Cut:** Already implemented. The existing self-watchdog (`_self_watchdog_task`), `_is_lock_stale()` PID+timestamp checks, and `_check_conductor_timeout()` with bridge lock verification constitute a probe-before-restart pattern. PDSA is a rebranding of existing behavior.
**Dissent:** None. All 7 agents agreed this is already done.
**Re-evaluate When:** Never. Mark as implemented.
**Council Source:** Adversarial auditor MEDIUM — "PDSA is a rebranding of existing behavior, not new functionality."

---

## Deferred to Phase 3

### Boot (Independent Deacon Watchdog Daemon)
**What:** Separate process that monitors Deacon health externally, independent of Deacon's self-watchdog.
**Why Deferred:** Duplicates systemd `WatchdogSec=120` + `Restart=on-failure` + the internal `_self_watchdog_task`. Adding a second supervisor creates coordination races (Boot restarts Deacon while systemd RestartSec counting down = double-spawn). Phase 2 adds behavioral watchdog (time-in-state) which covers the gap Boot was meant to fill.
**Dissent:** Simplicity auditor rated 5/5 (essential). Gas Town has Boot as a core role. Thinker investigator found the behavioral-health gap that Phase 2 item 3.1 now addresses.
**Re-evaluate When:** If Deacon behavioral watchdog (3.1) proves insufficient in production — specifically if stuck-in-CONDUCTING events occur that the enhanced watchdog fails to catch. Evidence: 3+ incidents in colony-sessions.log where CONDUCTING exceeded max-state-duration without watchdog intervention.
**Council Source:** Adversarial CRITICAL — "Two supervisors fighting over the same process." Gap analyst — "Boot EXISTS as _self_watchdog_task."

### Dogs (Maintenance Patrol Daemon)
**What:** Separate daemon for clone pruning, branch hygiene, WAL checkpoints, Wisp cleanup.
**Why Deferred:** Core function (clone pruning) absorbed into Deacon item 3.3. Adding a fourth process increases failure mode surface quadratically. Existing `clone-manager.sh` functions cover the mechanics; they just need a caller.
**Dissent:** Test integrity noted Dogs would be the natural home for scheduled maintenance. STPA identified 2 CRITICAL UCAs if Dogs prunes clones with bridge_synced=0.
**Re-evaluate When:** If Deacon main loop becomes overloaded with maintenance tasks (pruning takes >30s blocking loop). Evidence: watchdog near-miss warnings in deacon.log during prune cycles. Phase 2 mitigation: pruning runs in `asyncio.to_thread()`.
**Council Source:** Adversarial HIGH — "Adding a fourth process to a system designed for three."

### Seancing (Session Resurrection via /resume)
**What:** New Conductor reads old session transcript for crash recovery context, using Claude CLI `/resume`.
**Why Deferred:** Pre-flight handoff block (SC-COL-04) + RECOVER session type already provide structured recovery. Claude CLI `--resume` in non-interactive `-p` mode is unvalidated (same class of issue as V-02 `--permission-mode auto`). Session transcripts are natural language requiring re-interpretation by LLM — introduces hallucination risk in recovery path.
**Dissent:** Simplicity auditor rated 4/5. Thinker investigator identified it as "hard to retrofit later." Gas Town uses Seancing as a core resilience mechanism.
**Re-evaluate When:** If Claude CLI validates `--resume` support in `-p` mode (add to validation spike as V-07). Also requires a structured session summary format (not raw transcript) to eliminate hallucination risk.
**Council Source:** Adversarial HIGH — "Either duplicates existing recovery, or requires persisting full LLM session transcripts."

### Convoys (Multi-Bead Delivery Bundles)
**What:** Named work-order bundles wrapping multiple beads with stall detection, dashboard tracking, and smart skip logic.
**Why Deferred:** Existing bead dependency graph (SC-COL-10) + per-bead tracking suffices for current scale. Convoys add an abstraction layer that must stay synchronized with the underlying dependency graph — two systems tracking the same concept = inevitable drift.
**Dissent:** Gap analyst rated MED. STPA identified convoy stall timeout conflicting with per-domain heartbeat thresholds (needs SC-COL-34 if implemented).
**Re-evaluate When:** If colony processes >20 beads in a single task and the Conductor's per-bead EVALUATE loop becomes unwieldy. Evidence: EVALUATE sessions timing out because per-bead iteration exceeds 30-min wall clock.
**Council Source:** Adversarial HIGH — "Abstraction layer that must stay synchronized with the underlying bead dependency graph."

### Chaos Probing (Synthetic Fault Injection)
**What:** Fault injection framework: random SIGTERM to conductor, lock file corruption, inotify kill, DB WAL truncation. Guard behind `COLONY_CHAOS_MODE=1` env var.
**Why Deferred:** Premature. Colony has never run at scale. Zero production failure data exists. The end-to-end completion rate metric (Phase 2 item 3.6) must exist before chaos probing has a metric to validate against.
**Dissent:** Reason (thinker) — "Proactive identification of latent conditions requires active probing, not just post-incident analysis." Leveson — "Safety is emergent; safe components can create unsafe systems."
**Re-evaluate When:** After 10+ real colony runs produce baseline completion rate data. Chaos probing validates whether the completion rate degrades gracefully under fault injection or collapses.
**Council Source:** Adversarial MEDIUM — "Engineering effort spent on testing a system that has not been proven to work in the normal case."

### Codex Cross-Model as Separate Implementation
**What:** Building a new cross-model review flow separate from the existing sdlc-crossmodel skill.
**Why Deferred:** The `sdlc-crossmodel` skill already manages tmux grid lifecycle, Codex worker dispatch, artifact collection, and finding deduplication via `crossmodel-triage`. Phase 2 item 3.4 wires the trigger into the conductor prompt — no new implementation needed.
**Dissent:** None. Merged into existing skill.
**Re-evaluate When:** If sdlc-crossmodel skill proves insufficient for colony-specific needs (e.g., clone-aware review, bead-output validation). Currently no evidence it will be.
**Council Source:** Adversarial MEDIUM — "Maintaining two implementations of the same cross-model review flow."

---

## Deferred Thinker Principles (Phase 3 Backlog)

From the 7-agent deep-dive, 7 HIGH-priority concepts from `docs/research/2026-03-26-reconciled-delta.md`:

| # | Concept | Thinker | Why Deferred | Re-evaluate |
|---|---------|---------|-------------|-------------|
| NE-6 | Deterministic task routing pre-L1 | Karpathy | Requires defining which L1 checks can be deterministic vs LLM | After Phase 2 completion metrics show L1 correction rates |
| NE-11 | Acceptance criteria semantic gate | Reward Hacking | Conductor-level change; bridge stays deterministic by design | After Phase 2 shows false-positive bead advancement rate |
| NE-13 | Common/special cause variation gate | Deming | Needs baseline metrics (Phase 2 item 3.6) before calibration policy | After 20+ colony sessions produce threshold adjustment data |
| NE-15 | Let-it-crash L0→L1 on first failure | Actor Model | Controversial: reduces L0 self-correction budget from 3 to 1 | After Phase 2 shows L0 retry success rate — if <30%, cut to 1 |
| NE-22 | Pull-based work distribution (Hook/GUPP) | Yegge | Architectural shift from push to pull; highest scope change | Phase 4 if Conductor becomes dispatch bottleneck |
| NE-23 | Persistent agent identity + CV chains | Yegge | Requires tmup schema migration v5 (agent_performance table) | After Phase 2 per-agent metrics show worker-type correlations |
| NE-24 | Behavioral-health Boot-tier watchdog | Yegge | Partially addressed by Phase 2 item 3.1 (time-in-state) | If 3.1 proves insufficient in production |

---

## Proposed Safety Constraints (Not Yet in Registry)

Constraints identified by STPA but deferred because their parent items were deferred:

| ID | Constraint | Parent Item | Status |
|----|-----------|-------------|--------|
| SC-COL-32 | Boot restart MUST check BRIDGE_LOCK_FILE staleness before SIGTERM to Deacon | Boot | Deferred (Boot deferred) |
| SC-COL-33 | Seance MUST only ingest context produced after most recent recover_stale_claims | Seancing | Deferred (Seancing deferred) |
| SC-COL-34 | Convoy stall timeout MUST use per-domain HEARTBEAT_THRESHOLDS, not flat value | Convoys | Deferred (Convoys deferred) |

---

*Last updated: 2026-04-03. Review trigger: after 10 real colony runs or any production incident attributable to a deferred item.*
