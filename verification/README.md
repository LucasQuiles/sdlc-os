# SDLC-OS Verification

This directory contains the committed Release 1A verification authorities. Generated evidence is written under the root-ignored `.verification-results/` directory; the committed files in `verification/` are never ignored.

## Prerequisites

- Python 3.12
- Node.js 20.20.2 and dependencies installed from `colony/package-lock.json`
- Bash, Git, npm, jq, Perl, `lsof`, and every tool named by the selected manifest rows
- Claude CLI on macOS for the strict plugin-validation rows
- A clean, immutable Git candidate for a release run
- macOS and Linux execution for every row applicable to both platforms

The runner constructs a minimal child environment. It owns `PATH`, `HOME`, `TMPDIR`, `LC_ALL=C`, `LANG=C`, and `TZ=UTC`. A row may use only reviewed non-secret keys and the substitutions `${REPO_ROOT}`, `${HOST_HOME}`, `${CHECK_HOME}`, and `${CHECK_TMPDIR}`. The exact child environment remains in memory; receipts and `environment.json` contain stable tokens and hashes rather than ambient or declared raw values.

## Prepare an Immutable Candidate

The candidate provider supplies all three assertions. Do not infer an expected digest from the received bundle.

```bash
set -euo pipefail
EXPECTED_CANDIDATE="<full-candidate-sha>"
EXPECTED_BUNDLE_SHA256="<provider-supplied-bundle-sha256>"
BUNDLE="<absolute-path-to-candidate.bundle>"
WORK_ROOT="$(mktemp -d /tmp/sdlc-os-review.XXXXXX)"
ACTUAL_BUNDLE_SHA256="$(python3.12 -c 'import hashlib,sys; print(hashlib.file_digest(open(sys.argv[1], "rb"), "sha256").hexdigest())' "$BUNDLE")"
test "$ACTUAL_BUNDLE_SHA256" = "$EXPECTED_BUNDLE_SHA256"
git clone --no-hardlinks "$BUNDLE" "$WORK_ROOT/repository"
cd "$WORK_ROOT/repository"
git bundle verify "$BUNDLE"
git switch --detach "$EXPECTED_CANDIDATE"
test "$(git rev-parse HEAD)" = "$EXPECTED_CANDIDATE"
test -z "$(git status --porcelain --untracked-files=all)"
for tool in bash python3.12 node npm git jq perl lsof; do command -v "$tool" >/dev/null; done
```

On macOS, resolve the canonical Node installation and the additional validation CLI explicitly:

```bash
set -euo pipefail
NODE20_BIN="$(brew --prefix node@20)/bin"
test "$($NODE20_BIN/node --version)" = "v20.20.2"
command -v claude >/dev/null
command -v lsof >/dev/null
PATH="$NODE20_BIN:$PATH" npm ci --prefix colony
```

On Linux, require the selected host's Node to match the same release:

```bash
set -euo pipefail
test "$(node --version)" = "v20.20.2"
command -v lsof >/dev/null
npm ci --prefix colony
```

## Run Release 1A

From the repository root:

```bash
set -euo pipefail
NODE20_BIN="$(brew --prefix node@20)/bin"
test "$($NODE20_BIN/node --version)" = "v20.20.2"
RUN_ID="$(git rev-parse --short=12 HEAD)-macos-$(date -u +%Y%m%dT%H%M%SZ)-$$"
PATH="$NODE20_BIN:$PATH" \
  python3.12 scripts/run-verification.py \
    --manifest verification/manifest.json \
    --stage 1A \
    --platform macos \
    --run-id "$RUN_ID" \
    --results-dir ".verification-results/$RUN_ID"
```

## Run Release 1A on Linux

Use the same committed candidate and manifest bytes on the authorized Linux x86_64 verification host. `/tmp` must be a readable, writable, and traversable directory for the verification user; the explicit temp base keeps descriptor-held F-01 evidence traversable independently of a login manager's private temp hierarchy.

```bash
set -euo pipefail
test -d /tmp && test -r /tmp && test -w /tmp && test -x /tmp
RUN_ID="$(git rev-parse --short=12 HEAD)-linux-$(date -u +%Y%m%dT%H%M%SZ)-$$"
TMPDIR=/tmp \
  python3.12 scripts/run-verification.py \
    --manifest verification/manifest.json \
    --stage 1A \
    --platform linux \
    --run-id "$RUN_ID" \
    --results-dir ".verification-results/$RUN_ID"
```

