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
  set-option|show-options|select-layout|send-keys|capture-pane|list-panes)
    [[ "$*" == *'-t =xm-test:'* ]] || exit 1 ;;
  split-window) [[ "$*" == *'-t %0 '* || "$*" == *'-t =xm-test:'* ]] || exit 1 ;;
  kill-pane) [[ "$*" != *'-t =%'* ]] || exit 1 ;;
esac
case "$1" in
  has-session) if [[ "$CLIENT" == hung_has ]]; then sleep 10; fi; [[ "$CLIENT" == existing ]] ;;
  new-session) if [[ "$CLIENT" == creation_timeout ]]; then kill -KILL "$$"; fi; [[ "$CLIENT" != collision ]] ;;
  set-option) printf '%s' "$5" >"$OWNER" ;;
  show-options) if [[ "$CLIENT" == foreign ]]; then printf 'someone-else\n'; elif [[ -f "$OWNER" ]]; then cat "$OWNER"; else exit 1; fi ;;
  list-panes) printf 'pane\n' ;;
  capture-pane) printf 'xm $ \n' ;;
  display-message) printf '%s\n' "$CALLER_STATE" ;;
  split-window) touch "$LAUNCHED"; printf '%%viewer\n' ;;
  list-clients)
    [[ "$*" == *'-t =xm-test'* ]] || { printf '/dev/other 1\n'; exit 0; }
    [[ "$CLIENT" == preexisting ]] && printf '/dev/old 0\n'
    if [[ -f "$LAUNCHED" ]]; then
      [[ "$CLIENT" == yes ]] && printf '/dev/ttys001 1\n'
      [[ "$CLIENT" == writable ]] && printf '/dev/ttys001 0\n'
    fi
    exit 0 ;;
esac
STUB
cat >"$TMPROOT/bin/uname" <<'STUB'
#!/bin/bash
printf '%s\n' "$OS"
STUB
cat >"$TMPROOT/bin/osascript" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$LOG"
[[ "$OSASCRIPT_OK" == yes ]] || exit 1
touch "$LAUNCHED"
STUB
cat >"$TMPROOT/bin/gnome-terminal" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$LOG"
touch "$LAUNCHED"
STUB
cat >"$TMPROOT/tmup/scripts/sync-codex-agents.sh" <<'STUB'
#!/bin/bash
exit 0
STUB
chmod +x "$TMPROOT/bin/tmux" "$TMPROOT/bin/uname" "$TMPROOT/bin/osascript" "$TMPROOT/bin/gnome-terminal"

