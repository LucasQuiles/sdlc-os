# Debt Scan Report

Owned by the `debt-crawler` agent. Updated during Evolve bead types #18 (Adoption Scan) and #19 (Duplicate Scan).

## Scan History

No scans completed yet. First scan will establish baselines.

## Schema Reference

Each scan appends a section with this structure:

### Adoption Metrics
| Canonical | Violations | Previous | Trend | Delta |
|---|---|---|---|---|

### Duplicate Metrics
| Classification | Count | Previous | Trend |
|---|---|---|---|

### Ratchet Status
- TRUE_DUP (PROMOTE) count: {N}
- Previous baseline: {N}
- Ratchet result: PASS | FAIL

### Findings Detail
(full evidence per finding)
