#!/usr/bin/env python3

import argparse
import datetime as dt
import errno
import hashlib
import json
import math
import os
import platform
import pwd
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


MANIFEST_SCHEMA = "sdlc-os-verification-manifest-v1"
RECEIPT_SCHEMA = "sdlc-os-verification-receipt-v1"
RUN_SCHEMA = "sdlc-os-verification-run-v1"
ERROR_CATALOG_SCHEMA = "sdlc-os-error-catalog-v1"
BASELINE_SCHEMA = "sdlc-os-baseline-inventory-v1"
REVIEW_STATE_SCHEMA = "sdlc-os-review-state-v1"
REVIEW_RESULT_SCHEMA = "sdlc-os-review-result-v1"
RUNNER_VERSION = "1.0.0"

MAX_JSON_BYTES = 1024 * 1024
MAX_JSON_STRING = 64 * 1024
MAX_JSON_MEMBERS = 4096
MAX_JSON_DEPTH = 16
MAX_ARG_BYTES = 8192
MAX_ARGS = 256
MAX_STREAM_BYTES = 16 * 1024 * 1024
MAX_OBSERVATION_BYTES = 1024 * 1024
MONITOR_SECONDS = 0.1
TERM_GRACE_SECONDS = 2.0
KILL_GRACE_SECONDS = 2.0

ERROR_CODES = (
    "F01_FIXTURE_ESCAPE",
    "F01_INSTALLED_DRIFT",
    "F01_FAILPOINT_NOT_REACHED",
    "F01_DRIVER_INTERRUPTED",
    "F01_TEMP_TREE_HELPER_MISSING",
    "F01_PRE_FAILPOINT_CASES_FAILED",
    "F01_RESTORE_FAILED",
    "F01_INNER_RETAINED",
    "F01_INNER_CONTAINER_RETAINED",
    "F01_RESTORE_RETAINED",
    "ROOT_INVALID",
    "PLUGIN_METADATA_DRIFT",
    "INVENTORY_DRIFT",
    "VERIFY_MANIFEST_INVALID",
    "VERIFY_SELECTION_EMPTY",
    "VERIFY_RESULTS_ESCAPE",
    "VERIFY_ENV_INVALID",
    "VERIFY_PLATFORM_MISMATCH",
    "VERIFY_EXECUTABLE_DRIFT",
    "VERIFY_EXIT_MISMATCH",
    "VERIFY_OBSERVATION_FAILED",
    "VERIFY_ENCODING_INVALID",
    "VERIFY_OUTPUT_LIMIT",
    "VERIFY_WRITE_FAILED",
    "VERIFY_TIMEOUT",
    "VERIFY_INTERRUPTED",
    "VERIFY_ARTIFACT_INVALID",
    "VERIFY_BACKGROUND_PROCESS",
    "VERIFY_SOURCE_DIRTY",
    "VERIFY_SOURCE_MUTATION",
    "CANDIDATE_MISMATCH",
    "CLEANUP_FAILED",
)

SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_CHECK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SAFE_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SECRET_KEY = re.compile(r"TOKEN|SECRET|PASSWORD|KEY|COOKIE|AUTH", re.IGNORECASE)
SUBSTITUTION = re.compile(r"\$\{([A-Z_]+)\}")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40,64}$")
RESERVED_ENV = {"PATH", "HOME", "TMPDIR", "LC_ALL", "LANG", "TZ"}
ALLOWED_SUBSTITUTIONS = {"REPO_ROOT", "HOST_HOME", "CHECK_HOME", "CHECK_TMPDIR"}
PROHIBITED_DIRECT_SCRIPTS = {
    "tests/test-fixture-regression.sh",
    "colony/validation/run-all.sh",
    "scripts/crossmodel-grid-down.sh",
}

MANIFEST_TOP_KEYS = {
    "schema_version",
    "requirement_catalog",
    "executable_allowlist",
    "protected_ignored_paths",
    "checks",
}
ROW_KEYS = {
    "check_id",
    "stage",
    "requirement_ids",
    "command",
    "required_tools",
    "working_directory",
    "environment",
    "platforms",
    "applicability",
    "timeout_seconds",
    "max_output_bytes",
    "expected_exit",
    "inconclusive_exit_codes",
    "expected_observation",
    "negative_falsifier",
    "independence_requirement",
    "required_artifacts",
    "clean_source",
}
REVIEW_RESULT_KEYS = {
    "schema_version",
    "candidate_sha",
    "manifest_sha256",
    "requirement_catalog_sha256",
    "reviewer",
    "commands",
    "material_claims",
    "findings",
    "limitations",
    "protected_evidence_hashes",
    "verdict",
}
REVIEW_FINDING_KEYS = {
    "finding",
    "severity",
    "disposition",
    "evidence",
    "owner",
    "due_trigger",
    "closure_proof",
}
REVIEW_FINDING_SEVERITIES = {"CRITICAL", "MATERIAL", "NONMATERIAL"}
REVIEW_FINDING_DISPOSITIONS = {
    "ACCEPTED",
    "REJECTED",
    "ACCEPTED_RESIDUAL",
    "UNRESOLVED",
}


class VerificationError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 64):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class EvidenceWriteError(Exception):
    pass


class VerificationArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):
        raise VerificationError("VERIFY_MANIFEST_INVALID", message)


def _exact_keys(value: dict[str, Any], expected: set[str], label: str):
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID",
            f"{label} keys invalid; missing={missing} unknown={unknown}",
        )


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} must be an array")
    return value


def _require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} must be a string")
    if nonempty and not value.strip():
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} must be nonempty")
    if len(value.encode("utf-8")) > MAX_JSON_STRING:
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} is too large")
    return value


def _require_int(value: Any, label: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"{label} must be an integer"
        )
    if not low <= value <= high:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"{label} must be between {low} and {high}"
        )
    return value


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _validate_json_shape(value: Any, depth: int = 0):
    if depth > MAX_JSON_DEPTH:
        raise ValueError(f"JSON nesting exceeds {MAX_JSON_DEPTH}")
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_JSON_STRING:
            raise ValueError("JSON string exceeds 64 KiB")
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return
    if isinstance(value, list):
        if len(value) > MAX_JSON_MEMBERS:
            raise ValueError("JSON array has too many members")
        for item in value:
            _validate_json_shape(item, depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_JSON_MEMBERS:
            raise ValueError("JSON object has too many members")
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object key is not a string")
            _validate_json_shape(key, depth + 1)
            _validate_json_shape(item, depth + 1)
        return
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def strict_json_load(raw: bytes, label: str = "JSON") -> Any:
    if len(raw) > MAX_JSON_BYTES:
        raise VerificationError("VERIFY_MANIFEST_INVALID", f"{label} exceeds 1 MiB")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON token: {token}")
            ),
        )
        _validate_json_shape(value)
        return value
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"{label} is invalid: {error}"
        ) from error


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_shape(value)
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            size += len(chunk)
            if limit is not None and size > limit:
                raise VerificationError(
                    "VERIFY_ARTIFACT_INVALID", f"artifact exceeds {limit} bytes", 3
                )
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(name: str):
    if not SAFE_SEGMENT.fullmatch(name):
        raise EvidenceWriteError(f"unsafe evidence name: {name!r}")


def atomic_write_at(
    directory_fd: int, name: str, data: bytes, mode: int = 0o600
) -> dict[str, Any]:
    _safe_name(name)
    temp_name = f".{name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    descriptor = None
    try:
        descriptor = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            mode,
            dir_fd=directory_fd,
        )
        os.fchmod(descriptor, mode)
        view = memoryview(data)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            if count <= 0:
                raise OSError(errno.EIO, "short evidence write")
            written += count
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(
            temp_name,
            name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
        read_fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd
        )
        try:
            metadata = os.fstat(read_fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise OSError(errno.EINVAL, "evidence is not regular")
            chunks = []
            while True:
                chunk = os.read(read_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            observed = b"".join(chunks)
        finally:
            os.close(read_fd)
        if observed != data:
            raise OSError(errno.EIO, "evidence readback mismatch")
        return {
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "mode": f"{mode:04o}",
        }
    except (OSError, ValueError) as error:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            os.unlink(temp_name, dir_fd=directory_fd)
        except OSError:
            pass
        raise EvidenceWriteError(str(error)) from error


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def capture_timing(action: Callable[[], Any]) -> dict[str, Any]:
    start_wall = time.time_ns()
    start_mono = time.monotonic_ns()
    result = action()
    end_mono = time.monotonic_ns()
    end_wall = time.time_ns()
    return {
        "start_wall_ns": start_wall,
        "end_wall_ns": end_wall,
        "duration_monotonic_ns": max(0, end_mono - start_mono),
        "result": result,
    }


def _descriptor(path: Path, repo_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root)
        return f"repo:{relative.as_posix()}"
    except ValueError:
        return f"system:{path.name}"


def _path_parts(value: str, label: str, *, allow_dot: bool = False) -> list[str]:
    if not isinstance(value, str) or not value:
        raise VerificationError("VERIFY_RESULTS_ESCAPE", f"{label} must be nonempty")
    if "\x00" in value or Path(value).is_absolute():
        raise VerificationError("VERIFY_RESULTS_ESCAPE", f"{label} must be relative")
    if value == "." and allow_dot:
        return []
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise VerificationError("VERIFY_RESULTS_ESCAPE", f"{label} has unsafe segments")
    return parts


def _existing_beneath(
    repo_root: Path, value: str, label: str, *, directory: bool = False
) -> Path:
    parts = _path_parts(value, label, allow_dot=directory)
    current = repo_root
    for part in parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError as error:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", f"{label} does not exist"
            ) from error
        if stat.S_ISLNK(metadata.st_mode):
            raise VerificationError(
                "VERIFY_RESULTS_ESCAPE", f"{label} crosses a symlink"
            )
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(repo_root)
    except ValueError as error:
        raise VerificationError(
            "VERIFY_RESULTS_ESCAPE", f"{label} escapes repository"
        ) from error
    metadata = resolved.stat()
    if directory and not stat.S_ISDIR(metadata.st_mode):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"{label} is not a directory"
        )
    if not directory and not stat.S_ISREG(metadata.st_mode):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"{label} is not a regular file"
        )
    return resolved


