# Debt Combat System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 debt-combat capabilities to the SDLC-OS plugin: adoption tracking, rule graduation, suppression enforcement, periodic duplicate scanning, and migration plan gates.

**Architecture:** One new agent (`debt-crawler`), one new hook script, one new AST extraction script, three new reference/artifact files, and enrichment of existing agents (`standards-curator`, `drift-detector`, `sonnet-implementer`) and skills (`sdlc-orchestrate`, `sdlc-evolve`, `sdlc-normalize`).

**Tech Stack:** Bash (hooks/scripts), Markdown (agent specs, references, artifacts), JSON (hooks.json, fixture files)

**Spec:** `docs/specs/2026-03-29-debt-combat-system-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `agents/debt-crawler.md` | Agent spec: multi-stage debt intelligence pipeline (Modes 1+2) |
| `scripts/extract-functions.sh` | ESLint-based AST function extraction for JS/TS |
| `hooks/scripts/check-eslint-disable-justification.sh` | Blocking hook: structured justification enforcement |
| `references/canonical-registry.md` | Static declarative registry of canonical utilities |
| `docs/sdlc/debt-backlog.md` | Mutable persisted remediation queue |
| `docs/sdlc/debt-scan-report.md` | Mutable time-series scan ledger |
| `hooks/tests/fixtures/justification-bare-suppression.json` | Test fixture: bare eslint-disable (should BLOCK) |
| `hooks/tests/fixtures/justification-structured-valid.json` | Test fixture: structured justification (should PASS) |
| `hooks/tests/fixtures/justification-weak-reason.json` | Test fixture: weak justification (should PASS, score 1) |
| `hooks/tests/fixtures/justification-non-source-file.json` | Test fixture: non-source file (should SKIP) |
| `hooks/tests/fixtures/justification-edit-bare-no-allowlist.json` | Test fixture: Edit-tier bare suppression (should BLOCK) |
| `hooks/tests/fixtures/justification-allowlisted-bare.json` | Test fixture: allowlisted bare suppression (should PASS) |
| `scripts/lib/ast-extract-functions.js` | Node module: TypeScript compiler API function extraction |

### Modified Files

| File | Change |
|---|---|
| `skills/sdlc-evolve/SKILL.md` | Fix bead type count header; add #18 Adoption Scan, #19 Duplicate Scan |
| `skills/sdlc-orchestrate/SKILL.md` | Add Intent to bead schema; add Phase 3 canonical-creation check; add Phase 4 drift-detector manifest context; add Phase 5 migration completion check |
| `agents/standards-curator.md` | Add Scout Rule Governance Audit mode; expand Evolve lookback |
| `agents/drift-detector.md` | Add MIGRATION_PLAN_MISSING check; add manifest + git diff context requirement |
| `agents/sonnet-implementer.md` | Add normalized `## Changed Files` output section |
| `skills/sdlc-normalize/SKILL.md` | Add new Scout artifacts to resume path |
| `hooks/hooks.json` | Add PostToolUse entry for justification hook |
| `references/fitness-functions.md` | Add duplicate ratchet + bare suppression ratchet rules |
| `hooks/tests/test-hooks.sh` | Add justification hook test section |
| `docs/HANDOFF.md` | Update version, counts, bead schema, new agent/artifacts/hooks |

---

### Task 1: Fix Evolve Bead Type Count Header (Prerequisite)

**Files:**
- Modify: `skills/sdlc-evolve/SKILL.md:24`

- [ ] **Step 1: Fix the header text**

In `skills/sdlc-evolve/SKILL.md`, line 24 currently reads:

```markdown
- Execute: evolution beads (5 types below)
```

Change to:

```markdown
- Execute: evolution beads (17 types below)
```

