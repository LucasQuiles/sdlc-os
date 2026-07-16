#!/usr/bin/env python3

import ast
import errno
import copy
import hashlib
import importlib.util
import json
import os
import platform
import re
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import venv
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run-verification.py"
if not RUNNER_PATH.is_file():
    raise FileNotFoundError(f"required verification runner is missing: {RUNNER_PATH}")

SPEC = importlib.util.spec_from_file_location("sdlc_verification_runner", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import verification runner: {RUNNER_PATH}")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

CURRENT_PLATFORM = "macos" if platform.system() == "Darwin" else "linux"
OTHER_PLATFORM = "linux" if CURRENT_PLATFORM == "macos" else "macos"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ERROR_CODE_RE = re.compile(
    r"^(?:F01|ROOT|PLUGIN|INVENTORY|VERIFY|CANDIDATE|CLEANUP)_[A-Z0-9_]+$"
)


PROBE_SOURCE = r"""#!/usr/bin/env python3
import json
import os
import signal
import sys
import time
from pathlib import Path

mode = os.environ.get("PROBE_MODE", "pass")
tmp = Path(os.environ["TMPDIR"])
tmp.mkdir(parents=True, exist_ok=True)

if mode == "pass":
    print("tests=3")
    print("probe diagnostic", file=sys.stderr)
    (tmp / "proof.json").write_text('{"ok":true}\n', encoding="utf-8")
elif mode == "exit":
    print("intentional exit")
    raise SystemExit(int(os.environ.get("PROBE_EXIT", "7")))
elif mode == "inconclusive":
    print("dependency unavailable")
    raise SystemExit(3)
elif mode == "zero":
    print("tests=0")
elif mode == "ambiguous":
    print("tests=2\ntests=3")
elif mode == "json":
    print(json.dumps({"outer": {"ok": True, "items": [1, 2]}}))
elif mode == "silent":
    pass
elif mode == "invalid-utf8":
    os.write(1, b"\xff\xfe")
elif mode == "timeout":
    print("partial-before-timeout", flush=True)
    child = os.fork()
    if child == 0:
        time.sleep(60)
        os._exit(0)
    print(f"child_pid={child}", flush=True)
    time.sleep(60)
elif mode == "background":
    child = os.fork()
    if child == 0:
        time.sleep(60)
        os._exit(0)
    print(f"child_pid={child}", flush=True)
elif mode == "setsid":
    child = os.fork()
    if child == 0:
        os.setsid()
        time.sleep(60)
        os._exit(0)
    print(f"escaped_pid={child}", flush=True)
    time.sleep(0.8)
elif mode == "setsid-transient":
    child = os.fork()
    if child == 0:
        os.setsid()
        time.sleep(0.3)
        os._exit(0)
    os.waitpid(child, 0)
    print("tests=1")
elif mode == "setsid-orphan":
    middle = os.fork()
    if middle == 0:
        orphan = os.fork()
        if orphan == 0:
            os.setsid()
            for descriptor in (0, 1, 2):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            time.sleep(60)
            os._exit(0)
        print(f"orphan_pid={orphan}", flush=True)
        os._exit(0)
    os.waitpid(middle, 0)
    print("tests=1")
elif mode == "signal":
    print("ready-for-signal", flush=True)
    time.sleep(60)
elif mode == "signal-ignore-term":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print("ready-for-signal", flush=True)
    time.sleep(60)
elif mode == "flood":
    os.write(1, b"x" * (20 * 1024 * 1024))
elif mode == "missing-artifact":
    print("tests=1")
elif mode == "symlink-artifact":
    target = tmp / "target.txt"
    target.write_text("sentinel", encoding="utf-8")
    (tmp / "proof.json").symlink_to(target)
    print("tests=1")
elif mode == "directory-artifact":
    (tmp / "proof.json").mkdir()
    print("tests=1")
elif mode == "large-artifact":
    (tmp / "proof.json").write_bytes(b"x" * 4096)
    print("tests=1")
elif mode == "tracked-mutation":
    Path("tracked.txt").write_text("mutated\n", encoding="utf-8")
    print("tests=1")
elif mode == "untracked-mutation":
    Path("unexpected.txt").write_text("created\n", encoding="utf-8")
    print("tests=1")
elif mode == "protected-mutation":
    Path(os.environ["PROTECTED_PATH"]).write_text("changed\n", encoding="utf-8")
    print("tests=1")
elif mode == "result-swap":
    check_dir = Path(os.environ["HOME"]).parents[1]
    held = check_dir.with_name(check_dir.name + ".held")
    victim = Path(os.environ["SWAP_VICTIM"])
    check_dir.rename(held)
    check_dir.symlink_to(victim, target_is_directory=True)
    print("tests=1")
else:
    raise SystemExit(f"unknown probe mode: {mode}")
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def production_error_codes() -> set[str]:
    runner_tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    emitted = set()

    class RunnerCodeCollector(ast.NodeVisitor):
        def visit_Assign(self, node):
            if any(
                isinstance(target, ast.Name) and target.id == "ERROR_CODES"
                for target in node.targets
            ):
                return
            self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str) and ERROR_CODE_RE.fullmatch(node.value):
                emitted.add(node.value)

    RunnerCodeCollector().visit(runner_tree)
    diagnostic_pattern = re.compile(
        r"(?:printf\s+|print\s*\(\s*)f?['\"]([A-Z][A-Z0-9_]+)(?=[:\\\s])"
    )
    diagnostic_paths = (
        PROJECT_ROOT / "scripts" / "check-plugin-metadata.py",
        PROJECT_ROOT / "scripts" / "check-repository-inventory.py",
        PROJECT_ROOT / "tests" / "lib" / "plugin-root.sh",
        PROJECT_ROOT / "tests" / "test-sdlc-dispatch.sh",
        PROJECT_ROOT / "tests" / "test-sdlc-dispatch-isolation.sh",
    )
    for path in diagnostic_paths:
        for code in diagnostic_pattern.findall(path.read_text(encoding="utf-8")):
            if ERROR_CODE_RE.fullmatch(code):
                emitted.add(code)
    emitted.difference_update(
        {
            "F01_FORCED_ASSERTION_AFTER_VALIDATOR_SWAP",
            "F01_FINGERPRINTS",
            "F01_SIDECAR_INVENTORY",
            "CLEANUP_SOURCE_UNPARSEABLE",
        }
    )
    return emitted


def wait_until(predicate, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return bool(predicate())


def pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class VerificationRepo:
    def __init__(self):
        self._temp = tempfile.TemporaryDirectory(prefix="verification-runner-test-")
        self.root = Path(self._temp.name).resolve()
        (self.root / "checks").mkdir()
        (self.root / "verification").mkdir()
        (self.root / ".gitignore").write_text(
            "/.verification-results/\n/artifacts/\n", encoding="utf-8"
        )
        (self.root / "checks" / "probe.py").write_text(PROBE_SOURCE, encoding="utf-8")
        (self.root / "tracked.txt").write_text("original\n", encoding="utf-8")
        (self.root / "verification" / "error-catalog.json").write_bytes(
            (PROJECT_ROOT / "verification" / "error-catalog.json").read_bytes()
        )
        self.git("init", "-q")
        self.git("config", "user.name", "Verification Test")
        self.git("config", "user.email", "verification@example.invalid")
        self.commit("initial fixture")
        self.run_counter = 0
        self.last_results: Path | None = None

    def close(self):
        self._temp.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def commit(self, message: str):
        self.git("add", "-A", "--", ".")
        staged = self.git("diff", "--cached", "--quiet", check=False)
        if staged.returncode != 0:
            self.git("commit", "-q", "-m", message)

    def base_row(self, check_id: str = "check-pass", **overrides):
        row = {
            "check_id": check_id,
            "stage": "1A",
            "requirement_ids": ["REQ-1"],
            "command": ["python3.12", "checks/probe.py"],
            "required_tools": ["python3.12", "git"],
            "working_directory": ".",
            "environment": {"PROBE_MODE": "pass"},
            "platforms": [CURRENT_PLATFORM],
            "applicability": {
                "state": "REQUIRED",
                "evidence": "synthetic verification-runner contract fixture",
            },
            "timeout_seconds": 10,
            "max_output_bytes": 1048576,
            "expected_exit": 0,
            "inconclusive_exit_codes": [],
            "expected_observation": {
                "type": "test_count_regex",
                "stream": "stdout",
                "pattern": r"tests=(\d+)",
                "min_count": 1,
            },
            "negative_falsifier": "Any wrong exit, missing count, or missing proof fails",
            "independence_requirement": "author-executable; independent release replay required",
            "required_artifacts": [
                {
                    "path": "proof.json",
                    "type": "file",
                    "min_bytes": 1,
                    "max_bytes": 1024,
                }
            ],
            "clean_source": False,
        }
        row.update(overrides)
        return row

    def base_manifest(self, checks=None, **overrides):
        if checks is None:
            checks = [self.base_row()]
        manifest = {
            "schema_version": "sdlc-os-verification-manifest-v1",
            "requirement_catalog": {
                "REQ-1": {
                    "source": "synthetic-test-contract",
                    "disposition": "REQUIRED",
                    "owner_release": "1A",
                    "closure_in_1a": True,
                }
            },
            "executable_allowlist": [
                {
                    "executable": "python3.12",
                    "argument_mode": "script",
                    "allowed_roots": ["checks", "scripts", "tests"],
                    "allowed_scripts": ["checks/probe.py"],
                },
                {
                    "executable": "bash",
                    "argument_mode": "script",
                    "allowed_roots": ["checks", "scripts", "tests", "colony"],
                    "allowed_scripts": [],
                },
                {
                    "executable": "git",
                    "argument_mode": "read_only",
                    "allowed_subcommands": [
                        "check-ignore",
                        "diff",
                        "rev-parse",
                        "status",
                    ],
                },
            ],
            "protected_ignored_paths": [],
            "checks": checks,
        }
        manifest.update(overrides)
        return manifest

    @property
    def manifest_path(self) -> Path:
        return self.root / "verification" / "manifest.json"

    def write_manifest(self, manifest, *, commit: bool = True):
        if isinstance(manifest, bytes):
            self.manifest_path.write_bytes(manifest)
        else:
            self.manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        if commit:
            self.commit("verification manifest")

    def runner_argv(
        self,
        *,
        stage: str = "1A",
        run_id: str | None = None,
        results: str | None = None,
        selected_platform: str = CURRENT_PLATFORM,
        extra: list[str] | None = None,
    ) -> list[str]:
        self.run_counter += 1
        if run_id is None:
            run_id = f"test-run-{os.getpid()}-{self.run_counter}"
        if results is None:
            results = f".verification-results/{run_id}"
        self.last_results = self.root / results
        argv = [
            sys.executable,
            str(RUNNER_PATH),
            "--manifest",
            "verification/manifest.json",
            "--stage",
            stage,
            "--platform",
            selected_platform,
            f"--run-id={run_id}",
            "--results-dir",
            results,
        ]
        if extra:
            argv.extend(extra)
        return argv

    def run(self, **kwargs) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        env["AMBIENT_PRIVATE_CANARY"] = "private-canary-must-not-leak"
        return subprocess.run(
            self.runner_argv(**kwargs),
            cwd=self.root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )

    def start(self, **kwargs) -> subprocess.Popen[bytes]:
        env = os.environ.copy()
        env["AMBIENT_PRIVATE_CANARY"] = "private-canary-must-not-leak"
        return subprocess.Popen(
            self.runner_argv(**kwargs),
            cwd=self.root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def receipt(self, check_id: str = "check-pass"):
        assert self.last_results is not None
        return json.loads(
            (self.last_results / check_id / "receipt.json").read_text(encoding="utf-8")
        )

    def summary(self):
        assert self.last_results is not None
        return json.loads((self.last_results / "run.json").read_text(encoding="utf-8"))


class VerificationRunnerCase(unittest.TestCase):
    def setUp(self):
        self.repo = VerificationRepo()

    def tearDown(self):
        self.repo.close()

    def run_row(self, row, **manifest_overrides):
        self.repo.write_manifest(self.repo.base_manifest([row], **manifest_overrides))
        return self.repo.run()

    def assert_mode(self, path: Path, expected: int):
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected, path)


class ManifestContractTests(VerificationRunnerCase):
    def test_cli_parser_errors_return_64(self):
        for argv in (["--unknown"], ["--run-id", "-leading"]):
            with self.subTest(argv=argv):
                result = subprocess.run(
                    [sys.executable, str(RUNNER_PATH), *argv],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 64)
                self.assertIn(b"VERIFY_MANIFEST_INVALID", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                for field in (
                    b"check=none",
                    b"run=none",
                    b"candidate=unknown",
                    b"where=runner",
                    b"what=",
                    b"evidence=none",
                    b"remediation=",
                ):
                    self.assertIn(field, result.stderr)

    def test_normal_run_rejects_error_catalog_drift(self):
        self.repo.write_manifest(self.repo.base_manifest())
        catalog_path = self.repo.root / "verification" / "error-catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["errors"].pop()
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.repo.commit("drift error catalog")

        result = self.repo.run()
        self.assertEqual(result.returncode, 64)
        self.assertIn(b"error catalog coverage drift", result.stderr)

    def test_rejects_invalid_manifest_shapes_and_injection(self):
        cases = {}

        def add(name, mutate, code="VERIFY_MANIFEST_INVALID"):
            value = self.repo.base_manifest()
            mutate(value)
            cases[name] = (value, code)

        add("unknown top key", lambda value: value.update({"extra": True}))
        add(
            "unknown row key",
            lambda value: value["checks"][0].update({"extra": True}),
        )
        add(
            "command string",
            lambda value: value["checks"][0].update({"command": "python probe.py"}),
        )
        add(
            "env executable",
            lambda value: value["checks"][0].update(
                {"command": ["env", "python3.12", "checks/probe.py"]}
            ),
        )
        add(
            "python command string",
            lambda value: value["checks"][0].update(
                {"command": ["python3.12", "-c", "print('bad')"]}
            ),
        )
        add(
            "shell command string",
            lambda value: value["checks"][0].update(
                {"command": ["bash", "-c", "exit 0"]}
            ),
        )
        add(
            "absolute cwd",
            lambda value: value["checks"][0].update({"working_directory": "/tmp"}),
            "VERIFY_RESULTS_ESCAPE",
        )
        add(
            "unknown requirement",
            lambda value: value["checks"][0].update({"requirement_ids": ["UNKNOWN"]}),
        )
        add(
            "empty requirements",
            lambda value: value["checks"][0].update({"requirement_ids": []}),
        )
        add(
            "empty falsifier",
            lambda value: value["checks"][0].update({"negative_falsifier": ""}),
        )
        add(
            "reserved environment",
            lambda value: value["checks"][0].update({"environment": {"LC_ALL": "C"}}),
            "VERIFY_ENV_INVALID",
        )
        add(
            "secret environment",
            lambda value: value["checks"][0].update(
                {"environment": {"API_TOKEN": "synthetic"}}
            ),
            "VERIFY_ENV_INVALID",
        )
        add(
            "unknown observation",
            lambda value: value["checks"][0].update(
                {"expected_observation": {"type": "anything"}}
            ),
        )
        add(
            "observation extra field",
            lambda value: value["checks"][0]["expected_observation"].update(
                {"value": "extra"}
            ),
        )
        add(
            "empty contains observation",
            lambda value: value["checks"][0].update(
                {
                    "expected_observation": {
                        "type": "contains",
                        "stream": "stdout",
                        "value": "",
                    }
                }
            ),
        )
        add(
            "inconclusive overlaps expected",
            lambda value: value["checks"][0].update({"inconclusive_exit_codes": [0]}),
        )
        add(
            "boolean timeout",
            lambda value: value["checks"][0].update({"timeout_seconds": True}),
        )
        add(
            "zero timeout",
            lambda value: value["checks"][0].update({"timeout_seconds": 0}),
        )
        add(
            "oversized timeout",
            lambda value: value["checks"][0].update({"timeout_seconds": 1801}),
        )
        add(
            "too many argv",
            lambda value: value["checks"][0].update(
                {"command": ["python3.12"] + ["x"] * 256}
            ),
        )
        add(
            "oversized argument",
            lambda value: value["checks"][0].update(
                {"command": ["python3.12", "x" * 8193]}
            ),
        )
        add(
            "oversized stream limit",
            lambda value: value["checks"][0].update({"max_output_bytes": 16777217}),
        )
        add(
            "empty applicability evidence",
            lambda value: value["checks"][0]["applicability"].update({"evidence": ""}),
        )
        add(
            "future schema",
            lambda value: value.update(
                {"schema_version": "sdlc-os-verification-manifest-v99"}
            ),
        )
        duplicate = self.repo.base_manifest(
            [self.repo.base_row("duplicate"), self.repo.base_row("duplicate")]
        )
        cases["duplicate check ID"] = (duplicate, "VERIFY_MANIFEST_INVALID")

        for name, (manifest, expected_code) in cases.items():
            with self.subTest(name=name):
                self.repo.write_manifest(manifest)
                result = self.repo.run()
                self.assertEqual(
                    result.returncode, 64, result.stderr.decode(errors="replace")
                )
                self.assertIn(expected_code.encode(), result.stderr)

    def test_script_allowlist_is_physically_contained_and_strictly_typed(self):
        outside = self.repo.root / "outside.py"
        outside.write_text("print('tests=1')\n", encoding="utf-8")
        self.repo.commit("outside allowlist fixture")
        traversal = self.repo.base_row(
            command=["python3.12", "checks/../outside.py"],
            required_artifacts=[],
        )
        self.repo.write_manifest(self.repo.base_manifest([traversal]))
        escaped = self.repo.run()
        self.assertEqual(escaped.returncode, 64, escaped.stderr)
        self.assertIn(b"VERIFY_MANIFEST_INVALID", escaped.stderr)

        malformed = self.repo.base_manifest()
        git_entry = next(
            entry
            for entry in malformed["executable_allowlist"]
            if entry["executable"] == "git"
        )
        git_entry["allowed_subcommands"] = 7
        self.repo.write_manifest(malformed)
        rejected = self.repo.run()
        self.assertEqual(rejected.returncode, 64, rejected.stderr)
        self.assertIn(b"VERIFY_MANIFEST_INVALID", rejected.stderr)
        self.assertNotIn(b"Traceback", rejected.stderr)

        module_escape = self.repo.base_row(
            command=[
                "python3.12",
                "-m",
                "unittest",
                "checks/../../outside.py",
            ],
            required_artifacts=[],
        )
        self.repo.write_manifest(self.repo.base_manifest([module_escape]))
        module_rejected = self.repo.run()
        self.assertEqual(module_rejected.returncode, 64, module_rejected.stderr)

        git_write = self.repo.base_row(
            command=["git", "diff", "--output=git-output.txt"],
            required_tools=["git"],
            required_artifacts=[],
            expected_observation={"type": "empty", "stream": "stdout"},
        )
        self.repo.write_manifest(self.repo.base_manifest([git_write]))
        git_rejected = self.repo.run()
        self.assertEqual(git_rejected.returncode, 64, git_rejected.stderr)

    def test_python_startup_flag_is_allowed_once_before_module_only(self):
        manifest = self.repo.base_manifest()
        python_entry = next(
            entry
            for entry in manifest["executable_allowlist"]
            if entry["executable"] == "python3.12"
        )
        python_entry["allowed_modules"] = ["unittest"]
        python_entry["allowed_flags"] = ["-S"]
        manifest["checks"][0]["command"] = [
            "python3.12",
            "-S",
            "-m",
            "unittest",
            "checks/probe.py",
        ]
        RUNNER.validate_manifest(manifest, self.repo.root)

        for command in (
            ["python3.12", "-S", "-S", "-m", "unittest", "checks/probe.py"],
            ["python3.12", "-m", "unittest", "-S", "checks/probe.py"],
            ["python3.12", "-E", "-m", "unittest", "checks/probe.py"],
            ["python3.12", "-S", "checks/probe.py"],
        ):
            with self.subTest(command=command):
                invalid = copy.deepcopy(manifest)
                invalid["checks"][0]["command"] = command
                with self.assertRaises(RUNNER.VerificationError):
                    RUNNER.validate_manifest(invalid, self.repo.root)

    def test_deferred_or_mutating_script_families_are_not_admissible(self):
        commands = [
            ["bash", "tests/test-fixture-regression.sh"],
            ["bash", "colony/validation/run-all.sh"],
            ["bash", "scripts/crossmodel-grid-down.sh", "--force"],
        ]
        for command in commands:
            with self.subTest(command=command):
                row = self.repo.base_row(
                    command=command,
                    required_tools=["bash"],
                    required_artifacts=[],
                )
                with self.assertRaises(RUNNER.VerificationError):
                    RUNNER.validate_manifest(
                        self.repo.base_manifest([row]), self.repo.root
                    )

    def test_stage_one_requirements_need_stage_one_rows_and_are_projected(self):
        deferred_only = self.repo.base_manifest([self.repo.base_row(stage="1B")])
        self.repo.write_manifest(deferred_only)
        rejected = self.repo.run(stage="1B")
        self.assertEqual(rejected.returncode, 64, rejected.stderr)
        self.assertIn(b"VERIFY_MANIFEST_INVALID", rejected.stderr)

        partial_row = self.repo.base_row(
            check_id="check-partial", requirement_ids=["REQ-PARTIAL"]
        )
        manifest = self.repo.base_manifest([self.repo.base_row(), partial_row])
        manifest["requirement_catalog"]["REQ-PARTIAL"] = {
            "source": "synthetic-partial-contract",
            "disposition": "PARTIAL",
            "owner_release": "1A",
            "closure_in_1a": False,
        }
        manifest["requirement_catalog"]["REQ-LATER"] = {
            "source": "synthetic-later-contract",
            "disposition": "DEFERRED",
            "owner_release": "1B",
            "closure_in_1a": False,
        }
        self.repo.write_manifest(manifest)
        result = self.repo.run()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = self.repo.summary()
        requirement = summary["requirements"]["REQ-1"]
        self.assertEqual(requirement["status"], "PASS")
        self.assertEqual(requirement["rows"][0]["check_id"], "check-pass")
        self.assertTrue(SHA256_RE.fullmatch(requirement["rows"][0]["receipt_sha256"]))
        partial = summary["requirements"]["REQ-PARTIAL"]
        self.assertEqual(partial["status"], "PARTIAL")
        self.assertEqual(partial["rows"][0]["verdict"], "PASS")
        self.assertEqual(summary["requirements"]["REQ-LATER"]["status"], "LATER_OWNED")
        self.assertEqual(
            summary["unmet_or_later_owned_requirements"],
            ["REQ-LATER", "REQ-PARTIAL"],
        )

    def test_rejects_strict_json_failures_and_bounds(self):
        valid = self.repo.base_manifest()
        encoded = json.dumps(valid, separators=(",", ":")).encode()
        malformed_cases = {
            "truncated": encoded[:-1],
            "invalid utf8": b"\xff" + encoded,
            "duplicate key": encoded.replace(
                b'"schema_version":',
                b'"schema_version":"sdlc-os-verification-manifest-v1","schema_version":',
                1,
            ),
            "nan": encoded.replace(b'"checks":', b'"nonfinite":NaN,"checks":', 1),
            "too large": b'{"schema_version":"' + b"x" * 1048576 + b'"}',
        }
        deep = (
            b'{"schema_version":"sdlc-os-verification-manifest-v1","x":'
            + (b"[" * 18 + b"0" + b"]" * 18)
            + b"}"
        )
        malformed_cases["too deep"] = deep

        for name, raw in malformed_cases.items():
            with self.subTest(name=name):
                self.repo.write_manifest(raw, commit=False)
                result = self.repo.run()
                self.assertEqual(result.returncode, 64)
                self.assertIn(b"VERIFY_MANIFEST_INVALID", result.stderr)

    def test_rejects_unsafe_results_run_id_platform_and_empty_selection(self):
        self.repo.write_manifest(self.repo.base_manifest())
        for run_id in ("../escape", "nested/run", ".", "-leading"):
            with self.subTest(run_id=run_id):
                self.assertFalse(SAFE_RUN_RE.fullmatch(run_id))
                result = self.repo.run(run_id=run_id)
                self.assertEqual(result.returncode, 64)

        existing = self.repo.root / ".verification-results" / "existing"
        existing.mkdir(parents=True)
        result = self.repo.run(
            run_id="existing", results=".verification-results/existing"
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn(b"VERIFY_RESULTS_ESCAPE", result.stderr)

        outside = Path(self.repo._temp.name).parent / f"outside-{os.getpid()}"
        result = self.repo.run(run_id="outside", results=str(outside))
        self.assertEqual(result.returncode, 64)

        symlink_parent = self.repo.root / "linked-results"
        target = self.repo.root / "real-results"
        target.mkdir()
        symlink_parent.symlink_to(target, target_is_directory=True)
        result = self.repo.run(run_id="linked", results="linked-results/linked")
        self.assertEqual(result.returncode, 64)

        result = self.repo.run(selected_platform=OTHER_PLATFORM)
        self.assertEqual(result.returncode, 64)
        self.assertIn(b"VERIFY_PLATFORM_MISMATCH", result.stderr)

        result = self.repo.run(stage="9Z")
        self.assertEqual(result.returncode, 64)
        self.assertIn(b"VERIFY_SELECTION_EMPTY", result.stderr)

    def test_platform_non_applicability_requires_evidence_and_is_not_vacuous_green(
        self,
    ):
        row = self.repo.base_row(
            platforms=[OTHER_PLATFORM],
            applicability={
                "state": "REQUIRED",
                "evidence": "fixture applies only on the other platform",
            },
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 3, result.stderr.decode(errors="replace"))
        receipt = self.repo.receipt()
        self.assertEqual(receipt["execution_state"], "NOT_APPLICABLE")
        self.assertEqual(receipt["verdict"], "NOT_APPLICABLE")
        self.assertEqual(self.repo.summary()["aggregate_verdict"], "INCONCLUSIVE")

    def test_observation_union_accepts_only_exact_variants(self):
        rows = [
            self.repo.base_row(
                "contains",
                required_artifacts=[],
                expected_observation={
                    "type": "contains",
                    "stream": "stdout",
                    "value": "tests=3",
                },
            ),
            self.repo.base_row(
                "regex",
                required_artifacts=[],
                expected_observation={
                    "type": "regex",
                    "stream": "stderr",
                    "pattern": r"probe diagnostic$",
                },
            ),
            self.repo.base_row(
                "count",
                required_artifacts=[],
            ),
            self.repo.base_row(
                "json-subset",
                environment={"PROBE_MODE": "json"},
                required_artifacts=[],
                expected_observation={
                    "type": "json_subset",
                    "stream": "stdout",
                    "value": {"outer": {"ok": True}},
                },
            ),
            self.repo.base_row(
                "empty",
                environment={"PROBE_MODE": "silent"},
                required_artifacts=[],
                expected_observation={"type": "empty", "stream": "stdout"},
            ),
        ]
        self.repo.write_manifest(self.repo.base_manifest(rows))
        result = self.repo.run()
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(self.repo.summary()["counts"]["PASS"], 5)


class ExecutionReceiptTests(VerificationRunnerCase):
    def test_pass_records_true_execution_and_protected_evidence(self):
        result = self.run_row(self.repo.base_row())
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertRegex(result.stdout.decode(), r"RUN_SHA256=[0-9a-f]{64}\n")
        receipt = self.repo.receipt()
        summary = self.repo.summary()
        self.assertEqual(receipt["schema_version"], "sdlc-os-verification-receipt-v1")
        self.assertEqual(receipt["command"], ["python3.12", "checks/probe.py"])
        self.assertEqual(receipt["working_directory"], ".")
        self.assertEqual(receipt["execution"]["exit_code"], 0)
        self.assertFalse(receipt["execution"]["timed_out"])
        self.assertGreaterEqual(receipt["execution"]["duration_monotonic_ns"], 0)
        self.assertEqual(
            receipt["execution"]["process_monitor"]["resolved"], "system:lsof"
        )
        self.assertTrue(
            SHA256_RE.fullmatch(receipt["execution"]["process_monitor"]["sha256"])
        )
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertEqual(
            receipt["source"]["candidate_sha"],
            self.repo.git("rev-parse", "HEAD").stdout.decode().strip(),
        )
        self.assertIn("dirty", receipt["source"])
        self.assertEqual(receipt["platform"]["os"], CURRENT_PLATFORM)
        self.assertTrue(receipt["platform"]["architecture"])
        self.assertGreaterEqual(len(receipt["tool_fingerprints"]), 2)
        self.assertTrue(SHA256_RE.fullmatch(receipt["manifest_sha256"]))
        self.assertTrue(SHA256_RE.fullmatch(receipt["manifest_row_sha256"]))
        self.assertTrue(SHA256_RE.fullmatch(receipt["runner_sha256"]))
        self.assertTrue(SHA256_RE.fullmatch(receipt["requirement_catalog_sha256"]))

        check_dir = self.repo.last_results / "check-pass"
        self.assert_mode(self.repo.last_results, 0o700)
        self.assert_mode(check_dir, 0o700)
        for name in ("stdout", "stderr", "environment.json", "receipt.json"):
            self.assert_mode(check_dir / name, 0o600)
        self.assertEqual(
            receipt["streams"]["stdout"]["sha256"], sha256_file(check_dir / "stdout")
        )
        self.assertEqual(
            receipt["streams"]["stderr"]["sha256"], sha256_file(check_dir / "stderr")
        )
        environment = json.loads((check_dir / "environment.json").read_text())
        self.assertEqual(environment["LC_ALL"], "C")
        self.assertEqual(environment["LANG"], "C")
        self.assertEqual(environment["TZ"], "UTC")
        self.assertNotIn("AMBIENT_PRIVATE_CANARY", environment)
        runtime_tmp = Path(environment["TMPDIR"])
        self.assertFalse(runtime_tmp.is_relative_to(self.repo.root))
        self.assertFalse(runtime_tmp.exists())
        structured = json.dumps(
            {"receipt": receipt, "summary": summary}, sort_keys=True
        )
        self.assertNotIn("private-canary-must-not-leak", structured)
        self.assertNotIn("probe diagnostic", structured)
        self.assertNotIn(str(Path.home()), structured)
        self.assertEqual(summary["aggregate_verdict"], "PASS")
        self.assertEqual(summary["counts"]["PASS"], 1)

    def test_structured_environment_tokenizes_declared_secret_like_values(self):
        marker = "ghp_secret-like-canary-must-never-be-serialized"
        row = self.repo.base_row(
            environment={
                "PROBE_MODE": "pass",
                "BUILD_NOTE": f"{marker}-${{CHECK_HOME}}",
            }
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        check_dir = self.repo.last_results / "check-pass"
        environment_bytes = (check_dir / "environment.json").read_bytes()
        receipt = self.repo.receipt()
        summary = self.repo.summary()
        structured = environment_bytes + json.dumps(
            {"receipt": receipt, "summary": summary}, sort_keys=True
        ).encode("utf-8")
        self.assertNotIn(marker.encode("utf-8"), structured)
        environment = json.loads(environment_bytes)
        self.assertRegex(environment["BUILD_NOTE"], r"\Aredacted:sha256:[0-9a-f]{64}\Z")
        self.assertEqual(environment["HOME"], "${CHECK_HOME}")
        self.assertEqual(environment["TMPDIR"], "${CHECK_TMPDIR}")

    def test_true_exit_inconclusive_and_fail_precedence(self):
        rows = [
            self.repo.base_row(
                "exit-seven",
                environment={"PROBE_MODE": "exit", "PROBE_EXIT": "7"},
                required_artifacts=[],
                expected_observation={
                    "type": "contains",
                    "stream": "stdout",
                    "value": "intentional exit",
                },
            ),
            self.repo.base_row(
                "declared-inconclusive",
                environment={"PROBE_MODE": "inconclusive"},
                required_artifacts=[],
                inconclusive_exit_codes=[3],
                expected_observation={
                    "type": "contains",
                    "stream": "stdout",
                    "value": "dependency unavailable",
                },
            ),
        ]
        self.repo.write_manifest(self.repo.base_manifest(rows))
        result = self.repo.run()
        self.assertEqual(result.returncode, 1)
        fail = self.repo.receipt("exit-seven")
        inconclusive = self.repo.receipt("declared-inconclusive")
        self.assertEqual(fail["execution"]["exit_code"], 7)
        self.assertEqual(fail["verdict"], "FAIL")
        self.assertEqual(fail["error_code"], "VERIFY_EXIT_MISMATCH")
        self.assertEqual(inconclusive["execution"]["exit_code"], 3)
        self.assertEqual(inconclusive["verdict"], "INCONCLUSIVE")
        self.assertEqual(self.repo.summary()["aggregate_verdict"], "FAIL")

    def test_zero_ambiguous_and_invalid_encoding_never_pass(self):
        cases = [
            ("zero", 1, "FAIL"),
            ("ambiguous", 1, "FAIL"),
            ("invalid-utf8", 3, "INCONCLUSIVE"),
        ]
        for mode, expected_exit, verdict in cases:
            with self.subTest(mode=mode):
                repo = VerificationRepo()
                try:
                    row = repo.base_row(
                        environment={"PROBE_MODE": mode},
                        required_artifacts=[],
                    )
                    repo.write_manifest(repo.base_manifest([row]))
                    result = repo.run()
                    self.assertEqual(result.returncode, expected_exit)
                    self.assertEqual(repo.receipt()["verdict"], verdict)
                finally:
                    repo.close()

    def test_required_artifacts_are_regular_bounded_and_no_follow(self):
        cases = [
            ("missing-artifact", 3),
            ("symlink-artifact", 3),
            ("directory-artifact", 3),
            ("large-artifact", 3),
        ]
        for mode, expected_exit in cases:
            with self.subTest(mode=mode):
                repo = VerificationRepo()
                try:
                    row = repo.base_row(
                        environment={"PROBE_MODE": mode},
                        required_artifacts=[
                            {
                                "path": "proof.json",
                                "type": "file",
                                "min_bytes": 1,
                                "max_bytes": 1024,
                            }
                        ],
                    )
                    repo.write_manifest(repo.base_manifest([row]))
                    result = repo.run()
                    self.assertEqual(result.returncode, expected_exit)
                    receipt = repo.receipt()
                    self.assertEqual(receipt["verdict"], "INCONCLUSIVE")
                    self.assertEqual(receipt["error_code"], "VERIFY_ARTIFACT_INVALID")
                finally:
                    repo.close()

    def test_dirty_and_child_source_mutations_are_nonpass(self):
        cases = ["tracked-mutation", "untracked-mutation"]
        for mode in cases:
            with self.subTest(mode=mode):
                repo = VerificationRepo()
                try:
                    row = repo.base_row(
                        environment={"PROBE_MODE": mode},
                        required_artifacts=[],
                    )
                    repo.write_manifest(repo.base_manifest([row]))
                    result = repo.run()
                    self.assertEqual(result.returncode, 1)
                    receipt = repo.receipt()
                    self.assertEqual(receipt["verdict"], "FAIL")
                    self.assertEqual(receipt["error_code"], "VERIFY_SOURCE_MUTATION")
                finally:
                    repo.close()

        row = self.repo.base_row(clean_source=True)
        self.repo.write_manifest(self.repo.base_manifest([row]))
        (self.repo.root / "tracked.txt").write_text(
            "dirty before run\n", encoding="utf-8"
        )
        result = self.repo.run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_SOURCE_DIRTY")

    def test_protected_ignored_mutation_is_detected(self):
        protected = self.repo.root / "artifacts"
        protected.mkdir()
        protected_file = protected / "protected.txt"
        protected_file.write_text("before\n", encoding="utf-8")
        row = self.repo.base_row(
            environment={
                "PROBE_MODE": "protected-mutation",
                "PROTECTED_PATH": "${REPO_ROOT}/artifacts/protected.txt",
            },
            required_artifacts=[],
        )
        result = self.run_row(row, protected_ignored_paths=["artifacts"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_SOURCE_MUTATION")

    def test_preexisting_verification_result_mutation_is_detected(self):
        prior = self.repo.root / ".verification-results" / "prior" / "receipt.json"
        prior.parent.mkdir(parents=True)
        prior.write_text("before\n", encoding="utf-8")
        row = self.repo.base_row(
            environment={
                "PROBE_MODE": "protected-mutation",
                "PROTECTED_PATH": "${REPO_ROOT}/.verification-results/prior/receipt.json",
            },
            required_artifacts=[],
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_SOURCE_MUTATION")

    def test_other_ignored_mutation_is_detected(self):
        ignored = self.repo.root / "dist" / "mutated.txt"
        ignored.parent.mkdir()
        ignored.write_text("before\n", encoding="utf-8")
        row = self.repo.base_row(
            environment={
                "PROBE_MODE": "protected-mutation",
                "PROTECTED_PATH": "${REPO_ROOT}/dist/mutated.txt",
            },
            required_artifacts=[],
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_SOURCE_MUTATION")

    def test_already_dirty_tracked_content_mutation_is_detected(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "tracked-mutation"},
            required_artifacts=[],
        )
        self.repo.write_manifest(self.repo.base_manifest([row]))
        (self.repo.root / "tracked.txt").write_text(
            "dirty before execution\n", encoding="utf-8"
        )
        result = self.repo.run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_SOURCE_MUTATION")


class ProcessLifecycleTests(VerificationRunnerCase):
    def _owned_pid_from_stdout(self, key: str) -> int:
        receipt = self.repo.receipt()
        stdout_path = self.repo.last_results / receipt["streams"]["stdout"]["path"]
        match = re.search(
            re.escape(key).encode("ascii") + rb"=(\d+)", stdout_path.read_bytes()
        )
        self.assertIsNotNone(match)
        return int(match.group(1))

    def test_timeout_kills_process_group_and_retains_partial_output(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "timeout"},
            timeout_seconds=1,
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "partial-before-timeout",
            },
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 3)
        receipt = self.repo.receipt()
        child_pid = self._owned_pid_from_stdout("child_pid")
        self.assertTrue(receipt["execution"]["timed_out"])
        self.assertEqual(receipt["error_code"], "VERIFY_TIMEOUT")
        self.assertTrue(wait_until(lambda: not pid_exists(child_pid)))

    def test_leader_exit_with_background_member_is_inconclusive(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "background"},
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "child_pid=",
            },
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 3)
        child_pid = self._owned_pid_from_stdout("child_pid")
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_BACKGROUND_PROCESS")
        self.assertTrue(wait_until(lambda: not pid_exists(child_pid)))

    def test_escaped_setsid_descendant_is_detected_and_cleaned(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "setsid"},
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "escaped_pid=",
            },
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 3, result.stderr.decode(errors="replace"))
        escaped_pid = self._owned_pid_from_stdout("escaped_pid")
        self.assertEqual(self.repo.receipt()["error_code"], "VERIFY_BACKGROUND_PROCESS")
        self.assertTrue(wait_until(lambda: not pid_exists(escaped_pid)))

    def test_cleaned_transient_setsid_child_does_not_false_fail(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "setsid-transient"},
            required_artifacts=[],
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(self.repo.receipt()["verdict"], "PASS")

    def test_reparented_setsid_descendant_is_detected_and_cleaned(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "setsid-orphan"},
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "orphan_pid=",
            },
        )
        result = self.run_row(row)
        orphan_pid = self._owned_pid_from_stdout("orphan_pid")
        try:
            self.assertEqual(
                result.returncode, 3, result.stderr.decode(errors="replace")
            )
            receipt = self.repo.receipt()
            self.assertEqual(receipt["error_code"], "VERIFY_BACKGROUND_PROCESS")
            self.assertGreaterEqual(
                receipt["execution"]["escaped_descendants_observed"], 1
            )
            self.assertTrue(wait_until(lambda: not pid_exists(orphan_pid)))
        finally:
            if pid_exists(orphan_pid):
                os.kill(orphan_pid, signal.SIGKILL)

    def test_orphan_cleanup_does_not_signal_unrelated_process(self):
        unrelated = subprocess.Popen(["/bin/sleep", "30"])
        orphan_pid = None
        try:
            row = self.repo.base_row(
                environment={"PROBE_MODE": "setsid-orphan"},
                required_artifacts=[],
                expected_observation={
                    "type": "contains",
                    "stream": "stdout",
                    "value": "orphan_pid=",
                },
            )
            result = self.run_row(row)
            orphan_pid = self._owned_pid_from_stdout("orphan_pid")
            self.assertEqual(
                result.returncode, 3, result.stderr.decode(errors="replace")
            )
            self.assertIsNone(unrelated.poll())
            self.assertTrue(wait_until(lambda: not pid_exists(orphan_pid)))
        finally:
            if orphan_pid is not None and pid_exists(orphan_pid):
                os.kill(orphan_pid, signal.SIGKILL)
            unrelated.terminate()
            unrelated.wait(timeout=5)

    def test_holder_identity_drift_refuses_signal(self):
        with mock.patch.object(
            RUNNER,
            "_ownership_holders",
            return_value={12345: (os.getuid(), "replacement-start")},
        ):
            with mock.patch.object(RUNNER.os, "kill") as kill:
                signaled = RUNNER._signal_verified_holder(
                    Path("/usr/sbin/lsof"),
                    Path("/tmp/owner.sock"),
                    12345,
                    (os.getuid(), "original-start"),
                    signal.SIGTERM,
                )
        self.assertFalse(signaled)
        kill.assert_not_called()

    def test_process_monitor_timeout_fails_closed(self):
        with mock.patch.object(
            RUNNER.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["lsof"], 2),
        ) as run:
            with self.assertRaises(RUNNER.VerificationError) as raised:
                RUNNER._ownership_holders(
                    Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                )
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")
        self.assertEqual(run.call_count, 3)

    def test_process_monitor_transient_timeout_retries_before_observing_holders(self):
        runner_pid = os.getpid()
        observed = subprocess.CompletedProcess(
            ["lsof"], 0, stdout=f"p{runner_pid}\n".encode(), stderr=b""
        )
        with mock.patch.object(
            RUNNER.subprocess,
            "run",
            side_effect=[subprocess.TimeoutExpired(["lsof"], 2), observed],
        ) as run:
            with mock.patch.object(
                RUNNER,
                "_process_start_identity",
                return_value=(os.getuid(), "runner-start"),
            ):
                holders = RUNNER._ownership_holders(
                    Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                )
        self.assertEqual(holders, {runner_pid: (os.getuid(), "runner-start")})
        self.assertEqual(run.call_count, 2)

    def test_process_monitor_transient_nonzero_retries_before_observing_holders(self):
        runner_pid = os.getpid()
        failed = subprocess.CompletedProcess(
            ["lsof"], 1, stdout=b"", stderr=b"transient inventory failure"
        )
        observed = subprocess.CompletedProcess(
            ["lsof"], 0, stdout=f"p{runner_pid}\n".encode(), stderr=b""
        )
        with mock.patch.object(
            RUNNER.subprocess, "run", side_effect=[failed, observed]
        ) as run:
            with mock.patch.object(
                RUNNER,
                "_process_start_identity",
                return_value=(os.getuid(), "runner-start"),
            ):
                holders = RUNNER._ownership_holders(
                    Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                )
        self.assertEqual(holders, {runner_pid: (os.getuid(), "runner-start")})
        self.assertEqual(run.call_count, 2)

    def test_process_monitor_persistent_nonzero_exhausts_bounded_retries(self):
        failed = subprocess.CompletedProcess(
            ["lsof"], 1, stdout=b"", stderr=b"persistent inventory failure"
        )
        with mock.patch.object(RUNNER.subprocess, "run", return_value=failed) as run:
            with self.assertRaises(RUNNER.VerificationError) as raised:
                RUNNER._ownership_holders(
                    Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                )
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")
        self.assertEqual(run.call_count, 3)

    def test_process_monitor_malformed_success_does_not_retry(self):
        malformed = subprocess.CompletedProcess(
            ["lsof"], 0, stdout=b"pnot-a-pid\n", stderr=b""
        )
        with mock.patch.object(RUNNER.subprocess, "run", return_value=malformed) as run:
            with self.assertRaises(RUNNER.VerificationError) as raised:
                RUNNER._ownership_holders(
                    Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                )
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")
        self.assertIn("malformed", str(raised.exception))
        self.assertEqual(run.call_count, 1)

    def test_process_monitor_missing_runner_lease_does_not_retry(self):
        other_pid = os.getpid() + 10_000
        observed = subprocess.CompletedProcess(
            ["lsof"], 0, stdout=f"p{other_pid}\n".encode(), stderr=b""
        )
        with mock.patch.object(RUNNER.subprocess, "run", return_value=observed) as run:
            with mock.patch.object(
                RUNNER,
                "_process_start_identity",
                return_value=(os.getuid(), "other-start"),
            ):
                with self.assertRaises(RUNNER.VerificationError) as raised:
                    RUNNER._ownership_holders(
                        Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                    )
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")
        self.assertIn("runner ownership lease is unobservable", str(raised.exception))
        self.assertEqual(run.call_count, 1)

    def test_process_holder_with_unreadable_identity_fails_closed(self):
        runner_pid = os.getpid()
        unreadable_pid = runner_pid + 10_000
        lsof_result = subprocess.CompletedProcess(
            ["lsof"],
            0,
            stdout=f"p{runner_pid}\np{unreadable_pid}\n".encode(),
            stderr=b"",
        )

        def identity_for(pid):
            if pid == runner_pid:
                return os.getuid(), "runner-start"
            return None

        with mock.patch.object(
            RUNNER.subprocess, "run", return_value=lsof_result
        ) as run:
            with mock.patch.object(
                RUNNER, "_process_start_identity", side_effect=identity_for
            ):
                with self.assertRaises(RUNNER.VerificationError) as raised:
                    RUNNER._ownership_holders(
                        Path("/usr/sbin/lsof"), Path("/tmp/owner.sock")
                    )
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")
        self.assertIn("identity is unavailable", str(raised.exception))
        self.assertEqual(run.call_count, 1)

    def test_darwin_process_identity_timeout_fails_closed(self):
        with mock.patch.object(RUNNER.platform, "system", return_value="Darwin"):
            with mock.patch.object(
                RUNNER.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(["/bin/ps"], 2),
            ):
                with self.assertRaises(RUNNER.VerificationError) as raised:
                    RUNNER._process_start_identity(12345)
        self.assertEqual(raised.exception.code, "VERIFY_BACKGROUND_PROCESS")

    def test_runner_sigint_terminates_group_and_writes_inconclusive_receipt(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "signal"},
            timeout_seconds=20,
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "ready-for-signal",
            },
        )
        self.repo.write_manifest(self.repo.base_manifest([row]))
        process = self.repo.start()
        try:
            stdout_file = self.repo.last_results / "check-pass" / "stdout"
            self.assertTrue(
                wait_until(
                    lambda: (
                        stdout_file.is_file()
                        and b"ready-for-signal" in stdout_file.read_bytes()
                    )
                )
            )
            os.kill(process.pid, signal.SIGINT)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 3, (stdout, stderr))
            receipt = self.repo.receipt()
            self.assertTrue(receipt["execution"]["interrupted"])
            self.assertEqual(receipt["error_code"], "VERIFY_INTERRUPTED")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    def test_runner_sigterm_escalates_to_kill_for_term_resistant_child(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "signal-ignore-term"},
            timeout_seconds=20,
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "ready-for-signal",
            },
        )
        self.repo.write_manifest(self.repo.base_manifest([row]))
        process = self.repo.start()
        try:
            stdout_file = self.repo.last_results / "check-pass" / "stdout"
            self.assertTrue(
                wait_until(
                    lambda: (
                        stdout_file.is_file()
                        and b"ready-for-signal" in stdout_file.read_bytes()
                    )
                )
            )
            os.kill(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=12)
            self.assertEqual(process.returncode, 3, (stdout, stderr))
            receipt = self.repo.receipt()
            self.assertTrue(receipt["execution"]["interrupted"])
            self.assertEqual(receipt["execution"]["signal"], signal.SIGKILL)
            self.assertEqual(receipt["error_code"], "VERIFY_INTERRUPTED")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    def test_output_limit_terminates_without_green(self):
        row = self.repo.base_row(
            environment={"PROBE_MODE": "flood"},
            max_output_bytes=8192,
            required_artifacts=[],
            expected_observation={
                "type": "contains",
                "stream": "stdout",
                "value": "x",
            },
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 3)
        receipt = self.repo.receipt()
        self.assertEqual(receipt["error_code"], "VERIFY_OUTPUT_LIMIT")
        stdout_path = self.repo.last_results / receipt["streams"]["stdout"]["path"]
        self.assertLessEqual(stdout_path.stat().st_size, 8192)
        self.assertTrue((self.repo.last_results / "run.json").is_file())


class DurabilityContainmentPrivacyTests(VerificationRunnerCase):
    def test_atomic_writer_retries_short_write_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            directory_fd = os.open(directory_path, os.O_RDONLY | os.O_DIRECTORY)
            try:
                original_write = os.write
                calls = 0

                def short_write(fd, data):
                    nonlocal calls
                    calls += 1
                    if calls == 1 and len(data) > 1:
                        return original_write(fd, data[: len(data) // 2])
                    return original_write(fd, data)

                with mock.patch.object(RUNNER.os, "write", side_effect=short_write):
                    result = RUNNER.atomic_write_at(
                        directory_fd, "short.json", b"abcdef"
                    )
                self.assertEqual(
                    (directory_path / "short.json").read_bytes(), b"abcdef"
                )
                self.assertEqual(result["bytes"], 6)

                faults = [
                    ("write", OSError(errno.ENOSPC, "synthetic no space")),
                    ("fsync", OSError(errno.EIO, "synthetic fsync")),
                    ("replace", OSError(errno.EIO, "synthetic rename")),
                ]
                for method, error in faults:
                    with self.subTest(method=method):
                        with mock.patch.object(RUNNER.os, method, side_effect=error):
                            with self.assertRaises(RUNNER.EvidenceWriteError):
                                RUNNER.atomic_write_at(
                                    directory_fd, f"fault-{method}.json", b"value"
                                )
            finally:
                os.close(directory_fd)

    def test_summary_write_failure_returns_70_without_success_digest(self):
        row = self.repo.base_row()
        self.repo.write_manifest(self.repo.base_manifest([row]))
        argv = self.repo.runner_argv()[2:]
        original = RUNNER.atomic_write_at

        def fail_summary(directory_fd, name, data, *args, **kwargs):
            if name == "run.json":
                raise RUNNER.EvidenceWriteError("synthetic summary failure")
            return original(directory_fd, name, data, *args, **kwargs)

        previous = Path.cwd()
        os.chdir(self.repo.root)
        try:
            with mock.patch.object(RUNNER, "atomic_write_at", side_effect=fail_summary):
                with mock.patch("sys.stdout") as stdout:
                    rc = RUNNER.main(argv)
            self.assertEqual(rc, 70)
            stdout.write.assert_not_called()
            receipt_path = self.repo.last_results / "check-pass" / "receipt.json"
            self.assertTrue(receipt_path.is_file())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["verdict"], "PASS")
            self.assertFalse((self.repo.last_results / "run.json").exists())
        finally:
            os.chdir(previous)

    def test_monotonic_duration_ignores_wall_clock_regression(self):
        with mock.patch.object(RUNNER.time, "time_ns", side_effect=[1000, 100]):
            with mock.patch.object(RUNNER.time, "monotonic_ns", side_effect=[50, 75]):
                timing = RUNNER.capture_timing(lambda: None)
        self.assertEqual(timing["duration_monotonic_ns"], 25)
        self.assertGreaterEqual(timing["duration_monotonic_ns"], 0)

    def test_post_open_result_path_swap_cannot_redirect_receipt_writes(self):
        victim = self.repo.root / "swap-victim"
        victim.mkdir()
        sentinel = victim / "sentinel.txt"
        sentinel.write_text("unchanged\n", encoding="utf-8")
        row = self.repo.base_row(
            environment={
                "PROBE_MODE": "result-swap",
                "SWAP_VICTIM": "${REPO_ROOT}/swap-victim",
            },
            required_artifacts=[],
        )
        result = self.run_row(row)
        self.assertEqual(result.returncode, 70)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged\n")
        self.assertFalse((victim / "receipt.json").exists())
        held = self.repo.last_results / "check-pass.held"
        self.assertTrue(held.is_dir())
        self.assertTrue((held / "stdout").is_file())


class CommittedAuthorityTests(VerificationRunnerCase):
    def test_python_unit_rows_ignore_ambient_tests_package(self):
        manifest = json.loads(
            (PROJECT_ROOT / "verification" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        rows = {row["check_id"]: row for row in manifest["checks"]}
        expected = {
            "s1a-metadata-unit": [
                "python3.12",
                "-S",
                "-m",
                "unittest",
                "tests/test_metadata_inventory.py",
                "-v",
            ],
            "s1a-verification-runner-contracts": [
                "python3.12",
                "-S",
                "-m",
                "unittest",
                "tests/test_verification_runner.py",
                "-v",
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            environment_root = Path(temp_dir) / "python"
            venv.EnvBuilder(with_pip=False).create(environment_root)
            python = environment_root / "bin" / "python3.12"
            purelib = subprocess.run(
                [
                    str(python),
                    "-c",
                    "import sysconfig; print(sysconfig.get_path('purelib'))",
                ],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            shadow = Path(purelib) / "tests"
            shadow.mkdir()
            (shadow / "__init__.py").write_text("", encoding="utf-8")

            command = [str(python), *rows["s1a-metadata-unit"]["command"][1:]]
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                result.stderr.decode(errors="replace"),
            )
            self.assertRegex(result.stderr, rb"(?m)^Ran 8 tests in [0-9.]+s$")

        for check_id, command in expected.items():
            with self.subTest(check_id=check_id):
                self.assertEqual(rows[check_id]["command"], command)

    def test_python_unit_rows_disable_repository_bytecode(self):
        manifest = json.loads(
            (PROJECT_ROOT / "verification" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        rows = {row["check_id"]: row for row in manifest["checks"]}
        expected = {
            "s1a-metadata-unit",
            "s1a-verification-runner-contracts",
        }
        declared = {
            row["check_id"]
            for row in manifest["checks"]
            if row["environment"].get("PYTHONDONTWRITEBYTECODE") == "1"
        }
        self.assertEqual(declared, expected)
        for check_id in expected:
            with self.subTest(check_id=check_id):
                self.assertEqual(
                    rows[check_id]["environment"].get("PYTHONDONTWRITEBYTECODE"),
                    "1",
                )

    def test_final_correction_findings_are_accounted_without_hiding_residual(self):
        inventory = json.loads(
            (PROJECT_ROOT / "verification" / "baseline-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        findings = {item["stable_id"]: item for item in inventory["items"]}
        for stable_id in ("P27-35", "P27-36", "P27-37", "P27-38", "P27-40"):
            with self.subTest(stable_id=stable_id):
                finding = findings[stable_id]
                self.assertEqual(finding["affected_stage_release"], "1A")
                self.assertEqual(finding["disposition"], "RESOLVED_1A")
                self.assertEqual(finding["current_verdict"], "PASS")
                self.assertTrue(finding["evidence"].strip())
                self.assertTrue(finding["closure_proof"].strip())

        residual = findings["P27-39"]
        self.assertEqual(residual["affected_stage_release"], "1C")
        self.assertEqual(residual["current_verdict"], "INCONCLUSIVE")
        self.assertEqual(residual["disposition"], "ACCEPTED_RESIDUAL_DEFERRED_TO_1C")
        self.assertTrue(residual["trigger_or_due"].strip())
        self.assertTrue(residual["closure_proof"].strip())

    def test_authority_files_validate_and_deferred_commands_stay_out(self):
        verification = PROJECT_ROOT / "verification"
        files = {
            "manifest": verification / "manifest.json",
            "catalog": verification / "error-catalog.json",
            "inventory": verification / "baseline-inventory.json",
            "review": verification / "review-state.json",
            "review_schema": verification / "review-result.schema.json",
        }
        for name, path in files.items():
            with self.subTest(name=name):
                self.assertTrue(path.is_file(), path)
                RUNNER.strict_json_load(path.read_bytes(), str(path))
        manifest = RUNNER.strict_json_load(files["manifest"].read_bytes(), "manifest")
        RUNNER.validate_manifest(manifest, PROJECT_ROOT)
        catalog = RUNNER.strict_json_load(files["catalog"].read_bytes(), "catalog")
        inventory = RUNNER.strict_json_load(
            files["inventory"].read_bytes(), "inventory"
        )
        review = RUNNER.strict_json_load(files["review"].read_bytes(), "review")
        RUNNER.validate_error_catalog(catalog)
        RUNNER.validate_baseline_inventory(inventory)
        RUNNER.validate_review_state(review)
        mandatory_commands = [
            row["command"] for row in manifest["checks"] if row["stage"] == "1A"
        ]
        direct_f01 = next(
            row
            for row in manifest["checks"]
            if row["check_id"] == "s1a-f01-direct-sidecar"
        )
        self.assertEqual(direct_f01["environment"].get("F01_EMIT_FINGERPRINTS"), "1")
        self.assertEqual(direct_f01["expected_observation"]["type"], "regex")
        with tempfile.TemporaryDirectory(prefix="f01-receipt-binding-") as tmpdir:
            environment = os.environ.copy()
            environment.update(
                {
                    "F01_TEST_MODE": "assert",
                    "F01_EMIT_FINGERPRINTS": "1",
                    "SDLC_INSTALLED_PLUGIN_ROOT": str(
                        Path(tmpdir) / "no-installed-plugin"
                    ),
                    "TMPDIR": tmpdir,
                }
            )
            f01_result = subprocess.run(
                ["/bin/bash", "tests/test-sdlc-dispatch-isolation.sh"],
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
        self.assertEqual(f01_result.returncode, 0, f01_result.stderr.decode())
        self.assertRegex(
            f01_result.stdout.decode("utf-8"),
            direct_f01["expected_observation"]["pattern"],
        )
        self.assertIn(b"installed=NOT_APPLICABLE", f01_result.stdout)
        signal_rows = {
            row["environment"].get("F01_TEST_SIGNAL"): row
            for row in manifest["checks"]
            if row["environment"].get("F01_TEST_SIGNAL") in {"HUP", "INT", "TERM"}
        }
        self.assertEqual(set(signal_rows), {"HUP", "INT", "TERM"})
        for signal_name, row in signal_rows.items():
            with self.subTest(f01_signal=signal_name):
                observation = row["expected_observation"]
                self.assertEqual(observation["type"], "contains")
                self.assertIn(f"signal={signal_name}", observation["value"])
        vitest_row = next(
            row
            for row in manifest["checks"]
            if row["check_id"] == "s1a-vitest-discovered-suite"
        )
        self.assertEqual(
            vitest_row["command"],
            [
                "./node_modules/.bin/vitest",
                "run",
                "--no-cache",
                "--configLoader",
                "runner",
            ],
        )
        self.assertEqual(vitest_row["expected_observation"]["min_count"], 154)
        tooling_source = (PROJECT_ROOT / "tests/test-colony-tooling.sh").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            tooling_source,
            r'(?m)^\s*"\$VITEST_BIN" run --no-cache --configLoader runner \\$',
        )
        joined = "\n".join(" ".join(command) for command in mandatory_commands)
        self.assertNotIn(
            ["bash", "tests/test-fixture-regression.sh"], mandatory_commands
        )
        self.assertNotIn(["bash", "colony/validation/run-all.sh"], mandatory_commands)
        self.assertNotIn("clone-security", joined)
        self.assertIn("colony/node_modules", manifest["protected_ignored_paths"])
        for requirement_id in {
            "S1-03",
            "AP-10",
            "AP-16",
            "S1-07",
            "AP-11",
            "AP-13",
        }:
            with self.subTest(partial_requirement=requirement_id):
                authority = manifest["requirement_catalog"][requirement_id]
                self.assertEqual(authority["disposition"], "PARTIAL")
                self.assertEqual(authority["owner_release"], "1A")
                self.assertFalse(authority["closure_in_1a"])
        ap24 = manifest["requirement_catalog"]["AP-24"]
        self.assertEqual(ap24["disposition"], "REQUIRED")
        self.assertEqual(ap24["owner_release"], "Task8")
        self.assertFalse(ap24["closure_in_1a"])
        self.assertFalse(
            any("AP-24" in row["requirement_ids"] for row in manifest["checks"])
        )
        for index, command in enumerate(
            (
                ["bash", "tests/test-fixture-regression.sh"],
                ["bash", "colony/validation/run-all.sh"],
                ["bash", "scripts/crossmodel-grid-down.sh", "--force"],
            )
        ):
            with self.subTest(prohibited_command=command):
                mutated = copy.deepcopy(manifest)
                row = copy.deepcopy(mutated["checks"][0])
                row["check_id"] = f"prohibited-command-{index}"
                row["command"] = command
                row["required_tools"] = ["bash"]
                mutated["checks"].append(row)
                with self.assertRaises(RUNNER.VerificationError):
                    RUNNER.validate_manifest(mutated, PROJECT_ROOT)
        self.assertTrue(
            any(item["stable_id"] == "P27-01" for item in inventory["items"])
        )
        p27 = next(item for item in inventory["items"] if item["stable_id"] == "P27-01")
        self.assertEqual(p27["affected_stage_release"], "1B")
        self.assertIn("OWNER", p27["disposition"])

    def test_gitignore_and_readme_cli_examples(self):
        gitignore = (
            (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        )
        self.assertIn("/.verification-results/", gitignore)
        self.assertIn("/artifacts/", gitignore)
        self.assertNotIn("/verification/", gitignore)
        readme = (PROJECT_ROOT / "verification" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("python3.12 scripts/run-verification.py", readme)
        self.assertIn("--validate-review-result", readme)
        self.assertIn("--validate-run-result", readme)
        self.assertIn("EXPECTED_BUNDLE_SHA256", readme)
        self.assertIn("git bundle verify", readme)
        self.assertIn("git switch --detach", readme)
        self.assertIn("brew --prefix node@20", readme)
        self.assertIn("command -v lsof", readme)
        prepare_section = re.search(
            r"## Prepare an Immutable Candidate\n.*?```bash\n(.*?)\n```",
            readme,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(prepare_section)
        self.assertIn("set -euo pipefail", prepare_section.group(1))
        self.assertNotIn("npm ci", prepare_section.group(1))
        self.assertIsNotNone(
            re.search(
                r'NODE20_BIN=.*?test .*?v20\.20\.2.*?PATH="\$NODE20_BIN:\$PATH" npm ci',
                readme,
                flags=re.DOTALL,
            )
        )
        self.assertIn("unmet_or_later_owned_requirements", readme)
        self.assertIn("VERIFY_SOURCE_MUTATION", readme)

        manifest = json.loads(
            (PROJECT_ROOT / "verification" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        script_section = re.search(
            r"### Exact Script Allowlist\n\n```text\n(.*?)\n```",
            readme,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(script_section, "missing exact script allowlist")
        documented_scripts = set(script_section.group(1).splitlines())
        expected_scripts = {
            f"{entry['executable']} {script}"
            for entry in manifest["executable_allowlist"]
            if entry["argument_mode"] == "script"
            for script in entry["allowed_scripts"]
        }
        self.assertEqual(documented_scripts, expected_scripts)

        def parse_readme_command(section: str):
            match = re.search(
                rf"## {re.escape(section)}\n.*?```bash\n(.*?)\n```",
                readme,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, f"missing bash example for {section}")
            command = re.sub(r"\\\n\s*", " ", match.group(1))
            tokens = shlex.split(command)
            python_index = tokens.index("python3.12")
            self.assertEqual(tokens[python_index + 1], "scripts/run-verification.py")
            argv = tokens[python_index:]
            return (
                RUNNER.build_parser().parse_args(argv[2:]),
                argv,
                tokens[:python_index],
            )

        release_args, macos_release_command, _ = parse_readme_command("Run Release 1A")
        self.assertEqual(release_args.stage, "1A")
        self.assertEqual(release_args.platform, "macos")
        self.assertEqual(release_args.run_id, "$RUN_ID")
        self.assertEqual(release_args.results_dir, ".verification-results/$RUN_ID")
        linux_args, linux_release_command, linux_prefix = parse_readme_command(
            "Run Release 1A on Linux"
        )
        self.assertEqual(linux_args.stage, "1A")
        self.assertEqual(linux_args.platform, "linux")
        self.assertEqual(linux_args.run_id, "$RUN_ID")
        self.assertEqual(linux_args.results_dir, ".verification-results/$RUN_ID")
        self.assertIn("TMPDIR=/tmp", linux_prefix)
        review_args, review_command, _ = parse_readme_command(
            "Validate a Review Result"
        )
        self.assertEqual(
            review_args.validate_review_result,
            ".verification-results/<candidate>-reviews/independent.json",
        )
        self.assertEqual(review_args.candidate, "<full-candidate-sha>")

        scripts_dir = self.repo.root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run-verification.py").write_bytes(RUNNER_PATH.read_bytes())
        self.repo.write_manifest(self.repo.base_manifest())
        run_id = f"readme-example-{os.getpid()}"
        release_command = (
            macos_release_command
            if CURRENT_PLATFORM == "macos"
            else linux_release_command
        )
        executable_release = [
            token.replace("$RUN_ID", run_id) for token in release_command
        ]
        example_environment = os.environ.copy()
        example_environment["PATH"] = (
            f"/opt/homebrew/opt/node@20/bin:{example_environment['PATH']}"
        )
        if CURRENT_PLATFORM == "linux":
            example_environment["TMPDIR"] = "/tmp"
        release_result = subprocess.run(
            executable_release,
            cwd=self.repo.root,
            env=example_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(release_result.returncode, 0, release_result.stderr.decode())
        self.assertRegex(
            release_result.stdout.decode("ascii"), r"\ARUN_SHA256=[0-9a-f]{64}\n\Z"
        )

        candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        executable_review = [
            candidate if token == "<full-candidate-sha>" else token
            for token in review_command
        ]
        review_result = subprocess.run(
            executable_review,
            cwd=self.repo.root,
            env=example_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(review_result.returncode, 64)
        self.assertIn(b"review result", review_result.stderr)
        self.assertNotIn(b"Traceback", review_result.stderr)
        help_result = subprocess.run(
            [sys.executable, str(RUNNER_PATH), "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(b"--validate-review-result", help_result.stdout)
        self.assertIn(b"--validate-run-result", help_result.stdout)

    def test_run_result_validation_is_candidate_and_content_bound(self):
        result = self.run_row(self.repo.base_row())
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        match = re.fullmatch(rb"RUN_SHA256=([0-9a-f]{64})\n", result.stdout)
        self.assertIsNotNone(match)
        run_sha256 = match.group(1).decode("ascii")
        candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        run_path = self.repo.last_results / "run.json"
        relative_run = run_path.relative_to(self.repo.root).as_posix()

        def validate(expected_sha=run_sha256):
            return subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_PATH),
                    "--validate-run-result",
                    relative_run,
                    "--run-sha256",
                    expected_sha,
                    "--candidate",
                    candidate,
                ],
                cwd=self.repo.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        valid = validate()
        self.assertEqual(valid.returncode, 0, valid.stderr.decode(errors="replace"))
        self.assertEqual(valid.stdout, b"RUN_RESULT_VALID\n")
        mismatch = validate("f" * 64)
        self.assertEqual(mismatch.returncode, 64)
        self.assertIn(b"VERIFY_ARTIFACT_INVALID", mismatch.stderr)

        receipt_path = self.repo.last_results / "check-pass" / "receipt.json"
        receipt_path.write_bytes(receipt_path.read_bytes() + b" ")
        changed = validate()
        self.assertEqual(changed.returncode, 64)
        self.assertIn(b"VERIFY_ARTIFACT_INVALID", changed.stderr)

    def test_run_result_validation_rejects_omitted_rows_and_evidence(self):
        rows = [
            self.repo.base_row("check-one"),
            self.repo.base_row("check-two"),
        ]
        self.repo.write_manifest(self.repo.base_manifest(rows))
        result = self.repo.run()
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        run_path = self.repo.last_results / "run.json"
        relative_run = run_path.relative_to(self.repo.root).as_posix()
        original_run = run_path.read_bytes()
        original_receipt = (
            self.repo.last_results / "check-one" / "receipt.json"
        ).read_bytes()

        def validate_current():
            return subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_PATH),
                    "--validate-run-result",
                    relative_run,
                    "--run-sha256",
                    sha256_file(run_path),
                    "--candidate",
                    candidate,
                ],
                cwd=self.repo.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        omitted = json.loads(original_run)
        omitted["checks"] = omitted["checks"][1:]
        omitted["counts"]["PASS"] = 1
        run_path.write_bytes(RUNNER.canonical_json_bytes(omitted))
        self.assertEqual(validate_current().returncode, 64)

        run_path.write_bytes(original_run)
        receipt_path = self.repo.last_results / "check-one" / "receipt.json"
        receipt = json.loads(original_receipt)
        receipt.pop("streams")
        receipt.pop("environment_artifact")
        receipt_path.write_bytes(RUNNER.canonical_json_bytes(receipt))
        summary = json.loads(original_run)
        summary["checks"][0]["receipt_sha256"] = sha256_file(receipt_path)
        run_path.write_bytes(RUNNER.canonical_json_bytes(summary))
        self.assertEqual(validate_current().returncode, 64)

    def test_review_result_validation_is_candidate_bound(self):
        self.repo.write_manifest(self.repo.base_manifest())
        review_schema_path = (
            self.repo.root / "verification" / "review-result.schema.json"
        )
        review_schema_bytes = (
            PROJECT_ROOT / "verification" / "review-result.schema.json"
        ).read_bytes()
        review_schema_path.write_bytes(review_schema_bytes)
        self.repo.commit("review result schema fixture")
        candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        manifest = json.loads(self.repo.manifest_path.read_text(encoding="utf-8"))
        review_dir = self.repo.root / ".verification-results" / "candidate-reviews"
        review_dir.mkdir(parents=True)
        evidence = review_dir / "review.txt"
        evidence.write_text("independent replay evidence\n", encoding="utf-8")
        payload = {
            "schema_version": "sdlc-os-review-result-v1",
            "candidate_sha": candidate,
            "manifest_sha256": sha256_file(self.repo.manifest_path),
            "requirement_catalog_sha256": hashlib.sha256(
                RUNNER.canonical_json_bytes(manifest["requirement_catalog"])
            ).hexdigest(),
            "reviewer": {
                "runtime": "independent-runtime",
                "method": "source-and-command-replay",
            },
            "commands": [{"argv": ["bash", "tests/example.sh"], "exit_code": 0}],
            "material_claims": [
                {
                    "claim": "example claim",
                    "file_line": "tracked.txt:1",
                    "symbol_or_test": "example",
                    "file_sha256": sha256_file(self.repo.root / "tracked.txt"),
                }
            ],
            "findings": [
                {
                    "finding": "synthetic finding",
                    "severity": "NONMATERIAL",
                    "disposition": "REJECTED",
                    "evidence": "review.txt",
                    "owner": "reviewer",
                    "due_trigger": "before the candidate verdict",
                    "closure_proof": "review.txt records the reproduced result",
                }
            ],
            "limitations": ["synthetic fixture"],
            "protected_evidence_hashes": {"review.txt": sha256_file(evidence)},
            "verdict": "PASS",
        }
        path = review_dir / "review.json"

        def validate(value, asserted_candidate=candidate):
            path.write_text(json.dumps(value), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_PATH),
                    "--validate-review-result",
                    path.relative_to(self.repo.root).as_posix(),
                    "--candidate",
                    asserted_candidate,
                ],
                cwd=self.repo.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        result = validate(payload)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        mismatch = validate(payload, "f" * 40)
        self.assertEqual(mismatch.returncode, 64)
        self.assertIn(b"CANDIDATE_MISMATCH", mismatch.stderr)

        cases = {
            "candidate not HEAD": lambda value: value.update(
                {"candidate_sha": "a" * 40}
            ),
            "manifest hash": lambda value: value.update({"manifest_sha256": "b" * 64}),
            "catalog hash": lambda value: value.update(
                {"requirement_catalog_sha256": "c" * 64}
            ),
            "claim path": lambda value: value["material_claims"][0].update(
                {"file_line": "missing.txt:1"}
            ),
            "claim line": lambda value: value["material_claims"][0].update(
                {"file_line": "tracked.txt:99"}
            ),
            "claim hash": lambda value: value["material_claims"][0].update(
                {"file_sha256": "d" * 64}
            ),
            "finding shape": lambda value: value["findings"][0].update(
                {"severity": "HIGH"}
            ),
            "finding owner": lambda value: value["findings"][0].update({"owner": ""}),
            "finding due": lambda value: value["findings"][0].update(
                {"due_trigger": ""}
            ),
            "finding closure": lambda value: value["findings"][0].update(
                {"closure_proof": ""}
            ),
            "evidence missing": lambda value: value["protected_evidence_hashes"].update(
                {"missing.txt": value["protected_evidence_hashes"].pop("review.txt")}
            ),
            "evidence hash": lambda value: value["protected_evidence_hashes"].update(
                {"review.txt": "e" * 64}
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                invalid = copy.deepcopy(payload)
                mutate(invalid)
                rejected = validate(invalid)
                self.assertEqual(rejected.returncode, 64, rejected.stderr)

        no_evidence = copy.deepcopy(payload)
        no_evidence["protected_evidence_hashes"] = {}
        self.assertEqual(validate(no_evidence).returncode, 64)

        unresolved = copy.deepcopy(payload)
        unresolved["findings"][0].update(
            {"severity": "MATERIAL", "disposition": "UNRESOLVED"}
        )
        self.assertEqual(validate(unresolved).returncode, 64)

        drifted_schema = json.loads(review_schema_path.read_text(encoding="utf-8"))
        drifted_schema["properties"]["findings"]["items"]["required"].remove("owner")
        review_schema_path.write_text(json.dumps(drifted_schema), encoding="utf-8")
        self.repo.commit("drift review schema")
        drift_candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        drift_payload = copy.deepcopy(payload)
        drift_payload["candidate_sha"] = drift_candidate
        drift = validate(drift_payload, drift_candidate)
        self.assertEqual(drift.returncode, 64)
        self.assertIn(b"review result schema differs from runtime", drift.stderr)

        review_schema_path.write_bytes(review_schema_bytes)
        self.repo.commit("restore review schema")

        unrelated = self.repo.root / "unrelated.txt"
        unrelated.write_text("committed\n", encoding="utf-8")
        self.repo.commit("unrelated review fixture")
        new_candidate = self.repo.git("rev-parse", "HEAD").stdout.decode().strip()
        clean_payload = copy.deepcopy(payload)
        clean_payload["candidate_sha"] = new_candidate
        unrelated.write_text("dirty\n", encoding="utf-8")
        dirty = validate(clean_payload, new_candidate)
        self.assertEqual(dirty.returncode, 64)
        self.assertIn(b"CANDIDATE_MISMATCH", dirty.stderr)

    def test_review_result_schema_matches_runtime_finding_contract(self):
        schema_path = PROJECT_ROOT / "verification" / "review-result.schema.json"
        schema = RUNNER.strict_json_load(schema_path.read_bytes(), "review schema")
        RUNNER.validate_review_result_schema(schema)

        drifted = copy.deepcopy(schema)
        drifted["properties"]["findings"]["items"]["required"].remove("owner")
        with self.assertRaisesRegex(
            RUNNER.VerificationError, "review result schema differs from runtime"
        ):
            RUNNER.validate_review_result_schema(drifted)

    def test_runner_manifest_threshold_matches_current_contract_suite(self):
        manifest_path = PROJECT_ROOT / "verification" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        runner_row = next(
            row
            for row in manifest["checks"]
            if row["check_id"] == "s1a-verification-runner-contracts"
        )
        test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        test_count = sum(
            1
            for node in ast.walk(test_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
        self.assertEqual(runner_row["expected_observation"]["min_count"], test_count)

    def test_baseline_inventory_rejects_false_green_deferred_items(self):
        inventory_path = PROJECT_ROOT / "verification" / "baseline-inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        deferred = next(
            item
            for item in inventory["items"]
            if item["affected_stage_release"] in {"1B", "1C"}
        )
        deferred["current_verdict"] = "PASS"
        deferred["disposition"] = "CLOSED"
        with self.assertRaises(RUNNER.VerificationError):
            RUNNER.validate_baseline_inventory(inventory)

        load_bearing = json.loads(inventory_path.read_text(encoding="utf-8"))
        a04 = next(
            item for item in load_bearing["items"] if item["stable_id"] == "A-04"
        )
        a04["affected_stage_release"] = "1C"
        a04["current_verdict"] = "INCONCLUSIVE"
        a04["disposition"] = "DEFERRED_TO_1C"
        with self.assertRaisesRegex(
            RUNNER.VerificationError, "load-bearing assumption cannot be deferred"
        ):
            RUNNER.validate_baseline_inventory(load_bearing)

        review_state = {
            "schema_version": "sdlc-os-review-state-v1",
            "prior_reviews": [],
            "release_1a_candidate_reviews": {
                "independent": {"status": "PENDING"},
                "adversarial": {"status": "PENDING"},
            },
        }
        with self.assertRaises(RUNNER.VerificationError):
            RUNNER.validate_review_state(review_state)

    def test_same_reviewer_spec_history_must_remain_inconclusive(self):
        review_path = PROJECT_ROOT / "verification" / "review-state.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        same_reviewer = next(
            entry
            for entry in review["prior_reviews"]
            if entry["kind"] == "final-spec-review"
        )
        same_reviewer["verdict"] = "PASS"
        with self.assertRaisesRegex(
            RUNNER.VerificationError, "same-reviewer spec review must be INCONCLUSIVE"
        ):
            RUNNER.validate_review_state(review)

        erased = json.loads(review_path.read_text(encoding="utf-8"))
        erased["prior_reviews"] = [
            {
                "review_id": "replacement-review",
                "kind": "other-review",
                "verdict": "PASS",
                "reason": "synthetic replacement",
                "source": "synthetic replacement",
            }
        ]
        with self.assertRaisesRegex(
            RUNNER.VerificationError, "required prior review history is missing"
        ):
            RUNNER.validate_review_state(erased)

    def test_error_catalog_exactly_matches_production_emitters(self):
        catalog_path = PROJECT_ROOT / "verification" / "error-catalog.json"
        catalog = RUNNER.strict_json_load(catalog_path.read_bytes(), "catalog")
        codes = [entry["code"] for entry in catalog["errors"]]
        self.assertEqual(len(codes), len(set(codes)))
        emitted = production_error_codes()
        self.assertEqual(set(codes), emitted)
        self.assertEqual(set(RUNNER.ERROR_CODES), emitted)
        for entry in catalog["errors"]:
            with self.subTest(template=entry["code"]):
                self.assertIn("where=<relative-surface>", entry["template"])
                self.assertIn("evidence=<relative-artifact>", entry["template"])

        missing_context = copy.deepcopy(catalog)
        missing_context["errors"][0]["template"] = missing_context["errors"][0][
            "template"
        ].replace(" where=<relative-surface>", "")
        with self.assertRaisesRegex(
            RUNNER.VerificationError, "error template lacks required fields"
        ):
            RUNNER.validate_error_catalog(missing_context)


if __name__ == "__main__":
    unittest.main()
