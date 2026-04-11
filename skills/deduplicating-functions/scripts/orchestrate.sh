#!/usr/bin/env bash
# ABOUTME: Master orchestration script — runs the full multi-signal duplicate detection pipeline
# Coordinates extraction, detection, merging, and reporting phases with parallel execution.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] <source-directory>

Run the full multi-signal duplicate function detection pipeline.

OPTIONS:
    -o, --output-dir DIR    Output directory for all artifacts (default: ./dupcheck)
    -t, --types GLOB        File types to scan (default: auto-detect)
    -c, --context N         Lines of context for regex extraction (default: 15)
    --lang LANG             Language hint: ts, py, go, rs, java, auto (default: auto)
    --include-tests         Include test files
    --skip-llm              Skip manual semantic follow-up reminder (classical pipeline only)
    --skip-ast              Skip AST extraction (use regex only)
    --threshold N           Merge-phase HIGH confidence cutoff (default: 0.80)
    --parallel              Run independent phases in parallel (default)
    --sequential            Run phases sequentially (for debugging)
    -v, --verbose           Verbose output
    -h, --help              Show this help

PHASES:
    Phase 0: Extract function catalog (regex + AST; optional manual LSP enrichment outside the runner)
    Phase 1: Run all classical detection strategies in parallel
    Phase 2: Merge signals and score
    Phase 3: Generate report

EXAMPLES:
    $(basename "$0") src/
    $(basename "$0") -o ./analysis --lang py src/
    $(basename "$0") --skip-llm --verbose packages/
    $(basename "$0") --lang ts -t "*.ts,*.tsx" src/ -o ./ts-dupes
EOF
    exit 0
}

# Resolve Python interpreter: PYTHON env var > python3 on PATH
# This avoids hardcoding a path while letting users override if needed.
PYTHON="${PYTHON:-python3}"

# Defaults
OUTPUT_DIR="./dupcheck"
FILE_TYPES=""
CONTEXT_LINES=15
LANG="auto"
INCLUDE_TESTS=false
SKIP_LLM=false
SKIP_AST=false
THRESHOLD=0.80
PARALLEL=true
VERBOSE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        -t|--types) FILE_TYPES="$2"; shift 2 ;;
        -c|--context) CONTEXT_LINES="$2"; shift 2 ;;
        --lang) LANG="$2"; shift 2 ;;
        --include-tests) INCLUDE_TESTS=true; shift ;;
        --skip-llm) SKIP_LLM=true; shift ;;
        --skip-ast) SKIP_AST=true; shift ;;
        --threshold) THRESHOLD="$2"; shift 2 ;;
        --parallel) PARALLEL=true; shift ;;
        --sequential) PARALLEL=false; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -h|--help) usage ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) SRC_DIR="$1"; shift ;;
    esac
done

if [[ -z "${SRC_DIR:-}" ]]; then
    echo "Error: source directory required" >&2
    usage
fi

if [[ ! -d "$SRC_DIR" ]]; then
    echo "Error: directory not found: $SRC_DIR" >&2
    exit 1
fi

# Resolve absolute paths
SRC_DIR="$(cd "$SRC_DIR" && pwd)"
mkdir -p "$OUTPUT_DIR"/{extract,detect,merge}
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

log() {
    echo "[$(date '+%H:%M:%S')] $*" >&2
}

vlog() {
    if [[ "$VERBOSE" == "true" ]]; then
        log "$@"
    fi
}

# Auto-detect language from file extensions
detect_language() {
    local dir="$1"
    local counts=""

    counts=$(
        find "$dir" -type f \( \
            -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
            -o -name "*.py" \
            -o -name "*.go" \
            -o -name "*.rs" \
            -o -name "*.java" -o -name "*.kt" \
        \) 2>/dev/null | \
        sed 's/.*\.//' | sort | uniq -c | sort -rn | head -5
    )

    if [[ -z "$counts" ]]; then
        echo "ts"  # default
        return
    fi

    # Return all detected languages
    local langs=()
    while read -r count ext; do
        case "$ext" in
            ts|tsx|js|jsx) [[ ! " ${langs[*]:-} " =~ " ts " ]] && langs+=("ts") ;;
            py) langs+=("py") ;;
            go) langs+=("go") ;;
            rs) langs+=("rs") ;;
            java|kt) langs+=("java") ;;
        esac
    done <<< "$counts"

    echo "${langs[*]:-ts}"
}