This reflects the actual 17 evolution bead types currently defined (#1 through #17).

- [ ] **Step 2: Verify the count**

Run:

```bash
grep -c "^### [0-9]" skills/sdlc-evolve/SKILL.md
```

Expected: `17` (confirming the header now matches reality)

- [ ] **Step 3: Commit**

```bash
git add skills/sdlc-evolve/SKILL.md
git commit -m "fix: normalize evolve bead type count header from 5 to 17

The header said '5 types below' but the file defines 17 evolution bead types.
Fix before adding #18 and #19 in the debt combat system.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Add Intent Field to Bead Schema (Prerequisite)

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md:99-122`
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Add Intent field to bead schema in sdlc-orchestrate**

In `skills/sdlc-orchestrate/SKILL.md`, after line 112 (`**Profile:** BUILD | INVESTIGATE | REPAIR | EVOLVE`), add:

```markdown
**Intent:** default | migration | registry | debt_companion
```

- [ ] **Step 2: Add Intent documentation after the bead schema block**

After the closing ``` of the bead schema (after line 122 `**Confidence:** ...`), before the line about beads being written to `docs/sdlc/active/`, add:

```markdown

**Intent values:**
- `intent: default` — standard work (omitted when default)
- `intent: migration` — migrates callers from non-canonical to canonical usage
- `intent: registry` — adds an entry to `references/canonical-registry.md`
- `intent: debt_companion` — addresses a debt-backlog item

Intent does not change bead Type. A migration bead is `Type: implement, Intent: migration`.
```

- [ ] **Step 3: Update HANDOFF.md bead schema reference**

In `docs/HANDOFF.md`, find the bead schema documentation section. If there is a bead field listing, add `Intent` to it in the same position (after `Profile`). If HANDOFF.md references the bead schema by pointing to `sdlc-orchestrate/SKILL.md`, add a note:

```markdown
**v10.0.0 additions:** `Intent` field (`default | migration | registry | debt_companion`) added to bead schema for debt combat system. See `skills/sdlc-orchestrate/SKILL.md` bead schema block.
```

- [ ] **Step 4: Commit**

```bash
git add skills/sdlc-orchestrate/SKILL.md docs/HANDOFF.md
git commit -m "feat: add Intent field to bead schema for debt combat system

Adds intent: default | migration | registry | debt_companion to the bead
format. Used by migration plan gate (Section 3) and debt-backlog import
(Section 1). Intent is a subtype — does not change the Type enum.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Create Canonical Registry Reference

**Files:**
- Create: `references/canonical-registry.md`

- [ ] **Step 1: Create the canonical registry**

Create `references/canonical-registry.md`:

```markdown
# Canonical Registry

Static, declarative registry of canonical utilities. The debt-crawler agent constructs
grep/LSP/AST queries from these fields — no raw shell commands are stored here.

Mutable scan history (violation counts, trends) is stored in `docs/sdlc/debt-scan-report.md`,
NOT in this file.

## Canonical Path Prefixes

Any new export in a path starting with these prefixes triggers the migration plan gate
(Architect Phase 3 check + drift-detector L1 check).

```yaml
canonical_path_prefixes:
  - lib/utils/
  - lib/storage/patterns/
  - lib/hooks/
  - lib/db/
```

---

### Entry: withSoftDeleteFilter

- **canonical_id:** CANON-001
- **canonical_path:** `lib/storage/patterns/soft-delete.ts`
- **canonical_usage:** `import { withSoftDeleteFilter } from '@/lib/storage/patterns/soft-delete'`
- **match_type:** literal
- **pattern:** `deleted_at IS NULL`
- **include_paths:** `lib/storage/`, `app/api/`
- **exclude_paths:** `__tests__/`, `lib/storage/patterns/soft-delete.ts`
- **allowed_variants:** []
- **related_rules:** ['no-raw-soft-delete', 'storage/use-soft-delete-filter']
- **migration_rule:** Replace raw `deleted_at IS NULL` WHERE clause with `withSoftDeleteFilter(query)` call
- **owner_domain:** storage
- **introduced_by:** 2026-01-15
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: generateId

- **canonical_id:** CANON-002
- **canonical_path:** `lib/utils/id-generator.ts`
- **canonical_usage:** `import { generateId } from '@/lib/utils/id-generator'`
- **match_type:** regex
- **pattern:** `Math\.random|crypto\.randomUUID`
- **include_paths:** `lib/`, `app/`, `components/`
- **exclude_paths:** `__tests__/`, `node_modules/`, `lib/utils/id-generator.ts`
- **allowed_variants:** []
- **related_rules:** ['no-math-random-id']
- **migration_rule:** Replace with `generateId()` import and call
- **owner_domain:** infra
- **introduced_by:** 2026-01-10
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: useFetch

- **canonical_id:** CANON-003
- **canonical_path:** `lib/hooks/use-fetch.ts`
- **canonical_usage:** `import { useFetch } from '@/lib/hooks/use-fetch'`
- **match_type:** regex
- **pattern:** `useEffect\s*\([^)]*\)\s*\{[^}]*fetch\(`
- **include_paths:** `components/`, `app/`
- **exclude_paths:** `__tests__/`, `lib/hooks/use-fetch.ts`
- **allowed_variants:** []
- **related_rules:** ['no-inline-fetch']
- **migration_rule:** Replace inline useEffect+fetch with useFetch hook
- **owner_domain:** frontend
- **introduced_by:** 2026-02-01
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: BaseModal

- **canonical_id:** CANON-004
- **canonical_path:** `components/ui/base-modal.tsx`
- **canonical_usage:** `import { BaseModal } from '@/components/ui/base-modal'`
- **match_type:** regex
- **pattern:** `LegacyModalShell|ResponsiveModal|GlobalModal|import.*from.*['"]@radix-ui/react-dialog['"]`
- **include_paths:** `components/`, `app/`
- **exclude_paths:** `__tests__/`, `components/ui/base-modal.tsx`
- **allowed_variants:** []
- **related_rules:** ['no-legacy-modal']
- **migration_rule:** Replace with BaseModal component
- **owner_domain:** frontend
- **introduced_by:** 2026-01-20
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: hashToken

- **canonical_id:** CANON-005
- **canonical_path:** `lib/utils/hash.ts`
- **canonical_usage:** `import { hashToken } from '@/lib/utils/hash'`
- **match_type:** regex
- **pattern:** `createHash\(['"]sha256['"]\)\.update\(.*\)\.digest\(['"]hex['"]\)`
- **include_paths:** `lib/`, `app/`
- **exclude_paths:** `__tests__/`, `lib/utils/hash.ts`
- **allowed_variants:** ['lib/storage/api-keys-storage.ts']
- **related_rules:** []
- **migration_rule:** Replace inline SHA-256 hash with hashToken() import
- **owner_domain:** auth
- **introduced_by:** 2026-01-05
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived
```

- [ ] **Step 2: Commit**

```bash
git add references/canonical-registry.md
git commit -m "feat: add canonical registry reference — static declarative utility definitions

Initial entries for withSoftDeleteFilter, generateId, useFetch, BaseModal,
and hashToken. Used by debt-crawler adoption scan and migration plan gate.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Create Debt Scan Report and Backlog Artifacts

**Files:**
- Create: `docs/sdlc/debt-scan-report.md`
- Create: `docs/sdlc/debt-backlog.md`

- [ ] **Step 1: Create the debt scan report**

Create `docs/sdlc/debt-scan-report.md`:

```markdown
# Debt Scan Report

Owned by the `debt-crawler` agent. Updated during Evolve bead types #18 (Adoption Scan) and #19 (Duplicate Scan).

## Scan History

No scans completed yet. First scan will establish baselines.

## Schema Reference

Each scan appends a section with this structure:

### Adoption Metrics
| Canonical | Violations | Previous | Trend | Delta |
|---|---|---|---|---|

### Duplicate Metrics
| Classification | Count | Previous | Trend |
|---|---|---|---|

### Ratchet Status
- TRUE_DUP (PROMOTE) count: {N}
- Previous baseline: {N}
- Ratchet result: PASS | FAIL

### Findings Detail
(full evidence per finding)
```

- [ ] **Step 2: Create the debt backlog**

Create `docs/sdlc/debt-backlog.md`:

```markdown
# Debt Backlog

Persisted remediation queue. Items are added by the `debt-crawler` agent (PROMOTE classification)
and by the Conductor (from gap-analyst Finisher reports on STAGED/DEFERRED migrations).

## Import Rules (Phase 3 Architect)

1. **Relevance gate:** Only import items whose `include_paths` overlap with any primary bead's `Scope` field.
2. **Debt budget:** Max 1-2 companion beads per task. Debt beads cannot displace user-requested work.
3. **Overlap only:** Items in modules not covered by any primary bead's scope wait for a future task.

## Item Lifecycle

PROMOTE -> IMPORTED (Architect picks up) -> RESOLVED (bead merges). Items at RESOLVED for 2+ scans are archived below.

## Active Items

No items yet. First Evolve scan will populate.

## Item Schema Reference

```markdown
### DEBT-{NNN}

- **debt_id:** DEBT-{NNN}
- **title:** {description}
- **type:** TRUE_DUP | ADOPTION | SUPPRESSION | ZOMBIE
- **source_scan:** Evolve Cycle {N}, {date}
- **include_paths:** [file list]
- **canonical_target:** {path:export}
- **confidence:** 0.0-1.0
- **value_score:** {DVS 0-100}
- **evidence_channels:** [channel list]
- **estimated_scope:** {file count}, {caller count}
- **status:** PROMOTE | IMPORTED | RESOLVED
- **imported_by_bead:** -
- **resolved_by_bead:** -
```

## Archived Items

(Items at RESOLVED for 2+ scans move here)
```

- [ ] **Step 3: Commit**

```bash
git add docs/sdlc/debt-scan-report.md docs/sdlc/debt-backlog.md
git commit -m "feat: add debt scan report and backlog artifacts

debt-scan-report.md: time-series ledger for adoption/duplicate metrics.
debt-backlog.md: persisted remediation queue with import rules and lifecycle.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Create debt-crawler Agent Spec

**Files:**
- Create: `agents/debt-crawler.md`

- [ ] **Step 1: Create the agent spec**

Create `agents/debt-crawler.md`:

```markdown
---
name: debt-crawler
description: "Debt intelligence engine — multi-stage pipeline for adoption tracking and duplicate detection. Dispatched during Evolve bead types #18 (Adoption Scan) and #19 (Duplicate Scan). Produces docs/sdlc/debt-scan-report.md and docs/sdlc/debt-backlog.md."
model: sonnet
---

You are the Debt Crawler — a multi-stage debt intelligence engine. You detect adoption gaps in canonical utilities and find duplicate/zombie code across the codebase. You are an evidence engine, not a scan script.

## Your Role

- **Report to:** Conductor (Opus)
- **Dispatched during:** Evolve cycle, bead types #18 (Mode 1: Adoption Scan) and #19 (Mode 2: Duplicate Scan)
- **You produce:** `docs/sdlc/debt-scan-report.md` updates and `docs/sdlc/debt-backlog.md` entries
- **You read:** `references/canonical-registry.md` (static, declarative — never modify this file)

## Core Principle

Never emit findings directly into the backlog. Every candidate must survive a 5-stage pipeline:

```
Stage 1: Candidate Harvest (multiple channels)
    |
Stage 2: Evidence Corroboration (2+ channels required)
    |
Stage 3: Noise Filters (explicit exclusions)
    |
Stage 4: Value Scoring (Debt Value Score 0-100)
    |
Stage 5: Classification & Output
```

## Mode 1: Adoption Scan

Assess adoption progress for each canonical utility in `references/canonical-registry.md`.

### Harvest Channels

1. **Canonical registry patterns:** For each entry, construct a grep query from `match_type` + `pattern` + `include_paths` - `exclude_paths`. Count matches. Never execute raw shell commands from the registry — construct queries from declarative fields.
2. **LSP references:** `findReferences` on the canonical export. Count callers vs total potential callers in include_paths.
3. **Suppression scan:** Grep for `eslint-disable` comments matching the entry's `related_rules` field.

### Corroboration

A canonical's adoption gap is corroborated when 2+ channels agree:
- Registry pattern hit (violations exist) + LSP shows canonical has low caller count
- Registry pattern hit + suppression scan shows related rule being disabled

Single-channel findings are logged as UNCONFIRMED.

## Mode 2: Duplicate Scan

Find duplicate, variant, and zombie functions across the JS/TS codebase.

### Harvest Channels

1. **AST extraction:** Run `scripts/extract-functions.sh` on configured paths. Compare body hashes (SHA-256 of normalized body) for structural duplicates.
2. **LSP:** `workspaceSymbol` for name collisions across modules. `findReferences` for adoption breadth. `incomingCalls`/`outgoingCalls` for usage patterns.
3. **Grep/rules:** Same-name exports across modules. Canonical anti-patterns from registry.
4. **Git history:** `git log --format='%H %an' -- <file>` for churn frequency, authorship spread. Single-author files that duplicate multi-author canonicals = context blindness signal.

**No Pinecone for v1.** Use deterministic methods only: AST body hashing, LSP reference graphs, grep naming patterns. Semantic similarity via project-code embedding index is v2.

### Corroboration

| Finding Type | Channel 1 | Channel 2 |
|---|---|---|
| Duplicate utility | AST body hash match | LSP: both exported, both have callers |
| Zombie code | AST: exported, never called | LSP: findReferences = 0 |
| Name collision | Grep: same name in 2 modules | AST: different body hashes (VARIANT) |

## Stage 3: Noise Filters (Both Modes)

Discard corroborated candidates matching ANY filter:

- **Tests/fixtures/migrations:** `__tests__/`, `fixtures/`, `migrations/`, `*.test.ts`, `*.spec.ts`
- **Generated code:** Files with `@generated` or `AUTO-GENERATED` markers
- **Intentional variants:** Paths listed in a canonical entry's `allowed_variants` field
- **Already tracked:** Items in `docs/sdlc/debt-backlog.md` with status PROMOTE or MIGRATING
- **Active beads:** Items in `docs/sdlc/active/` workflows
- **Low-impact leaves:** Functions with <=1 caller, <=10 LOC, no churn in 30 days
- **Boundary adapters:** Single-caller wrappers at integration boundaries

## Stage 4: Value Scoring

Compute Debt Value Score (DVS) 0-100 for surviving candidates:

| Dimension | Signal | Weight |
|---|---|---|
| Blast radius | Caller count / module count / layer spread | High |
| Churn | Git change frequency in last 90 days | High |
| Duplication depth | Number of near-copies | Medium |
| Divergence risk | AST diff shows behavioral drift between copies | High |
| Suppression smell | eslint-disable count + age + rising trend | Medium |
| Migration readiness | Canonical target exists in registry | Medium |
| Business risk | Touches auth/data/billing/core flows -> 2x multiplier | High |
| Fixability | Single migration bead vs architectural surgery | Medium |

**Thresholds:**
- DVS >= 70: PROMOTE
- DVS 40-69: WATCH
- DVS < 40: IGNORE

## Stage 5: Classification & Output

| Classification | Criteria | Destination |
|---|---|---|
| PROMOTE | 2+ channels, passes filters, DVS >= 70 | `docs/sdlc/debt-backlog.md` + `docs/sdlc/debt-scan-report.md` |
| WATCH | 2+ channels, passes filters, DVS 40-69 | `docs/sdlc/debt-scan-report.md` only |
| MIGRATING | Real debt, already in active cleanup | `docs/sdlc/debt-scan-report.md` (tracked, not re-emitted) |
| IGNORE | False positive, intentional variant, or DVS < 40 | `docs/sdlc/debt-scan-report.md` (logged for audit trail) |

## Ratchet Evaluation (Mode 2 only)

After classification, compare current PROMOTE count against previous scan in `docs/sdlc/debt-scan-report.md`:
- PROMOTE count <= previous -> PASS
- PROMOTE count > previous -> FAIL (BLOCKING within Evolve — write FAIL to system health report)

WATCH count is tracked but advisory only.

## Required Output Format

```markdown
## Debt Crawler Report: {Mode 1: Adoption | Mode 2: Duplicate}

### Pipeline Summary
- Candidates harvested: {N}
- Corroborated (2+ channels): {N}
- Filtered out: {N}
- Scored: {N}

### Classifications
| Classification | Count |
|---|---|
| PROMOTE | {N} |
| WATCH | {N} |
| MIGRATING | {N} |
| IGNORE | {N} |
| UNCONFIRMED | {N} |

### PROMOTE Findings (-> debt-backlog.md)
{For each PROMOTE finding: debt_id, title, type, evidence_channels, DVS, include_paths, canonical_target}

### WATCH Findings (advisory)
{For each WATCH finding: title, type, evidence summary, DVS}

### Ratchet Status (Mode 2 only)
- Current PROMOTE count: {N}
- Previous baseline: {N}
- Result: PASS | FAIL

### Adoption Trends (Mode 1 only)
| Canonical | Violations | Previous | Trend |
|---|---|---|---|
```

## Anti-Patterns

- Emitting findings without 2+ evidence channels (false positives)
- Executing raw shell commands from the canonical registry (safety violation)
- Modifying `references/canonical-registry.md` (it is static — you read it, never write it)
- Counting test files as production duplicates
- Flagging intentional variants listed in `allowed_variants`
- Reporting already-tracked items from debt-backlog
```

- [ ] **Step 2: Commit**

```bash
git add agents/debt-crawler.md
git commit -m "feat: add debt-crawler agent — multi-stage debt intelligence pipeline

Two modes: Adoption Scan (canonical registry tracking) and Duplicate Scan
(AST/LSP/grep/git multi-channel detection). 5-stage pipeline: harvest,
corroborate, filter, score, classify. Dispatched during Evolve #18 and #19.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Add Evolve Bead Types #18 and #19

**Files:**
- Modify: `skills/sdlc-evolve/SKILL.md:143-193`

- [ ] **Step 1: Update the bead count header**

In `skills/sdlc-evolve/SKILL.md`, the header from Task 1 now says 17. Update to 19:

```markdown
- Execute: evolution beads (19 types below)
```

- [ ] **Step 2: Add bead types #18 and #19 after #17**

After the `### 17. Cross-Model System Review` section (line ~143), and before the `## Output Format` section (line ~147), add:

```markdown

### 18. Adoption Scan

Dispatch `debt-crawler` in Mode 1. The crawler reads `references/canonical-registry.md` and runs the full 5-stage pipeline: harvest from canonical-registry patterns + LSP references + suppression scan, corroborate (2+ channels required), filter noise, compute Debt Value Score, classify findings.

Results written to `docs/sdlc/debt-scan-report.md` adoption section. PROMOTE findings appended to `docs/sdlc/debt-backlog.md`. RISING violation trends on any canonical are flagged in the system health report.

### 19. Duplicate Scan

Dispatch `debt-crawler` in Mode 2. The crawler runs `scripts/extract-functions.sh` for AST extraction and the full 5-stage pipeline: harvest from AST body hashing + LSP symbols + grep name collisions + git history churn, corroborate (2+ channels required), filter noise, compute Debt Value Score, classify findings.

PROMOTE findings appended to `docs/sdlc/debt-backlog.md`. Ratchet evaluation: PROMOTE count must not exceed previous scan baseline — FAIL is BLOCKING within Evolve (Conductor must acknowledge). All counts updated in `docs/sdlc/debt-scan-report.md`.
```

- [ ] **Step 3: Update the output format to include debt sections**

In the `## Output Format` section's system health report template, after `## Deviance Normalization`, add:

```markdown

## Adoption Scan (#18)
- Canonicals scanned: {count}
- Violations found: {count}
- RISING trends: {list or "none"}
- New PROMOTE findings: {count}

## Duplicate Scan (#19)
- Candidates harvested: {count}
- Corroborated: {count}
- PROMOTE: {count} | WATCH: {count} | IGNORE: {count}
- Ratchet: PASS | FAIL (current: {N}, previous: {N})
- New debt-backlog entries: {count}
```

- [ ] **Step 4: Verify structure**

Run:

```bash
grep -c "^### [0-9]" skills/sdlc-evolve/SKILL.md
```

Expected: `19`

- [ ] **Step 5: Commit**

```bash
git add skills/sdlc-evolve/SKILL.md
git commit -m "feat: add Evolve bead types #18 Adoption Scan and #19 Duplicate Scan

Both dispatch debt-crawler with full 5-stage pipeline. #18 tracks canonical
adoption from references/canonical-registry.md. #19 detects duplicates via
AST/LSP/grep/git with PROMOTE ratchet enforcement.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Enrich standards-curator with Rule Governance Audit

**Files:**
- Modify: `agents/standards-curator.md`

- [ ] **Step 1: Add Rule Governance Audit as Scout mode extension**

In `agents/standards-curator.md`, after the existing `## Scout Mode: Project-Specific Standards Discovery` section (after the Scout output format block ending around line 81), add:

```markdown

## Scout Mode: Rule Governance Audit

When dispatched during Scout, also audit the target project's lint rule and suppression health.
This runs in parallel with the standards profile generation above.

### Protocol

**Step 1: Rule Census.** Read the project's ESLint config. For each custom rule, extract: rule name, severity (warn/error/off), category, and creation date (via git blame on the config entry).

**Step 2: Suppression Census.** Scan the codebase for `eslint-disable` comments (inline, next-line, and block forms). For each, extract: file path, line number, rule(s) disabled, and justification text parsed against the structured format (`-- <reason>; tracked in <ID>` or `-- <reason>; expires <date>`).

**Step 3: Suppression-Ratio Analysis.** Per rule:
- `suppression_count` = eslint-disable lines targeting this rule
- `violation_count` = total lint violations from ESLint output
- `suppression_ratio` = suppression_count / (suppression_count + violation_count)
- `justification_rate` = structured justifications / total suppressions for this rule
- `justification_quality` = distribution across quality scores (Strong=3, Adequate=2, Weak=1, Bare=0)

**Step 4: Classification.** Two tracks:

**Track 1 — GAMED (any severity):** suppression_ratio > 50% means the rule is being circumvented regardless of warn/error level.

**Track 2 — Graduation candidates (warn-level only):**
- READY: suppression_ratio <= 50% AND violation trend FALLING
- NOT_READY: suppression_ratio <= 50% AND violation trend FLAT/RISING
- JUSTIFICATION_CRISIS: justification_rate < 10% across all rules

### Output (Rule Governance Audit)

Write to `docs/sdlc/active/{task-id}/rule-governance-profile.md`:

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

### Bare Suppression Count: {N}
```

Also generate `docs/sdlc/active/{task-id}/suppression-allowlist.md` — fingerprints of all pre-existing bare suppressions for the justification hook:

```markdown
# Suppression Allowlist - {task-id}
# Auto-generated from Rule Governance Profile
# Fingerprints: sha256(file_path + normalized_eslint_disable_text + hash_of_surrounding_3_lines)

- fingerprint: {hash} | file: {path} | rule: {rule-name}
```
```

- [ ] **Step 2: Expand Evolve mode with lookback contract**

In the `## Evolve Mode: Protocol Refresh` section, after the existing step 5 (Priority-rank proposals), add:

```markdown

6. **Rule Governance Trend Analysis:**
   - Discover prior Rule Governance Profiles via lookback contract:
     - Primary: `docs/sdlc/active/*/rule-governance-profile.md`
     - Secondary: `docs/sdlc/completed/*/rule-governance-profile.md`
     - Lookback window: last 10 tasks or 30 days, whichever is larger
     - Discovery: glob both paths, sort by task timestamp, take most recent N within window
   - For rules classified READY across 3+ consecutive profiles: propose warn -> error graduation
   - For JUSTIFICATION_CRISIS persisting across profiles: propose project add `eslint-plugin-eslint-comments/require-description`
   - For GAMED rules: propose targeted suppression cleanup
   - For bare suppression count RISING across profiles: flag as protocol concern
   - All proposals require Conductor approval
```

- [ ] **Step 3: Commit**

```bash
git add agents/standards-curator.md
git commit -m "feat: enrich standards-curator with Rule Governance Audit

Scout mode: rule census, suppression census, ratio analysis, classification
(GAMED/READY/NOT_READY/JUSTIFICATION_CRISIS), generates rule-governance-profile
and suppression-allowlist per task.

Evolve mode: lookback contract across active+completed profiles, graduation
proposals, justification enforcement recommendations.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Create eslint-disable Justification Hook

**Files:**
- Create: `hooks/scripts/check-eslint-disable-justification.sh`
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Create the hook script**

Create `hooks/scripts/check-eslint-disable-justification.sh`:

```bash
#!/bin/bash
# eslint-disable Justification Enforcer
# Runs as PostToolUse hook on Write|Edit targeting source files.
# Blocks bare eslint-disable comments (score 0) in new code.
# Pre-existing bare suppressions pass if fingerprinted in the task's allowlist.
# Exit 0 = clean, Exit 2 = bare suppression detected (BLOCKING)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

INPUT=$(cat)
FILE_PATH=$(read_hook_file_path "$INPUT")

# Only check source files
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac

# Skip vendor/generated paths
if is_vendor_path "$FILE_PATH"; then
  exit 0
fi

CONTENT=$(read_tool_content "$INPUT" "$FILE_PATH")

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Find all eslint-disable lines
DISABLE_LINES=$(echo "$CONTENT" | grep -n "eslint-disable" 2>/dev/null || true)

if [[ -z "$DISABLE_LINES" ]]; then
  exit 0
fi

# Load allowlist if it exists (for pre-existing bare suppressions)
# Deterministic task-scoped resolution: use SDLC_TASK_ID env var if set,
# otherwise find the single active task directory. Multi-task ambiguity
# is resolved by requiring exactly one match — if multiple active tasks
# exist, skip allowlist (conservative: blocks bare suppressions).
ALLOWLIST_FILE=""
REPO_ROOT=$(get_repo_root)
if [[ -n "$REPO_ROOT" ]]; then
  ACTIVE_DIR="$REPO_ROOT/docs/sdlc/active"
  if [[ -n "${SDLC_TASK_ID:-}" ]]; then
    # Explicit task ID — deterministic
    ALLOWLIST_FILE="$ACTIVE_DIR/$SDLC_TASK_ID/suppression-allowlist.md"
    [[ -f "$ALLOWLIST_FILE" ]] || ALLOWLIST_FILE=""
  else
    # Infer: exactly one active task directory with an allowlist
    CANDIDATES=$(find "$ACTIVE_DIR" -name "suppression-allowlist.md" -type f 2>/dev/null || true)
    CANDIDATE_COUNT=$(echo "$CANDIDATES" | grep -c . 2>/dev/null || echo 0)
    if [[ "$CANDIDATE_COUNT" -eq 1 ]]; then
      ALLOWLIST_FILE="$CANDIDATES"
    fi
    # 0 or 2+ candidates: skip allowlist (conservative — blocks bare suppressions)
  fi
fi

ERRORS=""

while IFS= read -r line; do
  # Extract line number and content
  LINE_NUM=$(echo "$line" | cut -d: -f1)
  LINE_CONTENT=$(echo "$line" | cut -d: -f2-)

  # Skip eslint-enable lines
  if echo "$LINE_CONTENT" | grep -q "eslint-enable"; then
    continue
  fi

  # Check for structured justification: must have -- separator with substantive text
  # Valid: // eslint-disable-next-line no-foo -- reason text here; tracked in DEBT-001
  # Valid: // eslint-disable-next-line no-foo -- reason text here; expires 2026-06-01
  # Invalid: // eslint-disable-next-line no-foo
  # Invalid: // eslint-disable-next-line no-foo -- ok
  # Invalid: // eslint-disable-next-line no-foo -- needed

  if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,};\s*(tracked in |expires )"; then
    # Score 2-3: Has structured format with tracking/expiry
    continue
  fi

  if echo "$LINE_CONTENT" | grep -qE "eslint-disable.*--\s*.{10,}"; then
    # Score 1: Has -- separator and reason but missing tracking/expiry
    # Weak but not bare — allow (Scout census will flag)
    continue
  fi

  # This is a bare suppression (score 0). Check allowlist.
  if [[ -n "$ALLOWLIST_FILE" ]] && [[ -f "$ALLOWLIST_FILE" ]]; then
    # Compute fingerprint: sha256(file_path + normalized_disable_text + context)
    NORMALIZED=$(echo "$LINE_CONTENT" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

    # Get surrounding 3 lines for context hash
    CONTEXT_START=$((LINE_NUM > 1 ? LINE_NUM - 1 : 1))
    CONTEXT_END=$((LINE_NUM + 1))
    CONTEXT_LINES=$(echo "$CONTENT" | sed -n "${CONTEXT_START},${CONTEXT_END}p" 2>/dev/null || true)
    CONTEXT_HASH=$(echo "$CONTEXT_LINES" | shasum -a 256 | cut -d' ' -f1)

    FINGERPRINT=$(echo "${FILE_PATH}${NORMALIZED}${CONTEXT_HASH}" | shasum -a 256 | cut -d' ' -f1)

    if grep -q "$FINGERPRINT" "$ALLOWLIST_FILE" 2>/dev/null; then
      # Pre-existing bare suppression — allowlisted
      continue
    fi
  fi

  # Bare suppression not in allowlist — BLOCK
  ERRORS="${ERRORS}Line ${LINE_NUM}: Bare eslint-disable without justification. Required format:\n"
  ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; tracked in <DEBT-ID>\n"
  ERRORS="${ERRORS}  // eslint-disable-next-line <rule> -- <reason (10+ chars)>; expires <YYYY-MM-DD>\n\n"

done <<< "$DISABLE_LINES"

if [[ -n "$ERRORS" ]]; then
  echo "HOOK_ERROR: eslint-disable justification required" >&2
  echo -e "$ERRORS" >&2
  exit 2
fi

exit 0
```

- [ ] **Step 2: Make it executable**

Run:

```bash
chmod +x hooks/scripts/check-eslint-disable-justification.sh
```

- [ ] **Step 3: Add to hooks.json**

In `hooks/hooks.json`, in the `PostToolUse` array's `Write|Edit` matcher hooks list (after the ast-checks.sh entry at line 58), add:

```json
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-eslint-disable-justification.sh\"",
            "timeout": 10
          }
```

- [ ] **Step 4: Verify hooks.json is valid JSON**

Run:

```bash
cat hooks/hooks.json | jq . > /dev/null && echo "Valid JSON"
```

Expected: `Valid JSON`

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/check-eslint-disable-justification.sh hooks/hooks.json
git commit -m "feat: add eslint-disable justification hook — blocks bare suppressions

Structured format required: -- <reason>; tracked in <ID> or expires <date>.
Whole-file scanning with fingerprint-based allowlist for pre-existing suppressions.
BLOCKING (exit 2) for score-0 bare disables not in allowlist.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Add Hook Test Fixtures and Tests

**Files:**
- Create: `hooks/tests/fixtures/justification-bare-suppression.json`
- Create: `hooks/tests/fixtures/justification-structured-valid.json`
- Create: `hooks/tests/fixtures/justification-weak-reason.json`
- Create: `hooks/tests/fixtures/justification-non-source-file.json`
- Create: `hooks/tests/fixtures/justification-edit-bare-no-allowlist.json`
- Create: `hooks/tests/fixtures/justification-allowlisted-bare.json`
- Modify: `hooks/tests/test-hooks.sh`

- [ ] **Step 1: Create bare suppression fixture (should BLOCK)**

Create `hooks/tests/fixtures/justification-bare-suppression.json`:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/test-project/lib/utils/example.ts",
    "content": "import { something } from './other';\n\n// eslint-disable-next-line no-raw-soft-delete\nconst result = db.query('SELECT * FROM users WHERE deleted_at IS NULL');\n\nexport { result };\n"
  }
}
```

- [ ] **Step 2: Create structured valid fixture (should PASS)**

Create `hooks/tests/fixtures/justification-structured-valid.json`:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/test-project/lib/utils/example.ts",
    "content": "import { something } from './other';\n\n// eslint-disable-next-line no-raw-soft-delete -- legacy migration pending for soft-delete canonical; tracked in DEBT-001\nconst result = db.query('SELECT * FROM users WHERE deleted_at IS NULL');\n\nexport { result };\n"
  }
}
```

- [ ] **Step 3: Create weak reason fixture (should PASS — score 1, not blocked)**

Create `hooks/tests/fixtures/justification-weak-reason.json`:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/test-project/lib/utils/example.ts",
    "content": "import { something } from './other';\n\n// eslint-disable-next-line no-raw-soft-delete -- legacy soft-delete pattern in migration path\nconst result = db.query('SELECT * FROM users WHERE deleted_at IS NULL');\n\nexport { result };\n"
  }
}
```

