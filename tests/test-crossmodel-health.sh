#!/bin/bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PLUGIN_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
HEALTH="$PLUGIN_ROOT/scripts/crossmodel-health.sh"
TMPROOT=""
PASS=0
FAIL=0

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if [[ -n "$TMPROOT" ]]; then
    rm -rf "$TMPROOT"
  fi
  exit "$rc"
}

record_pass() {
  PASS=$((PASS + 1))
  printf 'PASS: %s\n' "$1"
}

record_fail() {
  FAIL=$((FAIL + 1))
  printf 'FAIL: %s\n' "$1" >&2
}

assert_contains() {
  local label="$1"
  local file="$2"
  local pattern="$3"
  if grep -qE "$pattern" "$file"; then
    record_pass "$label"
  else
    record_fail "$label (missing contract marker in $file)"
  fi
}

assert_absent() {
  local label="$1"
  local pattern="$2"
  local rc
  shift 2
  set +e
  grep -nE "$pattern" "$@" >"$TMPROOT/forbidden"
  rc=$?
  set -e
  case "$rc" in
    0) record_fail "$label ($(tr '\n' ' ' <"$TMPROOT/forbidden"))" ;;
    1) record_pass "$label" ;;
    *) record_fail "$label (grep could not inspect every required file; exit $rc)" ;;
  esac
}

hash_file() {
  local path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
  else
    sha256sum "$path" | awk '{print $1}'
  fi
}

run_case() {
  local label="$1"
  local journal="$2"
  local expected_rc="$3"
  local expected_health="$4"
  local expected_gate="$5"
  local expected_advance="$6"
  local stdout="$TMPROOT/stdout"
  local stderr="$TMPROOT/stderr"
  local rc

  set +e
  /bin/bash "$HEALTH" --session-journal "$journal" >"$stdout" 2>"$stderr"
  rc=$?
  set -e

  if [[ "$rc" -ne "$expected_rc" ]]; then
    record_fail "$label (expected exit $expected_rc, got $rc; stdout=$(tr '\n' ' ' <"$stdout"); stderr=$(tr '\n' ' ' <"$stderr"))"
    return
  fi

  if jq -e \
    --arg health "$expected_health" \
    --arg gate "$expected_gate" \
    --argjson advance "$expected_advance" \
    '.health == $health and .gate_status == $gate and .advance_allowed == $advance' \
    "$stdout" >/dev/null; then
    record_pass "$label"
  else
    record_fail "$label (unexpected payload: $(tr '\n' ' ' <"$stdout"))"
  fi
}

TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/sdlc-crossmodel-health.XXXXXX")"
TMPROOT="$(cd "$TMPROOT" && pwd -P)"
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

cat >"$TMPROOT/reference-runtime.json" <<'JSON'
{"receipt_id":"aqs-runtime-1","selector":"native-agent","requested_model":"configured","observed_model":"claude-reference","observation_source":"runtime-status-json","fallback_used":false}
JSON
REFERENCE_RECEIPT_CHECKSUM="$(hash_file "$TMPROOT/reference-runtime.json")"

run_case "missing journal is inconclusive" "$TMPROOT/missing.json" 2 UNKNOWN inconclusive false

printf '{not-json\n' >"$TMPROOT/malformed.json"
run_case "malformed journal is inconclusive" "$TMPROOT/malformed.json" 2 UNKNOWN inconclusive false

cat >"$TMPROOT/skip.json" <<'JSON'
{
  "project_root": "PROJECT_ROOT",
  "cross_model_required": false,
  "policy_outcome": "SKIP",
  "targeted_domain": null,
  "worker_tasks": [],
  "required_task_ids": [],
  "expected_artifacts": [],
  "validated_artifacts": [],
  "health_state": "DISABLED",
  "breaker_open": false
}
JSON
jq --arg root "$TMPROOT" '.project_root = $root' "$TMPROOT/skip.json" >"$TMPROOT/skip.tmp"
mv "$TMPROOT/skip.tmp" "$TMPROOT/skip.json"
run_case "explicit policy skip is not applicable" "$TMPROOT/skip.json" 0 DISABLED not_applicable true

