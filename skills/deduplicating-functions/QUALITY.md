# Repository quality checks

`run_quality.py` measures Git-tracked and nonignored untracked Python, Swift and shell
sources. A reviewed policy assigns every eligible file to exactly one production,
test or tooling group. Missing roots, empty groups, overlaps, unclassified files,
syntax errors, changed inputs and incomplete parser coverage fail closed.

The checked-in baseline caps files, bytes, physical lines, syntax nodes, functions, longest
line and longest function per group and in total. The check never updates it.
`--capture-baseline` creates a new file and refuses to overwrite one. Initial imports
and later budget changes require a reviewed diff explaining the cost; reducing a
budget is a separate deliberate ratchet. Renaming groups is not a way to hide growth.

Python uses the existing AST signature/complexity collector. Its new fingerprint
preserves constants, operators, decorators, annotations, member names and globals;
only the outer function name is omitted. Swift uses the active Xcode toolchain's
SwiftParser/SwiftSyntax modules, requires a lossless parse and validates UTF-8 source
ranges. Compiler debug dumps are unsuitable: valid function types can produce
malformed debug output. Shell coverage is `bash -n` and physical size only.
Swift matching conservatively retains declaration names; renamed Swift clones are
not detected. The baseline pins all analyzer files and Swift parser-library hashes.

Syntax matches are advisory candidates, never semantic-equivalence or deletion proof.
The older pipeline's normalized, token-shape and semantic-similarity labels are also
heuristics. Swift complexity and LSP references remain unknown. A size gate does not
prove behavior preservation; use existing behavioral tests and independent review.

Each engineering round should record the problem and a falsifiable hypothesis, run
the cheapest discriminating test, simplify proven duplication, review the whole diff,
and check remaining delivery gaps. Before a release, plant a representative fault in
a disposable copy, require the intended assertion to fail (not merely a build error),
restore the copy, and require the positive control to pass. Record skipped or masked
checks as inconclusive. Report production, test and tooling costs separately.

Run the analyzer with `--root REPO --policy POLICY --baseline BASELINE --report REPORT`.
Use Python 3.12, an owned temporary `TMPDIR`, the host's resource admission wrapper,
and a bounded controller. Swift checks additionally need full Xcode with the shipped
host parser libraries. Tests live in `tests/test_quality.py`; the Swift integration
fixtures require that toolchain and never silently skip it.

Consumers pin the analyzer revision and SHA-256 of all three executable source files:
`run_quality.py`, `scripts/extract-functions-ast-py.py`, and `scripts/quality-swift.swift`.
The small consumer adapter verifies these bytes and executes Python in isolated mode.
Its fresh temporary receipt must report a nonempty successful analysis. Install the
three files under `~/.local/share/qcode-quality/REVISION/`, retaining `scripts/`, or set
`QCODE_QUALITY_ENGINE` to that exact pinned skill directory. The adapter performs no
network fetch and refuses a missing or modified engine. CI checks out the immutable
revision separately. Analyzer code never ships in either product's runtime package.
