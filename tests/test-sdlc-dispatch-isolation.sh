#!/bin/bash
set -euo pipefail

umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
DISPATCH_TEST_SOURCE="$SCRIPT_DIR/test-sdlc-dispatch.sh"
SOURCE_VALIDATOR="$SOURCE_ROOT/hooks/validators/safety-constraints.sh"
INSTALLED_ROOT="${SDLC_INSTALLED_PLUGIN_ROOT:-$HOME/.claude/plugins/sdlc-os}"
INSTALLED_VALIDATOR="$INSTALLED_ROOT/hooks/validators/safety-constraints.sh"
CHILD_PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PYTHON_BIN="${PYTHON_BIN:-}"
TEMP_TREE_HELPER="$SCRIPT_DIR/lib/f01-temp-tree.py"
OUTER_ROOT=""
OUTER_ROOT_PREFIX=""
OUTER_ROOT_TOKEN=""
PRESERVE_OUTER_ROOT=0
CHILD_PID=""
CHILD_PID_A=""
CHILD_PID_B=""

resolve_python_bin() {
  local candidate probe version executable
  candidate="$PYTHON_BIN"
  if [[ -z "$candidate" ]]; then
    if ! candidate="$(command -v python3.12 2>/dev/null)"; then
      return 1
    fi
  fi
  [[ "$candidate" == /* && -x "$candidate" ]] || return 1
  if ! probe="$("$candidate" -c '
import os
import sys

print(f"{sys.version_info.major}.{sys.version_info.minor}")
print(os.path.realpath(sys.executable))
' 2>/dev/null)"; then
    return 1
  fi
  case "$probe" in
    *$'\n'*) ;;
    *) return 1 ;;
  esac
  version="${probe%%$'\n'*}"
  executable="${probe#*$'\n'}"
  [[ "$version" == "3.12" &&
      "$executable" == /* &&
      "$executable" != *$'\n'* &&
      -f "$executable" &&
      ! -L "$executable" &&
      -x "$executable" ]] || return 1
  printf '%s\n' "$executable"
}

if ! PYTHON_BIN="$(resolve_python_bin)"; then
  printf 'F01_FIXTURE_ESCAPE: canonical Python 3.12 is unavailable\n' >&2
  exit 1
fi
if [[ ! -f "$TEMP_TREE_HELPER" || -L "$TEMP_TREE_HELPER" ]]; then
  printf 'F01_TEMP_TREE_HELPER_MISSING:%s\n' "$TEMP_TREE_HELPER" >&2
  exit 1
fi

terminate_pid() {
  local pid="${1:-}"
  [[ -n "$pid" ]] || return 0
  if kill -0 "$pid" 2>/dev/null; then
    if ! kill -TERM "$pid" 2>/dev/null; then
      return 1
    fi
  fi
  set +e
  wait "$pid" 2>/dev/null
  set -e
  return 0
}

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if ! terminate_pid "$CHILD_PID"; then rc=125; fi
  if ! terminate_pid "$CHILD_PID_A"; then rc=125; fi
  if ! terminate_pid "$CHILD_PID_B"; then rc=125; fi
  if [[ "$PRESERVE_OUTER_ROOT" -ne 0 ]]; then
    exit 125
  fi
  if [[ -n "$OUTER_ROOT" ]]; then
    if [[ -z "$OUTER_ROOT_PREFIX" || -z "$OUTER_ROOT_TOKEN" ]] ||
        ! "$PYTHON_BIN" "$TEMP_TREE_HELPER" remove \
          "$OUTER_ROOT" "$OUTER_ROOT_PREFIX" "$OUTER_ROOT_TOKEN"; then
      printf 'CLEANUP_FAILED:%s\n' "$OUTER_ROOT" >&2
      rc=125
    fi
  fi
  exit "$rc"
}

handle_signal() {
  local stop_failed=0
  trap - HUP INT TERM
  if ! terminate_pid "$CHILD_PID"; then stop_failed=1; fi
  if ! terminate_pid "$CHILD_PID_A"; then stop_failed=1; fi
  if ! terminate_pid "$CHILD_PID_B"; then stop_failed=1; fi
  if [[ "$stop_failed" -ne 0 ]]; then
    printf 'CLEANUP_FAILED:unable to terminate retained child\n' >&2
    exit 125
  fi
  printf 'F01_DRIVER_INTERRUPTED\n' >&2
  exit 3
}

trap cleanup EXIT
trap handle_signal HUP INT TERM

fail_fixture() {
  printf 'F01_FIXTURE_ESCAPE:%s\n' "$1" >&2
  exit 1
}

physical_dir() {
  (cd "$1" 2>/dev/null && pwd -P)
}

require_descendant_dir() {
  local root="$1" path="$2" physical
  physical="$(physical_dir "$path")" || fail_fixture "cannot resolve directory $path"
  case "$physical/" in
    "$root"/*) ;;
    *) fail_fixture "directory escaped outer root: $path" ;;
  esac
  printf '%s\n' "$physical"
}

require_regular_file() {
  local path="$1"
  [[ -f "$path" && ! -L "$path" ]] || fail_fixture "regular non-symlink file required: $path"
}

reject_tree_symlinks() {
  local first_link
  first_link="$(find "$@" -type l -print -quit)"
  [[ -z "$first_link" ]] || fail_fixture "copied dependency symlink: $first_link"
}

file_state() {
  "$PYTHON_BIN" - "$1" <<'PY'
import hashlib
import os
import stat
import sys

path = sys.argv[1]
metadata = os.lstat(path)
if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
    raise SystemExit(1)
digest = hashlib.sha256()
with open(path, "rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
print(f"{stat.S_IMODE(metadata.st_mode):04o}\t{metadata.st_size}\t{digest.hexdigest()}")
PY
}

validate_file_state() {
  awk -F '\t' '
    NR == 1 && NF == 3 &&
      length($1) == 4 && $1 ~ /^[0-7][0-7][0-7][0-7]$/ &&
      $2 ~ /^[0-9]+$/ &&
      length($3) == 64 && $3 ~ /^[0-9a-f]+$/ { valid = 1 }
    END { exit !(NR == 1 && valid == 1) }
  ' "$1"
}

emit_validator_fingerprints() {
  local source_digest decoy_digest installed_digest
  source_digest="$(awk -F '\t' 'NR == 1 { print $3 }' \
    "$EVIDENCE_ROOT/source.state.before")"
  decoy_digest="$(awk -F '\t' 'NR == 1 { print $3 }' \
    "$EVIDENCE_ROOT/decoy.state.before")"
  if [[ "$INSTALLED_APPLICABLE" == "1" ]]; then
    installed_digest="$(awk -F '\t' 'NR == 1 { print $3 }' \
      "$EVIDENCE_ROOT/installed.state.before")"
  else
    installed_digest="NOT_APPLICABLE"
  fi
  [[ "$source_digest" =~ ^[0-9a-f]{64}$ ]] ||
    fail_fixture "cannot emit validator fingerprints"
  [[ "$decoy_digest" =~ ^[0-9a-f]{64}$ ]] ||
    fail_fixture "cannot emit validator fingerprints"
  if [[ "$installed_digest" != "NOT_APPLICABLE" ]]; then
    [[ "$installed_digest" =~ ^[0-9a-f]{64}$ ]] ||
      fail_fixture "cannot emit validator fingerprints"
  fi
  printf 'F01_FINGERPRINTS source=%s decoy=%s installed=%s\n' \
    "$source_digest" "$decoy_digest" "$installed_digest"
}

sidecar_inventory() {
  "$PYTHON_BIN" - "$1" <<'PY'
import hashlib
import os
import stat
import sys

validator = os.fsencode(sys.argv[1])
directory = os.path.dirname(validator)
basename = os.path.basename(validator)
entries = sorted(
    (
        entry
        for entry in os.scandir(directory)
        if entry.name != basename and entry.name.startswith(basename)
    ),
    key=lambda entry: entry.name,
)
print("F01_SIDECAR_INVENTORY\t1")
for entry in entries:
    path = entry.path
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        kind = "symlink"
        digest = hashlib.sha256(os.readlink(path)).hexdigest()
    elif stat.S_ISREG(metadata.st_mode):
        kind = "regular"
        value = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                value.update(block)
        digest = value.hexdigest()
    else:
        raise SystemExit(1)
    print(
        f"entry\t{entry.name.hex()}\t{kind}\t"
        f"{stat.S_IMODE(metadata.st_mode):04o}\t{metadata.st_size}\t{digest}"
    )
PY
}

validate_sidecar_inventory() {
  "$PYTHON_BIN" - "$1" <<'PY'
import sys

lines = open(sys.argv[1], "rb").read().splitlines()
if not lines or lines[0] != b"F01_SIDECAR_INVENTORY\t1":
    raise SystemExit(1)

previous = None
for line in lines[1:]:
    fields = line.split(b"\t")
    if len(fields) != 6 or fields[0] != b"entry":
        raise SystemExit(1)
    name_hex, kind, mode, size, digest = fields[1:]
    try:
        name = bytes.fromhex(name_hex.decode("ascii"))
    except (UnicodeDecodeError, ValueError):
        raise SystemExit(1)
    if not name or (previous is not None and name <= previous):
        raise SystemExit(1)
    previous = name
    if len(mode) != 4 or any(byte < 48 or byte > 55 for byte in mode):
        raise SystemExit(1)
    if not size or not size.isdigit():
        raise SystemExit(1)
    if kind not in (b"regular", b"symlink"):
        raise SystemExit(1)
    if len(digest) != 64 or any(
        byte not in b"0123456789abcdef" for byte in digest
    ):
        raise SystemExit(1)
PY
}

snapshot_file() {
  local label="$1" path="$2"
  cp "$path" "$EVIDENCE_ROOT/$label.bytes"
  if ! file_state "$path" >"$EVIDENCE_ROOT/$label.state.before" ||
      ! validate_file_state "$EVIDENCE_ROOT/$label.state.before"; then
    fail_fixture "invalid $label validator fingerprint"
  fi
  if ! sidecar_inventory "$path" >"$EVIDENCE_ROOT/$label.sidecars.before" ||
      ! validate_sidecar_inventory "$EVIDENCE_ROOT/$label.sidecars.before"; then
    fail_fixture "invalid $label sidecar inventory"
  fi
}

verify_file_unchanged() {
  local label="$1" path="$2"
  [[ -f "$path" && ! -L "$path" ]] || return 1
  cmp -s "$EVIDENCE_ROOT/$label.bytes" "$path" || return 1
  file_state "$path" >"$EVIDENCE_ROOT/$label.state.after" || return 1
  validate_file_state "$EVIDENCE_ROOT/$label.state.after" || return 1
  sidecar_inventory "$path" >"$EVIDENCE_ROOT/$label.sidecars.after" || return 1
  validate_sidecar_inventory "$EVIDENCE_ROOT/$label.sidecars.after" || return 1
  cmp -s "$EVIDENCE_ROOT/$label.state.before" "$EVIDENCE_ROOT/$label.state.after" || return 1
  cmp -s "$EVIDENCE_ROOT/$label.sidecars.before" "$EVIDENCE_ROOT/$label.sidecars.after" || return 1
}

verify_protected_state() {
  if ! verify_file_unchanged source "$SOURCE_VALIDATOR"; then
    printf 'F01_FIXTURE_ESCAPE:source validator or sidecar drift\n' >&2
    return 1
  fi
  if ! verify_file_unchanged decoy "$DECOY_VALIDATOR"; then
    printf 'F01_FIXTURE_ESCAPE:decoy validator or sidecar drift\n' >&2
    return 1
  fi
  if [[ "$INSTALLED_APPLICABLE" == "1" ]]; then
    if ! verify_file_unchanged installed "$INSTALLED_VALIDATOR"; then
      printf 'F01_INSTALLED_DRIFT:concurrent installed-tree change; evidence inconclusive\n' >&2
      return 3
    fi
  elif [[ -e "$INSTALLED_VALIDATOR" || -L "$INSTALLED_VALIDATOR" ]]; then
    printf 'F01_INSTALLED_DRIFT:installed applicability changed; evidence inconclusive\n' >&2
    return 3
  fi
  if [[ "${F01_TEST_INSTALLED_DRIFT:-}" == "synthetic" ]]; then
    printf 'F01_INSTALLED_DRIFT:synthetic installed-tree drift; evidence inconclusive\n' >&2
    return 3
  fi
}

prove_decoy_sidecar_detection() {
  local probe="$DECOY_VALIDATOR~unexpected-probe"
  printf 'sidecar inventory falsifier\n' >"$probe"
  if verify_file_unchanged decoy "$DECOY_VALIDATOR"; then
    if ! rm -f "$probe"; then
      fail_fixture "cannot remove decoy sidecar probe"
    fi
    fail_fixture "decoy sidecar drift detector false pass"
  fi
  if ! rm -f "$probe"; then
    fail_fixture "cannot remove decoy sidecar probe"
  fi
  if ! verify_file_unchanged decoy "$DECOY_VALIDATOR"; then
    fail_fixture "decoy sidecar state did not recover after probe"
  fi
}

run_concurrent() {
  local base_tmp root_a root_b rc_a rc_b count_a count_b lines_a lines_b
  if [[ -n "${F01_TEST_SIGNAL:-}" ]]; then
    printf 'concurrent mode does not accept F01_TEST_SIGNAL\n' >&2
    return 64
  fi
  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  OUTER_ROOT="$(mktemp -d "$base_tmp/sdlc-f01-concurrent.XXXXXX")"
  OUTER_ROOT="$(physical_dir "$OUTER_ROOT")" || fail_fixture "cannot resolve concurrent root"
  OUTER_ROOT_PREFIX="sdlc-f01-concurrent."
  OUTER_ROOT_TOKEN="$(capture_temp_tree "$OUTER_ROOT" "$OUTER_ROOT_PREFIX")" ||
    fail_fixture "cannot capture concurrent root"
  mkdir -p "$OUTER_ROOT/a-tmp" "$OUTER_ROOT/b-tmp"
  root_a="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/a-tmp")"
  root_b="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/b-tmp")"
  [[ "$root_a" != "$root_b" ]] || fail_fixture "concurrent roots alias"

  if [[ -n "${F01_TEST_CONCURRENT_OUTCOMES:-}" ]]; then
    case "$F01_TEST_CONCURRENT_OUTCOMES" in
      1,3)
        rc_a=1
        rc_b=3
        ;;
      *) return 64 ;;
    esac
  else
    F01_TEST_MODE=assert \
      F01_TEST_SIGNAL='' \
      TMPDIR="$root_a" \
      SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
      /bin/bash "$SCRIPT_PATH" >"$OUTER_ROOT/a.stdout" 2>"$OUTER_ROOT/a.stderr" &
    CHILD_PID_A=$!
    F01_TEST_MODE=assert \
      F01_TEST_SIGNAL='' \
      TMPDIR="$root_b" \
      SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
      /bin/bash "$SCRIPT_PATH" >"$OUTER_ROOT/b.stdout" 2>"$OUTER_ROOT/b.stderr" &
    CHILD_PID_B=$!

    set +e
    wait "$CHILD_PID_A"
    rc_a=$?
    CHILD_PID_A=""
    wait "$CHILD_PID_B"
    rc_b=$?
    CHILD_PID_B=""
    set -e
  fi

  if [[ ("$rc_a" -ne 0 && "$rc_a" -ne 3) ||
        ("$rc_b" -ne 0 && "$rc_b" -ne 3) ]]; then
    printf 'concurrent driver failed: child_a=%s child_b=%s\n' "$rc_a" "$rc_b" >&2
    return 1
  fi
  if [[ "$rc_a" -eq 3 || "$rc_b" -eq 3 ]]; then
    printf 'F01_INSTALLED_DRIFT:concurrent child evidence inconclusive\n' >&2
    return 3
  fi
  count_a="$(awk '$0 == "F01 isolation PASS mode=assert" { count++ } END { print count + 0 }' "$OUTER_ROOT/a.stdout")"
  count_b="$(awk '$0 == "F01 isolation PASS mode=assert" { count++ } END { print count + 0 }' "$OUTER_ROOT/b.stdout")"
  lines_a="$(awk 'END { print NR + 0 }' "$OUTER_ROOT/a.stdout")"
  lines_b="$(awk 'END { print NR + 0 }' "$OUTER_ROOT/b.stdout")"
  [[ "$count_a" -eq 1 && "$count_b" -eq 1 &&
      "$lines_a" -eq 1 && "$lines_b" -eq 1 ]] || {
    printf 'concurrent driver pass marker mismatch\n' >&2
    return 1
  }
  [[ ! -s "$OUTER_ROOT/a.stderr" && ! -s "$OUTER_ROOT/b.stderr" ]] || {
    printf 'concurrent driver emitted unexpected stderr\n' >&2
    return 1
  }
  printf 'F01 isolation PASS mode=concurrent\n'
}

capture_temp_tree() {
  "$PYTHON_BIN" "$TEMP_TREE_HELPER" capture "$1" "$2"
}

remove_temp_tree() {
  "$PYTHON_BIN" "$TEMP_TREE_HELPER" remove "$1" "$2" "$3"
}

verify_no_recursive_cleanup() {
  "$PYTHON_BIN" - "$SCRIPT_PATH" "$DISPATCH_TEST_SOURCE" <<'PY'
import re
import shlex
import sys

rm_command = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:/[A-Za-z0-9_./-]*/)?rm(?=\s)"
)
indirect_command = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:eval|(?:/bin/)?(?:ba)?sh\s+-c)(?=\s|$)"
)
heredoc_start = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

