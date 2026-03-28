#!/bin/bash
# Cross-Model Adversarial Review — Session Health
# Computes session health from worker states in a session journal file.
# Args: --session-journal PATH
# Exit 0 + JSON with health field. Health values:
#   READY | RUNNING | DEGRADED | FALLBACK_CLAUDE_ONLY | COMPLETE | DISABLED | UNKNOWN

set -euo pipefail

# --- Arg parsing ---

SESSION_JOURNAL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-journal)
      SESSION_JOURNAL="${2:-}"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SESSION_JOURNAL" ]]; then
  printf 'Missing required argument: --session-journal\n' >&2
  exit 2
fi

# --- Helper: emit result ---

emit_health() {
  local health="$1"
  printf '%s\n' "$2"
  # health is embedded in $2 already — this function is just for documentation
}

# --- Read session journal ---

if [[ ! -f "$SESSION_JOURNAL" ]]; then
  printf '{"health":"UNKNOWN","reason":"session journal not found","path":"%s"}\n' "$SESSION_JOURNAL"
  exit 0
fi

JOURNAL_CONTENT=$(cat "$SESSION_JOURNAL" 2>/dev/null || echo "")

if [[ -z "$JOURNAL_CONTENT" ]]; then
  printf '{"health":"UNKNOWN","reason":"session journal is empty","path":"%s"}\n' "$SESSION_JOURNAL"
  exit 0
fi

# --- Parse with jq (preferred) or grep fallback ---

if command -v jq &> /dev/null; then
  # Validate JSON first
  if ! printf '%s\n' "$JOURNAL_CONTENT" | jq empty 2>/dev/null; then
    printf '{"health":"UNKNOWN","reason":"session journal is not valid JSON","path":"%s"}\n' "$SESSION_JOURNAL"
    exit 0
  fi

  # Extract worker array — canonical field is .worker_tasks (spec), with fallbacks
  WORKERS_JSON=$(printf '%s\n' "$JOURNAL_CONTENT" | jq -r '(.worker_tasks // .workers // .worker_states // []) | @json' 2>/dev/null || echo "[]")

  TOTAL=$(printf '%s\n' "$WORKERS_JSON" | jq 'length' 2>/dev/null || echo "0")
  COMPLETED=$(printf '%s\n' "$WORKERS_JSON" | jq '[.[] | select(.status == "completed")] | length' 2>/dev/null || echo "0")
  FAILED=$(printf '%s\n' "$WORKERS_JSON" | jq '[.[] | select(.status == "failed")] | length' 2>/dev/null || echo "0")
  TIMED_OUT=$(printf '%s\n' "$WORKERS_JSON" | jq '[.[] | select(.status == "timed_out")] | length' 2>/dev/null || echo "0")
  NO_EVIDENCE=$(printf '%s\n' "$WORKERS_JSON" | jq '[.[] | select(.status == "no_evidence")] | length' 2>/dev/null || echo "0")

  VALIDATED_ARTIFACTS=$(printf '%s\n' "$JOURNAL_CONTENT" | jq '(.validated_artifacts // 0)' 2>/dev/null || echo "0")
  BREAKER_OPEN=$(printf '%s\n' "$JOURNAL_CONTENT" | jq '(.breaker_open // false)' 2>/dev/null || echo "false")
  HEALTH_STATE=$(printf '%s\n' "$JOURNAL_CONTENT" | jq -r '(.health_state // "")' 2>/dev/null || echo "")

else
  # --- grep fallback (approximate counts) ---

  TOTAL=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -c '"status"' 2>/dev/null || echo "0")
  COMPLETED=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -c '"completed"' 2>/dev/null || echo "0")
  FAILED=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -c '"failed"' 2>/dev/null || echo "0")
  TIMED_OUT=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -c '"timed_out"' 2>/dev/null || echo "0")
  NO_EVIDENCE=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -c '"no_evidence"' 2>/dev/null || echo "0")
  VALIDATED_ARTIFACTS=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -oE '"validated_artifacts"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+$' | head -1 || echo "0")
  BREAKER_RAW=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -oE '"breaker_open"[[:space:]]*:[[:space:]]*(true|false)' | grep -oE '(true|false)$' | head -1 || echo "false")
  BREAKER_OPEN="${BREAKER_RAW:-false}"
  HEALTH_STATE=$(printf '%s\n' "$JOURNAL_CONTENT" | grep -oE '"health_state"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -oE '"[^"]*"$' | tr -d '"' | head -1 || echo "")