Use the immutable-candidate procedure above before execution, and copy the complete protected result tree back without changing modes. A platform, dependency, transfer, or hash failure is `INCONCLUSIVE`, never a macOS-only pass.

The command prints `RUN_SHA256=<digest>` only after `run.json` is durably written, fsynced, atomically admitted, and read back. Validate the printed digest against the retained file before using the result.

A per-check receipt is only partial evidence until the same result directory contains a validated `run.json` whose SHA-256 matches the printed `RUN_SHA256`. If final summary admission fails, the runner returns `70`, prints no digest, and may retain truthful row receipts for diagnosis; those orphan receipts cannot authorize any task or release verdict.

## Validate a Run Result

Capture the runner's single printed digest without a pipeline, then validate the complete protected result tree against the current candidate and committed authorities:

```bash
set -euo pipefail
RUN_SHA256="<digest-printed-by-the-runner>"
python3.12 scripts/run-verification.py \
  --validate-run-result ".verification-results/$RUN_ID/run.json" \
  --run-sha256 "$RUN_SHA256" \
  --candidate "$EXPECTED_CANDIDATE"
```

The validator prints exactly `RUN_RESULT_VALID` only after the run digest, candidate, manifest, requirement catalog, runner, receipt hashes, file modes, stream/environment/artifact hashes, counts, and aggregate verdict all agree. It does not promote a failing or inconclusive aggregate; it establishes that the retained result is complete and internally bound.

## Exit and Verdict Mapping

| Exit | Meaning |
|---:|---|
| `0` | Every selected required row passed and at least one required row executed. |
| `1` | At least one selected row conclusively failed. |
| `3` | No row failed, but at least one row or required surface was inconclusive or not run. |
| `64` | Invocation, authority schema, platform assertion, selection, or candidate binding is invalid. |
| `70` | The runner could not safely or durably write and validate protected evidence. |

Row verdicts are `PASS`, `FAIL`, `INCONCLUSIVE`, or `NOT_APPLICABLE`; execution states are `RAN`, `NOT_RUN`, or `NOT_APPLICABLE`. A missing count, missing artifact, timeout, survivor, escaped descendant, invalid encoding, output overflow, masked exit, source mutation, dirty clean-source row, or stale candidate binding cannot become `PASS`.

## Authorities and Receipts

- `manifest.json` is `sdlc-os-verification-manifest-v1`. It contains the requirement catalog, executable allowlist, protected ignored paths, and strict argv-only check rows. Unknown fields or future schema versions are rejected.
- `error-catalog.json` is `sdlc-os-error-catalog-v1`. Every stable emitted code has one audience, sanitized template, bounded remediation, evidence-field list, and owning requirement.
- `baseline-inventory.json` is `sdlc-os-baseline-inventory-v1`. Stable A-series, P27, and 1A/1B/1C findings remain visible with owner, due trigger, verdict, disposition, and closure proof.
- `review-state.json` is `sdlc-os-review-state-v1`. It records pre-candidate review history; its Release 1A candidate fields intentionally remain `PENDING`.
- `review-result.schema.json` defines the ignored immutable-candidate review payload.

Each check directory is mode `0700`; stdout, stderr, tokenized-environment evidence, copied artifacts, and `receipt.json` are mode `0600`. Receipts bind the candidate, manifest, requirement catalog, runner, row, executable/tool fingerprints, source state, platform, true process outcome, observations, artifacts, and hashes. Raw untrusted output remains only in protected stream files. Structured receipts contain sanitized/tokenized values and hashes, not ambient secrets or private raw data.

Result directories are unique and non-overwriting. Directory descriptors, no-follow opens, device/inode revalidation, durable temporary siblings, fsync, atomic replacement, and readback prevent path retargeting or partial evidence from authorizing success. Do not delete the only raw evidence tree. Retain Release 1A evidence through the Stage 1 owner checkpoint and for at least 90 days after the final Stage 1 checkpoint.

Every executed check inherits a private runner-owned Unix-socket descriptor. The runner uses at most three bounded canonical `lsof` attempts to identify exact holders after leader exit, accepting only one complete successful inventory and discarding failed-attempt output. It then revalidates the holder's start identity before signaling it. Linux uses `pidfd` signaling when available; macOS repeats lease and start-identity validation immediately before `kill(2)`. Persistent monitor timeout/nonzero exit, malformed inventory, an unobservable runner lease, unreadable holder identity, an observed holder, or incomplete cleanup makes the row `VERIFY_BACKGROUND_PROCESS`/`INCONCLUSIVE`. Malformed or ambiguous successful output is never retried into a pass. This is leak detection for reviewed commands, not a hostile-process sandbox; committed checks must not deliberately close unknown inherited descriptors before daemonizing.