for raw_path in sys.argv[1:]:
    lines = open(raw_path, encoding="utf-8").read().replace("\\\n", " ").splitlines()
    marker = None
    for number, line in enumerate(lines, 1):
        if marker is not None:
            if line.strip() == marker:
                marker = None
            continue
        start = heredoc_start.search(line)
        shell_line = line if start is None else line[: start.start()]
        if start is not None:
            marker = start.group(2)
        stripped = shell_line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if indirect_command.search(shell_line):
            print(f"INDIRECT_CLEANUP_COMMAND:{raw_path}:{number}", file=sys.stderr)
            raise SystemExit(1)
        for match in rm_command.finditer(shell_line):
            tail = shell_line[match.end() :]
            tail = re.split(r"(?:&&|\|\||[;|&])", tail, maxsplit=1)[0]
            try:
                arguments = shlex.split(tail, posix=True)
            except ValueError:
                print(f"CLEANUP_SOURCE_UNPARSEABLE:{raw_path}:{number}", file=sys.stderr)
                raise SystemExit(1)
            for argument in arguments:
                recursive = argument == "--recursive" or (
                    argument.startswith("-")
                    and not argument.startswith("--")
                    and any(flag in argument[1:] for flag in "rR")
                )
                if recursive:
                    print(f"RECURSIVE_CLEANUP_COMMAND:{raw_path}:{number}", file=sys.stderr)
                    raise SystemExit(1)
