#!/bin/bash
# clone-manager.sh — Worker git clone isolation for colony runtime
# Provides functions for creating, verifying, and managing isolated git clones
# that colony workers operate in.
#
# Safety constraints implemented:
#   SC-COL-12: Verify clone path under /tmp/sdlc-colony/ + .git exists
#   SC-COL-21: Refuse prune if bridge not synced; recover output first
#   SC-COL-26: Check commits beyond origin/main (not origin/HEAD)
#   SC-COL-27: Set no-push remote URL on clones
#
# Usage: source this file, then call functions directly.

set -euo pipefail

COLONY_BASE="${COLONY_BASE:-/tmp/sdlc-colony}"

# _colony_log <event> <key:val pairs...>
# Appends a timestamped JSON line to ${COLONY_BASE}/clone-events.log
_colony_log() {
  local event="$1" && shift
  echo "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"event\":\"${event}\",$@}" >> "${COLONY_BASE}/clone-events.log"
}

# colony_clone_create <source_dir> <session_name> <agent_id>
# Creates an isolated git clone for a worker.
# Prints the clone directory path on stdout.
colony_clone_create() {
  local source="${1:?colony_clone_create: source directory required}"
  local session_name="${2:?colony_clone_create: session_name required}"
  local agent_id="${3:?colony_clone_create: agent_id required}"

  local clone_dir="${COLONY_BASE}/${session_name}/worker-${agent_id}"
  local start_ns=$(date +%s%N)

  # Ensure parent directory exists
  mkdir -p "$(dirname "$clone_dir")"

  # Full clone via file:// protocol (not shallow — workers need full history)
  if ! git clone "file://${source}" "${clone_dir}" >/dev/null 2>&1; then
    echo "ERROR: git clone failed from ${source} to ${clone_dir}" >&2
    return 1
  fi

  # Verify .git directory was created (SC-COL-12)
  if [[ ! -d "${clone_dir}/.git" ]]; then
    echo "ERROR: Clone invalid — no .git directory at ${clone_dir}" >&2
    return 1
  fi

  # Prevent accidental pushes from workers (SC-COL-27)
  git -C "${clone_dir}" remote set-url --push origin no-push

  local elapsed_ms=$(( ($(date +%s%N) - start_ns) / 1000000 ))
  local clone_bytes=$(du -sb "${clone_dir}" | cut -f1)
  _colony_log "clone_created" "\"source\":\"${source}\",\"session\":\"${session_name}\",\"agent_id\":\"${agent_id}\",\"clone_dir\":\"${clone_dir}\",\"elapsed_ms\":${elapsed_ms},\"clone_bytes\":${clone_bytes}"

  # Return the clone path on stdout
  echo "${clone_dir}"
}