@dataclass
class ResultRoot:
    path: Path
    parent_fd: int
    fd: int
    name: str
    identity: tuple[int, int]

    def revalidate(self) -> bool:
        try:
            held = os.fstat(self.fd)
            current = os.stat(self.name, dir_fd=self.parent_fd, follow_symlinks=False)
        except OSError:
            return False
        return (
            stat.S_ISDIR(current.st_mode)
            and (held.st_dev, held.st_ino) == self.identity
            and (current.st_dev, current.st_ino) == self.identity
        )

    def close(self):
        for descriptor in (self.fd, self.parent_fd):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _open_directory_at(parent_fd: int, name: str) -> tuple[int, tuple[int, int]]:
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=parent_fd,
    )
    metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(descriptor)
        raise VerificationError(
            "VERIFY_RESULTS_ESCAPE", "result component is not a directory"
        )
    return descriptor, (metadata.st_dev, metadata.st_ino)


def create_result_root(repo_root: Path, relative: str, run_id: str) -> ResultRoot:
    if not SAFE_SEGMENT.fullmatch(run_id):
        raise VerificationError(
            "VERIFY_RESULTS_ESCAPE", "run-id is not one safe path segment"
        )
    parts = _path_parts(relative, "results directory")
    if not parts or parts[-1] != run_id:
        raise VerificationError(
            "VERIFY_RESULTS_ESCAPE", "results directory leaf must equal run-id"
        )
    current_fd = os.open(
        repo_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        for part in parts[:-1]:
            try:
                next_fd, _ = _open_directory_at(current_fd, part)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=current_fd)
                    next_fd, _ = _open_directory_at(current_fd, part)
                except OSError as error:
                    if error.errno in {errno.EEXIST, errno.ELOOP, errno.ENOTDIR}:
                        raise VerificationError(
                            "VERIFY_RESULTS_ESCAPE",
                            "results directory parent is unsafe",
                        ) from error
                    raise
            except OSError as error:
                if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise VerificationError(
                        "VERIFY_RESULTS_ESCAPE",
                        "results directory parent is unsafe",
                    ) from error
                raise
            os.close(current_fd)
            current_fd = next_fd
        leaf = parts[-1]
        try:
            os.stat(leaf, dir_fd=current_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise VerificationError(
                "VERIFY_RESULTS_ESCAPE", "results directory already exists"
            )
        os.mkdir(leaf, 0o700, dir_fd=current_fd)
        result_fd, identity = _open_directory_at(current_fd, leaf)
        os.fchmod(result_fd, 0o700)
        path = repo_root.joinpath(*parts)
        return ResultRoot(path, current_fd, result_fd, leaf, identity)
    except Exception:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise


def mkdir_open_at(parent_fd: int, name: str) -> tuple[int, tuple[int, int]]:
    _safe_name(name)
    os.mkdir(name, 0o700, dir_fd=parent_fd)
    descriptor, identity = _open_directory_at(parent_fd, name)
    os.fchmod(descriptor, 0o700)
    return descriptor, identity


def revalidate_child(parent_fd: int, name: str, child_fd: int, identity) -> bool:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        held = os.fstat(child_fd)
    except OSError:
        return False
    return (
        stat.S_ISDIR(current.st_mode)
        and (current.st_dev, current.st_ino) == identity
        and (held.st_dev, held.st_ino) == identity
    )


def discover_repo_root(cwd: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "current directory is not a Git repository"
        )
    try:
        root = Path(result.stdout.decode("utf-8", errors="strict").strip()).resolve(
            strict=True
        )
    except (UnicodeDecodeError, OSError) as error:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "repository root is unreadable"
        ) from error
    return root


def _validate_substitutions(value: str, label: str):
    for name in SUBSTITUTION.findall(value):
        if name not in ALLOWED_SUBSTITUTIONS:
            raise VerificationError(
                "VERIFY_ENV_INVALID", f"{label} uses unknown substitution"
            )
    stripped = SUBSTITUTION.sub("", value)
    if "${" in stripped:
        raise VerificationError(
            "VERIFY_ENV_INVALID", f"{label} has malformed substitution"
        )


def _safe_relative_artifact(path: str):
    parts = _path_parts(path, "required artifact")
    if len(parts) > 8:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "artifact path is too deep")


def _validate_observation(value: Any):
    observation = _require_dict(value, "expected_observation")
    kind = _require_string(observation.get("type"), "expected_observation.type")
    if kind == "contains":
        expected = {"type", "stream", "value"}
        _exact_keys(observation, expected, "contains observation")
        _require_string(observation["value"], "contains value")
    elif kind == "regex":
        expected = {"type", "stream", "pattern"}
        _exact_keys(observation, expected, "regex observation")
        pattern = _require_string(observation["pattern"], "regex pattern")
        _validate_pattern(pattern, count=False)
    elif kind == "test_count_regex":
        expected = {"type", "stream", "pattern", "min_count"}
        _exact_keys(observation, expected, "test count observation")
        pattern = _require_string(observation["pattern"], "test count pattern")
        _validate_pattern(pattern, count=True)
        _require_int(observation["min_count"], "min_count", 1, 1_000_000)
    elif kind == "json_subset":
        expected = {"type", "stream", "value"}
        _exact_keys(observation, expected, "json subset observation")
        _validate_json_shape(observation["value"])
    elif kind == "empty":
        expected = {"type", "stream"}
        _exact_keys(observation, expected, "empty observation")
    else:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"unknown observation type: {kind}"
        )
    stream = _require_string(observation.get("stream"), "observation stream")
    if stream not in {"stdout", "stderr"}:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "observation stream is invalid"
        )


def _validate_pattern(pattern: str, *, count: bool):
    if len(pattern.encode("utf-8")) > 4096:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "regex pattern is too large")
    if re.search(r"\([^)]*[+*][^)]*\)[+*{]", pattern):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "nested regex quantifier rejected"
        )
    try:
        compiled = re.compile(pattern)
    except re.error as error:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", f"regex is invalid: {error}"
        ) from error
    if count and compiled.groups != 1:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "test_count_regex requires exactly one capture"
        )


def _validate_allowlist(entries: Any) -> dict[str, dict[str, Any]]:
    values = _require_list(entries, "executable_allowlist")
    if not values:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "executable allowlist is empty"
        )
    result = {}
    for index, raw in enumerate(values):
        entry = _require_dict(raw, f"allowlist[{index}]")
        mode = _require_string(entry.get("argument_mode"), "allowlist argument mode")
        executable = _require_string(entry.get("executable"), "allowlist executable")
        if executable in result:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "duplicate allowlist executable"
            )
        if mode == "script":
            allowed = {
                "executable",
                "argument_mode",
                "allowed_roots",
                "allowed_scripts",
            }
            optional = {"allowed_modules", "allowed_flags"}
        elif mode == "read_only":
            allowed = {"executable", "argument_mode", "allowed_subcommands"}
            optional = set()
        elif mode == "prefix":
            allowed = {"executable", "argument_mode", "allowed_prefixes"}
            optional = set()
        elif mode == "exact":
            allowed = {"executable", "argument_mode", "allowed_argv"}
            optional = set()
        else:
            raise VerificationError("VERIFY_MANIFEST_INVALID", "unknown allowlist mode")
        actual = set(entry)
        if not allowed <= actual or actual - allowed - optional:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "allowlist entry keys invalid"
            )
        if mode == "script":
            roots = _require_list(entry["allowed_roots"], "allowed roots")
            if not roots:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "allowed roots are empty"
                )
            for root in roots:
                _require_string(root, "allowed root")
            scripts = _require_list(entry["allowed_scripts"], "allowed scripts")
            for script in scripts:
                _require_string(script, "allowed script")
            if len(scripts) != len(set(scripts)):
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "allowed scripts have duplicates"
                )
            for key in optional:
                values = _require_list(entry.get(key, []), f"allowlist {key}")
                for value in values:
                    _require_string(value, f"allowlist {key} value")
                if len(values) != len(set(values)):
                    raise VerificationError(
                        "VERIFY_MANIFEST_INVALID", f"allowlist {key} has duplicates"
                    )
        elif mode == "read_only":
            subcommands = _require_list(
                entry["allowed_subcommands"], "allowed subcommands"
            )
            if not subcommands:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "allowed subcommands are empty"
                )
            for subcommand in subcommands:
                _require_string(subcommand, "allowed subcommand")
            if len(subcommands) != len(set(subcommands)):
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "allowed subcommands have duplicates"
                )
        else:
            key = "allowed_prefixes" if mode == "prefix" else "allowed_argv"
            variants = _require_list(entry[key], key)
            if not variants:
                raise VerificationError("VERIFY_MANIFEST_INVALID", f"{key} is empty")
            for raw_variant in variants:
                variant = _require_list(raw_variant, f"{key} variant")
                if not variant:
                    raise VerificationError(
                        "VERIFY_MANIFEST_INVALID", f"{key} variant is empty"
                    )
                for argument in variant:
                    _require_string(argument, f"{key} argument", nonempty=False)
        result[executable] = entry
    return result


def _validate_script_path(row, repo_root: Path, value: str, roots: list[str]):
    _validate_substitutions(value, "script path")
    static = SUBSTITUTION.sub("HOST", value)
    parts = static.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "script path has unsafe segments"
        )
    if parts[0] == "HOST":
        if "HOST" not in roots:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "host script path is not allowlisted"
            )
        return
    working = row["working_directory"]
    combined = static if working == "." else f"{working}/{static}"
    candidate = _existing_beneath(repo_root, combined, "script path")
    for root in roots:
        if root == "HOST":
            continue
        allowed_root = _existing_beneath(
            repo_root, root, "allowed script root", directory=True
        )
        try:
            candidate.relative_to(allowed_root)
            return
        except ValueError:
            continue
    raise VerificationError(
        "VERIFY_MANIFEST_INVALID", "script path is outside allowed physical roots"
    )


def _normalize_command_executable(row, repo_root: Path) -> str:
    command0 = row["command"][0]
    if "/" not in command0:
        return command0
    working = (
        repo_root
        if row["working_directory"] == "."
        else repo_root / row["working_directory"]
    )
    candidate = working / command0
    try:
        resolved = candidate.resolve(strict=True)
        relative = resolved.relative_to(repo_root)
    except (OSError, ValueError) as error:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "command executable escapes repository"
        ) from error
    return relative.as_posix()


