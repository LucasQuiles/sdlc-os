# Debt Combat System Design

**Date:** 2026-03-29
**Version:** SDLC-OS v10.0.0 (proposed)
**Scope:** Gaps A-E from consolidation root cause analysis
**Approach:** Hybrid — one new agent (`debt-crawler`) + enrichment of existing agents/phases

## Problem Statement

The consolidation root cause analysis (2026-03-29) identified 5 systemic patterns producing legacy debt at velocity:

| Root Cause | Pattern | Current SDLC Coverage |
|---|---|---|
| RC1 | Build without adoption gates — canonicals created but callers never migrated | Partial |
| RC2 | LLM context blindness — duplicate utilities created across sessions | Strong (reuse-scout) |
| RC3 | Additive refactors — DRY initiatives that create more duplication | Moderate |
| RC4 | Warn forever — enforcement without teeth, suppression without justification | Weak |
| RC5 | Ghost architecture — scaffolding without follow-through | Moderate |

This design closes the remaining gaps by adding 5 capabilities mapped to 5 gaps:

| Gap | Capability | Mechanism |
|---|---|---|
| A | Adoption tracking for canonicals | debt-crawler Mode 1 |
| B | Rule graduation loop (warn to error) | standards-curator Rule Governance Audit |
| C | eslint-disable justification enforcement | Hook + structured format |
| D | Periodic duplicate scan | debt-crawler Mode 2 |
| E | Migration plan gate for new canonicals | Architect gate + L1 sentinel |

## Architecture Overview

```
Evolve Cycle
  #18 Adoption Scan --> debt-crawler Mode 1 --> debt-scan-report.md
  #19 Duplicate Scan --> debt-crawler Mode 2 --> debt-scan-report.md + debt-backlog.md
  #15 Standards Refresh --> standards-curator (expanded) --> graduation proposals

Scout (Phase 2)
  Rule Governance Audit --> standards-curator --> rule-governance-profile.md + suppression-allowlist.md

Architect (Phase 3)
  Primary manifest --> canonical-creation check --> require intent:migration + intent:registry beads
  After manifest --> debt-backlog import (relevance-gated, budget-limited)

Execute (Phase 4)
  L1 Sentinel --> drift-detector: MIGRATION_PLAN_MISSING check
  L1 Hook --> check-eslint-disable-justification.sh (whole-file, allowlist-gated)

Synthesize (Phase 5)
  gap-analyst Finisher --> reports unmigrated callers --> Conductor writes debt-backlog entries
```

---

## Section 1: New Agent — debt-crawler

### Identity