# colony_clone_verify <clone_dir>
# Verifies that a clone directory is valid for colony use.
# Checks: path under COLONY_BASE, .git exists, push URL is no-push.
# Returns 0 on success, 1 on failure.
colony_clone_verify() {
  local clone_dir="${1:?colony_clone_verify: clone_dir required}"

  # Resolve to absolute path for reliable comparison
  local resolved_dir
  resolved_dir="$(cd "${clone_dir}" 2>/dev/null && pwd -P)" || {
    echo "ERROR: Cannot resolve clone directory: ${clone_dir}" >&2
    return 1
  }

  # Check path is under COLONY_BASE (SC-COL-12)
  if [[ "${resolved_dir}" != "${COLONY_BASE}"/* ]]; then
    echo "ERROR: Clone directory not under ${COLONY_BASE}/: ${resolved_dir}" >&2
    _colony_log "clone_verified" "\"clone_dir\":\"${clone_dir}\",\"valid\":false"
    return 1
  fi

  # Check .git exists (SC-COL-12)
  if [[ ! -d "${clone_dir}/.git" ]]; then
    echo "ERROR: No .git directory in ${clone_dir}" >&2
    _colony_log "clone_verified" "\"clone_dir\":\"${clone_dir}\",\"valid\":false"
    return 1
  fi

  # Check push URL is no-push (SC-COL-27)
  local push_url
  push_url="$(git -C "${clone_dir}" remote get-url --push origin 2>/dev/null || true)"
  if [[ "${push_url}" != "no-push" ]]; then
    echo "ERROR: Push URL is not 'no-push': ${push_url}" >&2
    _colony_log "clone_verified" "\"clone_dir\":\"${clone_dir}\",\"valid\":false"
    return 1
  fi

  _colony_log "clone_verified" "\"clone_dir\":\"${clone_dir}\",\"valid\":true"
  return 0
}

# colony_clone_has_commits <clone_dir>
# Checks whether the clone has at least one commit beyond origin/main.
# Uses origin/main (not origin/HEAD) per council decision M3 (SC-COL-26).
# Returns 0 if commits exist, 1 otherwise.
colony_clone_has_commits() {
  local clone_dir="${1:?colony_clone_has_commits: clone_dir required}"

  if [[ ! -d "${clone_dir}/.git" ]]; then
    echo "ERROR: Not a git repository: ${clone_dir}" >&2
    return 1
  fi

  local commit_count
  commit_count="$(git -C "${clone_dir}" log --oneline origin/main..HEAD 2>/dev/null | wc -l)"

  _colony_log "clone_commit_check" "\"clone_dir\":\"${clone_dir}\",\"commit_count\":${commit_count}"

  if [[ "${commit_count}" -ge 1 ]]; then
    return 0
  else
    return 1
  fi
}

# colony_clone_prune <clone_dir> <bridge_synced>
# Removes a clone directory. Refuses if bridge_synced != 1 (SC-COL-21).
# Returns 0 on success, 1 on refusal/failure.
colony_clone_prune() {
  local clone_dir="${1:?colony_clone_prune: clone_dir required}"
  local bridge_synced="${2:?colony_clone_prune: bridge_synced required}"
  local start_ns=$(date +%s%N)

  # Refuse prune if bridge has not synced (SC-COL-21)
  if [[ "${bridge_synced}" != "1" ]]; then
    echo "ERROR: Cannot prune clone — bridge_synced is not 1 (value: ${bridge_synced})" >&2
    return 1
  fi

  # Safety: verify path is under COLONY_BASE before rm -rf
  local resolved_dir
  resolved_dir="$(cd "${clone_dir}" 2>/dev/null && pwd -P)" || {
    echo "ERROR: Cannot resolve clone directory: ${clone_dir}" >&2
    return 1
  }

  if [[ "${resolved_dir}" != "${COLONY_BASE}"/* ]]; then
    echo "ERROR: Refusing to prune directory not under ${COLONY_BASE}/: ${resolved_dir}" >&2
    return 1
  fi

  rm -rf "${clone_dir}"
  local elapsed_ms=$(( ($(date +%s%N) - start_ns) / 1000000 ))
  _colony_log "clone_pruned" "\"clone_dir\":\"${clone_dir}\",\"bridge_synced\":${bridge_synced},\"elapsed_ms\":${elapsed_ms}"
  return 0
}

# colony_clone_recover_output <clone_dir> <task_id>
# Copies bead-output.md and correction.json (if present) from a clone
# to /tmp/sdlc-colony/recovered-outputs/<task_id>/ for recovery processing.
# Returns 0 on success, 1 if no output files found.
colony_clone_recover_output() {
  local clone_dir="${1:?colony_clone_recover_output: clone_dir required}"
  local task_id="${2:?colony_clone_recover_output: task_id required}"

  local recover_dir="${COLONY_BASE}/recovered-outputs/${task_id}"
  mkdir -p "${recover_dir}"

  local found=0

  if [[ -f "${clone_dir}/bead-output.md" ]]; then
    cp "${clone_dir}/bead-output.md" "${recover_dir}/bead-output.md"
    found=1
  fi

  if [[ -f "${clone_dir}/correction.json" ]]; then
    cp "${clone_dir}/correction.json" "${recover_dir}/correction.json"
    found=1
  fi

  if [[ "${found}" -eq 0 ]]; then
    echo "WARNING: No output files found in ${clone_dir}" >&2
    _colony_log "clone_output_recovered" "\"clone_dir\":\"${clone_dir}\",\"task_id\":\"${task_id}\",\"output_bytes\":0"
    return 1
  fi

  local output_bytes=$(du -sb "${recover_dir}" | cut -f1)
  _colony_log "clone_output_recovered" "\"clone_dir\":\"${clone_dir}\",\"task_id\":\"${task_id}\",\"output_bytes\":${output_bytes}"
  return 0
}