def _validate_command_shape(row, allowlist, repo_root: Path):
    command = row["command"]
    command0 = command[0]
    basename = Path(command0).name
    if basename == "env":
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "env executable is prohibited"
        )
    forbidden = {
        "bash": {"-c", "--command"},
        "sh": {"-c"},
        "zsh": {"-c"},
        "python": {"-c"},
        "python3": {"-c"},
        "python3.12": {"-c"},
        "node": {"-e", "--eval", "-p", "--print"},
    }
    if any(argument in forbidden.get(basename, set()) for argument in command[1:]):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "interpreter command strings are prohibited"
        )
    normalized = _normalize_command_executable(row, repo_root)
    entry = (
        allowlist.get(command0) or allowlist.get(normalized) or allowlist.get(basename)
    )
    if entry is None:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "command executable is not allowlisted"
        )
    arguments = command[1:]
    mode = entry["argument_mode"]
    if mode == "script":
        roots = [
            _require_string(item, "allowed root")
            for item in _require_list(entry["allowed_roots"], "allowed roots")
        ]
        modules = entry.get("allowed_modules", [])
        flags = set(entry.get("allowed_flags", []))
        if arguments[:1] == ["-m"]:
            if len(arguments) < 2 or arguments[1] not in modules:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "Python module is not allowlisted"
                )
            for item in arguments[2:]:
                if not item.startswith("-"):
                    _validate_script_path(row, repo_root, item, roots)
        elif arguments[:1] and arguments[0] in flags:
            paths = arguments[1:]
            if not paths:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "script flag requires paths"
                )
            for item in paths:
                if item.startswith("-"):
                    raise VerificationError(
                        "VERIFY_MANIFEST_INVALID",
                        "script path is outside allowlisted roots",
                    )
                _validate_script_path(row, repo_root, item, roots)
        else:
            if not arguments:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "script command requires a path"
                )
            script = arguments[0]
            if script not in entry["allowed_scripts"]:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "script is not exactly allowlisted"
                )
            if script in PROHIBITED_DIRECT_SCRIPTS:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID",
                    "script belongs to a deferred or mutation-capable command family",
                )
            _validate_script_path(row, repo_root, script, roots)
    elif mode == "read_only":
        allowed = entry["allowed_subcommands"]
        if not arguments or arguments[0] not in allowed:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "Git subcommand is not read-only allowlisted"
            )
        forbidden_git_arguments = (
            "--output",
            "--ext-diff",
            "--textconv",
            "--no-index",
            "--open-files-in-pager",
        )
        if any(
            argument == "-o"
            or any(argument.startswith(prefix) for prefix in forbidden_git_arguments)
            for argument in arguments[1:]
        ):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "Git argument can write or execute helpers"
            )
    elif mode == "prefix":
        prefixes = entry["allowed_prefixes"]
        if not any(arguments[: len(prefix)] == prefix for prefix in prefixes):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "command prefix is not allowlisted"
            )
    elif mode == "exact":
        if arguments not in entry["allowed_argv"]:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "command argv is not exactly allowlisted"
            )


def validate_manifest(value: Any, repo_root: Path) -> dict[str, Any]:
    manifest = _require_dict(value, "manifest")
    _exact_keys(manifest, MANIFEST_TOP_KEYS, "manifest")
    if manifest["schema_version"] != MANIFEST_SCHEMA:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "unsupported manifest schema"
        )
    requirements = _require_dict(manifest["requirement_catalog"], "requirement_catalog")
    if not requirements:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "requirement catalog is empty"
        )
    requirement_keys = {"source", "disposition", "owner_release", "closure_in_1a"}
    for requirement_id, raw in requirements.items():
        _require_string(requirement_id, "requirement ID")
        entry = _require_dict(raw, f"requirement {requirement_id}")
        _exact_keys(entry, requirement_keys, f"requirement {requirement_id}")
        _require_string(entry["source"], "requirement source")
        _require_string(entry["disposition"], "requirement disposition")
        _require_string(entry["owner_release"], "requirement owner release")
        if not isinstance(entry["closure_in_1a"], bool):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "closure_in_1a must be boolean"
            )
    allowlist = _validate_allowlist(manifest["executable_allowlist"])
    protected = _require_list(manifest["protected_ignored_paths"], "protected paths")
    seen_protected = set()
    for item in protected:
        path = _require_string(item, "protected path")
        _path_parts(path, "protected path")
        if path in seen_protected:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "duplicate protected path"
            )
        seen_protected.add(path)
    checks = _require_list(manifest["checks"], "checks")
    if not checks:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "checks are empty")
    seen_ids = set()
    covered_1a = set()
    for index, raw in enumerate(checks):
        row = _require_dict(raw, f"checks[{index}]")
        _exact_keys(row, ROW_KEYS, f"checks[{index}]")
        check_id = _require_string(row["check_id"], "check_id")
        if not SAFE_CHECK_ID.fullmatch(check_id):
            raise VerificationError("VERIFY_MANIFEST_INVALID", "check_id is unsafe")
        if check_id in seen_ids:
            raise VerificationError("VERIFY_MANIFEST_INVALID", "duplicate check_id")
        seen_ids.add(check_id)
        _require_string(row["stage"], "stage")
        requirement_ids = _require_list(row["requirement_ids"], "requirement_ids")
        if not requirement_ids:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "requirement_ids are empty"
            )
        for requirement_id in requirement_ids:
            if requirement_id not in requirements:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "unknown requirement ID"
                )
            if row["stage"] == "1A":
                covered_1a.add(requirement_id)
        command = _require_list(row["command"], "command")
        if not command or len(command) > MAX_ARGS:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "command argv count is invalid"
            )
        for argument in command:
            _require_string(argument, "command argument", nonempty=False)
            if len(argument.encode("utf-8")) > MAX_ARG_BYTES:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "command argument exceeds 8 KiB"
                )
            _validate_substitutions(argument, "command argument")
        tools = _require_list(row["required_tools"], "required_tools")
        if not tools:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "required_tools are empty"
            )
        if len(set(tools)) != len(tools):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "required_tools contain duplicates"
            )
        for tool in tools:
            if not isinstance(tool, str) or not tool or "/" in tool:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "required tool name is invalid"
                )
        cwd = _require_string(row["working_directory"], "working_directory")
        _existing_beneath(repo_root, cwd, "working_directory", directory=True)
        environment = _require_dict(row["environment"], "environment")
        for key, environment_value in environment.items():
            if not isinstance(key, str) or not SAFE_ENV_KEY.fullmatch(key):
                raise VerificationError(
                    "VERIFY_ENV_INVALID", "environment key is invalid"
                )
            if key in RESERVED_ENV or SECRET_KEY.search(key):
                raise VerificationError(
                    "VERIFY_ENV_INVALID", "environment key is reserved or secret-like"
                )
            _require_string(environment_value, f"environment {key}", nonempty=False)
            if len(environment_value.encode("utf-8")) > MAX_ARG_BYTES:
                raise VerificationError(
                    "VERIFY_ENV_INVALID", "environment value exceeds 8 KiB"
                )
            _validate_substitutions(environment_value, f"environment {key}")
        platforms = _require_list(row["platforms"], "platforms")
        if not platforms or len(platforms) != len(set(platforms)):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "platforms are empty or duplicated"
            )
        if any(item not in {"macos", "linux"} for item in platforms):
            raise VerificationError("VERIFY_MANIFEST_INVALID", "platform is unknown")
        applicability = _require_dict(row["applicability"], "applicability")
        _exact_keys(applicability, {"state", "evidence"}, "applicability")
        if applicability["state"] not in {"REQUIRED", "NOT_APPLICABLE"}:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "applicability state is invalid"
            )
        _require_string(applicability["evidence"], "applicability evidence")
        _require_int(row["timeout_seconds"], "timeout_seconds", 1, 1800)
        _require_int(row["max_output_bytes"], "max_output_bytes", 1, MAX_STREAM_BYTES)
        expected_exit = _require_int(row["expected_exit"], "expected_exit", 0, 125)
        inconclusive = _require_list(
            row["inconclusive_exit_codes"], "inconclusive exits"
        )
        if len(inconclusive) != len(set(inconclusive)):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "inconclusive exits duplicated"
            )
        for exit_code in inconclusive:
            _require_int(exit_code, "inconclusive exit", 1, 125)
            if exit_code == expected_exit:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "inconclusive exit overlaps expected"
                )
        _validate_observation(row["expected_observation"])
        _require_string(row["negative_falsifier"], "negative_falsifier")
        _require_string(row["independence_requirement"], "independence_requirement")
        artifacts = _require_list(row["required_artifacts"], "required_artifacts")
        seen_artifacts = set()
        for artifact_index, raw_artifact in enumerate(artifacts):
            artifact = _require_dict(raw_artifact, f"artifact[{artifact_index}]")
            _exact_keys(
                artifact,
                {"path", "type", "min_bytes", "max_bytes"},
                f"artifact[{artifact_index}]",
            )
            artifact_path = _require_string(artifact["path"], "artifact path")
            _safe_relative_artifact(artifact_path)
            if artifact_path in seen_artifacts:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "duplicate artifact path"
                )
            seen_artifacts.add(artifact_path)
            if artifact["type"] != "file":
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "artifact type must be file"
                )
            minimum = _require_int(
                artifact["min_bytes"], "artifact min_bytes", 0, MAX_STREAM_BYTES
            )
            maximum = _require_int(
                artifact["max_bytes"], "artifact max_bytes", 1, MAX_STREAM_BYTES
            )
            if minimum > maximum:
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "artifact size bounds inverted"
                )
        if not isinstance(row["clean_source"], bool):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "clean_source must be boolean"
            )
        _validate_command_shape(row, allowlist, repo_root)
    for requirement_id, entry in requirements.items():
        if (
            entry["owner_release"] == "1A"
            and entry["closure_in_1a"]
            and requirement_id not in covered_1a
        ):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "applicable 1A requirement has no check"
            )
    return manifest


def _current_platform() -> tuple[str, str, str]:
    kernel = platform.system()
    if kernel == "Darwin":
        os_name = "macos"
    elif kernel == "Linux":
        os_name = "linux"
    else:
        os_name = kernel.lower()
    return os_name, platform.machine(), platform.release()


def _resolve_tool(
    name: str, acquisition_path: str, repo_root: Path
) -> dict[str, Any] | None:
    path = shutil.which(name, path=acquisition_path)
    if not path:
        return None
    resolved = Path(path).resolve(strict=True)
    metadata = resolved.stat()
    if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
        return None
    return {
        "name": name,
        "path": resolved,
        "descriptor": _descriptor(resolved, repo_root),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
        "sha256": sha256_file(resolved),
    }


def _tool_projection(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "resolved": tool["descriptor"],
        "size": tool["size"],
        "sha256": tool["sha256"],
    }