cat >"$TMPROOT/ready.json" <<'JSON'
{
  "project_root": "PROJECT_ROOT",
  "cross_model_required": true,
  "policy_outcome": "TARGETED",
  "targeted_domain": "security",
  "reference_model": "claude-reference",
  "reference_model_receipt": {
    "receipt_id": "aqs-runtime-1",
    "selector": "native-agent",
    "requested_model": "configured",
    "observed_model": "claude-reference",
    "observation_source": "runtime-status-json",
    "source_artifact": {
      "path": "reference-runtime.json",
      "checksum": "REFERENCE_RECEIPT_CHECKSUM"
    },
    "fallback_used": false
  },
  "required_task_ids": ["investigate-task", "review-task"],
  "expected_artifacts": [
    {"task_id":"investigate-task","name":"investigator-findings","path":"docs/sdlc/active/task/crossmodel/investigator.md"},
    {"task_id":"review-task","name":"review-findings","path":"docs/sdlc/active/task/crossmodel/reviewer.md"}
  ],
  "worker_tasks": [],
  "validated_artifacts": [],
  "health_state": "READY",
  "breaker_open": false
}
JSON
jq --arg root "$TMPROOT" --arg checksum "$REFERENCE_RECEIPT_CHECKSUM" \
  '.project_root = $root | .reference_model_receipt.source_artifact.checksum = $checksum' \
  "$TMPROOT/ready.json" >"$TMPROOT/ready.tmp"
mv "$TMPROOT/ready.tmp" "$TMPROOT/ready.json"
run_case "required role not dispatched remains running" "$TMPROOT/ready.json" 1 READY running false

