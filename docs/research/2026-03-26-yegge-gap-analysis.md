Now I have comprehensive knowledge of both systems. Let me compile the gap analysis report.

---

# GAP ANALYSIS: sdlc-os vs. Yegge's Gas Town Framework

## Methodology

This analysis compares the sdlc-os multi-agent SDLC plugin (as documented in its skill files, agent definitions, and reference materials) against Steve Yegge's Gas Town framework and broader thinking (as documented in "Welcome to Gas Town," "The Future of Coding Agents," "Welcome to the Wasteland," "Six New Tips for Better Coding With Agents," "Software Survival 3.0," the Gas Town Emergency User Manual, the GitHub repos steveyegge/gastown and steveyegge/beads, and commentary from Steve Klabnik, Maggie Appleton, and paddo.dev).

Each Gas Town concept is classified as ALREADY EMBEDDED, PARTIALLY EMBEDDED, or NOT YET EMBEDDED. NOT YET items are rated HIGH/MEDIUM/LOW priority.

---

## ALREADY EMBEDDED

### 1. Beads as Atomic Work Units
**Gas Town:** Beads are Git-backed atomic work units with ID, description, status, assignee, dependencies. The fundamental unit of work tracking.
**sdlc-os:** Beads are the core abstraction in `sdlc-orchestrate/SKILL.md`. Every piece of work is a bead with status, type, runner, dependencies, scope, input, output, Cynefin domain, assumptions, safe-to-fail, and confidence. Beads persist as markdown in `docs/sdlc/active/{task-id}/beads/`. Status flow: `pending -> running -> submitted -> verified -> proven -> hardened -> merged`.
**Verdict:** Fully embedded. sdlc-os beads are arguably richer than Gas Town beads (Cynefin classification, VORP confidence, loop state tracking).

### 2. Colony/Factory Model (Multi-Agent Over Single-Agent)
**Gas Town:** "Nature prefers colonies. Factories are going to win." Agents should be colony workers, not pair programmers. 20-30 parallel Claude Code instances.
**sdlc-os:** The entire architecture is a conductor-runner-sentinel-oracle colony. The Conductor (Opus) decomposes, Runners (Sonnet) execute in parallel, Guppies (Haiku) swarm for breadth, Sentinels (Haiku) patrol continuously. Five distinct operational roles, not a single agent.
**Verdict:** Fully embedded. sdlc-os was designed from the ground up as a multi-agent colony.

### 3. Disposable Ephemeral Workers
**Gas Town:** Polecats are ephemeral, per-rig workers spawning on-demand. They self-destruct after task completion. Sessions are disposable; identities persist.
**sdlc-os:** Runners are explicitly "Disposable. One work unit, one runner. Fresh context every time." Guppies are "Disposable micro-agents. One question, one answer, one exit." The system dispatches fresh agents for every bead, never accumulating context across work units.
**Verdict:** Fully embedded. sdlc-os's disposability discipline is strong.

### 4. Guppy/Swarm Pattern (Breadth-First Investigation)
**Gas Town:** Polecats work in swarms. Multiple agents attack a convoy simultaneously.
**sdlc-os:** Dedicated `sdlc-swarm` skill with a complete swarm cycle: DECOMPOSE -> DISPATCH -> HARVEST -> SYNTHESIZE -> RE-SWARM -> DELIVER. Guppies (Haiku) are the cheapest possible unit of work. Patterns documented: codebase audit, claim verification, regression scan, evidence collection, progressive narrowing. Maximum 3 swarm waves. Cost awareness: 20 guppies cost roughly the same as 1 Sonnet runner.
**Verdict:** Fully embedded. sdlc-os swarm mechanics are more formalized than Gas Town's.

### 5. Watchdog/Supervisor Chain (Erlang Influence)
**Gas Town:** Three-tier watchdog: Boot -> Deacon -> Witness. The Deacon patrols, the Witness monitors per-rig, Boot watches the Deacon. Klabnik explicitly connects this to Erlang supervisor trees.
**sdlc-os:** Sentinel (Haiku) runs continuous patrol alongside runners, not at checkpoints. Detects stuck work, drifted scope, weak evidence, broken assumptions, regressions. The Oracle Council provides a second tier of verification. The L6 Calibration Loop monitors system health across sessions. LOSA observer randomly samples quality.
**Verdict:** Fully embedded. sdlc-os has a functionally equivalent supervision hierarchy, though it uses different names and is organized around quality verification rather than liveness/health.

