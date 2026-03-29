# Deterministic Checks Catalog

Checks that MUST be routed to shell scripts (p=1.0), not LLM agents (p<1.0). Used by FFT-08 to classify each verification check.

**Principle:** Every LLM call removed from the pipeline improves end-to-end reliability (Karpathy March of Nines). Deterministic questions get deterministic tools.

**Anti-pattern guarded:** Garbage In, Gospel Out (Sterman) — do not use probabilistic reasoning for questions with known, computable answers.

---

## Classification Rules

| Routing | Criteria | Reliability |
|---------|----------|-------------|
| DETERMINISTIC | Binary pass/fail answerable by running a command | p=1.0 |
| LLM_AGENT | Requires reading code and reasoning about behavior, architecture, or intent | p<1.0 |

## Deterministic Check Catalog

| Check | Command | Output | Category |
|-------|---------|--------|----------|
| TypeScript type check | `npx tsc --noEmit` | exit 0/1 | compilation |
| ESLint | `npx eslint {files}` | exit 0/1 + error count | linting |
| Python type check | `mypy {files}` | exit 0/1 | compilation |
| Python lint | `ruff check {files}` | exit 0/1 | linting |
| Go vet | `go vet ./...` | exit 0/1 | compilation |
| Test suite | `npm test` / `pytest` / `go test` | exit 0/1 + pass count | testing |
| File exists | `test -f {path}` | exit 0/1 | existence |
| Import cycle detection | `madge --circular {entry}` | exit 0/1 + cycle list | structural |
| Schema validation | `ajv validate -s {schema} -d {data}` | exit 0/1 | conformance |
| Coverage threshold | `coverage report --fail-under={N}` | exit 0/1 | coverage |
| Secret pattern scan | `gitleaks detect --source {path}` | exit 0/1 | security |
| License header check | `grep -l "Copyright" {files}` | match/no-match | compliance |
| JSON/YAML validity | `jq . {file}` / `python -c "import yaml; yaml.safe_load(open('{file}'))"` | exit 0/1 | syntax |
| Dependency audit | `npm audit --audit-level=critical` | exit 0/1 | security |
| Git conflict markers | `grep -r "<<<<<<" {files}` | match/no-match | structural |

## AST-Based Checks

AST analysis complements grep (pattern matching) and LSP (symbol resolution) by providing structural code analysis. Use tree-sitter or language-specific parsers when available.

**When to use AST over grep:**
- Cyclomatic complexity computation (need to count branches in control flow, not just grep for `if`)
- Nesting depth measurement (need to track scope depth, not just indentation)
- Dead code detection (need to trace reachability, not just grep for function names)
- Pattern matching on syntax structure (factory wrapping single function, strategy for two-branch conditional)

**When to use AST over LSP:**
- LSP provides type-level information (signatures, references, hierarchy)
- AST provides syntax-level information (control flow, nesting, complexity)
- Both are needed for full analysis — they answer different questions

**Available via:**
- `tree-sitter` CLI (if installed) — language-agnostic, fast parsing
- Language-specific: `tsc --noEmit` for TypeScript type checking, `eslint --rule` for rule-based AST checks
- Claude Code's LSP tool provides some AST-adjacent capabilities (documentSymbol gives structure)

**Checks that benefit from AST:**

| Check | grep | LSP | AST | Best approach |
|---|---|---|---|---|
| Cyclomatic complexity (MAINT-001) | Approximate (count keywords) | No | Exact (count branches) | AST preferred, grep fallback |
| Nesting depth | Approximate (indentation) | No | Exact (scope tracking) | AST preferred, grep fallback |
| Dead code paths (REL-005) | Partial (unused exports) | Partial (findReferences) | Full (reachability) | LSP + AST |
| Factory wrapping single function | Regex heuristic | Class with 1 method (documentSymbol) | Exact structural match | AST preferred |
| N+1 query pattern (PERF-001) | Partial (query inside loop) | Call hierarchy helps | Full (loop + query in scope) | AST + LSP |

## Adding New Checks

When adding a new verification check to the pipeline:
1. Ask FFT-08: "Is this answerable by running a command with binary pass/fail?"
2. If YES → add to this catalog with command and category
3. If NO → route to LLM_AGENT
4. Classification is reviewed during Evolve cycles
