# SDLC-OS Stage 1A Mechanical Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a locally committed, hermetic, relocatable, cross-platform Stage 1A mechanical baseline without changing any legacy bridge, pruning, inbox, health, phase, lifecycle, permission, or completion semantics.

**Architecture:** Repair the hazardous dispatcher fixture before making checkout paths relocatable, then centralize only the mechanical boundaries Stage 1A owns: plugin-root discovery, portable shell primitives, manifest-based tmup entry discovery, metadata/inventory checks, local `tsx` execution, and a fail-closed verification runner. Each change is test-first and independently committed; the runner records unmasked receipts but may report only the 1A release green until the separately planned 1B and 1C releases close the repository-wide Stage 1 gate.

**Tech Stack:** Bash 3.2-compatible shell, Python 3.12 standard library and `unittest`, Node.js 20.20.2, TypeScript, Vitest, npm lockfiles, JSON manifests, the owner macOS workstation, an owner-authorized Linux x86_64 verification host, and Git worktrees.

## Global Constraints

- Governing spec: `docs/superpowers/specs/2026-07-14-sdlc-os-production-control-plane-design.md`, approved at local commit `1c3285ad92c0daea2449bf3c5d56a3c248841a20`.
- Owner approval and F-01/F-02/F-03 review record: resolve the owner-local `OWNER_APPROVAL_RECORD` without committing its path; §4b was observed at SHA-256 `741ffe91ecc5ab4d4fd7d27037fc75e1eedeaba3d3d29dbfdefc754969721903`. This external record is provenance, not a repository artifact.
- Execution branch: `stage1/1a-mechanical-baseline`; use the operator-selected isolated worktree returned by `git rev-parse --show-toplevel` rather than publishing a machine-local absolute path.
- “Land” means a verified local commit only. Do not push, publish, deploy, open or mutate a pull request/issue, enable a service, or write another repository.
- Codex root is the sole repository writer, integrator, and local commit authority. Claude, OpenCode, and all delegated workers are read-only unless the owner grants new authority.
- Preserve every existing `docs/sdlc/active/*` artifact byte-for-byte. Normalization found nine legacy active directories and no Stage 1 task; the owner-selected Stage 1 work proceeds without rewriting or rejudging them.
- Preserve all v1 behavior: no-bead warnings, null-SLI warnings, advisory phase transitions, bead lifecycle vocabulary, worker permissions including `bypassPermissions`, health vocabulary, and completion outcomes.
- Missing, masked, stale, malformed, partial, author-only, candidate-mismatched, or unobserved evidence is `INCONCLUSIVE`, never `PASS`.
- F-01 is a hard dependency: Task 1 must commit fixture isolation and a restoration failpoint proof before, or atomically with, the first canonical-root adoption. No other executable test may adopt canonical root resolution first.
- Release 1A contains only mechanical baseline work. Direct tmup registry surgery, bridge synchronization, pruning, event inbox, and health semantics belong to the separately planned Release 1B; remaining deterministic failures, full test-integrity closure, and service packaging belong to Release 1C.
- Stage 1A green means every required 1A row passes. It does not imply the Stage 1 exit gate or production readiness; the repository-wide deterministic baseline remains non-green until 1B and 1C pass.
- Canonical runtimes are Node `20.20.2` and Python `3.12`; execute Colony commands with `/opt/homebrew/opt/node@20/bin` first on `PATH` on macOS. Resolve the owner-authorized Linux x86_64 target from local mesh inventory into `LINUX_VERIFY_HOST`; never commit its private alias or address.
- Stateful tests must use isolated temporary `HOME`, task root, tmup state, SQLite database, clone root, and hook/validator tree as applicable. No tested process may have a mutation path to the installed validator, live tmup registry/grid, or live task database.
- Do not use `eval`, shell command strings, `|| true`, piped success proxies, or substring-only success to execute mandatory checks. Capture the true process exit, stdout, and stderr separately.
- Use TDD for every behavior change: demonstrate the expected safe red state, implement the minimum change, then run focused and regression checks.
- Before each commit, inspect `git diff --check`, the scoped diff, staged diff, and worktree status. Commit messages must contain no attribution trailers, model names, personal work email, or generated-by text.
- Prior final spec-review passes used the same surviving reviewer and are recorded as `INCONCLUSIVE`, not independent. They cannot satisfy Release 1A or Stage 1 review gates.
- F-03 remains a Stage 2+ proportionality question. Run a simplicity audit after Stage 1 is green and before authoring or executing Stage 2 work.

## Rules, Policies, and Guardrail Application

`artifacts/rules_and_guardrails.md` is the operator matrix. New shell remains Bash 3.2-compatible, uses strict mode, avoids `eval`/dynamic download/masked required exits, and mutates only validated temporary roots. New Python targets 3.12, uses the standard library unless an approved dependency is locked, and never dumps ambient secrets. TypeScript runs under Node 20 with exact local tooling. Follow DRY/YAGNI: share only the finite contracts in the File Map, add no speculative framework, and add comments only where changed behavior needs explanation.

Workflow rules are local-only scoped commits, sole Codex write/integration authority, preserved user/legacy state, SSH-only LucasQuiles remotes if a read is needed, no push/publication/deploy/external message, no hook bypass, no destructive Git reset/checkout/restore/clean, and no live registry/task/validator mutation. Public commit identity and attribution rules are enforced by global hooks. Secrets never enter prompts, receipts, command output, or worker lanes.

A blocker is an authority/scope/safety breach, mandatory non-pass, masked/empty/candidate-mismatched evidence, unresolved material finding, missing required platform/reviewer, dirty candidate, or prohibited live reachability. A warning is only a reproduced preexisting out-of-scope finding with no changed-line/load-bearing effect, a named 1C owner/trigger, and visible evidence; warnings cannot satisfy checks. Exception paths require a current owner instruction naming the rule/change and a plan amendment with renewed validation. No exception can waive safety, authorization, independent review, or mandatory evidence.

Violations are detected by hooks, scoped Git diff/status, literal/path scans, manifest schema/receipts, before/after hashes, test-integrity/static gates, and non-author review. Preserve evidence, classify the rule, stop the dependent task, and correct/reverify or report the non-success verdict. Never silently normalize a violation into a limitation.

## Plan Review Control Header

This plan was hardened from the repository root with the 27-pass PlanPrompt protocol before execution. During that review only, `artifacts/` is the evidence root and `artifacts/run_manifest.json` is the command/provenance ledger. Those PlanPrompt artifacts assess plan quality; they are not implementation receipts and cannot satisfy any Stage 1A manifest row.

- Every review command records its argv or exact shell text, true exit, tool version, source commit, and output path in `artifacts/run_manifest.json`.
- Review verdicts are limited to `Pass`, `Fail`, `Inconclusive`, and `Blocked`. Implementation verdicts retain the governing spec's uppercase taxonomy.
- A missing tool is recorded as `not installed`; a deliberately inapplicable check is recorded as `skipped` with evidence; neither is silently omitted or promoted to `Pass`.
- Missing Git context, a missing target plan, absent required evidence, an unreadable artifact, or an unrecorded command blocks the affected review claim.
- Repo observations are time-bound to the commit and worktree status named in the run manifest. An untracked plan is expected before its plan-only commit; unrelated dirty state is not.
- The final PlanPrompt verdict can authorize only plan execution readiness. It cannot claim code correctness, Stage 1A green, Stage 1 green, production readiness, or reviewer independence.
- The PlanPrompt artifact directory is retained outside the release diff after review. Only the hardened plan is staged.

The plan-hardening orchestrator runs all 27 named PlanPrompt passes strictly in numeric order: control/scope/assumptions/validation/observability/readiness/decomposition/verification/testing/handoff/orchestration (1–12), reuse/impact/error/silent-failure/messages/TDD/tooling/contradiction (13–20), then lint/regression/hooks/rules/docs/capabilities/final synthesis (21–27). Before each pass it re-reads and snapshots the current plan; after each pass it records diff stats, required artifact-contract results, verdict, risks, and summary in the run manifest. A missing required artifact or failed render is recorded and corrected or stops the review. No code execution readiness claim is made until pass 27 finalizes consistency.

The pass-20 integration audit is recorded in `artifacts/contradiction_check.md`. It corrected missing installed-validator coverage, eliminated a second operational version literal, bound pre-commit Linux reproduction to `git write-tree`, and removed a post-review evidence commit that would invalidate the reviewed candidate. Pass 27 corrected one setup error: the safe red driver creates its decoy `tests/lib/` directory and copies that source directory only when it exists, because the shared helper is intentionally absent until Task 1 Step 3. The post-commit Task 1 entry audit then found `P27-07`: that decoy also needs the manifest required by the future resolver, explicit physical CWD/directory isolation, and post-swap signal/concurrency proof. During Task 1 green replay, `P27-08` proved that Apple Bash 3.2 does not apply `errexit` to the planned false `[[ ... ]]` conditional command; the copied test emitted its marker, continued through all 11 cases, and exited `0`. The amended failpoint uses `/usr/bin/false`, requires exact child exit `1` with empty child stdout, and retains a fail-closed unreachable exit. Subsequent read-only containment review found `P27-09` restore-evidence deletion, `P27-10` ancestor-retargetable lexical cleanup, and `P27-11` SIGINT distortion by a backgrounding capture wrapper. A second source-only Task 1 review found `P27-12..P27-16`: pre-swap case failures could coexist with the admitted marker, a disappeared backup could erase the restore obligation, lexical root disappearance could bypass cleanup verification, mixed concurrent exits could demote failure to inconclusive, and post-open drift was rejected only after clearing the held original. The four-path WIP is frozen while this plan-only amendment adds exact falsifiers and fail-closed precedence/retention rules; no corrected implementation byte is admitted before the amendment commit. PlanPrompt's Python 3.14 helper runtime is separated from canonical implementation Python 3.12; plan-review artifacts are separated from release receipts; and focused temp-helper proof is separated from the unsafe full smoke suite.

### Pass 27 First-Hand Synthesis

Three read-only inherited-model lanes audited the frozen pre-edit plan snapshot by disjoint Question IDs; their reports are advisory evidence, not independent candidate review. The reports cover IDs `1..320` exactly once and are retained as `artifacts/pass27-bank-{a-f,g-l,m-t}.md` with SHA-256 values `a5e5599c8615cfa77c9ca441cea541355b7b0a606a6e4c7284f2e6615a11e0bf`, `a76dc5921a9d58994caf8350b28ed7ad7aa196d0e130be29c8c60b4193d0c3e0`, and `df2a92b5fc300889ae7a9e94ed48d665204dff7d6c783050620e778ad48ea6f4`. Combined dispositions are 30 `PASS`, 62 `PARTIAL`, 27 `FAIL`, and 201 `INCONCLUSIVE`.

Most `INCONCLUSIVE` rows concern an unrelated guard/watchdog product and cannot establish SDLC-OS coverage. The applicable failures produced concrete revisions: requirement-to-receipt traceability, exact plan-only staging, pre-mutation clone identifier containment, protected evidence handling and durable receipt writes, a committed error-catalog authority, complete register fields, call-removal/dead-surface falsifiers, and fresh-bundle usability replay. The pass-27 artifact verdict remains `Inconclusive` because implementation, platform, and non-author candidate evidence do not yet exist; execution readiness remains `Ready with Constraints` for the safe Task 1 action only.

Time-bound Git provenance before the plan-only commit is: approved source `1c3285ad92c0daea2449bf3c5d56a3c248841a20`, merge base `bdc6635020d39ce005b4785481196aa096d1e989`, branch one commit ahead of local and SSH-origin `main`, no upstream configured, and origin `git@github.com:LucasQuiles/sdlc-os.git`. Current Git/source bytes outrank the bounded Pinecone search: the search found no directly matching Stage 1A record, only older low-relevance context, so no retrieved text is implementation proof.

| Generic pass-27 surface | Repository disposition |
|---|---|
| Guard CLI, `runCycle`, `runOneProbe`, watchdog, policy engine, collectors, simulators | Absent and outside 1A; `INCONCLUSIVE`, never fabricated as `PASS` |
| Guard `EventKind`, sinks, alerts, mutes, storm control, alert deduplication | Absent and outside 1A; no relationship to release evidence |
| Verification receipt events | Task 7 repository-local evidence only; they do not change Colony event or health semantics |
| Colony `EventType`, inbox, health, bridge, prune | Existing behavior; safety containment belongs to 1B and remaining deterministic closure to 1C |
| Deduplicating-functions tests | Code-clone analysis assigned to 1C; not alert/event deduplication |
| systemd/launchd | Disabled packaging belongs to 1C; installation or enablement is unauthorized |

## Objective, Scope, and Measurable Exit

**In scope:** executable and documentation surfaces named in the File and Interface Map under `tests/`, `hooks/` (copied fixtures only), `colony/`, `scripts/`, `.claude-plugin/`, `.claude/CLAUDE.md`, `README.md`, and `verification/`. The affected interfaces are Bash functions and CLIs, plugin/marketplace JSON, npm package/lock metadata, test configuration, and the new verification JSON/receipt contract. Plan-review reconnaissance is recorded in `artifacts/changed_files.txt`, `artifacts/top_level_dirs.txt`, and `artifacts/public_surface_hints.txt`.

**Out of scope:** all 1B/1C behavior, any Stage 2+ schema/control-plane implementation, changes under existing `docs/sdlc/active/`, live tmup teardown or registry writes, live task/Colony database mutation, service installation/enablement, external publication, and cross-repository edits.

| Criterion | Concrete check | Required threshold | Evidence |
|---|---|---|---|
| F-01 disarmed | Forced direct assertion after fixture swap plus byte/sidecar/cleanup comparisons | `Pass`; marker is temporary, source/decoy are identical, installed bytes are identical when applicable, restore failure retains evidence, cleanup retargeting deletes neither tree, and unexplained concurrent installed drift is `Inconclusive` | `.verification-results/.../s1a-f01-dispatch-isolation/{receipt.json,stdout,stderr}` |
| Relocatable tests | Run four scripts from an archived checkout in a path containing spaces; scan old literal | `Pass`; `13/13`, `14/14`, dispatcher/benchmark exit `0`, zero matches | Stage 1A root/relocation receipts |
| Portable/contained clone shell | Run helper/clone tests on macOS and Linux | `Pass` on both; positive byte telemetry, invalid identifiers mutate nothing, zero GNU literals | macOS/Linux helper and clone receipts |
| tmup discovery | Isolated manifest fixtures and installed-entry read-only observation | `Pass`; declared entry selected, escape/missing cases rejected | tmup discovery receipt and captured installed manifest digest |
| Metadata/inventory | Mutation tests, two checkers, two strict Claude plugin validations | `Pass`; version authority `10.0.0`, counts `46/16`, core subset `30` | metadata/inventory/plugin validation receipts |
| Local TypeScript runner | Offline/empty-cache execution, absent-install negative, TypeScript/Vitest | `Pass`; exact `tsx 4.23.1`, absent local binary exits `127`, nonempty tests | Colony tooling/typecheck/Vitest receipts |
| Verification authority | Runner unit tests and clean-candidate manifest run | `Pass`; true exits captured, no selected row `FAIL`/`INCONCLUSIVE`, run digest validates | runner tests and `run.json` |
| Review | Distinct read-only candidate reproduction | `Pass`; immutable candidate hash matches and no material unresolved finding | validated candidate-bound review results plus reviewer command receipts |

Release 1A is `Fail` when a mandatory check conclusively misses its threshold. It is `Inconclusive` when a required platform, reviewer, command exit, artifact, hash, test count, source commit, or safety boundary cannot be observed reliably. It is `Blocked` before execution when F-01 isolation cannot precede root adoption, the approved source is unavailable, or continuing would touch a prohibited live surface. Only all eight criteria at `Pass`, a clean local candidate commit, and no material unresolved finding permit the 1A owner checkpoint.

## Requirement-to-Evidence Traceability

The manifest retains every listed requirement ID even when Release 1A owns only a subgate. `PARTIAL` means later Stage 1 work is still mandatory; it never means the governing requirement passed.

| Requirement(s) | 1A disposition and owner | Task/files | Red, green, and negative proof | Manifest/receipt and remaining work |
|---|---|---|---|---|
| `S1-01`, `AP-14` | Required in 1A; Codex root | T3; portable helper, clone manager, smoke call sites | Missing helper/GNU literals and macOS alias red; positive bytes on macOS/Linux green; invalid size/prefix negatives | portable/clone rows; no remaining 1A portability work after both platforms pass |
| `AC-07`, `TF-08`, `P27-01` | Applicable security amendment discovered before implementation; shell boundary only | T3; clone create/recovery and focused caller/docs tests | traversal and pre-existing-symlink red inside disposable outer root; contained physical parent green; empty/separator/symlink negatives | clone-security row; analogous Deacon recovery path is inventoried for 1C, not claimed fixed |
| `S1-02`, `AP-15`, `F-01` | Required in 1A; F-01 precedes all root adoption | T1–T2; dispatcher isolation/root tests and four scripts | Safe outer failpoint red; copied-fixture and relocated path green; invalid/symlink/path-escape/source-installed mutation negatives | F-01/root/relocation rows; source, decoy, and installed fingerprints bound to receipt |
| `S1-03`, `AP-10`, `AP-16` | `PARTIAL`: only manifest-declared entry discovery is 1A | T4; tmup discovery/preflight | Hardcoded-entry red; current/future manifest green; missing/escaping entry negatives | entry-discovery row; supported teardown and registry non-mutation remain 1B |
| `S1-04`, `AP-17` | Required in 1A | T5; metadata checker/manifests | duplicate-version red; strict validation green; mutated version/omission negatives | metadata rows; authoritative approved value asserted in verification, not duplicated operational metadata |
| `S1-05`, `AP-18` | Required in 1A | T6; package/lock, wrapper, Vitest config/callers | undeclared/dynamic/zero-test red; offline local execution green; absent binary and empty suite negatives | tooling/typecheck/nonempty-Vitest rows |
| `S1-06`, `AP-19` | Required in 1A | T5; inventory checker/docs | current drift red; `46/16/30` green; removed agent and stale projection negatives | inventory row; runtime-loaded counts remain separately labeled |
| `S1-07`, `AP-11`, `AP-13`, `AP-24`, `F-02` | `PARTIAL`: 1A mechanical baseline only | T7–T8; manifest, runner, receipts, non-author review | absent runner red; complete 1A rows/replay green; masked/zero/missing/stale/candidate-mismatch negatives | 1A aggregate and independent review; full Stage 1 remains blocked on 1B/1C |
| `AP-01`, `AP-03`–`AP-05`, `AP-07`, `AP-09` | Binding scope/legacy/local-only constraints | Global constraints, T1–T8 scoped diffs | source/active-state hashes and v1 regressions; any push, policy change, rewrite, or permission change fails | action/diff receipts; no external mutation or v1 rejudging |
| `AP-02`, `AP-06`, `AP-08`, `AP-12` | Design/future-stage requirements; not 1A implementation authority | approved spec and release map | absence of v2 enforcement/dialect/activation mutation is the 1A negative proof | remain owned by their specified later stages; cannot support 1A green |
| `AP-20`–`AP-23` | Binding current authority and sequencing | plan/review ledgers and worker contracts | sole-writer Git diff, read-only worker reports, approved spec/provenance hash | plan-only commit plus action audit; new runtime writer requires owner grant |
| `F-03` | Explicitly deferred proportionality audit | post-Stage-1 checkpoint | no Stage 2 architecture/code in 1A; later simplicity audit is mandatory | cannot be closed by this release |

Every Task 7 manifest row carries nonempty `requirement_ids`; runner unit tests reject unknown IDs or a traceability set that omits an applicable 1A mapping. The final run summary projects requirement → row verdict → receipt hash and lists every unmet or later-owned requirement rather than collapsing `PARTIAL` into `PASS`.

## Assumption Audit

Evidence quality uses `direct`, `indirect`, `stale`, `inferred`, or `missing`. Dispositions use `Validated`, `Constrained`, `Replaced`, `Unresolved`, or `Blocked`. A due-checkpoint assumption cannot support the release verdict until its named validation passes.