PY
}

run_cleanup_retarget() (
  local base_tmp controller controller_token ancestor_root ancestor_token
  local victim_root ancestor_rc swap_parent swap_root swap_leaf swap_token
  local replacement_root swap_rc duplicate_root duplicate_token duplicate_rc duplicate_stderr
  local missing_outer_root missing_outer_tmp missing_outer_rc missing_outer_residue
  local missing_inner_root missing_inner_tmp missing_inner_rc missing_inner_residue cleanup_rc
  if [[ ! -f "$TEMP_TREE_HELPER" || -L "$TEMP_TREE_HELPER" ]]; then
    printf 'F01_TEMP_TREE_HELPER_MISSING:%s\n' "$TEMP_TREE_HELPER" >&2
    return 1
  fi

  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  controller="$(mktemp -d "$base_tmp/sdlc-f01-cleanup-controller.XXXXXX")"
  controller="$(physical_dir "$controller")" || fail_fixture "cannot resolve cleanup controller"
  controller_token="$(capture_temp_tree "$controller" sdlc-f01-cleanup-controller.)" || {
    printf 'CLEANUP_FAILED:cannot capture cleanup controller %s\n' "$controller" >&2
    return 125
  }

  # Invoked by the EXIT trap below.
  # shellcheck disable=SC2329
  cleanup_retarget_controller() {
    cleanup_rc=$?
    trap - EXIT
    if [[ -n "$controller" ]]; then
      if ! remove_temp_tree "$controller" sdlc-f01-cleanup-controller. "$controller_token"; then
        printf 'CLEANUP_FAILED:%s\n' "$controller" >&2
        exit 125
      fi
    fi
    exit "$cleanup_rc"
  }
  trap cleanup_retarget_controller EXIT

  missing_outer_root="$controller/missing-outer"
  missing_outer_tmp="$controller/missing-outer-tmp"
  mkdir -p "$missing_outer_root/tests" "$missing_outer_tmp"
  cp "$SCRIPT_PATH" "$missing_outer_root/tests/test-sdlc-dispatch-isolation.sh"
  set +e
  PYTHON_BIN="$PYTHON_BIN" \
    F01_TEST_MODE=assert \
    TMPDIR="$missing_outer_tmp" \
    SDLC_INSTALLED_PLUGIN_ROOT="$controller/no-installed-plugin" \
    /bin/bash "$missing_outer_root/tests/test-sdlc-dispatch-isolation.sh" \
    >"$controller/missing-outer.stdout" 2>"$controller/missing-outer.stderr"
  missing_outer_rc=$?
  set -e
  [[ "$missing_outer_rc" -eq 1 ]] || fail_fixture "missing outer helper exit mismatch"
  [[ ! -s "$controller/missing-outer.stdout" ]] ||
    fail_fixture "missing outer helper emitted stdout"
  [[ "$(grep -c '^F01_TEMP_TREE_HELPER_MISSING:' \
      "$controller/missing-outer.stderr")" -eq 1 ]] ||
    fail_fixture "missing outer helper code mismatch"
  missing_outer_residue="$(find "$missing_outer_tmp" \
    -mindepth 1 -maxdepth 1 -print -quit)"
  [[ -z "$missing_outer_residue" ]] ||
    fail_fixture "missing outer helper created temporary state"

  missing_inner_root="$controller/missing-inner"
  missing_inner_tmp="$controller/missing-inner-tmp"
  mkdir -p \
    "$missing_inner_root/tests/lib" \
    "$missing_inner_root/.claude-plugin" \
    "$missing_inner_root/hooks" \
    "$missing_inner_tmp"
  cp "$DISPATCH_TEST_SOURCE" "$missing_inner_root/tests/test-sdlc-dispatch.sh"
  cp "$SOURCE_ROOT/tests/lib/plugin-root.sh" "$missing_inner_root/tests/lib/plugin-root.sh"
  cp "$SOURCE_ROOT/.claude-plugin/plugin.json" \
    "$missing_inner_root/.claude-plugin/plugin.json"
  set +e
  CLAUDE_PLUGIN_ROOT="$missing_inner_root" \
    PYTHON_BIN="$PYTHON_BIN" \
    TMPDIR="$missing_inner_tmp" \
    /bin/bash "$missing_inner_root/tests/test-sdlc-dispatch.sh" \
    >"$controller/missing-inner.stdout" 2>"$controller/missing-inner.stderr"
  missing_inner_rc=$?
  set -e
  [[ "$missing_inner_rc" -eq 1 ]] || fail_fixture "missing inner helper exit mismatch"
  [[ ! -s "$controller/missing-inner.stdout" ]] ||
    fail_fixture "missing inner helper emitted stdout"
  [[ "$(grep -c '^F01_TEMP_TREE_HELPER_MISSING:' \
      "$controller/missing-inner.stderr")" -eq 1 ]] ||
    fail_fixture "missing inner helper code mismatch"
  missing_inner_residue="$(find "$missing_inner_tmp" \
    -mindepth 1 -maxdepth 1 -print -quit)"
  [[ -z "$missing_inner_residue" ]] ||
    fail_fixture "missing inner helper created temporary state"

  duplicate_root="$controller/duplicate-token/sdlc-f01-retarget.root"
  mkdir -p "$duplicate_root"
  printf 'duplicate token sentinel\n' >"$duplicate_root/sentinel"
  duplicate_token="$(capture_temp_tree "$duplicate_root" sdlc-f01-retarget.)"
  duplicate_token="$("$PYTHON_BIN" - "$duplicate_token" <<'PY'
import sys

raw = sys.argv[1]
if not raw.startswith("{"):
    raise SystemExit(1)
print('{"schema_version":"f01-temp-tree-token-v1",' + raw[1:])
PY
)"
  set +e
  remove_temp_tree "$duplicate_root" sdlc-f01-retarget. "$duplicate_token" \
    >"$controller/duplicate-token.stdout" 2>"$controller/duplicate-token.stderr"
  duplicate_rc=$?
  set -e
  [[ "$duplicate_rc" -eq 1 ]] || fail_fixture "duplicate token key was accepted"
  [[ ! -s "$controller/duplicate-token.stdout" ]] ||
    fail_fixture "duplicate token emitted stdout"
  duplicate_stderr="$(<"$controller/duplicate-token.stderr")"
  [[ "$duplicate_stderr" == "F01_TEMP_TREE_RETAINED:token-duplicate-key" ]] ||
    fail_fixture "duplicate token error mismatch"
  [[ -f "$duplicate_root/sentinel" ]] ||
    fail_fixture "duplicate token removed retained sentinel"

  mkdir -p \
    "$controller/ancestor/sdlc-f01-retarget.root" \
    "$controller/victim/sdlc-f01-retarget.root"
  ancestor_root="$controller/ancestor/sdlc-f01-retarget.root"
  victim_root="$controller/victim/sdlc-f01-retarget.root"
  printf 'original sentinel\n' >"$ancestor_root/original.sentinel"
  printf 'victim sentinel\n' >"$victim_root/victim.sentinel"
  ancestor_token="$(capture_temp_tree "$ancestor_root" sdlc-f01-retarget.)"
  mv "$controller/ancestor" "$controller/original-ancestor"
  mv "$controller/victim" "$controller/ancestor"
  set +e
  remove_temp_tree \
    "$controller/ancestor/sdlc-f01-retarget.root" \
    sdlc-f01-retarget. \
    "$ancestor_token" \
    >"$controller/ancestor.stdout" 2>"$controller/ancestor.stderr"
  ancestor_rc=$?
  set -e
  [[ "$ancestor_rc" -ne 0 ]] || fail_fixture "ancestor retarget was accepted"
  [[ -f "$controller/original-ancestor/sdlc-f01-retarget.root/original.sentinel" ]] ||
    fail_fixture "ancestor retarget removed original sentinel"
  [[ -f "$controller/ancestor/sdlc-f01-retarget.root/victim.sentinel" ]] ||
    fail_fixture "ancestor retarget removed victim sentinel"

  swap_parent="$controller/root-swap"
  swap_leaf="sdlc-f01-retarget.root"
  swap_root="$swap_parent/$swap_leaf"
  replacement_root="$swap_root.replacement"
  mkdir -p "$swap_root" "$replacement_root"
  printf 'opened original sentinel\n' >"$swap_root/original.sentinel"
  printf 'replacement sentinel\n' >"$replacement_root/replacement.sentinel"
  swap_token="$(capture_temp_tree "$swap_root" sdlc-f01-retarget.)"
  set +e
  F01_TEMP_TREE_TEST_POST_OPEN_SWAP=1 \
    remove_temp_tree "$swap_root" sdlc-f01-retarget. "$swap_token" \
    >"$controller/root-swap.stdout" 2>"$controller/root-swap.stderr"
  swap_rc=$?
  set -e
  [[ "$swap_rc" -ne 0 ]] || fail_fixture "post-open root replacement was accepted"
  [[ -f "$swap_root/replacement.sentinel" ]] ||
    fail_fixture "post-open root swap removed replacement sentinel"
  [[ -d "$swap_root.opened-original" ]] ||
    fail_fixture "post-open root swap lost captured original directory"
  [[ -f "$swap_root.opened-original/original.sentinel" ]] ||
    fail_fixture "post-open root swap removed original sentinel"

  verify_no_recursive_cleanup
  printf 'F01 isolation PASS mode=cleanup-retarget\n'
)

