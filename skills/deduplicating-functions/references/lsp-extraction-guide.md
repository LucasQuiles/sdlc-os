# LSP-Based Symbol Extraction Guide

## Overview

Claude Code has a built-in LSP (Language Server Protocol) tool that provides rich type information, symbol hierarchies, and call graphs. This guide explains how to use it for duplicate detection enrichment.

## When to Use LSP

LSP extraction supplements AST and regex extraction by providing:
- **Resolved types** — actual types after inference, not just annotations
- **Call hierarchy** — which functions call which (helps identify wrapper duplicates)
- **References** — how many callers each function has (prioritize consolidation of widely-used functions)
- **Symbol hierarchy** — accurate class/method/namespace relationships

## LSP Tool Usage

Use Claude Code's `LSP` tool with these operations:

### Get Document Symbols

Extract all symbols from a file with their full type signatures:

```
LSP tool: documentSymbols
file: src/utils/date.ts
```

Returns symbol tree with kinds (Function, Method, Class, Variable) and position ranges.

### Get Type Definition

For a specific function, get its resolved type:

```
LSP tool: hover
file: src/utils/date.ts
line: 42
character: 15
```

Returns the full resolved type signature including inferred types.

### Get Call Hierarchy

Find all callers and callees of a function:

```
LSP tool: callHierarchy
file: src/utils/date.ts
line: 42
character: 15
direction: incoming  # or outgoing
```

Identifies wrapper functions (same callers), delegation chains, and unused duplicates.

### Get References

Count how many places reference a function:

```
LSP tool: references
file: src/utils/date.ts
line: 42
character: 15
```

Higher reference count = higher priority for consolidation (more callers to update).

## Integration with Detection Pipeline

### Enrichment Phase

After initial catalog extraction, dispatch a subagent to:

1. For each function in the catalog:
   - Use LSP `hover` to get resolved type signature
   - Use LSP `references` to count callers
2. Merge LSP data into the unified catalog:
   - `resolved_signature`: full type from LSP
   - `reference_count`: number of callers
   - `callers`: list of caller file:line locations

### Detection Enhancement

LSP data improves detection in several ways:

**Wrapper detection:** If function A's only statement is a call to function B with the same parameters, A is a wrapper/alias. LSP call hierarchy reveals this directly.

**Type-aware signature matching:** Regex/AST extractors see `any` or missing types. LSP resolves actual types, improving signature comparison accuracy.

**Consolidation priority:** Functions with more references should be the "survivor" in consolidation — fewer callers need updating.

## Dispatch Pattern

Since LSP operations require Claude Code's built-in LSP tool (not a standalone script), use a subagent:

```
Dispatch a subagent with model: haiku
Task: "For each function in catalog.json, use the LSP tool to get the resolved type 
signature and reference count. Enrich the catalog with lsp_signature and reference_count 
fields. Save to catalog-lsp-enriched.json."
```

## Limitations

- LSP requires a running language server (TypeScript/JavaScript has tsserver, Python has Pylance/Pyright)
- LSP accuracy depends on the project having proper `tsconfig.json` or type stubs
- Slow for large catalogs (one LSP query per function) — parallelize with subagents
- Not all languages have equally capable LSP servers