def _tool_unchanged(tool: dict[str, Any]) -> bool:
    try:
        metadata = tool["path"].stat()
        return (
            metadata.st_dev == tool["device"]
            and metadata.st_ino == tool["inode"]
            and metadata.st_size == tool["size"]
            and metadata.st_mtime_ns == tool["mtime_ns"]
            and sha256_file(tool["path"]) == tool["sha256"]
        )
    except OSError:
        return False


def _resolve_command(
    row: dict[str, Any], repo_root: Path, cwd: Path, tools: dict[str, dict[str, Any]]
) -> tuple[Path, str]:
    command0 = row["command"][0]
    if "/" in command0:
        candidate = (cwd / command0).resolve(strict=True)
        try:
            candidate.relative_to(repo_root)
        except ValueError as error:
            raise VerificationError(
                "VERIFY_EXECUTABLE_DRIFT", "executable escapes repository", 3
            ) from error
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            raise VerificationError(
                "VERIFY_EXECUTABLE_DRIFT", "repository executable is unavailable", 3
            )
        return candidate, _descriptor(candidate, repo_root)
    tool = tools.get(command0)
    if tool is None:
        raise VerificationError(
            "VERIFY_EXECUTABLE_DRIFT", "command executable was not resolved", 3
        )
    return tool["path"], tool["descriptor"]


def _expand(value: str, substitutions: dict[str, str]) -> str:
    _validate_substitutions(value, "runtime value")
    return SUBSTITUTION.sub(lambda match: substitutions[match.group(1)], value)