| ID | Statement; category; source | Why/risk/blast radius if false | Current evidence and quality | Validation, artifact, owner, due | Disposition |
|---|---|---|---|---|---|
| A-01 | The Claude plugin schema permits the matching marketplace entry to omit `version`; contract; spec §9.1 item 4 and `.claude-plugin/*.json` | Task 5 design is invalid; metadata and plugin loading are affected | Other installed valid marketplaces omit it; `direct` but not this candidate | `claude plugin validate . --strict` and marketplace validation; `artifacts/plugin-schema-probe.txt` plus Stage 1A receipt; Codex root; Task 5 | `Unresolved` until strict validation |
| A-02 | The owner-authorized Linux x86_64 verification surface remains available with Node 20/Python 3.12; environment/authority; spec §11.4 and local mesh inventory | Cross-platform byte and shell claims become inconclusive; Tasks 3/8 and release gate affected | Read-only SSH observed Node `20.20.2`, Python `3.12.3`, ShellCheck `0.9.0`; `direct`, time-bound | Resolve `LINUX_VERIFY_HOST` locally, then re-probe `uname`, `node --version`, `python3.12 --version`; capability and Linux run receipts; Codex root; Tasks 3/8 | `Constrained` to fresh probe |
| A-03 | `du -sk` reports integral kibibytes on both named platforms and multiplying by 1024 preserves byte-named telemetry; portability; spec S1-01 | Telemetry could be empty/non-numeric or change units; clone/recovery logs affected | POSIX/common behavior and source inspection; `indirect` | Helper fixtures plus positive `clone_bytes`/`output_bytes` on macOS/Linux; `artifacts/portable-size-probe.txt`; Codex root; Task 3 | `Unresolved` until two-platform proof |
| A-04 | Copying `hooks/` and `scripts/` supplies every dispatcher validator dependency; fixture topology; current dispatcher/validator imports | F-01 test may pass only by suppressing a dependency or may reach the source tree; Task 1 affected | Full source call-chain inspection; `direct` for current commit | Failpoint driver, normal dispatcher suite, source-path marker, before/after hashes; `artifacts/f01-call-chain.txt`; Codex root; Task 1 | `Constrained` to immutable source commit and path proof |
| A-05 | tmup's manifest-declared entry and sync script are the supported discovery surface; dependency contract; installed tmup manifest | Preflight can select wrong root or future layout; cross-model review unavailable | Installed manifest names `mcp-server/dist/index.js`; `direct`, time-bound | Fake current/future/escape manifests plus installed read-only observation; `artifacts/tmup-manifest-probe.txt`; Codex root; Task 4 | `Constrained`; no teardown claim in 1A |
| A-06 | Exact `tsx@4.23.1` supports Colony's Node `>=20 <24` range; dependency; npm metadata and `colony/package.json` | TypeScript commands fail or fetch dynamically; Colony tooling affected | `npm view` reported Node `>=18`; `direct`, registry-time-bound | Exact lock entry, local `--version`, offline empty-cache invocation, Node 20 typecheck/Vitest; `artifacts/tsx-metadata.txt`; Codex root; Task 6 | `Unresolved` until locked execution |
| A-07 | The full smoke suite is not required to validate only the three temp-call rewrites in 1A; release boundary; shared `/tmp/sdlc-colony-conductor.lock` source | Running it early can mutate shared state; omitting all temp proof would leave item 10 untested | Source shows shared lock and three GNU calls; `direct` | Unit-test `make_temp_file`, literal scan; inventory full smoke as mandatory 1C row; `artifacts/smoke-safety-scan.txt`; Codex root; Tasks 3/7 | `Replaced` by focused safe proof; full suite remains non-green |
| A-08 | The four root-bound scripts require `bash`, `perl`, `jq`, and their fixture files on each selected platform; dependency | Relocated runs can fail for missing tools rather than root logic; Task 2/Linux review affected | macOS commands present; Linux availability not yet refreshed; `indirect` | `command -v` probe recorded before platform run; `artifacts/platform-tool-probe.txt`; Codex root; Tasks 2/8 | `Unresolved` on Linux |
| A-09 | Existing nine `docs/sdlc/active/*` directories are unrelated legacy state and must remain byte-identical; state/authority; normalization result | Accidental mutation violates owner/spec boundary; entire release invalid | Read-only inventory found no Stage 1 task; `direct`, time-bound | Pre/post tracked path hashes and scoped Git diff; `artifacts/active-task-hashes.txt`; Codex root; Task 8 | `Constrained` to zero-diff proof |
| A-10 | A genuinely distinct, owner-authorized read-only runtime will be available for committed-candidate review; review capability; spec §11.3/§18 and F-02 | 1A reviewer gate is inconclusive; no release `Pass` | Owner nominated Claude lane, but availability/identity not yet observed; `missing` for candidate | Refresh runtime catalog, keychain-safe auth probe if needed, capture observed identity/method/commands; `artifacts/reviewer-capability.txt`; Codex root; Task 8 | `Unresolved`; release blocker if unavailable |
| A-11 | PlanPrompt reconnaissance tools `conftest` and `osv-scanner` are relevant only as optional plan-context probes, not 1A implementation gates; tooling | Their absence could be misreported as release failure or silently ignored | Both are `not installed`; `direct` in `artifacts/conftest.txt` and `artifacts/osv.txt` | Retain explicit absence; dependency/SCA closure stays in 1C inventory; Codex root; plan review | `Constrained`; PlanPrompt evidence is `Inconclusive`, not release evidence |

No implementation task may stack a release claim on an `Unresolved` assumption. A-01, A-02, A-03, A-06, A-08, and A-10 become blockers at their due checkpoints; A-07 and A-11 explicitly narrow claims rather than being called passes.

## Pre-Implementation Finding and Deferral Register

Task 7 converts this register and every prior baseline finding into the full committed `verification/baseline-inventory.json` schema. Required fields are stable ID, class, severity, priority, owner, affected requirement/stage, trigger/due condition, evidence, mitigation, disposition, review date, and closure proof. A later release may own an item only when it is non-load-bearing for 1A and cannot invalidate the 1A claim.

| ID | Class; severity; priority | Owner; affected requirement/stage; due | Evidence and mitigation | Disposition; review date; closure proof |
|---|---|---|---|---|
| `P27-01` | defect; `CRITICAL`; P0 | Codex root; `AC-07`/`TF-08`/T3; before any shell clone create/recovery mutation | identifiers and pre-existing session/recovery symlinks can redirect `git clone`/`cp`; validate segments, reject symlinks, and use a physically contained parent | `ACCEPTED` into T3; 2026-07-14; red/green clone receipt plus outside-path absence |
| `P27-02` | limitation/defect; `MATERIAL`; P0 | Codex root; `S1-07`/T7; before runner commit | runner plan lacked result-root containment, protected modes, ENOSPC/write/rename/clock/background/source-mutation cases; implement fail-closed durability/privacy contract | `ACCEPTED` into T7; 2026-07-14; runner mutation/fault receipts |
| `P27-03` | missing authority; `MATERIAL`; P0 | Codex root; T7; before error-code claims | only review-local error catalog existed; create committed versioned catalog and drift test | `ACCEPTED` into T7; 2026-07-14; catalog schema/coverage receipt |
| `P27-04` | verification gap; `MATERIAL`; P0 | Codex root plus non-author reviewers; T8; before release verdict | add written-but-not-consumed mutations, call-removal reachability, DRY/dead-surface fitness, and copy-paste Git-bundle replay | `ACCEPTED` into T8; 2026-07-14; reviewer and usability receipts |
| `P27-05` | privacy/provenance; `MATERIAL`; P0 | Codex root; plan bytes; before plan-only commit | public plan exposed machine-local username/worktree/host/skill paths; replace with `$HOME`, `$PLANPROMPT_ROOT`, and local runtime variables | `RESOLVED_IN_PLAN`; 2026-07-14; zero-private-locator scan and plan-only diff |
| `P27-06` | applicability mismatch; `NONMATERIAL`; P2 | Codex root; plan review only | 201 question-bank rows target an unrelated guard/watchdog product; retain explicit `INCONCLUSIVE` reports, create no guard code | `NOT_APPLICABLE_TO_1A`; 2026-07-14; three report hashes and exact ID coverage |
| `P27-07` | plan dependency/isolation defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before any implementation byte | decoy omitted the manifest required by the planned resolver, inherited the source CWD, and lacked exact post-swap signal/concurrency admission; copy the manifest, create/canonicalize all isolated roots, execute from the isolated project, and test direct/signal/concurrent cleanup | `RESOLVED_IN_PLAN`; 2026-07-14; static call-chain audit, safe temporary resolver probe, and exact plan-amendment commit; T1 behavior receipts remain mandatory |
| `P27-08` | runtime-compatibility defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before further Task 1 implementation | Apple Bash 3.2 returns status `1` from `[[ 1 -eq 0 ]]` without triggering `errexit`, so the post-swap failpoint can continue and false-pass; use `/usr/bin/false`, retain an unreachable `exit 125`, require exact child exit `1`, and reject any child stdout | `RESOLVED_IN_PLAN`; 2026-07-14; Bash 3.2 falsifier plus isolated copied-test marker/`Results: 11 passed, 0 failed` evidence and exact plan-amendment commit; corrected T1 behavior receipt remains mandatory |
| `P27-09` | evidence-preservation defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before Task 1 admission | a failed restore can consume its backup, then both EXIT traps delete the only bounded diagnostic tree; latch restore failure before emitting it, skip all further restore/delete attempts, preserve both nested roots, and prove retention after the failing process exits | `RESOLVED_IN_PLAN`; 2026-07-14; disposable exact-flow red plus copied-fixture `restore-failure` receipt and retained-tree inspection remain mandatory |
| `P27-10` | cleanup-containment defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before Task 1 admission | lexical suffix checks followed by `rm -rf` can be redirected through a retargeted ancestor; capture parent/root device and inode, traverse with no-follow directory descriptors, recursively clear only the opened root, and perform a separately revalidated nonrecursive final removal | `RESOLVED_IN_PLAN`; 2026-07-14; ancestor/victim and post-open root-swap receipts plus zero raw production cleanup sites remain mandatory |
| `P27-11` | evidence-harness limitation; `MATERIAL`; P1 | Codex root; `F-01`/T1 and T7; before SIGINT admission | the optional hypothesis capture wrapper backgrounds its command, so Apple Bash inherits ignored SIGINT and the copied child reaches exit `125`; capture INT stdout/stderr/exit with a foreground raw-file launch, and never treat wrapper output as the SIGINT row | `RESOLVED_IN_PLAN`; 2026-07-14; paired wrapper/foreground reproduction plus foreground receipt remains mandatory |
| `P27-12` | admission false-pass defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before Task 1 admission | any of the eight pre-swap cases can increment `FAIL`, emit extra stderr, then still reach the marker and expected exit; require `PASS=8`/`FAIL=0` before the swap and admit only the exact single marker line | `RESOLVED_IN_PLAN`; 2026-07-14; synthetic pre-failpoint red/green plus exact-stderr receipt remains mandatory |
| `P27-13` | restore-obligation defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before Task 1 admission | a nonempty backup path that disappears or type-drifts is treated as no restore obligation; require a regular non-symlink backup whenever the variable is nonempty, otherwise latch/preserve/exit `125` | `RESOLVED_IN_PLAN`; 2026-07-14; baseline-mismatch and removed-backup retained-tree receipts remain mandatory |
| `P27-14` | cleanup-evidence defect; `CRITICAL`; P0 | Codex root; `F-01`/T1; before Task 1 admission | an absent/type-drifted outer root skips helper verification, and inner token capture/removal failure can be erased by outer cleanup; invoke captured-root removal whenever an obligation is nonempty and propagate one bounded inner-retained marker to a preserved outer container | `RESOLVED_IN_PLAN`; 2026-07-14; renamed-outer and forced-capture retained-tree receipts remain mandatory |
| `P27-15` | verdict-precedence defect; `MATERIAL`; P0 | Codex root; `F-01`/T1; before direct or concurrent admission | direct mode returns installed-drift exit `3` before checking a conclusive child/stream failure, while concurrent child exits `(1,3)` or `(3,1)` are classified `INCONCLUSIVE`; record installed drift, but force any conclusive child/stream or nonzero/non-3 child failure before exit `3` is considered | `RESOLVED_IN_PLAN`; 2026-07-14; fixed direct drift-plus-child-failure and concurrent `(1,3)` counterexample receipts remain mandatory |
| `P27-16` | retained-evidence defect; `MATERIAL`; P1 | Codex root; `F-01`/T1; before cleanup admission | the post-open swap is detected only after the descriptor-held original is cleared; revalidate the parent entry immediately before recursion so both original and replacement sentinels remain on drift | `RESOLVED_IN_PLAN`; 2026-07-14; post-open original/replacement sentinel receipt remains mandatory |

The A-series assumption rows are material unless explicitly constrained as non-load-bearing; A-04 and A-09 are critical safety/state boundaries. Task 7 imports every A-series row into the unified register with severity, priority, evidence, rationale, owner, mitigation, review date, and closure proof while retaining the assumption-specific quality/disposition fields. Existing 1B/1C findings are valid deferrals only with their named release, owner, trigger, rationale, mitigation, review date, and closure proof; an item discovered to invalidate 1A is immediately reclassified P0 and cannot remain deferred.

## Primary Validation Gate

Before Task 1, the implementer writes `artifacts/primary_validation.md` with columns `question`, `evidence reviewed`, `finding`, `severity`, `affected sections`, `required fix`, `status`, and `verdict`. PlanPrompt observed no root Makefile, root `pyproject.toml`, root `package.json`, or Go module and no installed Semgrep; those absent generic lanes are recorded in `artifacts/{make_test_dry_run,pytest,npm_test,go_test,semgrep}.txt` and do not replace the repository-specific commands below.

| Audit question / failure pattern | Required evidence and threshold | Plan disposition |
|---|---|---|
| Does a step rely on an unverified contract? | Assumption IDs and due commands; no critical `Unresolved` assumption past its checkpoint | A-01 tmup/schema, A-03 size semantics, A-06 dependency, A-10 reviewer are explicit gates |
| Are preconditions or dependencies out of order? | Task DAG inspection; F-01 commit must be an ancestor of Tasks 2–8 | Task 1 alone first; 1B/1C have separate entry gates |
| Are task boundaries falsely independent or circular? | File/interface map plus `git diff --name-only`; no two concurrent writers and no later interface consumed early | Execution is serialized; review workers are read-only |
| Can a step look successful while failing materially? | True exit, stdout/stderr, minimum test count, hashes; any missing/masked evidence is `Inconclusive` | Runner Task 7 and per-task red/green commands reject substring/zero-test success |
| Are fallback paths executable? | Invalid root, missing tmup entry, absent local `tsx`, platform/reviewer unavailable negatives | Exact failure exits/messages are specified; unavailable reviewer/platform stops green |
| Are rollback paths specific and safe? | Task-scoped commit, fixture-only cleanup, no installed/live target, correction-cycle candidate hash | Revert is a later explicit local commit; no destructive Git reset/restore is permitted |
| Are approvals or operator judgments implied? | Authority record and release stop points | Current grant covers 1A local work; owner review gates 1B; no activation/publication authority exists |
| Are exits concrete? | Eight measurable criteria plus clean commit and review | Only all `Pass` yields the owner checkpoint; `Fail`/`Inconclusive`/`Blocked` mappings are explicit |
| Is invisible manual work required? | Every remote copy, package install, review dispatch, hash validation, and cleanup command is receipted | Unrecorded manual action cannot satisfy a row |
| Do partial success or silent failure remain? | Manifest aggregate retains each row verdict and runner returns nonzero for `Fail`/`Inconclusive` | A narrow 1A pass cannot be labeled Stage 1 pass; later-release findings remain visible |

Primary validation verdict is `Pass` only when the audit contains no undispositioned critical/material finding and each Task 1–8 step has an exact command or inspection, expected output, named receipt, and failure/inconclusive rule. It is `Blocked` for the F-01 ordering/live-state hazards and `Inconclusive` for absent contract/platform/reviewer evidence. Required fixes alter this plan before code; they are not silently handled during implementation.

## Layered Validation Escalation

Primary validation checks plan logic and focused command behavior. Secondary validation must use a different mechanism against a different failure class. Tertiary validation is mandatory here because Task 1 protects an installed-code trust boundary and Task 7 executes repository-declared commands.

| Layer | Automatic trigger | Required distinct methods | Evidence | Blocker rule |
|---|---|---|---|---|
| Primary | Every task | TDD red/green, exact focused regression, source/diff inspection | Task receipt plus `artifacts/primary_validation.md` | Failed or unobservable focused check stops its task |
| Secondary | Portability, dependency/contract, negative path, changed executable boundary, or any accepted primary finding | Fault injection, mutation fixture, manifest escape/counterfactual, offline missing-dependency test, macOS/Linux independent execution, replay from an exact staged-tree archive or committed Git bundle | `artifacts/validation_layer2.md` during plan review; Stage 1A check receipts during implementation | Repeating the primary review or skipping an applicable method is `Inconclusive` |
| Tertiary | Installed/live-state reachability, arbitrary command execution, external runtime dependency, safety/authority boundary, or material secondary finding | Distinct-runtime adversarial review, non-author independent reproduction, contradiction search against spec/source bytes, signal/concurrency attack, receipt/hash replay | `artifacts/validation_layer3.md`, reviewer report, command receipts, immutable candidate hash | Unavailable required reviewer, candidate mismatch, or critical/material unresolved finding blocks release `Pass` |

Each layer artifact records `validation layer`, `reason invoked`, `methods`, `evidence reviewed`, `findings`, `severity`, `disposition`, `residual risk`, and `final verdict`. Fault injection and counterfactual tests cannot reuse the same assertion as their primary proof. Linux execution from independently transferred immutable bytes is a distinct environment method; rerunning the same macOS command twice is not. A different model label without distinct source inspection or command reproduction is not independent.

Applicable secondary modes by task are: Task 1 direct-assertion fault injection plus signal/concurrency attack; Task 2 relocated/symlink/invalid-root counterfactuals; Task 3 cross-platform replay; Task 4 current/future/escape manifest mutation; Task 5 metadata mutation and strict contract re-check; Task 6 offline/absent binary plus zero-test counterfactual; Task 7 command-injection, timeout, dirty-source, secret-key, artifact-loss, and receipt-replay tests. Task 8 performs tertiary independent reproduction and adversarial contradiction/failure-mode review.

No OpenAPI specification or authorized web target exists in 1A scope, as recorded in `artifacts/{openapi-files,schemathesis,dast_note}.txt`; Schemathesis/DAST are therefore plan-review `skipped` with evidence, not release passes. An intentionally deferred applicable layer must name owner, release, trigger, and residual risk in `verification/baseline-inventory.json`; a critical safety layer cannot be deferred.

## Logging, Replay, and Auditability

Plan review commands are ledgered in `artifacts/run_manifest.json`; implementation checks use Task 7's content-addressed receipts. Both are append-oriented evidence records, but only the latter can support a release verdict. A reviewer must reconstruct selected inputs, decisions, execution, validation, outputs, candidate changes, and review dispositions without chat history or operator memory.

| Event layer | Purpose and minimum fields | Actor/correlation | Storage and replay use |
|---|---|---|---|
| Input | Candidate SHA/dirty state, manifest/row hash, argv, relative cwd, declared environment, platform/applicability | observed actor/runtime identity, `run_id`, `check_id`; `trace_id`/`span_id` are `null` because 1A adds no tracer | Run summary/check receipt; proves exact replay inputs |
| Decision | Applicability, expected exit/observation, classification rule, assumption/finding disposition | decision owner, requirement IDs, `run_id`, `check_id` | Receipt and committed pre-freeze review-state context; explains why a verdict followed |
| Execution | start/end UTC, monotonic duration, pid/signal/timeout, true exit, tool versions | runner identity, `run_id`, `check_id` | Receipt plus raw stdout/stderr; diagnoses subprocess behavior |
| Validation | execution state, verdict, test count/observation result, artifact/hash checks, falsifier result | validator/reviewer identity and candidate SHA | Manifest receipt/reviewer report; prevents fabricated or substring-only green |
| Output | stdout/stderr/artifact relative paths, sizes, SHA-256, summary digest | producing check and `run_id` | `.verification-results/<run>/`; supports byte replay and tamper detection |
| Change | before/after commit, scoped paths, plan amendment/correction cycle, reason | Codex root/local commit author, candidate ID | Git history, diff, and committed pre-freeze review-state context; detects candidate drift |
| Audit | authority, reviewer method/identity, limitations, findings/dispositions, final state | owner/lead/reviewer with distinct run IDs | Validated ignored review-result artifact plus protected raw review evidence; proves confidence-affecting actions without changing the candidate |

Every structured event/receipt contains at least:

```json
{
  "timestamp_utc": "RFC3339 UTC",
  "run_id": "stage1a-<candidate>-<unique-suffix>",
  "service": "sdlc-os-verification",
  "env": "local-macos|local-linux",
  "trace_id": null,
  "span_id": null,
  "event": "input|decision|execution|validation|output|change|audit",
  "action": "<check_id-or-review-action>",
  "actor": {"runtime": "observed value", "role": "runner|lead|reviewer"},
  "result": "Pass|Fail|Inconclusive|Blocked",
  "inputs": {"git_sha": "full SHA", "manifest_row_sha256": "sha256"},
  "evidence": {"artifact_paths": ["relative/path"], "sha256": {}},
  "error": {"type": null, "message": null}
}
```