fi

# Sanitize to integers
TOTAL="${TOTAL:-0}"
COMPLETED="${COMPLETED:-0}"
FAILED="${FAILED:-0}"
TIMED_OUT="${TIMED_OUT:-0}"
NO_EVIDENCE="${NO_EVIDENCE:-0}"
VALIDATED_ARTIFACTS="${VALIDATED_ARTIFACTS:-0}"
BREAKER_OPEN="${BREAKER_OPEN:-false}"
HEALTH_STATE="${HEALTH_STATE:-}"

# --- Check journal-declared DISABLED state (highest priority, checked before worker parsing) ---

if [[ "$HEALTH_STATE" == "DISABLED" ]]; then
  printf '{"health":"DISABLED","reason":"journal health_state is DISABLED","total":%d,"completed":0,"failed":0,"timed_out":0,"no_evidence":0,"validated_artifacts":%s,"breaker_open":%s}\n' \
    "$TOTAL" "$VALIDATED_ARTIFACTS" "$BREAKER_OPEN"
  exit 0
fi

# --- Detect READY: journal present and valid but no workers dispatched yet ---

if [[ "$TOTAL" -eq 0 ]]; then
  if [[ "$BREAKER_OPEN" != "true" ]]; then
    printf '{"health":"READY","reason":"journal valid with no workers dispatched","total":0,"completed":0,"failed":0,"timed_out":0,"no_evidence":0,"validated_artifacts":%s,"breaker_open":%s}\n' \
      "${VALIDATED_ARTIFACTS:-0}" "$BREAKER_OPEN"
  else
    printf '{"health":"FALLBACK_CLAUDE_ONLY","reason":"breaker open with no workers","total":0,"completed":0,"failed":0,"timed_out":0,"no_evidence":0,"validated_artifacts":%s,"breaker_open":true}\n' \
      "${VALIDATED_ARTIFACTS:-0}"
  fi
  exit 0
fi

# --- Compute health ---

HEALTH="RUNNING"

# Breaker open → FALLBACK_CLAUDE_ONLY (highest priority)
if [[ "$BREAKER_OPEN" == "true" ]]; then
  HEALTH="FALLBACK_CLAUDE_ONLY"

# All workers done (completed + failed + timed_out + no_evidence == total) → COMPLETE or DEGRADED
elif [[ $(( COMPLETED + FAILED + TIMED_OUT + NO_EVIDENCE )) -eq "$TOTAL" ]]; then
  if [[ "$FAILED" -gt 0 ]] || [[ "$NO_EVIDENCE" -gt 0 ]] || [[ "$TIMED_OUT" -gt 0 ]]; then
    HEALTH="DEGRADED"
  else
    HEALTH="COMPLETE"
  fi

# Still running workers, but any problem already visible → DEGRADED (spec §6.1: any worker loss/timeout/missing artifact)
elif [[ "$FAILED" -gt 0 ]] || [[ "$NO_EVIDENCE" -gt 0 ]] || [[ "$TIMED_OUT" -gt 0 ]]; then
  HEALTH="DEGRADED"
fi

printf '{"health":"%s","total":%d,"completed":%d,"failed":%d,"timed_out":%d,"no_evidence":%d,"validated_artifacts":%s,"breaker_open":%s}\n' \
  "$HEALTH" \
  "$TOTAL" \
  "$COMPLETED" \
  "$FAILED" \
  "$TIMED_OUT" \
  "$NO_EVIDENCE" \
  "$VALIDATED_ARTIFACTS" \
  "$BREAKER_OPEN"
