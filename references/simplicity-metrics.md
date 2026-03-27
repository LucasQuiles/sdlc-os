# Simplicity Metrics Reference

Reference for the simplicity-auditor agent. Provides metric definitions, detection heuristics, threshold calibration guidance, and theoretical grounding.

---

## 1. Complexity Metrics Catalog

### Solution Complexity Dimensions

| Metric | What It Measures | How to Compute | Weight |
|--------|-----------------|----------------|--------|
| Lines of code | Raw size | Count non-blank, non-comment lines in diff | 1 |
| Abstractions | Structural complexity | Count new class/interface/type/generic declarations | 3 |
| Dependencies | Coupling | Count new import statements from modules not previously imported | 2 |
| Nesting depth | Control flow complexity | Find maximum indentation level in new code blocks | 2 |
| Cyclomatic complexity | Branch complexity | Count if/else/switch/for/while/try/catch occurrences | 1 |

**Weight rationale:** Abstractions carry weight 3 because a new class or interface imposes a cognitive tax on every future reader — it must be understood, located, and traced. A line of code imposes weight 1 because a line is locally bounded. Dependencies carry weight 2 because they extend the blast radius of change.

---

## 2. Problem Complexity Estimation

| Factor | Values | Weight | Rationale |
|--------|--------|--------|-----------|
| Scope | file count in bead | 2 | More files means more legitimate surface area for code |
| Domain | ESSENTIAL=3, ACCIDENTAL=1 | — | Essential work (core logic) requires more code than accidental work (config, glue) |
| Cynefin | clear=1, complicated=2, complex=3 | — | Complex problems require exploration; clear problems have known solutions |
| Requirements | acceptance criteria count | 1 | More criteria means more legitimate behavioral coverage |

**Score formula:** Problem Complexity = (file_count × 2) + domain_score + cynefin_score + (criteria_count × 1)

---

## 3. Simplicity Coefficient Thresholds

```
simplicity_coefficient = problem_complexity_score / solution_complexity_score
```

| Range | Verdict | Interpretation |
|-------|---------|---------------|
| >= 0.5 | PASS | Solution is proportionate to the problem |
| 0.3 – 0.5 | WARNING | Solution may be over-engineered — justify or simplify specific areas |
| < 0.3 | BLOCKING | Solution is disproportionately complex — must simplify before merge |

**Domain adjustments:**
- ACCIDENTAL beads (config, boilerplate, scaffolding) should almost always produce coefficient >= 0.5. A coefficient below 0.5 for an ACCIDENTAL bead is a strong signal that the runner introduced unnecessary structure.
- ESSENTIAL beads receive more latitude because domain logic genuinely requires more code, but coefficient < 0.3 still requires justification.

---

## 4. Anti-Pattern Detection Heuristics

### 4.1 Factory Wrapping Single Function

**Detection:** Identify a class that (a) contains exactly one public method, (b) is instantiated exactly once at the call site, and (c) has no inheritance or interface relationship driving the pattern.

**False positive conditions:** The factory is justified when (a) the instantiation site will grow to multiple call sites, (b) the constructor arguments vary at runtime and cannot be inlined, or (c) the class is part of an existing factory hierarchy in the codebase.

**Recommended fix:** Inline the class body into the single call site. Replace `new FooFactory().create(x)` with `createFoo(x)` as a standalone function.

---

### 4.2 Strategy Pattern for Two Branches

**Detection:** Identify an interface with exactly two implementations where both are instantiated in the same function and selected by a boolean or enum condition.

**False positive conditions:** The strategy is justified when (a) the implementations are in different modules or packages, (b) the selection condition comes from external configuration and is expected to grow, or (c) the interface is part of an established extension point in the system.

**Recommended fix:** Collapse the two implementations into a single function with an if/else on the discriminant value. Delete the interface and both implementation classes.

---

### 4.3 Premature Generalization

**Detection:** Identify a generic type parameter (T, K, V, etc.) or a generic interface where there is exactly one concrete implementation or instantiation in the submitted code.

**False positive conditions:** Generics are justified when (a) the generic is constrained by a bounds that is meaningful (e.g., `T extends Comparable`) and the constraint is exercised, (b) the generic matches an established pattern in the codebase (e.g., a repository interface), or (c) the type parameter is required by a framework or library contract.

**Recommended fix:** Remove the type parameter and replace with the concrete type. If the concrete type is not yet known, that is a design smell — resolve it before writing the generic.

---

### 4.4 Dead Code Paths

**Detection:** Identify functions, methods, or branches defined in the diff that are never invoked or reached within the bead's scope (the set of files in the bead spec).

**False positive conditions:** Dead code is justified when (a) the function is exported as part of a public API and consumed by code outside the bead scope, (b) the function is registered as a callback or handler and invoked by a framework, or (c) the function is a test helper consumed by test files not in the diff.

**Recommended fix:** Delete the unreachable code. If it is intended for future use, move it to a clearly marked extension point or document the deferral in a comment.

---

### 4.5 Copy-Paste Amplification

**Detection:** Identify three or more code blocks in the diff that share the same structure and differ only in variable names, string literals, or numeric constants.

**False positive conditions:** Repetition is justified when (a) the blocks are declarative configuration that cannot be abstracted without a DSL, (b) the language does not support the abstraction without generics (and generics would introduce worse complexity), or (c) the blocks are in test files and repetition aids readability of individual test cases.

**Recommended fix:** Extract a shared function parameterized over the varying values. Replace all three or more call sites with calls to the extracted function.

---

### 4.6 Over-Abstraction

**Detection:** Trace the call path from an entry point to the actual operation. Count the number of function or method boundaries crossed. Flag when the count exceeds 3 for an operation that could be expressed directly (read a value, write a value, call an API).

**False positive conditions:** Indirection is justified when (a) each layer adds a distinct concern (logging, validation, caching, transformation) that cannot be collapsed, (b) the layering matches an established architectural pattern documented in the codebase, or (c) the indirection exists for testability and the intermediate interfaces are tested independently.

**Recommended fix:** Identify the layers that add no distinct concern and inline them. Name the target depth in the finding (e.g., "flatten from 5 layers to 2").

---

## 5. Calibration Notes

Track audit outcomes over time to tune thresholds:

- If the simplicity audit produces **>30% false positives** (auditor flags BLOCKING or WARNING but post-merge review confirms the complexity was warranted), **raise thresholds** — increase the WARNING floor from 0.3 to 0.35 or the PASS floor from 0.5 to 0.6.
- If the simplicity audit catches **<10% of post-merge complexity issues** identified in retrospectives, **lower thresholds** — decrease the PASS floor or increase the weight on abstractions.
- Track false positives by anti-pattern type. If one anti-pattern produces most false positives, refine its detection logic before adjusting the coefficient thresholds.

This is a Phase C telemetry system. The thresholds above are initial estimates derived from first principles, not from empirical calibration. Expect to revise them after the first 20–30 audits.

---

## 6. Sources

- **Karpathy Slopacolypse** — thinkers-lab netnew-004 (Slopacolypse Defense). Karpathy's nanoGPT simplicity ethos: prefer fewer abstractions, prefer code you can read end-to-end, prefer understanding over extensibility.
- **Gigerenzer less-is-more** — Gerd Gigerenzer, _Simple Heuristics That Make Us Smart_. In environments with uncertainty and limited data, simpler models generalize better than complex ones. Applies to code: simpler code degrades more gracefully under changing requirements.