run_case() {
  local name="$1" expected="$2" mode="$3" os="$4" client="$5" osa="$6" tmux_env="$7" pane="$8" ssh="$9" caller="${10:-1 1}" display="${11:-}"
  local rc
  : >"$TMPROOT/log"
  rm -f "$TMPROOT/launched"
  rm -f "$TMPROOT/owner"
  set +e
  env -i PATH="$TMPROOT/bin:/usr/bin:/bin:/opt/homebrew/bin" HOME="$TMPROOT/home" TMPDIR="$TMPROOT" \
    TMUP_PLUGIN_ROOT="$TMPROOT/tmup" LOG="$TMPROOT/log" OS="$os" CLIENT="$client" OSASCRIPT_OK="$osa" \
    TMUX="$tmux_env" TMUX_PANE="$pane" SSH_CONNECTION="$ssh" CALLER_STATE="$caller" DISPLAY="$display" LAUNCHED="$TMPROOT/launched" OWNER="$TMPROOT/owner" XM_VIEWER_TIMEOUT_SECONDS=1 \
    /bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" --session-name xm-test --panes 1 >"$TMPROOT/out" 2>"$TMPROOT/err"
  rc=$?
  set -e
  if [[ "$rc" != "$expected" ]]; then
    printf 'FAIL: %s expected exit %s got %s\n' "$name" "$expected" "$rc" >&2
    exit 1
  fi
  if [[ "$expected" == 0 ]]; then
    if ! jq -e --arg mode "$mode" '.ready == true and .visibility.read_only == true and .visibility.mode == $mode and .visibility.attached_clients == 1 and .visibility.client_ttys == ["/dev/ttys001"] and .visibility.session_name == "xm-test"' "$TMPROOT/out" >/dev/null; then
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
    if [[ "$name" == existing || "$name" == foreign || "$name" == collision || "$name" == creation_timeout || "$name" == hung_has ]]; then
      if grep -q 'kill-session' "$TMPROOT/log"; then
        printf 'FAIL: collision killed an unowned session\n' >&2
        exit 1
      fi
      if [[ "$name" == existing ]]; then jq -e '.code == "SESSION_EXISTS"' "$TMPROOT/out" >/dev/null; fi
      if [[ "$name" == foreign ]]; then jq -e '.cleanup_skipped_unowned == true' "$TMPROOT/out" >/dev/null; fi
      if [[ "$name" == creation_timeout ]]; then jq -e '.cleanup_skipped_unowned == true' "$TMPROOT/out" >/dev/null; fi
      if [[ "$name" == hung_has ]]; then jq -e '.ready == false' "$TMPROOT/out" >/dev/null; fi
      if [[ "$name" == collision ]]; then jq -e '.ready == false' "$TMPROOT/out" >/dev/null; fi
    else
      jq -e '.ready == false and .code == "VISIBILITY_UNAVAILABLE"' "$TMPROOT/out" >/dev/null
      grep -q 'kill-session -t =xm-test' "$TMPROOT/log"
    fi
    if [[ "$name" == split_timeout ]]; then
      grep -q 'kill-pane -t %viewer' "$TMPROOT/log"
    fi
  fi
}

grep -q 'crossmodel_tmup_review.*crossmodel_setting\|crossmodel_setting.*crossmodel_tmup_review' "$ROOT/colony/conductor-prompt.md" || { printf 'FAIL: conductor setting key missing\n' >&2; exit 1; }
set +e
/bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" --bad >"$TMPROOT/out" 2>"$TMPROOT/err"
rc=$?
set -e
[[ "$rc" == 2 ]] && jq -e '.ready == false' "$TMPROOT/out" >/dev/null && [[ -s "$TMPROOT/out" ]] || { printf 'FAIL: argument failure must emit JSON\n' >&2; exit 1; }
for option in --session-name --panes; do
  set +e
  /bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" "$option" >"$TMPROOT/out" 2>"$TMPROOT/err"
  rc=$?
  set -e
  [[ "$rc" == 2 && "$(wc -l <"$TMPROOT/out" | tr -d ' ')" == 1 ]] && jq -e '.code == "INVALID_ARGUMENT"' "$TMPROOT/out" >/dev/null || { printf 'FAIL: missing option value must emit JSON\n' >&2; exit 1; }