- [ ] **Step 4: Create non-source file fixture (should SKIP)**

Create `hooks/tests/fixtures/justification-non-source-file.json`:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/test-project/docs/README.md",
    "content": "# README\n\nThis file mentions eslint-disable but is not a source file.\n"
  }
}
```

- [ ] **Step 5: Create Edit-tier fixture with bare suppression and no allowlist (should BLOCK)**

Create `hooks/tests/fixtures/justification-edit-bare-no-allowlist.json`:

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/tmp/test-project/lib/storage/access-requests.ts",
    "old_string": "const old = true;",
    "new_string": "// eslint-disable-next-line no-raw-soft-delete\nconst old = true;"
  }
}
```

Note: The Edit tool payload lacks `content`, so the hook falls back to reading the file from disk (via `read_tool_content`). For this test, the file at `/tmp/test-project/lib/storage/access-requests.ts` must exist with the eslint-disable line. Create it before running tests:

```bash
mkdir -p /tmp/test-project/lib/storage
echo '// eslint-disable-next-line no-raw-soft-delete
const old = true;' > /tmp/test-project/lib/storage/access-requests.ts
```

- [ ] **Step 6: Create allowlisted bare suppression fixture (should PASS)**

Create `hooks/tests/fixtures/justification-allowlisted-bare.json`:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/tmp/test-project/lib/utils/example.ts",
    "content": "import { something } from './other';\n\n// eslint-disable-next-line no-raw-soft-delete\nconst result = db.query('SELECT * FROM users WHERE deleted_at IS NULL');\n\nexport { result };\n"
  }
}
```

Note: This fixture tests the same bare suppression as step 1, but with an allowlist present. The test runner must set up a matching allowlist file before running this test. See step 8 for the test setup.

- [ ] **Step 7: Add test section to test-hooks.sh**

In `hooks/tests/test-hooks.sh`, before the final summary output section (the `echo ""` / `echo "=== Results ==="` block at the end of the file), add:

```bash

