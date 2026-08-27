# Managed runtime output

`run_pipeline.py --output-dir ROOT` treats `ROOT` as a managed publication root. It never
deletes or rewrites caller-selected content. Each invocation exclusively creates
`ROOT/.inflight/RUN_ID`, writes only below that run directory, and moves a successful run to
`ROOT/runs/RUN_ID`. Only then does it atomically replace `ROOT/latest-complete.json`.

Failed and interrupted runs remain under `.inflight/` and never update the latest pointer.
Cleanup and retention are intentionally separate, owner-authorized operations; this repository
does not ship a recursive cleanup command or recommend `rm -rf` for runtime output.

The small regression baseline is checked in under `tests/fixtures/baseline-corpus/`. Runtime
output is ignored by Git and is not a golden fixture.
