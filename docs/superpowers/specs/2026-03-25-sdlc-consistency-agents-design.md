# SDLC-OS Consistency Agents — Design Spec

**Date:** 2026-03-25
**Status:** Approved (pending implementation)
**Plugin:** sdlc-os v3+
**Scope:** 4 new agents, 2 new skills, 1 new reference file, 1 new per-project artifact, 4 file updates, 2 new commands

---

## Problem Statement

The SDLC-OS plugin is strong on correctness verification (Oracle, AQS) and DRY detection (reuse-scout, drift-detector), but has gaps in:

1. **Convention enforcement** — No agent dynamically discovers and enforces naming conventions, styling patterns, import patterns, or structural conventions
2. **Codebase reality grounding** — Early phases (Frame, Scout) don't systematically extract the project's actual patterns, so plans float above codebase reality
3. **Mid-stream pickup** — No mechanism for entering work already in progress or recovering from interrupted SDLC sessions
4. **Gap analysis** — No systematic "what's missing?" sweep before or after implementation

These gaps mean that even when code is functionally correct and DRY-compliant, it can still drift from project conventions, reinvent components that exist under different names, or deliver incomplete features.

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Convention discovery model | **Hybrid** — dynamic scan produces map, Conductor validates, then persisted as authority | Adaptive across projects without manual setup; authoritative once validated |
| Mid-stream pickup trigger | **Mandatory + smart depth** — always fires on SDLC entry, depth controlled by state detection | Prevents silent convention drift on every entry; no-ops in <5s when clean |
| Gap analysis truth source | **Any available** — mission brief, external spec, codebase inference, or combination | Projects vary; the analyst must work with whatever truth exists |
| Convention map persistence | **Per-project, committed** — lives in repo at `docs/sdlc/convention-map.md` | Accumulates over time; shared across sessions and team members |
| Enforcement mode | **Blocking** — BLOCKING/WARNING/NOTE severity that can halt bead advancement | Conventions are not advisory; structural violations break findability and consistency |
| Architecture | **Dedicated agents + shared reference** — 4 single-purpose agents sharing `convention-dimensions.md` | Follows existing plugin pattern (drift-detector + reuse-scout + shared references); focused prompts do one thing well |

---

## New Components

### Agent 1: `convention-scanner` (model: sonnet)

**Purpose:** Dynamically scan a project's codebase to produce a Convention Map — a structured catalog of how this project does things.

**When dispatched:**
- Scout phase (mandatory, before any design or implementation)
- Normalizer entry point (when Convention Map is missing)
- On-demand when Convention Map is stale (>30 days) or Conductor detects drift

**What it produces:**
A `docs/sdlc/convention-map.md` file committed to the repo, covering every dimension defined in `convention-dimensions.md`:
- File naming patterns (per directory)
- Function/variable naming patterns (per layer)
- Component structure patterns (state, props, hooks)
- Styling approach (CSS modules, Tailwind, inline — which is canonical)
- Import patterns (ordering, aliases, barrel exports)
- Test patterns (placement, naming, framework, assertion style)
- Error handling patterns (per layer)
- Directory structure conventions (where each file type lives)

**Detection method:** For each dimension, the scanner reads a sample of existing files (3-5 per directory/layer), extracts the dominant pattern, and records it with a confidence label and evidence (file:line examples). Inconsistent patterns (e.g., 50/50 split) are flagged for Conductor/user resolution.

**Output format:**
```markdown
## Convention Map: {project}
**Generated:** {timestamp}
**Scanner confidence:** {overall}

### File Naming
| Directory | Convention | Evidence | Confidence |
|-----------|-----------|----------|------------|
| lib/storage/ | kebab-case-storage.ts | payments-storage.ts, users-storage.ts | Verified (5/5 files) |
| components/ | PascalCase.tsx | UserProfile.tsx, PaymentForm.tsx | Verified (8/8 files) |

### Function Naming
[same table structure per layer]

### [each dimension from convention-dimensions.md]

### Inconsistencies Detected
- {dimension}: {description} — needs Conductor/user resolution
```

---

### Agent 2: `convention-enforcer` (model: sonnet)

**Purpose:** Audit runner output against the committed Convention Map. Runs in L1 sentinel loop alongside drift-detector.