def _sanitized_declared_environment(environment: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in sorted(environment.items()):
        if SUBSTITUTION.search(value):
            result[key] = value
        else:
            result[key] = f"redacted:sha256:{sha256_bytes(value.encode('utf-8'))}"
    return result


def _git_state(repo_root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status_result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    worktree_diff = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "diff",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "--",
            ".",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    index_diff = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "--",
            ".",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    untracked_result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if any(
        result.returncode != 0
        for result in (
            commit,
            status_result,
            worktree_diff,
            index_diff,
            untracked_result,
        )
    ):
        raise VerificationError(
            "VERIFY_SOURCE_MUTATION", "Git source state is unavailable", 3
        )
    try:
        sha = commit.stdout.decode("ascii", errors="strict").strip()
        status_text = status_result.stdout.decode("utf-8", errors="strict")
        untracked = [
            value
            for value in untracked_result.stdout.decode("utf-8", errors="strict").split(
                "\0"
            )
            if value
        ]
    except UnicodeDecodeError as error:
        raise VerificationError(
            "VERIFY_SOURCE_MUTATION", "Git source state encoding is invalid", 3
        ) from error
    content = hashlib.sha256()
    content.update(worktree_diff.stdout)
    content.update(b"\0INDEX\0")
    content.update(index_diff.stdout)
    for relative in sorted(untracked):
        content.update(relative.encode("utf-8") + b"\0")
        content.update(_hash_path(repo_root / relative).encode("ascii") + b"\0")
    return {
        "candidate_sha": sha,
        "dirty": bool(status_text),
        "status_sha256": sha256_bytes(status_result.stdout),
        "content_sha256": content.hexdigest(),
        "status_lines": status_text.splitlines(),
    }


def _hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists() and not path.is_symlink():
        digest.update(b"MISSING\0")
        return digest.hexdigest()
    root = path.parent
    entries = [path]
    if path.is_dir() and not path.is_symlink():
        entries.extend(sorted(path.rglob("*"), key=lambda item: item.as_posix()))
    for entry in entries:
        try:
            relative = entry.relative_to(root).as_posix().encode("utf-8")
            metadata = entry.lstat()
        except OSError:
            digest.update(b"DRIFT\0")
            continue
        digest.update(relative + b"\0")
        digest.update(str(stat.S_IMODE(metadata.st_mode)).encode() + b"\0")
        if stat.S_ISLNK(metadata.st_mode):
            digest.update(b"L\0" + os.readlink(entry).encode("utf-8") + b"\0")
        elif stat.S_ISREG(metadata.st_mode):
            digest.update(b"F\0")
            with entry.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
        elif stat.S_ISDIR(metadata.st_mode):
            digest.update(b"D\0")
        else:
            digest.update(b"S\0")
    return digest.hexdigest()


def _protected_state(repo_root: Path, protected: list[str]) -> dict[str, str]:
    return {item: _hash_path(repo_root / item) for item in protected}


def _ignored_state(repo_root: Path, active_result_root: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            "VERIFY_SOURCE_MUTATION", "ignored source state is unavailable", 3
        )
    try:
        relative_paths = [
            value
            for value in result.stdout.decode("utf-8", errors="strict").split("\0")
            if value
        ]
    except UnicodeDecodeError as error:
        raise VerificationError(
            "VERIFY_SOURCE_MUTATION", "ignored source state encoding is invalid", 3
        ) from error
    digest = hashlib.sha256()
    for relative in sorted(relative_paths):
        candidate = repo_root / relative
        if candidate == active_result_root or active_result_root in candidate.parents:
            continue
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(_hash_path(candidate).encode("ascii") + b"\0")
    return digest.hexdigest()


def _process_snapshot() -> dict[int, dict[str, Any]]:
    ps = Path("/bin/ps") if Path("/bin/ps").exists() else Path("/usr/bin/ps")
    result = subprocess.run(
        [str(ps), "-axo", "pid=,ppid=,pgid=,state=,command="],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            "VERIFY_BACKGROUND_PROCESS", "process inventory is unavailable", 3
        )
    snapshot = {}
    for raw_line in result.stdout.decode("utf-8", errors="replace").splitlines():
        fields = raw_line.strip().split(None, 4)
        if len(fields) < 4:
            continue
        try:
            pid, ppid, pgid = map(int, fields[:3])
            sid = os.getsid(pid)
        except (ProcessLookupError, ValueError):
            continue
        snapshot[pid] = {
            "pid": pid,
            "ppid": ppid,
            "pgid": pgid,
            "sid": sid,
            "state": fields[3],
            "command": fields[4] if len(fields) > 4 else "",
        }
    return snapshot


def _descendant_pids(snapshot: dict[int, dict[str, Any]], root_pid: int) -> set[int]:
    descendants = set()
    changed = True
    while changed:
        changed = False
        parents = {root_pid} | descendants
        for pid, record in snapshot.items():
            if pid not in descendants and record["ppid"] in parents:
                descendants.add(pid)
                changed = True
    return descendants


def _live_group_members(snapshot, pgid: int) -> set[int]:
    return {
        pid
        for pid, record in snapshot.items()
        if record["pgid"] == pgid and not record["state"].startswith("Z")
    }


def _signal_group(pgid: int, sig: int):
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        if _live_group_members(_process_snapshot(), pgid):
            raise


def _wait_group_gone(pgid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _live_group_members(_process_snapshot(), pgid):
            return True
        time.sleep(0.05)
    return not _live_group_members(_process_snapshot(), pgid)


def _terminate_group(pgid: int):
    if not _live_group_members(_process_snapshot(), pgid):
        return
    _signal_group(pgid, signal.SIGTERM)
    if not _wait_group_gone(pgid, TERM_GRACE_SECONDS):
        _signal_group(pgid, signal.SIGKILL)
        _wait_group_gone(pgid, KILL_GRACE_SECONDS)


def _terminate_owned_pids(records: dict[int, dict[str, Any]]) -> bool:
    if not records:
        return True
    current = _process_snapshot()
    targets = []
    for pid, original in records.items():
        observed = current.get(pid)
        if observed and observed["command"] == original["command"]:
            targets.append(pid)
    for pid in targets:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + TERM_GRACE_SECONDS
    while time.monotonic() < deadline and any(
        pid in _process_snapshot() for pid in targets
    ):
        time.sleep(0.05)
    current = _process_snapshot()
    for pid in targets:
        if pid in current:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + KILL_GRACE_SECONDS
    while time.monotonic() < deadline:
        current = _process_snapshot()
        if not any(
            pid in current and not current[pid]["state"].startswith("Z")
            for pid in targets
        ):
            return True
        time.sleep(0.05)
    return False


def _make_runtime_tmp(repo_root: Path, check_id: str) -> tuple[Path, tuple[int, int]]:
    path = Path(tempfile.mkdtemp(prefix=f"sdlc-verification-{check_id}-")).resolve(
        strict=True
    )
    metadata = path.lstat()
    try:
        path.relative_to(repo_root)
    except ValueError:
        pass
    else:
        shutil.rmtree(path)
        raise EvidenceWriteError("runtime temporary root is inside the repository")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise EvidenceWriteError("runtime temporary root is not a physical directory")
    os.chmod(path, 0o700)
    return path, (metadata.st_dev, metadata.st_ino)


def _cleanup_runtime_tmp(path: Path, identity: tuple[int, int]):
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or (metadata.st_dev, metadata.st_ino) != identity
    ):
        raise EvidenceWriteError("runtime temporary root identity changed")
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise EvidenceWriteError("safe runtime temporary cleanup is unavailable")
    try:
        shutil.rmtree(path)
    except OSError as error:
        raise EvidenceWriteError(
            f"runtime temporary cleanup failed: {error}"
        ) from error
    if path.exists() or path.is_symlink():
        raise EvidenceWriteError("runtime temporary root was retained")


@dataclass
class ProcessOutcome:
    exit_code: int | None
    signal_number: int | None
    timed_out: bool
    interrupted: bool
    output_limited: bool
    background_process: bool
    escaped_descendants: list[int]
    duration_ns: int
    started_utc: str
    ended_utc: str


class _InterruptState:
    def __init__(self):
        self.signal_number = None

    def handler(self, signal_number, _frame):
        self.signal_number = signal_number


def _write_bounded_stream(
    descriptor: int, data: bytes, written: int, limit: int
) -> tuple[int, bool]:
    remaining = max(0, limit - written)
    admitted = memoryview(data)[:remaining]
    offset = 0
    while offset < len(admitted):
        count = os.write(descriptor, admitted[offset:])
        if count <= 0:
            raise OSError(errno.EIO, "stream evidence write made no progress")
        offset += count
    return written + len(admitted), len(data) > remaining


def _run_process(
    argv: list[str],
    cwd: Path,
    environment: dict[str, str],
    stdout_fd: int,
    stderr_fd: int,
    timeout_seconds: int,
    output_limit: int,
) -> ProcessOutcome:
    started_utc = utc_now()
    started = time.monotonic_ns()
    interrupt = _InterruptState()
    old_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        old_handlers[sig] = signal.getsignal(sig)
        signal.signal(sig, interrupt.handler)
    process = None
    selector = None
    streams = []
    seen_descendants = {}
    timed_out = False
    output_limited = False
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            close_fds=True,
        )
        if process.stdout is None or process.stderr is None:
            raise EvidenceWriteError("subprocess streams were not created")
        selector = selectors.DefaultSelector()
        stream_sizes = {"stdout": 0, "stderr": 0}
        streams = [process.stdout, process.stderr]
        for name, stream, descriptor in (
            ("stdout", process.stdout, stdout_fd),
            ("stderr", process.stderr, stderr_fd),
        ):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, (name, descriptor))

        def drain(timeout: float) -> bool:
            nonlocal output_limited
            events = selector.select(timeout)
            for key, _ in events:
                name, descriptor = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                stream_sizes[name], exceeded = _write_bounded_stream(
                    descriptor, chunk, stream_sizes[name], output_limit
                )
                output_limited = output_limited or exceeded
            return bool(events)

        deadline = time.monotonic() + timeout_seconds
        while True:
            snapshot = _process_snapshot()
            for pid in _descendant_pids(snapshot, process.pid):
                seen_descendants[pid] = snapshot[pid]
            had_stream_event = drain(MONITOR_SECONDS)
            if output_limited:
                break
            if interrupt.signal_number is not None:
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            if process.poll() is not None:
                if not selector.get_map() or not had_stream_event:
                    break
        final_snapshot = _process_snapshot()
        for pid in _descendant_pids(final_snapshot, process.pid):
            seen_descendants[pid] = final_snapshot[pid]
        if timed_out or output_limited or interrupt.signal_number is not None:
            _terminate_group(process.pid)
        try:
            return_code = process.wait(timeout=KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            _signal_group(process.pid, signal.SIGKILL)
            return_code = process.wait(timeout=KILL_GRACE_SECONDS)
        snapshot = _process_snapshot()
        group_members = _live_group_members(snapshot, process.pid) - {process.pid}
        background = bool(group_members)
        if background:
            _terminate_group(process.pid)
        escaped = {
            pid: observed
            for pid, record in seen_descendants.items()
            if (observed := snapshot.get(pid))
            and not observed["state"].startswith("Z")
            and observed["command"] == record["command"]
            and (observed["pgid"] != process.pid or observed["sid"] != process.pid)
        }
        if escaped:
            _terminate_owned_pids(escaped)
        for _ in range(20):
            if not selector.get_map() or not drain(0.05):
                break
        ended = time.monotonic_ns()
        if return_code is not None and return_code < 0:
            signal_number = -return_code
            exit_code = None
        else:
            signal_number = None
            exit_code = return_code
        return ProcessOutcome(
            exit_code=exit_code,
            signal_number=signal_number,
            timed_out=timed_out,
            interrupted=interrupt.signal_number is not None,
            output_limited=output_limited,
            background_process=background or bool(escaped),
            escaped_descendants=sorted(escaped),
            duration_ns=max(0, ended - started),
            started_utc=started_utc,
            ended_utc=utc_now(),
        )
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        if process is not None and process.poll() is None:
            _terminate_group(process.pid)
            try:
                process.wait(timeout=KILL_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                pass
        if selector is not None:
            selector.close()
        for stream in streams:
            stream.close()


def _stream_bytes(check_fd: int, name: str, limit: int = MAX_STREAM_BYTES) -> bytes:
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=check_fd
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise VerificationError(
                "VERIFY_ARTIFACT_INVALID", "stream is not regular", 3
            )
        chunks = []
        size = 0
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise VerificationError(
                    "VERIFY_OUTPUT_LIMIT", "stream exceeds limit", 3
                )
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _stream_metadata(check_fd: int, check_id: str, name: str) -> dict[str, Any]:
    data = _stream_bytes(check_fd, name)
    metadata = os.stat(name, dir_fd=check_fd, follow_symlinks=False)
    return {
        "path": f"{check_id}/{name}",
        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def _json_subset(observed: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(
            key in observed and _json_subset(observed[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(observed, list) and observed == expected
    return observed == expected


def _evaluate_observation(
    observation, stdout: bytes, stderr: bytes
) -> tuple[bool, str | None]:
    raw = stdout if observation["stream"] == "stdout" else stderr
    if len(raw) > MAX_OBSERVATION_BYTES:
        return False, "VERIFY_OUTPUT_LIMIT"
    if observation["type"] == "empty":
        return raw == b"", None if raw == b"" else "VERIFY_OBSERVATION_FAILED"
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False, "VERIFY_ENCODING_INVALID"
    kind = observation["type"]
    if kind == "contains":
        passed = observation["value"] in text
    elif kind == "regex":
        passed = re.search(observation["pattern"], text) is not None
    elif kind == "test_count_regex":
        matches = list(re.finditer(observation["pattern"], text))
        if len(matches) != 1:
            return False, "VERIFY_OBSERVATION_FAILED"
        try:
            count = int(matches[0].group(1))
        except (ValueError, IndexError):
            return False, "VERIFY_OBSERVATION_FAILED"
        passed = count >= observation["min_count"]
    elif kind == "json_subset":
        try:
            observed = strict_json_load(raw, "observation")
        except VerificationError:
            return False, "VERIFY_ENCODING_INVALID"
        passed = _json_subset(observed, observation["value"])
    else:
        passed = False
    return passed, None if passed else "VERIFY_OBSERVATION_FAILED"


def _read_artifact_no_follow(tmp_path: Path, relative: str, maximum: int) -> bytes:
    parts = _path_parts(relative, "artifact")
    root_fd = os.open(
        tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    current_fd = root_fd
    opened = []
    try:
        for part in parts[:-1]:
            current_fd, _ = _open_directory_at(current_fd, part)
            opened.append(current_fd)
        descriptor = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current_fd
        )
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise VerificationError(
                    "VERIFY_ARTIFACT_INVALID", "artifact is not regular", 3
                )
            if metadata.st_size > maximum:
                raise VerificationError(
                    "VERIFY_ARTIFACT_INVALID", "artifact is oversized", 3
                )
            chunks = []
            total = 0
            while True:
                chunk = os.read(descriptor, 65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum:
                    raise VerificationError(
                        "VERIFY_ARTIFACT_INVALID", "artifact is oversized", 3
                    )
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    except (FileNotFoundError, NotADirectoryError, OSError) as error:
        raise VerificationError(
            "VERIFY_ARTIFACT_INVALID", "artifact is missing or unsafe", 3
        ) from error
    finally:
        for descriptor in reversed(opened):
            try:
                os.close(descriptor)
            except OSError:
                pass
        os.close(root_fd)


def _artifact_records(check_fd: int, tmp_path: Path, artifacts: list[dict[str, Any]]):
    result = []
    for index, artifact in enumerate(artifacts):
        data = _read_artifact_no_follow(
            tmp_path, artifact["path"], artifact["max_bytes"]
        )
        if len(data) < artifact["min_bytes"]:
            raise VerificationError(
                "VERIFY_ARTIFACT_INVALID", "artifact is too small", 3
            )
        target = f"artifact-{index:03d}.bin"
        metadata = atomic_write_at(check_fd, target, data)
        result.append(
            {
                "declared_path": artifact["path"],
                "path": target,
                **metadata,
            }
        )
    return result


def _tool_versions(acquisition_path: str) -> dict[str, str | None]:
    versions = {"python": platform.python_version(), "node": None, "git": None}
    commands = {
        "node": ["node", "--version"],
        "git": ["git", "--version"],
    }
    for name, argv in commands.items():
        executable = shutil.which(argv[0], path=acquisition_path)
        if not executable:
            continue
        result = subprocess.run(
            [executable, *argv[1:]],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            versions[name] = result.stdout.decode("utf-8", errors="replace").strip()
    return versions


def _receipt_base(
    row,
    manifest_hash,
    catalog_hash,
    runner_hash,
    source,
    platform_record,
    tool_versions,
):
    return {
        "schema_version": RECEIPT_SCHEMA,
        "check_id": row["check_id"],
        "stage": row["stage"],
        "requirement_ids": row["requirement_ids"],
        "command": row["command"],
        "working_directory": row["working_directory"],
        "declared_environment": _sanitized_declared_environment(row["environment"]),
        "applicability": row["applicability"],
        "manifest_sha256": manifest_hash,
        "requirement_catalog_sha256": catalog_hash,
        "manifest_row_sha256": sha256_bytes(canonical_json_bytes(row)),
        "runner_sha256": runner_hash,
        "source": source,
        "platform": platform_record,
        "tool_versions": tool_versions,
        "independence_requirement": row["independence_requirement"],
    }


def _execute_row(
    row,
    repo_root: Path,
    result_root: ResultRoot,
    manifest_hash: str,
    catalog_hash: str,
    runner_hash: str,
    acquisition_path: str,
    protected_paths: list[str],
    platform_record: dict[str, str],
    tool_versions: dict[str, str | None],
) -> dict[str, Any]:
    check_id = row["check_id"]
    check_fd, check_identity = mkdir_open_at(result_root.fd, check_id)
    runtime_tmp_path = None
    runtime_tmp_identity = None
    try:
        base_source = _git_state(repo_root)
        base_protected = _protected_state(repo_root, protected_paths)
        base_ignored = _ignored_state(repo_root, result_root.path)
        receipt = _receipt_base(
            row,
            manifest_hash,
            catalog_hash,
            runner_hash,
            base_source,
            platform_record,
            tool_versions,
        )
        if (
            platform_record["os"] not in row["platforms"]
            or row["applicability"]["state"] == "NOT_APPLICABLE"
        ):
            receipt.update(
                {
                    "execution_state": "NOT_APPLICABLE",
                    "verdict": "NOT_APPLICABLE",
                    "reason": "platform/applicability evidence excludes execution",
                    "error_code": None,
                    "tool_fingerprints": [],
                    "execution": {
                        "exit_code": None,
                        "signal": None,
                        "timed_out": False,
                        "interrupted": False,
                        "background_process": False,
                        "duration_monotonic_ns": 0,
                    },
                    "streams": {},
                    "required_artifacts": [],
                }
            )
            atomic_write_at(check_fd, "receipt.json", canonical_json_bytes(receipt))
            return receipt

        resolved_tools = {}
        missing_tools = []
        for tool_name in row["required_tools"]:
            tool = _resolve_tool(tool_name, acquisition_path, repo_root)
            if tool is None:
                missing_tools.append(tool_name)
            else:
                resolved_tools[tool_name] = tool
        if missing_tools:
            receipt.update(
                {
                    "execution_state": "NOT_RUN",
                    "verdict": "INCONCLUSIVE",
                    "reason": "required tool unavailable",
                    "error_code": "VERIFY_EXECUTABLE_DRIFT",
                    "tool_fingerprints": [
                        _tool_projection(item) for item in resolved_tools.values()
                    ],
                    "missing_tools": sorted(missing_tools),
                    "execution": {
                        "exit_code": None,
                        "signal": None,
                        "timed_out": False,
                        "interrupted": False,
                        "background_process": False,
                        "duration_monotonic_ns": 0,
                    },
                    "streams": {},
                    "required_artifacts": [],
                }
            )
            atomic_write_at(check_fd, "receipt.json", canonical_json_bytes(receipt))
            return receipt

        cwd = _existing_beneath(
            repo_root, row["working_directory"], "working_directory", directory=True
        )
        executable, executable_descriptor = _resolve_command(
            row, repo_root, cwd, resolved_tools
        )
        executable_fingerprint = _resolve_tool(
            executable.name, str(executable.parent), repo_root
        )
        if executable_fingerprint is None:
            raise VerificationError(
                "VERIFY_EXECUTABLE_DRIFT", "executable cannot be fingerprinted", 3
            )
        if not all(_tool_unchanged(tool) for tool in resolved_tools.values()):
            raise VerificationError(
                "VERIFY_EXECUTABLE_DRIFT", "tool changed before launch", 3
            )

        runtime_fd, _ = mkdir_open_at(check_fd, "runtime")
        try:
            home_fd, _ = mkdir_open_at(runtime_fd, "home")
            os.close(home_fd)
        finally:
            os.close(runtime_fd)
        runtime_tmp_path, runtime_tmp_identity = _make_runtime_tmp(repo_root, check_id)
        check_path = result_root.path / check_id
        home_path = check_path / "runtime" / "home"
        tmp_path = runtime_tmp_path
        host_home = pwd.getpwuid(os.getuid()).pw_dir
        substitutions = {
            "REPO_ROOT": str(repo_root),
            "HOST_HOME": host_home,
            "CHECK_HOME": str(home_path),
            "CHECK_TMPDIR": str(tmp_path),
        }
        path_parts = []
        for tool in [*resolved_tools.values(), executable_fingerprint]:
            parent = str(tool["path"].parent)
            if parent not in path_parts:
                path_parts.append(parent)
        for fixed in ("/usr/bin", "/bin"):
            if fixed not in path_parts:
                path_parts.append(fixed)
        effective_environment = {
            "PATH": ":".join(path_parts),
            "HOME": str(home_path),
            "TMPDIR": str(tmp_path),
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
        for key, value in row["environment"].items():
            effective_environment[key] = _expand(value, substitutions)
        environment_metadata = atomic_write_at(
            check_fd, "environment.json", canonical_json_bytes(effective_environment)
        )

        expanded_arguments = [
            _expand(argument, substitutions) for argument in row["command"][1:]
        ]
        argv = [str(executable), *expanded_arguments]
        stdout_fd = os.open(
            "stdout",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=check_fd,
        )
        stderr_fd = os.open(
            "stderr",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=check_fd,
        )
        try:
            os.fchmod(stdout_fd, 0o600)
            os.fchmod(stderr_fd, 0o600)
            outcome = _run_process(
                argv,
                cwd,
                effective_environment,
                stdout_fd,
                stderr_fd,
                row["timeout_seconds"],
                row["max_output_bytes"],
            )
            os.fsync(stdout_fd)
            os.fsync(stderr_fd)
        finally:
            os.close(stdout_fd)
            os.close(stderr_fd)
        os.fsync(check_fd)
        if not result_root.revalidate() or not revalidate_child(
            result_root.fd, check_id, check_fd, check_identity
        ):
            raise EvidenceWriteError(
                "result/check directory identity changed during execution"
            )

        stdout = _stream_bytes(check_fd, "stdout")
        stderr = _stream_bytes(check_fd, "stderr")
        post_source = _git_state(repo_root)
        post_protected = _protected_state(repo_root, protected_paths)
        post_ignored = _ignored_state(repo_root, result_root.path)
        verdict = "PASS"
        reason = "expected exit, observation, artifacts, and source state satisfied"
        error_code = None
        if outcome.interrupted:
            verdict, reason, error_code = (
                "INCONCLUSIVE",
                "runner interrupted",
                "VERIFY_INTERRUPTED",
            )
        elif outcome.timed_out:
            verdict, reason, error_code = (
                "INCONCLUSIVE",
                "check timed out",
                "VERIFY_TIMEOUT",
            )
        elif outcome.output_limited:
            verdict, reason, error_code = (
                "INCONCLUSIVE",
                "output limit exceeded",
                "VERIFY_OUTPUT_LIMIT",
            )
        elif outcome.background_process:
            verdict, reason, error_code = (
                "INCONCLUSIVE",
                "background or escaped descendant remained",
                "VERIFY_BACKGROUND_PROCESS",
            )
        elif outcome.exit_code in row["inconclusive_exit_codes"]:
            verdict, reason, error_code = (
                "INCONCLUSIVE",
                "explicit inconclusive exit observed",
                "VERIFY_EXIT_MISMATCH",
            )
        elif (
            outcome.exit_code != row["expected_exit"]
            or outcome.signal_number is not None
        ):
            verdict, reason, error_code = (
                "FAIL",
                "true exit did not match",
                "VERIFY_EXIT_MISMATCH",
            )

        if verdict == "PASS":
            observation_passed, observation_code = _evaluate_observation(
                row["expected_observation"], stdout, stderr
            )
            if not observation_passed:
                if observation_code in {
                    "VERIFY_ENCODING_INVALID",
                    "VERIFY_OUTPUT_LIMIT",
                }:
                    verdict = "INCONCLUSIVE"
                else:
                    verdict = "FAIL"
                reason = "expected observation was not satisfied"
                error_code = observation_code

        artifact_records = []
        if verdict == "PASS":
            try:
                artifact_records = _artifact_records(
                    check_fd, tmp_path, row["required_artifacts"]
                )
            except VerificationError as error:
                verdict, reason, error_code = "INCONCLUSIVE", str(error), error.code
            except EvidenceWriteError:
                raise

        source_changed = (
            base_source["candidate_sha"] != post_source["candidate_sha"]
            or base_source["status_sha256"] != post_source["status_sha256"]
            or base_source["content_sha256"] != post_source["content_sha256"]
            or base_protected != post_protected
            or base_ignored != post_ignored
        )
        if source_changed:
            verdict, reason, error_code = (
                "FAIL",
                "source/protected state changed",
                "VERIFY_SOURCE_MUTATION",
            )
        elif row["clean_source"] and base_source["dirty"]:
            verdict, reason, error_code = (
                "FAIL",
                "clean source required",
                "VERIFY_SOURCE_DIRTY",
            )

        receipt.update(
            {
                "execution_state": "RAN",
                "verdict": verdict,
                "reason": reason,
                "error_code": error_code,
                "resolved_executable": executable_descriptor,
                "tool_fingerprints": [
                    _tool_projection(tool)
                    for tool in sorted(
                        resolved_tools.values(), key=lambda item: item["name"]
                    )
                ],
                "environment_artifact": {
                    "path": f"{check_id}/environment.json",
                    **environment_metadata,
                },
                "execution": {
                    "started_utc": outcome.started_utc,
                    "ended_utc": outcome.ended_utc,
                    "duration_monotonic_ns": outcome.duration_ns,
                    "exit_code": outcome.exit_code,
                    "signal": outcome.signal_number,
                    "timed_out": outcome.timed_out,
                    "interrupted": outcome.interrupted,
                    "background_process": outcome.background_process,
                    "escaped_descendants_observed": len(outcome.escaped_descendants),
                },
                "streams": {
                    "stdout": _stream_metadata(check_fd, check_id, "stdout"),
                    "stderr": _stream_metadata(check_fd, check_id, "stderr"),
                },
                "required_artifacts": artifact_records,
                "source_after": post_source,
                "protected_ignored_before": base_protected,
                "protected_ignored_after": post_protected,
                "ignored_state_before_sha256": base_ignored,
                "ignored_state_after_sha256": post_ignored,
            }
        )
        atomic_write_at(check_fd, "receipt.json", canonical_json_bytes(receipt))
        return receipt
    finally:
        try:
            if runtime_tmp_path is not None and runtime_tmp_identity is not None:
                _cleanup_runtime_tmp(runtime_tmp_path, runtime_tmp_identity)
        finally:
            os.close(check_fd)


def _aggregate(receipts: list[dict[str, Any]]) -> tuple[str, int]:
    verdicts = [receipt["verdict"] for receipt in receipts]
    if "FAIL" in verdicts:
        return "FAIL", 1
    if "INCONCLUSIVE" in verdicts or any(
        receipt["execution_state"] == "NOT_RUN" for receipt in receipts
    ):
        return "INCONCLUSIVE", 3
    executed_required = any(
        receipt["execution_state"] == "RAN" and receipt["verdict"] == "PASS"
        for receipt in receipts
    )
    if not executed_required:
        return "INCONCLUSIVE", 3
    return "PASS", 0


def _requirement_projection(
    catalog: dict[str, Any], checks: list[dict[str, Any]], stage: str
) -> tuple[dict[str, Any], list[str]]:
    projection = {}
    unmet_or_later_owned = []
    for requirement_id, authority in sorted(catalog.items()):
        rows = [
            {
                "check_id": check["check_id"],
                "verdict": check["verdict"],
                "receipt_path": check["receipt_path"],
                "receipt_sha256": check["receipt_sha256"],
            }
            for check in checks
            if requirement_id in check["requirement_ids"]
        ]
        if authority["owner_release"] != stage:
            status = "LATER_OWNED"
        elif not rows:
            status = "UNMET"
        else:
            verdicts = {row["verdict"] for row in rows}
            if "FAIL" in verdicts:
                status = "FAIL"
            elif "INCONCLUSIVE" in verdicts:
                status = "INCONCLUSIVE"
            elif not authority["closure_in_1a"]:
                status = "PARTIAL"
            elif "PASS" in verdicts:
                status = "PASS"
            else:
                status = "NOT_APPLICABLE"
        projection[requirement_id] = {
            "source": authority["source"],
            "disposition": authority["disposition"],
            "owner_release": authority["owner_release"],
            "closure_in_1a": authority["closure_in_1a"],
            "status": status,
            "rows": rows,
        }
        if status in {"UNMET", "LATER_OWNED", "PARTIAL"}:
            unmet_or_later_owned.append(requirement_id)
    return projection, unmet_or_later_owned


def _print_error(code: str, message: str, *, run_id: str | None = None):
    sanitized = " ".join(str(message).replace("\n", " ").split())[:1000]
    safe_run_id = run_id if run_id and SAFE_SEGMENT.fullmatch(run_id) else "none"
    print(
        f"{code} check=none run={safe_run_id} candidate=unknown where=runner "
        f"what={sanitized} evidence=none remediation=inspect-protected-evidence",
        file=sys.stderr,
    )


def _validate_committed_error_catalog(repo_root: Path):
    catalog_path = _existing_beneath(
        repo_root, "verification/error-catalog.json", "error catalog"
    )
    validate_error_catalog(strict_json_load(catalog_path.read_bytes(), "error catalog"))


def _normal_run(args) -> int:
    repo_root = discover_repo_root(Path.cwd())
    _validate_committed_error_catalog(repo_root)
    if Path(args.manifest).is_absolute():
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "manifest path must be repository-relative"
        )
    manifest_path = _existing_beneath(repo_root, args.manifest, "manifest")
    raw_manifest = manifest_path.read_bytes()
    manifest = validate_manifest(strict_json_load(raw_manifest, "manifest"), repo_root)
    current_os, architecture, kernel_release = _current_platform()
    if args.platform != current_os:
        raise VerificationError(
            "VERIFY_PLATFORM_MISMATCH",
            f"asserted platform {args.platform} does not match detected {current_os}",
        )
    selected = [row for row in manifest["checks"] if row["stage"] == args.stage]
    if not selected:
        raise VerificationError(
            "VERIFY_SELECTION_EMPTY", "selected stage has zero checks"
        )
    result_root = create_result_root(repo_root, args.results_dir, args.run_id)
    try:
        manifest_hash = sha256_bytes(raw_manifest)
        catalog_hash = sha256_bytes(
            canonical_json_bytes(manifest["requirement_catalog"])
        )
        runner_hash = sha256_file(Path(__file__).resolve())
        acquisition_path = os.environ.get("PATH", "")
        platform_record = {
            "os": current_os,
            "architecture": architecture,
            "kernel_release": kernel_release,
        }
        tool_versions = _tool_versions(acquisition_path)
        receipts = []
        for row in selected:
            receipts.append(
                _execute_row(
                    row,
                    repo_root,
                    result_root,
                    manifest_hash,
                    catalog_hash,
                    runner_hash,
                    acquisition_path,
                    manifest["protected_ignored_paths"],
                    platform_record,
                    tool_versions,
                )
            )
        verdict, exit_code = _aggregate(receipts)
        counts = {
            name: 0 for name in ("PASS", "FAIL", "INCONCLUSIVE", "NOT_APPLICABLE")
        }
        for receipt in receipts:
            counts[receipt["verdict"]] += 1
        check_summaries = [
            {
                "check_id": receipt["check_id"],
                "execution_state": receipt["execution_state"],
                "verdict": receipt["verdict"],
                "error_code": receipt["error_code"],
                "receipt_path": f"{receipt['check_id']}/receipt.json",
                "receipt_sha256": sha256_file(
                    result_root.path / receipt["check_id"] / "receipt.json"
                ),
                "requirement_ids": receipt["requirement_ids"],
            }
            for receipt in receipts
        ]
        requirements, unmet_or_later_owned = _requirement_projection(
            manifest["requirement_catalog"], check_summaries, args.stage
        )
        summary = {
            "schema_version": RUN_SCHEMA,
            "runner_version": RUNNER_VERSION,
            "run_id": args.run_id,
            "stage": args.stage,
            "candidate_sha": receipts[0]["source"]["candidate_sha"],
            "manifest_sha256": manifest_hash,
            "requirement_catalog_sha256": catalog_hash,
            "runner_sha256": runner_hash,
            "platform": platform_record,
            "aggregate_verdict": verdict,
            "counts": counts,
            "checks": check_summaries,
            "requirements": requirements,
            "unmet_or_later_owned_requirements": unmet_or_later_owned,
            "generated_utc": utc_now(),
        }
        if not result_root.revalidate():
            raise EvidenceWriteError("result root identity changed before summary")
        metadata = atomic_write_at(
            result_root.fd, "run.json", canonical_json_bytes(summary)
        )
        if not result_root.revalidate():
            raise EvidenceWriteError("result root identity changed after summary")
        print(f"RUN_SHA256={metadata['sha256']}")
        return exit_code
    finally:
        result_root.close()


def validate_error_catalog(value: Any):
    catalog = _require_dict(value, "error catalog")
    _exact_keys(catalog, {"schema_version", "errors"}, "error catalog")
    if catalog["schema_version"] != ERROR_CATALOG_SCHEMA:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "unsupported error catalog schema"
        )
    errors = _require_list(catalog["errors"], "errors")
    seen = set()
    keys = {
        "code",
        "audience",
        "template",
        "remediation",
        "evidence_fields",
        "owning_requirement",
    }
    for raw in errors:
        entry = _require_dict(raw, "error entry")
        _exact_keys(entry, keys, "error entry")
        code = _require_string(entry["code"], "error code")
        if code in seen:
            raise VerificationError("VERIFY_MANIFEST_INVALID", "duplicate error code")
        seen.add(code)
        for key in ("audience", "template", "remediation", "owning_requirement"):
            _require_string(entry[key], f"error {key}")
        required_template_fields = (
            "check=<check_id>",
            "run=<run_id>",
            "candidate=<short-sha>",
            "where=<relative-surface>",
            "what=",
            "evidence=<relative-artifact>",
        )
        if any(field not in entry["template"] for field in required_template_fields):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID",
                "error template lacks required fields",
            )
        fields = _require_list(entry["evidence_fields"], "evidence_fields")
        if not fields:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "evidence_fields are empty"
            )
        for field in fields:
            _require_string(field, "evidence field")
    if seen != set(ERROR_CODES):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "error catalog coverage drift"
        )


def validate_baseline_inventory(value: Any):
    inventory = _require_dict(value, "baseline inventory")
    _exact_keys(inventory, {"schema_version", "items"}, "baseline inventory")
    if inventory["schema_version"] != BASELINE_SCHEMA:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "unsupported baseline inventory schema"
        )
    keys = {
        "stable_id",
        "class",
        "severity",
        "priority",
        "owner",
        "affected_requirements",
        "affected_stage_release",
        "trigger_or_due",
        "evidence",
        "rationale",
        "mitigation",
        "current_verdict",
        "disposition",
        "review_date",
        "closure_proof",
    }
    seen = set()
    for raw in _require_list(inventory["items"], "baseline items"):
        item = _require_dict(raw, "baseline item")
        _exact_keys(item, keys, "baseline item")
        stable_id = _require_string(item["stable_id"], "stable_id")
        if stable_id in seen:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "duplicate baseline stable_id"
            )
        seen.add(stable_id)
        if item["severity"] not in {"CRITICAL", "MATERIAL", "NONMATERIAL"}:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "invalid baseline severity"
            )
        _require_int(item["priority"], "priority", 0, 9)
        requirements = _require_list(
            item["affected_requirements"], "affected requirements"
        )
        if not requirements:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "affected requirements empty"
            )
        for requirement in requirements:
            _require_string(requirement, "affected requirement")
        for key in keys - {"priority", "affected_requirements"}:
            _require_string(item[key], f"baseline {key}")
        try:
            dt.date.fromisoformat(item["review_date"])
        except ValueError as error:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "review_date is invalid"
            ) from error
        if (
            item["class"] == "assumption"
            and item["severity"] == "CRITICAL"
            and item["priority"] == 0
            and item["affected_stage_release"] != "1A"
        ):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID",
                "load-bearing assumption cannot be deferred",
            )
        if item["affected_stage_release"] in {"1B", "1C"}:
            if not item["trigger_or_due"].strip() or not item["closure_proof"].strip():
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "deferred item lacks trigger/closure"
                )
            if item["current_verdict"] == "PASS":
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "deferred item cannot be closed green"
                )
        if (
            item["severity"] == "CRITICAL"
            and item["current_verdict"] == "PASS"
            and "PENDING" in item["disposition"]
        ):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "critical pending item cannot pass"
            )


