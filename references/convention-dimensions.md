# Convention Dimensions

The canonical list of dimensions assessed by convention-scanner, convention-enforcer, normalizer, and gap-analyst agents. Each dimension defines scope, what to look for, how to detect it programmatically, how severe a violation is, and what evidence to record. Agents must consult this file before deciding what to check or how to report findings.

---

## Dimension 1: File Naming

**Scope:** All source files across the repository.

**What to check:**
- Whether files in each directory follow a consistent casing style (kebab-case, PascalCase, camelCase, snake_case).
- Whether file suffixes follow a discernible pattern (e.g., `.service.ts`, `.handler.ts`, `.test.ts`, `.spec.ts`).
- Whether index files are used consistently or inconsistently (every directory has one vs. none vs. selective).
- Whether test files share a naming convention with the files they test (e.g., `foo.test.ts` alongside `foo.ts`).

**Scanner method:**
- Sample 3–5 files per directory using a glob pass over the tree.
- Tally the casing style of each file name (strip extension, detect style).
- Identify the plurality style per directory; flag files that deviate.
- Do not assume a style — derive it from the existing corpus.

**Enforcer severity:** BLOCKING — file name inconsistency breaks module resolution assumptions and makes grepping unreliable.

**Evidence format:**
```
dimension: file-naming
directory: <relative path>
observed-style: kebab-case
violations:
  - file: MyComponent.ts  (expected: my-component.ts)
  - file: utilsHelper.ts  (expected: utils-helper.ts)
sample-size: 5
```

---

## Dimension 2: Function and Variable Naming

**Scope:** All exported symbols and internal symbols across source files.

**What to check:**
- Whether exported functions, classes, and constants follow a consistent casing convention (e.g., PascalCase for classes, camelCase for functions, SCREAMING_SNAKE for module-level constants).
- Whether internal (non-exported) variables and helpers follow the same or a documented internal convention.
- Whether boolean variables and functions use a consistent predicate prefix (e.g., `is`, `has`, `can`, `should`).
- Whether event handler names follow a consistent pattern (e.g., `handle*`, `on*`).

**Scanner method:**
- Use LSP `documentSymbol` to extract all symbols from each open file.
- Use LSP `workspaceSymbol` with an empty query to get a project-wide symbol index.
- Classify each symbol by kind (function, variable, class, constant) and check casing.
- If `sdlc-os:deduplicating-functions` has produced a `catalog.json` for this project, consume it for naming data at scale rather than re-scanning — join on file path and symbol name.

**Enforcer severity:**
- BLOCKING for exported symbols — public API naming is a contract.
- WARNING for internal symbols — important but not build-breaking.

**Evidence format:**
```
dimension: function-variable-naming
symbol: fetchUserData
kind: exported-function
file: <relative path>:42
issue: expected camelCase, found snake_case (fetch_user_data)
severity: BLOCKING
```

---

## Dimension 3: Component Structure

**Scope:** UI component files (detect by directory name or file suffix convention, e.g., `components/`, `.component.*`, `.view.*`).

**What to check:**
- Whether components follow a consistent internal layout (imports → types/props interface → component function → export).
- Whether prop types are defined inline, as a separate interface, or via a shared types file — and whether this is consistent.
- Whether default exports vs. named exports are used consistently for components.
- Whether co-located files (styles, tests, stories) follow a consistent pattern.

**Scanner method:**
- Read 3–5 representative component files, sampling from different subdirectories if present.
- Parse the top-level structure: identify the first import, the props definition location, the function definition, and the export statement.
- Compare across the sample to detect structural deviations.

**Enforcer severity:** WARNING — structural inconsistency increases cognitive overhead but does not break builds.

**Evidence format:**
```
dimension: component-structure
file: <relative path>
issue: props interface defined after component function (expected: before)
severity: WARNING
```

---

## Dimension 4: Styling Approach

**Scope:** All files that apply visual styles (components, layouts, pages).

