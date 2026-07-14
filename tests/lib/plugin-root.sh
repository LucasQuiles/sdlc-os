#!/bin/bash

resolve_plugin_root() {
  local caller="${1:?resolve_plugin_root: caller script required}"
  local candidate canonical
  if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    candidate="$CLAUDE_PLUGIN_ROOT"
  else
    candidate="$(dirname "$caller")/.."
  fi
  if ! canonical="$(cd "$candidate" 2>/dev/null && pwd -P)"; then
    printf 'ROOT_INVALID:invalid SDLC-OS plugin root: %s\n' "$candidate" >&2
    return 1
  fi
  candidate="$canonical"
  if [[ ! -f "$candidate/.claude-plugin/plugin.json" ||
        -L "$candidate/.claude-plugin/plugin.json" ||
        ! -d "$candidate/hooks" ||
        -L "$candidate/hooks" ]]; then
    printf 'ROOT_INVALID:invalid SDLC-OS plugin root: %s\n' "$candidate" >&2
    return 1
  fi
  printf '%s\n' "$candidate"
}