The following must never be silent: nonzero/signal/timeout, missing/empty/malformed evidence, zero discovered tests, failed cleanup/restore, candidate or hash mismatch, dirty source, platform/tool mismatch, `NOT_APPLICABLE` selection, reviewer substitution, redaction, retry/correction, unexplained live-state drift, and any attempted path escape. Confidence-affecting applicability, expected-output, finding, residual-risk, reviewer-independence, or verdict changes require an audit event and candidate binding.

Environment capture is allowlist-only; keys matching `TOKEN|SECRET|PASSWORD|KEY|COOKIE|AUTH` are rejected, values are never copied from the ambient environment into receipts, and filesystem paths in structured records are repository-relative or sanitized platform descriptors. Result directories are mode `0700`; raw stdout/stderr and receipts are mode `0600`, remain local, and are never embedded into summaries, prompts, or user-facing output. Synthetic canary tests prove nested receipt fields and summaries redact protected values while raw-artifact hashes remain verifiable; a detected real protected value makes admission `Inconclusive` and keeps the protected artifact out of reviewer payloads. Removing a required field or artifact contract is a regression and fails runner unit tests.

PlanPrompt artifacts remain reviewable through implementation-plan acceptance. Stage 1A implementation receipts remain local through the entire Stage 1 program and at least 90 days after its final owner checkpoint; no cleanup occurs in this release. An unreadable, unhashed, missing, or prematurely removed artifact changes the dependent verdict to `Inconclusive`.

## Execution Readiness Gate

| State | Evidence threshold | Allowed next action |
|---|---|---|
| `Ready` | All plan-level critical assumptions validated, no blocker/open critical risk, plan/repo/authority stable, Task 1 safe red command demonstrated | Execute Task 1, then follow the serialized DAG |
| `Ready with Constraints` | Stable objective/scope/authority and safe first action; due-checkpoint assumptions have exact validators and cannot be bypassed; no current blocker | Execute only through the next named assumption gate; stop on failed/inconclusive proof |
| `Not Ready` | Missing authority/spec/repo context, F-01 ordering not enforced, prohibited live reachability, unbounded task, absent safe red, or critical assumption without validator | No code; repair/amend plan or request owner decision |

The plan-review readiness record is `artifacts/readiness.json`. It names the state/date, evidence reviewed, open risks, blockers, rationale, decision authority, and next allowed action. Codex root decides plan execution readiness within the approved local scope; only the owner accepts scope/authority/residual-risk changes and reviews the release before 1B. Missing CODEOWNERS/CI/SCA surfaces are recorded in `artifacts/{codeowners_present,ci_configs,sca_readiness}.txt`: they narrow claims and keep full baseline/SCA work in 1C, but do not invent an external approver or CI gate for this local 1A release.

Readiness requires affirmative evidence for stable objective, bounded scope/non-goals, audited assumptions, a validator for every critical assumption, known dependencies and ordering, contract probes, real command seams, molecular tasks, explicit proof/falsifiers, sufficient receipt telemetry, measurable pass/fail/inconclusive signals, fixture cleanup/containment, named owners, and residual-risk disposition. The current pre-code state may be `Ready with Constraints` only: A-01/A-02/A-03/A-06/A-08/A-10 remain due gates, but Task 1's outer driver is a safe first action that cannot mutate the installed validator.

Readiness is reevaluated before every task and after any plan amendment, accepted material finding, changed candidate, tool/platform substitution, or evidence loss. A residual risk cannot waive a mandatory check, safety boundary, independent review, or owner authority. If a due gate becomes unavailable, the state changes immediately to `Not Ready` for dependent work or `Inconclusive` at the release gate.

## Molecular Execution Contract

Each checkbox step is an atomic unit with ID `T<task>.<step>` and parent `T<task>`. Before marking it complete, write `.verification-results/manual/T<task>.<step>/step.json` containing: `task_id`, `parent_task_id`, `objective`, `preconditions`, `inputs`, one `action`, `expected_output`, `observable_signals`, `validation_method`, `failure_modes`, `retry_path`, `rollback_path`, `evidence_produced`, `dependencies`, `blocking_conditions`, `true_exit`, and `verdict`. Raw stdout/stderr sit beside it and are hashed. Task 7 may ingest/hash these records but cannot retroactively turn a missing record into proof.

| Parent | Entry condition / inputs | Primary output / exit | Validation / evidence | Failure, retry, rollback, dependency |
|---|---|---|---|---|
| T1 | Approved source; source/decoy/installed snapshots; no root consumer changed | Fixture-isolated dispatcher and failpoint driver; normal suite green | Direct assertion, HUP/INT/TERM self-signals, two-driver concurrency, byte/mode/size/hash and sidecar checks; `manual/T1.*/` | Any installed reachability blocks; retry only after test/plan correction; rollback by local revert commit; no predecessor |
| T2 | T1 committed; shared resolver interface fixed | Four scripts resolve explicit/fallback physical roots | Relocated path-with-spaces run and literal scan; `manual/T2.*/` | Any old literal or changed assertion fails; revert Task 2 commit; depends T1 |
| T3 | T2 committed; isolated clone/temp roots | Portable size/temp functions, pre-mutation identifier validation, and canonical path boundary | macOS/Linux positive-byte, traversal, and lexical/physical tests; `manual/T3.*/` | Any outside-base side effect fails; platform absence is inconclusive; no full smoke; revert Task 3 commit; depends T2 |
| T4 | T3 committed; fake tmup/state/binaries | Manifest-declared entry resolution | Current/future/missing/escape fixtures; `manual/T4.*/` | Any live grid/registry access blocks; revert Task 4 commit; depends T3 |
| T5 | T4 committed; plugin schema CLI available | Sole version authority and exact inventory projection | Mutation tests plus strict validation; `manual/T5.*/` | Schema rejection stops for plan amendment; revert Task 5 commit; depends T4 |
| T6 | T5 committed; Node 20 and lockfile | Exact local `tsx` wrapper and nonempty Vitest policy | Offline/absent/zero-test negatives, typecheck, Vitest; `manual/T6.*/` | Dynamic fetch or zero-test green fails; revert Task 6 commit; depends T5 |
| T7 | T6 committed; manual receipts available | Strict manifest/runner plus baseline/review registers | Mutation/timeout/exit/hash unit tests and development manifest; `manual/T7.*/` | Unknown schema/path/secret/masked result fails; revert Task 7 commit; depends T6 |
| T8 | Clean immutable T7 candidate | Cross-platform receipts, distinct review, one release verdict | Full 1A manifest, receipt replay, independent/adversarial reports; `stage1a-{macos,linux}/` | Correction creates new candidate; two-cycle limit; no destructive rollback; depends T1–T7 |

Atomicity smell test: split a checkbox before execution if its action field contains `and`, mixes mutation with validation, yields unrelated outputs, requires unstated operator judgment, or can partially succeed without a distinct signal. Multiple commands are permitted only inside one validation action against one output. A step cannot be marked complete from its parent commit, prose, or a later aggregate alone.

## Tooling and Execution Orchestration

The live local inventory is captured in `artifacts/{tool_inventory,tool_versions}.txt`; the task/tool map is `artifacts/tooling_plan.md`. Required implementation executables are Bash 3.2-compatible `/bin/bash`, Python 3.12, Node 20/npm, Git, jq, perl, Claude CLI for strict plugin validation, SSH/scp to `${LINUX_VERIFY_HOST:?resolve from owner-local mesh inventory}`, and later ShellCheck/Ruff in 1C. `hypothesis-runtime` may capture pre-run receipts, but Task 7's repository runner remains the release authority. A standalone `tmup` CLI is not installed; tmup coordination uses the installed plugin/supported scripts or its documented wrapper, never an invented command.

Codex skills used in order are `executing-plans` (inline sole-writer execution), `test-driven-development`, `systematic-debugging` on any unexpected result, `hypothesis-driven` for falsifier/receipt discipline, `test-integrity`, `progressive-disclosure-coding`, then `verification-before-completion`, `requesting-code-review`, `sdlc-gap-analysis`, and adversarial/simplicity review at the gates. `using-git-worktrees` has already established isolation. Before invoking a named skill, the lead reads its current instructions; skill output is process guidance, not pass evidence.

Claude realm use is read-only candidate verification through the owner-nominated lane and installed SDLC-OS/tmup surfaces; Claude never edits this repository. OpenCode may provide a second read-only adversarial path via `opencode-delegation`. Before model-explicit dispatch, resolve the owner-local runtime-catalog helper without committing its absolute path, refresh runtime `codex` with Python 3.12, and inspect `ocwx <role> --models`; record observed identity, not an assumed label. Native Codex subagents inherit the active model and are advisory, never independent.

Pinecone/codebase or dev-docs search is read-only and applicable only to reuse/pattern discovery before implementation; retrieved text must be corroborated against current source bytes. Playwright, Sentry, Render, Google Workspace, WhatsApp, GitHub writes, browser automation, and deployment MCPs are not applicable to this local shell/tooling release. Their availability grants no authority and their omission is recorded, not silently treated as coverage.

Tasks 1–7 are serialized root-writer work because they depend on prior commits and overlap release evidence; no subagent gets a write scope. Parallel read-only lanes are allowed only after inputs freeze: source/caller audit, Linux reproduction, and distinct reviewer/adversary analysis. Each lane receives objective, immutable candidate/context boundary, no-write/no-external-action rule, wall-time/output budget, stop condition, expected commands/artifacts, and limitations schema. Intake is schema-first: lane ID, candidate/manifest hashes, observed runtime, commands/true exits, `file:line` plus symbol/test and source hash for material claims, findings, limitations, and report hash. Raw transcript capture is opt-in, mode `0600`, separately named `<lane>-raw`, and never substituted for the bounded `<lane>-report.json`; Codex root validates both and records disposition.

Determinism across lanes requires the same full candidate SHA/manifest hash, isolated temp/state roots, no shared mutable artifact, explicit platform/runtime fingerprints, raw true exits, and content hashes. Conflicting results remain separate and make the affected claim `Inconclusive` until reproduced/resolved; consensus never overwrites evidence. Secrets, commits, integration, publication, cleanup of non-temp state, and final verdict remain with Codex root.

### Capability and Historical-Context Inventory

| Class | Available/relevant use | Evidence and ownership |
|---|---|---|
| Skills | Planning/PlanPrompt, worktrees, executing-plans, TDD/debugging/hypothesis/test-integrity, progressive disclosure, verification/review/gap/adversarial/simplicity, Pinecone/OpenCode/tmup routing | `artifacts/available_skills.txt` plus skill-use ledger; guidance only, Codex root writes |
| Repository/runtime scripts | Existing Bash/Python/TS suites, Claude strict validator, hypothesis capture, test-integrity, future repository runner | `artifacts/repository_scripts.txt`, exact argv/exits; tools do not expand authority |
| Agents/runtimes | Native Codex read-only probes, owner-nominated Claude independent verifier, OpenCode adversary, owner-authorized Linux executor | Dispatch contracts/raw reports/observed identity; no worker repository writes |
| Plugins | Installed SDLC-OS, tmup, test-integrity and other observed plugins | `artifacts/installed_plugins.txt`; only tmup discovery/test-integrity/reviewer routes are relevant; read-only except this isolated SDLC-OS worktree |
| MCP/connectors | Pinecone read-only retrieval is potentially relevant; Playwright/Render/Google/WhatsApp/GitHub writes are not | Query/result provenance when used; source-byte corroboration; no external mutation |
| Runtime/devops | macOS shell/runtime tools, SSH/scp to `LINUX_VERIFY_HOST`, Git worktree/hooks | Tool/platform receipts; unique temp roots; no browser/deploy/service surface |
| History | Git log/show/blame/`-S`/`-G`, approved spec/plan, prior baseline captures, current review artifacts; Pinecone `dev-docs`/`thinkers-lab` only when query fits | `artifacts/{git_history,git_branch_context,prior_context_files}.txt`; current source/spec outrank retrieved history |

Before implementation, run one bounded Pinecone/repository-history reuse search for each new contract surface; a missing/not-indexed result is recorded and current `rg`/Git/source inspection remains authoritative. Do not use OnePlatform-specific embeddings as proof about SDLC-OS. Before deleting any future superseded branch, use range-diff/cherry comparison; no branch deletion is in 1A.

Subagent-driven development is used where decomposition is safe: independent read-only discovery/review lanes receive bounded contracts, while the sole-writer policy requires inline implementation. Effective parallelism is restricted to frozen, non-overlapping read-only/platform work. Every implementation mutation remains TDD-driven, and every meaningful correctness claim remains deterministic or explicitly `Inconclusive`. Hidden tools, vague future MCP use, unbounded workers, overlapping writes, and nondeterministic consensus-as-proof are rejected.

## Verification Design

`artifacts/verification_matrix.md` is the plan-review proof map; `verification/manifest.json` becomes the executable release authority in Task 7. Every atomic step links to a matrix parent row and its own `step.json`; every release claim links to the exact candidate, manifest-row hash, raw artifacts, and verdict receipt. Structured JSON is required where the check owns a schema; raw stdout/stderr and SHA-256 remain available beneath normalized summaries. Static-analysis tools may emit SARIF when available, but absence of SARIF never hides the underlying exit or output.

Preferred proof order is deterministic assertion, state/contract/schema inspection, diff/checksum, replay on immutable bytes, then independent evidence-linked review. Narrative validation, “looks correct,” unsupported intuition, completion without artifacts/signals, and a test without pass/fail/inconclusive thresholds are invalid. A missing row or receipt is `Inconclusive`; a conclusive threshold miss is `Fail`; only observed satisfaction is `Pass`.

The matrix records exact method, actor, expected output, artifact, all three verdict conditions, and escalation for T1–T8. Atomic children inherit the parent claim boundary but not its verdict. No aggregate can conceal a failed child, zero tests, missing platform row, or reviewer/candidate mismatch.

## Testing and Anti-Fabrication Standard

| Category | 1A family and provenance | Expected-result derivation / replay |
|---|---|---|
| Unit | Bash/Python helper and runner cases; synthetic minimal fixtures | Function/CLI contract in this plan; replay exact argv from receipt |
| Integration | Dispatcher copied hook tree, clone manager, preflight, Colony tooling; captured repository bytes plus synthetic state | Existing v1 behavior/spec plus pre-change baseline; replay from immutable staged or committed candidate bytes |
| End-to-end | Four relocated scripts and full manifest from an immutable candidate checkout; captured candidate | Spec §9.1 exit rows; replay on macOS/Linux with the same candidate and manifest hashes |
| Negative | Direct assertion, invalid root, manifest escape/missing entry, drift, absent `tsx`, zero tests, bad runner rows; synthetic mutations | A specifically named forbidden outcome must be rejected with exact exit/reason |
| Regression | Existing dispatcher exits, shims `14/14`, fixtures `13/13`, clone total, TypeScript/Vitest; captured legacy fixtures | Pre-change source contract and approved non-policy-change boundary |
| Observability | Receipt required-field deletion, raw hash mismatch, missing event/artifact; synthetic mutations | Governing receipt schema; any missing integrity field becomes `Inconclusive`/failure |
| Adversarial | Symlink/path escape, concurrency/signal, command/env injection, candidate mismatch; synthetic counterexamples | Safety/authority invariants have tolerance zero |
| Stale-data | Stale candidate SHA, prior-review receipt, changed manifest row; synthetic prior versions | Digest/time/candidate bindings must reject reuse |
| Partial-data | Empty/truncated stdout/stderr/receipt, missing Linux artifact, zero test count; synthetic truncation | Spec evidence-integrity mapping requires `Inconclusive`, never `Pass` |
| Degradation | Missing reviewer/platform/tool/local dependency; observed or synthetic absence | Explicit `Blocked`/`Inconclusive` contract; no fallback is called equivalent |

Every family records input locator/hash, provenance type (`synthetic`, `sampled`, `captured`, or `production-derived`), representativeness rationale, expected-result authority, raw artifact paths, and replay argv/environment. No 1A test uses production-derived secrets or live state; installed manifest/validator observations are captured read-only and time-bound. The provenance index lives under `artifacts/test_evidence/` during plan review and in each implementation receipt thereafter.

False-positive controls are: direct true-exit capture; minimum discovered-test assertions; mutation tests that prove the assertion can fail; before/after hashes; candidate/manifest-row binding; no `|| true` or `passWithNoTests`; separation of conditional live/provider rows; and per-row verdict aggregation. Anti-fabrication controls are raw stdout/stderr preservation, content hashes, immutable Git bundle/detached-checkout replay for integrated verification, staged-tree archives for pre-commit portability probes, observed runtime identity, independent command reproduction, and explicit disclosure of missing tools/methods. Exit zero without the required observation/artifact is not green.

Mutation fixtures, contract/schema mutation, contradiction search, and fault-injection/replay are applicable and required. Broad property-based generation is not required for the finite 1A interfaces; general mutation tooling, signing/attestation infrastructure, and production sampling are `not applicable` unless a later finding demonstrates need. Outputs are not cryptographically signed in this local environment; Git candidate hashes plus receipt SHA-256 provide tamper evidence without claiming signer identity.

Only `Pass`, `Fail`, `Inconclusive`, or `Blocked` are permitted in test summaries. Absence of an error, skipped execution, empty output, old receipts, reviewer agreement, or a passing aggregate without child evidence is never sufficient. An integrated replay must start from the verified Git bundle and detached candidate checkout, validate candidate/manifest/receipt hashes, and produce the same categorical verdict; nondeterministic timing values are compared by bounds, not byte equality. “Not reproduced” never closes a failure: after an unexpected or suspected transient result, run two additional identical replays (three total) on the same candidate, manifest, tool fingerprint, and isolated environment, retain all receipts, and keep any divergence `Inconclusive` until root cause and a falsifier are proven.

### TDD, Provenance, and Independent Validation Discipline

TDD is mandatory for Tasks 1–7 and every accepted correction in Task 8. A real red phase is a newly added/strengthened test that exits nonzero for the intended missing behavior or wrong contract, preserves prohibited state, and contains a falsifiable signature; syntax/import/setup failure is not a behavioral red unless that dependency is the exact contract under test. Capture the test diff, true exit, stdout/stderr, failure signature, candidate SHA, and installed/live before/after proof before implementation bytes change.

Green requires the minimum implementation, the same test now passing, its negative/counterexample still failing as designed, and relevant regressions. Refactoring occurs only after green and re-runs the same evidence set. A preexisting red baseline may establish the defect but does not substitute for the new regression's red proof.

Deterministic fields are exits, categorical verdicts, counts, canonical paths relative to controlled roots, hashes, selected entry/version, and error codes. UTC timestamps, run IDs, temp paths, PIDs, durations, filesystem allocation granularity, and concurrent external state are nondeterministic; tests validate format/uniqueness/bounds or classify unexplained drift `Inconclusive`. Randomness is not needed; if introduced by a dependency, record its seed or raw captured fixture.

Fixtures carry source locator/hash and `synthetic|sampled|captured|production-derived` tags in receipts. Each family records expected-result authority, replay argv/environment, counterexample, and applicable mutation/contract/schema/replay method. Independent validation is mandatory for installed-tree isolation, both-platform portability, runner command/evidence safety, and the integrated candidate. It must bind the commit and use source-byte inspection plus command reproduction or a materially different falsifier; inherited-model agreement alone does not qualify.

## Linting, Formatting, and Static Quality Gates

The executable matrix is `artifacts/linting_plan.md`; Task 7 mirrors applicable 1A commands into the verification manifest. No repository-wide formatter, root ESLint, or root Python type checker is configured, so 1A does not invent one. Formatting is protected by `git diff --check`, `ruff format --check` for new Python, existing TypeScript compiler conventions, and focused review. Semgrep is not installed and is recorded as unavailable plan context; it is not cited as coverage.

Mandatory fast gates are Bash `-n` for every touched shell file, ShellCheck `-x` for new/modified 1A shell surfaces, Python 3.12 compile plus Ruff check/format on new Python, JSON parse/schema tests, Node 20 `tsc --noEmit`, nonempty Vitest, strict Claude plugin validation, scoped test-integrity scans for new tests, and Git whitespace/staging hygiene. Exit nonzero or any error-level finding blocks the owning task. A warning is nonblocking only when reproduced at the approved base, does not touch changed lines/behavior, has a 1C inventory owner, and remains visible; new warnings and all masked/zero-test/static parse failures block.

Generated lockfile formatting is owned by npm and validated by `npm ci`/JSON parsing rather than manual formatting. Markdown tables/links/commands receive diff review and executable-command checks; documentation-wide tooling belongs to 1C. Static output is captured with true exits under the task receipt, not truncated to a success substring.

## Regression Protection and Change Safety

The executable protection map is `artifacts/regression_protection.md`. Baselines are the approved source commit, source/installed validator hashes and sidecar absence, active-task hashes, current plugin/tmup manifests, known test counts/exits, clone log field names, and Colony package/lock bytes. Every task captures its applicable before state before red and compares after green; unexplained drift is non-pass.