run_restore_failure() (
  local base_tmp controller controller_token cleanup_rc
  if [[ -n "${F01_TEST_SIGNAL:-}" ]]; then
    printf 'restore-failure mode does not accept F01_TEST_SIGNAL\n' >&2
    return 64
  fi
  require_regular_file "$TEMP_TREE_HELPER"
  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  controller="$(mktemp -d "$base_tmp/sdlc-f01-restore-controller.XXXXXX")"
  controller="$(physical_dir "$controller")" || fail_fixture "cannot resolve restore controller"
  controller_token="$(capture_temp_tree "$controller" sdlc-f01-restore-controller.)" ||
    fail_fixture "cannot capture restore controller"

  # Invoked by the EXIT trap below.
  # shellcheck disable=SC2329
  cleanup_restore_controller() {
    cleanup_rc=$?
    trap - EXIT
    if [[ -n "$controller" ]]; then
      if ! remove_temp_tree "$controller" sdlc-f01-restore-controller. "$controller_token"; then
        printf 'CLEANUP_FAILED:%s\n' "$controller" >&2
        exit 125
      fi
    fi
    exit "$cleanup_rc"
  }
  trap cleanup_restore_controller EXIT

  prove_restore_failure() {
    local selector="$1" label="$2" child_rc retained_count retained_outer
    local retained_token fixture_count fixture_root inner_root protected_rc
    local stdout_file="$controller/$label.stdout"
    local stderr_file="$controller/$label.stderr"

    set +e
    F01_TEST_MODE=assert \
      F01_TEST_SIGNAL='' \
      F01_TEST_RESTORE_FAILURE="$selector" \
      TMPDIR="$controller" \
      SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
      /bin/bash "$SCRIPT_PATH" \
      >"$stdout_file" 2>"$stderr_file"
    child_rc=$?
    set -e
    [[ "$child_rc" -eq 125 ]] || {
      printf '%s child exit mismatch: expected=125 actual=%s\n' \
        "$selector" "$child_rc" >&2
      return 1
    }
    [[ ! -s "$stdout_file" ]] || fail_fixture "$selector child emitted stdout"
    retained_count="$(awk '/^F01_RESTORE_RETAINED:/ { count++ } END { print count + 0 }' \
      "$stderr_file")"
    [[ "$retained_count" -eq 1 ]] ||
      fail_fixture "$selector retained marker count $retained_count"
    retained_outer="$(sed -n 's/^F01_RESTORE_RETAINED://p' "$stderr_file")"
    case "$retained_outer" in
      "$controller"/sdlc-f01.*) ;;
      *) fail_fixture "$selector retained outer path escaped controller" ;;
    esac
    retained_token="$(capture_temp_tree "$retained_outer" sdlc-f01.)" ||
      fail_fixture "$selector cannot capture retained outer root"
    if ! "$PYTHON_BIN" - "$controller_token" "$retained_token" <<'PY'