### 6. Escalation Protocol with Budget Exhaustion
**Gas Town:** Workers escalate when issues exceed local repair capacity. Severity-routed: CRITICAL (P0), HIGH (P1), MEDIUM (P2), flowing through Deacon -> Mayor -> Overseer.
**sdlc-os:** Six-level loop system (L0-L5) with hard budgets at every level. Each level self-corrects before escalating. "Naked escalation is forbidden" -- every escalation must include what was tried, why it failed, and what the target should consider. Correction signal format is standardized. Budget table: L0 (3 attempts), L1 (2 cycles), L2 (2 cycles), L2.5 (2 cycles). Budget exhaustion triggers backpressure cascade.
**Verdict:** Fully embedded. sdlc-os escalation is more structured and formalized than Gas Town's.

### 7. Adversarial Quality / Red-Blue Team Probing
**Gas Town:** Code review sweeps followed by bug-fix sweeps. The Refinery runs verification gates.
**sdlc-os:** Full Adversarial Quality System (AQS) with 4 red team commanders (functionality, security, usability, resilience), 4 blue team defenders, and an Arbiter using the Kahneman adversarial collaboration protocol. Non-zero-sum objective separation prevents GAN-style mode collapse. Daubert evidence gate. Pretrial filter with res judicata. Precedent system with stare decisis.
**Verdict:** sdlc-os goes far beyond Gas Town here. Gas Town has no formal adversarial quality system.

### 8. State Persistence in Git (Crash Recovery)
**Gas Town:** Work persists through Hooks -- git worktree-based persistent storage. Beads backed by Git. Sessions crash but work survives.
**sdlc-os:** Beads written to `docs/sdlc/active/{task-id}/beads/` as individual markdown files. "They persist in Git -- surviving agent sessions, crashes, and context resets." AQS state has explicit resume-from-state semantics. Phase 4.5 state written after each step to enable resume from last completed step. The normalization protocol (Phase 0) explicitly detects and recovers from interrupted workflows.
**Verdict:** Fully embedded.

### 9. Nondeterministic Idempotence (NDI)
**Gas Town:** "Even though the path is fully nondeterministic, the outcome -- the workflow you wanted to run -- eventually finishes, guaranteed, as long as you keep throwing agents at it." Unlike Temporal's deterministic replay, NDI accepts variable paths toward terminal goals.
**sdlc-os:** Explicitly referenced in `sdlc-harden/SKILL.md` ("State Persistence (Yegge NDI)"). The bead system with acceptance criteria ensures that regardless of which runner instance executes, the outcome converges on the same acceptance criteria. The loop system (L0-L5) keeps throwing agents at problems with decreasing budgets until convergence or explicit escalation. Phase 0 normalization recovers interrupted workflows.
**Verdict:** Fully embedded. sdlc-os explicitly names and implements NDI.

### 10. Rule of Five (Multi-Pass Review)
**Gas Town:** "If you make an LLM review something five times, with different focus areas each time, it generates superior outcomes." Apply to designs, plans, code, tests, audits.
**sdlc-os:** The multi-layer verification system implements this structurally: Runner self-check (L0) -> Sentinel verification (L1) -> Oracle audit (L2) -> AQS red/blue (L2.5) -> Phase 4.5 reliability hardening (L2.75). Each layer examines the same work with different focus areas and different agents. The Oracle Council alone has three tiers (static analysis, runtime proof, adversarial challenge). AQS uses 4 domain-specific review channels. LOSA provides random-sample verification on top.
**Verdict:** Fully embedded. sdlc-os achieves 5+ distinct review passes structurally.

