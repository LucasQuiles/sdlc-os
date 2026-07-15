#!/bin/bash
set -euo pipefail

umask 077

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PLUGIN_ROOT="$(cd "$TEST_DIR/.." && pwd -P)"
COLONY_ROOT="$PLUGIN_ROOT/colony"
WRAPPER="$COLONY_ROOT/run-tsx.sh"
PYTHON_BIN="$(command -v python3.12)"
VITEST_BIN="$COLONY_ROOT/node_modules/.bin/vitest"
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

check_exact_pin() {
  if "$PYTHON_BIN" - \
      "$COLONY_ROOT/package.json" "$COLONY_ROOT/package-lock.json" <<'PY'
import json
import sys
from pathlib import Path

package = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lock = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected = "4.23.1"
observed = {
    "package devDependency": package.get("devDependencies", {}).get("tsx"),
    "lock root devDependency": (
        lock.get("packages", {}).get("", {}).get("devDependencies", {}).get("tsx")
    ),
    "lock installed package": (
        lock.get("packages", {}).get("node_modules/tsx", {}).get("version")
    ),
}
failures = [f"{label}={value!r}" for label, value in observed.items() if value != expected]
if failures:
    print("; ".join(failures), file=sys.stderr)
    raise SystemExit(1)
PY
  then
    record_pass "exact tsx pin in package and lock"
  else
    record_fail "exact tsx pin missing"
  fi
}

check_local_wrapper() {
  local stdout_file="$TMPROOT/local.stdout"
  local stderr_file="$TMPROOT/local.stderr"
  local rc
  if [[ ! -x "$WRAPPER" ]]; then
    record_fail "local tsx wrapper missing"
    return
  fi
  mkdir -p "$TMPROOT/empty-cache"
  set +e
  npm_config_offline=true \
    npm_config_cache="$TMPROOT/empty-cache" \
    "$WRAPPER" --version >"$stdout_file" 2>"$stderr_file"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]] && grep -Fxq 'tsx v4.23.1' "$stdout_file" &&
      [[ ! -s "$stderr_file" ]]; then
    record_pass "offline local tsx execution"
  else
    record_fail "offline local tsx execution (exit $rc)"
  fi
}

check_missing_wrapper_binary() {
  local fixture="$TMPROOT/missing-install"
  local stdout_file="$fixture/stdout"
  local stderr_file="$fixture/stderr"
  local expected_stderr="$fixture/expected.stderr"
  local sentinel="$fixture/dynamic-tool-invoked"
  local rc
  if [[ ! -f "$WRAPPER" ]]; then
    record_fail "missing-install boundary cannot run without wrapper"
    return
  fi
  mkdir -p "$fixture/colony" "$fixture/bin" "$fixture/home" "$fixture/cache"
  cp "$WRAPPER" "$fixture/colony/run-tsx.sh"
  chmod +x "$fixture/colony/run-tsx.sh"
  for tool in npm npx; do
    cat >"$fixture/bin/$tool" <<'EOF'
#!/bin/bash
: >"$DYNAMIC_TOOL_SENTINEL"
exit 99
EOF
    chmod +x "$fixture/bin/$tool"
  done
  printf 'ERROR: local tsx is not installed; run npm ci in colony\n' >"$expected_stderr"

  set +e
  env -i \
    PATH="$fixture/bin:/usr/bin:/bin" \
    HOME="$fixture/home" \
    TMPDIR="$fixture" \
    DYNAMIC_TOOL_SENTINEL="$sentinel" \
    npm_config_offline=true \
    npm_config_cache="$fixture/cache" \
    /bin/bash "$fixture/colony/run-tsx.sh" \
    >"$stdout_file" 2>"$stderr_file"
  rc=$?
  set -e
  if [[ "$rc" -eq 127 ]] && [[ ! -s "$stdout_file" ]] &&
      cmp -s "$expected_stderr" "$stderr_file" && [[ ! -e "$sentinel" ]]; then
    record_pass "missing local tsx fails closed without npm or npx"
  else
    record_fail "missing local tsx boundary (exit $rc)"
  fi
}

check_dynamic_tsx_invocations() {
  local output="$TMPROOT/dynamic-tsx.txt"
  set +e
  "$PYTHON_BIN" - "$COLONY_ROOT" >"$output" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "smoke-test.sh",
    root / "bridge.test.ts",
    root / "bridge-cli.ts",
    root / "README.md",
    root / "conductor-prompt.md",
    root / "scripts" / "bootstrap-colony.ts",
    root / "scripts" / "capture-findings.ts",
]
patterns = [
    re.compile(r"\bnpx\s+tsx\b"),
    re.compile(
        r"execFileSync\s*\(\s*(['\"])npx\1\s*,\s*\[\s*(['\"])tsx\2",
        re.DOTALL,
    ),
]
findings = []
for path in paths:
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(root)}:{line}:{match.group(0)!r}")
if findings:
    print("\n".join(findings))
    raise SystemExit(1)
PY
  scan_rc=$?
  set -e
  if [[ "$scan_rc" -eq 0 ]] && [[ ! -s "$output" ]]; then
    record_pass "no dynamic tsx invocation"
  else
    record_fail "dynamic tsx invocation remains ($(tr '\n' ';' <"$output"))"
  fi
}

check_empty_vitest_suite() {
  local empty_root="$TMPROOT/empty-vitest"
  local stdout_file="$TMPROOT/empty-vitest.stdout"
  local stderr_file="$TMPROOT/empty-vitest.stderr"
  local rc
  mkdir -p "$empty_root"
  if [[ ! -x "$VITEST_BIN" ]]; then
    record_fail "local Vitest is unavailable for empty-suite proof"
    return
  fi
  set +e
  (
    cd "$empty_root" || exit 125
    "$VITEST_BIN" run --config "$COLONY_ROOT/vitest.config.ts"
  ) >"$stdout_file" 2>"$stderr_file"
  rc=$?
  set -e
  if [[ "$rc" -ne 0 ]] && grep -Fq 'No test files found' "$stderr_file"; then
    record_pass "empty Vitest suite fails"
  else
    record_fail "empty Vitest suite returned $rc"
  fi
}

TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/sdlc-colony-tooling.XXXXXX")"
TMPROOT="$(cd "$TMPROOT" && pwd -P)"
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

check_exact_pin
check_local_wrapper
check_missing_wrapper_binary
check_dynamic_tsx_invocations
check_empty_vitest_suite

printf '\nResults: %d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
printf 'COLONY_TOOLING_TESTS_PASS\n'