**When dispatched:**
- Execute phase, L1 sentinel loop — after every runner submission
- Synthesize phase — final cross-bead convention check
- Normalizer flow — when assessing existing work

**What it checks:**
Every new or modified file/function/component against the Convention Map, dimension by dimension.

**Severity classification:**
- **BLOCKING:** Naming violations, wrong file location, wrong styling approach — structural conventions that affect findability and consistency
- **WARNING:** Import ordering, test placement, minor structural drift
- **NOTE:** Stylistic preferences the Convention Map recorded with low confidence

**Key difference from drift-detector:** Drift-detector catches DRY/SSOT/SoC/pattern-reuse violations (semantic duplication, boundary violations). Convention-enforcer catches naming/structure/style violations (surface-level consistency). They complement each other without overlap.

**Output format:**
```markdown
## Convention Enforcement Report: Bead {id}

### Violations Found
| # | Severity | Dimension | Location | Violation | Convention | Fix |
|---|----------|-----------|----------|-----------|------------|-----|
| 1 | BLOCKING | file-naming | lib/storage/userPayments.ts | camelCase | kebab-case-storage.ts | Rename to user-payments-storage.ts |
| 2 | WARNING | test-placement | __tests__/payments.test.ts | Separate directory | Colocated .test.ts | Move to lib/storage/payments-storage.test.ts |

### Convention Map Version
**Source:** docs/sdlc/convention-map.md
**Generated:** {timestamp}

### Verdict
[CLEAN | VIOLATIONS — {N} blocking, {M} warnings | CONVENTION_DRIFT — map may be stale]
```

**Loop integration:**
- BLOCKING violations → L1 correction, same as drift-detector
- `CONVENTION_DRIFT` signal → Conductor reviews Convention Map for staleness, may dispatch convention-scanner to refresh

---

### Agent 3: `normalizer` (model: sonnet)

**Purpose:** Two modes — mid-stream pickup of unstructured work, and final consistency pass before delivery. Mandatory entry point for every SDLC session.

**When dispatched:**
- Session entry (always) — Phase 0: Normalize
- Synthesize phase — Final Pass mode

**Mode 1: Pickup (session entry)**

Detection logic:

| Signal | Depth |
|--------|-------|
| Clean working tree, no SDLC artifacts | **No-op** — exit in <5 seconds |
| Existing SDLC artifacts with bead state | **Resume** — read state.md + beads, identify last completed phase, recover Cynefin assignments and quality budget, recommend re-entry point |
| Dirty git / branch changes without SDLC artifacts | **Full normalization** — assess all changes against Convention Map + code-constitution, produce normalization directives |

Full normalization output:
```markdown
## Normalization Report

### Existing Work Detected
- {N} files changed on branch {name} since divergence from {base}
- {N} commits without SDLC tracking

### Convention Map Status
- [EXISTS — loaded | MISSING — dispatching convention-scanner]

### Alignment Assessment
| # | File | Issues | Severity |
|---|------|--------|----------|
| 1 | lib/storage/newFile.ts | Wrong naming, missing soft-delete filter | BLOCKING, BLOCKING |
| 2 | components/Widget.tsx | Inline styles (project uses Tailwind) | BLOCKING |

### Normalization Directives
1. Rename lib/storage/newFile.ts → lib/storage/new-file-storage.ts
2. Convert inline styles in Widget.tsx to Tailwind classes

### Recommended SDLC Entry Point
- Phase: {Execute | Scout | Frame} — {rationale}

### SDLC State Recovery (if partial artifacts found)
- Last completed phase: {N}
- Bead states: {summary}
- Quality budget state: {healthy | warning | depleted}
- Recommended: Resume from Phase {N+1}
```

Normalization directives require user approval before execution.

**Mode 2: Final Pass (Synthesize)**

Cross-bead consistency sweep after all beads merged:
- Checks that all beads together form a consistent whole (no bead-to-bead naming drift)
- Checks for cross-bead violations that per-bead enforcement missed (e.g., two beads independently creating similar utilities with different names)
- Produces a final consistency score alongside the fitness report