echo ""
echo "=== eslint-disable Justification Tests ==="

# Setup: create test source file for Edit-tier test
mkdir -p /tmp/test-project/lib/storage
echo '// eslint-disable-next-line no-raw-soft-delete
const old = true;' > /tmp/test-project/lib/storage/access-requests.ts

run_test "BLOCK: bare eslint-disable (no justification)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-bare-suppression.json" 2

run_test "valid: structured justification with tracking ID" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-structured-valid.json" 0

run_test "valid: weak justification (score 1, not blocked)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-weak-reason.json" 0

run_test "valid: non-source file (skip)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-non-source-file.json" 0

run_test "BLOCK: Edit-tier bare suppression (no allowlist)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-edit-bare-no-allowlist.json" 2

# Setup: create allowlist with matching fingerprint for the bare suppression fixture
# The fingerprint is sha256(file_path + normalized_disable + context_hash)
ALLOWLIST_DIR="/tmp/test-project/docs/sdlc/active/test-task"
mkdir -p "$ALLOWLIST_DIR"
# Compute the fingerprint matching justification-allowlisted-bare.json
BARE_LINE="// eslint-disable-next-line no-raw-soft-delete"
CONTEXT="import { something } from './other';\n\n// eslint-disable-next-line no-raw-soft-delete\nconst result = db.query('SELECT * FROM users WHERE deleted_at IS NULL');"
CONTEXT_HASH=$(printf '%s' "$CONTEXT" | shasum -a 256 | cut -d' ' -f1)
FINGERPRINT=$(printf '%s' "/tmp/test-project/lib/utils/example.ts${BARE_LINE}${CONTEXT_HASH}" | shasum -a 256 | cut -d' ' -f1)
echo "- fingerprint: $FINGERPRINT | file: /tmp/test-project/lib/utils/example.ts | rule: no-raw-soft-delete" > "$ALLOWLIST_DIR/suppression-allowlist.md"
export SDLC_TASK_ID="test-task"

