# Orchestration Receipt Enforcement Map — 2026-07-21

## Scope and authority

This map records the active SDLC-OS cross-model enforcement added on branch
`codex/orchestration-receipts-20260721`. It depends on tmup dispatch-receipt
support at or after commit `8ad8863e920d9250b9b6ab18980d99ed6f899d43`.
The historical 2026-03-28 design remains rationale only; the active skill,
supervisor, FFT, and health gate below are normative.

q-pi does not host SDLC-OS or tmup. These changes deploy to the maclab Claude
Code plugin surface, not to q-pi. q-pi's applicable continuation and resource
controls are tracked separately in the mesh deployment map.

## Required-role control flow

```text
AQS runs while bead remains proven
  -> captures machine-readable runtime receipt JSON plus SHA-256
  -> AQS exit block binds requested/observed identity to that source artifact
FFT-14 selects policy before checking availability
  -> SKIP: explicit not_applicable gate
  -> FULL/TARGETED: create exact required task set
tmup_task_batch records role/model/evidence policy
  -> tmup_dispatch returns atomic launch receipt
  -> tmup_attempt_attest persists live model observation and source in the receipt
worker writes unique artifact and reports ready for review
  -> supervisor validates path and checksum
  -> tmup_evidence_add + tmup_evidence_review(disposition=approved)
  -> supervisor-owned tmup_complete
  -> tmup_status(verbose=true) returns terminal receipt
crossmodel-health.sh validates the complete journal
  -> satisfied: Conductor may transition proven -> hardened
  -> running/blocked/inconclusive: retain proven and backpressure to L3
```

## Enforcement coverage

| Requirement | Active authority | Deterministic evidence |
|---|---|---|
| Required role, selector, requested/observed model, observation source, fallback, attempt, terminal status | `agents/crossmodel-supervisor.md`, tmup terminal receipt | `scripts/crossmodel-health.sh` receipt validation |
| Unavailable/skipped/inconclusive distinct from complete | `skills/sdlc-crossmodel/SKILL.md`, `skills/sdlc-loop/SKILL.md` | blocked-state negative tests |
| Attempt ledger wired through dispatch and completion | tmup dependency plus supervisor lifecycle | live `tools/list` preflight and matching attempt IDs |
| Evidence-required completion needs approved artifact | supervisor collect flow | evidence ID, attempt ID, confined real path, on-disk SHA-256, disposition binding |
| Cross-model gate rejects same observed model | FFT-14 plus task policy | normalized reference/worker comparison tests |
| Continuation dispatch must be acknowledged | loop invariant | pending and inconclusive remain non-advancing |
| Stale claimed work without launch receipt is not live proof | tmup reconciliation dependency | receipt-required task policy |
| Static model claims replaced by live selector/observation data | active skills, supervisor, AQS artifact template | stale-claim scan and runtime-receipt fields |

FULL requires four distinct Stage A workers for functionality, security,
usability, and resilience plus one distinct Stage B independent reviewer.
TARGETED requires the selected Stage A domain plus a distinct Stage B reviewer.
Attempt IDs, agent IDs, artifact names, canonical artifact paths, and physical
file identities must be unique. Symlinks, path aliases, and hard links cannot
satisfy multiple required roles.

## Compatibility and failure semantics

`crossmodel-preflight.sh` performs a bounded live MCP initialize/tools-list
probe and validates the exact receipt/evidence/task-policy schema. The default
`model: auto` path records that catalog validation is not applicable before
launch and still requires a live observed-model attestation afterward. An
explicit model on this MCP path is rejected because it cannot supply tmup's
required per-dispatch live-catalog receipt.

Exit codes from `crossmodel-health.sh` are semantic:

- `0`: required review satisfied, or explicit policy SKIP/not-applicable.
- `1`: required review pending or blocked; parent must not advance.
- `2`: journal, schema, or tooling is unavailable/malformed; result is
  inconclusive.

Same-model-only fallback, missing or checksum-mismatched on-disk artifacts, challenged/rejected evidence,
duplicate worker or attempt identity, wrong domain/stage shape, masked output,
and unknown model observations cannot satisfy the gate.

## Verification

Run from the repository root:

```bash
bash -n scripts/crossmodel-preflight.sh scripts/crossmodel-health.sh \
  tests/test-crossmodel-preflight.sh tests/test-crossmodel-health.sh
bash tests/test-crossmodel-preflight.sh
bash tests/test-crossmodel-health.sh
python3.12 scripts/check-plugin-metadata.py --root .
python3.12 scripts/check-repository-inventory.py --root .
```

Publication, installed-plugin parity, and any later release receipt are
separate evidence. A pushed branch does not by itself prove that maclab's
active plugin checkout has been advanced to it.