**What to check:**
- Whether the project uses a single styling approach or mixes approaches (e.g., utility classes, CSS modules, CSS-in-JS, plain CSS, inline styles).
- The canonical styling import or pattern (e.g., `import styles from './foo.module.css'`, `import 'tailwindcss'`, `styled-components`, etc.).
- Whether inline `style={{}}` props are used and whether that is sanctioned or forbidden.
- Whether a design token or theme system is used and whether components reference it consistently.

**Scanner method:**
- Grep for style imports and patterns: CSS module imports, styled-component patterns, utility class string literals, and `style={{` occurrences.
- Tally occurrences by type across the codebase to identify the dominant approach.
- Flag files that deviate from the dominant approach.

**Enforcer severity:** BLOCKING — mixed styling approaches create maintenance debt and often cause specificity conflicts.

**Evidence format:**
```
dimension: styling-approach
detected-canonical: css-modules
violations:
  - file: <relative path>:88  pattern: style={{ color: 'red' }}  (inline style, not sanctioned)
  - file: <relative path>:12  pattern: import 'styled-components'  (non-canonical approach)
severity: BLOCKING
```

---

## Dimension 5: Import Patterns

**Scope:** Import blocks across all source files.

**What to check:**
- Whether imports are ordered consistently (e.g., external packages → internal absolute paths → relative paths → type-only imports).
- Whether barrel files (`index.ts`) are used and whether their use is intentional or incidental (barrel misuse causes bundler bloat and circular dependency risk).
- Whether import aliases (e.g., `@/`, `~/`, `#`) are used consistently or mixed with raw relative paths.
- Whether `import type` is used for type-only imports where the project convention requires it.

**Scanner method:**
- Read the import block (lines before the first non-import statement) from 5–10 files across different layers.
- Detect the ordering pattern by classifying each import line (external, alias-absolute, relative, type-only).
- Grep for barrel index imports (`from './'`, `from '../'`, `from '@/feature'`) to identify barrel usage density.

**Enforcer severity:**
- NOTE for import ordering — cosmetic, auto-fixable.
- WARNING for barrel misuse — may cause real bundler and circular dependency issues.

**Evidence format:**
```
dimension: import-patterns
file: <relative path>
issue: relative import used where alias is canonical  (import '../../../lib/foo' vs '@/lib/foo')
severity: WARNING

dimension: import-patterns
file: <relative path>
issue: barrel re-export of 47 symbols may cause tree-shaking regression
severity: WARNING
```

---

## Dimension 6: Test Patterns

**Scope:** All test and spec files, and their relationship to the files they test.

**What to check:**
- Whether test files are co-located with source files or centralized in a `__tests__` / `tests` directory — and whether the project is consistent.
- Whether test file naming follows the source file name (e.g., `foo.test.ts` or `foo.spec.ts` for `foo.ts`).
- Whether test descriptions (`describe`, `it`, `test`) follow a consistent language pattern (e.g., imperative "does X", declarative "returns X when Y").
- Whether setup/teardown hooks are used consistently across test files.
- Whether mocking patterns are consistent (module mocks, spy patterns, fixture files).

**Scanner method:**
- Glob for test files using common suffixes: `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**/*`.
- For each test file, check whether a corresponding source file exists at the co-location path or known alias path.
- Sample 3–5 test files and read their `describe`/`it`/`test` call text to assess language pattern.

**Enforcer severity:**
- WARNING for placement inconsistency — co-location drift makes tests harder to find.
- NOTE for naming convention — cosmetic but aids discoverability.

**Evidence format:**
```
dimension: test-patterns
file: <relative path>
issue: test file in __tests__/ but all peers are co-located
severity: WARNING

dimension: test-patterns
file: <relative path>:15
issue: describe block uses passive voice ('User data is returned') vs. project pattern (imperative)
severity: NOTE
```

---

## Dimension 7: Error Handling

**Scope:** All layers where errors are caught, transformed, or surfaced (API handlers, service functions, storage functions, UI boundaries).