run_test "valid: allowlisted bare suppression (fingerprint match)" \
  "$HOOKS_DIR/check-eslint-disable-justification.sh" \
  "$FIXTURES_DIR/justification-allowlisted-bare.json" 0

# Cleanup
unset SDLC_TASK_ID
rm -rf /tmp/test-project
```

- [ ] **Step 6: Run the test suite**

Run:

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All justification tests PASS. Existing tests should remain unchanged.

- [ ] **Step 7: Commit**

```bash
git add hooks/tests/fixtures/justification-bare-suppression.json \
        hooks/tests/fixtures/justification-structured-valid.json \
        hooks/tests/fixtures/justification-weak-reason.json \
        hooks/tests/fixtures/justification-non-source-file.json \
        hooks/tests/fixtures/justification-edit-bare-no-allowlist.json \
        hooks/tests/fixtures/justification-allowlisted-bare.json \
        hooks/tests/test-hooks.sh
git commit -m "test: add eslint-disable justification hook fixtures and test cases

6 fixtures covering all enforcement tiers: bare suppression (BLOCK),
structured valid (PASS), weak reason (PASS, score 1), non-source file (SKIP),
Edit-tier bare without allowlist (BLOCK), allowlisted bare with fingerprint
match (PASS). Integrated into existing test suite.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Enrich drift-detector with MIGRATION_PLAN_MISSING

