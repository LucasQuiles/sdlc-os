# Reuse-First Enforcement System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add agents, skills, and tooling to the SDLC OS that enforce DRY, single source of truth, separation of concerns, and reuse-first principles — preventing drift, invariant violations, and duplicated work before they happen.

**Architecture:** Three layers of defense: (1) Pre-dispatch context injection — runners see what already exists before they start, (2) In-flight fitness checks — sentinel detects violations during execution, (3) Post-submission audit — dedicated agents catch what slipped through. The core insight from research: agents duplicate because they lack context, not because they are careless. Prevention = visibility.

**Tech Stack:** Claude Code plugin system (agents, skills, references), jscpd for clone detection, grep/AST patterns for invariant checks.

## Research Sources

- [Architectural Fitness Functions](https://continuous-architecture.org/practices/fitness-functions/) — automated invariant enforcement
- [CodeScene: Agentic AI Best Practices](https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality) — AGENTS.md, code health gates
- [Faros AI: DRY in AI-Generated Code](https://www.faros.ai/blog/ai-generated-code-and-the-dry-principle) — context-as-prevention
- [jscpd](https://github.com/kucherenko/jscpd) — copy/paste detection
- [Simon Willison: Agentic Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/better-code/) — compound engineering loops

---

## File Structure

```
~/.claude/plugins/sdlc-os/
├── agents/
│   ├── reuse-scout.md          # NEW — pre-dispatch: finds existing solutions
│   └── drift-detector.md       # NEW — post-submission: detects invariant violations
├── skills/
│   ├── sdlc-reuse/SKILL.md     # NEW — reuse-first protocol for the Conductor
│   └── sdlc-fitness/SKILL.md   # NEW — architectural fitness function runner
├── references/
│   ├── fitness-functions.md    # NEW — catalog of fitness checks
│   └── reuse-patterns.md      # NEW — canonical source registry
└── commands/
    └── audit.md                # NEW — /audit command for on-demand checks
```

---

### Task 1: Reuse Scout Agent

**Files:**
- Create: `agents/reuse-scout.md`

The Reuse Scout runs BEFORE every implementation runner. The Conductor dispatches it with the bead spec, and it returns existing solutions the runner must consider.

- [ ] **Step 1: Write the agent definition**

Frontmatter: name `reuse-scout`, model `haiku`, description mentions pre-dispatch, finding existing solutions.

System prompt mandate:
- Given a bead spec, search for existing functions, utilities, patterns, and abstractions
- Search strategies: grep for related function names, check lib/utils/ and lib/storage/ and lib/services/, check import graphs, check test files for existing capabilities
- Output format: `## Existing Solutions` table (path | function | relevance) + `## Reuse Recommendation` (reuse X, extend Y, create Z only if nothing exists)
- Anti-patterns: "I didn't find anything" without documenting search scope; recommending creation when an 80% solution exists
- The runner MUST receive this report in its dispatch context

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/plugins/sdlc-os && git add agents/reuse-scout.md && git commit -m "feat: add reuse-scout agent"
```

---

### Task 2: Drift Detector Agent

**Files:**
- Create: `agents/drift-detector.md`

Runs AFTER runner submission during sentinel loop. Checks for DRY/SSOT/SoC/pattern violations.

- [ ] **Step 1: Write the agent definition**

Frontmatter: name `drift-detector`, model `sonnet`, description mentions post-submission invariant checking.

System prompt checks for:
- DRY violations: duplicated logic that exists elsewhere
- SSOT violations: second sources of truth (duplicate constants, parallel config)
- SoC violations: mixed concerns (business logic in UI, storage in routes)
- Pattern drift: deviated from established project patterns
- Import graph health: circular deps, storage layer bypass

Output: Violations table (severity | type | file:line | canonical source | recommendation) + Fitness Score (0-100)
Severities: BLOCKING (must fix) | WARNING (should fix) | NOTE (consider)

- [ ] **Step 2: Commit**

```bash
git add agents/drift-detector.md && git commit -m "feat: add drift-detector agent"
```

---

### Task 3: Reuse-First Skill

**Files:**
- Create: `skills/sdlc-reuse/SKILL.md`

- [ ] **Step 1: Write the skill**

Defines the reuse-first protocol:
1. Pre-dispatch: Conductor dispatches reuse-scout before every implementation runner
2. Context injection: Scout report injected into runner context as "Existing Solutions"
3. Runner obligation: Must include Reuse Report (what was reused + what was created with justification)
4. Sentinel integration: drift-detector runs in L1 loop on every implementation bead
5. Guppy swarm pattern: For large beads, swarm guppies to pre-scan for reuse opportunities

- [ ] **Step 2: Commit**

```bash
mkdir -p skills/sdlc-reuse && git add skills/sdlc-reuse/SKILL.md && git commit -m "feat: add reuse-first skill"
```

---

### Task 4: Fitness Function Skill

**Files:**
- Create: `skills/sdlc-fitness/SKILL.md`

- [ ] **Step 1: Write the skill**

Defines architectural fitness functions:
- Types: structural, duplication, convention, coverage, boundary
- When: per-bead (sentinel loop), per-phase (after Execute), on-demand (/audit)
- How: dispatch drift-detector + guppy swarm, aggregate into fitness report
- Scoring: < 60 BLOCKING, 60-80 WARNING, > 80 PASS
- Integration with loop mechanics (L1 correction on BLOCKING)

- [ ] **Step 2: Commit**

```bash
mkdir -p skills/sdlc-fitness && git add skills/sdlc-fitness/SKILL.md && git commit -m "feat: add fitness function skill"
```

---

### Task 5: Reference Documents

**Files:**
- Create: `references/fitness-functions.md`
- Create: `references/reuse-patterns.md`

- [ ] **Step 1: Write fitness-functions.md**

Catalog of checks: import graph, StorageError usage, generateId usage, requirePermission usage, safeToast usage, test assertion quality. Each with type, how to check, pass condition, fail action.

- [ ] **Step 2: Write reuse-patterns.md**

Registry of canonical sources: id-generator, error-utils, safe-toast, currency-utils, formatting, permissions/shared, storage-error, transaction-helper. Each with canonical path, usage example, common misuse.

- [ ] **Step 3: Commit**

```bash
git add references/fitness-functions.md references/reuse-patterns.md && git commit -m "feat: add fitness catalog and reuse patterns registry"
```

---

### Task 6: Audit Command

**Files:**
- Create: `commands/audit.md`

- [ ] **Step 1: Write the command**

/audit [full|changed|path] — invokes sdlc-fitness skill for on-demand fitness checks.

- [ ] **Step 2: Commit**

```bash
git add commands/audit.md && git commit -m "feat: add /audit command"
```

---

### Task 7: Wire Into Orchestration

**Files:**
- Modify: `skills/sdlc-orchestrate/SKILL.md`

- [ ] **Step 1: Update orchestration skill**

Add reuse-first protocol to Execute phase. Add drift-detector to sentinel loop. Add fitness check to Synthesize phase. Update Quick Reference table.

- [ ] **Step 2: Commit and push**

```bash
git add skills/sdlc-orchestrate/SKILL.md && git commit -m "feat: wire reuse-first and fitness into orchestration" && git push origin main
```

---

### Task 8: Deploy to Mesh

- [ ] **Step 1: Update nucles**

```bash
ssh q@nucles.local 'cd ~/.claude/plugins/sdlc-os && git pull'
```

- [ ] **Step 2: Update brick**

```bash
ssh -i ~/.ssh/id_ed25519 andre@100.101.199.28 'wsl -u drew -- bash -c "cd ~/.claude/plugins/sdlc-os && git pull"'
```

---

## Addendum: Multi-Layer Analysis Chains (LSP + AST + Grep)

Based on research into [LSP agent integration](https://tech-talk.the-experts.nl/give-your-ai-coding-agent-eyes-how-lsp-integration-transform-coding-agents-4ccae8444929), [LSAP protocol](https://github.com/lsp-client/LSAP), and [AST-based analysis with ts-morph](https://kimmo.blog/posts/8-ast-based-refactoring-with-ts-morph/).

### Core Insight

Agents should NOT use a single tool per pass. They should orchestrate **multi-layer analysis chains** where each layer feeds the next. A grep match is a hint. An LSP resolution is a fact. A call hierarchy is a map. Combined, they produce compound intelligence no single pass achieves.

### The Four-Layer Analysis Chain

Every reuse-scout and drift-detector dispatch should follow this chain:

**Layer 1 — Broad Scan (Guppies + Grep)**
- Swarm guppies with grep patterns related to the bead objective
- Find files, function names, import patterns that are potentially relevant
- Output: candidate file list + keyword matches
- Cost: cheap (Haiku guppies)

**Layer 2 — Symbol Resolution (LSP)**
- Use `workspaceSymbol` to find functions/classes by name across the workspace
- Use `documentSymbol` to inventory exports in candidate files from Layer 1
- Use `hover` to get type signatures without reading full implementations
- Output: typed symbol map with locations and signatures
- Cost: zero (LSP is local, no model invocation)

**Layer 3 — Semantic Tracing (LSP Call Hierarchy)**
- Use `goToDefinition` to trace usages to canonical sources
- Use `findReferences` to map all consumers of candidate symbols
- Use `incomingCalls` / `outgoingCalls` to build call graphs
- Output: dependency graph showing canonical sources, all callers, and impact areas
- Cost: zero (LSP is local)

**Layer 4 — Deep Analysis (Sonnet)**
- Runner or drift-detector reads actual code WITH full context from Layers 1-3
- Makes informed decisions: reuse, extend, or create new
- Every decision references specific evidence from prior layers
- Output: actionable recommendation with traced evidence chain
- Cost: one Sonnet invocation with rich context (not blind)

### How This Changes Each Agent

**Reuse Scout (updated protocol):**
```
1. Receive bead spec
2. Layer 1: Swarm guppies — grep for related function names, patterns, imports
3. Layer 2: LSP workspaceSymbol — find typed symbols matching the objective
4. Layer 3: LSP goToDefinition — trace each candidate to its canonical source
5. Layer 4: Synthesize — produce Existing Solutions report with traced evidence
```

The scout now delivers not just "this function exists" but "this function exists at lib/utils/id-generator.ts:37, it is called by 47 other files, its signature is `generateId(prefix: string, randomLength?: number): string`, and it does exactly what your bead needs."

**Drift Detector (updated protocol):**
```
1. Receive runner output (files changed)
2. Layer 1: For each new function, grep — does a similar name exist elsewhere?
3. Layer 2: LSP findReferences — does the runner's code duplicate an existing pattern?
4. Layer 3: LSP incomingCalls on modified functions — did the change break any callers?
5. Layer 4: Deep analysis — classify each finding as DRY/SSOT/SoC/pattern violation
```

The detector now catches not just copy-paste clones but **semantic duplicates** — functions that do the same thing but have different names. LSP call hierarchy reveals whether a "new" function is actually a reimplementation of an existing one.

### LSP Operations Reference for Agents

Agents should use the LSP tool with these operations:

| When You Need | LSP Operation | Example |
|---|---|---|
| Find where a function is defined | `goToDefinition` | Trace `generateId` to its source |
| Find all places a function is used | `findReferences` | Who calls `getErrorMessage`? |
| Get type info without reading code | `hover` | What does `formatCurrency` accept/return? |
| List all exports in a file | `documentSymbol` | What does `lib/utils/formatting.ts` export? |
| Search for functions by name | `workspaceSymbol` | Find all functions containing "format" |
| Find what calls a function | `incomingCalls` | Who depends on `getUserRoleById`? |
| Find what a function calls | `outgoingCalls` | What does `createPayment` depend on? |
| Find interface implementations | `goToImplementation` | What classes implement `StorageError`? |

### Multi-Pass Pattern for Complex Analysis

For complex beads, agents can run **multiple passes with escalating depth**:

**Pass 1 — Survey (Guppies, 2 min):**
Swarm 10 guppies doing targeted greps. Get the lay of the land.

**Pass 2 — Map (LSP, 0 cost):**
Chain LSP calls to build a symbol/call graph of the relevant area. No model cost.

**Pass 3 — Analyze (Sonnet, 1 invocation):**
Feed the map to a Sonnet runner/detector with full context. One deep analysis.

**Pass 4 — Verify (Haiku sentinel, cheap):**
Sentinel cross-checks the analysis against the LSP-derived evidence.

Total cost: 10 guppy invocations + 1 Sonnet + 1 Haiku = 12 cheap calls with LSP doing the heavy lifting for free.

### Integration with Existing Loop Mechanics

The multi-layer chain integrates into the L0-L5 loop system:

- **L0 (Runner self-correction):** Runner uses LSP hover/goToDefinition to verify its own imports are correct before submitting
- **L1 (Sentinel):** Sentinel uses LSP findReferences to verify the runner did not break callers
- **L2 (Oracle):** Oracle uses LSP documentSymbol to verify test files actually test the right functions
- **Reuse Scout:** Full 4-layer chain before every implementation dispatch
- **Drift Detector:** Layers 1-3 to detect semantic duplication, Layer 4 for classification

---

## Addendum: Pinecone Vector Search as Layer 0

The codebase and documentation are indexed in Pinecone. This adds a semantic memory layer that operates BEFORE all other layers — finding related code and documentation by meaning, not just by keyword or symbol name.

### Why This Matters for Reuse-First

Grep finds exact matches. LSP finds typed symbols. Pinecone finds **semantic neighbors** — code and documentation that is related by meaning even when the names are completely different.

Example: A bead asks to "validate email addresses." 
- Grep finds: nothing (no function named "validate email")
- LSP finds: nothing (no symbol matches)
- Pinecone finds: `lib/validation/schemas.ts` has `z.string().email()` patterns used across 15 routes; `lib/utils/zod-preprocess.ts` has `safeParseBoundary`; docs describe the validation boundary pattern

The reuse scout would have missed this without Pinecone. With it, the runner gets injected with the existing validation patterns before it starts.

### Updated Five-Layer Chain

```
Layer 0 — Semantic Memory (Pinecone)
  Query: "What existing code/docs relate to {bead objective}?"
  Tool: mcp__pinecone__search-records or mcp__pinecone__search-docs
  Returns: related functions, patterns, documentation with similarity scores
  Cost: one API call

Layer 1 — Broad Scan (Guppies + Grep)
  Now INFORMED by Layer 0 hits — guppies grep for specific files/patterns Pinecone flagged
  Cost: cheap (Haiku guppies)

Layer 2 — Symbol Resolution (LSP)
  Use workspaceSymbol + documentSymbol on files identified by Layers 0-1
  Cost: zero (local LSP)

Layer 3 — Semantic Tracing (LSP Call Hierarchy)
  goToDefinition + findReferences + incomingCalls on symbols from Layer 2
  Cost: zero (local LSP)

Layer 4 — Deep Analysis (Sonnet)
  Full context from all prior layers — makes informed reuse/extend/create decisions
  Cost: one Sonnet invocation
```

### Pinecone Integration Points

**Reuse Scout — Pre-dispatch:**
1. Query Pinecone with bead objective as natural language
2. Get back related code snippets, file paths, documentation
3. Feed Pinecone results into Layer 1 grep targets (focused, not blind)
4. Include Pinecone matches in the Existing Solutions report

**Drift Detector — Post-submission:**
1. For each new function the runner created, query Pinecone: "does similar code already exist?"
2. Pinecone returns semantic neighbors — even with different names
3. Detector compares: is this genuinely new or a semantic clone?

**Runners — Context enrichment:**
1. Before starting work, runner can query Pinecone for relevant documentation
2. Framework docs, API references, project conventions — all searchable by meaning
3. Reduces "I didn't know that existed" failures

### Pinecone MCP Tools Available

| Tool | Use |
|------|-----|
| `search-records` | Search code vectors by semantic similarity |
| `search-docs` | Search documentation vectors |
| `cascading-search` | Search across multiple indexes/namespaces |
| `rerank-documents` | Re-rank search results for relevance |

### Cost Model Update

Adding Pinecone to the chain:
- Layer 0: 1 Pinecone API call per bead (~$0.001)
- Layers 1-3: Same as before (guppies + free LSP)
- Layer 4: Same as before (1 Sonnet)
- Net: ~$0.001 additional cost per bead for dramatically better context

---

## Addendum: Episodic Memory as Layer -1

The episodic-memory plugin stores conversation history across sessions with semantic search. This adds institutional memory — agents can recall past decisions, failed approaches, refactoring rationale, and user preferences from prior sessions.

### Why This Matters

Layer 0 (Pinecone) knows what code exists. Layer -1 (Episodic Memory) knows **why** it exists, what was tried before, and what the user decided.

Example: A bead asks to "add caching to the API."
- Pinecone finds: existing cache patterns in the codebase
- Episodic Memory finds: "In session 3 weeks ago, we discussed adding Redis caching but the user decided against it because the SQLite DB is fast enough. We added in-memory LRU caching instead."

Without episodic memory, the runner might propose Redis again. With it, the runner knows to use the LRU pattern.

### Updated Six-Layer Chain

```
Layer -1 — Episodic Memory (conversation history)
  Query: "What past decisions/sessions relate to {bead objective}?"
  Tool: episodic-memory:search-conversations agent
  Returns: relevant conversation excerpts, past decisions, failed approaches
  Cost: one agent dispatch

Layer 0 — Semantic Memory (Pinecone)
  [unchanged]

Layer 1-4 — [unchanged]
```

### Integration Points

**Reuse Scout — Pre-dispatch (enhanced):**
1. Query episodic memory: "Have we worked on {objective} before? What was decided?"
2. Query Pinecone: "What existing code/docs relate to this?"
3. Layers 1-3: LSP-based analysis
4. Inject ALL findings into runner context

**Drift Detector — Post-submission (enhanced):**
1. Query episodic memory: "Were there any past decisions about how {pattern} should be implemented?"
2. Compare runner output against historical decisions
3. Flag violations of past architectural decisions, not just current code patterns

**Conductor — Task decomposition (enhanced):**
1. Before decomposing, query episodic memory: "Have we done something similar before?"
2. Reuse prior bead decomposition patterns that worked
3. Avoid repeating decomposition mistakes from prior sessions

### Episodic Memory Tool

The `episodic-memory:search-conversations` agent searches conversation history. Dispatch it like any other agent:

```
Agent tool:
  subagent_type: episodic-memory:search-conversations
  description: "Recall prior sessions about {topic}"
  prompt: "Search for conversations about {bead objective}. 
           What decisions were made? What approaches were tried?
           What failed and why? What does the user prefer?"
```