Protected behavior includes v1 dispatcher/warning exits, validator contents, active task bytes, clone no-push/prune/refusal rules, `clone_bytes`/`output_bytes` names, tmup registry/lifecycle ownership, plugin version `10.0.0`, repository/runtime count distinction, existing TypeScript/Python behavior, and suite-specific command callability. Negative controls deliberately remove/break/escape/stale each boundary so a test that cannot detect the forbidden state is rejected.

Regression detection runs after every implementation step, before each commit, on the clean committed macOS candidate, on the Linux Git-bundle checkout, and during independent/adversarial replay. There is no rollout/deployment in 1A; a future merge/install must rerun the committed manifest and installed-tree fingerprint separately. Triggers are any changed v1 exit/policy, installed/live mutation, path-containment widening, missing field/test, dynamic fetch, version/count drift, tmup write, or new static/test-integrity finding. Containment is stop/preserve evidence/new scoped revert or correction commit; rollback never reinstates F-01 or weakens a safety invariant.

## Hooks, Automation, and Workflow Enforcement

The observed hook inventory is in `artifacts/{git_hooks_path,git_hooks_inventory,pre_commit_hook,commit_msg_hook,pre_push_hook}.txt`; policy is summarized in `artifacts/hook_plan.md`. Existing global pre-commit secret/identity checks and commit-message attribution rejection run on every local commit. This repository has no observed local Husky or CI configuration, so 1A adds no hidden CI/auto-deploy claim and does not mutate machine-global hooks.

Task commands and the manifest are explicit local gates, not Git-hook side effects. A hook or task gate failure stops the commit/task, preserves stderr/receipt, and is corrected before retry. `--no-verify`, hook editing, environment bypass, or threshold weakening is not permitted under this plan; if a machine hook is broken or falsely blocks, record the command/evidence and request owner direction rather than bypass it. The pre-push hook is never invoked because push is outside authority.

If CI is later added, it must execute the same lockfile/install, manifest, nonempty-test, artifact/hash, macOS/Linux applicability, and candidate-binding contracts and upload raw receipts. A CI green without required platform/reviewer rows cannot replace the local release gate. CI design/activation is outside 1A and remains a 1C/release-engineering disposition.

## Documentation, Runbook, and DevOps Readiness

The pass record is `artifacts/documentation_devops_readiness.md`. Release documentation changes are finite: correct repository inventory in `.claude/CLAUDE.md`/README; label README's core subset; replace all Colony dynamic-`tsx` commands/comments with local wrapper examples; and add `verification/README.md` for runner/schema/receipt/platform operations. Every command example is executed or syntax/contract checked on the named runtime.

The operator runbook is this plan plus `verification/README.md`: prerequisites, isolated worktree/branch, Task 1 safety order, Node/Python versions, owner-authorized staged-archive and integrated Git-bundle Linux flows, offline package execution, manifest exits, receipt replay/retention, correction/review gates, and owner checkpoint are explicit. No dashboard, external alert, service enablement, migration, deployment, CI, or release publication is delivered or claimed in 1A. Local runner summaries/receipts are the only operational signal.

Environment changes are limited to the exact Colony dev dependency/lockfile and documented invocation-time variables (`CLAUDE_PLUGIN_ROOT`, `SDLC_INSTALLED_PLUGIN_ROOT`, `TMUP_PLUGIN_ROOT`, `LINUX_VERIFY_HOST`, `TMPDIR`, isolated `HOME`, npm offline/cache settings). No shell profile, secret store, daemon unit, remote config, or persistent remote path changes. Temporary remote artifacts use unique roots and bounded cleanup receipts.

Open operational risks stay visible in the baseline inventory: absent CI/SCA/SBOM/attestation, shared smoke lock, service packaging/launchd absence, full ShellCheck/Ruff/test-integrity closure, and 1B containment gaps. These prevent broader Stage 1/production/devops claims but do not hide the reproducible 1A mechanical scope. Documentation readiness fails if examples disagree with code/lockfile, required README/schema text is missing, or a reproduction command is unexecuted without an explicit `Inconclusive` disposition.

## Release Map and Stop Conditions

| Release | Owned work | Entry gate | Exit claim |
|---|---|---|---|
| 1A (this plan) | F-01, checkout roots, portable size/temp, tmup entry discovery, metadata/version, inventory, local `tsx`, verification runner | Approved spec at `1c3285a`; F-01 must be first | `STAGE_1A_MECHANICAL_BASELINE=PASS` only |
| 1B (separate plan) | Supported tmup teardown, bridge-sync failure propagation, no age-only prune, inbox/health containment | Clean committed 1A plus owner review | `STAGE_1B_LEGACY_CONTAINMENT=PASS` only |
| 1C (separate plan) | Remaining deterministic failures, test-integrity closure, service packaging without enablement, full macOS/Linux matrix | Clean committed 1B plus owner review | Integrated Stage 1 candidate ready for independent and adversarial review |

Stop this release and report `INCONCLUSIVE` if F-01 cannot be proven without touching an installed validator; the owner-authorized Linux host cannot reproduce the platform-sensitive rows; strict plugin validation rejects removal of the marketplace version; a mandatory command is masked or discovers zero tests; a new load-bearing 1A defect is found; or a test reaches live task/tmux/validator state. A new load-bearing finding requires a written plan amendment before implementation, not an improvised fix.

## Review State Before Execution

| Review evidence | State | Reason |
|---|---|---|
| Two final spec passes by the same surviving reviewer | `INCONCLUSIVE` | Same reviewer and reasoning path; not independent under spec §11.3/§17.3 |
| Owner-nominated read-only spec review | `PASS` for spec approval, not candidate verification | It checked source bytes and found F-01; no Stage 1A candidate existed |
| Native Codex inventory/F-01 subagents | Advisory only | They inherited the active model and cannot satisfy independent review |
| Release 1A non-author reproduction | `PENDING` | Must inspect the immutable committed 1A candidate |

## File and Interface Map

| Path | Responsibility |
|---|---|
| `tests/lib/plugin-root.sh` | Resolve and validate `CLAUDE_PLUGIN_ROOT` or a test script's physical checkout root |
| `tests/lib/f01-temp-tree.py` | Reject temp-root identity drift and recursively clear only an opened F-01 tree through no-follow descriptor-relative operations |
| `tests/test-sdlc-dispatch-isolation.sh` | Force a direct post-swap assertion and prove installed/decoy validators remain unchanged |
| `tests/test-sdlc-dispatch.sh` | Exercise dispatcher behavior only against an inner copied fixture tree |
| `tests/test-plugin-root-resolution.sh` | Prove explicit, fallback, invalid, symlinked, and relocated checkout resolution |
| `tests/{benchmark-dispatch,test-validator-shims,test-fixture-regression}.sh` | Consume the shared canonical root without changing test semantics |
| `colony/lib/portable-shell.sh` | Provide portable path-size and temporary-file primitives |
| `colony/clone-manager.sh` | Consume byte-size helper, reject unsafe identifier segments before mutation, and compare canonical clone/base paths |
| `colony/clone-manager.test.sh` | Assert positive byte telemetry, `/var`/`/private/var` equivalence, and zero traversal side effects |
| `colony/smoke-test.sh` | Replace three GNU-only `mktemp --suffix` calls with the portable helper |
| `tests/test-portable-shell-helpers.sh` | Prove size/temp behavior without executing unsafe shared-lock smoke paths |
| `scripts/lib/tmup-discovery.sh` | Resolve tmup's manifest-declared MCP entry while retaining the plugin root |
| `scripts/crossmodel-preflight.sh` | Consume supported tmup discovery; no teardown or registry mutation in 1A |
| `tests/test-crossmodel-preflight.sh` | Exercise manifest-declared, future-equivalent, missing, and escaping entries in isolated state |
| `scripts/check-plugin-metadata.py` | Enforce plugin manifest as sole version authority and reject duplicate marketplace version |
| `scripts/check-repository-inventory.py` | Derive repository agent/skill counts and validate their documentation projections |
| `.claude-plugin/marketplace.json` | Keep marketplace discovery metadata without a duplicate version |
| `.claude/CLAUDE.md`, `README.md` | Correct 46/16 repository inventory and label README's 30-agent core subset |
| `colony/run-tsx.sh` | Execute only `colony/node_modules/.bin/tsx`, failing clearly when absent |
| `colony/package.json`, `colony/package-lock.json` | Pin exact `tsx` `4.23.1` and preserve Node `>=20 <24` |
| `colony/vitest.config.ts` | Reject zero-test success |
| `colony/{smoke-test.sh,bridge.test.ts,bridge-cli.ts,README.md,conductor-prompt.md}` and `colony/scripts/*.ts` | Document the safe clone-identifier grammar and replace dynamic-download examples/invocations with the local wrapper |
| `tests/test-colony-tooling.sh` | Prove local/offline `tsx`, missing-install failure, no dynamic invocation, and no-test failure |
| `verification/manifest.json` | Versioned authoritative list of executable Stage 1A checks |
| `verification/README.md` | Operator contract for manifest schema, runner exits, receipts, platform replay, and adding later-release rows |
| `verification/error-catalog.json` | Versioned committed authority for stable error codes, audiences, templates, remediation, and evidence fields |
| `verification/baseline-inventory.json` | Disposition every observed deterministic/test-integrity failure into 1A, 1B, or 1C |
| `verification/review-state.json` | Record only pre-freeze review history and leave candidate-review fields `PENDING` |
| `verification/review-result.schema.json` | Validate ignored immutable-candidate review results without changing the reviewed commit |
| `scripts/run-verification.py` | Execute argv-only checks and write unmasked, hashed receipts |
| `tests/test_verification_runner.py` | Verify verdict, timeout, zero-test, environment, durability, privacy, containment, and dirty-source semantics |
| `.gitignore` | Ignore root-local `artifacts/` plan-review evidence and `.verification-results/` implementation receipts while retaining committed `verification/` authorities |

## Reuse-First Audit

Before creating any listed file, re-run the broad/targeted searches captured in `artifacts/reuse_scan.txt`, `artifacts/reuse_targeted.txt`, and `artifacts/reuse_audit.md` against the current candidate. A new helper is allowed only when the audit names searched symbols/paths, candidate surfaces, reuse decision, and duplication boundary. Three similar call sites remain inline unless a shared semantic contract is already required by this plan.

| Proposed surface | Existing candidate inspected | Decision and reason |
|---|---|---|
| Dispatcher fixture isolation | `hooks/tests/test-ast-checks.sh` production-byte copy; `colony/clone-manager.test.sh` cleanup trap; `tests/test_pr_s2_injection.sh` side-effect sentinels | Reuse all three patterns; new driver is required to combine failpoint, unreachable tree, and before/after proof |
| `tests/lib/plugin-root.sh` | Script-relative `SCRIPT_DIR` patterns across tests and `hooks/lib/common.sh` | Consolidate five identical checkout-root references; do not couple test root discovery to hook runtime helpers |
| `colony/lib/portable-shell.sh` | Inline `mktemp -d`; clone-manager size calls; hook shell libraries | New Colony-local helper is the smallest shared boundary for two byte sites/three temp sites; hook libs have unrelated runtime semantics |
| `scripts/lib/tmup-discovery.sh` | Current `crossmodel-preflight.sh`; installed tmup manifest; tmup supported scripts | Extract discovery only for fixture testing; do not duplicate or reimplement tmup teardown/lifecycle |
| Metadata/inventory checkers | `claude plugin validate --strict`; repository enumeration; existing frontmatter tests | CLI handles schema, not cross-file authority/count drift; small stdlib checkers cover the missing contract without a framework |
| `colony/run-tsx.sh` | npm local-bin behavior and existing `npx tsx` calls | Wrapper is required to fail before npm/network; do not add a general process launcher |
| Root verification runner | `colony/validation/run-all.sh` and suite-specific scripts | Preserve callable suites; existing runner uses `eval` and lacks true-exit/artifact/verdict contracts, so a root argv-only orchestrator wraps rather than rewrites it |

During implementation, discovering an equivalent existing surface pauses that task for an explicit reuse decision. Rejection based only on preference is invalid. The review checks new symbols with `rg`, semantic overlap with targeted source inspection, and changed-file duplication before each commit; speculative generalization beyond these finite call sites is prohibited.

## Impact Analysis and Blast Radius

Detailed caller search evidence is in `artifacts/blast_callers.txt` and the disposition map is in `artifacts/blast_radius.md`.

| Surface / callers and consumers | Direct and indirect effect | Coordination, containment, rollback |
|---|---|---|
| Four executable test scripts; dispatcher/hook validators copied beneath them | Root resolution and F-01 affect test execution only; production hook behavior must remain byte-identical | Task 1 precedes all root adoption; hashes and v1 exit regressions; local revert commit |
| `colony/clone-manager.sh` direct callers in smoke/tests | Size telemetry becomes 1024-byte-granular positive bytes; physical base comparison accepts legitimate macOS `/var` aliases; unsafe or symlink-redirected session/agent/task destinations fail before mutation | Existing direct callers use compatible safe segments; no pruning authority change; focused clone tests both platforms; revert Task 3 if legitimate compatibility regresses or containment widens |
| `colony/smoke-test.sh` | Three DB temp paths lose `.db` suffix; SQLite does not require the suffix | Helper-only proof in 1A; unsafe shared lock remains isolated and full smoke is 1C |
| `scripts/crossmodel-preflight.sh` consumers in crossmodel workflow | Preflight discovers tmup through manifest and may progress farther than today's false missing result | Fake binaries/state; no live launch or teardown in 1A; manifest/missing/escape negatives; revert Task 4 |
| `.claude-plugin/plugin.json` and marketplace consumed by Claude plugin loader | Plugin manifest remains `10.0.0`; duplicate marketplace version disappears | Two strict validations; no install/reload/deployment in this release; revert metadata commit if schema rejects |
| Repository docs/inventory consumers | Counts/examples become accurate; no runtime agent composition is changed | Checker distinguishes repository/runtime counts; doc-only rollback |
| Colony npm/TypeScript callers and documentation | Dynamic `npx` fetching is replaced by local binary; absent install now fails clearly; zero-test Vitest now fails | Exact lock, offline/missing negatives, typecheck/tests; no global npm install; revert Task 6 |
| New verification manifest/runner and future Stage 1 release plans | Introduces a repository-internal JSON contract and receipt directory; later 1B/1C append rows | Schema mutation tests and version rejection; it wraps suite commands and changes none of their semantics |

No network API/route, database schema/migration, cron, queue, launchd/systemd unit, feature flag, role, or permission policy changes in 1A. No service is installed/enabled and no external dashboard/alert is created; observability is local receipt output only. The trust boundaries are the installed validator (must be unreachable for mutation), tmup-owned plugin/state (read-only discovery), package registry (read only during authorized dependency resolution; offline execution afterward), Linux temp verification directory, and distinct read-only reviewer.

Partial sequence commits are not a deployment: the isolated worktree is not the installed plugin and no branch is pushed. Nevertheless each commit must be internally testable; failure stops before the next dependency and remains visible in Git history. Rollback uses a new scoped local revert/correction commit after preserving evidence. No rollback may restore the hazardous F-01 test, weaken path containment, edit live registry/task state, or claim later-release behavior.

## Error Model and Exception Handling

`artifacts/error_model.md` mirrors this plan-level model. Implementation receipts log the affected `run_id`/`check_id`, class, true exit/signal/timeout, raw evidence paths, containment action, retry count, and terminal verdict. User-visible output states the release/task verdict and actionable boundary; operator-visible stderr/receipts retain exact diagnostics without secrets.

| Error class | Detection | Handling and visible behavior | Retry/idempotency/containment | Required evidence |
|---|---|---|---|---|
| Validation failure | Exact exit/observation/test-count/hash threshold miss | Task `Fail`; stop dependency chain; user sees failed requirement/check ID; operator sees raw output | No blind retry; add regression/minimal correction, new commit/candidate | Raw stdout/stderr, step/row receipt, diff, failing fixture |
| Dependency/contract failure | Missing executable/file, incompatible version/schema, strict validation rejection | Precondition `Blocked` or release `Inconclusive`; no fallback called equivalent | Task 6 alone may install exact locked npm dependency; other changes require plan amendment | Capability probe, versions, attempted argv/exit, contract bytes/hash |
| Network failure | npm metadata/install or SSH/scp nonzero/timeout | Separate acquisition failure from offline execution; user sees unavailable dependency/platform | One bounded retry only when no repository/live-state mutation occurred; otherwise stop | stdout/stderr, destination temp ID, cleanup result, retry count |
| Timeout/signal | Runner wall timeout or negative test signal injection | Process group terminated/killed; partial output retained; verdict `Inconclusive` unless the expected test is the signal assertion itself | One replay on unchanged candidate if classified transient; unique result directory prevents overwrite | timestamps/duration, signal, pid/group action, partial hashes |
| Idempotency/concurrency | Repeated run yields changed source/live hashes, sidecars, colliding result IDs, or divergent verdict | Safety failure; quarantine result from admission | Unique temp roots/run IDs; fixture traps; repeat negative cases; no shared backup names | Before/after hashes, both run receipts, temp-root proof |
| Cleanup/rollback failure | Trap/remote temp cleanup/revert validation nonzero or residue scan finds paths | `Blocked`; preserve residue path/evidence and do not continue | Never escalate cleanup to broader `rm -rf`; owner direction if residue is outside unique temp root | Cleanup command/exit, bounded path, residue listing, candidate status |
| Partial success | Any child row fails/inconclusive while aggregate/other rows pass | Aggregate cannot be `Pass`; user sees all non-pass rows; operator retains every child | Correction targets only owning row; rerun aggregate on new candidate | Full summary and per-row receipt hashes |
| Malformed/stale/mismatched evidence | Parse/hash/candidate/manifest/reviewer identity mismatch | Evidence is not admitted; verdict `Inconclusive`, never reconstructed or silently refreshed | Generate a new receipt from the immutable candidate; retain invalid bytes | Invalid artifact hash/path, rejection reason, replacement lineage |

No queue/dead-letter transport is introduced in 1A. Invalid or partial evidence is effectively quarantined by retaining its bytes and rejection receipt outside admitted `Pass` evidence; 1B owns legacy inbox containment and Stage 3 owns a durable spool/outbox. Retries are serialized, bounded to the task/correction limits, and never change expected thresholds after observing failure.

## Silent-Failure and Degraded-Mode Matrix

`artifacts/silent_failure_matrix.md` is the plan-review copy; Task 7 encodes the executable controls.

| Misleading-success mode | Detection and proving telemetry | Prevention/audit trail |
|---|---|---|
| Swallowed command/subprocess exit | Receipt true exit/signal/timeout differs from expected; raw stderr retained | argv-only direct subprocess; no required pipeline/`|| true`; mismatch is row `Fail` |
| Test helper records failure but returns zero | Final nonzero `FAIL` total plus minimum test count; F-01 uses a real direct assertion | Never use helper return as failpoint proof; aggregate must inspect final count/observation |
| Noop/fallback selects wrong root or tmup entry | Physical root/entry in stdout receipt, invalid/missing/escape negatives | Fallback validates manifest/hooks and remains within canonical root; no old HOME entry probe |
| Partial suite/platform success | Per-row/platform verdict list and aggregate counts | Any mandatory non-pass prevents aggregate `Pass`; macOS cannot stand in for Linux |
| Stale/cached success or prior review | Candidate SHA, manifest-row hash, timestamps, dirty state, reviewer candidate binding | Mismatch rejects evidence; same-reviewer prior passes remain `Inconclusive` |
| Dropped/background work | Runner records child lifecycle and never backgrounds checks; timeout kills group | No asynchronous check is admitted without terminal receipt; 1A has no queue |
| Mismatched health/success signal | Legacy health outputs are inventoried but absent from 1A completion inputs | 1B/Stage 2 adapter owns health classification; 1A runner accepts only manifest receipts |
| Missing log/artifact/alert | Required path/size/hash checks and terminal summary nonzero | Local audit event is mandatory; external alert is unauthorized/not applicable, never silently assumed |
| Success without tests/validation | Test-count regex/explicit observation and `passWithNoTests` negative | Exit zero with zero/no count is `Fail`; no absence-of-error inference |
| Best-effort Colony logging hides write failure | Manifest asserts required clone telemetry entry exists and byte fields parse | Missing log is non-pass for the check; changing runtime logging policy is 1C, not silently fixed in 1A |
| Conditional provider/tool absence | Capability/applicability receipt records exact missing surface | Conditional rows are separate `Inconclusive`/`NOT_APPLICABLE`, never included as green |

Every mode emits a local validation/audit event with `run_id`, `check_id`, candidate, reason, raw evidence references, and verdict. Since external alerting is outside current authority, the operator-visible nonzero summary and retained local audit record are the only alerts claimed. A mode without an implemented detector or required artifact is `Inconclusive` and blocks the dependent claim.

## Error Messaging and Traceability

Every failure writes a stable code from committed `verification/error-catalog.json`; `artifacts/error_catalog.md` is only the pre-implementation review seed and never an operational authority. Operator stderr/receipt shape is:

```text
<CODE> check=<check_id> run=<run_id> candidate=<short-sha> where=<relative-surface> what=<specific failure> evidence=<relative-artifact> remediation=<bounded next action>
```

User-facing summaries name the failed requirement/check, terminal verdict, whether work stopped, and the safe next decision; they do not expose raw environment values, private host aliases/addresses, temp paths containing user data, or untrusted subprocess content. Operator-facing diagnostics may name sanitized repository-relative paths, platform class, true exits/signals, tool versions, and receipt locations. `trace_id` is `null` in 1A; `run_id` plus `check_id` is the required correlation handle.

Required codes include `F01_FIXTURE_ESCAPE`, `F01_INSTALLED_DRIFT`, `F01_FAILPOINT_NOT_REACHED`, `F01_DRIVER_INTERRUPTED`, `F01_TEMP_TREE_HELPER_MISSING`, `F01_PRE_FAILPOINT_CASES_FAILED`, `F01_RESTORE_FAILED`, `F01_INNER_RETAINED`, `F01_INNER_CONTAINER_RETAINED`, `F01_RESTORE_RETAINED`, `ROOT_INVALID`, `PORTABLE_SIZE_INVALID`, `CLONE_IDENTIFIER_INVALID`, `TMUP_MANIFEST_INVALID`, `TMUP_ENTRY_ESCAPE`, `PLUGIN_METADATA_DRIFT`, `INVENTORY_DRIFT`, `LOCAL_TSX_MISSING`, `ZERO_TESTS`, `VERIFY_MANIFEST_INVALID`, `VERIFY_SELECTION_EMPTY`, `VERIFY_RESULTS_ESCAPE`, `VERIFY_ENV_INVALID`, `VERIFY_PLATFORM_MISMATCH`, `VERIFY_EXECUTABLE_DRIFT`, `VERIFY_EXIT_MISMATCH`, `VERIFY_OBSERVATION_FAILED`, `VERIFY_ENCODING_INVALID`, `VERIFY_OUTPUT_LIMIT`, `VERIFY_WRITE_FAILED`, `VERIFY_TIMEOUT`, `VERIFY_INTERRUPTED`, `VERIFY_ARTIFACT_INVALID`, `VERIFY_BACKGROUND_PROCESS`, `VERIFY_SOURCE_DIRTY`, `VERIFY_SOURCE_MUTATION`, `CANDIDATE_MISMATCH`, `PLATFORM_UNAVAILABLE`, `REVIEW_UNAVAILABLE`, and `CLEANUP_FAILED`. `F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP` remains a success-path test marker rather than an error code; every other emitted `F01_*` diagnostic is cataloged. Tests map every runner failure branch to exactly one code and assert that each production-code emitter resolves to exactly one committed catalog entry with audience, message template, remediation, and evidence fields. The drift scanner excludes test strings and declared selectors/markers; unused catalog entries and emitted-but-undefined codes fail.

Generic messages such as `something went wrong`, silent catches, bare stack traces, random IDs, or diagnostics without an evidence path/operator action are invalid. Underlying tool stderr is preserved verbatim only in a hashed raw artifact and referenced from the sanitized catalog message. Redaction must itself be recorded; if safe diagnosis cannot be produced without leaking a protected value, emit the code and artifact hash, omit the value, and mark the dependent verdict `Inconclusive`.

## Plan Acceptance and Task 1 Entry Gate

No implementation file changes before the hardened plan is the sole path in a local commit. Any load-bearing pre-implementation finding requires a second exact plan-only amendment commit under this same gate before Task 1 begins. PlanPrompt `artifacts/` remains untracked review evidence until Task 7 adds root-anchored ignore rules; it is never staged into either commit.

```bash
PLAN='docs/superpowers/plans/2026-07-14-sdlc-os-stage-1a-mechanical-baseline.md'
PLAN_CHECK="$(mktemp)"
set +e
git diff --no-index --check /dev/null "$PLAN" >"$PLAN_CHECK" 2>&1
plan_diff_rc=$?
set -e
test "$plan_diff_rc" -eq 1
test ! -s "$PLAN_CHECK"
rm -f "$PLAN_CHECK"
if rg -n -F "$HOME" "$PLAN"; then exit 1; fi
if rg -n -F "$(hostname -s)" "$PLAN"; then exit 1; fi
if [[ -n "${LINUX_VERIFY_HOST:-}" ]] && rg -n -F "$LINUX_VERIFY_HOST" "$PLAN"; then exit 1; fi
if [[ -n "${PLANPROMPT_ROOT:-}" ]] && rg -n -F "$PLANPROMPT_ROOT" "$PLAN"; then exit 1; fi
git status --porcelain --untracked-files=no
git add -- "$PLAN"
test "$(git diff --cached --name-only)" = "$PLAN"
git diff --cached --check
git diff --cached -- "$PLAN"
git commit -m "${PLAN_COMMIT_MESSAGE:-docs: plan Stage 1A mechanical baseline}"
test "$(git show --format= --name-only HEAD | sed '/^$/d')" = "$PLAN"
git status --porcelain --untracked-files=no
```

Expected: tracked state is clean before and after; the commit contains exactly the plan; review artifacts remain untracked; no hook is bypassed; no remote action occurs. The initial plan commit uses the default message; a later plan-only amendment sets `PLAN_COMMIT_MESSAGE='docs: amend Stage 1A Task 1 isolation gate'`. Any additional staged path, whitespace failure, hook failure, private-locator match, or tracked-state change blocks Task 1. Before the commit, scan the plan and require zero matches for machine-local username, private host alias/address, absolute worktree, and absolute skill-home paths.

---

### Task 1: Disarm F-01 Atomically With the First Root Resolver

**Files:**
- Create: `tests/lib/plugin-root.sh`
- Create: `tests/lib/f01-temp-tree.py`
- Create: `tests/test-sdlc-dispatch-isolation.sh`
- Modify: `tests/test-sdlc-dispatch.sh`
- Test: `tests/test-sdlc-dispatch-isolation.sh`

**Interfaces:**
- Consumes: caller path from `${BASH_SOURCE[0]}`, optional `CLAUDE_PLUGIN_ROOT`, and canonical Python 3.12.
- Produces: `resolve_plugin_root <caller-script>` on stdout; `f01-temp-tree.py capture|remove <root> <allowed-prefix> [token]`; dispatcher failpoint `SDLC_TEST_FAILPOINT=after-validator-swap`; optional outer selectors `F01_TEST_MODE=assert|concurrent|restore-failure|cleanup-retarget|signal-wrapper-negative|admission-negative` and `F01_TEST_SIGNAL=HUP|INT|TERM`; fixed test-only selectors `SDLC_TEST_RESTORE_FAILURE=after-backup-move|remove-backup`, `SDLC_TEST_PRE_FAILPOINT_FAILURE=synthetic`, `F01_TEST_INSTALLED_DRIFT=synthetic`, `F01_TEST_CONCURRENT_OUTCOMES=1,3`, `F01_TEST_OUTER_ROOT_DRIFT=rename`, `F01_TEST_INNER_CAPTURE_FAILURE=1`, `F01_TEMP_TREE_TEST_POST_OPEN_SWAP=1`, and `F01_TEMP_TREE_TEST_CAPTURE_FAILURE=1`; exact marker `F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:<fixture-path>` on stderr.