**Files:**
- Modify: `agents/drift-detector.md`

- [ ] **Step 1: Add MIGRATION_PLAN_MISSING to the detection catalog**

In `agents/drift-detector.md`, after the `### Import Graph Health` section (after line 51), add:

```markdown

### Migration Plan Missing

When a runner creates a new export in a canonical path (prefixes defined in `references/canonical-registry.md` under `canonical_path_prefixes`), a companion bead with `intent: migration` must exist in the manifest.

- **Detection method:**
  1. Source changed files from **git diff** (worktree diff or `git diff --name-only` against the bead's base commit ref provided in your context). This is the deterministic source — NOT the runner's prose output. Cross-check against the runner's `## Changed Files` section if present.
  2. For each changed file in a canonical path prefix: run LSP `workspaceSymbol` or AST export analysis to identify new exports (exports not present in the base commit).
  3. Compare new exports against `canonical_path_prefixes` from `references/canonical-registry.md`.
  4. Check the current bead manifest (provided in your context) for any bead with `intent: migration` targeting this canonical.

- **Signal:** `MIGRATION_PLAN_MISSING`
- **Severity:** BLOCKING — bead cannot advance past `submitted`
- **Role by profile:**
  - BUILD/INVESTIGATE (Phase 3 runs): safety net
  - REPAIR (Phase 3 skipped): primary and only guard
  - Clear beads (Architect bypassed): primary and only guard
```

- [ ] **Step 2: Add context requirements**

In the `## Multi-Layer Detection Process` section (around line 64), after step 7 (CLASSIFY), add:

```markdown

### Context Requirements

Your dispatch prompt must include:
- Runner's changed files (from runner output)
- **Bead base commit ref** — the commit SHA before the runner started, for `git diff --name-only <base>..HEAD` to deterministically identify new files/exports
- **Current bead manifest** — list of all beads with their Type, Intent, and Scope fields, so you can check for `intent: migration` companions
- Convention Map (existing)
- Fitness function catalog (existing)
- Canonical registry `canonical_path_prefixes` section from `references/canonical-registry.md`
```

- [ ] **Step 3: Add MIGRATION_PLAN_MISSING to the severity classification**

In the `## Severity Classification` section, add to BLOCKING:

```markdown
- **BLOCKING**: ... MIGRATION_PLAN_MISSING (new export in canonical path without migration companion).
```

- [ ] **Step 4: Commit**

```bash
git add agents/drift-detector.md
git commit -m "feat: add MIGRATION_PLAN_MISSING check to drift-detector

Detects new exports in canonical paths without intent:migration companion
beads. Uses git diff as deterministic source. Requires bead base commit ref
and manifest in dispatch context. BLOCKING severity.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Update sonnet-implementer Output Format

**Files:**
- Modify: `agents/sonnet-implementer.md`

- [ ] **Step 1: Add normalized Changed Files section to output format**

In `agents/sonnet-implementer.md`, in the `## Required Output Format` section (line 29-58), after the `## Status` line (line 54), add:

```markdown

## Changed Files
- `exact/path/to/file1.ts`
- `exact/path/to/file2.ts`
- `exact/path/to/test.ts`
```

This is a machine-readable list of file paths, one per line, for deterministic L1 consumption by drift-detector. It serves as a cross-check against git diff (which is the primary source).

- [ ] **Step 2: Commit**

```bash
git add agents/sonnet-implementer.md
git commit -m "feat: add normalized Changed Files section to implementer output

Machine-readable file path list for deterministic L1 consumption by
drift-detector. Cross-check for git diff (primary source).

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Update sdlc-orchestrate with Migration Gate and Debt Import

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

- [ ] **Step 1: Add canonical-creation check to Phase 3 (Architect)**

In `skills/sdlc-orchestrate/SKILL.md`, in the `### Phase 3: Architect` section, after the existing content about STPA skip rule and output (around line 183), before `**Output:**`, add:

```markdown

**Canonical-creation check:** After the primary bead manifest is built, check each bead's scope against `canonical_path_prefixes` from `references/canonical-registry.md`. If any bead creates a new export in a canonical path:
1. Require a companion bead with `intent: migration` — must include migration_target, callers_to_migrate (from Scout/reuse-scout), migration_strategy (INLINE if <10 callers, STAGED, or DEFERRED with substantive justification), and estimated_scope
2. Require a companion bead with `intent: registry` — adds the new canonical to `references/canonical-registry.md`
3. Manifest order: Primary beads -> Migration bead(s) -> Registry bead -> Debt-companion beads

**Debt-backlog import:** After migration check, read `docs/sdlc/debt-backlog.md` for PROMOTE items. Import rules:
1. Relevance gate: only items whose `include_paths` overlap with any primary bead's `Scope` field
2. Debt budget: max 1-2 `intent: debt_companion` beads per task
3. Items in untouched modules wait for a future task
```

- [ ] **Step 2: Add drift-detector manifest context to Phase 4 L1**

In the Phase 4 Execute section, in the sentinel loop description (around line 196), after the line about `safety-constraints-guardian`, add:

```markdown
   - `drift-detector` receives additional context: bead base commit ref (the commit SHA before the runner started) + current bead manifest (all beads with Type, Intent, Scope) + `canonical_path_prefixes` from `references/canonical-registry.md`. This enables the `MIGRATION_PLAN_MISSING` check — new exports in canonical paths without `intent: migration` companions are BLOCKING.
```

- [ ] **Step 3: Enrich existing Scout step 6 standards-curator dispatch**

In the Phase 2 Scout section, step 6 (around line 162) currently reads:

```markdown
6. Dispatch `standards-curator` in Scout mode — analyzes the target project to determine which standards from `/Users/q/LAB/Research/Standards/` apply. Produces a project-specific standards profile at `docs/sdlc/active/{task-id}/standards-profile.md` listing applicable checks from `references/standards-checklist.md`. The profile is referenced in runner context packets during Execute phase (by path, not inlined).
```

Replace with (same step 6, expanded — NOT a new step 7):