import json
import sys

controller = json.loads(sys.argv[1])
retained = json.loads(sys.argv[2])
if (retained["parent_dev"], retained["parent_ino"]) != (
    controller["root_dev"],
    controller["root_ino"],
):
    raise SystemExit(1)
PY
    then
      fail_fixture "$selector retained outer parent identity mismatch"
    fi

    fixture_count="$(awk '/^F01_RESTORE_FAILED:/ { count++ } END { print count + 0 }' \
      "$retained_outer/evidence/child.stderr")"
    [[ "$fixture_count" -eq 1 ]] ||
      fail_fixture "$selector restore failure marker count $fixture_count"
    fixture_root="$(sed -n 's/^F01_RESTORE_FAILED://p' \
      "$retained_outer/evidence/child.stderr")"
    inner_root="${fixture_root%/fixture}"
    case "$inner_root" in
      "$retained_outer"/runtime/sdlc-dispatch-test.*) ;;
      *) fail_fixture "$selector retained inner path escaped outer runtime" ;;
    esac
    [[ -d "$inner_root" && ! -L "$inner_root" && -d "$fixture_root" ]] ||
      fail_fixture "$selector retained inner fixture is missing"

    EVIDENCE_ROOT="$retained_outer/evidence"
    DECOY_ROOT="$retained_outer/decoy"
    DECOY_VALIDATOR="$DECOY_ROOT/hooks/validators/safety-constraints.sh"
    if [[ -f "$EVIDENCE_ROOT/installed.bytes" ]]; then
      INSTALLED_APPLICABLE=1
    else
      INSTALLED_APPLICABLE=0
    fi
    set +e
    verify_protected_state
    protected_rc=$?
    set -e
    [[ "$protected_rc" -eq 0 ]] || return "$protected_rc"

    if ! remove_temp_tree "$retained_outer" sdlc-f01. "$retained_token"; then
      fail_fixture "$selector cannot remove retained outer root"
    fi
    rm -f "$stdout_file" "$stderr_file"
    if ! "$PYTHON_BIN" - "$controller" <<'PY'
import os
import sys

if os.listdir(sys.argv[1]):
    raise SystemExit(1)
PY
    then
      fail_fixture "$selector restore controller contains unexpected entries"
    fi
  }

  prove_restore_failure after-backup-move baseline-mismatch
  prove_restore_failure remove-backup missing-backup
  printf 'F01 isolation PASS mode=restore-failure\n'
)

run_signal_wrapper_negative() (
  local base_tmp controller controller_token negative_rc foreground_rc cleanup_rc
  local negative_stderr foreground_stdout
  if [[ -n "${F01_TEST_SIGNAL:-}" ]]; then
    printf 'signal-wrapper-negative mode does not accept F01_TEST_SIGNAL\n' >&2
    return 64
  fi
  require_regular_file "$TEMP_TREE_HELPER"
  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  controller="$(mktemp -d "$base_tmp/sdlc-f01-signal-controller.XXXXXX")"
  controller="$(physical_dir "$controller")" || fail_fixture "cannot resolve signal controller"
  controller_token="$(capture_temp_tree "$controller" sdlc-f01-signal-controller.)" ||
    fail_fixture "cannot capture signal controller"

  # Invoked by the EXIT trap below.
  # shellcheck disable=SC2329
  cleanup_signal_controller() {
    cleanup_rc=$?
    trap - EXIT
    if [[ -n "$controller" ]]; then
      if ! remove_temp_tree "$controller" sdlc-f01-signal-controller. "$controller_token"; then
        printf 'CLEANUP_FAILED:%s\n' "$controller" >&2
        exit 125
      fi
    fi
    exit "$cleanup_rc"
  }
  trap cleanup_signal_controller EXIT

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_SIGNAL=INT \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/background.stdout" 2>"$controller/background.stderr" &
  CHILD_PID=$!
  wait "$CHILD_PID"
  negative_rc=$?
  CHILD_PID=""
  set -e
  [[ "$negative_rc" -eq 1 ]] || {
    printf 'background INT negative exit mismatch: expected=1 actual=%s\n' "$negative_rc" >&2
    return 1
  }
  [[ ! -s "$controller/background.stdout" ]] ||
    fail_fixture "background INT negative emitted stdout"
  negative_stderr="$(<"$controller/background.stderr")"
  [[ "$negative_stderr" == "failpoint child exit mismatch: expected=130 actual=125" ]] ||
    fail_fixture "background INT negative signature mismatch"

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_SIGNAL=INT \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/foreground.stdout" 2>"$controller/foreground.stderr"
  foreground_rc=$?
  set -e
  [[ "$foreground_rc" -eq 0 ]] || {
    printf 'foreground INT exit mismatch: expected=0 actual=%s\n' "$foreground_rc" >&2
    return 1
  }
  foreground_stdout="$(<"$controller/foreground.stdout")"
  [[ "$foreground_stdout" == "F01 isolation PASS mode=assert signal=INT launch=foreground" ]] ||
    fail_fixture "foreground INT launch marker mismatch"
  [[ ! -s "$controller/foreground.stderr" ]] ||
    fail_fixture "foreground INT emitted stderr"

  rm -f \
    "$controller/background.stdout" \
    "$controller/background.stderr" \
    "$controller/foreground.stdout" \
    "$controller/foreground.stderr"
  printf 'F01 isolation PASS mode=signal-wrapper-negative\n'
)