- [ ] **Step 1: Add the safe outer regression driver before touching the hazardous test**

  First add `tests/lib/f01-temp-tree.py` as a Python 3.12-only CLI, and require the regular non-symlink helper before either shell driver creates a root it must later delete. `capture` requires an absolute non-root directory whose raw leaf begins with the fixed caller-supplied prefix, traverses its physical parent from `/` using `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, and emits a versioned token containing the raw leaf plus parent/root device and inode. `remove` strictly parses that token, rejects duplicate JSON members and unknown/missing keys, repeats the no-follow traversal, opens and `fstat`-matches the captured root, and recursively clears entries only through held no-follow directory descriptors. Each child directory is opened and identity-checked before recursion; a changed entry causes nonzero retention rather than a fresh recursive lookup. Immediately before recursion, revalidate that the original parent leaf still names the opened root; after clearing, repeat that check and use only nonrecursive `os.rmdir(..., dir_fd=parent_fd)`. A deterministic test-only post-open swap hook must prove both original and replacement sentinels remain, while the ancestor-retarget falsifier must preserve both original and victim sentinels. Portable POSIX/Python has no atomic expected-inode recursive-delete primitive against a hostile same-UID renamer; that actor is outside this test-fixture threat model because it can directly mutate all protected owner files. Unique roots are mode `0700`, unexplained concurrent drift is non-pass, and no claim of sandboxing a malicious same-UID process is made.

  Create `tests/test-sdlc-dispatch-isolation.sh` with `umask 077`, an outer `mktemp -d` trap, signal handlers, and a retained child PID. `F01_TEST_MODE=concurrent` is a bounded orchestration mode that launches exactly two child driver processes with `F01_TEST_MODE=assert`, retains both exits and raw artifacts, rejects recursive concurrent mode, and emits an aggregate pass only when both isolated drivers pass. A conclusive nonzero/non-3 child exit is evaluated before installed-drift exit `3`, so mixed `(1,3)`/`(3,1)` results are `FAIL`, never demoted to `INCONCLUSIVE`. In `assert` mode, before execution, create and physically verify isolated `home`, `runtime`, `project`, `evidence`, and decoy directories beneath the unique outer root. The driver creates `$DECOY_ROOT/tests/lib` and `$DECOY_ROOT/.claude-plugin`, copies `tests/test-sdlc-dispatch.sh`, `.claude-plugin/plugin.json`, `hooks/`, and `scripts/`, and copies the contents of source `tests/lib/` only when that directory exists. This conditional setup is required because the behavioral-red Step 2 precedes creation of `tests/lib/plugin-root.sh`; the manifest is unconditional because Step 3's resolver requires it. A missing copied dependency, isolated directory, physical-containment check, optional source-directory handling error, or symlink in a copied dependency tree is a setup failure and cannot count as the red proof.

  Require source and decoy validators to be existing regular non-symlink files with distinct canonical roots and inodes; freeze installed applicability before launch and require the same file properties when present. Store all evidence outside source, decoy, and installed roots. Snapshot raw bytes, mode, size, SHA-256, and versioned sorted sidecar inventories for the source validator, decoy validator, and `${SDLC_INSTALLED_PLUGIN_ROOT:-$HOME/.claude/plugins/sdlc-os}/hooks/validators/safety-constraints.sh`, using canonical Python 3.12 rather than host-specific `shasum`/`sha256sum`. A sidecar is every same-directory raw basename that begins with the exact validator basename but is not the validator itself; hex-encoded names, type, mode, size, and content or link-target digest are strictly parsed, and header-only output is the sole valid empty inventory. The driver mutates one dotless decoy-only associated entry and requires the detector to reject it before restoring the baseline. Launch only the copied test as a retained child from the physical isolated project directory under an empty environment with isolated `HOME`, `TMPDIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PROJECT_DIR`, the direct failpoint, and optional signal selector; capture stdout, stderr, and true wait status without a pipeline. The installed snapshot is required on the owner host and may be evidence-backed `NOT_APPLICABLE` only when absence was frozen before launch; disappearance or type drift afterward is `INCONCLUSIVE`.

  The decisive assertions are:

  ```bash
  case "${F01_TEST_SIGNAL:-}" in
    "") EXPECTED_CHILD_EXIT=1 ;;
    HUP) EXPECTED_CHILD_EXIT=129 ;;
    INT) EXPECTED_CHILD_EXIT=130 ;;
    TERM) EXPECTED_CHILD_EXIT=143 ;;
    *) exit 64 ;;
  esac
  run_copied_child() {
    (
      cd "$OUTER_ROOT/project"
      exec env -i \
        PATH="$PATH" \
        HOME="$OUTER_ROOT/home" \
        TMPDIR="$OUTER_ROOT/runtime" \
        CLAUDE_PLUGIN_ROOT="$DECOY_ROOT" \
        CLAUDE_PROJECT_DIR="$OUTER_ROOT/project" \
        SDLC_TEST_FAILPOINT=after-validator-swap \
        SDLC_TEST_SIGNAL="${F01_TEST_SIGNAL:-}" \
        /bin/bash "$DECOY_ROOT/tests/test-sdlc-dispatch.sh"
    )
  }
  set +e
  if [[ "${F01_TEST_SIGNAL:-}" == "INT" ]]; then
    run_copied_child >"$STDOUT_FILE" 2>"$STDERR_FILE"
    child_rc=$?
  else
    set -m
    run_copied_child >"$STDOUT_FILE" 2>"$STDERR_FILE" &
    CHILD_PID=$!
    set +m
    wait "$CHILD_PID"
    child_rc=$?
    CHILD_PID=""
  fi
  set -e

  installed_drift=0
  cmp -s "$SOURCE_SNAPSHOT" "$SOURCE_VALIDATOR" || exit 1
  cmp -s "$DECOY_SNAPSHOT" "$DECOY_VALIDATOR" || exit 1
  cmp -s "$SOURCE_SIDECARS_BEFORE" "$SOURCE_SIDECARS_AFTER" || exit 1
  cmp -s "$DECOY_SIDECARS_BEFORE" "$DECOY_SIDECARS_AFTER" || exit 1
  if [[ "$INSTALLED_APPLICABLE" == "1" ]] &&
      { ! cmp -s "$INSTALLED_SNAPSHOT" "$INSTALLED_VALIDATOR" ||
        ! cmp -s "$INSTALLED_SIDECARS_BEFORE" "$INSTALLED_SIDECARS_AFTER"; }; then
    printf 'F01_INSTALLED_DRIFT: concurrent installed-tree change; evidence inconclusive\n' >&2
    installed_drift=1
  fi
  [[ ! -s "$STDOUT_FILE" ]] || exit 1
  marker_count="$(awk '/^F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:/ { count++ } END { print count + 0 }' "$STDERR_FILE")"
  [[ "$marker_count" -eq 1 ]] || exit 1
  marker="$(sed -n 's/^F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP://p' "$STDERR_FILE")"
  case "$marker" in "$OUTER_ROOT/runtime"/*/hooks/validators/safety-constraints.sh) ;; *) exit 1 ;; esac
  EXPECTED_STDERR="$EVIDENCE_ROOT/expected-child.stderr"
  printf 'F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:%s\n' "$marker" >"$EXPECTED_STDERR"
  cmp -s "$EXPECTED_STDERR" "$STDERR_FILE" || exit 1
  [[ "$child_rc" -eq "$EXPECTED_CHILD_EXIT" ]] || exit 1
  [[ "$installed_drift" -eq 0 ]] || exit 3
  ```

  Source/decoy protected-state failures are conclusive and stop immediately. Installed drift is recorded before marker/result admission but returned as exit `3` only after exact child stdout, stderr, marker, path, and exit checks; therefore a conclusive child/stream failure cannot be demoted to `INCONCLUSIVE`. Before moving the validator, the inner script requires exactly eight passed pre-swap cases and zero failures; a fixed synthetic failure must stop before the marker. For an admitted direct/signal row, child stdout must be empty and child stderr must equal the one marker line byte-for-byte, not merely contain it. When the marker is absent, require evidence that child execution reached the isolated legacy lookup and emit exactly `F01_FAILPOINT_NOT_REACHED child_exit=1`; any other setup/red signature is rejected. Direct assertion must exit exactly `1` with empty child stdout; self-signals after the swap must exit `129`, `130`, and `143` for `HUP`, `INT`, and `TERM`. The outer INT row and its copied child both execute synchronously in the foreground with raw-file redirection; direct/HUP/TERM retain a monitor-mode child for interruption handling. `signal-wrapper-negative` deliberately backgrounds a fresh outer INT process and must reproduce the known non-pass signature before a separate foreground INT run passes. `admission-negative` supervises the synthetic pre-failpoint failure, synthetic installed drift combined with that conclusive child failure, mixed `(1,3)` concurrency, renamed outer root, and forced inner capture-failure falsifiers. Any `Results:` line or other child stdout proves execution continued beyond the failpoint and fails admission. An outer interruption terminates and waits for its retained child, emits `F01_DRIVER_INTERRUPTED`, and exits `3` without a pass marker. Source or decoy mutation is `FAIL`; installed-tree drift alone is exit `3`/`INCONCLUSIVE` because the child has no installed path or handle and concurrent external drift cannot be attributed to it. The driver must never run the original hazardous script in place.

- [ ] **Step 2: Run the safe driver and verify the expected red state**

  Run:

  ```bash
  /bin/bash -n tests/test-sdlc-dispatch-isolation.sh
  /bin/bash tests/test-sdlc-dispatch-isolation.sh
  ```

  Expected: syntax check exits `0`; driver reaches child execution from the isolated physical project and exits nonzero with exact diagnostic `F01_FAILPOINT_NOT_REACHED child_exit=1` because the copied current test ignores `CLAUDE_PLUGIN_ROOT` and aborts on the isolated nonexistent legacy path. Missing manifest, missing `tests/lib` handling, wrong CWD, uncreated directory, symlink, or any other setup failure is rejected. Source and decoy fingerprints remain unchanged; installed drift, if observed, is recorded separately as `INCONCLUSIVE`.

- [ ] **Step 3: Implement the shared root resolver**

  Create `tests/lib/plugin-root.sh` with this contract:

  ```bash
  resolve_plugin_root() {
    local caller="${1:?resolve_plugin_root: caller script required}"
    local candidate canonical
    if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
      candidate="$CLAUDE_PLUGIN_ROOT"
    else
      candidate="$(dirname "$caller")/.."
    fi
    if ! canonical="$(cd "$candidate" 2>/dev/null && pwd -P)"; then
      printf 'ROOT_INVALID:invalid SDLC-OS plugin root: %s\n' "$candidate" >&2
      return 1
    fi
    candidate="$canonical"
    if [[ ! -f "$candidate/.claude-plugin/plugin.json" ||
          -L "$candidate/.claude-plugin/plugin.json" ||
          ! -d "$candidate/hooks" || -L "$candidate/hooks" ]]; then
      printf 'ROOT_INVALID:invalid SDLC-OS plugin root: %s\n' "$candidate" >&2
      return 1
    fi
    printf '%s\n' "$candidate"
  }
  ```

  Keep it Bash 3.2-compatible and free of mutation.

- [ ] **Step 4: Refactor the dispatcher test into an unreachable installed-tree boundary**

  In `tests/test-sdlc-dispatch.sh`, source the helper relative to the physical test script, resolve `SOURCE_ROOT`, then create and physically contain `TMPROOT`, `FIXTURE_ROOT`, isolated `HOME`, and `WORK_ROOT`. Copy `hooks/` and `scripts/` into `FIXTURE_ROOT`, reject symlinks in copied dependency trees, and set `DISPATCH` and `FIXTURE_VALIDATOR` only beneath that copied root. Require source and fixture validators to be existing regular non-symlink files before proving distinct canonical roots and inodes. Save a fixture-validator byte baseline before the first swap.

  Replace the fixed sidecars with files under `TMPROOT`. Before the first swap, require both:

  ```bash
  [[ "$FIXTURE_VALIDATOR" != "$SOURCE_VALIDATOR" ]]
  [[ ! "$FIXTURE_VALIDATOR" -ef "$SOURCE_VALIDATOR" ]]
  ```

  Install signal-to-exit traps plus an `EXIT` cleanup that preserves the original status, restores and byte-verifies a fixture backup before deleting the temp tree, and cannot recurse. Capture the helper token immediately after each temp root is physically resolved. Every restore/remove operation is handled explicitly rather than relying on `errexit`; `record_restore_failure` latches `RESTORE_FAILED=1` and `PRESERVE_TMPROOT=1` before emitting `F01_RESTORE_FAILED`. Once latched, cleanup makes no further restore or deletion attempt and exits `125`. Successful cleanup delegates only to the captured-token Python helper; raw `rm -rf "$TMPROOT"` and `rm -rf "$OUTER_ROOT"` are prohibited:

  ```bash
  cleanup() {
    local rc=$?
    trap - EXIT HUP INT TERM
    if [[ "$RESTORE_FAILED" -eq 0 && -n "${BACKUP_VALIDATOR:-}" ]]; then
      if [[ ! -f "$BACKUP_VALIDATOR" || -L "$BACKUP_VALIDATOR" ]] ||
          ! rm -f "$FIXTURE_VALIDATOR" ||
          ! mv "$BACKUP_VALIDATOR" "$FIXTURE_VALIDATOR" ||
          ! cmp -s "$FIXTURE_BASELINE" "$FIXTURE_VALIDATOR"; then
        record_restore_failure
      fi
    fi
    if [[ "$PRESERVE_TMPROOT" -ne 0 ]]; then
      exit 125
    fi
    if ! "$PYTHON_BIN" "$TEMP_TREE_HELPER" remove \
        "$TMPROOT" sdlc-dispatch-test. "$TMPROOT_TOKEN"; then
      printf 'CLEANUP_FAILED:%s\n' "$TMPROOT" >&2
      printf 'F01_INNER_RETAINED:%s\n' "$TMPROOT" >&2
      exit 125
    fi
    exit "$rc"
  }
  trap cleanup EXIT
  trap 'exit 129' HUP
  trap 'exit 130' INT
  trap 'exit 143' TERM
  ```

  The outer driver applies the same identity-checked descriptor-held removal to its root whenever its captured-root obligation is nonempty; it never skips helper verification merely because the lexical path is missing or no longer a directory. Immediately after `wait`, before any other admission or early return, it recognizes exactly one bounded `F01_INNER_RETAINED` or `F01_RESTORE_FAILED` marker, latches `PRESERVE_OUTER_ROOT=1`, emits the corresponding `F01_INNER_CONTAINER_RETAINED:<outer-root>` or `F01_RESTORE_RETAINED:<outer-root>`, and exits `125`; malformed or duplicate markers also preserve and fail closed. Inner token-capture failure emits the bounded retained-root marker before any trap exists, and token-removal failure emits it with `CLEANUP_FAILED`. `F01_TEST_MODE=restore-failure` is a supervising controller: it creates and token-captures a physical grandparent, runs both a corrupted-baseline and removed-backup case beneath that grandparent, then proves both retained roots exist after each failing process exits with source/decoy/installed state unchanged. The controller accepts each retained path only when no-follow traversal and the grandparent token prove it is a direct descendant, captures a fresh helper token whose parent identity equals that grandparent token, removes the retained root through the helper, and confirms the grandparent contains no unexpected entry. No exited child token is assumed or transmitted. `F01_TEST_MODE=cleanup-retarget` runs duplicate-token, missing-helper-before-root, ancestor-retarget, and deterministic post-open root-swap falsifiers; every required original/replacement/victim sentinel remains. The same mode normalizes shell line continuations and rejects any `rm` command in the two production test scripts whose argv contains `-r`, `-R`, or `--recursive`, plus indirect cleanup command dispatch; there is no raw-recursive-delete allowlist.

  Invoke every dispatcher child from `(cd "$WORK_ROOT" && ...)` with a minimal `env -i`, controlled `PATH`, `HOME="$ISOLATED_HOME"`, `TMPDIR="$TMPROOT/runtime"`, `CLAUDE_PLUGIN_ROOT="$FIXTURE_ROOT"`, and `CLAUDE_PROJECT_DIR="$WORK_ROOT"`. After the first fixture validator moves to its temp backup, emit the marker once, optionally self-send the allowlisted `SDLC_TEST_SIGNAL`, then execute `/usr/bin/false` when no signal was requested. Apple Bash 3.2 does not apply `errexit` to a false `[[ ... ]]` conditional command, so `[[ 1 -eq 0 ]]` is prohibited as this failpoint. The unreachable explicit exit keeps any future unexpected `errexit` suppression non-green:

  ```bash
  if [[ "$PASS" -ne 8 || "$FAIL" -ne 0 ]]; then
    printf 'F01_PRE_FAILPOINT_CASES_FAILED:pass=%s fail=%s\n' "$PASS" "$FAIL" >&2
    exit 1
  fi
  BACKUP_VALIDATOR="$BACKUP_ROOT/safety-constraints.original"
  mv "$FIXTURE_VALIDATOR" "$BACKUP_VALIDATOR"
  if [[ "${SDLC_TEST_FAILPOINT:-}" == "after-validator-swap" ]]; then
    printf 'F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:%s\n' \
      "$FIXTURE_VALIDATOR" >&2
    if [[ -n "${SDLC_TEST_SIGNAL:-}" ]]; then
      case "$SDLC_TEST_SIGNAL" in HUP|INT|TERM) ;; *) exit 64 ;; esac
      kill -s "$SDLC_TEST_SIGNAL" "$$"
      exit 125
    fi
    /usr/bin/false
    exit 125
  fi
  ```

  Keep all expected legacy exits unchanged. A helper-recorded mismatch still increments `FAIL` and returns normally; the failpoint deliberately tests the actual `errexit` window.

- [ ] **Step 5: Run the F-01 proof and focused dispatcher suite**

  Run:

  ```bash
  /bin/bash -n tests/lib/plugin-root.sh tests/test-sdlc-dispatch.sh tests/test-sdlc-dispatch-isolation.sh
  python3.12 -m py_compile tests/lib/f01-temp-tree.py
  SDLC_INSTALLED_PLUGIN_ROOT="$HOME/.claude/plugins/sdlc-os" /bin/bash tests/test-sdlc-dispatch-isolation.sh
  for signal in HUP INT TERM; do
    F01_TEST_SIGNAL="$signal" \
      SDLC_INSTALLED_PLUGIN_ROOT="$HOME/.claude/plugins/sdlc-os" \
      /bin/bash tests/test-sdlc-dispatch-isolation.sh
  done
  F01_TEST_MODE=concurrent /bin/bash tests/test-sdlc-dispatch-isolation.sh
  F01_TEST_MODE=signal-wrapper-negative /bin/bash tests/test-sdlc-dispatch-isolation.sh
  F01_TEST_MODE=cleanup-retarget /bin/bash tests/test-sdlc-dispatch-isolation.sh
  F01_TEST_MODE=restore-failure /bin/bash tests/test-sdlc-dispatch-isolation.sh
  F01_TEST_MODE=admission-negative /bin/bash tests/test-sdlc-dispatch-isolation.sh
  CLAUDE_PLUGIN_ROOT="$PWD" /bin/bash tests/test-sdlc-dispatch.sh
  ```

  Expected: direct and three signal modes report the one forced marker beneath their runtime temp roots with exact child exits `1/129/130/143`; every failpoint child has empty stdout and exactly one marker-only stderr line, so no `Results:` or pre-swap failure is admitted. The INT outer command and copied child must both execute in the foreground with direct raw stdout/stderr files; the deliberate background-wrapper negative must reproduce exit `125` without being admitted as the INT row, then the separate foreground INT row must pass. Two concurrent drivers use distinct roots and both pass; the `(1,3)` counterexample returns failure rather than inconclusive. Source/decoy snapshots and complete versioned sidecar inventories are byte-identical; installed bytes are unchanged when applicable; the dotless sidecar falsifier is detected. Missing/duplicate helper tokens and missing helper ordering fail closed; ancestor/post-open drift preserves every asserted sentinel; both restore variants retain both bounded trees; renamed outer and forced inner-capture failures retain inspectable bounded evidence and exit `125`; the normalized source-policy gate finds zero direct or indirect raw recursive-delete commands; and the separate normal dispatcher suite reports exactly `Results: 11 passed, 0 failed`. Exit `3` is retained as `INCONCLUSIVE`, never coerced to green. Task 8 separately attacks an external interruption of the outer driver, including bounded TERM→KILL behavior; Task 1 does not infer that result from inner self-signals.

- [ ] **Step 6: Inspect and commit the atomic F-01/root change**

  Run:

  ```bash
  git diff --check
  git diff -- tests/lib/plugin-root.sh tests/lib/f01-temp-tree.py tests/test-sdlc-dispatch-isolation.sh tests/test-sdlc-dispatch.sh
  git status --short
  git add tests/lib/plugin-root.sh tests/lib/f01-temp-tree.py tests/test-sdlc-dispatch-isolation.sh tests/test-sdlc-dispatch.sh
  git diff --cached --check
  git commit -m "test: isolate dispatcher validator fixtures"
  ```

  Expected: local commit succeeds with exactly the four Task 1 paths; no installed validator or sidecar changed; no other file is staged.

### Task 2: Make All Four Checkout-Bound Tests Relocatable

**Files:**
- Create: `tests/test-plugin-root-resolution.sh`
- Modify: `tests/benchmark-dispatch.sh`
- Modify: `tests/test-validator-shims.sh`
- Modify: `tests/test-fixture-regression.sh`
- Test: `tests/test-plugin-root-resolution.sh`

**Interfaces:**
- Consumes: `resolve_plugin_root <caller-script>` from Task 1.
- Produces: zero executable occurrences of literal `$HOME/LAB/sdlc-os`; `BENCHMARK_ITERATIONS` defaults to the existing count and permits a bounded relocated smoke run.

- [ ] **Step 1: Write root-resolution and relocated-checkout tests**

  Add cases that copy the committed source tree into a directory containing spaces, then prove:

  ```bash
  explicit="$(CLAUDE_PLUGIN_ROOT="$RELOCATED_ROOT" resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
  [[ "$explicit" == "$(cd "$RELOCATED_ROOT" && pwd -P)" ]]

  fallback="$(unset CLAUDE_PLUGIN_ROOT; resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
  [[ "$fallback" == "$(cd "$RELOCATED_ROOT" && pwd -P)" ]]

  ln -s "$RELOCATED_ROOT" "$TMPROOT/plugin-link"
  symlinked="$(CLAUDE_PLUGIN_ROOT="$TMPROOT/plugin-link" \
    resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
  [[ "$symlinked" == "$(cd "$RELOCATED_ROOT" && pwd -P)" ]]

  if CLAUDE_PLUGIN_ROOT="$TMPROOT/not-a-plugin" \
      resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh"; then
    exit 1
  fi
  ```

  Run all four relocated scripts with isolated `HOME` and `CLAUDE_PLUGIN_ROOT="$RELOCATED_ROOT"`; set `BENCHMARK_ITERATIONS=1` for the benchmark. Finish with `rg -n -F '$HOME/LAB/sdlc-os'` over the four executable files and fail on any match.

- [ ] **Step 2: Run the new test and verify it fails for the remaining three scripts**

  Run `bash tests/test-plugin-root-resolution.sh`.

  Expected: explicit/fallback/symlink/invalid helper cases pass, then the relocated validator-shim or fixture script exits `127` because it still uses the checkout-bound path.

- [ ] **Step 3: Adopt the shared resolver without changing assertions**

  At the top of each remaining script, compute `TEST_DIR` physically, source `tests/lib/plugin-root.sh`, and set paths from `PLUGIN_ROOT`:

  ```bash
  TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  source "$TEST_DIR/lib/plugin-root.sh"
  PLUGIN_ROOT="$(resolve_plugin_root "${BASH_SOURCE[0]}")"
  DISPATCH="$PLUGIN_ROOT/hooks/sdlc-dispatch.sh"
  ```

  For `test-validator-shims.sh`, derive `HOOKS_DIR="$PLUGIN_ROOT/hooks/scripts"`. For `benchmark-dispatch.sh`, introduce `ITERATIONS="${BENCHMARK_ITERATIONS:-100}"` and replace only the loop bound.

- [ ] **Step 4: Prove relocated execution and zero old literals**

  Run:

  ```bash
  bash -n tests/lib/plugin-root.sh tests/benchmark-dispatch.sh tests/test-validator-shims.sh tests/test-fixture-regression.sh tests/test-plugin-root-resolution.sh
  bash tests/test-plugin-root-resolution.sh
  CLAUDE_PLUGIN_ROOT="$PWD" bash tests/test-validator-shims.sh
  CLAUDE_PLUGIN_ROOT="$PWD" bash tests/test-fixture-regression.sh
  if rg -n -F '$HOME/LAB/sdlc-os' tests/benchmark-dispatch.sh tests/test-validator-shims.sh tests/test-fixture-regression.sh tests/test-sdlc-dispatch.sh; then exit 1; fi
  ```

  Expected: root-resolution suite passes; validator shims report `14/14`; fixture regression reports `13/13`; literal scan emits nothing.

- [ ] **Step 5: Commit the relocatability change**

  ```bash
  git diff --check
  git add tests/benchmark-dispatch.sh tests/test-validator-shims.sh tests/test-fixture-regression.sh tests/test-plugin-root-resolution.sh
  git diff --cached --check
  git commit -m "test: make plugin checks relocatable"
  ```

### Task 3: Make Colony Shell Boundaries Portable and Contained

**Files:**
- Create: `colony/lib/portable-shell.sh`
- Create: `tests/test-portable-shell-helpers.sh`
- Modify: `colony/clone-manager.sh`
- Modify: `colony/clone-manager.test.sh`
- Modify: `colony/smoke-test.sh`
- Modify: `colony/README.md`

**Interfaces:**
- Produces: `path_size_bytes <existing-path>` printing a positive integer equal to `du -sk` kibibytes multiplied by `1024`; `make_temp_file <prefix>` printing a unique file inside `${TMPDIR:-/tmp}`.
- Produces: `_validate_colony_identifier <kind> <value>` accepting only one safe `[A-Za-z0-9][A-Za-z0-9._-]*` path segment and returning `64`/`CLONE_IDENTIFIER_INVALID` before any filesystem mutation otherwise.
- Preserves: telemetry fields remain named `clone_bytes` and `output_bytes`; no pruning semantics change.

- [ ] **Step 1: Add failing portable-helper and canonical-path cases**

  `tests/test-portable-shell-helpers.sh` must create an isolated `TMPDIR`, source the planned helper, and assert positive integer byte output for a nonempty directory, a unique temp file, and no GNU-only literal in `clone-manager.sh` or `smoke-test.sh`.

  Extend `colony/clone-manager.test.sh` so `COLONY_BASE` uses the lexical `/var/...` spelling when its physical path is `/private/var/...` on macOS, then require valid-clone verification and pruning to succeed. Strengthen telemetry assertions to require both a positive `clone_bytes` and positive recovered `output_bytes`.

  Add table-driven session, agent, and task identifier cases for empty/missing, `..`, `../outside`, embedded `/`, and newline. Begin with a nonexistent `COLONY_BASE` for the empty/invalid cases; require exit `64`, exact `CLONE_IDENTIFIER_INVALID`, and that `_ensure_colony_base` was never reached. Keep all later cases inside one outer temporary root; fingerprint the base and outer sentinel before each call; require no created/copied path anywhere outside the base. The red is safe because even the vulnerable destination remains inside the outer disposable root and cleanup removes that root only.

  Add pre-existing symlink attacks for `$COLONY_BASE/<session>` and `$COLONY_BASE/recovered-outputs`, both pointing to an outer sentinel directory. Require rejection before `git clone`/`cp` and byte-identical sentinels. Add positive compatibility cases for every direct caller literal (`test-session`, `agent-1`, `agent-prune`, `agent-recover`, `agent-empty`, `task-recover-001`, `task-empty-001`, `smoke-session`, `agent1`) plus allowed `a.b` and `a_b` boundaries.

- [ ] **Step 2: Run focused tests and capture the known red evidence**

  Run:

  ```bash
  bash tests/test-portable-shell-helpers.sh
  bash colony/clone-manager.test.sh
  ```

  Expected: helper test fails because the file does not exist and GNU literals remain; clone manager reports the reproduced `du: invalid option -- b`, lexical/physical path failures on macOS, and at least one controlled traversal side effect inside the outer disposable root. Preserve that red path/fingerprint before cleanup; no live Colony path is reachable.

- [ ] **Step 3: Implement the two portable primitives**

  Create `colony/lib/portable-shell.sh`:

  ```bash
  path_size_bytes() {
    local target="${1:?path_size_bytes: path required}"
    local line kib
    line="$(du -sk "$target")" || return 1
    kib="${line%%[[:space:]]*}"
    [[ "$kib" =~ ^[0-9]+$ ]] || return 1
    printf '%s\n' "$((kib * 1024))"
  }

  make_temp_file() {
    local prefix="${1:-sdlc-os}"
    [[ "$prefix" =~ ^[A-Za-z0-9._-]+$ ]] || return 64
    mktemp "${TMPDIR:-/tmp}/${prefix}.XXXXXX"
  }
  ```

  Source it by physical script path from clone manager and smoke test. Replace both `du -sb ... | cut -f1` sites with separate declaration/assignment calls to `path_size_bytes`. Replace all three `mktemp --suffix=.db` calls with `make_temp_file sdlc-colony-db`.

- [ ] **Step 4: Validate identifiers before mutation and canonicalize the clone safety boundary**

  Add a private Bash 3.2-compatible validator. Capture `session_name`, `agent_id`, and `task_id` with `${n-}` rather than `${n:?}` so empty/missing input reaches the validator and obeys the promised exit/code. Call it at the start of `colony_clone_create` and `colony_clone_recover_output`, before `_ensure_colony_base`, `mkdir`, `git clone`, or `cp`:

  ```bash
  _validate_colony_identifier() {
    local kind="${1:?identifier kind required}"
    local value="${2-}"
    if [[ ! "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
      printf 'CLONE_IDENTIFIER_INVALID kind=%s remediation=use-one-safe-path-segment\n' \
        "$kind" >&2
      return 64
    fi
  }
  ```

  Existing in-repository callers use compatible identifiers. Document the public argument grammar in `colony/README.md`. Do not normalize, truncate, or replace rejected input; fail before mutation so two different identifiers cannot alias one path.

  Add one private helper that creates and physically resolves `COLONY_BASE`, then compare both clone and base physical paths:

  ```bash
  _resolved_colony_base() {
    _ensure_colony_base
    (cd "$COLONY_BASE" && pwd -P)
  }
  ```

  In `colony_clone_create`, derive the one-segment session path beneath `base_dir`, reject it when it is a symlink, create it only after that check, physically resolve it beneath `base_dir`, and construct the clone path from that physical parent. Reject a pre-existing clone path or symlink. In `colony_clone_recover_output`, apply the same sequence to fixed `recovered-outputs` and the one-segment task directory, then copy only through the physically contained task parent. The physical-parent value, not the original lexical spelling, is the mutation target.

  In `colony_clone_verify` and `colony_clone_prune`, resolve `base_dir="$(_resolved_colony_base)"` and use `case "$resolved_dir/" in "$base_dir"/*) ...`. Preserve all current refusal conditions and log fields. The test records the residual same-user replacement race as non-exploitable within mode-`0700` serialized fixtures; any observed concurrent parent drift is `INCONCLUSIVE` and stops the check.

- [ ] **Step 5: Run focused macOS checks**

  ```bash
  bash -n colony/lib/portable-shell.sh colony/clone-manager.sh colony/clone-manager.test.sh colony/smoke-test.sh tests/test-portable-shell-helpers.sh
  bash tests/test-portable-shell-helpers.sh
  bash colony/clone-manager.test.sh
  if rg -n 'du -sb|mktemp --suffix' colony/clone-manager.sh colony/smoke-test.sh; then exit 1; fi
  ```

  Expected: helper suite passes; clone manager reports the updated explicit nonzero test count with zero failures; both byte fields are positive; every invalid identifier exits `64` before base creation; symlink attacks and traversal change no outer sentinel or path; all named compatibility literals pass; literal scan is empty. Do not run the full smoke suite yet because its shared `/tmp/sdlc-colony-conductor.lock` fixture is assigned to 1C containment.

- [ ] **Step 6: Reproduce platform-sensitive checks on the owner-authorized Linux host**

  Resolve `LINUX_VERIFY_HOST` from owner-local inventory. Stage only the six Task 3 paths, create an exact candidate tree with `tree_id="$(git write-tree)"`, and produce `git archive "$tree_id"` plus its SHA-256. Copy that archive to a unique remote `/tmp` directory, verify the archive SHA-256 there, extract it, run only `tests/test-portable-shell-helpers.sh` and `colony/clone-manager.test.sh`, capture true exits/stdout/stderr, then remove only that unique remote directory. The local receipt binds `tree_id` to the archive digest; the extracted archive has no Git object database and must not claim to recompute the tree ID remotely. Expected: both commands exit `0`, traversal/symlink negatives have zero outside-base effects, compatibility literals pass, byte telemetry is positive, and local/remote archive digests match. If SSH, copy, digest, cleanup, or either command fails, record `INCONCLUSIVE` rather than green. Leave the exact scoped index staged for Step 7; do not stage any review artifact or unrelated path.

- [ ] **Step 7: Commit the portability change**

  ```bash
  git diff --check
  git diff --cached -- colony/lib/portable-shell.sh colony/clone-manager.sh colony/clone-manager.test.sh colony/smoke-test.sh colony/README.md tests/test-portable-shell-helpers.sh
  git diff --cached --check
  git commit -m "fix: make colony shell helpers portable"
  ```

### Task 4: Discover tmup From Its Declared Plugin Entry

**Files:**
- Create: `scripts/lib/tmup-discovery.sh`
- Create: `tests/test-crossmodel-preflight.sh`
- Modify: `scripts/crossmodel-preflight.sh`

**Interfaces:**
- Consumes: optional `TMUP_PLUGIN_ROOT`; otherwise candidate roots are sibling `tmup`, `$HOME/.claude/plugins/tmup`, and `$HOME/.local/share/tmup`.
- Produces: `discover_tmup_entry <tmup-plugin-root>` prints the physically canonical manifest-declared JavaScript entry; `TMUP_PLUGIN_DIR` remains the manifest root so sync scripts resolve correctly.

- [ ] **Step 1: Write isolated discovery tests**

  Build a fake tmup plugin with `.claude-plugin/plugin.json`, `mcp-server/dist/index.js`, and `scripts/sync-codex-agents.sh`; prepend fake `tmux` and `codex` binaries to `PATH`; set isolated `HOME` and state directories. Assert preflight JSON names the manifest entry and sync script.

  Add three negative/boundary cases: a future manifest entry `${CLAUDE_PLUGIN_ROOT}/server/main.js` succeeds; a missing declared file returns `TMUP_MISSING`; and a manifest argument escaping the plugin root with `../outside.js` is rejected.

- [ ] **Step 2: Verify the old hardcoded discovery fails**

  Run `bash tests/test-crossmodel-preflight.sh`.

  Expected: the declared `mcp-server/dist/index.js` fixture fails with `TMUP_MISSING` because the old preflight probes only `tmup/index.js`.

- [ ] **Step 3: Implement manifest-based discovery**

  Parse `.claude-plugin/plugin.json` with Python 3.12, select the `mcpServers.tmup.args` string that expands from `${CLAUDE_PLUGIN_ROOT}` to an existing JavaScript file, canonicalize it, and reject entries outside the physical plugin root. Keep discovery read-only. The helper returns only the entry; the preflight retains its candidate root separately for `scripts/sync-codex-agents.sh`.

  Candidate loop shape:

  ```bash
  for candidate_root in "${candidate_roots[@]}"; do
    [[ -n "$candidate_root" && -d "$candidate_root" ]] || continue
    if TMUP_ENTRY="$(discover_tmup_entry "$candidate_root")"; then
      TMUP_PLUGIN_DIR="$(cd "$candidate_root" && pwd -P)"
      break
    fi
  done
  ```

  Do not alter `crossmodel-grid-down.sh` or registry behavior in 1A.

- [ ] **Step 4: Run fixture and installed-entry checks**

  ```bash
  bash -n scripts/lib/tmup-discovery.sh scripts/crossmodel-preflight.sh tests/test-crossmodel-preflight.sh
  bash tests/test-crossmodel-preflight.sh
  test -f "$HOME/.claude/plugins/tmup/mcp-server/dist/index.js"
  python3.12 -m json.tool "$HOME/.claude/plugins/tmup/.claude-plugin/plugin.json" >/dev/null
  ```

  Expected: fixture suite passes and installed manifest/entry observations succeed. Do not launch tmux or mutate the live registry.

- [ ] **Step 5: Commit tmup discovery**

  ```bash
  git diff --check
  git add scripts/lib/tmup-discovery.sh scripts/crossmodel-preflight.sh tests/test-crossmodel-preflight.sh
  git diff --cached --check
  git commit -m "fix: resolve tmup from its plugin manifest"
  ```

### Task 5: Establish Metadata and Inventory Authorities

**Files:**
- Create: `scripts/check-plugin-metadata.py`
- Create: `scripts/check-repository-inventory.py`
- Create: `tests/test_metadata_inventory.py`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.claude/CLAUDE.md`
- Modify: `README.md`

**Interfaces:**
- Produces: metadata check JSON containing `plugin_version` and `marketplace_version_authority`; inventory check JSON containing `repository_agents`, `repository_skills`, and `readme_core_agents`.
- Authority: `.claude-plugin/plugin.json` remains unchanged at `10.0.0`; marketplace metadata contains no `version` key.

- [ ] **Step 1: Write mutation-based metadata and inventory tests**

  Use `unittest.TemporaryDirectory` to copy the minimum manifest/docs/agent/skill fixture, invoke each checker with `--root`, and assert:

  - current repository returns plugin `10.0.0`, 46 agent Markdown files, 16 top-level skill directories containing `SKILL.md`, and a README core subset count of 30;
  - inserting marketplace version `4.0.0` fails;
  - removing one agent fails the documented projection;
  - changing `.claude/CLAUDE.md` back to `45 agents` fails;
  - describing README's 30 names as the installed total fails.

- [ ] **Step 2: Run tests and verify the known drift**

  Run `python3.12 -m unittest tests/test_metadata_inventory.py -v`.

  Expected: failures cite marketplace `4.0.0` versus manifest `10.0.0`, documentation `45/15` versus repository `46/16`, and an unlabeled installed-total/core-subset ambiguity.

- [ ] **Step 3: Implement read-only checkers and correct projections**

  `check-plugin-metadata.py` must parse both JSON files, require a valid nonempty semantic version only in the plugin manifest, reject a `version` key in the matching marketplace plugin object, and emit that authoritative version in sorted JSON. The release test/verification row—not another operational metadata field—asserts the approved candidate value is `10.0.0`.

  `check-repository-inventory.py` must derive counts from bytes on disk, parse the two documented projections, require exact equality, count README's enumerated names, and require the heading/text to label those 30 as a `core-agent subset`. Runtime-loaded counts must be described as separate and must not be inferred by this script.

  Remove only the duplicate marketplace `version`; update `.claude/CLAUDE.md` from `15/45` to `16/46`; change `### Agents (30)` to `### Core-Agent Subset (30)` and add one sentence that the repository contains 46 agent files and 16 skill directories while runtime composition is separate.

- [ ] **Step 4: Run strict schema, drift, and mutation checks**

  ```bash
  python3.12 -m unittest tests/test_metadata_inventory.py -v
  python3.12 scripts/check-plugin-metadata.py --root .
  python3.12 scripts/check-repository-inventory.py --root .
  claude plugin validate . --strict
  claude plugin validate .claude-plugin/marketplace.json --strict
  ```

  Expected: all commands exit `0`; plugin output reports `10.0.0`; inventory output reports `46`, `16`, and core subset `30`. If strict validation rejects version omission, stop and amend the plan to generate the marketplace version from the manifest; do not reintroduce an independent literal.

- [ ] **Step 5: Commit authority corrections**

  ```bash
  git diff --check
  git add .claude-plugin/marketplace.json .claude/CLAUDE.md README.md scripts/check-plugin-metadata.py scripts/check-repository-inventory.py tests/test_metadata_inventory.py
  git diff --cached --check
  git commit -m "fix: reconcile plugin metadata and inventory"
  ```

### Task 6: Pin `tsx` and Prohibit Dynamic Download or Zero-Test Success

**Files:**
- Create: `colony/run-tsx.sh`
- Create: `tests/test-colony-tooling.sh`
- Modify: `colony/package.json`
- Modify: `colony/package-lock.json`
- Modify: `colony/vitest.config.ts`
- Modify: `colony/smoke-test.sh`
- Modify: `colony/bridge.test.ts`
- Modify: `colony/bridge-cli.ts`
- Modify: `colony/README.md`
- Modify: `colony/conductor-prompt.md`
- Modify: `colony/scripts/bootstrap-colony.ts`
- Modify: `colony/scripts/capture-findings.ts`

**Interfaces:**
- Produces: `colony/run-tsx.sh <script-or-tsx-args...>`; exact local dependency `tsx@4.23.1`.
- Failure contract: missing `colony/node_modules/.bin/tsx` prints `ERROR: local tsx is not installed; run npm ci in colony` to stderr and exits `127` without invoking npm or network.

- [ ] **Step 1: Write tooling boundary tests**

  The test must assert exact pinning in package and lock files; run the wrapper with `npm_config_offline=true` and an empty cache; copy the wrapper into a temp Colony tree with no `node_modules` and require exit `127`; scan executable/docs files for `npx tsx` and `#!/usr/bin/env npx tsx`; and create an empty Vitest directory/config invocation that must exit nonzero.

- [ ] **Step 2: Run the test and verify the expected red state**

  Run with canonical Node:

  ```bash
  PATH="/opt/homebrew/opt/node@20/bin:$PATH" bash tests/test-colony-tooling.sh
  ```

  Expected: failure because `tsx` is undeclared, the wrapper is absent, dynamic invocations remain, and `passWithNoTests: true` accepts an empty suite.

- [ ] **Step 3: Pin the exact dependency and add the local wrapper**

  From `colony/`, run `PATH="/opt/homebrew/opt/node@20/bin:$PATH" npm install --save-dev --save-exact tsx@4.23.1` so package and lockfile change together.

  Create `colony/run-tsx.sh`:

  ```bash
  #!/bin/bash
  set -euo pipefail
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  TSX_BIN="$SCRIPT_DIR/node_modules/.bin/tsx"
  if [[ ! -x "$TSX_BIN" ]]; then
    printf 'ERROR: local tsx is not installed; run npm ci in colony\n' >&2
    exit 127
  fi
  exec "$TSX_BIN" "$@"
  ```

- [ ] **Step 4: Replace dynamic invocations and fail zero-test runs**

  Use `"$SCRIPT_DIR/run-tsx.sh"` in smoke tests and `execFileSync(join(__dirname, 'run-tsx.sh'), [...])` in `bridge.test.ts`. Update repository examples to `colony/run-tsx.sh colony/...` from repository root or `./run-tsx.sh ...` from `colony/`. Remove the invalid executable shebang from `bootstrap-colony.ts` and keep its usage text aligned with the wrapper. Set `passWithNoTests: false` or remove the option from `vitest.config.ts`.

- [ ] **Step 5: Prove offline/local execution and TypeScript regression safety**

  ```bash
  PATH="/opt/homebrew/opt/node@20/bin:$PATH" bash tests/test-colony-tooling.sh
  PATH="/opt/homebrew/opt/node@20/bin:$PATH" colony/run-tsx.sh --version
  cd colony && PATH="/opt/homebrew/opt/node@20/bin:$PATH" ./node_modules/.bin/tsc --noEmit
  cd colony && PATH="/opt/homebrew/opt/node@20/bin:$PATH" ./node_modules/.bin/vitest run
  ```

  Expected: tooling suite exits `0`; version is `tsx v4.23.1`; TypeScript has zero errors; Vitest discovers tests and passes. Record any unrelated test failure as a 1C baseline finding rather than masking it.

- [ ] **Step 6: Commit the local-tooling boundary**

  ```bash
  git diff --check
  git add colony/run-tsx.sh colony/package.json colony/package-lock.json colony/vitest.config.ts colony/smoke-test.sh colony/bridge.test.ts colony/bridge-cli.ts colony/README.md colony/conductor-prompt.md colony/scripts/bootstrap-colony.ts colony/scripts/capture-findings.ts tests/test-colony-tooling.sh
  git diff --cached --check
  git commit -m "fix: pin local tsx execution"
  ```

### Task 7: Add the Fail-Closed Verification Manifest and Runner

**Files:**
- Create: `verification/manifest.json`
- Create: `verification/README.md`
- Create: `verification/error-catalog.json`
- Create: `verification/baseline-inventory.json`
- Create: `verification/review-state.json`
- Create: `verification/review-result.schema.json`
- Create: `scripts/run-verification.py`
- Create: `tests/test_verification_runner.py`
- Modify: `.gitignore`

**Interfaces:**
- CLI: `python3.12 scripts/run-verification.py --manifest verification/manifest.json --stage 1A --results-dir <dir> [--platform macos|linux] [--run-id <id>]`.
- Runner exits: `0` all required selected rows `PASS`/valid `NOT_APPLICABLE`; `1` at least one `FAIL` (even if another row is inconclusive); `3` at least one `INCONCLUSIVE` and no `FAIL`; `64` invocation/manifest/empty-selection error; `70` internal evidence-write error, which overrides row aggregation.
- Receipt verdicts: `PASS | FAIL | INCONCLUSIVE | NOT_APPLICABLE`; execution states: `RAN | NOT_RUN | NOT_APPLICABLE`. A required `NOT_RUN` row is `INCONCLUSIVE`; there is no green `SKIPPED` state.
- Path contract: manifest, cwd, executable-with-slash, artifacts, and a previously nonexistent relative `--results-dir` resolve physically beneath the repository; `run-id` is one safe path segment; symlink/traversal/overwrite attempts fail before execution.
- Environment/tool contract: before isolation, resolve every row's declared `required_tools` from the operator-supplied acquisition `PATH`, fingerprint them, build a runner-owned PATH from only their canonical parent directories plus `/usr/bin:/bin`, and replace `command[0]` with the already-resolved absolute executable. Child state then adds `LC_ALL=C`, `LANG=C`, `TZ=UTC`, per-check isolated `HOME`/`TMPDIR`, and only declared non-secret overrides; reserved keys (`PATH`, `HOME`, `TMPDIR`, locale/timezone keys) cannot be overridden. Manifest values may use only runner-owned `${REPO_ROOT}`, `${HOST_HOME}`, `${CHECK_HOME}`, and `${CHECK_TMPDIR}` substitutions; `HOST_HOME` comes from the OS account database before isolation, not ambient `HOME`. The exact expanded environment is a protected mode-`0600` local artifact; admitted receipts store only declared tokenized values, sanitized descriptors, and that artifact's hash.
- Platform contract: detect and record kernel OS and architecture; `--platform` is an assertion, not an override. A mismatch exits `64`. Zero selected checks exits `64`; a selected release with no executed mandatory row is aggregate `INCONCLUSIVE`, never vacuous success.

- [ ] **Step 1: Write runner contract tests first**

  In `tests/test_verification_runner.py`, create temporary Git repositories and manifests, then test:

  - argv execution records exact command, cwd, selected environment, stdout, stderr, exit `0`, duration, source commit, platform/tool fingerprint, and SHA-256 hashes;
  - tested exit `7` remains `7` in the receipt and yields `FAIL`;
  - timeout kills the process group and yields `INCONCLUSIVE` with partial evidence retained;
  - a leader that exits while a background member remains causes group termination and `INCONCLUSIVE`, never `PASS`;
  - runner `SIGINT`/`TERM` forwards TERM, waits a bounded two seconds, sends KILL, waits/reaps two seconds, retains partial evidence, and exits `3`; a canary `setsid()` escape is detected by the adversarial process snapshot and makes the claim `INCONCLUSIVE` because the runner is not an OS sandbox;
  - a `test_count_regex` observation matching zero or no count yields `FAIL`, never `PASS`;
  - missing required artifact yields `INCONCLUSIVE`;
  - a platform mismatch is `NOT_APPLICABLE` only when the manifest's applicability evidence is nonempty;
  - shell strings, `env`, interpreter command-string flags (`sh -c`, `python -c`, `node -e` and equivalents), absolute/outside paths, unsafe run IDs, symlinked/outside/existing results roots, unknown keys/types, duplicate IDs, unknown/empty `requirement_ids`, empty falsifiers, reserved environment overrides, or a key matching `TOKEN|SECRET|PASSWORD|KEY|COOKIE|AUTH` are rejected with exit `64`;
  - executable/tool resolution and fingerprints are recorded; launch uses the resolved absolute path and runner-owned PATH; missing or changed resolution is non-pass;
  - only observation types `contains`, `regex`, `test_count_regex`, `json_subset`, and `empty` are accepted, with exact per-type fields and positive `min_count` for test counts;
  - an explicitly declared `inconclusive_exit_codes` value such as F-01's `3` yields `INCONCLUSIVE`; undeclared nonzero remains `FAIL` and cannot overlap `expected_exit`;
  - dirty source is recorded, a row requiring `clean_source: true` cannot pass, and any child-created tracked change or unignored path makes that row non-pass even when the child exits zero;
  - result directories/files use `0700`/`0600`; structured receipts/summaries never contain synthetic secret canaries, exact private environment values, or raw subprocess content; protected `environment.json` retains exact local replay bytes and is excluded from reviewer projections;
  - read-only parent, permission denial, injected `ENOSPC`, short/partial write, failed flush/fsync/rename, and summary-write failure never emit `PASS` and cause exit `70` with the most complete protected partial evidence possible;
  - wall-clock jumps do not create negative or false durations because elapsed time uses `time.monotonic_ns()`; UTC wall timestamps remain labels only.
  - a child swapping a result path to a symlink cannot redirect writes: the runner retains directory descriptors, uses no-follow relative opens/replaces, and revalidates device/inode/ancestry before admission;
  - runner-owned `stdout`, `stderr`, `environment`, and `receipt` are distinct from row `required_artifacts`; check-produced artifacts must be regular no-follow files beneath `${CHECK_TMPDIR}`, satisfy declared type/size bounds, and are copied/hash-verified only after process termination;
  - manifest rows are bounded to 256 argv elements, 8 KiB per argument/value, timeout `1..1800` seconds, 16 MiB per raw stream/artifact, and 1 MiB regex/JSON observation input; a 100 ms monitor terminates the process group on overflow with `VERIFY_OUTPUT_LIMIT` and non-pass;
  - every authority/receipt JSON rejects malformed/truncated UTF-8, duplicate keys, NaN/Infinity, unknown/future schema versions, nesting deeper than 16, encoded input larger than 1 MiB, strings larger than 64 KiB, or containers larger than 4096 members; deterministic encoding is sorted UTF-8 with compact separators and `allow_nan=False`;
  - `verification/README.md` examples and `--help` output are parsed by the real CLI parser, and every copy-paste example either exits at its documented precondition or runs successfully in a temporary repository.

- [ ] **Step 2: Run the tests and verify the runner is absent**

  Run `python3.12 -m unittest tests/test_verification_runner.py -v`.

  Expected: import or executable-not-found failure naming `scripts/run-verification.py`.

- [ ] **Step 3: Implement a strict versioned manifest loader**

  The manifest top level contains only `schema_version`, a `requirement_catalog` keyed by the IDs in this plan's traceability table, a reviewed `executable_allowlist`, `protected_ignored_paths`, and `checks`. Each catalog entry names source, 1A disposition, owner release, and whether full closure is possible in 1A. Rows may reference only catalog IDs; every applicable 1A catalog ID must be covered by at least one required row, and aggregate output retains later-owned/partial IDs. Protected ignored paths include plan-review `artifacts/` and exact dependency trees/files whose pre/post fingerprints are load-bearing; the active unique result directory is the only ignored mutation allowance. The manifest is trusted committed executable policy, not a sandbox: its allowlist admits only the exact Bash/Python/Git/Claude/local-Node command families needed by named rows, with permitted argument shapes; dynamic interpreters, arbitrary executables, network clients, and mutation-oriented Git commands are rejected.

  Require this row shape, with `command` as a nonempty argv array and relative `working_directory`:

  ```json
  {
    "check_id": "s1a-f01-dispatch-isolation",
    "stage": "1A",
    "requirement_ids": ["S1-02", "F-01"],
    "command": ["bash", "tests/test-sdlc-dispatch-isolation.sh"],
    "required_tools": ["bash", "cp", "find", "mktemp", "sed", "python3.12"],
    "working_directory": ".",
    "environment": {"LC_ALL": "C"},
    "platforms": ["macos", "linux"],
    "applicability": {"state": "REQUIRED", "evidence": "Bash fixture boundary is platform-independent"},
    "timeout_seconds": 60,
    "max_output_bytes": 16777216,
    "expected_exit": 0,
    "inconclusive_exit_codes": [3],
    "expected_observation": {"type": "contains", "stream": "stdout", "value": "F01 isolation PASS"},
    "negative_falsifier": "Source/decoy mutation or missing/non-temporary failpoint fails; unexplained installed drift is exit 3/Inconclusive",
    "independence_requirement": "author-executable; non-author reproduction required at release gate",
    "required_artifacts": [],
    "clean_source": false
  }
  ```

  Reject unknown schema versions and unknown row keys. All committed authorities and generated receipts carry `schema_version`; unknown/future values fail closed. Decode strict UTF-8 with duplicate-key and non-finite-number rejection, enforce the bounded JSON limits above, and encode sorted/compact UTF-8 with `allow_nan=False`. Observation input must decode as strict UTF-8; invalid encoding/parsing is `INCONCLUSIVE`. Define the five observation variants as a strict tagged union: `contains` requires one bounded byte-exact decoded substring; `regex` uses one bounded Python regex search; `test_count_regex` requires exactly one match and one integer capture meeting positive `min_count`; `json_subset` recursively requires every expected object key/value while arrays compare exactly in order; `empty` requires zero bytes. Reject extra/missing variant fields, ambiguous multiple count matches, catastrophic/unbounded patterns, or input beyond the observation limit.

  Resolve every path physically beneath the repository root, require a nonexistent root-relative results directory, reject symlink components and unsafe run IDs, and refuse overwrite. Reject shell interpreter command-string flags even though the command is an argv array. Resolve the executable before launch and record its canonical path and fingerprint. Construct the exact minimal child environment described above and expand only the four runner-owned substitutions. Write the exact effective environment only to protected `environment.json`; the receipt records declared tokenized values, a sanitization map, relative artifact path, mode, size, and hash. Never serialize the full ambient environment. Owner-host installed-observation rows explicitly declare `SDLC_INSTALLED_PLUGIN_ROOT=${HOST_HOME}/.claude/plugins/sdlc-os` or `TMUP_PLUGIN_ROOT=${HOST_HOME}/.claude/plugins/tmup`; Linux rows may mark the installed-only observation `NOT_APPLICABLE` with evidence. `inconclusive_exit_codes` is optional, explicit, disjoint from `expected_exit`, and limited to `1..125`.

- [ ] **Step 4: Implement unmasked execution and content-addressed receipts**

  Open the unique result directory with a retained directory descriptor; all raw/temporary/final files use no-follow relative operations against that descriptor, and admission revalidates device/inode/physical ancestry. Use `subprocess.Popen` with the resolved absolute executable, runner-owned PATH, `cwd`, exact constructed `env`, and `start_new_session=True`, writing to mode-`0600` stdout/stderr handles. On timeout or runner interruption, apply bounded TERM→KILL→reap, preserve partial output, and classify `INCONCLUSIVE`. After ordinary leader exit, probe the launched process group; terminate any survivor and classify `INCONCLUSIVE`. The runner is not a general sandbox, so committed command review forbids daemonization/`setsid`; an adversarial escaped-descendant canary blocks green. Evaluate explicit inconclusive exit, true exit, structured observation, check-produced artifacts, post-command source state, and source cleanliness in that order.

  Capture pre/post commit and `git status --porcelain --untracked-files=all`; ignored result files are permitted, but any other child-created change is non-pass. Pre/post hash the protected ignored `artifacts/` tree and every manifest-declared ignored dependency fingerprint; the active result directory alone is allowed to change. This is mutation detection for reviewed checks, not sandbox isolation. Each receipt contains command, resolved executable/tool fingerprints, cwd, tokenized declared environment plus protected-environment hash, applicability, start/end UTC, monotonic duration, true exit/signal/timeout/background state, execution state, verdict/reason/error code, stdout/stderr relative paths/modes/sizes/hashes, pre/post source/protected-ignored state, detected OS/architecture, Python/Node/Git versions, full manifest hash, requirement-catalog hash, runner source/version hash, manifest-row hash, and candidate SHA.

  Flush and `fsync` raw stdout/stderr/environment/check-artifact copies before hashing them. Write receipts and `run.json` as mode-`0600` temporary siblings, flush, `fsync`, then atomically replace them relative to the retained directory descriptor; fsync the containing directory before admission. A write/flush/rename/inode-validation failure returns `70`, never prints a success digest, and retains only protected partial evidence. The summary enumerates the complete selected, executed, not-run, not-applicable, and rejected check universe plus hashes and sanitized bounded diagnostics, never raw streams or private host/path values; its own SHA-256 is printed only after readback validation.

- [ ] **Step 5: Create the Stage 1A manifest and honest baseline inventories**

  Add required 1A rows for F-01 direct assertion, each foreground `HUP`/`INT`/`TERM` signal mode, the background-wrapper SIGINT negative, two-driver concurrency, admission negatives, sidecar mutation, both restore-retention variants, cleanup retarget/source-policy rejection, normal dispatcher, root relocation, shims, fixture regression, portable shell helpers, clone manager, tmup discovery fixture, metadata checker, strict plugin validation, inventory checker, local/offline `tsx`, TypeScript typecheck, discovered Vitest suite, touched-shell syntax, old-literal scans, and clean committed candidate. Every F-01 row declares `inconclusive_exit_codes: [3]`; no undeclared nonzero exit may be coerced to green.

  `verification/baseline-inventory.json` is the unified Stage 1 register. Every entry requires `stable_id`, `class`, `severity` (`CRITICAL | MATERIAL | NONMATERIAL`), numeric `priority`, `owner`, `affected_requirements`, `affected_stage_release`, `trigger_or_due`, `evidence`, `rationale`, `mitigation`, `current_verdict`, `disposition`, ISO `review_date`, and `closure_proof`. The inventory, error catalog, and review state each have independent schema versions with current-version-only loaders and malformed/future-version negatives. Schema tests reject omitted fields, invalid deferral of a load-bearing item, or a later owner/release without a trigger and closure proof. Include:

  - checkout fixture `0/13`, validator shims `0/14`, dispatcher path exit `127`, clone manager `19/24`, clone identifier traversal, both `du -sb` sites, three `mktemp --suffix` sites, tmup stale entry, version/inventory/tsx drift, no-test config, and `P27-01..P27-16` as 1A or plan-review disposition;
  - direct registry surgery, bridge false-sync handling, age-only prune, shared inbox loss risk, and weak health evidence as 1B;
  - Deacon's independent `recovered-outputs/<task_id>` path containment, the legacy `colony/validation/run-all.sh` `eval` runner, best-effort Colony permission/log writes, log-field privacy minimization, dedup runner/package mismatch, ShellCheck, Ruff, weak/assertion-free/skipped/sleeping tests, masked provider paths, fixed `/tmp` tests, shared smoke lock, full deterministic matrix, and systemd/launchd packaging as 1C. These remain visible and cannot support 1A or Stage 1 green; Task 3 claims only the shell clone-manager boundary. A manifest schema test proves no mandatory 1A row invokes the legacy `eval` runner.

  Create `verification/error-catalog.json` with schema version, the codes listed under Error Messaging, audience, sanitized template, remediation, evidence fields, and owning requirement. Unit tests scan implementation/tests for emitted stable codes and fail on missing, duplicate, or unused catalog entries.

  `verification/review-state.json` must mark both same-reviewer final spec passes `INCONCLUSIVE`, identify the owner-nominated spec review separately, and leave Release 1A independent/adversarial candidate fields `PENDING` without claiming a reviewer identity. Its schema tests reject unknown/future versions and any candidate review missing candidate/manifest hashes, source locations, reviewer method, command exits, findings, or limitations.

  `verification/review-result.schema.json` defines the ignored immutable-candidate review artifact: schema/candidate/manifest/requirement-catalog hashes, reviewer runtime/method, commands and true exits, material claims with candidate-bound `file:line`, symbol/test name and file hash, findings/dispositions/limitations, protected evidence hashes, and reviewer verdict. `run-verification.py --validate-review-result <path> --candidate <sha>` validates it without changing `HEAD`; the committed `PENDING` review state is historical pre-freeze context, not proof that review occurred.

  Add root-anchored `/.verification-results/` and `/artifacts/` to `.gitignore`; do not ignore `verification/`. Prove `git check-ignore` selects both generated roots and rejects `verification/manifest.json`. Add `verification/README.md` with the exact Python 3.12 CLI, manifest/receipt/catalog/register schemas and verdict/exit mappings, minimal environment, protected modes, clean/offline replay, artifact retention/redaction/reviewer-payload rules, and the rule for appending 1B/1C rows without changing prior row IDs or receipts.

- [ ] **Step 6: Run runner tests and a development-mode 1A manifest pass**

  ```bash
  python3.12 -m unittest tests/test_verification_runner.py -v
  python3.12 -m json.tool verification/manifest.json >/dev/null
  python3.12 -m json.tool verification/error-catalog.json >/dev/null
  python3.12 -m json.tool verification/baseline-inventory.json >/dev/null
  python3.12 -m json.tool verification/review-state.json >/dev/null
  python3.12 -m json.tool verification/review-result.schema.json >/dev/null
  git check-ignore artifacts/probe .verification-results/probe
  if git check-ignore verification/manifest.json; then exit 1; fi
  DEV_RUN_ID="development-$(git rev-parse --short=12 HEAD)-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  python3.12 scripts/run-verification.py --manifest verification/manifest.json --stage 1A --platform macos --run-id "$DEV_RUN_ID" --results-dir ".verification-results/$DEV_RUN_ID"
  ```

  Expected: runner unit tests pass. Development manifest may classify only the `clean_source` candidate row as `FAIL` while edits are uncommitted; every other 1A row must pass or the release stops for a written amendment.

- [ ] **Step 7: Commit the verification authority**

  ```bash
  git diff --check
  git add .gitignore verification/manifest.json verification/README.md verification/error-catalog.json verification/baseline-inventory.json verification/review-state.json verification/review-result.schema.json scripts/run-verification.py tests/test_verification_runner.py
  git diff --cached --check
  git commit -m "feat: add hermetic verification runner"
  ```

### Task 8: Freeze, Reproduce, and Review the Release 1A Candidate

**Files:**
- Do not modify the frozen candidate during review.
- Generate candidate/run-bound ignored artifacts beneath `.verification-results/<candidate>-<platform>-<unique-run>/` and sanitized review projections beneath `.verification-results/<candidate>-reviews/`.
- If an accepted finding requires repository changes, return to its owning task, add a regression, create a new candidate commit, and restart Tasks 8.1–8.7.

**Interfaces:**
- Consumes: immutable clean Release 1A `HEAD` and Stage 1A manifest.
- Produces: macOS and Linux receipt digests, a scoped independent review record, and terminal claim `STAGE_1A_MECHANICAL_BASELINE=PASS|FAIL|INCONCLUSIVE`.

- [ ] **Step 1: Freeze the candidate and run repository hygiene gates**

  ```bash
  BASE=1c3285ad92c0daea2449bf3c5d56a3c248841a20
  git status --porcelain
  git diff --check
  git merge-base --is-ancestor "$BASE" HEAD
  test "$(git merge-base "$BASE" HEAD)" = "$BASE"
  git diff --check "$BASE"..HEAD
  git diff --name-only "$BASE"..HEAD
  git log --format='%H%n%an <%ae>%n%B%n--END--' "$BASE"..HEAD
  git show --stat --oneline HEAD
  ```

  The Stage 1A manifest includes a range-scope row that runs Git with an exact exclusion allowlist derived from the File and Interface Map, failing if any other path changed. A separate range-message row captures every commit message from `BASE..HEAD` and rejects prohibited attribution/model/email text without a pipeline. Expected: worktree is clean, ancestry/merge base match, range whitespace is clean, every range commit passes hygiene, and only approved 1A paths changed.

- [ ] **Step 2: Execute the canonical macOS 1A manifest**

  ```bash
  MAC_RUN_ID="$(git rev-parse --short=12 HEAD)-macos-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  PATH="/opt/homebrew/opt/node@20/bin:$PATH" \
    python3.12 scripts/run-verification.py \
      --manifest verification/manifest.json \
      --stage 1A \
      --platform macos \
      --run-id "$MAC_RUN_ID" \
      --results-dir ".verification-results/$MAC_RUN_ID"
  ```

  Expected: exit `0`; every selected mandatory row is `PASS`; run summary prints its digest. Any masked, empty, zero-test, failed, or missing row prevents green.

- [ ] **Step 3: Reproduce the committed candidate on Linux**

  Resolve `LINUX_VERIFY_HOST` from owner-local inventory. Create a verified Git bundle containing the exact candidate and required base history, hash it, transfer it to a unique remote `/tmp` directory, verify the digest, clone it, and check out the candidate SHA detached. Verify `HEAD`, merge base, and clean status before installing Colony dependencies from the lockfile and running the Linux 1A manifest under Node `20.20.2` and Python `3.12.x` with a unique candidate/platform/run ID.

  Copy the complete protected result tree (raw streams, environment artifacts, receipts, and summary) back into the matching local ignored run directory, preserving modes; validate every hash and summary locally before removing the unique remote directory. Derive a separate sanitized reviewer projection that contains no raw stream or private locator. Never delete the only retained raw evidence.

  Expected: runner exit `0`; both portable-size sites report positive byte telemetry; all Linux-applicable 1A rows pass. SSH failure, dependency-install failure, platform mismatch, or missing artifacts is `INCONCLUSIVE`.

- [ ] **Step 4: Obtain a genuine non-author, read-only Release 1A review**

  Resolve the live runtime catalog at dispatch time. Send the verified Git bundle, immutable commit hash, governing spec §9.1/§11/§17/§18, this plan, manifest, sanitized macOS/Linux receipt projections, and F-01 threat model to an owner-authorized read-only runtime that did not author the candidate. Require source-byte inspection and independent command reproduction, not summary agreement. Every material claim records candidate-bound `file:line`, symbol/test name, file SHA-256, method, command/true exit, finding, limitation, and candidate/manifest hashes in the committed review-result schema. Validate the result with `run-verification.py --validate-review-result` before admitting it.

  The same-model native Codex subagents do not qualify. If no distinct reviewer is available, set the review field to `INCONCLUSIVE` and do not claim the release gate.

- [ ] **Step 5: Run a bounded adversarial mechanical-scope pass**

  A second distinct read-only reasoning path is required to attack: installed-tree reachability, signal/interruption windows, symlink/path escape, clone identifier traversal before mutation, concurrent dispatcher runs, manifest command injection, result-root escape/overwrite, secret leakage into structured/reviewer evidence, permission/ENOSPC/partial-write/clock-jump handling, lingering/escaped background processes, zero-test/masked exits, tmup manifest escape, marketplace drift, offline `tsx`, and `/var` canonicalization. If it is unavailable, Release 1A is `INCONCLUSIVE`.

  In a disposable copy of the exact candidate, run a call-removal/written-but-not-consumed mutation matrix. Independently bypass the root-resolver call, portable size helper call, tmup manifest discovery call, local `tsx` wrapper call, and runner observation/artifact-consumption check; each mutation must make its named owning test fail. A test that stays green proves the interface is written but not load-bearing and blocks the release.

  Run a final architectural-fitness scan: every new helper/CLI/catalog field has at least one production caller and one falsifying test; no duplicate root/size/tmup/tsx/receipt implementation remains; no new unreachable or dead executable surface exists; and three similar lines remain inline unless an existing shared contract justifies extraction. Then give a fresh non-author reviewer only the verified Git bundle plus `verification/README.md`; require detached checkout and copy-paste execution from prerequisites through receipt-hash validation without chat-only steps or private absolute paths.

  Every finding receives `ACCEPTED`, `REJECTED`, `ACCEPTED_RESIDUAL`, or `UNRESOLVED` with evidence, owner, severity, due trigger, and closure proof. Critical/material `UNRESOLVED`, a surviving call-removal mutation, dead surface, or unusable runbook yields non-green.

- [ ] **Step 6: Correct accepted findings within the scoped correction budget**

  Permit at most two correction cycles. For each accepted 1A finding: add a failing regression, implement the minimum scoped correction, rerun focused tests plus both platform manifests, create a new local commit, and require review of the new candidate. A bridge/prune/inbox/health/service finding is assigned to its owning later release unless it invalidates 1A safety; an invalidating finding stops 1A for a plan amendment.

- [ ] **Step 7: Record the release verdict and create the owner checkpoint**

  Keep the committed `verification/review-state.json` candidate fields `PENDING`; it honestly records that no candidate review existed when the candidate froze. Store actual immutable-candidate review results and sanitized projections under ignored candidate-bound review directories, validate them against `verification/review-result.schema.json` without changing `HEAD`, and report exactly one terminal release state:

  - `PASS`: every mandatory 1A row passes on required platforms, candidate is clean/committed, independent review is conclusive, and no material unresolved finding remains;
  - `FAIL`: a conclusive mandatory 1A requirement failed;
  - `INCONCLUSIVE`: required platform/reviewer/evidence is unavailable, masked, or ambiguous.

  Stop for the Release 1A owner checkpoint. The handoff names the unchanged candidate SHA and macOS/Linux/reviewer receipt digests; no post-review evidence commit invalidates those bindings. Do not begin 1B code until its separate plan is written and the owner review requirement is satisfied. Do not claim Stage 1 green, production readiness, or authorization for Stage 2+.

## Self-Review Checklist

- [ ] Every Stage 1A item in spec §9.1 maps to a task: F-01/root (1–2), size/temp (3), tmup entry (4), version/inventory (5), `tsx`/no-test (6), runner/inventory (7), platform/review (8).
- [ ] Release 1B and 1C semantics are named and deferred without being silently implemented in 1A.
- [ ] All five checkout-bound references across four files are removed only after F-01 isolation lands atomically with the first resolver consumer.
- [ ] No step runs the hazardous original dispatcher suite before isolation.
- [ ] The Task 1 decoy includes its manifest and optional helper tree, all isolated roots/CWDs are physically contained, and direct/signal/concurrent post-swap proofs run before its commit.
- [ ] The direct post-swap failpoint uses `/usr/bin/false`, exits exactly `1`, and admits no child stdout; a false Bash `[[ ... ]]` command is not treated as an `errexit` proof.
- [ ] Eight pre-swap cases must be green before the validator move, admitted child stderr is exactly one marker, and conclusive concurrent failure takes precedence over exit `3`.
- [ ] Complete versioned validator-prefix inventories detect dot and dotless decoy sidecars; missing-backup/capture/cleanup failures retain both bounded trees; recursive cleanup is descriptor-held, no-follow, identity-checked, duplicate-token/ancestor/root-swap tested, and makes no malicious-same-UID sandbox claim.
- [ ] SIGINT evidence comes from a foreground raw-file launch; the backgrounding hypothesis capture wrapper is recorded as incompatible and cannot satisfy that row.
- [ ] No step runs the unsafe full Colony smoke test before its shared-lock fixture is isolated in 1C.
- [ ] Clone session/agent/task traversal is rejected before any `_ensure_colony_base`, `mkdir`, `git clone`, or `cp`, with zero outside-base side effect.
- [ ] macOS and owner-authorized Linux surfaces, runtimes, expected exits, and inconclusive fallbacks are explicit without committing private host locators.
- [ ] Prior same-reviewer passes are logged `INCONCLUSIVE`; native inherited-model workers are not mislabeled independent.
- [ ] No active v1 task, live registry, installed validator, live database, service, remote repository, or external communication target is mutated.
- [ ] Placeholder scan is clean: no `TBD`, `TODO`, “implement later,” unspecified error handling, or undefined interface is present.
- [ ] Function names remain consistent: `resolve_plugin_root`, `path_size_bytes`, `make_temp_file`, `discover_tmup_entry`, and `run-verification.py` CLI.
- [ ] The committed error catalog covers every emitted code; result-path, durability, privacy, background-process, source-mutation, and clock-jump negatives are load-bearing.
- [ ] Call-removal, DRY/dead-surface, and verified-bundle copy-paste usability checks fail closed on the immutable candidate.
- [ ] Every commit has a focused test cycle, expected result, scoped staging list, and no push/publication step.

## Final Review and Handoff

This file is the execution source of truth for Release 1A. A fresh operator must read the Global Constraints, pass-27 synthesis, Objective/Scope, traceability, assumption/finding registers, validation/readiness gates, Molecular Execution Contract, Verification Design, testing/logging rules, release map, file/interface map, Tasks 1–8, and Self-Review Checklist before acting. The current open risks are A-01/A-02/A-03/A-06/A-08/A-10 and accepted due-task findings P27-01..P27-04; none is accepted as a pass. F-01 ordering, installed/live-state exclusion, local-only commits, and the 1A-versus-Stage-1 claim boundary are blockers, not judgment calls.

Containment/rollback is task-local: stop the command, preserve raw evidence, restore only inner temporary fixtures via traps, and make a new explicit local revert/correction commit if committed bytes must change. Never use destructive Git reset/checkout/restore, never delete live tmup/task state, and never improvise around a failed platform/reviewer/contract gate. Two correction cycles are the maximum before returning to the owner checkpoint with a non-success verdict.

### Reproduce this plan-review run

Start from repository commit `1c3285ad92c0daea2449bf3c5d56a3c248841a20`, branch `stage1/1a-mechanical-baseline`, the plan-only diff, and the owner-local §4b record whose digest is listed in Global Constraints. The review used Apple Git `2.50.1`, PlanPrompt's observed Python `3.14.4`, canonical implementation Python `3.12.x`, and canonical Node `20.20.2`. Set `PLANPROMPT_ROOT` to the selected PlanPrompt skill directory discovered by the current runtime; do not commit its machine-local absolute path.

Run:

```bash
python3 "$PLANPROMPT_ROOT/scripts/render_plan_prompt.py" \
  --plan "$PWD/docs/superpowers/plans/2026-07-14-sdlc-os-stage-1a-mechanical-baseline.md" \
  --prompt 1
python3 "$PLANPROMPT_ROOT/scripts/check_artifact_consistency.py" \
  --artifacts-dir artifacts
git diff --check
git status --short
```

Re-run prompts `1..27` strictly in order, snapshotting/re-reading the current plan before each pass. Expected review artifacts include `artifacts/run_manifest.json`, `readiness.json`, `verification_matrix.md`, `primary_validation.md`, `validation_layer{2,3}.md`, `pass27-bank-{a-f,g-l,m-t}.md`, `final_review.md`, `test_evidence/`, and per-pass diff/summary/contract records. The final PlanPrompt artifact verdict is `Inconclusive` because implementation/platform/non-author candidate evidence is intentionally absent; `readiness.json` independently permits only the constrained safe Task 1 entry. The review cannot serve as implementation evidence.

Before handoff, reject the plan if any dependency is missing without a stop rule, a critical assumption lacks a validator, a verification step lacks thresholds/artifacts, readiness uses confidence language, an atomic action is unbounded, blocker/rollback logic is absent, telemetry cannot reconstruct failure, provenance is missing, or a claim exceeds 1A. Formal SBOM generation and signed attestations are not claimed in 1A; the exact npm lockfile is verified here, while repository-wide supply-chain/SBOM disposition remains an explicit Release 1C baseline item.