### 11. 40% Code Health Budget
**Gas Town:** "Spend 40% of your time on code health or spend >60% later." Regular code health reviews, agent-filed issues for code smells, dedicated refactoring sessions.
**sdlc-os:** Quality SLOs with error budget policy (`references/quality-slos.md`). Three budget states: healthy, warning, depleted. When budget depletes, the system slows down (all beads get full AQS, constitution review triggered, LOSA sampling increased). Fitness function catalog (`references/fitness-functions.md`) with concrete automated checks. Convention scanner + drift detector + convention enforcer patrol continuously.
**Verdict:** Fully embedded. sdlc-os has formalized this into an SLO-based governance system rather than a time-allocation heuristic.

### 12. Complexity/Cynefin-Based Scaling
**Gas Town:** Not explicitly Cynefin, but implicit -- different treatment for simple vs complex work. Clear beads skip AQS.
**sdlc-os:** Explicit Cynefin domain assignment to every bead (clear, complicated, complex, chaotic, confusion). Each domain has different treatment: clear beads skip AQS entirely; complicated get recon + 1-2 domains; complex get full AQS; chaotic skip to act-first; confusion blocked until decomposed. Complexity-based model escalation for Oracle (Layer 1/2/3 based on complexity).
**Verdict:** Fully embedded. sdlc-os has a richer complexity model than Gas Town.

### 13. Merge Conflict Resolution
**Gas Town:** The Refinery handles sequential merging. The merge wall problem: workers diverge from shared baseline, later workers can't rebase.
**sdlc-os:** Parallelization rules in `sdlc-orchestrate/SKILL.md`: safe to parallelize (different files/modules, investigation beads, independent tests), must serialize (same file, design dependencies, explicit dependency links). Conflict resolution: Conductor reads both outputs, dispatches fresh runner with both + conflict description, resolver produces merged result, Sentinel verifies merge.
**Verdict:** Fully embedded.

### 14. Seancing (Session Recovery)
**Gas Town:** `gt seance` lets workers communicate with predecessors via Claude Code's `/resume`. Workers restart killed sessions to retrieve handed-off work instructions.
**sdlc-os:** Phase 0 normalization (`sdlc-normalize/SKILL.md`) detects interrupted workflows, reconstructs bead states, and recommends re-entry points. Resume protocol: read state.md + beads, recover Cynefin assignments and quality budget. AQS has explicit resume-from-state semantics with phase tracking.
**Verdict:** Fully embedded. sdlc-os uses a different mechanism (state files vs session resume) but achieves the same outcome of cross-session continuity.

### 15. Convention/Constitution Governance
**Gas Town:** "Zero Framework Cognition" and guiding principles to prevent "heresies" (systematic misconceptions agents propagate).
**sdlc-os:** Code constitution (`references/code-constitution.md`), Convention Map (`docs/sdlc/convention-map.md`), convention scanner, convention enforcer, drift detector. Convention dimensions documented in `references/convention-dimensions.md`. Constitution review triggered when error budget depletes.
**Verdict:** Fully embedded. sdlc-os has a more elaborate convention governance system.

### 16. Calibration / Drift Detection
**Gas Town:** The DoltHub report documented status reporting inaccuracy and autonomous merges despite test failures. Gas Town's response: code review sweeps, the "Serial Killer Murder Mystery" bug class.
**sdlc-os:** Full calibration protocol (`references/calibration-protocol.md`) with L6 loop. Three drift types monitored: semantic, coordination, behavioral. Regression watchlist. Noise audit with overlap measurement. LOSA observer integration. Calibration beads with planted defects run through the full L1-L2.5 pipeline.
**Verdict:** Fully embedded. sdlc-os has a significantly more formalized drift detection system.

---

## PARTIALLY EMBEDDED

### 17. GUPP (Gas Town Universal Propulsion Principle)
**Gas Town:** "If there is work on your hook, YOU MUST RUN IT." Each agent has a persistent Hook (a special pinned bead) where work molecules attach. The GUPP Nudge compensates for Claude Code's politeness by sending notifications within 5 minutes to restart stalled workers. This is the engine that prevents agents from idling.
**sdlc-os implementation:** The Conductor dispatches runners, and the loop system ensures work keeps moving with hard budgets and backpressure cascades. Sentinels detect stuck work.
**Gap:** sdlc-os has no agent-side pull mechanism -- it is purely push-based (Conductor dispatches). There is no Hook concept where work sits waiting for an agent to pull it. There is no nudge/heartbeat mechanism to restart stalled runners. If a runner dies mid-execution, recovery depends on the Conductor noticing (via normalization on next session entry), not on an autonomous pull loop.
**Impact:** In single-session operation this gap is minor. In a persistent multi-session colony it would be significant.

