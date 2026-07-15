# Claude Command Hierarchy and Role-Based Delegation

**Date:** 2026-07-15

**Status:** Approved for written specification and red-first TDD planning; implementation and configuration activation are not authorized

**Primary scope:** Claude Code user/project hierarchy and the SDLC-OS doctrine that consumes it

**Canonical protocol dependency:** `/Users/q/LAB/agent-runtime-protocol` (ARC)

**Design worktree:** `/Users/q/LAB/.worktrees/claude-command-hierarchy-spec`

**Source branch:** `docs/claude-command-hierarchy-spec` at baseline `1c3285a`

---

## 1. Authority and Normative Language

`MUST` and `MUST NOT` are mandatory. `SHOULD` and `SHOULD NOT` define the default; deviations require a recorded rationale and proportionate validation. `MAY` is optional.

The owner has approved this specification and its red-first implementation plan only. This document does not authorize mutation of `/Users/q/.claude`, `/Users/q/LAB/agent-runtime-protocol`, installed plugins, active sessions, settings, hooks, agent definitions, or model routing. Later implementation requires a current owner grant naming the target repository or configuration surface. Activation of blocking hooks, model fallback changes, or global routing rules requires a separate grant after shadow and canary evidence.

Higher-priority platform, owner, machine, repository, and project-local instructions remain authoritative. Tool availability does not grant mutation authority. Delegation cannot expand authority. A model substitution cannot transfer or expand authority. A worker report is candidate evidence, not a final decision.

For Claude Code orchestration, this specification explicitly supersedes the one-level specialist-delegation allowance and requirements `LD-01`, `LD-02`, and `MI-E05` in `2026-07-14-sdlc-os-production-control-plane-design.md`. Those clauses are satisfied by the flat lead-owned work graph for ordinary runs. Their nested Tera/Luna path is replaced by the exceptional, separately fenced main-session coordinator in Section 5.2. Other production-control-plane constraints remain in force unless this specification names a narrower conflict.

## 2. Objective

Create one model-neutral command hierarchy in which:

- Fable is the preferred implementation of the `lead-conductor` role;
- Claude Opus 4.8 can perform the identical lead role when selected manually or resolved through configured availability fallback;
- only the active lead normally delegates and owns the integration decision;
- every worker is a non-delegating leaf with an explicit role, capability surface, target, effect boundary, and proof contract;
- SDLC-OS supplies doctrine and assurance, while one separately selected dispatch backend performs execution;
- ARC remains the canonical cross-runtime record and evidence vocabulary;
- model, authority, target, dispatch backend, definition source, wire transport, and evidence state are observed and recorded independently;
- useful reasoning is governed through scope and proof obligations rather than crude routine turn or token caps.

The design optimizes verified value per dispatch, not worker count. It parallelizes independent uncertainty, disjoint implementation, and genuinely independent verification. It does not parallelize tightly coupled stages or duplicate a quiet worker without a terminal failure or expired lease.

## 3. Explicit Non-Goals

This design does not:

- mutate live Claude Code configuration under the current approval;
- introduce a second local copy of ARC schemas;
- make SDLC-OS an execution transport;
- make Fable or Opus a role name or source of authority;
- treat `fallbackModel` as a durable session handoff;
- permit ordinary nested coordinators to dispatch;
- trust ignored plugin-agent frontmatter as a security boundary;
- infer a worker's model, effort, permissions, context, or tools from its name;
- disclose or encode hidden model reasoning instructions;
- set routine `maxTurns`, token budgets, or thinking limits as the primary control system;
- treat consensus, narrative confidence, a zero exit code, or a worker's “done” statement as mission completion;
- activate teams, workflows, native subagents, and tmup concurrently for the same task generation without a receipted transition;
- claim automatic outage failover is proven before a controlled canary observes it.

## 4. Evidence Classes and Baseline

The specification uses these evidence labels:

- `OBSERVED`: directly inspected in the installed runtime, source, settings, catalog, or command output;
- `DOCUMENTED`: supported by current official Claude Code documentation;
- `INFERRED`: a design conclusion derived from observed and documented facts;
- `UNKNOWN`: not established by admissible evidence and not silently guessed.

### 4.1 Observed local baseline

| ID | State | Observation | Consequence |
|---|---|---|---|
| `E-LOCAL-01` | `OBSERVED` | Claude Code `2.1.210` is installed on maclab. | Canary results are version-scoped. |
| `E-LOCAL-02` | `OBSERVED` | The live catalog contains `claude-fable-5` and permits `claude-opus-4-8` as a fallback candidate. | The preferred and alternate lead models exist locally, subject to per-run resolution receipts. |
| `E-LOCAL-03` | `OBSERVED` | Global settings request Fable and currently list Opus 4.8, Opus 4.7, and Sonnet 4.6 fallbacks. | The written design does not ratify the unverified extra fallbacks. |
| `E-LOCAL-04` | `OBSERVED` | `CLAUDE_CODE_SUBAGENT_MODEL` is not currently set. | A later preflight must continue to detect unexpected global overrides. |
| `E-LOCAL-05` | `OBSERVED` | The current global default permission mode is `bypassPermissions`, teams are enabled, and `Task` is allowed. | Existing broad authority must not be mistaken for the target role boundary. |
| `E-LOCAL-06` | `OBSERVED` | No user-scoped definitions exist in `/Users/q/.claude/agents`. | Neutral role definitions are a future implementation artifact. |
| `E-LOCAL-07` | `OBSERVED` | Native delegation, agent teams, SDLC-OS, tmup, and Superpowers guidance overlap without one machine-global selector. | Doctrine and transport selection must be separated and recorded. |
| `E-LOCAL-08` | `OBSERVED` | SDLC-OS contains 46 plugin agents; 40 omit `tools`; several names encode model families; multiple roles recursively dispatch. | The plugin currently violates the proposed flat authority graph. |
| `E-LOCAL-09` | `OBSERVED` | The existing SDLC `SubagentStop` validator is role-specific and advisory rather than a canonical typed result gate. | Result admission must move to one settings-level consumer adapter. |
| `E-LOCAL-10` | `OBSERVED` | `worktree.baseRef` is not configured globally. | A later implementation must explicitly choose `head` and still account for dirty state. |
| `E-LOCAL-11` | `OBSERVED` | ARC already owns envelope, work-packet, worker-result, session, run, fallback, capability, and verification schemas. | SDLC-OS and Claude settings must consume or extend ARC, never fork its vocabulary. |
| `E-LOCAL-12` | `OBSERVED` | The ARC worktree is dirty with owner changes. | This design performs no ARC mutation; future work requires separate isolation and approval. |
| `E-LOCAL-13` | `OBSERVED` | A sanitized transcript projection exposes `message.model`; captured Agent completion output on the installed release exposes `resolvedModel`. | Turn and dispatch model identity can be observed for this release, while fallback reason may remain unknown. |
| `E-LOCAL-14` | `OBSERVED` | Claude Code 2.1.210 Agent completion output includes release-scoped `agentId`, `resolvedModel`, status, and usage fields. | The canary may record those fields for this release, but missing fields remain `UNKNOWN` and are not treated as a stable cross-release contract. |