done
mkdir "$TMPROOT/empty-path"
set +e
env -i PATH="$TMPROOT/empty-path" /bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" --session-name xm-test --panes 1 >"$TMPROOT/out" 2>"$TMPROOT/err"
rc=$?
set -e
[[ "$rc" == 2 && ! -s "$TMPROOT/out" ]] && grep -q 'jq is required' "$TMPROOT/err" || { printf 'FAIL: missing jq\n' >&2; exit 1; }
set +e
XM_VIEWER_TIMEOUT_SECONDS=invalid /bin/bash "$ROOT/scripts/crossmodel-grid-up.sh" --session-name xm-test --panes 1 >"$TMPROOT/out" 2>"$TMPROOT/err"
rc=$?
set -e
[[ "$rc" == 2 && "$(wc -l <"$TMPROOT/out" | tr -d ' ')" == 1 ]] && jq -e '.code == "INVALID_TIMEOUT"' "$TMPROOT/out" >/dev/null || { printf 'FAIL: invalid timeout\n' >&2; exit 1; }
run_case split 0 split-pane Linux yes yes /tmp/socket,1,0 %0 ''
run_case mac 0 new-window Darwin yes yes '' '' ''
run_case unavailable 2 '' Linux no yes '' '' ''
run_case timeout 2 '' Darwin no yes '' '' ''
run_case split_timeout 2 '' Linux no yes /tmp/socket,1,0 %0 ''
run_case launch_failure 2 '' Darwin yes no '' '' ''
run_case ssh 2 '' Darwin yes yes '' '' remote
run_case preexisting 2 '' Darwin preexisting yes '' '' ''
run_case writable 2 '' Darwin writable yes '' '' ''
run_case detached 2 '' Linux yes yes /tmp/socket,1,0 %0 '' '0 1'
run_case inactive 2 '' Linux yes yes /tmp/socket,1,0 %0 '' '1 0'
run_case gnome 0 new-window Linux yes yes '' '' '' '1 1' :0
run_case gnome_no_client 2 '' Linux no yes '' '' '' '1 1' :0
run_case collision 2 '' Linux collision yes '' '' ''
run_case existing 2 '' Linux existing yes '' '' ''
run_case hung_has 2 '' Linux hung_has yes '' '' ''
run_case foreign 2 '' Linux foreign yes '' '' ''
run_case creation_timeout 2 '' Linux creation_timeout yes '' '' ''
ROOT="$ROOT" TMPROOT="$TMPROOT" python3 - <<'PY'
import json, os, pathlib, signal, subprocess, time
root = pathlib.Path(os.environ['ROOT'])
tmp = pathlib.Path(os.environ['TMPROOT'])
for sig in (signal.SIGINT, signal.SIGTERM):
    for name in ('launched', 'owner'):
        (tmp / name).unlink(missing_ok=True)
    (tmp / 'log').write_text('')
    env = dict(PATH=f"{tmp}/bin:/usr/bin:/bin:/opt/homebrew/bin", HOME=str(tmp / 'home'), TMPDIR=str(tmp),
               TMUP_PLUGIN_ROOT=str(tmp / 'tmup'), LOG=str(tmp / 'log'), OS='Linux', CLIENT='no',
               OSASCRIPT_OK='yes', TMUX='/tmp/socket,1,0', TMUX_PANE='%0', SSH_CONNECTION='',
               CALLER_STATE='1 1', DISPLAY='', LAUNCHED=str(tmp / 'launched'), OWNER=str(tmp / 'owner'),
               XM_VIEWER_TIMEOUT_SECONDS='5')
    proc = subprocess.Popen(['/bin/bash', str(root / 'scripts/crossmodel-grid-up.sh'), '--session-name', 'xm-test', '--panes', '1'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 10
        while not (tmp / 'launched').exists() and time.monotonic() < deadline:
            time.sleep(.05)
        assert (tmp / 'launched').exists(), 'viewer did not launch'
        proc.send_signal(sig)
        out, err = proc.communicate(timeout=15)
        assert len(out.splitlines()) == 1 and json.loads(out)['ready'] is False, (sig, out, err)
        assert 'kill-session -t =xm-test' in (tmp / 'log').read_text(), sig
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
PY
if command -v tmux >/dev/null 2>&1; then
  socket="xm-test-$$"
  tmux -L "$socket" new-session -d -s xm-real
  tmux -L "$socket" set-option -t '=xm-real:' @xm_owner token
  [[ "$(tmux -L "$socket" show-options -v -t '=xm-real:' @xm_owner)" == token ]]
  tmux -L "$socket" kill-session -t '=xm-real'
  if tmux -L "$socket" has-session -t '=xm-real' 2>/dev/null; then
    printf 'FAIL: real tmux session survived cleanup\n' >&2
    tmux -L "$socket" kill-server 2>/dev/null || true
    exit 1
  fi
  tmux -L "$socket" kill-server 2>/dev/null || true
  printf 'REAL_TMUX_CHECK_PASS\n'
else
  printf 'REAL_TMUX_CHECK_SKIPPED: tmux unavailable\n'
fi
printf 'CROSSMODEL_GRID_UP_TESTS_PASS\n'