### 18. Patrol Loops with Exponential Backoff
**Gas Town:** Patrol workers (Refinery, Witness, Deacon) run ephemeral loops processing work transactionally using wisps, implementing exponential backoff when idle, and waking immediately upon mutations.
**sdlc-os implementation:** Sentinels run "continuous patrol, not checkpoint QA." The loop system ensures continuous verification. LOSA observer runs on random samples.
**Gap:** sdlc-os patrols are conceptual (the Conductor dispatches sentinel checks after each runner submission) but there is no autonomous patrol loop running independently with its own backoff schedule. Sentinels are dispatched by the Conductor, not self-running. There is no exponential backoff -- the system either checks or doesn't.
**Impact:** This limits sdlc-os to a reactive supervision model rather than a proactive, self-sustaining one.

### 19. Handoff Protocol (Context Window Management)
**Gas Town:** `gt handoff` / `/handoff` -- agents gracefully restart sessions when context windows fill. Work state transfers to new session. Three variants: flexible/expensive, inflexible, mechanical/no-cost.
**sdlc-os implementation:** Phase 0 normalization detects and recovers from interrupted workflows. Beads persist in Git. AQS has resume-from-state semantics. State.md tracks progress.
**Gap:** sdlc-os has recovery FROM session loss but no proactive handoff BEFORE context exhaustion. There is no mechanism for a runner to detect its own context window filling up and trigger a graceful handoff. The system assumes either the runner completes or crashes, with no middle path.
**Impact:** Medium -- context exhaustion is a real failure mode for long-running beads, and the current system handles it only reactively.

### 20. Convoys (Work-Order Bundles)
**Gas Town:** Convoys wrap multiple work molecules into tracked delivery orders. Dashboards display expanding trees of constituent issues. Multiple swarms can attack a convoy before completion.
**sdlc-os implementation:** The bead manifest (created during Phase 3: Architect) groups beads into a task with dependencies. The task directory structure (`docs/sdlc/active/{task-id}/`) bundles all beads.
**Gap:** sdlc-os has no formal convoy abstraction that bundles beads into a higher-level trackable unit with its own lifecycle, dashboard, and multi-swarm attack capability. The task is the convoy-equivalent, but it lacks the autonomy of Gas Town convoys (which can be assigned to multiple workers, tracked independently, and have mountain-label autonomous stall detection).
**Impact:** Low for single-task workflows. Higher for long-running multi-task orchestration.

### 21. The Refinery (Bors-Style Bisecting Merge Queue)
**Gas Town:** The Refinery is a per-rig merge queue processor. It batches merge requests, runs verification gates, uses Bors-style bisecting to identify which merge broke the build. Failed merges are either fixed inline or re-dispatched.
**sdlc-os implementation:** Phase 5 Synthesize handles merging runner outputs. Conflict resolution dispatches a fresh runner with both outputs. Fitness checks and drift detection run on the integrated result.
**Gap:** sdlc-os has no bisecting merge queue. Merges happen during Synthesize as a batch, not as a sequential queue with automated bisection on failure. There is no concept of a dedicated merge agent that runs continuously.
**Impact:** In the current single-Conductor model this is manageable. If sdlc-os scaled to 20+ parallel runners, the lack of a dedicated merge queue would become critical.

---

## NOT YET EMBEDDED

### 22. Hook / Pull-Based Work Distribution -- **HIGH**
**Gas Town:** Every agent has a Hook (a special pinned bead) that serves as its work queue. GUPP mandates: if work is on your hook, run it. Work distribution is pull-based -- agents pull from their hooks, not just pushed by a conductor.
**sdlc-os gap:** Work distribution is entirely push-based. The Conductor dispatches runners with precise context packets. There is no agent-side work queue, no self-scheduling, no hook concept.
**Could strengthen:** The Conductor role in `sdlc-orchestrate/SKILL.md`. A hook mechanism would enable more autonomous operation, reduce Conductor bottlenecks, and support persistent colony operation where agents self-schedule.