- **Agent file:** `agents/debt-crawler.md`
- **Model:** sonnet
- **Role:** Debt intelligence engine — multi-stage pipeline for adoption tracking and duplicate detection
- **Dispatched by:** Conductor during Evolve (bead types #18 and #19)
- **Reports to:** Conductor

### Core Principle

Debt-crawler is an evidence engine, not a scan script. It never emits findings directly into backlog. Every candidate must survive a staged pipeline: harvest broadly, corroborate aggressively, filter noise hard, rank by value.

### The Pipeline (Both Modes)

```
Stage 1: Candidate Harvest (multiple channels)
    |
Stage 2: Evidence Corroboration (2+ channels required)
    |
Stage 3: Noise Filters (explicit exclusions)
    |
Stage 4: Value Scoring (payoff, not just existence)
    |
Stage 5: Classification & Output
```

### Stage 1: Candidate Harvest

Each mode activates different harvest channels. A candidate from any single channel is a signal, not a conclusion.

**Mode 1 (Adoption Scan) channels:**

- **Canonical registry:** For each entry in `references/canonical-registry.md`, detect noncanonical pattern within include_paths minus exclude_paths. Agent constructs grep/LSP queries from declarative fields — never executes raw shell commands from the registry.
- **LSP references:** `findReferences` on canonical export — count callers vs total potential callers.
- **Suppression scan:** `eslint-disable` comments matching `related_rules` field for each canonical entry.

**Mode 2 (Duplicate Scan) channels:**

- **AST extraction:** New `scripts/extract-functions.sh` — ESLint-based walker that exports function name, parameter signature, body hash, line count, branch count, nesting depth from configured paths. JS/TS only (.ts/.tsx/.js/.jsx).
- **LSP:** `workspaceSymbol` for name collisions across modules, `findReferences` for adoption breadth, `incomingCalls`/`outgoingCalls` for usage patterns.
- **Grep/rules:** Same-name exports, canonical anti-patterns from registry, naming variants.
- **Git history:** Churn frequency, age, authorship spread (single-author = context blindness signal), recent failed edits on the same area.

**No Pinecone for v1.** The only documented Pinecone index is `thinkers-lab` (research). Mode 2 v1 uses deterministic methods only: AST body hashing for structural similarity, LSP for reference graphs, grep for naming patterns. Semantic similarity via a project-code embedding index is deferred to v2.

### Stage 2: Evidence Corroboration

A candidate requires 2+ independent evidence channels to become actionable. Single-channel findings are logged in the scan report as UNCONFIRMED and do not advance.

| Finding Type | Channel 1 | Channel 2 | Corroborated? |
|---|---|---|---|
| Duplicate utility | AST body hash match | LSP: both exported, both have callers | Yes |
| Adoption debt | Registry pattern hit | LSP: canonical has 0 callers | Yes |
| Suppression debt | eslint-disable count high | Rule age >30d + suppression ratio >50% | Yes |
| Zombie code | AST: exported, never called internally | LSP: findReferences = 0 | Yes |
| Name collision | Grep: same name in 2 modules | AST: different body hashes | Yes (VARIANT) |
| Possible duplicate | Grep: similar name | No second signal | No -> UNCONFIRMED |

### Stage 3: Noise Filters

Before scoring, remove common garbage. A corroborated candidate is discarded if it matches any filter:

- **Tests/fixtures/migrations:** Paths matching `__tests__/`, `fixtures/`, `migrations/`, `*.test.ts`, `*.spec.ts`
- **Generated code:** Files with `@generated`, `AUTO-GENERATED`, or in configured generated paths
- **Intentional variants:** Entries in `canonical-registry.md` `allowed_variants` field
- **Already tracked:** Items already present in `docs/sdlc/debt-backlog.md` with status PROMOTE or MIGRATING
- **Active beads:** Items covered by beads in current `docs/sdlc/active/` workflows
- **Low-impact leaf helpers:** Functions with <=1 caller, <=10 LOC, no churn in 30 days
- **Boundary adapters:** One-off wrappers at explicit integration boundaries (single-caller + import-from-external pattern)

### Stage 4: Value Scoring

Surviving candidates receive a Debt Value Score (DVS) across 8 dimensions:

| Dimension | Signal | Weight |
|---|---|---|
| Blast radius | Caller count / module count / layer spread | High |
| Churn | Git change frequency in last 90 days | High |
| Duplication depth | Number of near-copies | Medium |
| Divergence risk | Have copies drifted behaviorally? (AST diff on body) | High |
| Suppression smell | eslint-disable count, age, rising trend | Medium |
| Migration readiness | Does a canonical target already exist? | Medium |
| Business risk | Touches auth/data/billing/core flows -> 2x multiplier | High |
| Fixability | Single migration bead vs architectural surgery | Medium |

DVS = weighted composite, normalized 0-100.

- **DVS >= 70:** PROMOTE candidate
- **DVS 40-69:** WATCH candidate
- **DVS < 40:** IGNORE

### Stage 5: Classification & Output

| Classification | Criteria | Destination |
|---|---|---|
| PROMOTE | 2+ evidence channels, passes filters, DVS >= 70 | `docs/sdlc/debt-backlog.md` + `docs/sdlc/debt-scan-report.md` |
| WATCH | 2+ evidence channels, passes filters, DVS 40-69 | `docs/sdlc/debt-scan-report.md` only |
| MIGRATING | Real debt, already in active cleanup path | `docs/sdlc/debt-scan-report.md` (tracked, not re-emitted) |
| IGNORE | False positive, intentional variant, or DVS < 40 | `docs/sdlc/debt-scan-report.md` (logged for audit trail) |

### Artifact Contracts

#### `references/canonical-registry.md` — Static, Declarative

No mutable state. No shell commands. Agent constructs queries from declarative fields.

**Canonical path prefixes** (used by Architect gate and drift-detector for canonical-creation detection): Any path starting with these prefixes is considered a canonical location. This is prefix-based metadata, not inferred ad hoc.

```
canonical_path_prefixes:
  - lib/utils/
  - lib/storage/patterns/
  - lib/hooks/
  - lib/db/
```

**Entry schema:**

```markdown
### Entry: withSoftDeleteFilter

- **canonical_id:** CANON-001
- **canonical_path:** `lib/storage/patterns/soft-delete.ts`
- **canonical_usage:** `import { withSoftDeleteFilter } from '@/lib/storage/patterns/soft-delete'`
- **match_type:** literal | regex
- **pattern:** `deleted_at IS NULL`
- **include_paths:** `lib/storage/`, `app/api/`
- **exclude_paths:** `__tests__/`, `lib/storage/patterns/soft-delete.ts`
- **allowed_variants:** [] (none) | [list of intentional variant paths]
- **related_rules:** ['no-raw-soft-delete', 'storage/use-soft-delete-filter']
- **migration_rule:** Replace raw `deleted_at IS NULL` WHERE clause with `withSoftDeleteFilter(query)` call
- **owner_domain:** storage | auth | frontend | infra
- **introduced_by:** YYYY-MM-DD
- **sunset_condition:** All violation count reaches 0 for 2 consecutive scans -> entry archived
```

#### `docs/sdlc/debt-backlog.md` — Persisted Remediation Queue

**Item schema:**

```markdown
### DEBT-001

- **debt_id:** DEBT-001
- **title:** hashToken - 3 identical copies
- **type:** TRUE_DUP | ADOPTION | SUPPRESSION | ZOMBIE
- **source_scan:** Evolve Cycle {N}, {date}
- **include_paths:** [list of files containing the debt]
- **canonical_target:** {path:export} (if applicable)
- **confidence:** 0.0-1.0
- **value_score:** {DVS 0-100}
- **evidence_channels:** [list of channels that corroborated]
- **estimated_scope:** {file count}, {caller count}
- **status:** PROMOTE | IMPORTED | RESOLVED
- **imported_by_bead:** - (set when Architect imports into a task)
- **resolved_by_bead:** - (set when migration bead merges)
```

**Lifecycle:** PROMOTE -> IMPORTED (Architect picks up) -> RESOLVED (bead merges). Items at RESOLVED for 2+ scans are archived.

**Architect import rules (Phase 3):**

1. **Relevance gate:** Only import items whose `include_paths` overlap with any primary bead's `Scope` field from the current manifest (planned scope, not post-execution diffs).
2. **Debt budget:** Max 1-2 companion beads per task. Debt beads cannot displace user-requested work.
3. **Overlap only:** Items in modules not covered by any primary bead's scope wait for a future task.

#### `docs/sdlc/debt-scan-report.md` — Time-Series Ledger

All scan history, violation counts, trends, and ratchet baselines. Owned by debt-crawler.

```markdown
# Debt Scan Report

## Scan: Evolve Cycle {N} - {date}

### Adoption Metrics
| Canonical | Violations | Previous | Trend | Delta |
|---|---|---|---|---|
| withSoftDeleteFilter | 1,719 | - | BASELINE | - |

### Duplicate Metrics
| Classification | Count | Previous | Trend |
|---|---|---|---|
| PROMOTE | 3 | - | BASELINE |
| WATCH | 5 | - | BASELINE |
| MIGRATING | 0 | - | - |
| IGNORE | 8 | - | - |
| UNCONFIRMED | 12 | - | - |

### Ratchet Status
- TRUE_DUP (PROMOTE) count: {N}
- Previous baseline: {N}
- Ratchet result: PASS | FAIL

### Findings Detail
(full evidence per finding)
```

#### `references/fitness-functions.md` — One New Rule

```markdown
### Check: Duplicate function count ratchet
**Type:** structural
**What:** PROMOTE-classified duplicate count must not exceed prior Evolve scan baseline
**How:** debt-crawler evaluates during Evolve bead #19; compares current PROMOTE count against previous in `docs/sdlc/debt-scan-report.md`
**Pass:** PROMOTE count <= previous scan count
**Fail action:** BLOCKING within Evolve - debt-crawler writes FAIL to system health report; Conductor must acknowledge and either fix or document justification before Evolve cycle completes
**Scope:** Evaluated by debt-crawler during Evolve bead #19 only. Does NOT run in per-bead sdlc-fitness checks.
**Note:** WATCH count is tracked and trended but advisory only
```

### New Script

**`scripts/extract-functions.sh`** — ESLint-based AST walker for JS/TS. Exports: function name, parameter signature, body hash (SHA-256 of normalized body), line count, branch count, nesting depth. Configured paths as arguments. Output: JSON array of function descriptors. Used by debt-crawler Mode 2 Stage 1.

### Evolve Integration

**#18. Adoption Scan:** Dispatch `debt-crawler` Mode 1. Full pipeline: harvest from canonical-registry + LSP + suppressions -> corroborate -> filter -> score -> classify. Write results to `docs/sdlc/debt-scan-report.md` adoption section. RISING trends -> flag in system health report.

**#19. Duplicate Scan:** Dispatch `debt-crawler` Mode 2. Full pipeline: harvest from AST extraction + LSP + grep + git history -> corroborate -> filter -> score -> classify. PROMOTE findings -> append to `docs/sdlc/debt-backlog.md`. Evaluate ratchet, write pass/fail to system health report. Update all counts in `docs/sdlc/debt-scan-report.md`.

### Future Additions (v2+)

- **Project code embedding index:** Pinecone namespace for project function embeddings -> enables semantic harvest channel in Mode 2
- **Debt precedent ledger:** Track which findings led to real wins vs noise, feeding back into DVS weights
- **Suppression intelligence:** Group suppressions by rule, age, author spread, justification quality
- **Divergence detector:** Separate "duplicate but equivalent" from "duplicate and drifting" via AST diff
- **Hotspot overlay:** Cross debt candidates with churn + incident/findings history

---

## Section 2: Standards-Curator Enrichment (Gaps B + C)

### Architectural Split

- **Scout** (Phase 2) audits the target project's rule and suppression health. Produces per-task artifacts.
- **Evolve** (step #15) reads accumulated audit artifacts across tasks. Proposes SDLC protocol changes.

This aligns with the existing separation: Scout is project-aware, Evolve is system-only.

### Scout Mode: Rule Governance Audit (New)

Added to `standards-curator` Scout mode as a parallel step during Phase 2.

**Step 1: Rule Census.** Read project ESLint config. For each custom rule: name, severity (warn/error/off), category, creation date (git blame on config entry).

**Step 2: Suppression Census.** Scan codebase for `eslint-disable` comments. For each: file path, line, rule(s) disabled, justification text (parsed against structured format).

**Step 3: Suppression-Ratio Analysis.** Per rule:

- `suppression_count` = eslint-disable lines targeting this rule
- `violation_count` = total lint violations (from ESLint output in warn mode)
- `suppression_ratio` = suppression_count / (suppression_count + violation_count)
- `justification_rate` = structured justifications / total suppressions
- `justification_quality` = distribution across quality scores (see hook section)

**Step 4: Classification.** Two classification tracks:

**Track 1 — GAMED (any severity):** A rule at any severity with suppression_ratio > 50% is being circumvented.

**Track 2 — Graduation candidates (warn-level only):**

| Condition | Classification |
|---|---|
| suppression_ratio <= 50% AND violation trend FALLING | READY |
| suppression_ratio <= 50% AND violation trend FLAT/RISING | NOT_READY |
| justification_rate < 10% across all rules | JUSTIFICATION_CRISIS |

**Output:** Written to `docs/sdlc/active/{task-id}/rule-governance-profile.md`:

```markdown
## Rule Governance Profile - {task-id}

### Rule Census
- Custom rules: {N} (warn: {N}, error: {N})

### Suppression Health
- Total eslint-disable: {N}
- Structured justification: {N} ({pct}%)
- Bare / weak: {N} ({pct}%)

### Per-Rule Analysis
| Rule | Severity | Suppressions | Violations | Ratio | Classification |
|---|---|---|---|---|---|
| no-raw-soft-delete | error | 188 | 1,531 | 11% | Healthy |
| no-inline-fetch | warn | 34 | 6 | 85% | GAMED |
| no-raw-auth-check | warn | 2 | 87 | 2% | READY |

### Bare Suppression Count: {N}
```

This profile is referenced by path in runner context packets during Execute and consumed by Evolve for trend analysis.

### Evolve Mode: Rule Governance Protocol Updates (Expanded Step #15)

During Evolve, the standards-curator reads accumulated Rule Governance Profiles and proposes SDLC-level protocol changes.

**Discovery contract:**

- Primary source: `docs/sdlc/active/*/rule-governance-profile.md`
- Secondary source: `docs/sdlc/completed/*/rule-governance-profile.md`
- Lookback window: Last 10 tasks or 30 days, whichever is larger
- Discovery: Glob both paths, sort by task timestamp, take most recent N within window
- Retention: Profiles are never deleted; they move with their task directory from `active/` to `completed/`

**Proposals (all require Conductor approval):**

- **Graduation:** Rules classified READY across 3+ consecutive scans -> propose warn -> error
- **Justification enforcement:** JUSTIFICATION_CRISIS persists -> propose project add `eslint-plugin-eslint-comments/require-description`
- **GAMED rule audit:** Rules classified GAMED -> propose targeted suppression cleanup (fed to debt-crawler as canonical-registry entries if pattern fits)
- **Bare suppression ratchet trend:** Count RISING across scans -> flag as protocol concern

**New fitness function rule (evaluated during Evolve only):**

```markdown
### Check: Bare suppression ratchet
**Type:** governance
**What:** Bare eslint-disable count (score 0) must not increase between Evolve scans
**How:** standards-curator compares current bare count from `docs/sdlc/active/{task-id}/rule-governance-profile.md` against the most recent prior profile found via the Evolve lookback contract (`active/*/rule-governance-profile.md` + `completed/*/rule-governance-profile.md`, last 10 tasks or 30 days)
**Pass:** Bare count <= previous
**Fail action:** WARNING - flag in system health report for Conductor review
**Scope:** Evaluated by standards-curator during Evolve step #15 only
```

### New Hook: eslint-disable Justification Check (Gap C)

**Script:** `hooks/scripts/check-eslint-disable-justification.sh`
**Hook type:** PostToolUse on Write|Edit
**Enforcement:** BLOCKING for score 0 (bare suppressions)

**Structured justification format (required):**

```
// eslint-disable-next-line <rule> -- <reason>; tracked in <DEBT-ID|ISSUE-ID>
// eslint-disable-next-line <rule> -- <reason>; expires <YYYY-MM-DD>
```

Required structure:

- `--` separator after rule name(s)
- Reason text (minimum 10 chars, not just "needed" or "legacy")
- One of: `tracked in <ID>` (linked to debt/issue) OR `expires <date>` (temporary with sunset)

**Justification quality scoring (used by Scout census):**

| Quality | Criteria | Score |
|---|---|---|
| Strong | Structured format + tracked ID + reason > 20 chars | 3 |
| Adequate | Structured format + expires date + reason > 10 chars | 2 |
| Weak | Has `--` separator but missing tracking/expiry | 1 |
| Bare | No justification at all | 0 |

The hook blocks score 0 (bare). Scout census reports distribution across all scores.

**Whole-file policy with migration allowlist:**

The hook scans the entire file (current hook helpers expose file_path and whole-file content only). Pre-existing bare suppressions are covered by a migration allowlist.

**Allowlist identity:** Position-independent fingerprint: `sha256(file_path + normalized_eslint_disable_text + hash_of_surrounding_3_lines)`. Lines can move freely during edits without invalidating the allowlist.

**Allowlist generation:** During Scout (Phase 2), after Rule Governance Audit, the suppression census is written as:

`docs/sdlc/active/{task-id}/suppression-allowlist.md`

```markdown
# Suppression Allowlist - {task-id}
# Auto-generated from Rule Governance Profile
# Fingerprints of pre-existing bare suppressions that pass the justification hook

- fingerprint: a1b2c3d4... | file: lib/storage/access-requests.ts | rule: no-raw-soft-delete
- fingerprint: e5f6g7h8... | file: lib/storage/access-requests.ts | rule: no-raw-soft-delete
...
```

Each new task generates a fresh allowlist. As bare suppressions get fixed, the allowlist shrinks naturally.

**Two tiers:**

- **New files (Write):** All eslint-disable lines must have structured justification. Zero tolerance.
- **Existing files (Edit):** Hook checks all eslint-disable lines. Fingerprints matching the allowlist pass. Non-matching bare suppressions are BLOCKED.

---

## Section 3: Migration Plan Gate (Gap E)

### The Mechanism

When the SDLC creates a new canonical/shared utility, it must also create a migration plan. "Create the canonical AND migrate callers" — not just "create the canonical."

### Bead Schema Extension

New `Intent` field added to the bead format (alongside existing Type). This avoids rippling changes through the bead type enum, HANDOFF.md, or task-profile tables.

**Addition to bead schema in `sdlc-orchestrate/SKILL.md`:**

```markdown
**Intent:** default | migration | registry | debt_companion
```

- `intent: migration` — this bead migrates callers from non-canonical to canonical usage
- `intent: registry` — this bead adds an entry to `references/canonical-registry.md`
- `intent: debt_companion` — this bead addresses a debt-backlog item (from Section 1)
- `intent: default` — standard work (omitted when default)

Intent does not change bead Type. A migration bead is `Type: implement, Intent: migration`.

### Architect Gate (Phase 3 — Primary for BUILD/INVESTIGATE)

**When:** After primary bead manifest is built from Completeness Map, before debt-backlog import.

**Trigger:** Any bead in the manifest whose scope includes creating a new export in a canonical path. Canonical paths are defined by the `canonical_path_prefixes` list in `references/canonical-registry.md`.

**If triggered, require companion beads:**

**1. Migration bead (`intent: migration`):**

```markdown
# Bead: IMPL-004
**Type:** implement
**Intent:** migration
**Dependencies:** [IMPL-003] (the bead creating the canonical)
**Scope:** [files to migrate]
**Input:**
  - migration_target: {path:export of the new canonical}
  - callers_to_migrate: [explicit file list from Scout/reuse-scout]
  - migration_strategy: INLINE | STAGED | DEFERRED
  - estimated_scope: {file count}, {caller count}
**Output:** Migrated files + (for STAGED/DEFERRED) migration report for Conductor
```

Migration strategies:

- **INLINE:** Migrate all callers in this task. Required when caller count is small (< 10).
- **STAGED:** Migrate N highest-churn callers inline, defer rest. Must specify which callers are inline vs deferred.
- **DEFERRED:** All callers deferred. Requires substantive justification (not just "too many files"). Conductor pushes back: "can you do 5-10 of the highest-churn callers inline?"

**2. Registry bead (`intent: registry`):** Adds entry to `references/canonical-registry.md` with all required fields.

**3. Debt-companion beads (`intent: debt_companion`):** Only if debt-backlog items overlap with planned bead scopes (Section 1 import rules apply).

**Manifest order:** Primary beads -> Migration bead(s) -> Registry bead -> Debt-companion beads

### L1 Sentinel Safety Net (Phase 4 — Primary for REPAIR/Clear)

**Role by profile:**

- **BUILD/INVESTIGATE (Phase 3 runs):** L1 = safety net for cases Architect missed
- **REPAIR (Phase 3 skipped):** L1 = primary and only guard
- **Clear beads (Architect bypassed):** L1 = primary and only guard

**Owner:** drift-detector. This check is assigned explicitly to drift-detector, not left as generic sentinel judgment. Drift-detector already checks DRY/SSOT/SoC/pattern/boundary violations in the L1 sentinel loop.

**New check added to drift-detector's catalog:** `MIGRATION_PLAN_MISSING`

**Detection method:** After runner submission, drift-detector:

1. Sources changed files from **git diff** (worktree diff or `git diff --name-only` against the bead's base commit) — NOT from runner prose output. This is the only deterministic source; the runner's `## Changed Files` section serves as a cross-check, not the primary input.
2. Runs LSP `workspaceSymbol` or AST export analysis on the changed files to identify new exports
3. Compares new exports against `canonical_path_prefixes` from `references/canonical-registry.md`
4. Checks current manifest for any bead with `intent: migration` targeting this canonical

**drift-detector context requirement:** The drift-detector dispatch prompt must include both the git diff context (base commit ref for the bead) AND the current bead manifest, so it can deterministically prove "no migration companion exists." This is a new context injection alongside existing Convention Map and fitness function references.

**If new export in canonical path AND no `intent: migration` bead exists:**

Emit `MIGRATION_PLAN_MISSING` signal. BLOCKING — bead cannot advance past `submitted`.

**Conductor resolution options:**

1. Create `intent: migration` bead retroactively (added to manifest, executed before Synthesize)
2. Document in decision trace why migration is not needed (e.g., internal helper wrongly placed in canonical path -> move it)

### Phase 5: Synthesize — Migration Completion Check

gap-analyst Finisher reports remaining unmigrated callers from STAGED/DEFERRED migration beads. It does NOT auto-create anything.

Flow: gap-analyst Finisher -> reports "IMPL-004 (migration) completed 10/1,719 callers, 1,709 remaining" -> Conductor reads report -> Conductor writes entries to `docs/sdlc/debt-backlog.md` with status PROMOTE, source referencing the migration bead.

---

## Prerequisites

Before implementing any of the above:

1. **Normalize Evolve bead count header.** `sdlc-evolve/SKILL.md` line 24 says "The 5 Evolution Bead Types" but the file defines 17. Fix to accurate count before adding #18 and #19.

2. **Add Intent field to bead schema.** Add `Intent: default | migration | registry | debt_companion` to the bead format in `sdlc-orchestrate/SKILL.md` (bead schema block) and `HANDOFF.md` wherever the bead schema is documented.

3. **Verify drift-detector can receive manifest context.** Current L1 dispatch gives drift-detector the runner's output. The new `MIGRATION_PLAN_MISSING` check requires the current bead manifest as additional context. Update the dispatch prompt template to include manifest.

---

## Files Created

| File | Type | Purpose |
|---|---|---|
| `agents/debt-crawler.md` | Agent spec | Debt intelligence engine (Modes 1+2) |
| `scripts/extract-functions.sh` | Script | ESLint-based AST function extraction (JS/TS) |
| `hooks/scripts/check-eslint-disable-justification.sh` | Hook script | Structured justification enforcement |
| `references/canonical-registry.md` | Reference (static) | Declarative canonical definitions |
| `docs/sdlc/debt-backlog.md` | Artifact (mutable) | Persisted remediation queue |
| `docs/sdlc/debt-scan-report.md` | Artifact (mutable) | Time-series scan ledger |

## Files Modified

| File | Change |
|---|---|
| `agents/standards-curator.md` | Add Scout Rule Governance Audit mode; expand Evolve mode with lookback contract |
| `agents/drift-detector.md` | Add `MIGRATION_PLAN_MISSING` check to catalog; add manifest context requirement |
| `skills/sdlc-orchestrate/SKILL.md` | Add Intent to bead schema; add canonical-creation check + companion bead requirement to Phase 3; add drift-detector manifest context to Phase 4 L1; add migration completion check to Phase 5 |
| `skills/sdlc-evolve/SKILL.md` | Fix bead type count header; add #18 Adoption Scan and #19 Duplicate Scan |
| `hooks/hooks.json` | Add PostToolUse entry for `check-eslint-disable-justification.sh` |
| `references/fitness-functions.md` | Add duplicate function count ratchet rule; add bare suppression ratchet rule |
| `skills/sdlc-normalize/SKILL.md` | Add `rule-governance-profile.md` and `suppression-allowlist.md` to resume artifact list alongside existing `standards-profile.md`, `quality-budget.md`, and `observability-profile.md` |
| `agents/sonnet-implementer.md` | Require normalized `## Changed Files` section in output format — machine-readable list of file paths, one per line — for deterministic L1 consumption by drift-detector |
| `hooks/tests/test-hooks.sh` | Add fixture coverage for `check-eslint-disable-justification.sh`: bare suppression blocked, structured justification passes, allowlist fingerprint matches, Write vs Edit tier behavior |
| `docs/HANDOFF.md` | Add Intent field to bead schema; document new agent, artifacts, and hooks |

## Success Criteria

| Metric | Current | Target |
|---|---|---|
| Canonicals with adoption tracking | 0 | All entries in canonical-registry.md |
| New canonicals created without migration plan | Unchecked | 0 (BLOCKED by Architect gate or L1) |
| Bare eslint-disable in new code | Unchecked | 0 (BLOCKED by hook) |
| Warn-level rules with governance review | 0 | All (via Scout audit) |
| Evolve duplicate scan | Does not exist | Runs every cycle with ratchet |
| Debt-backlog items with structured schema | Does not exist | All PROMOTE findings tracked |

## Open Questions

1. **DVS weight calibration.** The 8 dimension weights need tuning after initial scans. The variation-classifier (Deming PDSA) can calibrate these during Evolve — but initial weights are judgment calls.
2. **extract-functions.sh scope.** The initial implementation covers JS/TS. If the project gains non-JS code, the extraction primitive needs extending or a complementary tool.
3. **Allowlist performance.** For very large codebases, computing SHA-256 fingerprints of all pre-existing suppressions during Scout may add meaningful time. Monitor and optimize if needed.