### 4.2 Official behavior used by the design

| ID | State | Documented behavior | Design consequence |
|---|---|---|---|
| `E-DOC-01` | `DOCUMENTED` | Omitting `tools` lets a subagent inherit all available tools, including MCP tools. | Every managed role needs an explicit allowlist. |
| `E-DOC-02` | `DOCUMENTED` | Omitting `Agent` prevents delegation, and a main session launched with `--agent` can restrict its top-level `Agent(type, ...)` allowlist. | Only the lead definition includes ordinary delegation capability; every leaf omits `Agent` and legacy `Task`. |
| `E-DOC-04` | `DOCUMENTED` | Plugin-provided agents ignore `permissionMode`, agent-local `hooks`, and agent-local `mcpServers`. | Those controls must live in user/project/managed settings or a separate main session. |
| `E-DOC-05` | `DOCUMENTED` | `SubagentStart` may inject context but cannot block creation. `SubagentStop` can inspect the last assistant message and return corrective feedback. | Admission occurs before spawn through a settings-level tool hook; output shape is checked at stop. |
| `E-DOC-06` | `DOCUMENTED` | Structured main-session result output can report model usage, while hook schemas distinguish successful and failed tool completion events. | Main-session model proof uses documented result output; Agent-specific fields remain release-scoped observations and failure reconciliation needs `PostToolUseFailure`. |
| `E-DOC-07` | `DOCUMENTED` | `fallbackModel` handles primary overload or unavailability for the remainder of a turn and displays a notice. | It is turn substitution, not authority transfer or durable conductor replacement. |
| `E-DOC-07A` | `DOCUMENTED` | A Fable safety-classifier fallback re-runs the flagged request on the provider's default Opus model and leaves the session on that model until explicitly changed. | Classifier fallback is distinct from the turn-scoped availability chain and still does not transfer authority. |
| `E-DOC-08` | `DOCUMENTED` | `worktree.baseRef` defaults to `fresh`; `head` starts at local `HEAD` but excludes uncommitted changes. | Every writer packet pins expected commit and dirty-state policy. |
| `E-DOC-09` | `DOCUMENTED` | Agent teams share lead permissions at spawn, cannot create nested teams, have task-state and resume limitations, and add coordination cost. | Teams are an exceptional peer-communication transport, not the default hierarchy. |
| `E-DOC-10` | `DOCUMENTED` | Dynamic workflow workers run in `acceptEdits`, inherit the session tool allowlist, accept no ordinary mid-run input, and do not resume after exiting Claude Code. | Workflows are limited to homogeneous, pre-authorized batches. |
| `E-DOC-11` | `DOCUMENTED` | Persistent subagent memory enables read/write/edit access to the memory directory. | Strictly read-only roles have no persistent memory. |

