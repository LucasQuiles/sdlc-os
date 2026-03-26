---
name: sdlc-feature-sweep
description: "Codebase-wide neglected-feature sweep. Finder wave discovers incomplete/forgotten/unwired work and updates docs/sdlc/feature-matrix.md; Finisher wave triages findings and writes completion specs for 50%+ complete items."
---

# SDLC Feature Sweep

The feature sweep runs in two waves:

- Finder wave (Scout): discover neglected feature work
- Finisher wave (Synthesize): triage and closure recommendations

This skill operates across the full codebase and persists results in `docs/sdlc/feature-matrix.md`.

## Modes

| Mode | Behavior |
|------|----------|
| `finder` | Run discovery only, append/update matrix rows |
| `finisher` | Triage unresolved findings only |
| `full` (default) | Finder then Finisher in sequence |

## Finder Wave

1. Ensure `docs/sdlc/feature-matrix.md` exists. Create from template if missing.
2. Dispatch `feature-finder`.
3. Require item-level rows with evidence-backed fields.
4. Auto-mark old findings `RESOLVED` only when signal no longer exists.

Dispatch template:

```yaml
Agent tool:
  subagent_type: sdlc-os:feature-finder
  mode: auto
  name: "feature-finder"
  description: "Feature archaeology sweep (code + structure + git + docs)"
  prompt: |
    Run the Feature Finder process and update docs/sdlc/feature-matrix.md.
    Record only evidence-backed findings.
```

## Finisher Wave

1. Read unresolved findings (`DISCOVERED`/`TRIAGED`).
2. Dispatch `feature-finisher`.
3. Update each finding with `Type`, `Effort`, `Recommendation`, `Dependencies`, and `Notes`.
4. Enforce 50% action threshold: `Completion % >= 50` must include a concrete completion spec.

Dispatch template:

```yaml
Agent tool:
  subagent_type: sdlc-os:feature-finisher
  mode: auto
  name: "feature-finisher"
  description: "Feature closure triage and completion specs"
  prompt: |
    Triage unresolved feature-matrix findings and update docs/sdlc/feature-matrix.md.
    For Completion % >= 50, include concrete completion specs in Notes.
```

## Matrix Lifecycle

Status flow:

`DISCOVERED -> TRIAGED -> RESOLVED | DEFERRED | WONT_FIX`

Rules:

- Matrix is committed and persists across sessions.
- Findings are item-level, not feature-summary-only.
- Repeated sightings update `Last Seen`; do not duplicate rows.
- If a row stays unresolved for 3+ sessions, annotate `Notes` with `STALE_REVIEW_REQUIRED`.

## Integration Points

- Scout phase: run Finder wave alongside investigator, convention-scanner, and gap-analyst.
- Synthesize phase: run Finisher wave alongside reviewer, gap-analyst finisher, and normalizer final pass.
- Command entry: `/feature-sweep` for on-demand execution.

## Known Risk (Current Hook Layer)

Bead status guard has an absolute-path normalization edge case on symlinked path forms (`/var/...` vs `/private/var/...`). This is a separate infrastructure fix and does not block feature-sweep rollout, but should be tracked as system debt.