def validate_review_state(value: Any):
    review = _require_dict(value, "review state")
    _exact_keys(
        review,
        {"schema_version", "prior_reviews", "release_1a_candidate_reviews"},
        "review state",
    )
    if review["schema_version"] != REVIEW_STATE_SCHEMA:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "unsupported review state schema"
        )
    prior_reviews = _require_list(review["prior_reviews"], "prior reviews")
    if not prior_reviews:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "prior review history is empty"
        )
    seen_review_ids = set()
    for raw in prior_reviews:
        entry = _require_dict(raw, "prior review")
        _exact_keys(
            entry, {"review_id", "kind", "verdict", "reason", "source"}, "prior review"
        )
        for key in entry:
            _require_string(entry[key], f"prior review {key}")
        if entry["review_id"] in seen_review_ids:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "duplicate prior review ID"
            )
        seen_review_ids.add(entry["review_id"])
        if entry["kind"] == "final-spec-review" and entry["verdict"] != "INCONCLUSIVE":
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID",
                "same-reviewer spec review must be INCONCLUSIVE",
            )
    required_history = {
        "same-reviewer-final-spec-pass-1": (
            "final-spec-review",
            "INCONCLUSIVE",
        ),
        "same-reviewer-final-spec-pass-2": (
            "final-spec-review",
            "INCONCLUSIVE",
        ),
        "owner-nominated-read-only-spec-review": (
            "owner-nominated-spec-review",
            "PASS_FOR_SPEC_ONLY",
        ),
    }
    observed_history = {
        entry["review_id"]: (entry["kind"], entry["verdict"]) for entry in prior_reviews
    }
    if any(
        observed_history.get(review_id) != expected
        for review_id, expected in required_history.items()
    ):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "required prior review history is missing"
        )
    candidates = _require_dict(
        review["release_1a_candidate_reviews"], "candidate reviews"
    )
    _exact_keys(candidates, {"independent", "adversarial"}, "candidate reviews")
    for role, entry in candidates.items():
        candidate = _require_dict(entry, f"{role} candidate review")
        if candidate != {"status": "PENDING"}:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "pre-freeze candidate review must be PENDING"
            )