# Determine test exclusion flags
test_flags() {
    if [[ "$INCLUDE_TESTS" == "true" ]]; then
        echo "--include-tests"
    fi
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 0: EXTRACTION
# ═══════════════════════════════════════════════════════════════════

phase_extract() {
    log "═══ Phase 0: EXTRACT ═══"

    local detected_langs
    if [[ "$LANG" == "auto" ]]; then
        detected_langs=$(detect_language "$SRC_DIR")
        log "Auto-detected languages: $detected_langs"
    else
        detected_langs="$LANG"
    fi

    local pids=()

    # 0a. Regex extraction (always runs, fast)
    log "  [0a] Regex extraction..."
    local regex_args=(-o "$OUTPUT_DIR/extract/catalog-regex.json" -c "$CONTEXT_LINES")
    if [[ -n "$FILE_TYPES" ]]; then
        regex_args+=(-t "$FILE_TYPES")
    fi
    if [[ "$INCLUDE_TESTS" == "true" ]]; then
        regex_args+=(--include-tests)
    fi

    if [[ -x "$SCRIPT_DIR/extract-functions-regex.sh" ]]; then
        "$SCRIPT_DIR/extract-functions-regex.sh" "${regex_args[@]}" "$SRC_DIR" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    else
        vlog "  Warning: extract-functions-regex.sh not found"
    fi

    # 0b. AST extraction (if not skipped)
    if [[ "$SKIP_AST" != "true" ]]; then
        for lang in $detected_langs; do
            case "$lang" in
                py)
                    if [[ -x "$SCRIPT_DIR/extract-functions-ast-py.py" ]]; then
                        log "  [0b] Python AST extraction..."
                        local py_args=(-o "$OUTPUT_DIR/extract/catalog-ast-py.json")
                        if [[ -n "$FILE_TYPES" ]]; then
                            py_args+=(-t "$FILE_TYPES")
                        fi
                        if [[ "$INCLUDE_TESTS" == "true" ]]; then
                            py_args+=(--include-tests)
                        fi
                        "$PYTHON" "$SCRIPT_DIR/extract-functions-ast-py.py" "${py_args[@]}" "$SRC_DIR" 2>>"$OUTPUT_DIR/pipeline.log" &
                        pids+=($!)
                    fi
                    ;;
                ts)
                    if [[ -f "$SCRIPT_DIR/extract-functions-ast-ts.mjs" ]]; then
                        log "  [0b] TypeScript AST extraction..."
                        local ts_args=(--output "$OUTPUT_DIR/extract/catalog-ast-ts.json")
                        if [[ -n "$FILE_TYPES" ]]; then
                            ts_args+=(--types "$FILE_TYPES")
                        fi
                        if [[ "$INCLUDE_TESTS" == "true" ]]; then
                            ts_args+=(--include-tests)
                        fi
                        node "$SCRIPT_DIR/extract-functions-ast-ts.mjs" "${ts_args[@]}" "$SRC_DIR" 2>>"$OUTPUT_DIR/pipeline.log" &
                        pids+=($!)
                    fi
                    ;;
            esac
        done
    fi

    # Wait for all extraction jobs
    local failures=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            ((failures++))
            vlog "  Warning: extraction job $pid failed"
        fi
    done

    # Merge all catalogs into unified catalog
    log "  Merging extraction results..."
    merge_catalogs "$OUTPUT_DIR/extract" "$OUTPUT_DIR/extract/catalog-unified.json"

    local count
    count=$(jq 'length' "$OUTPUT_DIR/extract/catalog-unified.json" 2>/dev/null || echo 0)
    log "  Extracted $count function definitions ($failures extraction failures)"
}

