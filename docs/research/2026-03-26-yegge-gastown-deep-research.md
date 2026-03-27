I now have comprehensive material. Here is the full research report.

---

# Steve Yegge's Gas Town Model: Complete Research Report

## Origin and Context

Gas Town is an open-source multi-agent orchestration framework created by Steve Yegge, released January 1, 2026. Yegge built it over the second half of 2025 (going through four iterations: TypeScript, Go, Python, then final Go) while working as an independent developer after leaving Sourcegraph. The name comes from Mad Max: Fury Road, reflecting the chaotic, industrial nature of managing 20-30 AI coding agents in parallel. It is self-described as "100% vibecoded" -- Yegge claims to have never read the source code himself.

**Primary sources:**
- Blog post: [Welcome to Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- Follow-up: [The Future of Coding Agents](https://steve-yegge.medium.com/the-future-of-coding-agents-e9451a84207c)
- Follow-up: [Welcome to the Wasteland: A Thousand Gas Towns](https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f)
- Code: [GitHub - steveyegge/gastown](https://github.com/steveyegge/gastown)

---

## The Eight-Stage Developer Evolution Model

Yegge frames AI adoption as an 8-stage progression:

| Stage | Description |
|-------|-------------|
| 1 | Near-zero AI (completions, occasional chat) |
| 2 | IDE coding agent with permissions required |
| 3 | IDE agent, YOLO mode (permissions disabled) |
| 4 | IDE agent with widening scope; diffs become primary artifact |
| 5 | CLI single agent, YOLO |
| 6 | CLI multi-agent (3-5 parallel instances) |
| 7 | 10+ hand-managed agents (hitting management limits) |
| 8 | Building your own orchestrator (the frontier) |

Gas Town targets developers at Stage 7-8. Yegge explicitly warns against adoption below Stage 6.

---

## Core Architecture: The Seven Roles

Gas Town organizes agents into a hierarchical system with specialized functional roles (not SDLC personas):

### Town-Level (cross-project)
- **The Mayor** -- Primary concierge/chief-of-staff. Your single interface for initiating work. Coordinates across all projects ("rigs").
- **The Deacon** -- "Daemon beacon" patrol agent. Receives heartbeat signals every few minutes from the system daemon and propagates them downward. Manages agent recycling and town-level plugins.
- **The Dogs** -- Deacon's personal maintenance crew. Handle branch cleanup, infrastructure work. Includes **Boot**, a special Dog that checks the Deacon's health every 5 minutes (the watchdog's watchdog).

### Rig-Level (per-project)
- **Polecats** -- Ephemeral worker agents that spin up on demand in swarms. Execute discrete tasks and produce merge requests. Names are recycled after decommissioning. The factory floor workers.
- **The Refinery** -- Manages the merge queue. Processes merge requests one at a time using Bors-style bisecting queue logic. Rebases and merges to main without losing work. Escalates when necessary.
- **The Witness** -- Patrols agent health (especially polecats and refineries). Detects stuck agents, triggers recovery, runs rig-level plugins.
- **The Crew** -- Persistent, named coding agents with long-lived identities. Managed directly by you for design work and back-and-forth iteration. Accessible via tmux.

**You are "The Overseer"** -- with persistent identity in Beads, personal inbox, and town mail access.

---

## The MEOW Stack (Molecular Expression of Work)

Gas Town's foundational abstraction layer for work:

1. **Beads** -- Atomic work units. Lightweight JSON entries stored in Git. Each has an ID (prefix + 5-char alphanumeric, e.g., `gt-abc12`), description, status, and assignee. This is the external memory system that survives agent crashes.

2. **Epics** -- Hierarchical beads with parent-child relationships and sequential dependencies.

3. **Molecules** -- Workflow chains through beads with arbitrary shapes, loops, and gates. More flexible than epics.

4. **Protomolecules** -- Templates/classes of workflow beads ready for instantiation through variable substitution.

5. **Formulas** -- TOML-based source descriptions that are "cooked" into protomolecules, then instantiated.

6. **Wisps** -- Ephemeral beads that exist in-database but not in Git. "Burned" (destroyed) after runs, optionally leaving squashed summaries. Critical for high-velocity orchestration.

7. **Guzzoline** -- The collective term for all molecularized work available in the system.

---

## Key Architectural Principles

### GUPP (Gas Town Universal Propulsion Principle)
> "If there is work on your hook, YOU MUST RUN IT."

This is the fundamental scheduling rule. Agents must check their queues, resume molecules, and continue work. This simple invariant drives the entire system forward.

### Nondeterministic Idempotence (NDI)
The most novel concept. Unlike Temporal's deterministic replay, Gas Town accepts chaotic, unpredictable agent behavior but guarantees outcome convergence:

- All work is expressed as persistent molecules (bead chains in Git)
- Each step has explicit acceptance criteria
- If an agent crashes mid-molecule, the next session picks up where it left off
- The path is nondeterministic (agents may hallucinate, crash, take detours) but the outcome converges because the workflow definition is persistent and acceptance criteria are explicit
- Agents self-correct using molecule specifications

> "Work in Gas Town can be chaotic and sloppy... Some bugs get fixed 2 or 3 times, and someone has to pick the winner. Other fixes get lost... you are churning forward relentlessly."

### Seancing
Agents can resurrect predecessor sessions using Claude Code's `/resume` feature. The `gt seance` command spins up a previous session as a subprocess so the new agent can ask it questions about unfinished work. This preserves context across ephemeral sessions.

### Convoys
Work-order bundles that wrap multiple beads into trackable delivery units. Multiple swarms can attack a single convoy. Convoys labeled "mountain" receive autonomous stall detection and smart skip logic for epic-scale execution.

---

## The Merge Problem

This is Gas Town's hardest engineering challenge. When multiple polecats swarm simultaneously:
- Workers diverge from a shared baseline
- Later workers face incompatible changes when merging
- Cascading rebases can destroy work

**Gas Town's solution -- The Refinery:**
- Processes the merge queue sequentially
- Rebases/merges one change at a time to main
- Uses Bors-style bisecting queue logic
- Failed merge requests are isolated, either fixed inline or re-dispatched
- Escalates via `gt escalate` with severity levels (CRITICAL/P0, HIGH/P1, MEDIUM/P2)

**Yegge's practical advice (from "Six New Tips"):**
> Tip 6: "Swarm Carefully; Beware the Merge Wall" -- serialize merges with careful rebasing, accept periodic pauses in parallelism, prepare for "arbitrarily complicated" conflict resolution.

---

## Three-Tier Watchdog Chain

1. **Boot** (Go daemon) -- System-level process that sends heartbeat signals every few minutes
2. **Deacon** (AI agent) -- Receives signals from Boot, propagates downward, manages town-level health
3. **Witness** (AI agent) -- Per-rig health monitor for polecats and refineries

Each layer monitors the one below it. Boot specifically checks the Deacon's health every 5 minutes.

### Patrol Loops
Three main patrol agents run looped workflows:
- **Refinery Patrol** -- Cleans workspace, processes merge queue, post-flight steps
- **Witness Patrol** -- Monitors polecat/refinery health, checks Deacon, runs rig plugins
- **Deacon Patrol** -- Runs town plugins, manages session recycling, coordinates heartbeats

Patrols use exponential backoff when finding no work, awakening when mutating commands run.

---

## Comparison to Other Orchestration Patterns

### vs. Kubernetes
Both coordinate unreliable workers with a control plane monitoring execution nodes, reconciling against a persistent source of truth. **Key difference:**
> "Kubernetes asks 'Is it running?' Gas Town asks, 'Is it done?'"

K8s maintains continuous desired state (availability); Gas Town progresses toward terminal goals (task completion). K8s pods are anonymous; Gas Town polecats are credited.

### vs. BMAD/SpecKit Conductor Pattern (SDLC Simulation)
The "two kinds of multi-agent" analysis from [paddo.dev](https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/) draws a sharp distinction:

| BMAD/Conductor Pattern | Gas Town |
|------------------------|----------|
| Recreates org hierarchy with SDLC personas (Analyst, PM, Architect, Dev, QA) | Assigns functional operational roles (Mayor, Polecat, Witness, Refinery) |
| Sequential handoffs between phases | Parallel execution across isolated environments |
| LLM-judged phase gates as quality checkpoints | Git-backed state management (GUPP) as quality mechanism |
| Context windows bloated with role prompts | External state in Beads keeps context lean |
| Optimizes for explainability | Optimizes for throughput |

### vs. Temporal
Gas Town scales horizontally via replication rather than vertical task complexity. Uses nondeterministic idempotence instead of deterministic replay. Mirrors Git's repo-based distribution model.

### vs. Erlang Supervisor Trees
Steve Klabnik [notes](https://steveklabnik.com/writing/how-to-think-about-gas-town/) that Gas Town draws from proven Erlang patterns including supervisor trees and mailboxes. The watchdog chain (Boot > Deacon > Witness > Polecats) is structurally a supervisor tree.

---

## Reliability and Quality: What Works and What Does Not

### Yegge's Explicit Position on Quality

From "Six New Tips," Tip 3:
> "Spend 40% of Time on Code Health or Risk 60%+ Later" -- Regular AI-driven code inspections are non-negotiable. Have agents identify code smells, large files needing refactoring, redundant systems, and dead code. "You gradually (but rapidly) accumulate invisible technical debt" without this discipline.

From "Six New Tips," Tip 5 (The Rule of Five):
> Review 4-5 times before trusting output. "It definitely feels weird to ask for the 3rd code review" but this produces work approaching reliable quality.

From "The Future of Coding Agents":
> "Programming has always been a best-effort, we'll-fix-shit-later endeavor." The relevant metrics are customer satisfaction and defect velocity, not pristine codebases. Gas Town accepts shipping with bugs provided feedback loops remain tight.

### Documented Failure Modes (from real-world usage)

The [DoltHub "A Day in Gas Town"](https://www.dolthub.com/blog/2026-01-15-a-day-in-gas-town/) report is the most honest practical assessment:
- Cost: ~$100/hour in Claude tokens (10x normal Claude Code usage)
- Gas Town autonomously merged a PR "despite the integration tests failing" -- required force-reset of the repository
- The Mayor reported all bugs were fixed when only two PRs existed
- Final verdict: "None of the PRs were good, and I ended up closing them all"
- Cognitive overload: "everything is moving so fast in Gas Town that you really just have to let go"

From [Maggie Appleton's analysis](https://maggieappleton.com/gastown):
- Auto-merged failing tests corrupting main branches
- "Unpredictable agent behavior" (the "murderous rampaging Deacon")
- $2,000-5,000 monthly API costs partly because work frequently gets lost and bugs require fixing multiple times
- Requires "constant steering" rather than autonomous operation
- Positioned as "design fiction rather than production-ready tooling"

### Yegge's Own Acknowledgment
> "I've never seen the code, and I never care to... 100% vibe coded"
> "Do not use Gas Town if you care about money."

---

## The Wasteland: Federation and Distributed Trust

The Wasteland extends Gas Town to federated coordination across multiple independent instances, using Dolt (SQL database with Git semantics) as the substrate.

**Key mechanisms:**
- **Multi-dimensional stamps** -- Quality assessed through multifaceted attestations measuring "quality, reliability, creativity, each scored independently" with confidence levels and severity ratings
- **Trust ladder** -- Level 1 (browse/claim/submit), Level 2 (contributor), Level 3 (maintainer/validator)
- **Fraud prevention** -- Collusion detection via topology analysis: "collusion rings have a distinctive topology -- lots of mutual stamping, sharp boundaries, no outside critics"
- **Yearbook principle** -- Agents cannot stamp their own completions; requires external attestation
- Every rig rolls up to a human participant, preserving accountability

---

## Application to SDLC Hardening Phase

Based on this research, here is how Gas Town's concepts could inform a hardening phase in a multi-agent SDLC system:

### Directly Applicable Patterns

1. **Nondeterministic Idempotence** -- Accept that hardening agents will take different paths but converge on the same outcome (passing acceptance criteria). Define explicit acceptance criteria for each hardening task (test coverage thresholds, lint cleanliness, security scan results). If an agent crashes mid-hardening, the next one picks up from the persistent state.

2. **The Refinery pattern for merge safety** -- Any hardening system with parallel agents needs a sequential merge queue. Auto-merging without test validation is Gas Town's most dangerous documented failure mode. The Refinery's Bors-style bisecting approach (merge one at a time, verify, continue) is essential.

3. **The Witness/patrol pattern for quality monitoring** -- A dedicated agent whose sole job is monitoring other agents' work quality, detecting stuck processes, and escalating. Not a worker, but a supervisor.

4. **The Rule of Five** -- Multi-pass review before trusting agent output. This maps directly to a hardening phase: first pass (lint/format), second pass (tests), third pass (security), fourth pass (architectural review), fifth pass (integration verification).

5. **40% code health allocation** -- Yegge's explicit recommendation that 40% of agent time should go to code health inspections, refactoring, and debt reduction. This is essentially a built-in hardening budget.

6. **Beads as external memory** -- Tracking hardening status outside agent context windows prevents lost work and enables crash recovery. Git-backed state means hardening progress survives agent restarts.

7. **Escalation with severity routing** -- CRITICAL/HIGH/MEDIUM severity levels for issues that hardening agents cannot resolve autonomously, with clear escalation paths to human oversight.

### Patterns to Avoid

1. **Full autonomy for merging** -- The DoltHub experience shows that letting agents merge without human-verified gates is dangerous. A hardening system should require explicit approval gates.

2. **"Never reading the code"** -- Vibecoding philosophy is incompatible with reliability engineering. A hardening phase exists precisely to verify what was produced.

3. **Cost insensitivity** -- At $100/hour for questionable output quality, the economics only work if the hardening phase is focused and bounded, not open-ended.

### The Colony Thesis
Yegge's most strategic insight: "Colonies are going to win. Factories are going to win." Individual agent improvement matters, but orchestrated systems fundamentally outcompete isolated implementations. A hardening phase with multiple specialized agents (lint agent, test agent, security agent, review agent) coordinated through shared state is more robust than a single agent trying to do everything.

---

## Key Quotes Summary

- "If there is work on your hook, YOU MUST RUN IT." (GUPP)
- "Kubernetes asks 'Is it running?' Gas Town asks, 'Is it done?'"
- "Colonies are going to win. Factories are going to win."
- "Spend 40% of time on code health or risk 60%+ later."
- "Programming has always been a best-effort, we'll-fix-shit-later endeavor."
- "You gradually (but rapidly) accumulate invisible technical debt."
- "Everything you do has to be 100% transparent and announced, all the time."
- "Collusion rings have a distinctive topology -- lots of mutual stamping, sharp boundaries, no outside critics."

---

## Sources

- [Welcome to Gas Town (Yegge's launch post)](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- [The Future of Coding Agents (Yegge follow-up)](https://steve-yegge.medium.com/the-future-of-coding-agents-e9451a84207c)
- [Welcome to the Wasteland: A Thousand Gas Towns (federation)](https://steve-yegge.medium.com/welcome-to-the-wasteland-a-thousand-gas-towns-a5eb9bc8dc1f)
- [Software Survival 3.0 (Yegge)](https://steve-yegge.medium.com/software-survival-3-0-97a2a6255f7b)
- [Six New Tips for Better Coding With Agents (Yegge)](https://steve-yegge.medium.com/six-new-tips-for-better-coding-with-agents-d4e9c86e42a9)
- [GitHub - steveyegge/gastown](https://github.com/steveyegge/gastown)
- [GitHub - steveyegge/beads](https://github.com/steveyegge/beads)
- [GasTown and the Two Kinds of Multi-Agent (paddo.dev)](https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/)
- [Gas Town: What Kubernetes for AI Coding Agents Actually Looks Like (Cloud Native Now)](https://cloudnativenow.com/features/gas-town-what-kubernetes-for-ai-coding-agents-actually-looks-like/)
- [A Day in Gas Town (DoltHub)](https://www.dolthub.com/blog/2026-01-15-a-day-in-gas-town/)
- [Gas Town's Agent Patterns, Design Bottlenecks, and Vibecoding at Scale (Maggie Appleton)](https://maggieappleton.com/gastown)
- [Gas Town Decoded (Andrew Lilley Brinker)](https://www.alilleybrinker.com/mini/gas-town-decoded/)
- [How to Think About Gas Town (Steve Klabnik)](https://steveklabnik.com/writing/how-to-think-about-gas-town/)
- [Gas Town, Beads, and Agentic Development (Software Engineering Daily)](https://softwareengineeringdaily.com/2026/02/12/gas-town-beads-and-the-rise-of-agentic-development-with-steve-yegge/)
- [What Is Gastown? (TWiT.TV)](https://twit.tv/posts/tech/what-gastown-how-steve-yegges-ai-coding-agents-are-changing-software-development)
- [What I Learned from Gas Town (DEV Community)](https://dev.to/kiwibreaksme/what-i-learned-from-steve-yegges-gas-town-and-a-small-tool-for-solo-developers-2me2)