run_admission_negative() (
  local base_tmp controller controller_token child_rc child_stderr
  local concurrent_rc concurrent_stderr cleanup_rc drift_rc drift_stderr
  local framing_rc framing_stderr
  local expected_drift_stderr
  local outer_root_rc moved_root moved_token
  local capture_rc retained_count retained_outer retained_token inner_root
  if [[ -n "${F01_TEST_SIGNAL:-}" ]]; then
    printf 'admission-negative mode does not accept F01_TEST_SIGNAL\n' >&2
    return 64
  fi
  require_regular_file "$TEMP_TREE_HELPER"
  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  controller="$(mktemp -d "$base_tmp/sdlc-f01-admission-controller.XXXXXX")"
  controller="$(physical_dir "$controller")" || fail_fixture "cannot resolve admission controller"
  controller_token="$(capture_temp_tree "$controller" sdlc-f01-admission-controller.)" ||
    fail_fixture "cannot capture admission controller"

  # Invoked by the EXIT trap below.
  # shellcheck disable=SC2329
  cleanup_admission_controller() {
    cleanup_rc=$?
    trap - EXIT
    if [[ -n "$controller" ]]; then
      if ! remove_temp_tree "$controller" sdlc-f01-admission-controller. "$controller_token"; then
        printf 'CLEANUP_FAILED:%s\n' "$controller" >&2
        exit 125
      fi
    fi
    exit "$cleanup_rc"
  }
  trap cleanup_admission_controller EXIT

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_SIGNAL='' \
    F01_TEST_PRE_FAILPOINT_FAILURE=synthetic \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/child.stdout" 2>"$controller/child.stderr"
  child_rc=$?
  set -e
  [[ "$child_rc" -eq 1 ]] || {
    printf 'pre-failpoint negative exit mismatch: expected=1 actual=%s\n' \
      "$child_rc" >&2
    return 1
  }
  [[ ! -s "$controller/child.stdout" ]] ||
    fail_fixture "pre-failpoint negative emitted stdout"
  child_stderr="$(<"$controller/child.stderr")"
  [[ "$child_stderr" == "F01_FAILPOINT_NOT_REACHED marker_count=0 child_exit=1" ]] ||
    fail_fixture "pre-failpoint negative signature mismatch"
  rm -f "$controller/child.stdout" "$controller/child.stderr"

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_SIGNAL='' \
    F01_TEST_PRE_FAILPOINT_FAILURE=synthetic \
    F01_TEST_INSTALLED_DRIFT=synthetic \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/drift.stdout" 2>"$controller/drift.stderr"
  drift_rc=$?
  set -e
  [[ "$drift_rc" -eq 1 ]] || {
    printf 'installed-drift precedence exit mismatch: expected=1 actual=%s\n' \
      "$drift_rc" >&2
    return 1
  }
  [[ ! -s "$controller/drift.stdout" ]] ||
    fail_fixture "installed-drift precedence negative emitted stdout"
  drift_stderr="$(<"$controller/drift.stderr")"
  expected_drift_stderr="$(printf '%s\n%s' \
    'F01_INSTALLED_DRIFT:synthetic installed-tree drift; evidence inconclusive' \
    'F01_FAILPOINT_NOT_REACHED marker_count=0 child_exit=1')"
  [[ "$drift_stderr" == "$expected_drift_stderr" ]] ||
    fail_fixture "installed-drift precedence signature mismatch"
  rm -f "$controller/drift.stdout" "$controller/drift.stderr"

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_SIGNAL='' \
    F01_TEST_CHILD_STDERR_SUFFIX=blank-line \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/framing.stdout" 2>"$controller/framing.stderr"
  framing_rc=$?
  set -e
  [[ "$framing_rc" -eq 1 ]] || {
    printf 'stderr framing exit mismatch: expected=1 actual=%s\n' \
      "$framing_rc" >&2
    return 1
  }
  [[ ! -s "$controller/framing.stdout" ]] ||
    fail_fixture "stderr framing negative emitted stdout"
  framing_stderr="$(<"$controller/framing.stderr")"
  [[ "$framing_stderr" == "failpoint child stderr mismatch" ]] ||
    fail_fixture "stderr framing negative signature mismatch"
  rm -f "$controller/framing.stdout" "$controller/framing.stderr"

  set +e
  F01_TEST_MODE=concurrent \
    F01_TEST_CONCURRENT_OUTCOMES=1,3 \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/concurrent.stdout" 2>"$controller/concurrent.stderr"
  concurrent_rc=$?
  set -e
  [[ "$concurrent_rc" -eq 1 ]] || {
    printf 'concurrent aggregate exit mismatch: expected=1 actual=%s\n' \
      "$concurrent_rc" >&2
    return 1
  }
  [[ ! -s "$controller/concurrent.stdout" ]] ||
    fail_fixture "concurrent aggregate negative emitted stdout"
  concurrent_stderr="$(<"$controller/concurrent.stderr")"
  [[ "$concurrent_stderr" == "concurrent driver failed: child_a=1 child_b=3" ]] ||
    fail_fixture "concurrent aggregate negative signature mismatch"
  rm -f "$controller/concurrent.stdout" "$controller/concurrent.stderr"

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_OUTER_ROOT_DRIFT=rename \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/outer-root.stdout" 2>"$controller/outer-root.stderr"
  outer_root_rc=$?
  set -e
  [[ "$outer_root_rc" -eq 125 ]] || {
    printf 'outer root drift exit mismatch: expected=125 actual=%s\n' \
      "$outer_root_rc" >&2
    return 1
  }
  [[ ! -s "$controller/outer-root.stdout" ]] ||
    fail_fixture "outer root drift emitted stdout"
  [[ "$(grep -c '^CLEANUP_FAILED:' "$controller/outer-root.stderr")" -eq 1 ]] ||
    fail_fixture "outer root drift cleanup marker mismatch"
  moved_root="$("$PYTHON_BIN" - "$controller" <<'PY'
import os
import stat
import sys

parent = sys.argv[1]
matches = []
for name in os.listdir(parent):
    if not (name.startswith("sdlc-f01.") and name.endswith(".moved")):
        continue
    path = os.path.join(parent, name)
    metadata = os.lstat(path)
    if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
        matches.append(path)
if len(matches) != 1:
    raise SystemExit(1)
print(matches[0])
PY
)" || fail_fixture "outer root drift retained path mismatch"
  moved_token="$(capture_temp_tree "$moved_root" sdlc-f01.)" ||
    fail_fixture "cannot capture moved outer root"
  if ! remove_temp_tree "$moved_root" sdlc-f01. "$moved_token"; then
    fail_fixture "cannot remove moved outer root"
  fi
  rm -f "$controller/outer-root.stdout" "$controller/outer-root.stderr"

  set +e
  F01_TEST_MODE=assert \
    F01_TEST_INNER_CAPTURE_FAILURE=1 \
    TMPDIR="$controller" \
    SDLC_INSTALLED_PLUGIN_ROOT="$INSTALLED_ROOT" \
    /bin/bash "$SCRIPT_PATH" \
    >"$controller/capture.stdout" 2>"$controller/capture.stderr"
  capture_rc=$?
  set -e
  [[ "$capture_rc" -eq 125 ]] || {
    printf 'inner capture retention exit mismatch: expected=125 actual=%s\n' \
      "$capture_rc" >&2
    return 1
  }
  [[ ! -s "$controller/capture.stdout" ]] ||
    fail_fixture "inner capture retention emitted stdout"
  retained_count="$(awk '/^F01_INNER_CONTAINER_RETAINED:/ { count++ } END { print count + 0 }' \
    "$controller/capture.stderr")"
  [[ "$retained_count" -eq 1 ]] ||
    fail_fixture "inner capture retained marker count $retained_count"
  retained_outer="$(sed -n 's/^F01_INNER_CONTAINER_RETAINED://p' \
    "$controller/capture.stderr")"
  case "$retained_outer" in
    "$controller"/sdlc-f01.*) ;;
    *) fail_fixture "inner capture retained outer path escaped controller" ;;
  esac
  retained_token="$(capture_temp_tree "$retained_outer" sdlc-f01.)" ||
    fail_fixture "cannot capture inner-failure outer root"
  inner_root="$("$PYTHON_BIN" - "$retained_outer/runtime" <<'PY'