### 23. Persistent Agent Identity with CV Chains -- **HIGH**
**Gas Town:** Polecats have persistent identities as Beads backed by Git. Each maintains a permanent agent bead, CV chain, and work history. Names recycle but completion histories accumulate. Crew members are named, long-lived agents.
**sdlc-os gap:** Runners are purely disposable with no persistent identity. There is no agent identity bead, no CV chain, no accumulated work history. The system cannot learn which runner configurations perform best or track agent performance over time.
**Could strengthen:** The calibration protocol (`references/calibration-protocol.md`) and the quality SLO system. Persistent agent identity would enable per-agent performance tracking, drift detection at the individual agent level, and data-driven model/prompt optimization.

### 24. The Deacon Pattern (Autonomous Town-Level Daemon) -- **HIGH**
**Gas Town:** The Deacon is a daemon beacon running continuous patrol cycles. It is triggered by a heartbeat every few minutes. It propagates "Do Your Job" signals downward through the worker hierarchy. Boot watches the Deacon every 5 minutes. This creates a self-sustaining supervisory system that operates without human intervention.
**sdlc-os gap:** All supervision in sdlc-os is Conductor-initiated. The Conductor dispatches sentinel checks, but if the Conductor itself stalls, there is no watchdog watching the watchdog. There is no daemon heartbeat, no autonomous patrol cycle, no Boot-like meta-supervisor.
**Could strengthen:** Overall system liveness and resilience. A Deacon-equivalent would ensure the SDLC pipeline continues operating even when the Conductor session is lost or stalled.

### 25. MEOW Stack Hierarchy (Molecules / Protomolecules / Formulas / Wisps) -- **MEDIUM**
**Gas Town:** Full workflow abstraction hierarchy: Formulas (TOML templates) -> Protomolecules (template classes) -> Molecules (durable chained workflows) -> Wisps (ephemeral beads destroyed after runs). This enables composable, reusable, multi-step workflow definitions with different persistence characteristics.
**sdlc-os gap:** sdlc-os has beads and the bead manifest, but no formal workflow template/instantiation system. There is no formula-to-molecule pipeline, no wisps for ephemeral orchestration noise, no protomolecule reuse across tasks. The SDLC phases are hardcoded in `sdlc-orchestrate/SKILL.md` rather than expressed as composable molecules.
**Could strengthen:** Reusability across tasks and projects. Protomolecules for common patterns (e.g., "audit-then-fix," "investigate-design-implement") would reduce Conductor overhead. Wisps would prevent orchestration noise from polluting the Git history.

### 26. Wisps (Ephemeral Non-Persisted Orchestration Beads) -- **MEDIUM**
**Gas Town:** Wisps exist in-database with hash IDs but are NOT persisted to Git. Upon completion, they either vanish or "burn" into single-line summaries. This prevents orchestration noise from polluting the repository.
**sdlc-os gap:** Every bead and every AQS artifact persists to Git. Recon guppy results, strike guppy results, sentinel checks -- all written as markdown files. This creates significant Git noise for large tasks.
**Could strengthen:** Artifact management in `sdlc-adversarial/SKILL.md` and `sdlc-harden/SKILL.md`. A wisp concept would let ephemeral verification work (recon bursts, sentinel micro-checks) execute without polluting the repository, burning down to summary lines in the bead file.

### 27. Guzzoline (Work Liquidity Metric) -- **LOW**
**Gas Town:** Guzzoline represents the total "sea of molecularized work" -- work expressed in forms agents can execute atomically. It is the fuel metaphor for measuring how much executable work is available.
**sdlc-os gap:** No equivalent concept. The system tracks bead status but has no metric for work liquidity -- how much decomposed, ready-to-execute work exists in the pipeline.
**Could strengthen:** Phase 4 (Execute) dispatch efficiency. A guzzoline-equivalent metric would help the Conductor decide when to decompose more work versus execute existing beads, preventing both work starvation and over-decomposition.