Official references: [model configuration](https://code.claude.com/docs/en/model-config), [settings](https://code.claude.com/docs/en/settings), [subagents](https://code.claude.com/docs/en/sub-agents), [agent teams](https://code.claude.com/docs/en/agent-teams), [dynamic workflows](https://code.claude.com/docs/en/workflows), and [hooks](https://code.claude.com/docs/en/hooks).

### 4.3 Unknowns preserved by the design

- Automatic Fable-to-Opus outage fallback in this exact host, account, release, and session surface is `UNKNOWN` until a controlled canary observes the transition.
- A model notice alone does not prove the reason for resolution unless a supported receipt or event identifies the cause.
- Worker runtime model, permission profile, context, and tool surface remain `UNKNOWN` until their requested and observed values are recorded separately.
- Plugin worktree isolation and effective permissions remain release-specific until canaries verify their actual base, path, and write behavior.
- Nested `Agent` availability, maximum depth, and child-type filtering on the installed release remain `UNKNOWN` because public/runtime surfaces have varied. The canary inspects the effective child catalog before attempting a nested call; the policy remains `lead_only` either way.
- Read-only and workspace-write constrain writes; they do not prove confidentiality or read isolation.

## 5. Authority Graph

The ordinary topology is deliberately flat:

```text
Human / Mission Owner
        |
        v
Active Lead Conductor
Fable preferred; Opus 4.8 eligible
        |
        +---- Domain Planner / Coordinator
        |       no delegation, no mutation
        |
        +---- Investigator(s)
        |       read-only, bounded evidence
        |
        +---- Implementer(s)
        |       isolated, non-overlapping mutations
        |
        +---- Evidence Verifier(s)
        |       independent checks, no fixes
        |
        +---- Independent Reviewer
        |       adversarial review, no fixes
        |
        `---- Arbiter
                only a preregistered closed contradiction
```

### 5.1 Authority invariants

1. There is exactly one active lead generation for a task generation.
2. Only that lead normally invokes `Agent`, a transitional legacy `Task`, or another backend's dispatch primitive.
3. Every ordinary child is a leaf and receives no `Agent` or legacy `Task` tool.
4. A domain planner proposes a dependency graph and worker packets; the lead decides whether to dispatch them.
5. A worker cannot publish, promote, merge, expand scope, accept residual risk, or make the final mission claim.
6. The lead owns decomposition, permission decisions, deduplication, integration judgment, proof discharge, and final claims inside current owner authority. The baseline definition cannot execute the integration effect.
7. The human retains undelegated risk acceptance, irreversible authority, and any scope expansion.
8. A task has one owner and dedupe key. Every admissible dispatch has a successful pre-invocation generation-fence receipt; a prose manifest or post-launch log is not sufficient. If native hook failure permits an unreceipted invocation, that work is quarantined and cannot be integrated. A quiet worker is not intentionally duplicated without a terminal failure or expired lease.
9. Worker output remains advisory until the lead validates the decisive source, diff, test, log, or runtime receipt.

### 5.2 Exceptional delegating coordinator

A coordinator that genuinely needs to delegate MUST run as a separate main session or process, never as an ordinary nested plugin subagent. It requires:

- a new run identity and authority generation;
- a self-contained delegated scope;
- a mechanically restricted worker catalog;
- no merge, publication, or final-decision authority;
- a parent continuation contract;
- leases and dedupe records;
- an external watchdog for any bare process lane;
- a completion receipt returned to the lead.

tmup or another durable external DAG may provide this transport after a separately approved adapter and canary exist. The present implementation plan keeps that route disabled. The parent lead remains integration-decision authority. This is an exception with its own manifest, not a loophole that restores recursive plugin delegation.

## 6. Model-Neutral Lead and Resolution Semantics

The role is `lead-conductor`. Role policy, capability, authority generation, proof obligations, output contract, and transport rules are invariant across model selection.

### 6.1 Three distinct mechanisms

| Mechanism | Meaning | Required record | Authority effect |
|---|---|---|---|
| Manual model selection | The operator starts or changes the active session to an eligible model. | Requested, configured, and observed turn model. | None. Existing authority still requires validation. |
| Configured fallback | Claude Code resolves another model for a turn because the primary is unavailable or overloaded. | Requested primary, fallback chain, observed turn/dispatch model, reason if observed. | None. This is not a new lead generation. |
| Fable classifier fallback | A Fable safety classifier re-runs a flagged request on the provider's default Opus model and the session continues on that model until explicitly changed. | Prior model, observed resolved model, classifier notice/event if admissible, and continuing session identity. | None. Lead ID and authority generation remain unchanged. |
| Conductor replacement | A new session/process assumes coordination after the prior conductor becomes unavailable or is deliberately replaced. | Authority-handoff record, new generation, reconciled workers and proof debt. | New generation only after explicit revalidation. |

### 6.2 Turn and dispatch receipt

The canonical record MUST preserve requested and observed fields separately:

```yaml
lead_role: lead-conductor
lead_generation: 7
model:
  requested: fable
  configured_primary: fable
  configured_fallbacks:
    - claude-opus-4-8
  resolved_for_turn: claude-opus-4-8
  resolution_reason: primary_unavailable
  observation_state: observed
```

`resolution_reason` is `unknown` unless an admissible runtime signal supplies it. The design MUST NOT infer availability fallback or classifier fallback from a model-name mismatch alone. Authentication, billing, rate-limit, request-size, and transport errors are negative controls because official Claude Code behavior says they do not trigger the availability fallback chain.

For worker dispatch, the settings adapter records the requested `Agent.model` separately from release-scoped `PostToolUse` `resolvedModel` when present; absence remains `UNKNOWN`. For the lead turn, documented structured-result `modelUsage` is the primary receipt, while a sanitized transcript projection MAY supplement it with `message.model`. Neither path copies prompts, hidden reasoning, credentials, or full transcript content into receipts.

### 6.3 Model routing policy

- Preferred lead: Fable, after live catalog match and a Fable-led canary.
- Eligible alternate lead: Claude Opus 4.8, after live catalog match and an Opus-led parity canary.
- Routine worker selection is capability-first and recorded per dispatch.
- Verifier diversity MAY use a different model, but cross-model diversity is not evidence independence by itself.
- `CLAUDE_CODE_SUBAGENT_MODEL` MUST be absent in this hierarchy. Its presence produces a preflight refusal because it can silently flatten role-specific routing. A future experiment that needs a global override must use a different, explicitly named profile outside this contract.
- Static model-coded agent names are compatibility aliases only during migration and MUST NOT be interpreted as selector receipts.
- No cost, latency, token, or capability claim may be made from a role label or model heuristic without matched canary evidence.

### 6.4 Actual lead replacement

A replacement record contains at least:

```yaml
handoff:
  from_lead_generation: 7
  to_lead_generation: 8
  reason: primary_session_unavailable
  inherited_authority: false
  authority_revalidated: true
  task_generation_revalidated: true
  continuation_handle: sha256:...
  unresolved_proof_obligations:
    - verify_runtime_model
    - reconcile_running_workers
```

The new conductor MUST atomically fence the prior generation, increment the generation through compare-and-swap, verify the content digest of its continuation packet, and then verify owner authority, task generation, repository generation, active worker leases, partial effects, outstanding proof obligations, transport ownership, and dedupe reservations before dispatch or finalization. Until then its state is `RECONCILING`, not `ACTIVE`. If the old generation cannot be fenced or terminally observed, the new generation cannot integrate results.

## 7. Doctrine and Transport

SDLC-OS is a doctrine: it defines roles, quality obligations, evidence rules, and escalation semantics. It is not another dispatch backend alongside native subagents, teams, workflows, or tmup.

```yaml
orchestration:
  doctrine: sdlc-os
  dispatch_backend: native_subagents
  definition_source: plugin_and_user_agents
  envelope_protocol: arc
  coordination_backend: none
  wire_transport: in_process_agent_tool
```

or:

```yaml
orchestration:
  doctrine: sdlc-os
  dispatch_backend: external_dag
  definition_source: tmup_catalog
  envelope_protocol: arc
  coordination_backend: tmup
  wire_transport: mcp
```

### 7.1 Run-scoped invariant

```text
one task generation
one active owner
one primary dispatch backend
one doctrine
one dedupe key
one integration-decision authority
```

A dispatch-backend change creates a new task or run generation and a receipted handoff. The old backend stops admitting work, is terminally observed or fenced, reports all running or partial workers, and releases or transfers dedupe leases before the new backend starts. The transition is committed by compare-and-swap against the old generation. A task MUST NOT silently run through native subagents and tmup at the same time.

`dispatch_backend`, `definition_source`, `envelope_protocol`, `coordination_backend`, and `wire_transport` are separate fields. The word “transport” MUST NOT ambiguously stand for all five.

### 7.2 Transport selection

| Dispatch backend | Select when | Reject when |
|---|---|---|
| Single lead | Work is sequential, tightly coupled, or one targeted read is cheaper than dispatch. | Independent exploration, output isolation, or separate verification materially improves confidence. |
| Native subagents | Leaves are bounded, returns are compact, and the lead can fan out and fan in. | Workers require sustained peer negotiation or different enforced process boundaries. |
| Agent teams | A small number of peers require direct, long-running communication. | Roles need distinct permission envelopes, durable resume, nested teams, or compact bounded returns. |
| Dynamic workflows | A stable, repeatable, homogeneous batch can be encoded and fully pre-authorized. | Human stage approval, heterogeneous permission modes, or adaptive high-level judgment is needed mid-run. |
| tmup / external DAG | Work needs durable leases, cross-runtime lanes, warm contexts, retries, or a separate main-session coordinator. | A simple native leaf dispatch is sufficient. |

Dispatch-backend selection is a lead judgment recorded before dispatch. SDLC skills may recommend a backend but cannot activate a second control plane.

## 8. Role Capability Matrix

| Role | Delegates | Target writes | Worktree | Persistent memory | Final claims |
|---|---:|---:|---:|---:|---:|
| Lead conductor | Yes | No in the baseline definition; a separately approved launch-specific definition must list every direct-effect tool | Optional | Curated only | Yes, for integration decisions and final claims |
| Domain planner | No | No | No | No | Domain synthesis only |
| Investigator | No | No | No | No | No |
| Implementer | No | Scoped | Required by default | No | No |
| Evidence verifier | No | No target writes | Prefer clean checkout/worktree | No | No |
| Independent reviewer | No | No | Prefer clean checkout/worktree | No | No |
| Arbiter | No | No | No | No | Closed verdict only |

### 8.1 Capability dimensions

Every packet binds these independently:

```text
tool scope
filesystem scope
mutation scope
target identity
repository generation
network scope
credential scope
delegation authority
proof obligations
```

`read-only` and `workspace-write` describe write constraints, not confidentiality. A confidentiality claim requires a tested custom profile with host deny paths or external isolation; otherwise confidentiality remains `UNKNOWN`.

### 8.2 Role definitions

All managed agent definitions MUST have explicit `tools` and `disallowedTools` where useful. Ordinary leaves omit `Agent`, legacy `Task`, and `Skill` unless a named skill is explicitly required and its tool/shell surface is separately proven. A non-mutating planner omits `Agent`, `Task`, `Skill`, `Bash`, `Write`, `Edit`, persistent `memory`, and all MCP tools unless a specific read-only MCP operation and resource scope have been canaried. Plugin agent frontmatter MUST NOT claim enforcement through `permissionMode`, `hooks`, or `mcpServers`, because Claude Code ignores those fields for plugin-provided agents.

Canonical role definitions are model-neutral:

```yaml
---
name: lead-conductor
description: Owns decomposition, dispatch, integration, proof discharge, and final claims inside the current owner-authorized envelope.
tools: Read, Grep, Glob, Agent(domain-planner, investigator, implementer, evidence-verifier, independent-reviewer, evidence-arbiter)
model: inherit
---
```

The typed `Agent(...)` restriction is meaningful only when this definition runs as the main session through `claude --agent`; it is not reused as a nested coordinator. The `tools` field is an exclusive allowlist. The baseline lead is therefore non-mutating: settings and permission rules cannot restore omitted `Write`, `Edit`, `Bash`, MCP, or publication tools. It owns integration judgment and proof discharge; scoped implementers perform product mutations, and a human or separately authorized external adapter performs the final integration effect.

If a later run requires direct lead mutation, shell, MCP, or publication capability, its launcher MUST materialize a separate, content-digested main-agent definition that explicitly lists each additional tool. That definition remains under the same model-neutral `lead-conductor` authority contract but requires a named owner grant, a resolved-tool receipt, negative canaries, and a distinct capability-profile digest. This specification and plan do not implement or activate that direct-effect profile.

The future user-scoped definition lives at `~/.claude/agents/lead-conductor.md`. A controlled main session may select it with `claude --agent lead-conductor`; the CLI flag overrides the `agent` setting. Neither a stored default nor the flag proves effective capability by itself, so the launch receipt must record the resolved main-agent definition, tool surface, settings sources, model, and canary result.

```yaml
---
name: domain-planner
description: Decomposes one assigned domain into bounded candidate worker packets and reconciles returned evidence. Never delegates or mutates.
tools: Read, Grep, Glob
model: inherit
---
```

```yaml
---
name: investigator
description: Collects bounded evidence for one named question. Never writes, delegates, integrates, or makes final success claims.
tools: Read, Grep, Glob
model: sonnet
---
```

```yaml
---
name: implementer
description: Implements one bounded leaf in an isolated worktree and returns exact change and verification evidence.
tools: Read, Grep, Glob, Edit, Write, Bash
model: sonnet
isolation: worktree
---
```

```yaml
---
name: evidence-verifier
description: Independently performs static verification of named proof obligations. Never changes target files or repairs findings.
tools: Read, Grep, Glob
model: opus
---
```

```yaml
---
name: independent-reviewer
description: Adversarially reviews one immutable target generation and returns ranked findings. Never fixes, delegates, or accepts risk.
tools: Read, Grep, Glob
model: inherit
---
```

```yaml
---
name: evidence-arbiter
description: Resolves one explicitly named contradiction under closed rules. Never writes, delegates, changes scope, or accepts risk.
tools: Read, Grep, Glob
model: inherit
---
```

The concrete aliases `sonnet`, `opus`, and `inherit` in example frontmatter are routing metadata, not role identity. A live selector receipt is still required.

Raw `Bash` is not read-only, especially while a parent session uses `bypassPermissions`. Runtime verification that needs commands MUST use either:

1. a dedicated verification-command adapter whose settings-level `PreToolUse` gate accepts only a packet-referenced command and runs it in a disposable workspace; or
2. a separate process with a tested custom read-only permission profile or externally read-only source mount.

The first option may permit ephemeral cache/output writes inside the disposable workspace but MUST prove no target or external path was modified. Until a resolved-runtime canary proves one of these boundaries, command-executing verifier mutation scope is `UNKNOWN`, not read-only.

### 8.3 SDLC-OS migration map

| Current model-coded or delegating surface | Target doctrine role | Migration rule |
|---|---|---|
| `sonnet-investigator` | `investigator` | Preserve behavior behind a temporary alias; remove model claims from the canonical name. |
| `sonnet-designer` | `domain-planner` or narrowly named solution designer | No delegation or mutation. |
| `sonnet-implementer` | `implementer` | Explicit write tools, worktree contract, no delegation. |
| `sonnet-reviewer` | `independent-reviewer` | No fixes, no delegation. |
| `haiku-evidence` | `evidence-collector` | Explicit read-only tools, no persistent memory. |
| `haiku-verifier` | `evidence-verifier` | Objective verification, no repair. |
| `haiku-handoff` | `handoff-packager` | Produces a bounded delta, no authority transfer. |
| `reliability-conductor` | `reliability-planner` | Proposes packets and synthesizes; the active lead dispatches. |
| Red-team commanders | Adversarial planners/reviewers | Propose independent probes; no recursive guppies. |
| Gap analyst | Gap planner | Proposes disjoint probes; no recursive workers. |
| Arbiter variants | `evidence-arbiter` | Closed predicate only; no recursive research. |
| Cross-model supervisor | Exceptional external coordinator | Separate main process/session with a new authority generation. |

Compatibility aliases have an expiration plan and MUST NOT preserve recursive authority.

## 9. ARC as the Canonical Protocol

ARC owns cross-runtime envelope and proof vocabulary. Claude Code settings and SDLC-OS are consumers. They MUST NOT create local schemas named `arc.agent-result.v1`, `arc.orchestration-run.v1`, or equivalent unless those schemas are first canonicalized in ARC.

### 9.1 Existing canonical records

The current ARC repository already contains:

- `_envelope.schema.json`;
- `work-packet.schema.json`;
- `worker-result.schema.json`;
- `session-record.schema.json`;
- `run-record.schema.json`;
- `fallback-event.schema.json`;
- `capability-profile.schema.json`;
- `verification-record.schema.json` and associated promotion grammar.

The current Claude binding declares doctrine, verification, telemetry, and judgment responsibilities and explicitly avoids owning global doctrine, general worker dispatch, and host-global proof. That ownership boundary remains valid.

### 9.2 Required upstream ARC evolution

Before canonical Claude-native monitored records or any enforcement claim, a separately approved ARC change MUST:

1. ratify the additive protocol change as ARC `0.2.0`, update canonical pins/fixtures, and publish a migration record without deploying consumers implicitly;
2. add `claude-code` as a supported consumer/backend/lane where appropriate;
3. extend the existing `worker-result` payload compatibly with typed `status`, `effect_state`, `scope`, `claims`, `unresolved`, and `handoff` fields;
4. preserve existing required worker-result fields during migration so current consumers do not break;
5. add a canonical orchestration-run record for generation, owner, doctrine, dispatch backend, dedupe, lead, worker, proof, and join state;
6. add a canonical authority-handoff event for real conductor replacement;
7. update the Claude ARC binding to declare emitted/consumed records without transferring schema ownership;
8. add valid and invalid fixtures plus validator coverage for every new Claude-specific constraint.

Until that change lands, the Claude adapter may emit shadow records only into a clearly versioned experimental namespace. It cannot claim canonical ARC validation or promotion.

### 9.3 Consumer-local state

A Claude consumer adapter MAY keep a small non-authoritative run index mapping the active Claude session to ARC record handles, worker leases, and pending proof IDs. The index is control-state cache only. It cannot redefine record payloads, satisfy proof obligations, or become a second source of truth. Recovery rebuilds or reconciles it from canonical records and live worker receipts; ambiguity yields `INDETERMINATE`.

## 10. Work Packet and Worktree Contract

Every worker receives a self-contained packet containing:

- outcome and named question;
- inputs and bounded history;
- allowed and forbidden paths;
- exact permitted mutations;
- tool, network, and credential surface;
- repository and task generation;
- acceptance criteria and proof obligations;
- validation methods;
- timeout/watchdog and stop conditions where a separate process is used;
- dedupe key and owner;
- result schema and evidence-return contract.

A successfully executing native admission hook or future external launcher first acquires an atomic record keyed by `(task_id, generation)` that contains `dispatch_backend`, `transport_instance_id`, `dedupe_key`, `task_owner`, `doctrine_version`, and `integration_lead`. A losing native hook returns an explicit deny; if hook failure nevertheless permits an invocation, the missing fence receipt makes it unadmitted and non-integrable. A future external-process adapter must prove that losing the compare-and-swap race prevents invocation. No backend may publish or integrate under a stale or missing fencing token.

Writers additionally receive:

```yaml
workspace:
  source_repository: /path/to/repo
  expected_head: a16aa1b...
  dirty_state_policy: refuse
  worktree_base_policy: head
  owned_paths:
    - modules/component-a/**
  forbidden_paths:
    - schemas/**
    - docs/reference/authority/**
  integration_target: feature/orchestration-control
```

Before mutation, the implementer reports its actual worktree path, actual base commit, dirty-state result, and path lease. A mismatch is `REFUSED` or `INDETERMINATE`; it is never auto-corrected by rebasing or stashing owner work.

Admission records the parent `HEAD`, porcelain-v2 status bytes and digest, declared `.worktreeinclude` files, task inputs, and mutable paths. If a staged, unstaged, or untracked path intersects a task input or mutable path lease, native worktree dispatch is blocked until an owner-authorized immutable snapshot/overlay is materialized. Merely recording “dirty” does not make the worker's view equivalent to the lead's view.

Before integration, the lead checks:

- actual base ancestry matches the packet;
- no out-of-scope changes exist;
- no writer ownership overlaps;
- returned diff matches the named target;
- tests and proof handles resolve;
- integration is clean or explicitly conflicted;
- uncommitted, untracked, or unpushed state is preserved.

`isolation: worktree` does not enforce `owned_paths`. Settings-level `PreToolUse` gates for `Write`, `Edit`, and `MultiEdit` MUST resolve the subagent's active packet and reject paths outside its exclusive lease. Raw `Bash` for an implementer MUST be routed through a scoped command wrapper or externally fenced process that records pre/post repository state, refuses commands outside the packet, and quarantines unexpected changes. A post-run diff is required but is detective evidence, not a substitute for pre-execution enforcement.

## 11. Typed Worker Evidence

Workers return deltas, not transcripts:

```text
new facts
invalidated facts
contradictions
changed files
proof results
unresolved obligations
evidence handles
recommended next action
```

The future canonical ARC worker-result extension carries this semantic envelope:

```yaml
schema_version: arc.worker-result.vNext
run_id: run-...
task_id: task-...
task_generation: 3
worker_id: verifier-auth-02
role: evidence-verifier
parent: lead-conductor
dispatch_backend: native-subagent

status: completed | failed | partial | refused | indeterminate
effect_state: none | attempted | partial | committed | unknown

scope:
  requested: []
  inspected: []
  modified: []

claims:
  - claim_id: auth-regression-absent
    conclusion: pass | fail | contradicted | unknown | inconclusive
    method: pytest
    evidence_handle: sha256:...
    freshness: current_run
    coverage: named_profile
    independence: separate_worker
    limitations: []

unresolved:
  - browser_runtime_not_observed

handoff:
  recommended_next_action: inspect-evidence
  claims_requiring_lead_acceptance:
    - auth-regression-absent
```

The two axes are deliberately separate: `status` describes worker execution/lifecycle; `claims[].conclusion` describes a claim verdict; `effect_state` describes side effects. `UNKNOWN`, `CONTRADICTED`, and `INCONCLUSIVE` are claim/evidence states, never worker lifecycle states.

Narrative confidence MAY be retained for compatibility but is not a primary assurance field. The lead validates schema, identity, generation, target, evidence resolution, method execution, coverage, freshness, independence, negative controls, and stability before accepting a claim.

An `evidence_handle` is only a locator until it resolves to retained bytes or a reproducible immutable object and its content digest verifies. The record includes kind, locator, digest, producer/session, capture time, input/source snapshot, command/result status, access/redaction scope, and limitations. Mutable paths, bare URLs, transcript IDs, prose, and detached exit codes do not prove a claim. Missing resolver/readback, mutation, or digest mismatch yields `INCONCLUSIVE`.

Missing, malformed, progress-only, stale, masked, unverified, or partial output is `INCONCLUSIVE`/`INDETERMINATE`, never `PASS`.

## 12. Mechanical Enforcement Lifecycle

The target settings-level adapter owns enforcement. Plugin hooks may supply doctrine-specific observations but cannot be a competing admission or final-proof authority.

```text
lead proposes dispatch
        |
        v
PreToolUse(Agent|Task): authorize + reserve dedupe
        |
        v
Agent spawn
        |
        v
SubagentStart: inject packet handle only
        |
        v
leaf execution (no Agent/Task capability)
        |
        v
SubagentStop: validate typed result shape
        |
        v
PostToolUse(Agent|Task): record resolved model/status/agentId
        |
        v
lead validates evidence and authorizes or refuses integration
        |
        v
Stop: join and proof-debt gate
```

### 12.1 Admission gate

A settings-level `PreToolUse` matcher for `Agent|Task` MUST cover both tools during migration. The target configuration removes the legacy global `Task` allow and then retains the `Task` hook as a compatibility deny until canaries show the surface is unreachable. When it executes successfully, the gate MUST:

- deny the call if common hook input contains a subagent `agent_id`, providing defense in depth behind the leaf's static omission of `Agent`/`Task`;
- require an active run generation and lead authority;
- require an approved role and explicit work-packet handle;
- validate task generation, target generation, dispatch backend, dedupe key, and worker lease;
- reject duplicate or overlapping writer dispatch;
- record requested model separately;
- return an explicit deny on malformed, unavailable, or ambiguous control state; a missing hook remains unobserved/`UNKNOWN` rather than denied.

Every Agent call begins with compact canonical ARC orchestration-run and work-packet envelopes inside the Agent prompt:

```text
<arc-orchestration-run sha256="{64 lowercase hex}">
{canonical JSON orchestration-run envelope}
</arc-orchestration-run>
<arc-work-packet sha256="{64 lowercase hex}">
{canonical JSON work-packet envelope}
</arc-work-packet>
```

Its `description` contains `arc:{run_id}:{worker_id}:{first-16-hex-of-packet-sha256}`. The hook MUST NOT treat model-supplied owner, authority, or scope fields as authorization. The launch profile supplies a content-digested root authority manifest through a non-worker-writable path established before the model session starts. The PreToolUse hook resolves and validates that manifest, requires the inline run to match its fixed run, generation, owner, doctrine, backend, lead, and authority bounds, validates the work packet as a subset of those bounds, recomputes both inline digests, and atomically creates or matches the run/worker reservation before allowing spawn. Strict mode denies delegation when the root manifest or expected digest is missing, mutable by the worker lane, stale, or mismatched. Shadow mode records the same failure but does not claim enforcement.

This avoids adding a registry MCP inventory while keeping the worker packet self-contained. When the admission hook executes successfully, a malformed, mismatched, duplicate, stale, or authority-expanding packet is explicitly denied. The exceptional tmup coordinator is contract-only and disabled in this implementation. A later separately approved tmup adapter must consume the same ARC envelopes and compare-and-swap library, prove one invocation winner with an external counter, and avoid a second registry or MCP control surface before that backend is supported.

The dedupe/generation reservation is an atomic compare-and-swap completed before the admission hook returns allow. A post-launch log cannot provide single-primary fencing. This plan proves the native reservation path and generic compare-and-swap behavior only. Cross-backend invocation fencing remains `UNKNOWN` and tmup remains disabled until a real adapter and invocation-counter race are separately implemented.

Claude Code hook process failure, timeout, or absence is not itself a blocking decision. The permission engine also evaluates `deny` and `ask` rules regardless of a hook's allow output, so an ask-plus-`dontAsk` fallback would reject valid leased calls as well as invalid ones. The current native Agent surface therefore has no proven configuration that both admits dynamically leased calls and automatically denies them when the hook process is missing.

This implementation remains `shadow`/monitored for dynamic admission. A successfully executed hook may explicitly deny a malformed or unauthorized call. A missing, nonzero, or timed-out hook makes admission and effects `UNKNOWN`; the external launcher refuses result acceptance, integration, and publication, but it does not claim the invocation was prevented. Mutating native canaries run only in disposable worktrees with no external integration authority, and the supervisor captures/reconciles any partial effects. Promotion to mechanically fail-closed dynamic write enforcement is blocked until Claude Code exposes a suitable hook-failure policy or a separately approved external-process transport owns invocation beneath the model.

`SubagentStart` is not an admission gate and MUST NOT be described as one.

### 12.2 Leaf capability gate

Every leaf definition omits `Agent`, `Task`, and normally `Skill`. The settings-level Agent gate is defense in depth against unexpected inheritance or a definition regression. Planner/coordinator lanes also disable dynamic workflows, agent teams, and inline skill shell execution through a resolved launch/managed settings surface. Tests must prove the actual nested-subagent, `claude --agent`, teammate, workflow, interactive, print, and SDK surfaces that remain in scope; unsupported or untested surfaces remain `UNKNOWN` and disabled.

Separate `PreToolUse` matchers for file tools and Bash enforce active path leases. The Bash gate permits only a packet-referenced scoped wrapper for write-capable leaves or a verification wrapper for command-verifying leaves. Global `bypassPermissions` is not accepted as proof that these hooks or deny paths are effective; canaries must observe the resolved permission and hook behavior.

### 12.3 Result gate

A synchronous, anchored settings-level `SubagentStop` command hook validates `last_assistant_message` against the canonical result contract when the hook executes successfully. On a first correctable shape error, it returns `decision: "block"` with one bounded corrective instruction. Correction exhaustion observed by the hook quarantines the result as malformed and `INCONCLUSIVE`; the system MUST NOT create an infinite correction loop or call the worker successful.

A timeout, missing hook, nonzero hook failure, or unobserved engine behavior cannot quarantine itself. The external launcher/supervisor and final proof consumer require an expected content-digested hook receipt; its absence makes result admission and session completion `UNKNOWN`/`INCONCLUSIVE` and prevents external integration or publication. A successful worker return is not proof that the stop gate executed.

The hook validates syntax and required metadata. It does not promote claims. Only lead-side evidence admission and ARC verification records can satisfy proof obligations.

### 12.4 Model and completion receipt

`PostToolUse(Agent|Task)` records `agentId` where supplied, requested model, release-scoped observed `resolvedModel`, status, usage metadata permitted by policy, and result/evidence handles. `PostToolUseFailure(Agent|Task)` terminally reconciles failed launches and tool errors. Neither path copies the whole worker transcript. Missing `resolvedModel` remains `UNKNOWN`, and a legacy event that lacks the required receipt remains unobserved and cannot satisfy dispatch proof. Main-session model proof uses documented structured-result `modelUsage` rather than assuming the Agent response shape is stable.

Background workers remain outstanding until a terminal completion/failure event and result record are reconciled. A successfully executed final `Stop` gate refuses a success claim while required workers are running, missing, malformed, partial, rejected, or indeterminate, or while named proof obligations are unresolved. The external launcher or integration adapter also requires the final gate receipt; if the hook is missing or fails, completion remains `UNKNOWN` and no external integration/publication effect is authorized.

## 13. Arbiter Boundary

The arbiter may issue a binding verdict only for a preregistered, closed predicate. A `closed_predicate` is a deterministic function over an immutable, content-digested input snapshot with two preregistered semantic outcomes and a separate execution-status channel. Only a mechanically observed `PASS` or `FAIL` mapped before execution is binding. An LLM's prose verdict is advisory. Timeout, error, masked output, missing input, nondeterminism, or neither outcome remains `INCONCLUSIVE`/`UNKNOWN`. The arbiter may not change scope, authorize mutation, create policy, merge, publish, redefine success, or accept risk.

Valid questions include:

- did two workers inspect the same target generation;
- does receipt X satisfy proof obligation P-17;
- do two findings materially contradict;
- does the immutable input satisfy the preregistered `PASS` predicate or the preregistered `FAIL` predicate; otherwise execution status is inconclusive.

Invalid questions include:

- should we ship anyway;
- is the risk acceptable;
- should the task expand to fix a related issue;
- which product tradeoff should the organization choose.

The lead incorporates the narrow verdict into its mission decision. The human owns undelegated risk acceptance.

## 14. Evidence-State Routing

```text
PASS with sufficient proof
    -> integrate

FAIL with decisive evidence
    -> repair or stop

CONTRADICTED
    -> invoke a closed-predicate arbiter

PARTIAL
    -> continue, narrow, or preserve partial effects

UNKNOWN
    -> acquire discriminating evidence

REFUSED
    -> inspect authority or capability boundary

INDETERMINATE
    -> preserve effects and reconcile
```

“More agents” is not an escalation rule. Another worker is justified only when it can acquire different evidence, exercise a distinct capability, own a disjoint implementation leaf, or provide genuinely separate review.

## 15. Context and Efficiency Policy

The design intentionally avoids routine turn and token ceilings as its central control mechanism.

- The lead retains mission context, authority, dependency state, proof debt, and integration decisions.
- Workers receive bounded packets, not implicit full-session history.
- Domain planners return candidate task graphs rather than recursively spawning.
- Verbose search, logs, and batch evidence remain in leaf context; only typed deltas return.
- Existing workers are resumed when continuity is more valuable than independence and the target generation is unchanged.
- Fresh workers are used for independent verification, changed target generations, uncertain prior authority, or hypothesis-debiasing.
- Parallelism targets disjoint evidence or state, not volume for its own sake.
- Model routing is capability-specific. The strongest eligible model manages ambiguity, risk, contradictions, and final synthesis; bounded mechanical leaves may use other catalog-confirmed models.
- External watchdogs, leases, and stop conditions bound separate processes. Bare process commands are never promoted as safe primitives by prose alone.

Routine `maxTurns` MAY be used as a local safety valve for a demonstrably runaway path, but it is neither a role definition nor proof of completion. A cutoff result is `PARTIAL` or `INDETERMINATE` unless its acceptance criteria are independently satisfied.

### 15.1 Reconciliation of the optimization research packet

The later “Optimizing Fable Subagent Orchestration” report is accepted as research input, not as an automatic policy replacement. Its compatible recommendations are retained as measured optimization experiments:

- effort selection by task capability;
- task budgets as whole-loop cost controls where the API/runtime actually supports them;
- prompt caching and compaction for stable repeated context;
- batch execution for homogeneous offline rows;
- configuration linting and negative controls;
- minimal MCP inventories and managed trust boundaries;
- independent verification and model-resolution receipts.

Those knobs do not define authority, role, target scope, evidence sufficiency, or completion. They may be varied only after the flat hierarchy and proof contract remain fixed, so results can be compared without confounding management policy with model/runtime tuning.

The following examples from that packet are explicitly not adopted as defaults because they conflict with the ratified hierarchy or documented plugin/runtime boundaries:

- workflows as the broad default for medium/large work;
- `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, which would flatten role-specific routing;
- raw `Bash` labeled read-only;
- persistent verifier memory, which automatically expands write tools;
- plugin-agent reliance on `permissionMode`, hooks, or MCP frontmatter;
- routine `maxTurns` or task budgets as central command controls;
- auto-memory for managed leaves;
- producer-side model/config declarations treated as observed runtime proof.

The research packet's proposed `C0–C5` change and `P0–P5` provenance vocabulary is not present as a canonical versioned contract in the inspected ARC schemas. It may be proposed upstream, but this consumer specification cannot silently declare it canonical. Until ARC ratifies that vocabulary, implementation uses ARC's existing `proof_class`, `source_layer`, verification verdicts, work packets, worker results, and separately approved mutation authority.

## 16. Run Record

The future canonical ARC orchestration-run record expresses at least:

```yaml
schema_version: arc.orchestration-run.v1
run:
  id: run-20260715-001
  generation: 1
  owner: human-owner
  task_id: task-orchestration-hardening
  dedupe_key: sha256:...
  authority_contract: lead-conductor-v1
  doctrine: sdlc-os-vNext
  dispatch_backend: native-subagents
  definition_source: user-and-plugin-agents
  envelope_protocol: arc
  wire_transport: in-process-agent-tool

lead:
  role: lead-conductor
  requested_model: fable
  fallback_chain:
    - claude-opus-4-8
  may_delegate: true
  may_decide_integration: true
  may_execute_integration: false
  may_publish: within_user_authority
  may_expand_scope: false

delegation:
  max_depth_policy: lead_only
  nested_delegation: forbidden
  duplicate_dispatch: forbidden
  worker_results_are_candidate_evidence: true

proof_obligations:
  - explicit-tools-for-every-role
  - leaves-cannot-delegate
  - read-only-roles-cannot-write
  - writer-paths-do-not-overlap
  - fable-led-canary
  - opus-led-canary
  - malformed-result-is-rejected
  - model-resolution-is-observed
  - no-duplicate-dispatch-backend
  - final-claim-has-independent-proof

completion:
  join_policy: all_required_workers_terminal
  partial_worker_output: not_success
  missing_worker: unknown
  unverified_claim: unknown
```

This example is normative semantics, not permission to create a local competing schema. The ARC upstream change packet must ratify its exact canonical encoding.

## 17. Required Red-First Test and Canary Matrix

| Family | Required assertion |
|---|---|
| Agent definition lint | Every managed role has explicit tools; canonical names are model-neutral and unique. |
| Delegation authority | The lead can dispatch approved roles; every leaf's `Agent` or legacy `Task` attempt is denied. |
| Nested authority | No ordinary coordinator has `Agent`; exceptional coordinators require a separate run, generation, and restricted catalog. |
| Read-only enforcement | Investigator, verifier, reviewer, planner, and arbiter cannot write or edit target files. |
| Memory enforcement | Strictly read-only roles have no persistent memory field. |
| Plugin semantic lint | Plugin agents do not claim enforcement through ignored `permissionMode`, `hooks`, or `mcpServers`. |
| Writer isolation | Writers start in distinct worktrees at the expected base with non-overlapping owned paths. |
| Dirty-state handling | Uncommitted prerequisites cause the declared refusal/reconciliation path, not silent loss. |
| Preferred-lead parity | A Fable-led canary dispatches, verifies, makes the integration decision, and emits a requested/observed receipt without executing the integration effect. |
| Alternate-lead parity | A manually selected Opus 4.8 lead performs the identical authority graph and record protocol. |
| Automatic fallback | Safe simulation records per-turn substitution; actual outage behavior remains `UNKNOWN` until observed. |
| Environment override | Unexpected `CLAUDE_CODE_SUBAGENT_MODEL` produces a warning/refusal before dispatch. |
| Result contract | Malformed output is rejected/corrected; partial or masked output never becomes pass. |
| Background join | The lead cannot finalize while a required worker is running or indeterminate. |
| Agent failure reconciliation | `PostToolUseFailure(Agent|Task)` terminally reconciles the attempt without inventing a result or erasing effect uncertainty. |
| Duplicate dispatch | Same generation and dedupe key cannot acquire two active owners. |
| Reviewer independence | A reviewer cannot modify the implementation it evaluates. |
| Dispatch-backend isolation | A generation cannot activate multiple primary dispatch backends; a race proves one CAS winner and a receipted transition fences the predecessor. |
| Tool-surface resolution | Leaf capabilities are observed separately as nested subagent, main `--agent`, teammate, workflow, print, and SDK surfaces. |
| Bash/path boundary | Raw Bash is refused; packet wrappers and file-tool gates prevent out-of-lease target writes and detect unexpected effects. |
| Hook-failure handling | Missing, nonzero, and timed-out control hooks make the run unknown/non-integrable; canaries preserve and reconcile any effects and never claim prevention. |
| Evidence resolution | Deleted, mutated, inaccessible, or digest-mismatched evidence remains inconclusive. |
| Arbiter determinism | Only preregistered deterministic PASS/FAIL binds; timeout, error, masked, missing, and ambiguous fixtures do not. |
| Resume/handoff | A new lead revalidates authority, target, active workers, dispatch backend, and proof debt. |
| Final claim | A worker's zero exit or “done” cannot independently satisfy the mission. |
| Compatibility | Existing ARC consumers and legacy SDLC aliases continue to validate during the migration window. |

Manual preferred- and alternate-lead canaries are required before any automatic outage canary. Automatic outage failover remains `UNKNOWN` unless a safe, controlled test can trigger and observe the exact provider/runtime behavior without external side effects.

## 18. Rollout and Activation

### Stage 0 — Written artifacts only

- Ratify this specification and the implementation plan.
- Make no config, hook, plugin behavior, or ARC schema mutation.
- Preserve all observed unknowns.

### Stage 1 — ARC upstream contract, separately approved

- Isolate the dirty ARC repository in a new worktree without altering owner changes.
- Add backward-compatible schema and fixture support for Claude-native orchestration, result extensions, and lead handoff.
- Validate existing and new consumers.
- Do not activate Claude hooks.

### Stage 2 — SDLC-OS doctrine refactor, separately approved

- Add role-catalog and authority lint tests red first.
- Introduce model-neutral roles and compatibility aliases.
- remove recursive dispatch from ordinary planner/reviewer/arbiter doctrine;
- add explicit tools to every managed agent;
- preserve existing behavior behind shadow-compatible adapters until fixtures pass.

### Stage 3 — Claude consumer adapter in shadow, separately approved

- Add user/project role definitions and settings-level hook adapter.
- Observe and record would-block decisions without blocking.
- Compare shadow decisions with matched lead-only and existing-control baselines.
- Keep active global model and permissions unchanged unless separately authorized.

### Stage 4 — Manual canaries, separately approved

- Run read-only and isolated-write canaries under Fable leadership.
- Repeat the identical manifest under manually selected Opus 4.8 leadership.
- Verify model receipts, no nested delegation, no overlapping writers, correct result rejection, and final join behavior.
- Treat masked or flaky results as inconclusive.
- Resolve and canary planner tool, Skill shell, workflow, and team surfaces rather than trusting definition text.

### Stage 5 — Scoped monitored canary, separately approved

- Deploy shadow/monitored gates for a named disposable repository/cohort only.
- Monitor false blocks, duplicate dispatch, rejected unsupported claims, orphan workers, and rework.
- Missing or failed hook receipts block result acceptance and integration through the external supervisor, but do not prove the underlying tool call was prevented.
- Roll back by disabling the scoped adapter and preserving records; never rewrite evidence to pass.

### Stage 6 — Availability fallback canary and capability-boundary decision

- Attempt automatic outage fallback only if the provider/runtime offers a safe controlled mechanism.
- Record the actual per-turn result and reason; otherwise retain `UNKNOWN`.
- Do not promote dynamic native write enforcement as fail-closed on the current hook semantics. Broader promotion requires either new runtime support or a separately approved external-process adapter plus noninferior correctness, lower false completion, stable permissions, and no unresolved material findings.

No stage transition is implied by implementation completion. Each activation requires current owner authority and a rollback receipt.

## 19. Measurement Dashboard

| Metric | Desired movement |
|---|---:|
| Independently verified task correctness | Up or noninferior |
| False-complete rate | Down |
| Correct preservation of `UNKNOWN` | Up |
| Duplicate dispatch rate | Toward zero |
| Unauthorized delegation attempts | Zero |
| Tool-permission precision | Up |
| Workspace-permission precision | Up |
| Overlapping writer incidents | Zero |
| Worker findings accepted after verification | Up |
| Unsupported worker findings rejected | Visible, not hidden |
| Lead mechanical routing decisions | Down |
| Unique bookkeeping bytes delivered to lead | Down |
| Rework after integration | Down |
| Orphaned or unjoined workers | Toward zero |
| P95 latency by topology | Measured, not assumed |
| Verified value per worker | Up |
| Model-resolution uncertainty | Down |
| Transport-switch reconciliation failure | Zero |

The cited 2026 ClawArena-Team benchmark reports that no tested manager exceeded 50% workspace-permission precision and reports Fable's tested workspace-permission precision as 49.2%. This supports mechanical capability enforcement below the model; it does not establish local runtime superiority, savings, or permission correctness. See [arXiv:2606.31174](https://arxiv.org/abs/2606.31174).

## 20. Proof Obligations Before Completion

The implementation cannot be called complete until all applicable obligations are discharged:

1. ARC owns and validates the canonical record evolution.
2. Every managed role has an explicit capability declaration.
3. No ordinary leaf or coordinator can delegate through `Agent` or `Task`.
4. Read-only roles cannot mutate targets or gain persistent-memory writes.
5. Writers use verified expected bases and non-overlapping path leases.
6. Ordinary leaves statically omit delegation tools; when the settings gate executes, it also rejects a nested dispatch from a regressed definition. Missing gate execution remains `UNKNOWN` and non-integrable.
7. Requested and observed lead/worker models are recorded separately.
8. A real lead replacement creates and validates a new authority generation.
9. Malformed, partial, masked, stale, or missing worker output cannot become success.
10. Required background work is joined before final claims.
11. The final claim has fresh, covered, admissible, sufficiently independent evidence.
12. One dispatch backend owns each task generation, or an explicit handoff fences and reconciles the transition.
13. Atomic generation fencing admits exactly one receipted dispatch backend and rejects stale or unreceipted publication; it does not claim an unobserved native invocation was prevented.
14. Successful hook receipts demonstrate file/shell lease enforcement. Missing receipts make effects unknown and non-integrable; raw verifier Bash is not called read-only.
15. Evidence references resolve and verify content digests before promotion.
16. A closed arbiter predicate preserves inconclusive execution states.
17. Fable-led and manually selected Opus-led canaries satisfy the same authority and evidence protocol.
18. Availability and classifier fallback are separately observed or honestly remain `UNKNOWN`.
19. Existing ARC and SDLC compatibility fixtures remain green throughout migration.
20. The baseline lead can make integration decisions but cannot execute mutation, shell, MCP, publication, or integration effects.
21. `PostToolUseFailure` reconciles failed Agent attempts, and absent expected hook receipts remain inconclusive.
22. Hook-failure canaries preserve `UNKNOWN`, reconcile possible effects, and prove the external consumer refuses integration; they do not claim invocation prevention.
23. tmup stays disabled until a separately approved adapter and real invocation-counter race exist.

## 21. Ratified Operating Language

> Fable is the preferred implementation of the `lead-conductor` capability role. Claude Opus 4.8 is an eligible manually selected lead and configured availability fallback. Both operate under one model-neutral authority contract. Model substitution does not itself transfer or expand authority.
>
> The active lead is the sole ordinary delegation and integration-decision authority. The baseline lead is non-mutating; scoped implementers perform product changes and a separately authorized human or external adapter executes the final integration effect. Domain coordinators propose decomposition and synthesize domain results but do not recursively delegate. Every leaf has an explicit tool allowlist, no delegation capability, a bounded target and effect scope, and a typed result contract.
>
> SDLC-OS supplies role doctrine and assurance gates. Native subagents, agent teams, dynamic workflows, and tmup are dispatch backends selected under one run-scoped routing record. A task generation has one active dispatch backend and one owner unless an explicit, fenced, receipted handoff changes it.
>
> Worker reports are candidate evidence. Final success requires the lead to discharge named proof obligations with admissible, fresh, covered, and sufficiently independent evidence.

This design supersedes the earlier nested-coordinator proposal, plugin-frontmatter enforcement assumption, transport/doctrine conflation, and session-wide interpretation of model fallback. It deliberately leaves direct configuration mutation unapproved.