import os
import stat
import sys

parent = sys.argv[1]
matches = []
for name in os.listdir(parent):
    if not name.startswith("sdlc-dispatch-test."):
        continue
    path = os.path.join(parent, name)
    metadata = os.lstat(path)
    if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
        matches.append(path)
if len(matches) != 1:
    raise SystemExit(1)
print(matches[0])
PY
)" || fail_fixture "inner capture retained root mismatch"
  [[ -d "$inner_root" ]] || fail_fixture "inner capture retained root missing"
  if ! remove_temp_tree "$retained_outer" sdlc-f01. "$retained_token"; then
    fail_fixture "cannot remove inner-failure outer root"
  fi
  rm -f "$controller/capture.stdout" "$controller/capture.stderr"
  printf 'F01 isolation PASS mode=admission-negative\n'
)

run_assert() {
  local base_tmp raw_outer home_root runtime_root project_root manifest_dir
  local marker_count marker child_rc expected_child_exit protected_rc expected_legacy
  local installed_drift=0
  local restore_count restore_marker expected_child_stderr
  local inner_retained_count inner_retained_marker
  case "${F01_TEST_SIGNAL:-}" in
    "") expected_child_exit=1 ;;
    HUP) expected_child_exit=129 ;;
    INT) expected_child_exit=130 ;;
    TERM) expected_child_exit=143 ;;
    *) printf 'invalid F01_TEST_SIGNAL\n' >&2; return 64 ;;
  esac
  case "${F01_TEST_INNER_CAPTURE_FAILURE:-}" in
    ""|1) ;;
    *) return 64 ;;
  esac
  case "${F01_TEST_INSTALLED_DRIFT:-}" in
    ""|synthetic) ;;
    *) return 64 ;;
  esac
  case "${F01_TEST_CHILD_STDERR_SUFFIX:-}" in
    ""|blank-line) ;;
    *) return 64 ;;
  esac
  case "${F01_EMIT_FINGERPRINTS:-}" in
    ""|1) ;;
    *) return 64 ;;
  esac
  if [[ "${F01_TEST_INSTALLED_DRIFT:-}" == "synthetic" &&
        "${F01_TEST_PRE_FAILPOINT_FAILURE:-}" != "synthetic" ]]; then
    return 64
  fi

  base_tmp="${TMPDIR:-/tmp}"
  [[ -d "$base_tmp" ]] || fail_fixture "TMPDIR does not exist: $base_tmp"
  raw_outer="$(mktemp -d "$base_tmp/sdlc-f01.XXXXXX")"
  OUTER_ROOT="$(physical_dir "$raw_outer")" || fail_fixture "cannot resolve outer root"
  OUTER_ROOT_PREFIX="sdlc-f01."
  OUTER_ROOT_TOKEN="$(capture_temp_tree "$OUTER_ROOT" "$OUTER_ROOT_PREFIX")" ||
    fail_fixture "cannot capture outer root"
  mkdir -p \
    "$OUTER_ROOT/home" \
    "$OUTER_ROOT/runtime" \
    "$OUTER_ROOT/project" \
    "$OUTER_ROOT/evidence" \
    "$OUTER_ROOT/decoy/tests/lib" \
    "$OUTER_ROOT/decoy/.claude-plugin"
  home_root="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/home")"
  runtime_root="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/runtime")"
  project_root="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/project")"
  EVIDENCE_ROOT="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/evidence")"
  DECOY_ROOT="$(require_descendant_dir "$OUTER_ROOT" "$OUTER_ROOT/decoy")"
  manifest_dir="$(require_descendant_dir "$OUTER_ROOT" "$DECOY_ROOT/.claude-plugin")"

  require_regular_file "$SCRIPT_PATH"
  require_regular_file "$DISPATCH_TEST_SOURCE"
  require_regular_file "$SOURCE_ROOT/.claude-plugin/plugin.json"
  require_regular_file "$SOURCE_VALIDATOR"
  cp "$DISPATCH_TEST_SOURCE" "$DECOY_ROOT/tests/test-sdlc-dispatch.sh"
  cp "$SOURCE_ROOT/.claude-plugin/plugin.json" "$manifest_dir/plugin.json"
  cp -R "$SOURCE_ROOT/hooks" "$DECOY_ROOT/hooks"
  cp -R "$SOURCE_ROOT/scripts" "$DECOY_ROOT/scripts"
  if [[ -d "$SOURCE_ROOT/tests/lib" ]]; then
    cp -R "$SOURCE_ROOT/tests/lib/." "$DECOY_ROOT/tests/lib/"
  fi
  reject_tree_symlinks \
    "$DECOY_ROOT/hooks" \
    "$DECOY_ROOT/scripts" \
    "$DECOY_ROOT/tests" \
    "$DECOY_ROOT/.claude-plugin"
  require_regular_file "$DECOY_ROOT/.claude-plugin/plugin.json"
  DECOY_VALIDATOR="$DECOY_ROOT/hooks/validators/safety-constraints.sh"
  require_regular_file "$DECOY_VALIDATOR"
  [[ "$SOURCE_ROOT" != "$DECOY_ROOT" ]] || fail_fixture "source and decoy roots alias"
  [[ ! "$SOURCE_VALIDATOR" -ef "$DECOY_VALIDATOR" ]] || fail_fixture "source and decoy validator inodes alias"

  INSTALLED_APPLICABLE=0
  if [[ -e "$INSTALLED_VALIDATOR" || -L "$INSTALLED_VALIDATOR" ]]; then
    if [[ ! -f "$INSTALLED_VALIDATOR" || -L "$INSTALLED_VALIDATOR" ]]; then
      printf 'F01_INSTALLED_DRIFT:installed validator is not a regular non-symlink file\n' >&2
      return 3
    fi
    INSTALLED_APPLICABLE=1
  fi

  snapshot_file source "$SOURCE_VALIDATOR"
  snapshot_file decoy "$DECOY_VALIDATOR"
  if [[ "$INSTALLED_APPLICABLE" == "1" ]]; then
    snapshot_file installed "$INSTALLED_VALIDATOR"
  fi
  prove_decoy_sidecar_detection

  STDOUT_FILE="$EVIDENCE_ROOT/child.stdout"
  STDERR_FILE="$EVIDENCE_ROOT/child.stderr"
  run_copied_child() {
    (
      cd "$project_root"
      exec env -i \
        LC_ALL=C \
        PATH="$CHILD_PATH" \
        HOME="$home_root" \
        TMPDIR="$runtime_root" \
        PYTHON_BIN="$PYTHON_BIN" \
        CLAUDE_PLUGIN_ROOT="$DECOY_ROOT" \
        CLAUDE_PROJECT_DIR="$project_root" \
        SDLC_TEST_FAILPOINT=after-validator-swap \
        SDLC_TEST_SIGNAL="${F01_TEST_SIGNAL:-}" \
        SDLC_TEST_RESTORE_FAILURE="${F01_TEST_RESTORE_FAILURE:-}" \
        SDLC_TEST_PRE_FAILPOINT_FAILURE="${F01_TEST_PRE_FAILPOINT_FAILURE:-}" \
        SDLC_TEST_FAILPOINT_STDERR_SUFFIX="${F01_TEST_CHILD_STDERR_SUFFIX:-}" \
        F01_TEMP_TREE_TEST_CAPTURE_FAILURE="${F01_TEST_INNER_CAPTURE_FAILURE:-}" \
        /bin/bash "$DECOY_ROOT/tests/test-sdlc-dispatch.sh"
    )
  }
  set +e
  if [[ "${F01_TEST_SIGNAL:-}" == "INT" ]]; then
    run_copied_child >"$STDOUT_FILE" 2>"$STDERR_FILE"
    child_rc=$?
  else
    set -m
    run_copied_child >"$STDOUT_FILE" 2>"$STDERR_FILE" &
    CHILD_PID=$!
    set +m
    wait "$CHILD_PID"
    child_rc=$?
    CHILD_PID=""
  fi
  set -e

  inner_retained_count="$(awk '/^F01_INNER_RETAINED:/ { count++ } END { print count + 0 }' \
    "$STDERR_FILE")"
  if [[ "$inner_retained_count" -ne 0 ]]; then
    PRESERVE_OUTER_ROOT=1
    inner_retained_marker="$(sed -n 's/^F01_INNER_RETAINED://p' "$STDERR_FILE")"
    if [[ "$inner_retained_count" -ne 1 ]]; then
      printf 'F01_INNER_CONTAINER_RETAINED:%s\n' "$OUTER_ROOT" >&2
      return 125
    fi
    case "$inner_retained_marker" in
      "$runtime_root"/sdlc-dispatch-test.*) ;;
      *)
        printf 'F01_INNER_CONTAINER_RETAINED:%s\n' "$OUTER_ROOT" >&2
        return 125
        ;;
    esac
    printf 'F01_INNER_CONTAINER_RETAINED:%s\n' "$OUTER_ROOT" >&2
    return 125
  fi

  restore_count="$(awk '/^F01_RESTORE_FAILED:/ { count++ } END { print count + 0 }' \
    "$STDERR_FILE")"
  if [[ "$restore_count" -ne 0 ]]; then
    PRESERVE_OUTER_ROOT=1
    restore_marker="$(sed -n 's/^F01_RESTORE_FAILED://p' "$STDERR_FILE")"
    if [[ "$restore_count" -ne 1 ]]; then
      printf 'F01_RESTORE_RETAINED:%s\n' "$OUTER_ROOT" >&2
      return 125
    fi
    case "$restore_marker" in
      "$runtime_root"/sdlc-dispatch-test.*/fixture) ;;
      *)
        printf 'F01_RESTORE_RETAINED:%s\n' "$OUTER_ROOT" >&2
        return 125
        ;;
    esac
    printf 'F01_RESTORE_RETAINED:%s\n' "$OUTER_ROOT" >&2
    return 125
  fi

  set +e
  verify_protected_state
  protected_rc=$?
  set -e
  case "$protected_rc" in
    0) ;;
    1) return 1 ;;
    3) installed_drift=1 ;;
    *)
      printf 'F01_FIXTURE_ESCAPE:unexpected protected-state result %s\n' \
        "$protected_rc" >&2
      return 1
      ;;
  esac

  if [[ -s "$STDOUT_FILE" ]]; then
    printf 'failpoint child emitted unexpected stdout\n' >&2
    return 1
  fi

  marker_count="$(awk '/^F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:/ { count++ } END { print count + 0 }' "$STDERR_FILE")"
  if [[ "$marker_count" -eq 0 ]]; then
    expected_legacy="$home_root/LAB/sdlc-os/hooks/sdlc-dispatch.sh"
    if [[ "$child_rc" -eq 1 ]] && grep -Fq "$expected_legacy" "$STDERR_FILE"; then
      printf 'F01_FAILPOINT_NOT_REACHED child_exit=1\n' >&2
      return 1
    fi
    printf 'F01_FAILPOINT_NOT_REACHED marker_count=0 child_exit=%s\n' "$child_rc" >&2
    return 1
  fi
  if [[ "$marker_count" -ne 1 ]]; then
    printf 'F01_FAILPOINT_NOT_REACHED marker_count=%s child_exit=%s\n' "$marker_count" "$child_rc" >&2
    return 1
  fi
  marker="$(sed -n 's/^F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP://p' "$STDERR_FILE")"
  case "$marker" in
    "$runtime_root"/*/hooks/validators/safety-constraints.sh) ;;
    *) printf 'F01_FIXTURE_ESCAPE:failpoint marker path escaped runtime root\n' >&2; return 1 ;;
  esac
  if [[ "$child_rc" -ne "$expected_child_exit" ]]; then
    printf 'failpoint child exit mismatch: expected=%s actual=%s\n' "$expected_child_exit" "$child_rc" >&2
    return 1
  fi
  expected_child_stderr="$EVIDENCE_ROOT/expected-child.stderr"
  printf 'F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP:%s\n' \
    "$marker" >"$expected_child_stderr"
  if ! cmp -s "$expected_child_stderr" "$STDERR_FILE"; then
    printf 'failpoint child stderr mismatch\n' >&2
    return 1
  fi
  if [[ "$installed_drift" -ne 0 ]]; then
    return 3
  fi
  if [[ -n "${F01_TEST_OUTER_ROOT_DRIFT:-}" ]]; then
    case "$F01_TEST_OUTER_ROOT_DRIFT" in
      rename)
        mv "$OUTER_ROOT" "$OUTER_ROOT.moved"
        return 0
        ;;
      *) return 64 ;;
    esac
  fi
  if [[ "${F01_EMIT_FINGERPRINTS:-}" == "1" ]]; then
    emit_validator_fingerprints
  fi
  case "${F01_TEST_SIGNAL:-}" in
    INT) printf 'F01 isolation PASS mode=assert signal=INT launch=foreground\n' ;;
    HUP|TERM) printf 'F01 isolation PASS mode=assert signal=%s\n' "$F01_TEST_SIGNAL" ;;
    "") printf 'F01 isolation PASS mode=assert\n' ;;
  esac
}

case "${F01_TEST_MODE:-assert}" in
  assert) run_assert ;;
  admission-negative) run_admission_negative ;;
  cleanup-retarget) run_cleanup_retarget ;;
  concurrent) run_concurrent ;;
  restore-failure) run_restore_failure ;;
  signal-wrapper-negative) run_signal_wrapper_negative ;;
  *) printf 'invalid F01_TEST_MODE\n' >&2; exit 64 ;;
esac
