#!/bin/bash
# Cross-Model Adversarial Review — fail-closed completion gate.
#
# Exit codes:
#   0  required review satisfied, or an explicit policy decision made it inapplicable
#   1  required review is pending or blocked; parent workflow must not advance
#   2  journal/tooling is unavailable or malformed; result is inconclusive

set -euo pipefail

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

emit_unknown() {
  local reason="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg reason "$reason" --arg path "$SESSION_JOURNAL" \
      '{health:"UNKNOWN",gate_status:"inconclusive",advance_allowed:false,reason:$reason,path:$path}'
  else
    printf '{"health":"UNKNOWN","gate_status":"inconclusive","advance_allowed":false,"reason":"jq unavailable"}\n'
  fi
  exit 2
}

if ! command -v jq >/dev/null 2>&1; then
  emit_unknown "jq is required for authoritative receipt validation"
fi

if [[ ! -f "$SESSION_JOURNAL" ]]; then
  emit_unknown "session journal not found"
fi

if [[ ! -s "$SESSION_JOURNAL" ]]; then
  emit_unknown "session journal is empty"
fi

if ! jq -e '
  def clean: gsub("^[[:space:]]+|[[:space:]]+$"; "");
  def known_string:
    type == "string"
    and ((clean | ascii_downcase) as $value
      | ($value | length) > 0
      and ($value | IN("unknown", "null", "unavailable") | not));
  type == "object"
  and (.cross_model_required | type == "boolean")
  and (.policy_outcome | type == "string")
  and (.project_root | known_string)
  and (.worker_tasks | type == "array")
  and (.required_task_ids | type == "array")
  and (.expected_artifacts | type == "array")
  and (.validated_artifacts | type == "array")
  and (.breaker_open | type == "boolean")
  and ((.health_state | type) == "string")
  and (.health_state | IN("READY", "RUNNING", "DEGRADED", "COMPLETE", "DISABLED", "REQUIRED_UNAVAILABLE", "BLOCKED", "FALLBACK_CLAUDE_ONLY"))
  and (
    if .cross_model_required then
      (.policy_outcome | IN("FULL", "TARGETED"))
      and
      (.reference_model | known_string)
      and (.reference_model_receipt.receipt_id | known_string)
      and (.reference_model_receipt.selector | known_string)
      and (.reference_model_receipt.requested_model | known_string)
      and (.reference_model_receipt.observed_model | known_string)
      and (.reference_model_receipt.observation_source | known_string)
      and (.reference_model_receipt.source_artifact.path | known_string)
      and (.reference_model_receipt.source_artifact.checksum | type == "string" and test("^[0-9a-f]{64}$"))
      and (.reference_model_receipt.fallback_used | type == "boolean")
      and (
        if .reference_model_receipt.fallback_used then
          (.reference_model_receipt.fallback_model | known_string)
          and (.reference_model_receipt.fallback_reason | known_string)
          and ((.reference_model_receipt.fallback_model | clean | ascii_downcase) == (.reference_model_receipt.observed_model | clean | ascii_downcase))
        else
          ((.reference_model_receipt.fallback_model // null) == null)
          and ((.reference_model_receipt.fallback_reason // null) == null)
        end
      )
      and (.required_task_ids | length > 0 and all(.[]; known_string))
      and ((.required_task_ids | unique | length) == (.required_task_ids | length))
      and ((.expected_artifacts | length) == (.required_task_ids | length))
      and (
        if .policy_outcome == "FULL" then
          (.required_task_ids | length == 5) and ((.targeted_domain // null) == null)
        else
          (.required_task_ids | length == 2)
          and (.targeted_domain | known_string)
          and (.targeted_domain | IN("functionality", "security", "usability", "resilience"))
        end
      )
    else
      .policy_outcome == "SKIP"
      and (.required_task_ids | length == 0)
      and (.expected_artifacts | length == 0)
      and (.validated_artifacts | length == 0)
      and ((.targeted_domain // null) == null)
    end
  )
' "$SESSION_JOURNAL" >/dev/null 2>&1; then
  emit_unknown "session journal schema is invalid or incomplete"
fi

FILES_VALID=true
if [[ "$(jq -r '.cross_model_required' "$SESSION_JOURNAL")" == "true" ]]; then
  PYTHON_BIN="$(command -v python3.12 || command -v python3 || true)"
  if [[ -z "$PYTHON_BIN" ]]; then
    emit_unknown "python3 is required for artifact path and checksum validation"
  fi
  if ! "$PYTHON_BIN" - "$SESSION_JOURNAL" >/dev/null 2>&1 <<'PY'
import hashlib
import json
import pathlib
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    journal = json.load(stream)

root = pathlib.Path(journal["project_root"])
if not root.is_absolute() or not root.is_dir():
    raise SystemExit(1)
root = root.resolve(strict=True)

seen_paths = set()
seen_inodes = set()

def confined_file(path_value):
    relative = pathlib.PurePosixPath(path_value)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != path_value:
        raise SystemExit(1)
    candidate = root.joinpath(*relative.parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise SystemExit(1)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError:
        raise SystemExit(1)
    identity = (resolved.stat().st_dev, resolved.stat().st_ino)
    if resolved in seen_paths or identity in seen_inodes:
        raise SystemExit(1)
    seen_paths.add(resolved)
    seen_inodes.add(identity)
    return resolved

source = journal["reference_model_receipt"]["source_artifact"]
source_path = confined_file(source["path"])
source_bytes = source_path.read_bytes()
if hashlib.sha256(source_bytes).hexdigest() != source["checksum"]:
    raise SystemExit(1)
try:
    source_receipt = json.loads(source_bytes)
except (UnicodeDecodeError, json.JSONDecodeError):
    raise SystemExit(1)
reference = journal["reference_model_receipt"]
for field in (
    "receipt_id", "selector", "requested_model", "observed_model",
    "observation_source", "fallback_used",
):
    if source_receipt.get(field) != reference.get(field):
        raise SystemExit(1)
for field in ("fallback_model", "fallback_reason"):
    if source_receipt.get(field) != reference.get(field):
        raise SystemExit(1)

for artifact in journal["validated_artifacts"]:
    resolved = confined_file(artifact["path"])
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if digest != artifact["checksum"]:
        raise SystemExit(1)
PY
  then
    FILES_VALID=false
  fi
fi

RESULT=$(jq -c --argjson files_valid "$FILES_VALID" '
  def clean: gsub("^[[:space:]]+|[[:space:]]+$"; "");
  def normalized: clean | ascii_downcase;
  def present:
    type == "string"
    and ((normalized) as $value
      | ($value | length) > 0
      and ($value | IN("unknown", "null", "unavailable") | not));
  def sha256:
    type == "string" and test("^[0-9a-f]{64}$");
  def receipt_valid($worker; $journal):
    ($worker.status == "complete" or $worker.status == "completed")
    and ($worker.role | present)
    and (
      if $worker.role == "investigator" then
        $worker.stage == "A"
        and ($worker.domain | IN("functionality", "security", "usability", "resilience"))
      elif $worker.role == "reviewer" then
        $worker.stage == "B" and $worker.domain == "independent"
      else false
      end
    )
    and ($worker.task_policy.role_required == true)
    and ($worker.task_policy.evidence_required == true)
    and ($worker.task_policy.model_requirement == "cross_model")
    and (($worker.task_policy.reference_model | normalized) == ($journal.reference_model | normalized))
    and ($worker.receipt | type == "object")
    and ($worker.receipt.attempt_id | present)
    and ($worker.receipt.task_id == $worker.task_id)
    and ($worker.receipt.agent_id | present)
    and (($worker.receipt.role | normalized) == ($worker.role | normalized))
    and ($worker.receipt.selector | present)
    and ($worker.receipt.requested_model | present)
    and ($worker.receipt.observed_model | present)
    and ($worker.receipt.observation_source | present)
    and (($worker.receipt.observed_model | normalized) != ($journal.reference_model | normalized))
    and ($worker.model_observation.attempt_id == $worker.receipt.attempt_id)
    and ($worker.model_observation.observed_model | present)
    and (($worker.model_observation.observed_model | normalized) == ($worker.receipt.observed_model | normalized))
    and ($worker.model_observation.observation_source | present)
    and ($worker.model_observation.observation_source == $worker.receipt.observation_source)
    and ($worker.receipt.fallback_used | type == "boolean")
    and (
      if $worker.receipt.fallback_used then
        ($worker.receipt.fallback_model | present)
        and ($worker.receipt.fallback_reason | present)
        and (($worker.receipt.fallback_model | normalized) == ($worker.receipt.observed_model | normalized))
      else
        (($worker.receipt.fallback_model // null) == null)
        and (($worker.receipt.fallback_reason // null) == null)
      end
    )
    and ($worker.receipt.terminal_status == "succeeded")
    and ($worker.artifact.name | present)
    and ($worker.artifact.path | present)
    and ($worker.artifact.checksum | sha256)
    and ($worker.artifact.verification_status == "VALID")
    and ($worker.evidence.evidence_id | present)
    and ($worker.evidence.attempt_id == $worker.receipt.attempt_id)
    and ($worker.evidence.type == "artifact_checksum")
    and ($worker.evidence.hash == $worker.artifact.checksum)
    and ($worker.evidence.disposition == "approved")
    and (($journal.reference_model_receipt.observed_model | normalized) == ($journal.reference_model | normalized))
    and ([$journal.expected_artifacts[]
      | select(.task_id == $worker.task_id
        and .name == $worker.artifact.name
        and .path == $worker.artifact.path)] | length) == 1
    and ([$journal.validated_artifacts[]
      | select(.task_id == $worker.task_id
        and .name == $worker.artifact.name
        and .path == $worker.artifact.path
        and .checksum == $worker.artifact.checksum
        and .attempt_id == $worker.receipt.attempt_id
        and .evidence_id == $worker.evidence.evidence_id)] | length) == 1;

  if .cross_model_required == false then
    {
      health: "DISABLED",
      gate_status: "not_applicable",
      advance_allowed: true,
      reason: "cross-model review explicitly skipped by policy",
      total_required: 0,
      satisfied: 0,
      blocked: 0,
      pending: 0,
      breaker_open: .breaker_open
    }
  else
    . as $journal
    | [
        $journal.required_task_ids[] as $task_id
        | [$journal.worker_tasks[] | select(.required == true and .task_id == $task_id)] as $rows
        | {
            task_id: $task_id,
            row_count: ($rows | length),
            terminal_problem: (
              ($rows | length) == 1
              and ($rows[0].status | IN("failed", "timed_out", "no_evidence", "skipped", "unavailable", "inconclusive", "replaced"))
            ),
            pending: (
              ($rows | length) == 0
              or (($rows | length) == 1 and ($rows[0].status | IN("pending", "claimed", "running")))
            ),
            satisfied: (
              ($rows | length) == 1
              and receipt_valid($rows[0]; $journal)
            ),
            attempt_id: (if ($rows | length) == 1 then ($rows[0].receipt.attempt_id // null) else null end)
          }
      ] as $checks
    | ([$checks[] | select(.satisfied)] | length) as $satisfied
    | ([$checks[] | select(.pending)] | length) as $pending
    | ([$checks[] | .attempt_id | select(. != null)] | length) as $attempt_count
    | ([$checks[] | .attempt_id | select(. != null)] | unique | length) as $unique_attempts
    | ([$checks[] | select(.row_count > 1 or .terminal_problem or ((.pending | not) and (.satisfied | not)))] | length) as $invalid
    | ([$journal.worker_tasks[] as $worker | select($worker.required == true and ($journal.required_task_ids | index($worker.task_id) != null)) | $worker.role]) as $roles
    | ([$journal.worker_tasks[] as $worker | select($worker.required == true and $worker.role == "investigator" and ($journal.required_task_ids | index($worker.task_id) != null)) | $worker.domain] | sort) as $investigator_domains
    | ([$journal.worker_tasks[] as $worker | select($worker.required == true and ($journal.required_task_ids | index($worker.task_id) != null)) | $worker.receipt.agent_id // null | select(. != null)]) as $agent_ids
    | ([$journal.worker_tasks[] as $worker | select($worker.required == true and ($journal.required_task_ids | index($worker.task_id) != null)) | $worker.artifact.name // null | select(. != null)]) as $artifact_names
    | ([$journal.worker_tasks[] as $worker | select($worker.required == true and ($journal.required_task_ids | index($worker.task_id) != null)) | $worker.artifact.path // null | select(. != null)]) as $artifact_paths
    | (
        if $journal.policy_outcome == "FULL" then
          (([$roles[] | select(. == "investigator")] | length) != 4 or ([$roles[] | select(. == "reviewer")] | length) != 1)
        else
          (([$roles[] | select(. == "investigator")] | length) != 1 or ([$roles[] | select(. == "reviewer")] | length) != 1)
        end
      ) as $role_shape_invalid
    | (
        if $journal.policy_outcome == "FULL" then
          $investigator_domains != ["functionality", "resilience", "security", "usability"]
        else
          ($investigator_domains | length) != 1 or $investigator_domains[0] != $journal.targeted_domain
        end
      ) as $domain_shape_invalid
    | if $journal.breaker_open
        or ($journal.health_state | IN("DISABLED", "DEGRADED", "FALLBACK_CLAUDE_ONLY", "REQUIRED_UNAVAILABLE", "BLOCKED"))
      then {
        health: "BLOCKED",
        gate_status: "blocked",
        advance_allowed: false,
        reason: "required cross-model review degraded or unavailable",
        total_required: ($checks | length),
        satisfied: $satisfied,
        blocked: (($checks | length) - $satisfied),
        pending: $pending,
        breaker_open: $journal.breaker_open
      }
      elif $invalid > 0
        or $attempt_count != $unique_attempts
        or (($agent_ids | length) != ($agent_ids | unique | length))
        or (($artifact_names | length) != ($artifact_names | unique | length))
        or (($artifact_paths | length) != ($artifact_paths | unique | length))
        or ($pending == 0 and $role_shape_invalid)
        or ($pending == 0 and $domain_shape_invalid)
        or ($files_valid | not)
        or ($journal.health_state == "COMPLETE" and $satisfied != ($checks | length))
      then {
        health: "BLOCKED",
        gate_status: "blocked",
        advance_allowed: false,
        reason: "required role lacks a unique accepted terminal receipt and artifact",
        total_required: ($checks | length),
        satisfied: $satisfied,
        blocked: (if $invalid > 0 then $invalid else 1 end),
        pending: $pending,
        breaker_open: $journal.breaker_open
      }
      elif $journal.health_state == "COMPLETE" and $files_valid and $satisfied == ($checks | length)
      then {
        health: "COMPLETE",
        gate_status: "satisfied",
        advance_allowed: true,
        reason: "every required role has an accepted terminal receipt and artifact",
        total_required: ($checks | length),
        satisfied: $satisfied,
        blocked: 0,
        pending: 0,
        breaker_open: $journal.breaker_open
      }
      else {
        health: "READY",
        gate_status: "running",
        advance_allowed: false,
        reason: "required role dispatch or completion remains pending",
        total_required: ($checks | length),
        satisfied: $satisfied,
        blocked: 0,
        pending: $pending,
        breaker_open: $journal.breaker_open
      }
      end
  end
' "$SESSION_JOURNAL") || emit_unknown "session journal evaluation failed"

printf '%s\n' "$RESULT"

case "$(printf '%s\n' "$RESULT" | jq -r '.gate_status')" in
  satisfied|not_applicable)
    exit 0
    ;;
  running|blocked)
    exit 1
    ;;
  *)
    exit 2
    ;;
esac