merge_catalogs() {
    local dir="$1"
    local output="$2"

    # Merge all catalog-*.json files, deduplicating by file+name+line
    local files=()
    for f in "$dir"/catalog-*.json; do
        [[ -f "$f" ]] && files+=("$f")
    done

    if [[ ${#files[@]} -eq 0 ]]; then
        echo "[]" > "$output"
        return
    fi

    if [[ ${#files[@]} -eq 1 ]]; then
        cp "${files[0]}" "$output"
        return
    fi

    # Merge with deduplication — prefer AST entries (richer data) over regex
    jq -s '
        flatten |
        group_by(.file + ":" + .name + ":" + (.line | tostring)) |
        map(
            # Sort by richness: entries with ast_fingerprint first
            sort_by(if .ast_fingerprint then 0 else 1 end) |
            .[0] as $base |
            reduce .[] as $entry ($base;
                # Merge fields from other entries if base is missing them
                . + (
                    [$entry | to_entries[] | select(.value != null and .value != "")] |
                    from_entries |
                    with_entries(select(.key as $k | ($base[$k] == null or $base[$k] == "")))
                )
            )
        ) |
        sort_by(.file, .line)
    ' "${files[@]}" > "$output"
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: DETECTION
# ═══════════════════════════════════════════════════════════════════

phase_detect() {
    log "═══ Phase 1: DETECT ═══"

    local catalog="$OUTPUT_DIR/extract/catalog-unified.json"
    if [[ ! -f "$catalog" ]] || [[ "$(jq 'length' "$catalog")" == "0" ]]; then
        log "  No functions in catalog, skipping detection"
        return
    fi

    local pids=()

    # 1a. Fuzzy name matching
    if [[ -x "$SCRIPT_DIR/detect-fuzzy-names.py" ]]; then
        log "  [1a] Fuzzy name matching..."
        "$PYTHON" "$SCRIPT_DIR/detect-fuzzy-names.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/fuzzy-name-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1b. Signature matching
    if [[ -x "$SCRIPT_DIR/detect-signature-match.py" ]]; then
        log "  [1b] Signature matching..."
        "$PYTHON" "$SCRIPT_DIR/detect-signature-match.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/signature-match-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1c. Token clone detection
    if [[ -x "$SCRIPT_DIR/detect-token-clones.py" ]]; then
        log "  [1c] Token clone detection..."
        "$PYTHON" "$SCRIPT_DIR/detect-token-clones.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/token-clone-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1d. AST structural similarity
    if [[ -x "$SCRIPT_DIR/detect-ast-similarity.py" ]]; then
        log "  [1d] AST structural similarity..."
        "$PYTHON" "$SCRIPT_DIR/detect-ast-similarity.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/ast-similarity-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1e. Metric similarity
    if [[ -x "$SCRIPT_DIR/detect-metric-similarity.py" ]]; then
        log "  [1e] Metric similarity..."
        "$PYTHON" "$SCRIPT_DIR/detect-metric-similarity.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/metric-similarity-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1f. TF-IDF inverted index
    if [[ -x "$SCRIPT_DIR/detect-tfidf-index.py" ]]; then
        log "  [1f] TF-IDF inverted index..."
        "$PYTHON" "$SCRIPT_DIR/detect-tfidf-index.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/tfidf-index-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1g. Bag-of-AST-nodes cosine
    if [[ -x "$SCRIPT_DIR/detect-bag-of-ast.py" ]]; then
        log "  [1g] Bag-of-AST-nodes cosine..."
        "$PYTHON" "$SCRIPT_DIR/detect-bag-of-ast.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/bag-of-ast-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1h. Winnowing fingerprints
    if [[ -x "$SCRIPT_DIR/detect-winnowing.py" ]]; then
        log "  [1h] Winnowing fingerprints..."
        "$PYTHON" "$SCRIPT_DIR/detect-winnowing.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/winnowing-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1i. LSH AST features
    if [[ -x "$SCRIPT_DIR/detect-lsh-ast.py" ]]; then
        log "  [1i] LSH AST features..."
        "$PYTHON" "$SCRIPT_DIR/detect-lsh-ast.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/lsh-ast-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1j. PDG semantic detection
    if [[ -x "$SCRIPT_DIR/detect-pdg-semantic.py" ]]; then
        log "  [1j] PDG semantic detection..."
        "$PYTHON" "$SCRIPT_DIR/detect-pdg-semantic.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/pdg-semantic-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1k. Code embedding similarity
    if [[ -x "$SCRIPT_DIR/detect-code-embedding.py" ]]; then
        log "  [1k] Code embedding similarity..."
        "$PYTHON" "$SCRIPT_DIR/detect-code-embedding.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/code-embedding-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # Wait for all classical detectors
    local failures=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            ((failures++))
            vlog "  Warning: detection job $pid failed"
        fi
    done

    # Count results per strategy
    for f in "$OUTPUT_DIR"/detect/*-results.json; do
        [[ -f "$f" ]] || continue
        local name count
        name=$(basename "$f" -results.json)
        count=$(jq 'length' "$f" 2>/dev/null || echo 0)
        log "  $name: $count candidate pairs"
    done

    log "  Classical detection complete ($failures failures)"

    # 1l. Manual semantic follow-up (optional, expensive)
    if [[ "$SKIP_LLM" != "true" ]]; then
        log "  [1l] Manual semantic follow-up is outside orchestrate.sh"
        log "       1. Categorize with scripts/categorize-prompt.md"
        log "       2. Split categories with scripts/prepare-category-analysis.sh"
        log "       3. Review each category with scripts/find-duplicates-prompt.md"
        log "       Save results to $OUTPUT_DIR/detect/duplicates/*.json"
    fi
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: MERGE
# ═══════════════════════════════════════════════════════════════════

phase_merge() {
    log "═══ Phase 2: MERGE ═══"

    "$PYTHON" "$SCRIPT_DIR/merge-signals.py" \
        "$OUTPUT_DIR/detect" \
        -o "$OUTPUT_DIR/merge/merged-results.json" \
        --include-summary \
        --high-threshold "$THRESHOLD"

    local total high medium low
    total=$(jq '.summary.total_pairs' "$OUTPUT_DIR/merge/merged-results.json" 2>/dev/null || echo 0)
    high=$(jq '.summary.by_confidence.HIGH // 0' "$OUTPUT_DIR/merge/merged-results.json" 2>/dev/null || echo 0)
    medium=$(jq '.summary.by_confidence.MEDIUM // 0' "$OUTPUT_DIR/merge/merged-results.json" 2>/dev/null || echo 0)
    low=$(jq '.summary.by_confidence.LOW // 0' "$OUTPUT_DIR/merge/merged-results.json" 2>/dev/null || echo 0)

    log "  $total pairs: $high HIGH, $medium MEDIUM, $low LOW"
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: REPORT
# ═══════════════════════════════════════════════════════════════════

phase_report() {
    log "═══ Phase 3: REPORT ═══"

    local merged="$OUTPUT_DIR/merge/merged-results.json"
    local report="$OUTPUT_DIR/duplicates-report.md"

    if [[ -x "$SCRIPT_DIR/generate-report-enhanced.sh" ]]; then
        "$SCRIPT_DIR/generate-report-enhanced.sh" "$merged" "$report"
    elif [[ -x "$SCRIPT_DIR/generate-report.sh" ]]; then
        # Fallback to original report generator
        # Need to convert merged format to original format first
        log "  Using legacy report generator"
        mkdir -p "$OUTPUT_DIR/detect/duplicates"
        "$SCRIPT_DIR/generate-report.sh" "$OUTPUT_DIR/detect/duplicates" "$report"
    else
        log "  Warning: No report generator found"
        return
    fi

    log "  Report: $report"
}

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

main() {
    log "Multi-Signal Duplicate Function Detection"
    log "Source: $SRC_DIR"
    log "Output: $OUTPUT_DIR"
    log ""

    phase_extract
    echo "" >&2
    phase_detect
    echo "" >&2
    phase_merge
    echo "" >&2
    phase_report

    log ""
    log "═══ COMPLETE ═══"
    log "Results: $OUTPUT_DIR/merge/merged-results.json"
    log "Report:  $OUTPUT_DIR/duplicates-report.md"
    log "Catalog: $OUTPUT_DIR/extract/catalog-unified.json"
}

main