### 28. Federation / Wasteland Model (Multi-Instance Trust Network) -- **LOW**
**Gas Town:** The Wasteland links multiple independent Gas Town instances into a trust network. Dolt database enables fork/branch/merge on structured data. Trust ladders gate participation. Stamps provide evidence-backed reputation. The Yearbook Principle prevents self-attestation.
**sdlc-os gap:** sdlc-os is a single-instance system. There is no federation model, no trust network, no cross-instance reputation, no stamps, no Wanted Board. The system operates within one project, one repository, one Claude session at a time.
**Could strengthen:** Multi-project, multi-team, or open-source scenarios. However, sdlc-os is currently scoped as a single-project SDLC orchestrator, so federation is out of scope for the near term.

### 29. Trust Ladders and Stamps (Reputation System) -- **LOW**
**Gas Town:** Three-level trust system: Registered Participant -> Contributor -> Maintainer. Stamps are multi-dimensional attestations scoring quality, reliability, creativity. Yearbook Principle: you cannot stamp your own work.
**sdlc-os gap:** No agent reputation system. All agents are treated equally within their model tier. There is no mechanism for tracking which agent configurations or prompt patterns produce better results over time, nor for building trust in specific agent behaviors.
**Could strengthen:** The calibration protocol and quality SLO tracking. Agent-level reputation would enable data-driven decisions about which agents to trust with complex vs clear beads.

### 30. Collusion Detection (Anti-Fraud for Multi-Agent) -- **LOW**
**Gas Town:** Analyzes stamp graph topology for suspicious patterns: mutual stamping clusters, sharp boundaries, absence of external critics. Designed to make fraud unprofitable, not impossible.
**sdlc-os gap:** No collusion detection. The AQS has structural separation (red/blue teams don't share context) and the Arbiter is independent, but there is no mechanism to detect if agents develop coordinated anti-patterns (e.g., a Sentinel consistently overlooking a specific runner's defects).
**Could strengthen:** The calibration protocol. Collusion detection would be relevant if sdlc-os ever supports persistent agent identities -- detecting when specific agent pairings produce suspiciously clean results.

### 31. Wanted Board (Open Work Registry) -- **LOW**
**Gas Town:** Centralized, open work registry where anyone can post tasks and anyone can claim them. Four-stage lifecycle: open, claimed, in review, completed.
**sdlc-os gap:** Work originates from the user and is decomposed by the Conductor. There is no open work registry. Agents cannot propose work or claim tasks independently.
**Could strengthen:** Phase 1 (Frame) and Phase 2 (Scout). A Wanted Board pattern could let investigator agents surface work opportunities that the Conductor or user hadn't considered. However, this is more relevant for a colony model than sdlc-os's current conductor-centric model.

### 32. The Mayor (User-Facing Concierge Agent) -- **MEDIUM**
**Gas Town:** The Mayor is the primary concierge agent handling user interactions, kicking off convoys, and receiving completion notifications. The Mayor never writes code -- it is a pure coordinator.
**sdlc-os gap:** The Conductor (Opus) serves both as orchestrator AND as the user-facing interface. There is no dedicated concierge agent that handles user communication separately from orchestration. The Conductor's prompt mixes orchestration logic with user-facing responsibilities.
**Could strengthen:** Separation of concerns in `sdlc-orchestrate/SKILL.md`. A dedicated Mayor-equivalent would let the orchestration logic focus purely on work distribution while a concierge handles user interaction, progress reporting, and decision solicitation.

### 33. PR Sheriff (Automated PR Triage) -- **LOW**
**Gas Town:** Automated role with permanent hook that automatically triages pull requests, routing simple merges to crew while flagging complex reviews for human attention.
**sdlc-os gap:** No automated PR triage. The system produces code but does not manage the PR lifecycle. Phase 5 Synthesize produces a delivery summary but does not auto-create or triage PRs.
**Could strengthen:** The end-to-end delivery pipeline. A PR Sheriff equivalent would close the loop between sdlc-os output and the actual merge-to-main workflow.

