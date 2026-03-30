# Debt Backlog

Persisted remediation queue. Items are added by the `debt-crawler` agent (PROMOTE classification)
and by the Conductor (from gap-analyst Finisher reports on STAGED/DEFERRED migrations).

## Import Rules (Phase 3 Architect)

1. **Relevance gate:** Only import items whose `include_paths` overlap with any primary bead's `Scope` field.
2. **Debt budget:** Max 1-2 companion beads per task. Debt beads cannot displace user-requested work.
3. **Overlap only:** Items in modules not covered by any primary bead's scope wait for a future task.

## Item Lifecycle

PROMOTE -> IMPORTED (Architect picks up) -> RESOLVED (bead merges). Items at RESOLVED for 2+ scans are archived below.

## Active Items

No items yet. First Evolve scan will populate.

## Item Schema Reference

```markdown
### DEBT-{NNN}

- **debt_id:** DEBT-{NNN}
- **title:** {description}
- **type:** TRUE_DUP | ADOPTION | SUPPRESSION | ZOMBIE
- **source_scan:** Evolve Cycle {N}, {date}
- **include_paths:** [file list]
- **canonical_target:** {path:export}
- **confidence:** 0.0-1.0
- **value_score:** {DVS 0-100}
- **evidence_channels:** [channel list]
- **estimated_scope:** {file count}, {caller count}
- **status:** PROMOTE | IMPORTED | RESOLVED
- **imported_by_bead:** -
- **resolved_by_bead:** -
```

## Archived Items

(Items at RESOLVED for 2+ scans move here)