def validate_review_result_schema(value: Any):
    schema = _require_dict(value, "review result schema")
    _exact_keys(
        schema,
        {
            "$schema",
            "$id",
            "title",
            "type",
            "additionalProperties",
            "required",
            "properties",
        },
        "review result schema",
    )
    required = _require_list(schema["required"], "review schema required")
    properties = _require_dict(schema["properties"], "review schema properties")
    findings = _require_dict(properties.get("findings"), "review schema findings")
    finding_items = _require_dict(findings.get("items"), "review schema finding items")
    finding_required = _require_list(
        finding_items.get("required"), "review schema finding required"
    )
    finding_properties = _require_dict(
        finding_items.get("properties"), "review schema finding properties"
    )
    string_field = {"type": "string", "minLength": 1}
    expected_finding_properties = {
        "finding": string_field,
        "severity": {"enum": sorted(REVIEW_FINDING_SEVERITIES)},
        "disposition": {"enum": sorted(REVIEW_FINDING_DISPOSITIONS)},
        "evidence": string_field,
        "owner": string_field,
        "due_trigger": string_field,
        "closure_proof": string_field,
    }
    if (
        schema["$id"] != REVIEW_RESULT_SCHEMA
        or schema["type"] != "object"
        or schema["additionalProperties"] is not False
        or len(required) != len(set(required))
        or set(required) != REVIEW_RESULT_KEYS
        or set(properties) != REVIEW_RESULT_KEYS
        or findings.get("type") != "array"
        or set(findings) != {"type", "items"}
        or finding_items.get("type") != "object"
        or finding_items.get("additionalProperties") is not False
        or set(finding_items)
        != {
            "type",
            "additionalProperties",
            "required",
            "properties",
        }
        or len(finding_required) != len(set(finding_required))
        or set(finding_required) != REVIEW_FINDING_KEYS
        or finding_properties != expected_finding_properties
    ):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID",
            "review result schema differs from runtime",
        )