cat >"$TMPROOT/complete.json" <<'JSON'
{
  "project_root": "PROJECT_ROOT",
  "cross_model_required": true,
  "policy_outcome": "TARGETED",
  "targeted_domain": "security",
  "reference_model": "claude-reference",
  "reference_model_receipt": {
    "receipt_id": "aqs-runtime-1",
    "selector": "native-agent",
    "requested_model": "configured",
    "observed_model": "claude-reference",
    "observation_source": "runtime-status-json",
    "source_artifact": {
      "path": "reference-runtime.json",
      "checksum": "REFERENCE_RECEIPT_CHECKSUM"
    },
    "fallback_used": false
  },
  "required_task_ids": ["investigate-task", "review-task"],
  "expected_artifacts": [
    {"task_id":"investigate-task","name":"investigator-findings","path":"docs/sdlc/active/task/crossmodel/investigator.md"},
    {"task_id":"review-task","name":"review-findings","path":"docs/sdlc/active/task/crossmodel/reviewer.md"}
  ],
  "worker_tasks": [
    {
      "task_id": "investigate-task",
      "role": "investigator",
      "stage": "A",
      "domain": "security",
      "required": true,
      "status": "completed",
      "task_policy": {
        "role_required": true,
        "evidence_required": true,
        "model_requirement": "cross_model",
        "reference_model": "claude-reference"
      },
      "receipt": {
        "attempt_id": "attempt-1",
        "task_id": "investigate-task",
        "agent_id": "agent-1",
        "role": "investigator",
        "selector": "codex-runtime",
        "requested_model": "auto",
        "observed_model": "gpt-observed",
        "observation_source": "runtime-session-banner",
        "fallback_used": false,
        "terminal_status": "succeeded"
      },
      "model_observation": {
        "attempt_id": "attempt-1",
        "observed_model": "gpt-observed",
        "observation_source": "runtime-session-banner"
      },
      "artifact": {
        "name": "investigator-findings",
        "path": "docs/sdlc/active/task/crossmodel/investigator.md",
        "checksum": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "verification_status": "VALID"
      },
      "evidence": {
        "evidence_id": "evidence-1",
        "attempt_id": "attempt-1",
        "type": "artifact_checksum",
        "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "disposition": "approved"
      }
    },
    {
      "task_id": "review-task",
      "role": "reviewer",
      "stage": "B",
      "domain": "independent",
      "required": true,
      "status": "completed",
      "task_policy": {
        "role_required": true,
        "evidence_required": true,
        "model_requirement": "cross_model",
        "reference_model": "claude-reference"
      },
      "receipt": {
        "attempt_id": "attempt-2",
        "task_id": "review-task",
        "agent_id": "agent-2",
        "role": "reviewer",
        "selector": "codex-runtime",
        "requested_model": "auto",
        "observed_model": "gpt-observed",
        "observation_source": "runtime-session-banner",
        "fallback_used": false,
        "terminal_status": "succeeded"
      },
      "model_observation": {
        "attempt_id": "attempt-2",
        "observed_model": "gpt-observed",
        "observation_source": "runtime-session-banner"
      },
      "artifact": {
        "name": "review-findings",
        "path": "docs/sdlc/active/task/crossmodel/reviewer.md",
        "checksum": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "verification_status": "VALID"
      },
      "evidence": {
        "evidence_id": "evidence-2",
        "attempt_id": "attempt-2",
        "type": "artifact_checksum",
        "hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "disposition": "approved"
      }
    }
  ],
  "validated_artifacts": [
    {"task_id":"investigate-task","name":"investigator-findings","path":"docs/sdlc/active/task/crossmodel/investigator.md","checksum":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","attempt_id":"attempt-1","evidence_id":"evidence-1"},
    {"task_id":"review-task","name":"review-findings","path":"docs/sdlc/active/task/crossmodel/reviewer.md","checksum":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","attempt_id":"attempt-2","evidence_id":"evidence-2"}
  ],
  "health_state": "COMPLETE",
  "breaker_open": false
}
JSON
ARTIFACT_DIR="$TMPROOT/docs/sdlc/active/task/crossmodel"
mkdir -p "$ARTIFACT_DIR"
printf 'investigator evidence\n' >"$ARTIFACT_DIR/investigator.md"
printf 'reviewer evidence\n' >"$ARTIFACT_DIR/reviewer.md"
INVESTIGATOR_CHECKSUM="$(hash_file "$ARTIFACT_DIR/investigator.md")"
REVIEWER_CHECKSUM="$(hash_file "$ARTIFACT_DIR/reviewer.md")"
jq \
  --arg root "$TMPROOT" \
  --arg reference_checksum "$REFERENCE_RECEIPT_CHECKSUM" \
  --arg investigator_checksum "$INVESTIGATOR_CHECKSUM" \
  --arg reviewer_checksum "$REVIEWER_CHECKSUM" \
  '.project_root = $root
   | .reference_model_receipt.source_artifact.checksum = $reference_checksum
   | .worker_tasks[0].artifact.checksum = $investigator_checksum
   | .worker_tasks[0].evidence.hash = $investigator_checksum
   | .validated_artifacts[0].checksum = $investigator_checksum
   | .worker_tasks[1].artifact.checksum = $reviewer_checksum
   | .worker_tasks[1].evidence.hash = $reviewer_checksum
   | .validated_artifacts[1].checksum = $reviewer_checksum' \
  "$TMPROOT/complete.json" >"$TMPROOT/complete.tmp"
mv "$TMPROOT/complete.tmp" "$TMPROOT/complete.json"
run_case "accepted terminal receipt satisfies required role" "$TMPROOT/complete.json" 0 COMPLETE satisfied true

jq '
  .worker_tasks[0] as $base
  | .policy_outcome = "FULL"
  | .targeted_domain = null
  | .required_task_ids += ["investigate-functionality", "investigate-resilience", "investigate-usability"]
  | .expected_artifacts += [
      {"task_id":"investigate-functionality","name":"functionality-findings","path":"docs/sdlc/active/task/crossmodel/functionality.md"},
      {"task_id":"investigate-resilience","name":"resilience-findings","path":"docs/sdlc/active/task/crossmodel/resilience.md"},
      {"task_id":"investigate-usability","name":"usability-findings","path":"docs/sdlc/active/task/crossmodel/usability.md"}
    ]
  | .worker_tasks += [
      ($base
        | .task_id = "investigate-functionality" | .domain = "functionality"
        | .receipt.task_id = "investigate-functionality" | .receipt.attempt_id = "attempt-3" | .receipt.agent_id = "agent-3"
        | .model_observation.attempt_id = "attempt-3"
        | .artifact.name = "functionality-findings" | .artifact.path = "docs/sdlc/active/task/crossmodel/functionality.md" | .artifact.checksum = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
        | .evidence.evidence_id = "evidence-3" | .evidence.attempt_id = "attempt-3" | .evidence.hash = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"),
      ($base
        | .task_id = "investigate-resilience" | .domain = "resilience"
        | .receipt.task_id = "investigate-resilience" | .receipt.attempt_id = "attempt-4" | .receipt.agent_id = "agent-4"
        | .model_observation.attempt_id = "attempt-4"
        | .artifact.name = "resilience-findings" | .artifact.path = "docs/sdlc/active/task/crossmodel/resilience.md" | .artifact.checksum = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
        | .evidence.evidence_id = "evidence-4" | .evidence.attempt_id = "attempt-4" | .evidence.hash = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"),
      ($base
        | .task_id = "investigate-usability" | .domain = "usability"
        | .receipt.task_id = "investigate-usability" | .receipt.attempt_id = "attempt-5" | .receipt.agent_id = "agent-5"
        | .model_observation.attempt_id = "attempt-5"
        | .artifact.name = "usability-findings" | .artifact.path = "docs/sdlc/active/task/crossmodel/usability.md" | .artifact.checksum = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        | .evidence.evidence_id = "evidence-5" | .evidence.attempt_id = "attempt-5" | .evidence.hash = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    ]
  | .validated_artifacts += [
      {"task_id":"investigate-functionality","name":"functionality-findings","path":"docs/sdlc/active/task/crossmodel/functionality.md","checksum":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","attempt_id":"attempt-3","evidence_id":"evidence-3"},
      {"task_id":"investigate-resilience","name":"resilience-findings","path":"docs/sdlc/active/task/crossmodel/resilience.md","checksum":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","attempt_id":"attempt-4","evidence_id":"evidence-4"},
      {"task_id":"investigate-usability","name":"usability-findings","path":"docs/sdlc/active/task/crossmodel/usability.md","checksum":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","attempt_id":"attempt-5","evidence_id":"evidence-5"}
    ]
' "$TMPROOT/complete.json" >"$TMPROOT/full.json"
printf 'functionality evidence\n' >"$ARTIFACT_DIR/functionality.md"
printf 'resilience evidence\n' >"$ARTIFACT_DIR/resilience.md"
printf 'usability evidence\n' >"$ARTIFACT_DIR/usability.md"
FUNCTIONALITY_CHECKSUM="$(hash_file "$ARTIFACT_DIR/functionality.md")"
RESILIENCE_CHECKSUM="$(hash_file "$ARTIFACT_DIR/resilience.md")"
USABILITY_CHECKSUM="$(hash_file "$ARTIFACT_DIR/usability.md")"
jq \
  --arg functionality_checksum "$FUNCTIONALITY_CHECKSUM" \
  --arg resilience_checksum "$RESILIENCE_CHECKSUM" \
  --arg usability_checksum "$USABILITY_CHECKSUM" \
  '.worker_tasks[2].artifact.checksum = $functionality_checksum
   | .worker_tasks[2].evidence.hash = $functionality_checksum
   | .validated_artifacts[2].checksum = $functionality_checksum
   | .worker_tasks[3].artifact.checksum = $resilience_checksum
   | .worker_tasks[3].evidence.hash = $resilience_checksum
   | .validated_artifacts[3].checksum = $resilience_checksum
   | .worker_tasks[4].artifact.checksum = $usability_checksum
   | .worker_tasks[4].evidence.hash = $usability_checksum
   | .validated_artifacts[4].checksum = $usability_checksum' \
  "$TMPROOT/full.json" >"$TMPROOT/full.tmp"
mv "$TMPROOT/full.tmp" "$TMPROOT/full.json"
run_case "full domain set satisfies required role shape" "$TMPROOT/full.json" 0 COMPLETE satisfied true

jq '.worker_tasks[] |= if .domain == "functionality" then .domain = "security" else . end' "$TMPROOT/full.json" >"$TMPROOT/repeated-full-domain.json"
run_case "repeated full domain blocks completion" "$TMPROOT/repeated-full-domain.json" 1 BLOCKED blocked false

jq 'del(.worker_tasks[0].receipt.observed_model)' "$TMPROOT/complete.json" >"$TMPROOT/missing-model.json"
run_case "missing observed model blocks completion" "$TMPROOT/missing-model.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.observed_model = .reference_model' "$TMPROOT/complete.json" >"$TMPROOT/same-model.json"
run_case "same model cannot satisfy cross-model gate" "$TMPROOT/same-model.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].evidence.disposition = "challenged"' "$TMPROOT/complete.json" >"$TMPROOT/inconclusive.json"
run_case "inconclusive evidence is not completion" "$TMPROOT/inconclusive.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.fallback_used = true' "$TMPROOT/complete.json" >"$TMPROOT/incomplete-fallback.json"
run_case "incomplete fallback provenance blocks completion" "$TMPROOT/incomplete-fallback.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.fallback_used = true | .worker_tasks[0].receipt.fallback_model = "gpt-observed" | .worker_tasks[0].receipt.fallback_reason = "requested model unavailable"' "$TMPROOT/complete.json" >"$TMPROOT/valid-fallback.json"
run_case "fully receipted cross-model fallback can satisfy gate" "$TMPROOT/valid-fallback.json" 0 COMPLETE satisfied true

jq '.worker_tasks[0].status = "skipped" | .worker_tasks[0].receipt.terminal_status = "unavailable"' "$TMPROOT/complete.json" >"$TMPROOT/skipped.json"
run_case "skipped required role blocks completion" "$TMPROOT/skipped.json" 1 BLOCKED blocked false

jq '.worker_tasks = [.worker_tasks[0]]' "$TMPROOT/complete.json" >"$TMPROOT/declared-complete-missing-role.json"
run_case "declared complete with missing required role blocks" "$TMPROOT/declared-complete-missing-role.json" 1 BLOCKED blocked false

jq '.worker_tasks[1].receipt.attempt_id = .worker_tasks[0].receipt.attempt_id' "$TMPROOT/complete.json" >"$TMPROOT/duplicate-attempt.json"
run_case "duplicate attempt receipt blocks completion" "$TMPROOT/duplicate-attempt.json" 1 BLOCKED blocked false

jq '.worker_tasks[1].receipt.agent_id = .worker_tasks[0].receipt.agent_id' "$TMPROOT/complete.json" >"$TMPROOT/duplicate-agent.json"
run_case "same worker cannot satisfy independent roles" "$TMPROOT/duplicate-agent.json" 1 BLOCKED blocked false

jq '.worker_tasks[1].artifact.name = .worker_tasks[0].artifact.name' "$TMPROOT/complete.json" >"$TMPROOT/duplicate-artifact.json"
run_case "duplicate artifact cannot satisfy two roles" "$TMPROOT/duplicate-artifact.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].task_policy.evidence_required = false' "$TMPROOT/complete.json" >"$TMPROOT/weakened-policy.json"
run_case "weakened tmup task policy blocks completion" "$TMPROOT/weakened-policy.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].evidence.hash = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"' "$TMPROOT/complete.json" >"$TMPROOT/evidence-mismatch.json"
run_case "evidence checksum mismatch blocks completion" "$TMPROOT/evidence-mismatch.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].artifact.path = "docs/sdlc/active/task/crossmodel/missing.md" | .expected_artifacts[0].path = "docs/sdlc/active/task/crossmodel/missing.md" | .validated_artifacts[0].path = "docs/sdlc/active/task/crossmodel/missing.md"' "$TMPROOT/complete.json" >"$TMPROOT/missing-artifact-file.json"
run_case "missing artifact file blocks completion" "$TMPROOT/missing-artifact-file.json" 1 BLOCKED blocked false

jq '.health_state = "RUNNING" | .worker_tasks[0].artifact.path = "docs/sdlc/active/task/crossmodel/not-created.md" | .expected_artifacts[0].path = "docs/sdlc/active/task/crossmodel/not-created.md" | .validated_artifacts[0].path = "docs/sdlc/active/task/crossmodel/not-created.md"' "$TMPROOT/complete.json" >"$TMPROOT/running-missing-artifact.json"
run_case "terminal receipts cannot bypass files under running journal state" "$TMPROOT/running-missing-artifact.json" 1 BLOCKED blocked false

jq --arg checksum "$INVESTIGATOR_CHECKSUM" '
  .worker_tasks[1].artifact.path = "docs/sdlc/active/task/crossmodel/./investigator.md"
  | .worker_tasks[1].artifact.checksum = $checksum
  | .worker_tasks[1].evidence.hash = $checksum
  | .expected_artifacts[1].path = "docs/sdlc/active/task/crossmodel/./investigator.md"
  | .validated_artifacts[1].path = "docs/sdlc/active/task/crossmodel/./investigator.md"
  | .validated_artifacts[1].checksum = $checksum
' "$TMPROOT/complete.json" >"$TMPROOT/aliased-artifact-path.json"
run_case "canonical path alias cannot satisfy two roles" "$TMPROOT/aliased-artifact-path.json" 1 BLOCKED blocked false

ln "$ARTIFACT_DIR/investigator.md" "$ARTIFACT_DIR/investigator-hardlink.md"
jq --arg checksum "$INVESTIGATOR_CHECKSUM" '
  .worker_tasks[1].artifact.path = "docs/sdlc/active/task/crossmodel/investigator-hardlink.md"
  | .worker_tasks[1].artifact.checksum = $checksum
  | .worker_tasks[1].evidence.hash = $checksum
  | .expected_artifacts[1].path = "docs/sdlc/active/task/crossmodel/investigator-hardlink.md"
  | .validated_artifacts[1].path = "docs/sdlc/active/task/crossmodel/investigator-hardlink.md"
  | .validated_artifacts[1].checksum = $checksum
' "$TMPROOT/complete.json" >"$TMPROOT/hardlinked-artifact.json"
run_case "hard-linked artifact cannot satisfy two roles" "$TMPROOT/hardlinked-artifact.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.observed_model = " CLAUDE-REFERENCE "' "$TMPROOT/complete.json" >"$TMPROOT/normalized-same-model.json"
run_case "case and whitespace cannot evade same-model check" "$TMPROOT/normalized-same-model.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.observed_model = " UNKNOWN "' "$TMPROOT/complete.json" >"$TMPROOT/normalized-unknown-model.json"
run_case "normalized unknown model blocks completion" "$TMPROOT/normalized-unknown-model.json" 1 BLOCKED blocked false

jq 'del(.worker_tasks[0].model_observation.observation_source)' "$TMPROOT/complete.json" >"$TMPROOT/missing-observation-source.json"
run_case "missing worker model observation source blocks" "$TMPROOT/missing-observation-source.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].receipt.observation_source = "different-source"' "$TMPROOT/complete.json" >"$TMPROOT/mismatched-observation-source.json"
run_case "worker observation must match terminal receipt provenance" "$TMPROOT/mismatched-observation-source.json" 1 BLOCKED blocked false

jq 'del(.reference_model_receipt.observation_source)' "$TMPROOT/complete.json" >"$TMPROOT/missing-reference-source.json"
run_case "missing reference model observation is inconclusive" "$TMPROOT/missing-reference-source.json" 2 UNKNOWN inconclusive false

jq '.reference_model_receipt.source_artifact.checksum = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"' "$TMPROOT/complete.json" >"$TMPROOT/mismatched-reference-source.json"
run_case "reference model observation must match captured source receipt" "$TMPROOT/mismatched-reference-source.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].role = "reviewer" | .worker_tasks[0].receipt.role = "reviewer"' "$TMPROOT/complete.json" >"$TMPROOT/wrong-role-shape.json"
run_case "wrong required-role shape blocks completion" "$TMPROOT/wrong-role-shape.json" 1 BLOCKED blocked false

jq '.worker_tasks[0].domain = "functionality"' "$TMPROOT/complete.json" >"$TMPROOT/wrong-targeted-domain.json"
run_case "wrong targeted domain blocks completion" "$TMPROOT/wrong-targeted-domain.json" 1 BLOCKED blocked false

jq '.worker_tasks[1].stage = "A"' "$TMPROOT/complete.json" >"$TMPROOT/wrong-stage.json"
run_case "wrong review stage blocks completion" "$TMPROOT/wrong-stage.json" 1 BLOCKED blocked false

jq '.health_state = "REQUIRED_UNAVAILABLE"' "$TMPROOT/complete.json" >"$TMPROOT/required-unavailable.json"
run_case "required unavailable cannot satisfy completion" "$TMPROOT/required-unavailable.json" 1 BLOCKED blocked false

jq '.breaker_open = true | .health_state = "FALLBACK_CLAUDE_ONLY"' "$TMPROOT/complete.json" >"$TMPROOT/fallback.json"
run_case "Claude-only fallback cannot satisfy required gate" "$TMPROOT/fallback.json" 1 BLOCKED blocked false

assert_contains \
  "health gate evaluates terminal receipts" \
  "$HEALTH" \
  'receipt_valid|terminal_status'
assert_contains \
  "orchestrator requires positive gate result" \
  "$PLUGIN_ROOT/skills/sdlc-orchestrate/SKILL.md" \
  'gate_status: satisfied.*advance_allowed: true'
assert_contains \
  "supervisor retrieves verbose terminal receipts" \
  "$PLUGIN_ROOT/agents/crossmodel-supervisor.md" \
  'tmup_status.*verbose: true'
assert_contains \
  "loop doctrine requires dispatch receipts" \
  "$PLUGIN_ROOT/skills/sdlc-loop/SKILL.md" \
  'Required-Role Dispatch Invariant'
assert_contains \
  "AQS records an observed runtime receipt" \
  "$PLUGIN_ROOT/references/artifact-templates.md" \
  'runtime_receipt:'
assert_contains \
  "AQS retains proven status until receipt gate" \
  "$PLUGIN_ROOT/skills/sdlc-adversarial/SKILL.md" \
  'bead remains .proven.'
assert_contains \
  "colony bridge transition is post-gate only" \
  "$PLUGIN_ROOT/colony/conductor-prompt.md" \
  'On required-role failure or inconclusive evidence, do not call the bridge transition'
assert_contains \
  "supervisor journal retains tmup task policy" \
  "$PLUGIN_ROOT/agents/crossmodel-supervisor.md" \
  '"model_requirement": "cross_model"'
assert_contains \
  "preflight queries live MCP schema" \
  "$PLUGIN_ROOT/scripts/crossmodel-preflight.sh" \
  'method.*tools/list'
assert_absent \
  "active cross-model contract has no fail-open or stale model claims" \
  'SKIP_UNAVAILABLE|FALLBACK_CLAUDE_ONLY|CLAUDE_ONLY is always valid|Skip worker, continue|Accept loss, continue|gpt-5\.[0-9]|1050000|750000' \
  "$PLUGIN_ROOT/skills/sdlc-crossmodel/SKILL.md" \
  "$PLUGIN_ROOT/agents/crossmodel-supervisor.md" \
  "$PLUGIN_ROOT/skills/sdlc-orchestrate/SKILL.md" \
  "$PLUGIN_ROOT/references/fft-decision-trees.md" \
  "$PLUGIN_ROOT/colony/conductor-prompt.md" \
  "$PLUGIN_ROOT/skills/sdlc-orchestrate/colony-mode.md" \
  "$PLUGIN_ROOT/skills/sdlc-adversarial/SKILL.md" \
  "$PLUGIN_ROOT/skills/sdlc-evolve/SKILL.md" \
  "$PLUGIN_ROOT/commands/adversarial.md" \
  "$PLUGIN_ROOT/references/adversarial-quality.md"

printf '\nResults: %d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
printf 'CROSSMODEL_HEALTH_TESTS_PASS\n'
