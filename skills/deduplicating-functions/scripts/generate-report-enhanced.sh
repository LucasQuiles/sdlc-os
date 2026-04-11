#!/usr/bin/env bash
# ABOUTME: Enhanced report generator — produces markdown report from multi-signal merged results
# Shows which detection strategies triggered for each duplicate, clone type classification,
# and defense-in-depth scoring evidence.

set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") <merged-results.json> [output-file]

Generate enhanced markdown report from multi-signal merged duplicate results.

ARGUMENTS:
    merged-results.json   Output from merge-signals.py (with --include-summary)
    output-file           Output markdown file (default: duplicates-report.md)

EXAMPLE:
    $(basename "$0") ./merge/merged-results.json ./duplicates-report.md
EOF
    exit 0
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
fi

if [[ -z "${1:-}" ]]; then
    echo "Error: merged results file required" >&2
    usage
fi

MERGED="$1"
OUTPUT="${2:-duplicates-report.md}"

if [[ ! -f "$MERGED" ]]; then
    echo "Error: file not found: $MERGED" >&2
    exit 1
fi

# Check if the input has summary wrapper or is raw array
HAS_SUMMARY=$(jq 'has("summary")' "$MERGED" 2>/dev/null || echo "false")

if [[ "$HAS_SUMMARY" == "true" ]]; then
    PAIRS_EXPR=".pairs"
    SUMMARY_EXPR=".summary"
else
    PAIRS_EXPR="."
    SUMMARY_EXPR="null"
fi

{
    echo "# Duplicate Functions Report"
    echo ""
    echo "_Multi-Signal Detection with Defense in Depth_"
    echo ""
    echo "Generated: $(date '+%Y-%m-%d %H:%M')"
    echo ""

    # Summary section
    if [[ "$HAS_SUMMARY" == "true" ]]; then
        jq -r '
            .summary |
            "## Summary\n\n" +
            "| Metric | Value |\n" +
            "|--------|-------|\n" +
            "| Total duplicate pairs | \(.total_pairs) |\n" +
            "| HIGH confidence | \(.by_confidence.HIGH // 0) |\n" +
            "| MEDIUM confidence | \(.by_confidence.MEDIUM // 0) |\n" +
            "| LOW confidence | \(.by_confidence.LOW // 0) |\n" +
            "| Multi-signal pairs (2+) | \(.multi_signal_pairs) |\n" +
            "| Defense depth pairs (3+) | \(.defense_depth_pairs) |\n" +
            "| Detection strategies used | \(.strategies_used | join(", ")) |\n"
        ' "$MERGED"
    fi

    echo ""
    echo "### Clone Type Distribution"
    echo ""
    if [[ "$HAS_SUMMARY" == "true" ]]; then
        jq -r '
            .summary.by_clone_type | to_entries | sort_by(-.value) |
            "| Clone Type | Count |\n|-----------|-------|\n" +
            (map("| \(.key) | \(.value) |") | join("\n"))
        ' "$MERGED"
    fi

    echo ""
    echo "### Action Summary"
    echo ""
    if [[ "$HAS_SUMMARY" == "true" ]]; then
        jq -r '
            .summary.by_action | to_entries | sort_by(-.value) |
            "| Action | Count |\n|--------|-------|\n" +
            (map("| \(.key) | \(.value) |") | join("\n"))
        ' "$MERGED"
    fi

    echo ""
    echo "---"
    echo ""

    # HIGH confidence section
    echo "## HIGH Confidence Duplicates"
    echo ""
    echo "> These pairs were flagged by multiple independent detection strategies."
    echo "> Consolidate them — the evidence is strong."
    echo ""

    jq -r "$PAIRS_EXPR"' |
        map(select(.confidence == "HIGH")) |
        if length == 0 then
            "_No HIGH confidence duplicates found._\n"
        else
            map(
                "### \(.func_a.name) \u2194 \(.func_b.name)\n\n" +
                "| | Function A | Function B |\n" +
                "|---|-----------|------------|\n" +
                "| **Name** | `\(.func_a.name)` | `\(.func_b.name)` |\n" +
                "| **File** | `\(.func_a.file):\(.func_a.line)` | `\(.func_b.file):\(.func_b.line)` |\n" +
                "\n" +
                "**Clone Type:** \(.clone_type)\n\n" +
                "**Composite Score:** \(.composite_score) from \(.num_strategies) strategies\n\n" +
                "**Detection Signals:**\n\n" +
                (.strategies | to_entries | map("- \(.key): \(.value)") | join("\n")) +
                "\n\n" +
                "**Recommendation:** \(.recommendation.action) (\(.recommendation.urgency)) — \(.recommendation.reason)\n\n" +
                "---\n"
            ) | join("\n")
        end
    ' "$MERGED"

    echo ""

    # MEDIUM confidence section
    echo "## MEDIUM Confidence Duplicates"
    echo ""
    echo "> These pairs show moderate duplicate signals. Investigate before consolidating."
    echo ""

    jq -r "$PAIRS_EXPR"' |
        map(select(.confidence == "MEDIUM")) |
        if length == 0 then
            "_No MEDIUM confidence duplicates found._\n"
        else
            map(
                "### \(.func_a.name) \u2194 \(.func_b.name)\n\n" +
                "- **A:** `\(.func_a.name)` in `\(.func_a.file):\(.func_a.line)`\n" +
                "- **B:** `\(.func_b.name)` in `\(.func_b.file):\(.func_b.line)`\n" +
                "- **Score:** \(.composite_score) from \(.num_strategies) strategy(ies)\n" +
                "- **Clone Type:** \(.clone_type)\n" +
                "- **Signals:** " + (.strategies | to_entries | map("\(.key)=\(.value)") | join(", ")) + "\n" +
                "- **Action:** \(.recommendation.action) — \(.recommendation.reason)\n\n" +
                "---\n"
            ) | join("\n")
        end
    ' "$MERGED"

    echo ""

    # LOW confidence section
    echo "## LOW Confidence (Review)"
    echo ""
    echo "> Weak signals — review if time permits."
    echo ""

    jq -r "$PAIRS_EXPR"' |
        map(select(.confidence == "LOW")) |
        if length == 0 then
            "_No LOW confidence duplicates found._\n"
        else
            map(
                "- `\(.func_a.name)` (\(.func_a.file):\(.func_a.line)) \u2194 `\(.func_b.name)` (\(.func_b.file):\(.func_b.line)) — score \(.composite_score), signals: " +
                (.strategies | to_entries | map("\(.key)") | join(", "))
            ) | join("\n")
        end
    ' "$MERGED"

    echo ""
    echo ""
    echo "---"
    echo ""
    echo "_Report generated by multi-signal duplicate detection pipeline._"
    echo "_Clone types follow the standard taxonomy: Type 1 (exact), Type 2 (renamed), Type 3 (near-miss), Type 4 (semantic)._"

} > "$OUTPUT"

echo "Report generated: $OUTPUT" >&2

# Quick stats to stderr
if [[ "$HAS_SUMMARY" == "true" ]]; then
    jq -r '
        .summary |
        "  HIGH: \(.by_confidence.HIGH // 0) | MEDIUM: \(.by_confidence.MEDIUM // 0) | LOW: \(.by_confidence.LOW // 0) | Multi-signal: \(.multi_signal_pairs)"
    ' "$MERGED" >&2
fi
