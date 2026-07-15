#!/bin/bash
set -euo pipefail

umask 077

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=tests/lib/plugin-root.sh
source "$TEST_DIR/lib/plugin-root.sh"
SOURCE_ROOT="$(resolve_plugin_root "${BASH_SOURCE[0]}")"
TEMP_TREE_HELPER="$SOURCE_ROOT/tests/lib/f01-temp-tree.py"
PYTHON_BIN="${PYTHON_BIN:-}"
CHILD_PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CHECKOUT_LITERAL="\$HOME/LAB/sdlc-os"
GIT_BIN=""
FIND_BIN=""
RG_BIN=""
TMPROOT=""
TMPROOT_TOKEN=""

fail() {
  printf 'PLUGIN_ROOT_RELOCATION_FAILED:%s\n' "$1" >&2
  exit 1
}

resolve_python() {
  local candidate version
  candidate="$PYTHON_BIN"
  if [[ -z "$candidate" ]]; then
    candidate="$(command -v python3.12 2>/dev/null)" || return 1
  fi
  [[ "$candidate" == /* && -x "$candidate" ]] || return 1
  version="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" ||
    return 1
  [[ "$version" == "3.12" ]] || return 1
  printf '%s\n' "$candidate"
}

resolve_required_tool() {
  local name="${1:?tool name required}"
  local candidate
  candidate="$(command -v "$name" 2>/dev/null)" || return 1
  [[ "$candidate" == /* && -x "$candidate" ]] || return 1
  printf '%s\n' "$candidate"
}

is_regular_nonsymlink_file() {
  local path="${1:?file path required}"
  [[ -f "$path" && ! -L "$path" ]]
}

classify_non_git_probe() {
  local rc="${1:?probe exit required}"
  local stdout_file="${2:?stdout path required}"
  local stderr_file="${3:?stderr path required}"
  is_regular_nonsymlink_file "$stdout_file" || return 1
  is_regular_nonsymlink_file "$stderr_file" || return 1
  [[ "$rc" -eq 128 && ! -s "$stdout_file" ]] || return 1
  cmp -s "$EXPECTED_NON_GIT_STDERR" "$stderr_file"
}

classify_empty_find_probe() {
  local rc="${1:?probe exit required}"
  local stdout_file="${2:?stdout path required}"
  local stderr_file="${3:?stderr path required}"
  is_regular_nonsymlink_file "$stdout_file" || return 1
  is_regular_nonsymlink_file "$stderr_file" || return 1
  [[ "$rc" -eq 0 && ! -s "$stdout_file" && ! -s "$stderr_file" ]]
}

classify_literal_no_match_probe() {
  local rc="${1:?probe exit required}"
  local stdout_file="${2:?stdout path required}"
  local stderr_file="${3:?stderr path required}"
  is_regular_nonsymlink_file "$stdout_file" || return 1
  is_regular_nonsymlink_file "$stderr_file" || return 1
  [[ "$rc" -eq 1 && ! -s "$stdout_file" && ! -s "$stderr_file" ]]
}

verify_probe_classifiers() {
  local root="$EVIDENCE_ROOT/probe-classifier-selftest"
  local empty="$root/empty"
  local empty_link="$root/empty-link"
  local expected_link="$root/expected-link"
  local missing="$root/missing"
  local wrong="$root/wrong"
  mkdir -p "$root"
  : >"$empty"
  printf 'fatal: unrelated repository error\n' >"$wrong"
  ln -s "$empty" "$empty_link"
  ln -s "$EXPECTED_NON_GIT_STDERR" "$expected_link"

  classify_non_git_probe 128 "$empty" "$EXPECTED_NON_GIT_STDERR" || return 1
  if classify_non_git_probe 128 "$empty" "$wrong"; then return 1; fi
  if classify_non_git_probe 127 "$empty" "$EXPECTED_NON_GIT_STDERR"; then return 1; fi
  if classify_non_git_probe 128 "$missing" "$EXPECTED_NON_GIT_STDERR"; then return 1; fi
  if classify_non_git_probe 128 "$empty" "$missing"; then return 1; fi
  if classify_non_git_probe 128 "$empty_link" "$EXPECTED_NON_GIT_STDERR"; then return 1; fi
  if classify_non_git_probe 128 "$empty" "$expected_link"; then return 1; fi
  classify_empty_find_probe 0 "$empty" "$empty" || return 1
  if classify_empty_find_probe 2 "$empty" "$empty"; then return 1; fi
  if classify_empty_find_probe 0 "$missing" "$empty"; then return 1; fi
  if classify_empty_find_probe 0 "$empty" "$missing"; then return 1; fi
  if classify_empty_find_probe 0 "$empty_link" "$empty"; then return 1; fi
  if classify_empty_find_probe 0 "$empty" "$empty_link"; then return 1; fi
  classify_literal_no_match_probe 1 "$empty" "$empty" || return 1
  if classify_literal_no_match_probe 2 "$empty" "$empty"; then return 1; fi
  if classify_literal_no_match_probe 127 "$empty" "$empty"; then return 1; fi
  if classify_literal_no_match_probe 1 "$empty" "$wrong"; then return 1; fi
  if classify_literal_no_match_probe 1 "$missing" "$empty"; then return 1; fi
  if classify_literal_no_match_probe 1 "$empty" "$missing"; then return 1; fi
  if classify_literal_no_match_probe 1 "$empty_link" "$empty"; then return 1; fi
  if classify_literal_no_match_probe 1 "$empty" "$empty_link"; then return 1; fi
}

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if [[ -n "$TMPROOT" ]]; then
    if [[ -z "$TMPROOT_TOKEN" ]] ||
        ! "$PYTHON_BIN" "$TEMP_TREE_HELPER" remove \
          "$TMPROOT" sdlc-root-resolution. "$TMPROOT_TOKEN"; then
      printf 'CLEANUP_FAILED:%s\n' "$TMPROOT" >&2
      rc=125
    fi
  fi
  exit "$rc"
}

if ! PYTHON_BIN="$(resolve_python)"; then
  fail "canonical Python 3.12 is unavailable"
fi
[[ -f "$TEMP_TREE_HELPER" && ! -L "$TEMP_TREE_HELPER" ]] ||
  fail "temp-tree helper is unavailable"
GIT_BIN="$(resolve_required_tool git)" || fail "required Git executable is unavailable"
FIND_BIN="$(resolve_required_tool find)" || fail "required find executable is unavailable"
RG_BIN="$(resolve_required_tool rg)" || fail "required rg executable is unavailable"

TMP_BASE="${TMPDIR:-/tmp}"
[[ -d "$TMP_BASE" ]] || fail "TMPDIR does not exist"
TMPROOT="$(mktemp -d "$TMP_BASE/sdlc-root-resolution.XXXXXX")"
TMPROOT="$(cd "$TMPROOT" && pwd -P)"
TMPROOT_TOKEN="$("$PYTHON_BIN" "$TEMP_TREE_HELPER" capture \
  "$TMPROOT" sdlc-root-resolution.)" || fail "cannot capture temporary root"
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

RELOCATED_ROOT="$TMPROOT/relocated checkout with spaces/sdlc os plugin"
ISOLATED_HOME="$TMPROOT/home"
RUNTIME_ROOT="$TMPROOT/runtime"
EVIDENCE_ROOT="$TMPROOT/evidence"
WORK_ROOT="$RUNTIME_ROOT/work"
mkdir -p \
  "$RELOCATED_ROOT" "$ISOLATED_HOME" "$RUNTIME_ROOT" "$EVIDENCE_ROOT" "$WORK_ROOT"
EXPECTED_NON_GIT_STDERR="$EVIDENCE_ROOT/non-git.expected.stderr"
printf 'fatal: not a git repository (or any of the parent directories): .git\n' \
  >"$EXPECTED_NON_GIT_STDERR"
verify_probe_classifiers || fail "mandatory probe classifier self-test failed"

cp -R "$SOURCE_ROOT/.claude-plugin" "$RELOCATED_ROOT/.claude-plugin"
cp -R "$SOURCE_ROOT/hooks" "$RELOCATED_ROOT/hooks"
cp -R "$SOURCE_ROOT/scripts" "$RELOCATED_ROOT/scripts"
cp -R "$SOURCE_ROOT/tests" "$RELOCATED_ROOT/tests"

RELOCATED_ROOT="$(cd "$RELOCATED_ROOT" && pwd -P)"
# shellcheck source=tests/lib/plugin-root.sh
source "$RELOCATED_ROOT/tests/lib/plugin-root.sh"

explicit="$(CLAUDE_PLUGIN_ROOT="$RELOCATED_ROOT" \
  resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
[[ "$explicit" == "$RELOCATED_ROOT" ]] || fail "explicit root mismatch"

fallback="$(unset CLAUDE_PLUGIN_ROOT; \
  resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
[[ "$fallback" == "$RELOCATED_ROOT" ]] || fail "fallback root mismatch"

ln -s "$RELOCATED_ROOT" "$TMPROOT/plugin-link"
symlinked="$(CLAUDE_PLUGIN_ROOT="$TMPROOT/plugin-link" \
  resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh")"
[[ "$symlinked" == "$RELOCATED_ROOT" ]] || fail "symlink root mismatch"

mkdir -p "$TMPROOT/not-a-plugin"
set +e
CLAUDE_PLUGIN_ROOT="$TMPROOT/not-a-plugin" \
  resolve_plugin_root "$RELOCATED_ROOT/tests/test-fixture-regression.sh" \
  >"$EVIDENCE_ROOT/invalid.stdout" 2>"$EVIDENCE_ROOT/invalid.stderr"
invalid_rc=$?
set -e
[[ "$invalid_rc" -eq 1 ]] || fail "invalid root exit mismatch"
[[ ! -s "$EVIDENCE_ROOT/invalid.stdout" ]] || fail "invalid root emitted stdout"
grep -Fq 'ROOT_INVALID:invalid SDLC-OS plugin root:' \
  "$EVIDENCE_ROOT/invalid.stderr" || fail "invalid root diagnostic mismatch"

assert_isolated_work_root() {
  local git_rc find_rc
  local probe_root
  local git_stdout git_stderr find_stdout find_stderr
  [[ -d "$WORK_ROOT" && ! -L "$WORK_ROOT" ]] || return 1
  probe_root="$(mktemp -d "$EVIDENCE_ROOT/work-root.XXXXXX")" || return 1
  [[ -d "$probe_root" && ! -L "$probe_root" ]] || return 1
  git_stdout="$probe_root/git.stdout"
  git_stderr="$probe_root/git.stderr"
  find_stdout="$probe_root/find.stdout"
  find_stderr="$probe_root/find.stderr"
  [[ ! -e "$git_stdout" && ! -L "$git_stdout" ]] || return 1
  [[ ! -e "$git_stderr" && ! -L "$git_stderr" ]] || return 1
  [[ ! -e "$find_stdout" && ! -L "$find_stdout" ]] || return 1
  [[ ! -e "$find_stderr" && ! -L "$find_stderr" ]] || return 1
  set +e
  LC_ALL=C "$GIT_BIN" -C "$WORK_ROOT" rev-parse --is-inside-work-tree \
    >"$git_stdout" 2>"$git_stderr"
  git_rc=$?
  set -e
  classify_non_git_probe "$git_rc" "$git_stdout" "$git_stderr" || return 1

  set +e
  LC_ALL=C "$FIND_BIN" "$WORK_ROOT" -mindepth 1 -print -quit \
    >"$find_stdout" 2>"$find_stderr"
  find_rc=$?
  set -e
  classify_empty_find_probe "$find_rc" "$find_stdout" "$find_stderr"
}

run_relocated() {
  local label="$1"
  shift
  assert_isolated_work_root || fail "isolated work directory is not empty and non-Git"
  set +e
  (
    cd "$WORK_ROOT" || exit 125
    env -i \
      LC_ALL=C \
      PATH="$CHILD_PATH" \
      HOME="$ISOLATED_HOME" \
      TMPDIR="$RUNTIME_ROOT" \
      PYTHON_BIN="$PYTHON_BIN" \
      CLAUDE_PLUGIN_ROOT="$RELOCATED_ROOT" \
      CLAUDE_PROJECT_DIR="$WORK_ROOT" \
      "$@"
  ) >"$EVIDENCE_ROOT/$label.stdout" 2>"$EVIDENCE_ROOT/$label.stderr"
  RELOCATED_RC=$?
  set -e
  assert_isolated_work_root || fail "relocated child changed the work directory"
}

remap_fixture_payloads() {
  local copied_fixtures="$1"
  local source_fixtures="$2"
  local evidence_file="$3"

  LC_ALL=C \
    REMAP_COPIED_FIXTURES="$copied_fixtures" \
    REMAP_SOURCE_FIXTURES="$source_fixtures" \
    REMAP_RUNTIME_ROOT="$RUNTIME_ROOT" \
    REMAP_EVIDENCE_FILE="$evidence_file" \
    "$PYTHON_BIN" - <<'PY'
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path


class RemapError(Exception):
    pass


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RemapError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise RemapError(f"invalid JSON constant: {value}")


def parse_payload(raw, name):
    try:
        payload = json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, RemapError) as exc:
        raise RemapError(f"{name}: malformed JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RemapError(f"{name}: payload must be an object")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise RemapError(f"{name}: tool_input must be an object")
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str):
        raise RemapError(f"{name}: file_path must be a string")
    if not file_path or "\x00" in file_path:
        raise RemapError(f"{name}: file_path must be nonempty and NUL-free")
    if not file_path.startswith("/"):
        raise RemapError(f"{name}: file_path must be absolute")
    return payload, file_path


def validate_segments(relative, name):
    segments = relative.split("/")
    if not segments or any(segment in ("", ".", "..") for segment in segments):
        raise RemapError(f"{name}: unsafe relative path")
    return segments


def map_path(file_path, payload_root, name):
    marker = "/LAB/test-project/"
    legacy_prefix = None
    is_scratch = file_path.startswith("/tmp/")
    marker_count = file_path.count(marker)
    if is_scratch and marker_count:
        raise RemapError(f"{name}: file_path matches both route classes")
    if is_scratch:
        bucket = "scratch"
        relative = file_path[len("/tmp/") :]
    elif marker_count == 1:
        marker_end = file_path.index(marker) + len(marker)
        legacy_prefix = file_path[:marker_end]
        bucket = "project"
        relative = file_path[marker_end:]
    else:
        raise RemapError(f"{name}: absolute path is outside the allowlist")

    segments = validate_segments(relative, name)
    bucket_root = (payload_root / bucket).resolve(strict=False)
    mapped = (bucket_root / Path(*segments)).resolve(strict=False)
    try:
        contained = os.path.commonpath((str(bucket_root), str(mapped))) == str(
            bucket_root
        )
    except ValueError as exc:
        raise RemapError(f"{name}: mapped path cannot be compared") from exc
    if not contained:
        raise RemapError(f"{name}: mapped path escapes the runtime root")
    if mapped.name != segments[-1]:
        raise RemapError(f"{name}: mapped basename changed")
    if os.path.lexists(mapped):
        raise RemapError(f"{name}: mapped target already exists")
    return mapped, legacy_prefix, bucket


def validate_legacy_prefix(current, candidate, name):
    if candidate is None:
        return current
    if current is not None and current != candidate:
        raise RemapError(f"{name}: inconsistent legacy project prefix")
    return candidate


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_inode_distinct(source, copied):
    source_stat = os.stat(source, follow_symlinks=False)
    copied_stat = os.stat(copied, follow_symlinks=False)
    if not stat.S_ISREG(source_stat.st_mode) or not stat.S_ISREG(copied_stat.st_mode):
        raise RemapError("source/copy payload pair must contain regular files")
    if (source_stat.st_dev, source_stat.st_ino) == (
        copied_stat.st_dev,
        copied_stat.st_ino,
    ):
        raise RemapError(f"{copied.name}: copied payload aliases its source inode")


def hash_tree(root):
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for directory in directories:
            if (current_path / directory).is_symlink():
                raise RemapError("source fixture contains a symlinked directory")
        for filename in files:
            path = current_path / filename
            if path.is_symlink() or not path.is_file():
                raise RemapError("source fixture contains a non-regular file")
            result[path.relative_to(root).as_posix()] = hash_file(path)
    return dict(sorted(result.items()))


def regular_payloads(root, label):
    files = sorted(root.glob("*.payload.json"))
    if len(files) != 13:
        raise RemapError(f"{label}: expected 13 payloads, found {len(files)}")
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise RemapError(f"{label}: payload is not a regular file: {path.name}")
    return files


def expect_remap_error(label, callback):
    try:
        callback()
    except RemapError:
        return
    raise RemapError(f"self-test admitted invalid case: {label}")


def run_self_tests(payload_root, evidence_root):
    duplicate = b'{"tool_input":{"file_path":"/tmp/a","file_path":"/tmp/b"}}'
    expect_remap_error("duplicate member", lambda: parse_payload(duplicate, "self"))
    expect_remap_error("malformed JSON", lambda: parse_payload(b"{", "self"))
    expect_remap_error(
        "missing file_path",
        lambda: parse_payload(b'{"tool_input":{}}', "self"),
    )
    expect_remap_error(
        "non-string file_path",
        lambda: parse_payload(b'{"tool_input":{"file_path":7}}', "self"),
    )
    expect_remap_error(
        "empty file_path",
        lambda: parse_payload(b'{"tool_input":{"file_path":""}}', "self"),
    )
    expect_remap_error(
        "encoded NUL",
        lambda: parse_payload(
            br'{"tool_input":{"file_path":"/tmp/a\u0000b"}}', "self"
        ),
    )
    expect_remap_error(
        "non-finite constant",
        lambda: parse_payload(b'{"tool_input":{"file_path":NaN}}', "self"),
    )
    for label, value in (
        ("relative path", "tmp/a"),
        ("other absolute path", "/var/tmp/a"),
        ("empty suffix", "/tmp/"),
        ("dot segment", "/tmp/./a"),
        ("parent segment", "/tmp/../a"),
        ("repeated separator", "/tmp//a"),
        (
            "repeated marker",
            "/one/LAB/test-project/two/LAB/test-project/a",
        ),
        (
            "ambiguous route",
            "/tmp/one/LAB/test-project/a",
        ),
    ):
        if not value.startswith("/"):
            expect_remap_error(
                label,
                lambda value=value: parse_payload(
                    json.dumps({"tool_input": {"file_path": value}}).encode(),
                    "self",
                ),
            )
        else:
            expect_remap_error(
                label,
                lambda value=value: map_path(value, payload_root, "self"),
            )
    _, encoded_path = parse_payload(
        br'{"tool_input":{"file_path":"\u002ftmp\u002fencoded.py"}}', "self"
    )
    encoded_target, _, encoded_bucket = map_path(
        encoded_path, payload_root, "self"
    )
    if encoded_bucket != "scratch" or encoded_target != (
        payload_root / "scratch" / "encoded.py"
    ).resolve(strict=False):
        raise RemapError("self-test rejected decoded valid slash path")
    _, encoded_traversal = parse_payload(
        br'{"tool_input":{"file_path":"\u002ftmp\u002f..\u002fx"}}', "self"
    )
    expect_remap_error(
        "encoded traversal",
        lambda: map_path(encoded_traversal, payload_root, "self"),
    )
    expect_remap_error(
        "inconsistent legacy prefix",
        lambda: validate_legacy_prefix(
            "/one/LAB/test-project/", "/two/LAB/test-project/", "self"
        ),
    )
    with tempfile.TemporaryDirectory(
        prefix="payload-hardlink-selftest.", dir=evidence_root
    ) as temporary:
        temporary_root = Path(temporary)
        source = temporary_root / "source.payload.json"
        copied = temporary_root / "copied.payload.json"
        source.write_bytes(b'{"tool_input":{"file_path":"/tmp/self"}}\n')
        source_before = hash_file(source)
        os.link(source, copied)
        expect_remap_error(
            "hardlink source/copy alias",
            lambda: ensure_inode_distinct(source, copied),
        )
        if hash_file(source) != source_before:
            raise RemapError("hardlink self-test changed source bytes")


def main():
    copied_input = Path(os.environ["REMAP_COPIED_FIXTURES"])
    source_input = Path(os.environ["REMAP_SOURCE_FIXTURES"])
    runtime_input = Path(os.environ["REMAP_RUNTIME_ROOT"])
    for label, path in (
        ("copied fixtures", copied_input),
        ("source fixtures", source_input),
        ("runtime root", runtime_input),
    ):
        if path.is_symlink():
            raise RemapError(f"{label} must not be a symlink")
    copied_root = copied_input.resolve(strict=True)
    source_root = source_input.resolve(strict=True)
    runtime_root = runtime_input.resolve(strict=True)
    evidence_file = Path(os.environ["REMAP_EVIDENCE_FILE"])
    evidence_root = evidence_file.parent.resolve(strict=True)
    payload_root_input = runtime_root / "payload-files"
    if os.path.lexists(payload_root_input):
        raise RemapError("mapped payload root already exists")
    payload_root = payload_root_input.resolve(strict=False)
    run_self_tests(payload_root, evidence_root)

    copied_files = regular_payloads(copied_root, "copied fixtures")
    source_files = regular_payloads(source_root, "source fixtures")
    if [path.name for path in copied_files] != [path.name for path in source_files]:
        raise RemapError("copied/source payload inventory mismatch")
    source_by_name = {path.name: path for path in source_files}
    for path in copied_files:
        source_path = source_by_name[path.name]
        ensure_inode_distinct(source_path, path)
        if hash_file(path) != hash_file(source_path):
            raise RemapError(f"{path.name}: initial copied bytes differ from source")

    transformations = []
    payload_targets = {}
    original_paths = {}
    legacy_prefix = None
    route_counts = {"scratch": 0, "project": 0}
    for path in copied_files:
        payload, file_path = parse_payload(path.read_bytes(), path.name)
        mapped, candidate_prefix, bucket = map_path(
            file_path, payload_root, path.name
        )
        legacy_prefix = validate_legacy_prefix(
            legacy_prefix, candidate_prefix, path.name
        )
        route_counts[bucket] += 1
        original_paths[path.name] = file_path
        payload["tool_input"]["file_path"] = str(mapped)
        transformed = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        transformations.append((path, transformed))
        payload_targets[path.name] = str(mapped)

    if legacy_prefix is None:
        raise RemapError("no legacy project prefix was derived")
    if route_counts != {"scratch": 6, "project": 7}:
        raise RemapError(f"unexpected payload route counts: {route_counts}")
    prefix_bytes = legacy_prefix.encode("utf-8")
    for path, transformed in transformations:
        if prefix_bytes in transformed:
            raise RemapError(f"{path.name}: legacy prefix remains after remap")
        for original_path in original_paths.values():
            if original_path.encode("utf-8") in transformed:
                raise RemapError(
                    f"{path.name}: source-declared path remains after remap"
                )

    source_hashes = hash_tree(source_root)
    for path, transformed in transformations:
        path.write_bytes(transformed)
    if os.path.lexists(payload_root_input):
        raise RemapError("mapped payload root was created during remap")
    copied_hashes = {path.name: hash_file(path) for path, _ in transformations}

    evidence = {
        "schema_version": 1,
        "legacy_prefix": legacy_prefix,
        "original_paths": dict(sorted(original_paths.items())),
        "payload_targets": dict(sorted(payload_targets.items())),
        "source_sha256": source_hashes,
        "copied_sha256": dict(sorted(copied_hashes.items())),
    }
    evidence_file.write_text(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


try:
    main()
except RemapError as exc:
    print(f"PAYLOAD_REMAP_INVALID:{exc}", file=sys.stderr)
    raise SystemExit(64)
except Exception as exc:
    print(f"PAYLOAD_REMAP_INVALID:internal error: {exc}", file=sys.stderr)
    raise SystemExit(70)
PY
}

verify_fixture_payload_isolation() {
  local copied_fixtures="$1"
  local source_fixtures="$2"
  local evidence_file="$3"

  LC_ALL=C \
    REMAP_COPIED_FIXTURES="$copied_fixtures" \
    REMAP_SOURCE_FIXTURES="$source_fixtures" \
    REMAP_RUNTIME_ROOT="$RUNTIME_ROOT" \
    REMAP_EVIDENCE_FILE="$evidence_file" \
    "$PYTHON_BIN" - <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path


def fail(message):
    print(f"PAYLOAD_REMAP_INVALID:{message}", file=sys.stderr)
    raise SystemExit(1)


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_tree(root):
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        if any((current_path / directory).is_symlink() for directory in directories):
            fail("source fixture contains a symlinked directory")
        for filename in files:
            path = current_path / filename
            if path.is_symlink() or not path.is_file():
                fail("source fixture contains a non-regular file")
            result[path.relative_to(root).as_posix()] = hash_file(path)
    return dict(sorted(result.items()))


copied_input = Path(os.environ["REMAP_COPIED_FIXTURES"])
source_input = Path(os.environ["REMAP_SOURCE_FIXTURES"])
runtime_input = Path(os.environ["REMAP_RUNTIME_ROOT"])
for label, path in (
    ("copied fixtures", copied_input),
    ("source fixtures", source_input),
    ("runtime root", runtime_input),
):
    if path.is_symlink():
        fail(f"{label} became a symlink")
copied_root = copied_input.resolve(strict=True)
source_root = source_input.resolve(strict=True)
runtime_root = runtime_input.resolve(strict=True)
evidence_file = Path(os.environ["REMAP_EVIDENCE_FILE"])
try:
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    fail(f"cannot read remap evidence: {exc}")
if evidence.get("schema_version") != 1:
    fail("unsupported remap evidence schema")
if hash_tree(source_root) != evidence.get("source_sha256"):
    fail("source fixture bytes changed")

legacy_prefix = evidence.get("legacy_prefix")
original_paths = evidence.get("original_paths")
payload_targets = evidence.get("payload_targets")
copied_hashes = evidence.get("copied_sha256")
if not isinstance(legacy_prefix, str) or not legacy_prefix.endswith(
    "/LAB/test-project/"
):
    fail("legacy prefix evidence is invalid")
if (
    not isinstance(original_paths, dict)
    or not isinstance(payload_targets, dict)
    or not isinstance(copied_hashes, dict)
):
    fail("payload evidence is invalid")
if any(not isinstance(value, str) for value in original_paths.values()) or any(
    not isinstance(value, str) for value in payload_targets.values()
):
    fail("payload path evidence is invalid")

payload_root_input = runtime_root / "payload-files"
if os.path.lexists(payload_root_input):
    fail("mapped payload root was created")
payload_root = payload_root_input.resolve(strict=False)
copied_files = sorted(copied_root.glob("*.payload.json"))
if len(copied_files) != 13 or any(
    path.is_symlink() or not path.is_file() for path in copied_files
):
    fail("copied payload inventory is not 13 regular files")
if [path.name for path in copied_files] != sorted(payload_targets):
    fail("copied payload inventory changed")
if sorted(copied_hashes) != sorted(payload_targets) or sorted(
    original_paths
) != sorted(payload_targets):
    fail("copied payload hash inventory changed")

for path in copied_files:
    raw = path.read_bytes()
    if legacy_prefix.encode("utf-8") in raw:
        fail(f"{path.name}: legacy prefix reappeared")
    if any(value.encode("utf-8") in raw for value in original_paths.values()):
        fail(f"{path.name}: source-declared path reappeared")
    if hash_file(path) != copied_hashes[path.name]:
        fail(f"{path.name}: remapped payload bytes changed")
    try:
        current_target = json.loads(raw)["tool_input"]["file_path"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        fail(f"{path.name}: remapped payload is invalid: {exc}")
    if current_target != payload_targets[path.name]:
        fail(f"{path.name}: remapped target changed")
    if current_target == original_paths[path.name]:
        fail(f"{path.name}: original target was restored")

for target_text in payload_targets.values():
    target = Path(target_text).resolve(strict=False)
    try:
        contained = os.path.commonpath((str(payload_root), str(target))) == str(
            payload_root
        )
    except ValueError:
        contained = False
    if not contained:
        fail("recorded target escapes the runtime root")
    if os.path.lexists(target):
        fail("a remapped target was created")
PY
}

emit_relocation_evidence() {
  LC_ALL=C \
    EVIDENCE_CANDIDATE_TEST="$SOURCE_ROOT/tests/test-plugin-root-resolution.sh" \
    EVIDENCE_RELOCATED_TEST="$RELOCATED_ROOT/tests/test-plugin-root-resolution.sh" \
    EVIDENCE_FIXTURE_STDOUT="$EVIDENCE_ROOT/fixture-regression.stdout" \
    EVIDENCE_FIXTURE_STDERR="$EVIDENCE_ROOT/fixture-regression.stderr" \
    EVIDENCE_REMAP="$PAYLOAD_REMAP_EVIDENCE" \
    "$PYTHON_BIN" - <<'PY'
import base64
import binascii
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path


class EvidenceError(Exception):
    pass


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise EvidenceError(f"invalid JSON constant: {value}")


def load_json(raw, label):
    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as exc:
        raise EvidenceError(f"{label} is malformed: {exc}") from exc


def canonical_record(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def parse_canonical_line(raw, label):
    if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
        raise EvidenceError(f"{label} must be one LF-terminated JSON record")
    record = raw[:-1]
    if not record or not record.isascii() or any(
        byte < 0x20 or byte == 0x7F for byte in record
    ):
        raise EvidenceError(f"{label} is not one control-free ASCII line")
    value = load_json(record, label)
    if record != canonical_record(value):
        raise EvidenceError(f"{label} is not canonical compact serialization")
    return value


def exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise EvidenceError(f"{label} members differ from schema")


def require_sha256(value, label):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EvidenceError(f"{label} is not a lowercase SHA-256")


def artifact(raw):
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "base64": base64.b64encode(raw).decode("ascii"),
    }


def source_map_digest(source_map):
    return hashlib.sha256(
        json.dumps(source_map, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def validate_remap(raw):
    remap = parse_canonical_line(raw, "remap evidence")
    exact_keys(
        remap,
        (
            "schema_version",
            "legacy_prefix",
            "original_paths",
            "payload_targets",
            "source_sha256",
            "copied_sha256",
        ),
        "remap evidence",
    )
    if type(remap["schema_version"]) is not int or remap["schema_version"] != 1:
        raise EvidenceError("remap evidence schema is invalid")
    source_map = remap["source_sha256"]
    if not isinstance(source_map, dict) or not source_map:
        raise EvidenceError("source fixture hash map is invalid")
    for key, value in source_map.items():
        if not isinstance(key, str):
            raise EvidenceError("source fixture hash name is invalid")
        require_sha256(value, f"source_sha256.{key}")
    targets = remap["payload_targets"]
    if not isinstance(targets, dict):
        raise EvidenceError("payload target evidence is invalid")
    quality_target = targets.get("quality-budget.block.payload.json")
    if not isinstance(quality_target, str) or not quality_target.endswith(
        "/payload-files/scratch/quality-budget.yaml"
    ):
        raise EvidenceError("quality-budget target evidence is invalid")
    return remap, source_map, quality_target


def validate_envelope(outer, candidate_raw):
    pass_line = b"Plugin root relocation: PASS\n"
    if not outer.endswith(pass_line):
        raise EvidenceError(
            "outer evidence must contain one JSON line and one exact PASS line"
        )
    record_with_lf = outer[: -len(pass_line)]
    event = parse_canonical_line(record_with_lf, "outer evidence")
    exact_keys(event, ("event", "schema_version", "binding", "artifacts"), "outer evidence")
    if event["event"] != "PLUGIN_ROOT_RELOCATION_EVIDENCE" or (
        type(event["schema_version"]) is not int or event["schema_version"] != 1
    ):
        raise EvidenceError("outer evidence identity is invalid")

    binding = event["binding"]
    exact_keys(
        binding,
        (
            "candidate_test_sha256",
            "relocated_test_sha256",
            "source_fixture_tree_sha256",
        ),
        "binding",
    )
    for key, value in binding.items():
        require_sha256(value, f"binding.{key}")
    candidate_hash = hashlib.sha256(candidate_raw).hexdigest()
    if binding["candidate_test_sha256"] != candidate_hash:
        raise EvidenceError("candidate test hash does not match current bytes")
    if binding["relocated_test_sha256"] != candidate_hash:
        raise EvidenceError("relocated test hash does not match candidate")

    artifacts = event["artifacts"]
    exact_keys(
        artifacts,
        ("fixture_stdout", "fixture_stderr", "remap_evidence"),
        "artifacts",
    )
    decoded = {}
    for name, record in artifacts.items():
        exact_keys(record, ("bytes", "sha256", "base64"), f"artifacts.{name}")
        if type(record["bytes"]) is not int or record["bytes"] < 0:
            raise EvidenceError(f"artifacts.{name}.bytes is invalid")
        require_sha256(record["sha256"], f"artifacts.{name}.sha256")
        if not isinstance(record["base64"], str):
            raise EvidenceError(f"artifacts.{name}.base64 is invalid")
        try:
            raw = base64.b64decode(record["base64"], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise EvidenceError(f"artifacts.{name}.base64 is malformed") from exc
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record[
            "sha256"
        ]:
            raise EvidenceError(f"artifacts.{name} length/hash mismatch")
        decoded[name] = raw

    _, source_map, quality_target = validate_remap(decoded["remap_evidence"])
    if source_map_digest(source_map) != binding["source_fixture_tree_sha256"]:
        raise EvidenceError("source fixture tree binding mismatch")
    expected_stdout = b"Fixture regression: 12 passed, 1 failed (13 total)\n"
    expected_stderr = (
        "FAIL: quality-budget.block -- stderr mismatch\n"
        "1c1\n"
        '< {"decision":"deny","reason":"quality-budget.yaml missing task_id field"}\n'
        "---\n"
        f"> quality-budget.yaml written but file not found at {quality_target}\n"
    ).encode("utf-8")
    if decoded["fixture_stdout"] != expected_stdout:
        raise EvidenceError("fixture stdout differs from admitted signature")
    if decoded["fixture_stderr"] != expected_stderr:
        raise EvidenceError("fixture stderr differs from admitted signature")
    return event


def encoded_outer(event):
    return canonical_record(event) + b"\nPlugin root relocation: PASS\n"


def expect_error(label, outer, candidate_raw):
    try:
        validate_envelope(outer, candidate_raw)
    except EvidenceError:
        return
    raise EvidenceError(f"self-test admitted invalid envelope: {label}")


def replace_artifact(event, name, raw):
    result = copy.deepcopy(event)
    result["artifacts"][name] = artifact(raw)
    return result


def read_regular(path_text, label):
    path = Path(path_text)
    if path.is_symlink() or not path.is_file():
        raise EvidenceError(f"{label} is not a regular file")
    return path.read_bytes()


def main():
    candidate_raw = read_regular(os.environ["EVIDENCE_CANDIDATE_TEST"], "candidate test")
    relocated_raw = read_regular(os.environ["EVIDENCE_RELOCATED_TEST"], "relocated test")
    stdout_raw = read_regular(os.environ["EVIDENCE_FIXTURE_STDOUT"], "fixture stdout")
    stderr_raw = read_regular(os.environ["EVIDENCE_FIXTURE_STDERR"], "fixture stderr")
    remap_raw = read_regular(os.environ["EVIDENCE_REMAP"], "remap evidence")
    _, source_map, _ = validate_remap(remap_raw)
    candidate_hash = hashlib.sha256(candidate_raw).hexdigest()
    relocated_hash = hashlib.sha256(relocated_raw).hexdigest()
    if candidate_hash != relocated_hash:
        raise EvidenceError("candidate and relocated test bytes differ")
    event = {
        "event": "PLUGIN_ROOT_RELOCATION_EVIDENCE",
        "schema_version": 1,
        "binding": {
            "candidate_test_sha256": candidate_hash,
            "relocated_test_sha256": relocated_hash,
            "source_fixture_tree_sha256": source_map_digest(source_map),
        },
        "artifacts": {
            "fixture_stdout": artifact(stdout_raw),
            "fixture_stderr": artifact(stderr_raw),
            "remap_evidence": artifact(remap_raw),
        },
    }
    outer = encoded_outer(event)
    validate_envelope(outer, candidate_raw)

    boolean_schema = copy.deepcopy(event)
    boolean_schema["schema_version"] = True
    expect_error("boolean schema", encoded_outer(boolean_schema), candidate_raw)
    record = canonical_record(event)
    expect_error(
        "alternate separator",
        record + b"\v\nPlugin root relocation: PASS\n",
        candidate_raw,
    )
    expect_error(
        "noncanonical JSON",
        json.dumps(event, sort_keys=True).encode("ascii")
        + b"\nPlugin root relocation: PASS\n",
        candidate_raw,
    )
    expect_error(
        "extra line",
        record + b"\nEXTRA\nPlugin root relocation: PASS\n",
        candidate_raw,
    )
    expect_error(
        "outer DEL",
        record + b"\x7f\nPlugin root relocation: PASS\n",
        candidate_raw,
    )
    expect_error("truncated outer", outer[:-1], candidate_raw)

    missing = copy.deepcopy(event)
    del missing["artifacts"]["fixture_stderr"]
    expect_error("missing artifact", encoded_outer(missing), candidate_raw)
    extra = copy.deepcopy(event)
    extra["unexpected"] = None
    expect_error("extra member", encoded_outer(extra), candidate_raw)
    duplicate = (
        b'{"event":"PLUGIN_ROOT_RELOCATION_EVIDENCE",'
        + record[1:]
        + b"\nPlugin root relocation: PASS\n"
    )
    expect_error("duplicate member", duplicate, candidate_raw)
    expect_error("malformed JSON", b"{\nPlugin root relocation: PASS\n", candidate_raw)

    truncated_base64 = copy.deepcopy(event)
    truncated_base64["artifacts"]["fixture_stdout"]["base64"] = truncated_base64[
        "artifacts"
    ]["fixture_stdout"]["base64"][:-1]
    expect_error("truncated base64", encoded_outer(truncated_base64), candidate_raw)
    hash_mismatch = copy.deepcopy(event)
    hash_mismatch["artifacts"]["fixture_stdout"]["sha256"] = "0" * 64
    expect_error("hash mismatch", encoded_outer(hash_mismatch), candidate_raw)

    remap_value = parse_canonical_line(remap_raw, "remap evidence")
    remap_boolean = copy.deepcopy(remap_value)
    remap_boolean["schema_version"] = True
    expect_error(
        "remap boolean schema",
        encoded_outer(
            replace_artifact(
                event,
                "remap_evidence",
                canonical_record(remap_boolean) + b"\n",
            )
        ),
        candidate_raw,
    )
    remap_noncanonical = json.dumps(remap_value, sort_keys=True).encode("ascii") + b"\n"
    expect_error(
        "noncanonical remap",
        encoded_outer(replace_artifact(event, "remap_evidence", remap_noncanonical)),
        candidate_raw,
    )
    remap_del = remap_raw.replace(b"/LAB/test-project/", b"/LAB/\x7ftest-project/", 1)
    expect_error(
        "remap DEL",
        encoded_outer(replace_artifact(event, "remap_evidence", remap_del)),
        candidate_raw,
    )

    sys.stdout.buffer.write(record + b"\n")


try:
    main()
except EvidenceError as exc:
    print(f"PLUGIN_ROOT_RELOCATION_EVIDENCE_INVALID:{exc}", file=sys.stderr)
    raise SystemExit(64)
except Exception as exc:
    print(f"PLUGIN_ROOT_RELOCATION_EVIDENCE_INVALID:internal error: {exc}", file=sys.stderr)
    raise SystemExit(70)
PY
}

run_relocated validator-shims \
  /bin/bash "$RELOCATED_ROOT/tests/test-validator-shims.sh"
if [[ "$RELOCATED_RC" -ne 0 ]]; then
  if [[ "$RELOCATED_RC" -ne 1 ]] ||
      ! grep -Fqx 'Results: 0 passed, 14 failed' \
        "$EVIDENCE_ROOT/validator-shims.stdout"; then
    fail "validator-shims unexpected red signature"
  fi
  LEGACY_TARGET="$ISOLATED_HOME/LAB/sdlc-os/hooks/scripts/validate-quality-budget.sh"
  set +e
  /bin/bash "$LEGACY_TARGET" \
    >"$EVIDENCE_ROOT/legacy-probe.stdout" \
    2>"$EVIDENCE_ROOT/legacy-probe.stderr"
  legacy_rc=$?
  set -e
  [[ "$legacy_rc" -eq 127 ]] || fail "legacy child probe exit mismatch"
  [[ ! -s "$EVIDENCE_ROOT/legacy-probe.stdout" ]] ||
    fail "legacy child probe emitted stdout"
  grep -Fq "$LEGACY_TARGET" "$EVIDENCE_ROOT/legacy-probe.stderr" ||
    fail "legacy child probe path missing"
  printf 'RELOCATABILITY_RED:validator-shims aggregate_exit=1 cases=0/14 child_exit=127\n' >&2
  exit 1
fi
[[ ! -s "$EVIDENCE_ROOT/validator-shims.stderr" ]] ||
  fail "validator-shims emitted stderr"
grep -Fqx 'Results: 14 passed, 0 failed' \
  "$EVIDENCE_ROOT/validator-shims.stdout" || fail "validator-shims result mismatch"

SOURCE_FIXTURES="$SOURCE_ROOT/tests/fixtures/validator-baseline"
RELOCATED_FIXTURES="$RELOCATED_ROOT/tests/fixtures/validator-baseline"
PAYLOAD_REMAP_EVIDENCE="$EVIDENCE_ROOT/payload-remap.json"
[[ "$SOURCE_FIXTURES" != "$RELOCATED_FIXTURES" ]] ||
  fail "source and relocated fixtures overlap"
[[ ! "$SOURCE_FIXTURES" -ef "$RELOCATED_FIXTURES" ]] ||
  fail "source and relocated fixtures alias"
if ! remap_fixture_payloads \
    "$RELOCATED_FIXTURES" "$SOURCE_FIXTURES" "$PAYLOAD_REMAP_EVIDENCE"; then
  fail "fixture payload remap failed"
fi

run_relocated fixture-regression \
  /bin/bash "$RELOCATED_ROOT/tests/test-fixture-regression.sh"
[[ "$RELOCATED_RC" -eq 1 ]] || fail "fixture regression exit mismatch"
printf '%s\n' 'Fixture regression: 12 passed, 1 failed (13 total)' \
  >"$EVIDENCE_ROOT/fixture-regression.expected.stdout"
cmp -s \
  "$EVIDENCE_ROOT/fixture-regression.expected.stdout" \
  "$EVIDENCE_ROOT/fixture-regression.stdout" || fail "fixture result mismatch"
QUALITY_TARGET="$RUNTIME_ROOT/payload-files/scratch/quality-budget.yaml"
printf '%s\n' \
  'FAIL: quality-budget.block -- stderr mismatch' \
  '1c1' \
  '< {"decision":"deny","reason":"quality-budget.yaml missing task_id field"}' \
  '---' \
  "> quality-budget.yaml written but file not found at $QUALITY_TARGET" \
  >"$EVIDENCE_ROOT/fixture-regression.expected.stderr"
cmp -s \
  "$EVIDENCE_ROOT/fixture-regression.expected.stderr" \
  "$EVIDENCE_ROOT/fixture-regression.stderr" ||
  fail "fixture diagnostic mismatch"
verify_fixture_payload_isolation \
  "$RELOCATED_FIXTURES" "$SOURCE_FIXTURES" "$PAYLOAD_REMAP_EVIDENCE" ||
  fail "fixture payload isolation changed"

run_relocated dispatcher \
  /bin/bash "$RELOCATED_ROOT/tests/test-sdlc-dispatch.sh"
[[ "$RELOCATED_RC" -eq 0 ]] || fail "dispatcher exit mismatch"
[[ ! -s "$EVIDENCE_ROOT/dispatcher.stderr" ]] || fail "dispatcher emitted stderr"
grep -Fqx 'Results: 11 passed, 0 failed' \
  "$EVIDENCE_ROOT/dispatcher.stdout" || fail "dispatcher result mismatch"

grep -Fqx "ITERATIONS=\"\${BENCHMARK_ITERATIONS:-10}\"" \
  "$RELOCATED_ROOT/tests/benchmark-dispatch.sh" || fail "benchmark default changed"
assert_isolated_work_root || fail "benchmark work directory is not empty and non-Git"
set +e
(
  cd "$WORK_ROOT" || exit 125
  env -i \
    LC_ALL=C \
    PATH="$CHILD_PATH" \
    HOME="$ISOLATED_HOME" \
    TMPDIR="$RUNTIME_ROOT" \
    PYTHON_BIN="$PYTHON_BIN" \
    CLAUDE_PLUGIN_ROOT="$RELOCATED_ROOT" \
    CLAUDE_PROJECT_DIR="$WORK_ROOT" \
    BENCHMARK_ITERATIONS=1 \
    /bin/bash "$RELOCATED_ROOT/tests/benchmark-dispatch.sh"
) >"$EVIDENCE_ROOT/benchmark.stdout" 2>"$EVIDENCE_ROOT/benchmark.stderr"
benchmark_rc=$?
set -e
assert_isolated_work_root || fail "benchmark changed the work directory"
[[ "$benchmark_rc" -eq 0 ]] || fail "benchmark exit mismatch"
[[ ! -s "$EVIDENCE_ROOT/benchmark.stderr" ]] || fail "benchmark emitted stderr"
[[ "$(grep -c 'over 1 runs)' "$EVIDENCE_ROOT/benchmark.stdout")" -eq 5 ]] ||
  fail "benchmark override count mismatch"

set +e
LC_ALL=C "$RG_BIN" -n -F "$CHECKOUT_LITERAL" \
    "$RELOCATED_ROOT/tests/benchmark-dispatch.sh" \
    "$RELOCATED_ROOT/tests/test-validator-shims.sh" \
    "$RELOCATED_ROOT/tests/test-fixture-regression.sh" \
    "$RELOCATED_ROOT/tests/test-sdlc-dispatch.sh" \
    >"$EVIDENCE_ROOT/literal-scan.stdout" \
    2>"$EVIDENCE_ROOT/literal-scan.stderr"
literal_rc=$?
set -e
classify_literal_no_match_probe \
  "$literal_rc" \
  "$EVIDENCE_ROOT/literal-scan.stdout" \
  "$EVIDENCE_ROOT/literal-scan.stderr" || fail "checkout-bound literal scan failed"

verify_fixture_payload_isolation \
  "$RELOCATED_FIXTURES" "$SOURCE_FIXTURES" "$PAYLOAD_REMAP_EVIDENCE" ||
  fail "fixture payload isolation changed after relocated checks"

emit_relocation_evidence || fail "cannot emit relocation evidence"
printf 'Plugin root relocation: PASS\n'
