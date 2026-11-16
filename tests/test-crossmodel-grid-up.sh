#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/crossmodel-grid-test.XXXXXX")"
trap 'rm -rf "$TMPROOT"' EXIT
mkdir -p "$TMPROOT/bin" "$TMPROOT/home" "$TMPROOT/tmup/scripts"
cat >"$TMPROOT/bin/tmux" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$LOG"
case "$1" in
  has-session) exit 1 ;;
  list-panes) printf 'pane\n' ;;
  capture-pane) printf 'xm $ \n' ;;
  split-window) printf '%%viewer\n' ;;
  list-clients) [[ "$CLIENT" == yes ]] && printf '/dev/ttys001\n'; exit 0 ;;
esac
STUB
cat >"$TMPROOT/bin/uname" <<'STUB'
#!/bin/bash
printf '%s\n' "$OS"
STUB
cat >"$TMPROOT/bin/osascript" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$LOG"
[[ "$OSASCRIPT_OK" == yes ]]
STUB
cat >"$TMPROOT/tmup/scripts/sync-codex-agents.sh" <<'STUB'
#!/bin/bash
exit 0
STUB
chmod +x "$TMPROOT/bin/tmux" "$TMPROOT/bin/uname" "$TMPROOT/bin/osascript"

run_case() {
  local name="$1" expected="$2" mode="$3" os="$4" client="$5" osa="$6" tmux_env="$7" pane="$8" ssh="$9"
  local rc
  : >"$TMPROOT/log"
  set +e
  env -i PATH="$TMPROOT/bin:/usr/bin:/bin:/opt/homebrew/bin" HOME="$TMPROOT/home" TMPDIR="$TMPROOT" \
    TMUP_PLUGIN_ROOT="$TMPROOT/tmup" LOG="$TMPROOT/log" OS="$os" CLIENT="$client" OSASCRIPT_OK="$osa" \
    TMUX="$tmux_env" TMUX_PANE="$pane" SSH_CONNECTION="$ssh" XM_VIEWER_TIMEOUT_SECONDS=1 \
    /bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" --session-name xm-test --panes 1 >"$TMPROOT/out" 2>"$TMPROOT/err"
  rc=$?
  set -e
  if [[ "$rc" != "$expected" ]]; then
    printf 'FAIL: %s expected exit %s got %s\n' "$name" "$expected" "$rc" >&2
    exit 1
  fi
  if [[ "$expected" == 0 ]]; then
    if ! jq -e --arg mode "$mode" '.ready == true and .visibility.mode == $mode and .visibility.attached_clients == 1 and .visibility.client_ttys == ["/dev/ttys001"] and .visibility.session_name == "xm-test"' "$TMPROOT/out" >/dev/null; then
      printf 'FAIL: %s missing verified viewer\n' "$name" >&2
      exit 1
    fi
    grep -q 'attach-session -r -t' "$TMPROOT/log"
    if [[ "$mode" == split-pane ]]; then
      grep -q 'split-window .* -t %0 ' "$TMPROOT/log"
      grep -q "attach-session -r -t '=xm-test'" "$TMPROOT/log"
    else
      grep -q 'attach-session -r -t =xm-test' "$TMPROOT/log"
    fi
  else
    jq -e '.ready == false and .code == "VISIBILITY_UNAVAILABLE"' "$TMPROOT/out" >/dev/null
    grep -q 'kill-session -t xm-test' "$TMPROOT/log"
    if [[ "$name" == split_timeout ]]; then
      grep -q 'kill-pane -t %viewer' "$TMPROOT/log"
    fi
  fi
}

run_case split 0 split-pane Linux yes yes /tmp/socket,1,0 %0 ''
run_case mac 0 new-window Darwin yes yes '' '' ''
run_case unavailable 2 '' Linux no yes '' '' ''
run_case timeout 2 '' Darwin no yes '' '' ''
run_case split_timeout 2 '' Linux no yes /tmp/socket,1,0 %0 ''
run_case launch_failure 2 '' Darwin yes no '' '' ''
run_case ssh 2 '' Darwin yes yes '' '' remote
printf 'CROSSMODEL_GRID_UP_TESTS_PASS\n'