def validate_review_result(
    value: Any,
    candidate: str,
    repo_root: Path,
    review_path: Path,
    manifest_hash: str,
    catalog_hash: str,
):
    result = _require_dict(value, "review result")
    _exact_keys(result, REVIEW_RESULT_KEYS, "review result")
    if result["schema_version"] != REVIEW_RESULT_SCHEMA:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "unsupported review result schema"
        )
    if not GIT_SHA.fullmatch(result["candidate_sha"]):
        raise VerificationError(
            "CANDIDATE_MISMATCH", "review candidate hash is invalid"
        )
    if result["candidate_sha"] != candidate:
        raise VerificationError(
            "CANDIDATE_MISMATCH", "review candidate does not match assertion"
        )
    for key in ("manifest_sha256", "requirement_catalog_sha256"):
        if not isinstance(result[key], str) or not SHA256.fullmatch(result[key]):
            raise VerificationError("VERIFY_MANIFEST_INVALID", f"{key} is invalid")
    if result["manifest_sha256"] != manifest_hash:
        raise VerificationError(
            "VERIFY_ARTIFACT_INVALID", "review manifest hash does not match authority"
        )
    if result["requirement_catalog_sha256"] != catalog_hash:
        raise VerificationError(
            "VERIFY_ARTIFACT_INVALID",
            "review requirement catalog hash does not match authority",
        )
    reviewer = _require_dict(result["reviewer"], "reviewer")
    _exact_keys(reviewer, {"runtime", "method"}, "reviewer")
    _require_string(reviewer["runtime"], "reviewer runtime")
    _require_string(reviewer["method"], "reviewer method")
    commands = _require_list(result["commands"], "review commands")
    if not commands:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "review commands are empty")
    for raw in commands:
        command = _require_dict(raw, "review command")
        _exact_keys(command, {"argv", "exit_code"}, "review command")
        argv = _require_list(command["argv"], "review command argv")
        if not argv:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "review command argv empty"
            )
        for argument in argv:
            _require_string(argument, "review command argument", nonempty=False)
        _require_int(command["exit_code"], "review command exit", 0, 255)
    claims = _require_list(result["material_claims"], "material claims")
    if not claims:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "material claims are empty")
    claim_keys = {"claim", "file_line", "symbol_or_test", "file_sha256"}
    for raw in claims:
        claim = _require_dict(raw, "material claim")
        _exact_keys(claim, claim_keys, "material claim")
        for key in claim_keys - {"file_sha256"}:
            _require_string(claim[key], f"claim {key}")
        if not SHA256.fullmatch(claim["file_sha256"]):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "claim file hash invalid"
            )
        try:
            claim_path_text, line_text = claim["file_line"].rsplit(":", 1)
            line_number = int(line_text)
        except (ValueError, AttributeError) as error:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "claim file_line must end in :<line>"
            ) from error
        if line_number < 1:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "claim line must be positive"
            )
        claim_path = _existing_beneath(repo_root, claim_path_text, "claim file")
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-files",
                "--error-unmatch",
                "--",
                claim_path_text,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if tracked.returncode != 0:
            raise VerificationError(
                "CANDIDATE_MISMATCH", "claim file is not tracked by the candidate"
            )
        claim_bytes = claim_path.read_bytes()
        if line_number > len(claim_bytes.splitlines()):
            raise VerificationError(
                "VERIFY_ARTIFACT_INVALID", "claim line is outside the cited file"
            )
        if sha256_bytes(claim_bytes) != claim["file_sha256"]:
            raise VerificationError(
                "VERIFY_ARTIFACT_INVALID", "claim file hash does not match"
            )
    findings = _require_list(result["findings"], "findings")
    for raw in findings:
        finding = _require_dict(raw, "finding")
        _exact_keys(finding, REVIEW_FINDING_KEYS, "finding")
        for key in {
            "finding",
            "evidence",
            "owner",
            "due_trigger",
            "closure_proof",
        }:
            _require_string(finding[key], f"finding {key}")
        if finding["severity"] not in REVIEW_FINDING_SEVERITIES:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "finding severity is invalid"
            )
        if finding["disposition"] not in REVIEW_FINDING_DISPOSITIONS:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "finding disposition is invalid"
            )
    limitations = _require_list(result["limitations"], "limitations")
    for limitation in limitations:
        _require_string(limitation, "limitation")
    hashes = _require_dict(
        result["protected_evidence_hashes"], "protected evidence hashes"
    )
    if not hashes:
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "protected review evidence is empty"
        )
    for path, digest in hashes.items():
        _require_string(path, "protected evidence path")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "protected evidence hash invalid"
            )
        evidence_path = _existing_beneath(
            review_path.parent, path, "protected review evidence"
        )
        if sha256_file(evidence_path) != digest:
            raise VerificationError(
                "VERIFY_ARTIFACT_INVALID", "protected review evidence hash mismatch"
            )
    if result["verdict"] not in {"PASS", "FAIL", "INCONCLUSIVE"}:
        raise VerificationError("VERIFY_MANIFEST_INVALID", "review verdict invalid")
    if result["verdict"] == "PASS" and any(
        finding["severity"] in {"CRITICAL", "MATERIAL"}
        and finding["disposition"] == "UNRESOLVED"
        for finding in findings
    ):
        raise VerificationError(
            "VERIFY_MANIFEST_INVALID", "passing review has unresolved material finding"
        )


def _review_validation(args) -> int:
    if not args.candidate or not GIT_SHA.fullmatch(args.candidate):
        raise VerificationError("CANDIDATE_MISMATCH", "candidate assertion is invalid")
    repo_root = discover_repo_root(Path.cwd())
    source = _git_state(repo_root)
    if source["candidate_sha"] != args.candidate:
        raise VerificationError(
            "CANDIDATE_MISMATCH", "candidate assertion does not match repository HEAD"
        )
    if source["dirty"]:
        raise VerificationError("CANDIDATE_MISMATCH", "candidate worktree is not clean")
    _validate_committed_error_catalog(repo_root)
    review_path = _existing_beneath(
        repo_root, args.validate_review_result, "review result"
    )
    value = strict_json_load(review_path.read_bytes(), "review result")
    schema_path = _existing_beneath(
        repo_root,
        "verification/review-result.schema.json",
        "review result schema",
    )
    validate_review_result_schema(
        strict_json_load(schema_path.read_bytes(), "review result schema")
    )
    manifest_path = _existing_beneath(
        repo_root, "verification/manifest.json", "verification manifest"
    )
    raw_manifest = manifest_path.read_bytes()
    manifest = validate_manifest(
        strict_json_load(raw_manifest, "verification manifest"), repo_root
    )
    validate_review_result(
        value,
        args.candidate,
        repo_root,
        review_path,
        sha256_bytes(raw_manifest),
        sha256_bytes(canonical_json_bytes(manifest["requirement_catalog"])),
    )
    print("REVIEW_RESULT_VALID")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = VerificationArgumentParser(
        description="Run fail-closed SDLC-OS verification checks and write protected receipts."
    )
    parser.add_argument("--manifest")
    parser.add_argument("--stage")
    parser.add_argument("--results-dir")
    parser.add_argument("--platform", choices=("macos", "linux"))
    parser.add_argument("--run-id")
    parser.add_argument("--validate-review-result")
    parser.add_argument("--candidate")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = None
    try:
        args = parser.parse_args(argv)
        if args.validate_review_result:
            if any(
                (
                    args.manifest,
                    args.stage,
                    args.results_dir,
                    args.platform,
                    args.run_id,
                )
            ):
                raise VerificationError(
                    "VERIFY_MANIFEST_INVALID", "review and run modes are exclusive"
                )
            return _review_validation(args)
        required = {
            "manifest": args.manifest,
            "stage": args.stage,
            "results_dir": args.results_dir,
            "platform": args.platform,
            "run_id": args.run_id,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", f"missing run arguments: {missing}"
            )
        if args.candidate:
            raise VerificationError(
                "VERIFY_MANIFEST_INVALID", "--candidate requires review mode"
            )
        return _normal_run(args)
    except EvidenceWriteError as error:
        _print_error(
            "VERIFY_WRITE_FAILED", str(error), run_id=getattr(args, "run_id", None)
        )
        return 70
    except VerificationError as error:
        _print_error(error.code, str(error), run_id=getattr(args, "run_id", None))
        return error.exit_code
    except (OSError, subprocess.SubprocessError) as error:
        _print_error(
            "VERIFY_WRITE_FAILED", str(error), run_id=getattr(args, "run_id", None)
        )
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