**What to check:**
- Whether the project has a canonical error type or error factory and whether it is used in each layer.
- Whether `catch` blocks re-throw, transform, log, or swallow errors — and whether the pattern is consistent per layer.
- Whether user-facing error messages are extracted from errors using a canonical utility (see `reuse-patterns.md` for the canonical source if one is registered).
- Whether raw `throw new Error('string')` is used where a typed error class is the convention.
- Whether error boundaries (UI) or error middleware (API) are present and whether they are consistent.

**Scanner method:**
- Grep for `catch` blocks and `throw new Error` across each layer directory separately.
- Cross-reference with `reuse-patterns.md`: if a canonical error source is listed there (e.g., `StorageError`, `getErrorMessage`), grep for deviations from that pattern within the layer it governs.
- Count bare `catch (e) {}` (swallowed errors) separately — these are highest severity.

**Enforcer severity:** BLOCKING if a canonical source in `reuse-patterns.md` governs the layer in question; WARNING otherwise (until a canonical is established).

**Evidence format:**
```
dimension: error-handling
layer: storage
file: <relative path>:77
issue: throw new Error('not found') — canonical is StorageError.notFound()  (per reuse-patterns.md)
severity: BLOCKING

dimension: error-handling
layer: api-handler
file: <relative path>:34
issue: catch block swallows error with no log or rethrow
severity: BLOCKING
```

---

## Dimension 8: Directory Structure

**Scope:** The top-level and second-level directory layout of the project.

**What to check:**
- Whether the directory structure follows a consistent organizational principle (feature-based, layer-based, domain-based, or hybrid) across the whole project.
- Whether new directories have been added that don't conform to the established pattern (e.g., a `helpers/` directory in a project that uses `utils/`, or a top-level `pages/` directory mixed with a `app/` router).
- Whether directories that should be private (implementation details) are accidentally exposed at the root level.
- Whether the structure matches any declared architecture in `code-constitution.md`.

**Scanner method:**
- Map the existing directory tree to depth 2 using a recursive listing.
- Identify the organizational principle from the majority of directories (feature directories, layer directories, etc.).
- Flag any directory that does not fit the identified principle.
- If `code-constitution.md` declares a structure, diff the actual structure against it.

**Enforcer severity:** BLOCKING — directory structure is the primary navigation aid; drift makes the project unmaintainable.

**Evidence format:**
```
dimension: directory-structure
identified-principle: layer-based (lib/, app/, components/, __tests__/)
violations:
  - directory: helpers/  (does not fit layer principle; expected: lib/utils/ or lib/helpers/)
  - directory: pages/  (conflicts with app/ router convention)
severity: BLOCKING
```

---

## Cross-References

- **`reuse-patterns.md`** — Dimension 7 (Error Handling) depends on this file to know which error utilities are canonical per layer. Scanners must read `reuse-patterns.md` before assessing error handling.
- **`fitness-functions.md`** — Individual fitness functions (e.g., "No Math.random() for IDs", "StorageError in storage layer") are concrete instantiations of Dimension 7. Convention dimensions are the categories; fitness functions are the specific checks within them.
- **`code-constitution.md`** — Dimension 8 (Directory Structure) should be validated against any structural declarations in the constitution. If the constitution names specific directories as canonical, those declarations take precedence over inference from the existing corpus.

---

## Adding New Dimensions

To extend this catalog:

1. Add a new `## Dimension N: <Name>` section following the same structure: Scope, What to check, Scanner method, Enforcer severity, Evidence format.
2. Keep the dimension **framework-agnostic** — describe patterns by their observable properties (casing, import shape, file placement), not by framework-specific APIs.
3. Assign severity based on blast radius: BLOCKING if violation causes build failures, data loss, or security issues; WARNING if it causes maintainability or runtime risk; NOTE if it is cosmetic or auto-fixable.
4. If the dimension depends on a canonical source registered in `reuse-patterns.md`, call that out explicitly in the "What to check" section.
5. Update the Cross-References section if the new dimension has dependencies on other reference files.
6. Add a corresponding fitness function to `fitness-functions.md` for any check that can be expressed as a deterministic pass/fail.