### 34. Desire Paths / Agent UX Design -- **MEDIUM**
**Gas Town / Software Survival 3.0:** Build interfaces that match how agents naturally attempt to use them. Watch agents fail, ask "how did you want this to work?", then implement their intuitive preferences. "Agent UX Designer" is an emerging career.
**sdlc-os gap:** The dispatch patterns and agent definitions are designed by the human operator, not iteratively shaped by observing agent behavior. There is no feedback mechanism for detecting when agents struggle with the dispatch format, context packet structure, or output format.
**Could strengthen:** All agent dispatch patterns in `references/dispatch-patterns.md` and agent definitions in `agents/*.md`. A desire-path feedback loop would capture agent failures at the dispatch/format level and surface them for iterative improvement.

### 35. Software Survival Ratio / Insight Compression -- **LOW**
**Gas Town / Software Survival 3.0:** Survival(T) = (Savings x Usage x H) / (Awareness_cost + Friction_cost). Tools survive by compressing insight and minimizing agent friction.
**sdlc-os gap:** sdlc-os does not evaluate its own tooling through a survival lens. The reuse-scout checks for existing code to reuse, but there is no meta-evaluation of whether sdlc-os's own orchestration overhead is justified by the quality it produces.
**Could strengthen:** Meta-analysis. A survival-ratio check could help the Conductor decide when the full SDLC pipeline is worth running vs when a simpler approach suffices (partially addressed by Cynefin scaling, but not formalized as a cost-benefit ratio).

