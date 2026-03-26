---
name: sdlc-swarm
description: "Wield guppy swarms to chip away at a problem progressively. Decompose a question into micro-directives, dispatch haiku guppies in parallel, synthesize findings, and re-swarm on gaps. Used by the Conductor or Sentinel to attack problems with focused, disposable micro-agents."
---

# Swarm Control

You are wielding guppies — cheap, disposable, laser-focused micro-agents. Each guppy answers ONE question, then dies. The power comes from directing many of them at a problem simultaneously, synthesizing their findings, and re-swarming on the gaps.

## When to Swarm

Use guppy swarms when:
- You need to audit a pattern across many files (e.g., "do all storage functions use soft-delete?")
- You need to verify multiple independent claims simultaneously
- You need to search/grep across a codebase and analyze each match
- A problem can be decomposed into many independent yes/no questions
- Speed matters more than depth on any single check

Do NOT swarm when:
- The task requires deep reasoning about interconnected logic
- You need multi-step analysis where step 2 depends on step 1's answer
- The question is inherently singular (one file, one function, one decision)

## The Swarm Cycle

```
1. DECOMPOSE: Break the problem into N independent micro-directives
2. DISPATCH: Launch N guppies in parallel (Agent tool, model: haiku)
3. HARVEST: Collect all guppy responses
4. SYNTHESIZE: Merge findings into a coherent picture
5. RE-SWARM: If gaps remain, decompose the gaps and dispatch again
6. DELIVER: Report the consolidated result
```

### Step 1: Decompose

Turn one big question into many small ones. Each directive must be:
- **Self-contained** — the guppy needs no other context to answer
- **Binary or factual** — yes/no, exists/doesn't, count, or specific value
- **Scoped to one location** — one file, one function, one endpoint

**Example decomposition:**

Problem: "Which API routes are missing Zod validation?"

Directives:
```
Guppy 1: "Read app/api/supply-orders/route.ts POST handler. Does it parse request.json() through a Zod schema before using the data? Answer YES with the schema name or NO."
Guppy 2: "Read app/api/payments/route.ts POST handler. Does it parse request.json() through a Zod schema before using the data? Answer YES with the schema name or NO."
Guppy 3: "Read app/api/expenses/route.ts POST handler. Does it parse..."
...one guppy per route
```

### Step 2: Dispatch

Launch guppies in parallel using the Agent tool:

```
Agent tool:
  subagent_type: general-purpose
  model: haiku
  mode: auto
  name: "guppy-{N}"
  description: "Guppy: {short directive summary}"
  prompt: |
    You are a Guppy — the smallest unit of work. Answer this ONE directive:

    {directive}

    Output format:
    **Answer:** [direct answer]
    **Evidence:** [file:line or command output]
    **Confidence:** [Verified | Likely | Assumed]

    If unclear, respond: UNCLEAR: [what's ambiguous]
```

**Parallelization:** Dispatch as many as the system allows simultaneously. Guppies are read-only and non-overlapping — they cannot conflict.

### Step 3: Harvest

Collect all guppy responses. Each gives you:
- An answer (yes/no/value/UNCLEAR)
- Evidence (file:line reference)
- Confidence label

### Step 4: Synthesize

Merge guppy findings into a table or summary:

```markdown
## Swarm Results: {problem description}

**Dispatched:** {N} guppies | **Returned:** {N} | **UNCLEAR:** {N}

| # | Directive | Answer | Evidence | Confidence |
|---|-----------|--------|----------|------------|
| 1 | {short} | YES/NO | file:line | Verified |
| 2 | {short} | YES/NO | file:line | Verified |

**Findings:**
- {X} of {N} routes missing Zod validation
- {list of specific files}

**Gaps:** {anything guppies couldn't answer}
```

### Step 5: Re-swarm

If gaps remain, decompose them into new directives and dispatch another wave:

```
Wave 1: "Which routes are missing validation?" → 15 guppies → 3 unclear
Wave 2: "For the 3 unclear routes, check if validation happens in middleware instead" → 3 guppies → all resolved
```

Maximum 3 swarm waves before escalating gaps to a Runner (Sonnet) for deeper analysis.

### Step 6: Deliver

Report the consolidated finding to whoever requested the swarm (Conductor, Sentinel, or Oracle).

## Swarm Patterns

### Pattern: Codebase Audit
**Use when:** Checking a rule across many files
**Decompose by:** One guppy per file/function/route
**Example:** "Do all storage functions filter deleted_at IS NULL?"

### Pattern: Claim Verification
**Use when:** A Runner made N claims that need independent checking
**Decompose by:** One guppy per claim
**Example:** "Runner says these 7 files were updated. Verify each."

### Pattern: Regression Scan
**Use when:** Code changed and you need to check callers
**Decompose by:** One guppy per caller/importer of the changed function
**Example:** "getUserRole was renamed. Check each importer still works."

### Pattern: Evidence Collection
**Use when:** Building a case from scattered data
**Decompose by:** One guppy per evidence source
**Example:** "Gather all instances of Math.random() in production code."

### Pattern: Progressive Narrowing
**Use when:** Starting broad and focusing on problems
**Wave 1:** Broad scan (one guppy per file in directory)
**Wave 2:** Deeper check on flagged files only
**Wave 3:** Specific line-level analysis on confirmed problems

## Cost Awareness

Guppies are Haiku — the cheapest model. A swarm of 20 guppies costs roughly the same as one Sonnet Runner. Use this to your advantage:

- **20 guppies checking 20 files** is faster and cheaper than 1 Sonnet reading 20 files
- **Guppies for breadth, Runners for depth** — swarm to find the problem, dispatch a Runner to fix it
- **Don't swarm what you can grep** — if a simple `grep` command answers the question, use Bash instead

## Anti-Patterns

- **Fat guppies** — If a directive takes more than 3 lines to answer, it's too complex. Split it.
- **Dependent guppies** — If guppy 2 needs guppy 1's answer, they can't be parallel. Use waves instead.
- **Guppies for judgment** — Guppies report facts. They don't design, decide, or recommend. That's Runner/Conductor work.
- **Infinite re-swarming** — 3 waves max. After that, the problem needs deeper analysis, not more guppies.
- **Swarming one file** — If the whole problem is in one file, just read it. Don't dispatch 10 guppies at the same file.