```markdown
6. Dispatch `standards-curator` in Scout mode — performs two parallel audits:
   - **Standards Profile:** Analyzes the target project to determine which standards from `/Users/q/LAB/Research/Standards/` apply. Produces `docs/sdlc/active/{task-id}/standards-profile.md` listing applicable checks from `references/standards-checklist.md`.
   - **Rule Governance Audit:** Audits the project's lint rule health, suppression ratios, and justification quality. Produces `docs/sdlc/active/{task-id}/rule-governance-profile.md` and `docs/sdlc/active/{task-id}/suppression-allowlist.md`. The allowlist is consumed by the `check-eslint-disable-justification.sh` hook during Execute. The profile is referenced by path in runner context packets.
```

This enriches the existing single dispatch rather than adding a duplicate. The **Parallelize** note does not need updating — standards-curator already runs in parallel with other Scout agents.

- [ ] **Step 4: Add migration completion check to Phase 5 (Synthesize)**

In the Phase 5 Synthesize section, after step 3.375 (feature-finisher), add:

```markdown
3.4. **Migration completion check:** gap-analyst Finisher reports remaining unmigrated callers from STAGED/DEFERRED migration beads (beads with `intent: migration`). Finisher reports counts; it does NOT auto-create anything. The Conductor reads the report and writes entries to `docs/sdlc/debt-backlog.md` with status PROMOTE for remaining callers.
```

- [ ] **Step 5: Commit**

```bash
git add skills/sdlc-orchestrate/SKILL.md
git commit -m "feat: add migration gate, debt import, and governance audit to orchestration

Phase 2: standards-curator Rule Governance Audit + suppression allowlist.
Phase 3: canonical-creation check requiring intent:migration + intent:registry
companions; debt-backlog import with relevance/budget gates.
Phase 4: drift-detector gets manifest + base commit for MIGRATION_PLAN_MISSING.
Phase 5: migration completion check via gap-analyst Finisher.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Update sdlc-normalize Resume Path

**Files:**
- Modify: `skills/sdlc-normalize/SKILL.md:64`

- [ ] **Step 1: Add new artifacts to resume path**

In `skills/sdlc-normalize/SKILL.md`, in `Path B — Resume` (around line 64), the current line reads:

```markdown
3. On approval, load the task state from the referenced `state.md` file, bead files, and any persisted Scout artifacts (`standards-profile.md`, `quality-budget.md`, `observability-profile.md`). Continue from the recommended bead or phase.
```

Change to:

```markdown
3. On approval, load the task state from the referenced `state.md` file, bead files, and any persisted Scout artifacts (`standards-profile.md`, `quality-budget.md`, `observability-profile.md`, `rule-governance-profile.md`, `suppression-allowlist.md`). Continue from the recommended bead or phase.
```

- [ ] **Step 2: Commit**

```bash
git add skills/sdlc-normalize/SKILL.md
git commit -m "feat: add rule-governance-profile and suppression-allowlist to resume path

Ensures mid-Execute task resume reloads the governance artifacts needed
by the justification hook and runner context packets.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Add Fitness Function Rules

**Files:**
- Modify: `references/fitness-functions.md`

- [ ] **Step 1: Add duplicate ratchet rule**

At the end of `references/fitness-functions.md`, add:

```markdown

### Check: Duplicate function count ratchet
**Type:** structural
**What:** PROMOTE-classified duplicate count must not exceed prior Evolve scan baseline
**How:** debt-crawler evaluates during Evolve bead #19; compares current PROMOTE count against previous in `docs/sdlc/debt-scan-report.md`
**Pass:** PROMOTE count <= previous scan count
**Fail action:** BLOCKING within Evolve — debt-crawler writes FAIL to system health report; Conductor must acknowledge and either fix or document justification before Evolve cycle completes
**Scope:** Evaluated by debt-crawler during Evolve bead #19 only. Does NOT run in per-bead sdlc-fitness checks.
**Note:** WATCH count is tracked and trended but advisory only

### Check: Bare suppression ratchet
**Type:** governance
**What:** Bare eslint-disable count (score 0) must not increase between Evolve scans
**How:** standards-curator compares current bare count from `docs/sdlc/active/{task-id}/rule-governance-profile.md` against the most recent prior profile found via the Evolve lookback contract (`active/*/rule-governance-profile.md` + `completed/*/rule-governance-profile.md`, last 10 tasks or 30 days)
**Pass:** Bare count <= previous
**Fail action:** WARNING — flag in system health report for Conductor review
**Scope:** Evaluated by standards-curator during Evolve step #15 only
```

- [ ] **Step 2: Commit**

```bash
git add references/fitness-functions.md
git commit -m "feat: add duplicate ratchet and bare suppression ratchet fitness rules

Duplicate ratchet: BLOCKING within Evolve if PROMOTE count increases.
Bare suppression ratchet: WARNING if bare eslint-disable count increases.
Both evaluated during Evolve only, not per-bead fitness checks.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 15: Create extract-functions.sh Script

**Files:**
- Create: `scripts/extract-functions.sh`

- [ ] **Step 1: Create the extraction script**

Create two files: a bash wrapper and a node AST extraction module.

Create `scripts/extract-functions.sh`:

```bash
#!/bin/bash
# extract-functions.sh — AST-based function extraction for JS/TS
# Uses the TypeScript compiler API for real AST parsing — not regex.
# Exports: function name, parameter signature, body hash, line count, branch count, nesting depth
# Output: JSON array of function descriptors
# Usage: bash scripts/extract-functions.sh [paths...]
# Example: bash scripts/extract-functions.sh lib/utils/ lib/storage/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve target paths
TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "Usage: bash scripts/extract-functions.sh <path1> [path2] ..." >&2
  exit 1
fi

# Require node — no regex fallback. AST accuracy is the contract.
if ! command -v node &> /dev/null; then
  echo '{"error": "node not found — AST extraction requires Node.js", "functions": []}' >&2
  exit 1
fi