### 36. Heresies Detection (Systematic Agent Misconceptions) -- **MEDIUM**
**Gas Town Emergency Manual:** Agents propagate "heresies" -- systematic misconceptions that embed incorrect architectural assumptions (e.g., "idle polecats" concept). These require explicit guiding principles in agent onboarding.
**sdlc-os gap:** The code constitution and convention map address code-level conventions but not agent-level misconceptions. There is no mechanism for detecting and documenting recurring incorrect assumptions that agents make about the system itself (as opposed to the codebase they're working on).
**Could strengthen:** Agent prompt management and the calibration protocol. A heresies registry would document known agent misconceptions, and calibration could test whether agents still hold them.

### 37. Crew Pattern (Long-Lived Named Agents for Design Work) -- **MEDIUM**
**Gas Town:** Crew members are named, long-lived agents (3-8 per rig) for persistent collaboration. Unlike ephemeral Polecats, Crew members maintain context across sessions. They excel at design work requiring extensive back-and-forth negotiation.
**sdlc-os gap:** All agents are ephemeral. The sonnet-designer is dispatched fresh for each design task. There is no mechanism for maintaining a design agent across sessions that accumulates domain knowledge about the project.
**Could strengthen:** Phase 3 (Architect) and long-running complex projects. A Crew-equivalent for design work would enable richer architectural reasoning that draws on accumulated project context rather than starting fresh each time.

---

## SUMMARY TABLE

| # | Concept | Status | Priority |
|---|---------|--------|----------|
| 1 | Beads as atomic work units | ALREADY | -- |
| 2 | Colony/factory model | ALREADY | -- |
| 3 | Disposable ephemeral workers | ALREADY | -- |
| 4 | Guppy/swarm pattern | ALREADY | -- |
| 5 | Watchdog/supervisor chain | ALREADY | -- |
| 6 | Escalation with budgets | ALREADY | -- |
| 7 | Adversarial quality (Red/Blue) | ALREADY | -- |
| 8 | State persistence in Git | ALREADY | -- |
| 9 | Nondeterministic Idempotence (NDI) | ALREADY | -- |
| 10 | Rule of Five (multi-pass review) | ALREADY | -- |
| 11 | 40% code health budget | ALREADY | -- |
| 12 | Complexity-based scaling (Cynefin) | ALREADY | -- |
| 13 | Merge conflict resolution | ALREADY | -- |
| 14 | Seancing (session recovery) | ALREADY | -- |
| 15 | Convention/constitution governance | ALREADY | -- |
| 16 | Calibration/drift detection | ALREADY | -- |
| 17 | GUPP (pull-based propulsion) | PARTIAL | -- |
| 18 | Patrol loops with backoff | PARTIAL | -- |
| 19 | Handoff protocol | PARTIAL | -- |
| 20 | Convoys (work-order bundles) | PARTIAL | -- |
| 21 | Refinery (bisecting merge queue) | PARTIAL | -- |
| 22 | Hook / pull-based work distribution | NOT YET | HIGH |
| 23 | Persistent agent identity + CV chains | NOT YET | HIGH |
| 24 | Deacon pattern (autonomous daemon) | NOT YET | HIGH |
| 25 | MEOW hierarchy (Molecules/Protomolecules/Formulas) | NOT YET | MEDIUM |
| 26 | Wisps (ephemeral non-persisted beads) | NOT YET | MEDIUM |
| 27 | Guzzoline (work liquidity metric) | NOT YET | LOW |
| 28 | Federation / Wasteland model | NOT YET | LOW |
| 29 | Trust ladders and stamps | NOT YET | LOW |
| 30 | Collusion detection | NOT YET | LOW |
| 31 | Wanted Board (open work registry) | NOT YET | LOW |
| 32 | Mayor (dedicated concierge agent) | NOT YET | MEDIUM |
| 33 | PR Sheriff (automated PR triage) | NOT YET | LOW |
| 34 | Desire paths / agent UX feedback | NOT YET | MEDIUM |
| 35 | Software survival ratio | NOT YET | LOW |
| 36 | Heresies detection | NOT YET | MEDIUM |
| 37 | Crew pattern (long-lived design agents) | NOT YET | MEDIUM |

**Totals:** 16 ALREADY EMBEDDED, 5 PARTIALLY EMBEDDED, 16 NOT YET EMBEDDED (3 HIGH, 5 MEDIUM, 8 LOW).

---

## CRITICAL ARCHITECTURAL OBSERVATION

The paddo.dev analysis identifies a fundamental tension: Gas Town uses **operational/functional roles** (Mayor, Polecat, Witness, Deacon) while BMAD-style systems use **SDLC personas** (Analyst, Architect, Developer, QA). sdlc-os occupies a fascinating middle ground -- it uses **SDLC phase names** (Frame, Scout, Architect, Execute, Synthesize) but populates them with **operational role agents** (Conductor, Runner, Sentinel, Oracle, Guppy). The agents do not have elaborate personas competing for attention; they have functional contracts. This hybrid avoids the worst traps of SDLC-persona scaffolding (context pollution, sequential friction, phase gate confusion) while retaining SDLC-phase legibility for humans.

The three HIGH-priority gaps (Hooks, Persistent Identity, Deacon) all point toward the same underlying difference: **sdlc-os is a single-session orchestration system, while Gas Town is a persistent colony runtime.** Closing these gaps would require sdlc-os to evolve from "a conductor that dispatches agents within a session" to "a colony that self-sustains across sessions." Whether that evolution is desirable depends on whether sdlc-os aims to remain a session-scoped quality system or become a persistent development factory.

---

Sources:
- [Welcome to Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- [The Future of Coding Agents](https://steve-yegge.medium.com/the-future-of-coding-agents-e9451a84207c)
- [Welcome to the Wasteland: A Thousand Gas Towns](https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f)
- [Six New Tips for Better Coding With Agents](https://steve-yegge.medium.com/six-new-tips-for-better-coding-with-agents-d4e9c86e42a9)
- [Software Survival 3.0](https://steve-yegge.medium.com/software-survival-3-0-97a2a6255f7b)
- [Gas Town Emergency User Manual](https://steve-yegge.medium.com/gas-town-emergency-user-manual-cf0e4556d74b)
- [GitHub: steveyegge/gastown](https://github.com/steveyegge/gastown)
- [GitHub: steveyegge/beads](https://github.com/steveyegge/beads)
- [Gas Town Glossary](https://github.com/steveyegge/gastown/blob/main/docs/glossary.md)
- [How to Think About Gas Town - Steve Klabnik](https://steveklabnik.com/writing/how-to-think-about-gas-town/)
- [Gas Town's Agent Patterns - Maggie Appleton](https://maggieappleton.com/gastown)
- [A Day in Gas Town - DoltHub](https://www.dolthub.com/blog/2026-01-15-a-day-in-gas-town/)
- [GasTown and the Two Kinds of Multi-Agent - paddo.dev](https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/)