## Command Admission and Source Mutation

The manifest allowlist is fail-closed. Interpreter command strings (`-c`, `--command`, `-e`, and equivalents), `env`, unlisted executables, unlisted script paths, unsafe path segments, and scripts outside their physically resolved roots are rejected before execution. Git is limited to the manifest's read-only subcommands; the Claude CLI is limited to `plugin validate`; the Colony launcher, TypeScript compiler, and Vitest accept only their exact declared argv. Python module mode is limited to `unittest` and `json.tool`. The only admitted Python startup flag is `-S`, exactly once and only before `-m`, so the two unit rows cannot import ambient site packages; duplicate, misplaced, unknown, direct-script, and command-string startup forms are rejected. Bash and Node flags are limited to the declared safe forms.

### Exact Script Allowlist

```text
bash tests/test-sdlc-dispatch-isolation.sh
bash tests/test-sdlc-dispatch.sh
bash tests/test-plugin-root-resolution.sh
bash tests/test-validator-shims.sh
bash tests/test-portable-shell-helpers.sh
bash colony/clone-manager.test.sh
bash tests/test-crossmodel-preflight.sh
bash tests/test-colony-tooling.sh
python3.12 scripts/check-plugin-metadata.py
python3.12 scripts/check-repository-inventory.py
```

Each row snapshots the candidate SHA, tracked worktree and index bytes, untracked files, every ignored path outside the active result directory, and the manifest's protected ignored roots (`artifacts`, `.superpowers`, and `colony/node_modules`) before and after the child. A net change to any of those surfaces is `VERIFY_SOURCE_MUTATION` and makes the row `FAIL`, including changes to already-dirty tracked content, pre-existing `.verification-results/` trees, or ignored files outside the protected roots. Only the active result directory is excluded so the runner can write its own evidence. A clean-source row also fails when its initial source state is dirty.

The direct F-01 row additionally emits the source, decoy, and installed validator SHA-256 values before its pass marker. Its exact regex observation and the runner-owned stdout hash bind those values to the row receipt; only an absent installed plugin may be represented as `NOT_APPLICABLE`.

## Requirement Projection

Row verdicts and requirement closure are separate. A passing row projects a requirement to `PASS` only when that requirement is owned by the selected stage and `closure_in_1a` is true. Passing evidence for an intentionally incomplete 1A requirement projects to `PARTIAL`; requirements owned by a later release project to `LATER_OWNED`; an owned requirement with no row projects to `UNMET`. `PARTIAL`, `LATER_OWNED`, and `UNMET` remain listed in `unmet_or_later_owned_requirements` and cannot be cited as closed Stage 1 work.

The runner validates the committed error catalog in normal execution and review-validation modes. The catalog must match the stable codes emitted by the runner and the Stage 1A command surfaces exactly. Child-specific diagnostics that are not runner codes remain hashed in raw stdout or stderr and are classified by the applicable `VERIFY_*` receipt code; they are not silently promoted into the stable catalog.

## Validate a Review Result

After a distinct read-only reviewer produces a candidate-bound JSON result beneath an ignored result directory:

```bash
set -euo pipefail
python3.12 scripts/run-verification.py \
  --validate-review-result .verification-results/<candidate>-reviews/independent.json \
  --candidate <full-candidate-sha>
```

Validation checks the schema version, exact candidate assertion, manifest/catalog hashes, observed reviewer method, argv and true exits, material source claims with file hashes, findings, limitations, protected evidence hashes, and verdict. Every finding records `finding`, `severity`, `disposition`, `evidence`, `owner`, `due_trigger`, and `closure_proof`; a `PASS` review cannot contain a critical or material unresolved finding. Validation does not modify `HEAD`. A different model label without source-byte inspection and command reproduction is not independent evidence.

## Extending the Manifest

Release 1B and 1C may append new requirement entries and rows. They must not rename or reuse an existing requirement ID, check ID, baseline stable ID, schema version, or receipt path; they must not rewrite prior receipts. A schema change requires a new version, migration/replay tests, and review. Later rows cannot promote a deferred finding by omission: update its inventory disposition only when the named closure proof exists on the exact candidate.