Output:
```markdown
## Final Consistency Pass

### Cross-Bead Convention Check
| # | Severity | Beads | Issue | Fix |
|---|----------|-------|-------|-----|
| 1 | WARNING | B2 + B4 | Both created formatDate() variants | Consolidate to single utility |
| 2 | NOTE | B1 + B3 | Slightly different import ordering | Align to Convention Map pattern |

### Convention Adherence Score
| Dimension | Score | Issues |
|-----------|-------|--------|
| File Naming | 100/100 | — |
| Styling | 85/100 | 1 component uses inline style |

### Verdict
[CONSISTENT — no cross-bead drift | DRIFT — {N} cross-bead issues found | NEEDS_NORMALIZATION — significant inconsistency]
```

---

### Agent 4: `gap-analyst` (model: sonnet)

**Purpose:** Bidirectional gap analysis — Feature Finder before implementation, Feature Finisher after.

**When dispatched:**
- Scout phase (Finder mode) — after investigation, before design
- Synthesize phase (Finisher mode) — after all beads merged
- On-demand — user or Conductor triggers

**Mode 1: Feature Finder (pre-implementation)**

Accepts requirements from any available source:
1. SDLC mission brief (success criteria from mission brief)
2. External source (GitHub issue, design doc, user description)
3. Codebase inference (what's obviously incomplete)
4. Precedent system (prior arbiter verdicts informing completeness)

Output:
```markdown
## Feature Gap Analysis: {task}
**Mode:** Finder (pre-implementation)
**Truth source:** {mission brief / GitHub issue #N / codebase inference / combination}

### Completeness Map
| # | Requirement | Status | Evidence | Action |
|---|-------------|--------|----------|--------|
| 1 | CRUD for payments | PARTIAL | Create/Read exist, Update/Delete missing | Build Update + Delete |
| 2 | Input validation | MISSING | No Zod schemas in app/api/payments/ | Build from scratch |
| 3 | Error handling | EXISTS | StorageError used consistently | No action needed |

### Summary
- **EXISTS:** {N} requirements already satisfied
- **PARTIAL:** {N} requirements partially implemented
- **MISSING:** {N} requirements not started
- **Recommendation:** {N} beads estimated for remaining work

### Reuse Opportunities Found
- {Existing utility that covers part of a MISSING requirement}
```

Bead decomposition in Architect phase only creates beads for MISSING and PARTIAL items.

**Mode 2: Feature Finisher (post-implementation)**

Compares delivery against original requirements + success criteria + codebase inference:

```markdown
## Feature Gap Analysis: {task}
**Mode:** Finisher (post-implementation)
**Truth source:** {mission brief + bead outputs + codebase scan}

### Delivery Completeness
| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|----------|
| 1 | "Users can create payments" | DELIVERED | Bead B1, tests pass (Verified) |
| 2 | "Audit log for payment changes" | NOT_DELIVERED | Not in any bead output |

### Inferred Gaps (not in spec but obviously missing)
| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| 1 | No delete confirmation UI | LOW | Existing forms have it, new ones don't |

### Closing Checklist
- [ ] {Specific remaining item}

### Verdict
[COMPLETE | GAPS — {N} items remaining | INCOMPLETE — significant work outstanding]
```

If gaps found: minor gaps → Conductor creates follow-up beads; significant gaps → Conductor presents to user.

**Swarm integration:** For large features, gap-analyst dispatches guppy swarms — one per requirement checking "does this exist?" — then synthesizes into the completeness map.

---

## New Skills

### Skill: `sdlc-normalize`

**Trigger:** Fires automatically at SDLC session start (Phase 0). Also invocable via `/normalize` command.

**Flow:**
```
1. Normalizer agent fires (always)
   ├─ Clean state → no-op, proceed to Phase 1
   ├─ Partial SDLC artifacts → resume protocol
   │   ├─ Read state.md + bead files + quality-budget.md
   │   ├─ Recover Cynefin assignments
   │   ├─ Identify last completed phase
   │   └─ Recommend re-entry point to Conductor
   └─ Unstructured changes → full normalization
       ├─ Convention Map exists? → load it
       ├─ Convention Map missing? → dispatch convention-scanner
       ├─ Normalizer assesses changes against map + code-constitution
       ├─ Produces normalization directives
       ├─ Conductor presents directives to user for approval
       └─ SDLC enters at recommended phase

2. Gap-analyst fires in Finder mode (if full normalization)
   ├─ Assesses what existing work covers
   ├─ Identifies what's remaining
   └─ Feeds into Frame/Scout phase
```

### Skill: `sdlc-gap-analysis`

**Trigger:** Automatically during Scout (Finder) and Synthesize (Finisher). On-demand via `/gap-analysis` command.

**Finder wave flow:**
```
1. Collect truth sources (mission brief, external spec, codebase state)
2. Dispatch gap-analyst in Finder mode
3. For large scope: gap-analyst swarms guppies (one per requirement)
4. Synthesize completeness map
5. Feed into Architect phase — beads only for MISSING and PARTIAL items
```

**Finisher wave flow:**
```
1. Collect truth sources (mission brief, bead outputs, codebase state)
2. Dispatch gap-analyst in Finisher mode
3. Produce closing checklist
4. Minor gaps → follow-up beads | Significant gaps → user scoping decision
```

---

## New Reference File

### `references/convention-dimensions.md`

Shared vocabulary consumed by all four new agents. Defines WHAT to check, not specific answers.

**Dimensions:**

| Dimension | Scope | Scanner Method | Enforcer Severity |
|-----------|-------|---------------|-------------------|
| File Naming | All source files | Sample 3-5 files per directory | BLOCKING |
| Function/Variable Naming | Exported symbols | LSP documentSymbol per layer | BLOCKING (exported), WARNING (internal) |
| Component Structure | UI components | Read 3-5 representative components | WARNING |
| Styling Approach | Style definitions | Grep for style imports/patterns | BLOCKING |
| Import Patterns | All source files | Read import blocks from 5-10 files | NOTE (ordering), WARNING (barrel misuse) |
| Test Patterns | Test files | Glob for test files, categorize | WARNING (placement), NOTE (naming) |
| Error Handling | Per-layer | Cross-reference with reuse-patterns.md | BLOCKING (if canonical source exists) |
| Directory Structure | Project root | Map existing structure | BLOCKING |

Framework-agnostic by design. The scanner fills in project-specific answers.

---

## New Per-Project Artifact

### `docs/sdlc/convention-map.md`

Produced by `convention-scanner`, committed to the project repo.

**Lifecycle:**
- **Created:** First convention-scanner run during Scout phase
- **Validated:** Conductor presents to user for correction
- **Refreshed:** When >30 days old, when CONVENTION_DRIFT detected, when user runs `/normalize`
- **Overridden:** Code-constitution rules take precedence over convention map entries

**Relationship to existing references:**

| Reference | Axis | Consumed By |
|-----------|------|-------------|
| `reuse-patterns.md` | "Use THIS function for X" | reuse-scout, drift-detector |
| `fitness-functions.md` | "These patterns are violations" | drift-detector, guppy swarms |
| `convention-dimensions.md` | "These categories to check" | convention-scanner, convention-enforcer |
| `convention-map.md` | "This project does X this way" | convention-enforcer, normalizer, gap-analyst |
| `code-constitution.md` | "These rules override everything" | all agents |

**Staleness detection:**
The convention-scanner stamps the map with a generation timestamp and file counts per dimension. If the enforcer encounters a file in a directory the map doesn't cover (new directory since last scan), it flags `CONVENTION_DRIFT — unmapped directory: {path}` and the Conductor decides whether to re-scan or add a one-off entry.

---

## Orchestration Updates

### Phase Modifications to `sdlc-orchestrate/SKILL.md`

**Phase 0: Normalize (NEW — mandatory, auto-depth)**
- Dispatch `normalizer` agent on every session entry
- Clean state → no-op | Partial artifacts → resume | Unstructured changes → full normalization
- Normalization directives require user approval
- Never skipped

**Phase 2: Scout — additions:**
- Dispatch `convention-scanner` if Convention Map missing or stale (>30 days)
- Dispatch `gap-analyst` in Finder mode
- Convention Map + Gap Analysis feed into Phase 3 as required context
- Phase 3 only creates beads for MISSING and PARTIAL items from gap analysis

**Phase 4: Execute — L1 sentinel loop expansion:**
- `convention-enforcer` runs alongside `drift-detector` in L1
- BLOCKING convention violations trigger L1 correction (same path as drift-detector)
- CONVENTION_DRIFT signal → Conductor reviews Convention Map

**Phase 5: Synthesize — additions:**
- After drift-detector (step 3): dispatch `gap-analyst` in Finisher mode (step 3.25)
- After gap-analyst: dispatch `normalizer` in Final Pass mode (step 3.5)
- Then: losa-observer (step 3.75) → haiku-handoff (step 4)

### Updated Quick Reference

| Phase | Runners | Sentinel | Oracle | Reuse/Fitness/Convention | Conductor |
|-------|---------|----------|--------|-------------------------|-----------|
| Normalize | normalizer | — | — | convention-scanner (if needed) | Detect state, approve directives |
| Frame | sonnet-investigator | haiku-evidence | — | — | Define mission, scope, criteria |
| Scout | sonnet-investigator + convention-scanner + gap-analyst (Finder) | haiku-evidence | — | — | Gather context, map conventions, find gaps |
| Architect | sonnet-designer | haiku-verifier | — | — | Choose approach, create bead manifest |
| Execute | sonnet-implementer (parallel OK) | haiku-verifier + drift-detector + convention-enforcer | oracle L1+L2 (per bead) | reuse-scout (pre-dispatch) | Distribute beads, recover failures |
| Synthesize | sonnet-reviewer + gap-analyst (Finisher) + normalizer (Final Pass) + losa-observer | haiku-handoff | oracle L1+L2+L3 (integration) | fitness report (full, includes Conventions) | Merge results, deliver |

### `sdlc-fitness/SKILL.md` — New Dimension

Add to Fitness Dimensions table:
```
| **Conventions** | Naming, structure, style match Convention Map | convention-enforcer report |
```
Same thresholds: >80 PASS, 60-80 WARNING, <60 BLOCKING.

### `sdlc-loop/SKILL.md` — L1 Description Update

L1 sentinel loop description updated to include convention-enforcer alongside drift-detector. No new loop level — convention enforcement is part of L1 with the same budget and escalation path.

---

## New Commands

### `/normalize`
**File:** `commands/normalize.md`
**Purpose:** Manually trigger normalization — assess current state, produce convention map if missing, generate alignment directives
**When:** User knows they're picking up mid-stream work or wants a convention refresh

### `/gap-analysis`
**File:** `commands/gap-analysis.md`
**Purpose:** Manually trigger gap analysis in either Finder or Finisher mode
**Args:** Optional `--mode finder|finisher` (defaults to Finder if no SDLC artifacts exist, Finisher if they do)
**When:** User wants a completeness assessment outside of the normal SDLC flow

---

## V3 Integration Points

These new components interact with v3 additions:

| V3 Feature | Integration |
|------------|-------------|
| Cynefin domain classification | Normalizer recovers Cynefin assignments during resume; convention-enforcer severity may be relaxed for Chaotic beads |
| Code constitution | Constitution rules override convention map entries; normalizer checks constitution during full normalization |
| Precedent system | Gap-analyst Finder mode checks precedent system for verdicts informing completeness |
| Quality SLOs | Gap-analyst Finisher mode feeds uncovered gaps into test coverage delta SLI; convention violations may affect lint pass rate SLI |
| Calibration protocol | Convention-enforcer false positive rate can be tracked as a calibration signal; persistent CONVENTION_DRIFT may indicate scanner calibration needed |
| LOSA observer | LOSA can assess convention adherence as part of its quality baseline scoring |
| Error budgets | Convention violations at BLOCKING level count against lint pass rate SLI |

---

## Implementation Order

1. `references/convention-dimensions.md` — shared vocabulary (no dependencies)
2. `agents/convention-scanner.md` — depends on convention-dimensions.md
3. `agents/convention-enforcer.md` — depends on convention-dimensions.md
4. `agents/normalizer.md` — depends on convention-scanner (dispatches it)
5. `agents/gap-analyst.md` — independent
6. `skills/sdlc-normalize/SKILL.md` — depends on normalizer + convention-scanner + gap-analyst
7. `skills/sdlc-gap-analysis/SKILL.md` — depends on gap-analyst
8. `commands/normalize.md` — depends on sdlc-normalize skill
9. `commands/gap-analysis.md` — depends on sdlc-gap-analysis skill
10. Update `skills/sdlc-orchestrate/SKILL.md` — depends on all new agents + skills
11. Update `skills/sdlc-fitness/SKILL.md` — depends on convention-enforcer
12. Update `skills/sdlc-loop/SKILL.md` — depends on convention-enforcer
13. Update Quick Reference table in orchestrate skill
