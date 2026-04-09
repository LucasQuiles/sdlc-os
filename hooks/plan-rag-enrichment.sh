#!/bin/bash
# PostToolUse hook: Enforce RAG enrichment evidence in plan files.
#
# Checks Write/Edit on plan-path files for:
#   1. "## RAG Context" or "### RAG Context" heading with substantive evidence
#   2. "RAG_DEGRADED:<reason>" marker (explicit exception)
#
# Substantive evidence requires (within the RAG Context section):
#   - At least one query intent marker (Query, intent, searched for)
#   - At least one retrieval source marker (index, namespace, known index name)
#   - At least one approved index mention:
#       oneplatform-codebase-v2, claude, codex, bes-notes, dev-docs
#   - At least one result marker (hit, score, path, takeaway, finding)
#   - At least 2 query blocks (unless RAG_DEGRADED is present)
#
# Output: Structured JSON for PostToolUse context injection.
# Always exits 0. Set PLAN_RAG_GATE_STRICT=1 to emit block decision.
#
# Plan paths checked:
#   - ~/.claude/plans/*.md
#   - **/docs/plans/*.md
#   - **/Docs/plans/*.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

INPUT=$(read_hook_stdin) || exit 0

FILE_PATH=$(read_hook_file_path "$INPUT")

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Only check plan files
IS_PLAN=""
case "$FILE_PATH" in
    */.claude/plans/*.md)  IS_PLAN="1" ;;
    */docs/plans/*.md)     IS_PLAN="1" ;;
    */Docs/plans/*.md)     IS_PLAN="1" ;;
esac

if [ -z "$IS_PLAN" ]; then
    exit 0
fi

# Check file content for RAG evidence
if [ ! -f "$FILE_PATH" ]; then
    # File doesn't exist yet (pre-write); skip this check
    exit 0
fi

HAS_RAG_HEADING=""
HAS_RAG_DEGRADED=""

if grep -qE '^#{2,3}\s+RAG Context' "$FILE_PATH" 2>/dev/null; then
    HAS_RAG_HEADING="1"
fi

if grep -qE 'RAG_DEGRADED:' "$FILE_PATH" 2>/dev/null; then
    HAS_RAG_DEGRADED="1"
fi

# RAG_DEGRADED is an explicit exception — pass without further checks
if [ -n "$HAS_RAG_DEGRADED" ]; then
    exit 0
fi

# --- Substantive evidence validation ---
# If heading is present, extract the RAG section body and check for required markers.
# If heading is absent, fail with "missing section" message.

FAILURE_REASON=""

if [ -z "$HAS_RAG_HEADING" ]; then
    FAILURE_REASON="missing_section"
else
    # Extract RAG Context section body: from heading to next ##/### heading or EOF.
    # Stops at any heading of level 2+ that is NOT the RAG Context heading itself.
    RAG_BODY=$(awk '
        /^#{2,3}[[:space:]]+RAG Context/ { found=1; next }
        found && /^#{2,3}[[:space:]]/ { exit }
        found { print }
    ' "$FILE_PATH" 2>/dev/null)

    # Check for placeholder-only content
    RAG_BODY_TRIMMED=$(echo "$RAG_BODY" | sed '/^[[:space:]]*$/d')
    if [ -z "$RAG_BODY_TRIMMED" ]; then
        FAILURE_REASON="empty_section"
    else
        # Check required evidence markers (case-insensitive)
        HAS_QUERY=""
        HAS_SOURCE=""
        HAS_RESULT=""
        HAS_APPROVED_INDEX=""

        if echo "$RAG_BODY" | grep -qiE '(query|intent|searched\s+for)'; then
            HAS_QUERY="1"
        fi
        if echo "$RAG_BODY" | grep -qiE '(index|namespace|pinecone)'; then
            HAS_SOURCE="1"
        fi
        if echo "$RAG_BODY" | grep -qiE '(oneplatform-codebase-v2|claude|codex|bes-notes|dev-docs)'; then
            HAS_APPROVED_INDEX="1"
        fi
        if echo "$RAG_BODY" | grep -qiE '(hit|score|path|takeaway|finding|result|top\s+\d)'; then
            HAS_RESULT="1"
        fi

        # Build list of missing markers
        MISSING=""
        if [ -z "$HAS_QUERY" ]; then MISSING="${MISSING}query intent, "; fi
        if [ -z "$HAS_SOURCE" ]; then MISSING="${MISSING}retrieval source (index/namespace), "; fi
        if [ -z "$HAS_APPROVED_INDEX" ]; then MISSING="${MISSING}approved index focus (oneplatform-codebase-v2/claude/codex/bes-notes/dev-docs), "; fi
        if [ -z "$HAS_RESULT" ]; then MISSING="${MISSING}result evidence (hit/takeaway), "; fi

        if [ -n "$MISSING" ]; then
            MISSING="${MISSING%, }"
            FAILURE_REASON="insufficient_evidence:${MISSING}"
        else
            # Count query blocks (lines matching query-like patterns)
            QUERY_COUNT=$(echo "$RAG_BODY" | grep -ciE '(query\s*[0-9:]|query\s+intent|searched\s+for|retrieval\s+query)' || true)
            if [ "$QUERY_COUNT" -lt 2 ]; then
                # Also count bullet items that look like separate queries
                QUERY_BULLET_COUNT=$(echo "$RAG_BODY" | grep -ciE '^\s*[-*]\s.*(query|search|looked\s+up|retrieved)' || true)
                TOTAL_QUERIES=$((QUERY_COUNT + QUERY_BULLET_COUNT))
                if [ "$TOTAL_QUERIES" -lt 2 ]; then
                    FAILURE_REASON="insufficient_queries:found ${TOTAL_QUERIES}, need 2+"
                fi
            fi
        fi
    fi
fi

# If validation passed, exit silently
if [ -z "$FAILURE_REASON" ]; then
    exit 0
fi

# --- Emit structured output ---

# Build remediation text based on failure reason
case "$FAILURE_REASON" in
    missing_section)
        CONTEXT_MSG="[Plan RAG Gate] Plan file missing RAG enrichment evidence section. Add a '## RAG Context' section with: (1) query intent, (2) index/namespace used, (3) approved index mention (oneplatform-codebase-v2/claude/codex/bes-notes/dev-docs), (4) top hits/paths, (5) takeaway. Minimum 2 retrieval queries required. Or add 'RAG_DEGRADED:<reason>' if Pinecone is unavailable."
        ;;
    empty_section)
        CONTEXT_MSG="[Plan RAG Gate] RAG Context section is present but empty/placeholder. Add substantive evidence: query intent, retrieval source (index/namespace), approved index mention (oneplatform-codebase-v2/claude/codex/bes-notes/dev-docs), and result evidence (hits/takeaway). Minimum 2 retrieval queries required."
        ;;
    insufficient_evidence:*)
        DETAIL="${FAILURE_REASON#insufficient_evidence:}"
        CONTEXT_MSG="[Plan RAG Gate] RAG Context section is missing required evidence markers: ${DETAIL}. Each query block should include intent, index/namespace, approved index focus, and hit/takeaway."
        ;;
    insufficient_queries:*)
        DETAIL="${FAILURE_REASON#insufficient_queries:}"
        CONTEXT_MSG="[Plan RAG Gate] RAG Context section has insufficient retrieval queries (${DETAIL}). Policy requires minimum 2 documented retrieval queries per planning event."
        ;;
esac

if [ "${PLAN_RAG_GATE_STRICT:-0}" = "1" ]; then
    # Strict mode: top-level decision and reason per PostToolUse spec
    cat <<ENDJSON
{"decision":"block","reason":"Plan file missing required RAG Context evidence.","hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"${CONTEXT_MSG}"}}
ENDJSON
else
    # Warn mode: structured JSON with additionalContext for agent visibility
    cat <<ENDJSON
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"${CONTEXT_MSG}"}}
ENDJSON
fi

exit 0
