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

AST analysis complements grep (pattern matching) and LSP (symbol resolution) by providing structural code analysis. The primary implementation is `scripts/ast-checks.sh`, which uses eslint AST rules for deterministic structural checks. tree-sitter support is planned for language-agnostic analysis when installed.

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

### AST Catalog Entries

| Check | Command | Pass Criterion | Category |
|---|---|---|---|
| MAINT-001: Cyclomatic complexity | `bash "${CLAUDE_PLUGIN_ROOT}/scripts/ast-checks.sh" --check MAINT-001 {files}` | `status: CLEAN` (no function exceeds complexity 15) | maintainability |
| REL-005: Dead code / unreachable | `bash "${CLAUDE_PLUGIN_ROOT}/scripts/ast-checks.sh" --check REL-005 {files}` | `status: CLEAN` (no unreachable code or unused vars) | reliability |
| MAINT-003: God class / file length | `bash "${CLAUDE_PLUGIN_ROOT}/scripts/ast-checks.sh" --check MAINT-003 {files}` | `status: CLEAN` (no file > 500 lines, no function > 100 lines) | maintainability |
| PERF-001: Expensive loop operations | `bash "${CLAUDE_PLUGIN_ROOT}/scripts/ast-checks.sh" --check PERF-001 {files}` | `status: CLEAN` (no await-in-loop) | performance |

**Availability:** Requires a project-local `node_modules/.bin/eslint` (v8 or earlier) on the target file's ancestor path, or a globally-installed `eslint` in `PATH`. If unavailable, the script emits `{"status":"UNAVAILABLE","reason":"..."}` on **stdout** and exits 0 (fail-open — never blocks PostToolUse). Consumers must treat any non-{CLEAN,FINDINGS} status as "check could not run" and fall back to LLM-based agents (simplicity-auditor, drift-detector). This graceful degradation is by design: AST checks are the preferred path but not a hard gate when tooling is absent.

**Known limitation:** The current invocation uses `--no-eslintrc` and `--parser` CLI flags, which were removed in ESLint 9's flat config. On projects using ESLint 9+, the script emits UNAVAILABLE with a clear diagnostic pointing to the version mismatch. A rewrite for ESLint 9 flat config is pending.

**FFT-08 routing:** These checks are deterministic (binary pass/fail output). Per FFT-08, the Conductor routes them to the script before dispatching LLM-based sentinel checks. If the script returns FINDINGS, the L1 correction directive includes the AST-detected issues alongside any LLM findings.

## Adding New Checks

When adding a new verification check to the pipeline:
1. Ask FFT-08: "Is this answerable by running a command with binary pass/fail?"
2. If YES → add to this catalog with command and category
3. If NO → route to LLM_AGENT
4. Classification is reviewed during Evolve cycles