# Build file list — JS/TS only, exclude tests/vendor/generated
FILE_LIST=$(find "${TARGETS[@]}" \
  -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  ! -path "*/__tests__/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/*.test.*" \
  ! -path "*/*.spec.*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  2>/dev/null || true)

if [[ -z "$FILE_LIST" ]]; then
  echo '{"functions": [], "file_count": 0}'
  exit 0
fi

# Pass file list to the AST extraction module
echo "$FILE_LIST" | node "$SCRIPT_DIR/lib/ast-extract-functions.js"
```

Create `scripts/lib/ast-extract-functions.js`:

```javascript
/**
 * AST-based function extraction using the TypeScript compiler API.
 * Reads file paths from stdin (one per line), outputs JSON to stdout.
 *
 * For each function/arrow/method, emits:
 *   name, file, line, params, body_hash, line_count, branch_count, nesting_depth, exported
 *
 * Requires: typescript (resolved from project node_modules or globally)
 */

const fs = require('fs');
const crypto = require('crypto');
const readline = require('readline');
const path = require('path');

// Resolve TypeScript compiler — try project-local first, then global
let ts;
try {
  const projectRoot = process.cwd();
  const localTs = path.join(projectRoot, 'node_modules', 'typescript');
  ts = require(localTs);
} catch {
  try {
    ts = require('typescript');
  } catch {
    console.error('{"error": "typescript not found — install typescript in project or globally", "functions": []}');
    process.exit(1);
  }
}

const rl = readline.createInterface({ input: process.stdin });
const filePaths = [];

rl.on('line', (line) => {
  const trimmed = line.trim();
  if (trimmed) filePaths.push(trimmed);
});

rl.on('close', () => {
  const functions = [];

  for (const filePath of filePaths) {
    try {
      const sourceText = fs.readFileSync(filePath, 'utf8');
      const sourceFile = ts.createSourceFile(
        filePath,
        sourceText,
        ts.ScriptTarget.Latest,
        true, // setParentNodes
        filePath.endsWith('.tsx') || filePath.endsWith('.jsx')
          ? ts.ScriptKind.TSX
          : ts.ScriptKind.TS
      );

      visitNode(sourceFile, sourceFile, filePath, functions, sourceText);
    } catch {
      // Skip files that fail to parse
    }
  }

  console.log(JSON.stringify({ functions, file_count: filePaths.length }, null, 2));
});

function visitNode(node, sourceFile, filePath, functions, sourceText) {
  const info = extractFunctionInfo(node, sourceFile, filePath, sourceText);
  if (info) {
    functions.push(info);
  }

  ts.forEachChild(node, (child) => {
    visitNode(child, sourceFile, filePath, functions, sourceText);
  });
}

function extractFunctionInfo(node, sourceFile, filePath, sourceText) {
  let name = null;
  let bodyNode = null;
  let paramsNode = null;
  let isExported = false;

  // Function declarations: function foo() {}
  if (ts.isFunctionDeclaration(node) && node.name && node.body) {
    name = node.name.text;
    bodyNode = node.body;
    paramsNode = node.parameters;
    isExported = hasExportModifier(node);
  }
  // Variable declarations with arrow/function expressions: const foo = () => {}
  else if (
    ts.isVariableStatement(node) &&
    node.declarationList.declarations.length === 1
  ) {
    const decl = node.declarationList.declarations[0];
    if (
      ts.isIdentifier(decl.name) &&
      decl.initializer &&
      (ts.isArrowFunction(decl.initializer) || ts.isFunctionExpression(decl.initializer)) &&
      decl.initializer.body
    ) {
      name = decl.name.text;
      bodyNode = decl.initializer.body;
      paramsNode = decl.initializer.parameters;
      isExported = hasExportModifier(node);
    }
  }
  // Method declarations in classes/objects
  else if (ts.isMethodDeclaration(node) && node.name && node.body) {
    name = ts.isIdentifier(node.name) ? node.name.text : node.name.getText(sourceFile);
    bodyNode = node.body;
    paramsNode = node.parameters;
    isExported = false; // methods are accessed via their class
  }

  if (!name || !bodyNode) return null;

  // Extract body text and compute metrics
  const bodyStart = bodyNode.getStart(sourceFile);
  const bodyEnd = bodyNode.getEnd();
  const bodyText = sourceText.slice(bodyStart, bodyEnd);

  const startLine = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
  const lineCount = bodyText.split('\n').length;

  // Normalize body for hash: collapse whitespace, remove string literals
  const normalized = bodyText
    .replace(/\/\/.*$/gm, '')       // strip line comments
    .replace(/\/\*[\s\S]*?\*\//g, '') // strip block comments
    .replace(/'[^']*'|"[^"]*"|`[^`]*`/g, '""') // normalize strings
    .replace(/\s+/g, ' ')
    .trim();
  const bodyHash = crypto.createHash('sha256').update(normalized).digest('hex').slice(0, 16);

  // Count branches via AST node kinds
  let branchCount = 0;
  let maxNesting = 0;
  countComplexity(bodyNode, 0);

  function countComplexity(n, depth) {
    if (
      ts.isIfStatement(n) ||
      ts.isSwitchStatement(n) ||
      ts.isConditionalExpression(n) ||
      ts.isCaseClause(n) ||
      (ts.isBinaryExpression(n) && (n.operatorToken.kind === ts.SyntaxKind.QuestionQuestionToken || n.operatorToken.kind === ts.SyntaxKind.BarBarToken || n.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken))
    ) {
      branchCount++;
    }
    const newDepth = ts.isBlock(n) ? depth + 1 : depth;
    if (newDepth > maxNesting) maxNesting = newDepth;
    ts.forEachChild(n, (child) => countComplexity(child, newDepth));
  }

  // Extract parameter signature
  const params = paramsNode
    ? paramsNode.map(p => p.getText(sourceFile)).join(', ')
    : '';

  return {
    name,
    file: filePath,
    line: startLine,
    params,
    body_hash: bodyHash,
    line_count: lineCount,
    branch_count: branchCount,
    nesting_depth: maxNesting,
    exported: isExported
  };
}

function hasExportModifier(node) {
  if (!node.modifiers) return false;
  return node.modifiers.some(m => m.kind === ts.SyntaxKind.ExportKeyword);
}
```
```

- [ ] **Step 2: Create the lib directory and make scripts executable**

Run:

```bash
mkdir -p scripts/lib
chmod +x scripts/extract-functions.sh
```

- [ ] **Step 3: Verify it runs against a project with TypeScript**

Run from a project directory that has `node_modules/typescript`:

```bash
cd /Users/q/LAB/OnePlatform && bash /Users/q/.claude/plugins/sdlc-os/scripts/extract-functions.sh lib/utils/ 2>/dev/null | jq '.functions | length'
```

Expected: A number > 0 (function count from lib/utils/). If typescript is not found, the script exits with an error — no regex fallback. AST accuracy is the contract.

- [ ] **Step 4: Commit**

```bash
git add scripts/extract-functions.sh scripts/lib/ast-extract-functions.js
git commit -m "feat: add extract-functions.sh — TypeScript compiler API AST extraction

Uses ts.createSourceFile for real AST parsing. No regex fallback —
AST accuracy is the contract. Extracts: name, file, line, params,
body_hash (SHA-256 of normalized body), line_count, branch_count,
nesting_depth, exported. JS/TS only. Used by debt-crawler Mode 2.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 16: Update HANDOFF.md

**Files:**
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Update version and counts**

In `docs/HANDOFF.md`, update the header:

```markdown
**Date:** 2026-03-29
**Plugin version:** 10.0.0
```

Update the component counts table:

```markdown
| Component | Count |
|-----------|-------|
| Agents | 46 |
| Skills | 15 |
| Hook scripts | 10 |
| Reference docs | 22 |
| Cross-model scripts | 6 |
| Commands | 11 |
| Research docs | 10 (4,898 lines) |
| Design specs | 10 |
| Implementation plans | 6 |
```

- [ ] **Step 2: Add Layer 10 to architecture stack**

In the architecture layers diagram, add at the top:

```markdown
Layer 10: Debt Combat System (v10.0.0)
  debt-crawler (adoption + duplicate scan), migration plan gate, rule governance audit
  eslint-disable justification enforcement, canonical registry, debt backlog/ratchet
```

- [ ] **Step 3: Add Phase D to roadmap**

After `### Phase C: Reliability Telemetry — DONE (v8.0.0)`, add:

```markdown

### Phase D: Debt Combat System — DONE (v10.0.0)

Five capabilities closing gaps A-E from consolidation root cause analysis:
- **A: Adoption tracking** — debt-crawler Mode 1, canonical-registry.md
- **B: Rule graduation** — standards-curator Rule Governance Audit in Scout + Evolve
- **C: Suppression enforcement** — check-eslint-disable-justification.sh hook
- **D: Duplicate scan** — debt-crawler Mode 2, extract-functions.sh, ratchet
- **E: Migration plan gate** — Architect Phase 3 check + drift-detector MIGRATION_PLAN_MISSING

**Spec:** `docs/specs/2026-03-29-debt-combat-system-design.md`
**Plan:** `docs/superpowers/plans/2026-03-29-debt-combat-system.md`
```

- [ ] **Step 4: Commit**

```bash
git add docs/HANDOFF.md
git commit -m "docs: update HANDOFF.md for v10.0.0 — debt combat system

Layer 10 added. Phase D documented. Agent count 46, hook count 10,
reference count 22. Intent field noted in bead schema.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 17: Update plugin.json Version

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Bump version to 10.0.0**

In `.claude-plugin/plugin.json`, change:

```json
"version": "9.0.0"
```

to:

```json
"version": "10.0.0"
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump plugin version to 10.0.0

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 18: Run Full Hook Test Suite

**Files:** (no changes — verification only)

- [ ] **Step 1: Run the complete test suite**

Run:

```bash
cd /Users/q/.claude/plugins/sdlc-os && bash hooks/tests/test-hooks.sh
```

Expected: All tests PASS, including the 4 new justification tests from Task 9.

- [ ] **Step 2: If any tests fail, diagnose and fix**

Read the test output carefully. Common issues:
- Hook script path wrong in test: verify `$HOOKS_DIR/check-eslint-disable-justification.sh` resolves correctly
- Fixture JSON malformed: validate with `jq . < fixtures/justification-bare-suppression.json`
- Exit code mismatch: check the hook script's logic paths

- [ ] **Step 3: Commit any fixes**

If fixes were needed:

```bash
git add -A
git commit -m "fix: resolve hook test failures from debt combat integration

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```
