#!/usr/bin/env python3.12

import json
import os
import re
import stat
import sys


TOKEN_VERSION = "f01-temp-tree-token-v1"
TOKEN_KEYS = {
    "leaf_hex",
    "parent_dev",
    "parent_ino",
    "root_dev",
    "root_ino",
    "schema_version",
}
OPEN_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
PREFIX_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.\Z")


class TreeError(Exception):
    pass


def fail(code: str, detail: str, status: int = 1) -> None:
    print(f"{code}:{detail}", file=sys.stderr)
    raise SystemExit(status)


def validate_runtime() -> None:
    if sys.version_info[:2] != (3, 12):
        fail("F01_TEMP_TREE_RUNTIME", "Python 3.12 required", 64)


def parse_root(root: str, prefix: str) -> tuple[bytes, list[bytes], bytes]:
    if not PREFIX_PATTERN.fullmatch(prefix):
        raise TreeError("invalid-prefix")
    if not os.path.isabs(root) or root == os.sep or os.path.normpath(root) != root:
        raise TreeError("invalid-root-path")
    raw_root = os.fsencode(root)
    components = raw_root[1:].split(b"/")
    if not components or any(part in (b"", b".", b"..") for part in components):
        raise TreeError("invalid-root-components")
    leaf = components[-1]
    if not leaf.startswith(prefix.encode("ascii")):
        raise TreeError("root-prefix-mismatch")
    return raw_root, components, leaf


def open_parent(components: list[bytes]) -> int:
    descriptor = os.open(b"/", OPEN_FLAGS)
    try:
        for component in components[:-1]:
            child = os.open(component, OPEN_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def require_private_directory(metadata: os.stat_result, detail: str) -> None:
    if not stat.S_ISDIR(metadata.st_mode):
        raise TreeError(f"{detail}-not-directory")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise TreeError(f"{detail}-mode")


def open_root(parent_fd: int, leaf: bytes) -> tuple[int, os.stat_result]:
    before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
    require_private_directory(before, "root")
    descriptor = os.open(leaf, OPEN_FLAGS, dir_fd=parent_fd)
    try:
        opened = os.fstat(descriptor)
        require_private_directory(opened, "opened-root")
        if not same_identity(before, opened):
            raise TreeError("root-open-drift")
        return descriptor, opened
    except BaseException:
        os.close(descriptor)
        raise


def encode_token(leaf: bytes, parent: os.stat_result, root: os.stat_result) -> str:
    value = {
        "leaf_hex": leaf.hex(),
        "parent_dev": parent.st_dev,
        "parent_ino": parent.st_ino,
        "root_dev": root.st_dev,
        "root_ino": root.st_ino,
        "schema_version": TOKEN_VERSION,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise TreeError("token-duplicate-key")
        value[key] = item
    return value


def parse_token(raw: str) -> dict[str, int | str | bytes]:
    if len(raw.encode("utf-8")) > 2048:
        raise TreeError("token-too-large")
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TreeError("token-json") from error
    if type(value) is not dict or set(value) != TOKEN_KEYS:
        raise TreeError("token-shape")
    if value["schema_version"] != TOKEN_VERSION:
        raise TreeError("token-version")
    for key in ("parent_dev", "parent_ino", "root_dev", "root_ino"):
        if type(value[key]) is not int or value[key] < 0:
            raise TreeError(f"token-{key}")
    if type(value["leaf_hex"]) is not str or not value["leaf_hex"]:
        raise TreeError("token-leaf")
    try:
        leaf = bytes.fromhex(value["leaf_hex"])
    except ValueError as error:
        raise TreeError("token-leaf-hex") from error
    if not leaf or b"/" in leaf or b"\x00" in leaf:
        raise TreeError("token-leaf-value")
    value["leaf"] = leaf
    return value


def require_token_identity(
    token: dict[str, int | str | bytes],
    parent: os.stat_result,
    root: os.stat_result,
    leaf: bytes,
) -> None:
    if token["leaf"] != leaf:
        raise TreeError("token-root-leaf-mismatch")
    if (token["parent_dev"], token["parent_ino"]) != (
        parent.st_dev,
        parent.st_ino,
    ):
        raise TreeError("parent-identity-drift")
    if (token["root_dev"], token["root_ino"]) != (root.st_dev, root.st_ino):
        raise TreeError("root-identity-drift")


def require_entry_identity(
    directory_fd: int, name: bytes, expected: os.stat_result
) -> os.stat_result:
    current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if not same_identity(expected, current) or stat.S_IFMT(
        expected.st_mode
    ) != stat.S_IFMT(current.st_mode):
        raise TreeError("entry-identity-drift")
    return current


def clear_directory(directory_fd: int, device: int) -> None:
    names = sorted((os.fsencode(name) for name in os.listdir(directory_fd)))
    for name in names:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISDIR(metadata.st_mode):
            child_fd = os.open(name, OPEN_FLAGS, dir_fd=directory_fd)
            try:
                opened = os.fstat(child_fd)
                if not same_identity(metadata, opened) or opened.st_dev != device:
                    raise TreeError("child-directory-drift")
                clear_directory(child_fd, device)
                require_entry_identity(directory_fd, name, opened)
                os.rmdir(name, dir_fd=directory_fd)
            finally:
                os.close(child_fd)
        elif stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            require_entry_identity(directory_fd, name, metadata)
            os.unlink(name, dir_fd=directory_fd)
        else:
            raise TreeError("unsupported-entry-type")


def apply_post_open_swap(parent_fd: int, leaf: bytes, prefix: str) -> None:
    if os.environ.get("F01_TEMP_TREE_TEST_POST_OPEN_SWAP") != "1":
        return
    if prefix != "sdlc-f01-retarget." or leaf != b"sdlc-f01-retarget.root":
        raise TreeError("test-hook-scope")
    held = leaf + b".opened-original"
    replacement = leaf + b".replacement"
    try:
        os.stat(held, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise TreeError("test-hook-held-exists")
    replacement_state = os.stat(replacement, dir_fd=parent_fd, follow_symlinks=False)
    require_private_directory(replacement_state, "test-hook-replacement")
    os.rename(leaf, held, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    os.rename(replacement, leaf, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)


def capture(root_path: str, prefix: str) -> None:
    _, components, leaf = parse_root(root_path, prefix)
    if os.environ.get("F01_TEMP_TREE_TEST_CAPTURE_FAILURE") == "1":
        if prefix != "sdlc-dispatch-test." or not leaf.startswith(
            b"sdlc-dispatch-test."
        ):
            raise TreeError("test-hook-scope")
        raise TreeError("test-capture-failure")
    parent_fd = open_parent(components)
    try:
        parent_state = os.fstat(parent_fd)
        root_fd, root_state = open_root(parent_fd, leaf)
        os.close(root_fd)
        print(encode_token(leaf, parent_state, root_state))
    finally:
        os.close(parent_fd)


def remove(root_path: str, prefix: str, raw_token: str) -> None:
    _, components, leaf = parse_root(root_path, prefix)
    token = parse_token(raw_token)
    parent_fd = open_parent(components)
    try:
        parent_state = os.fstat(parent_fd)
        root_fd, root_state = open_root(parent_fd, leaf)
        try:
            require_token_identity(token, parent_state, root_state, leaf)
            apply_post_open_swap(parent_fd, leaf, prefix)
            require_entry_identity(parent_fd, leaf, root_state)
            clear_directory(root_fd, root_state.st_dev)
            current = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
            if not same_identity(root_state, current) or not stat.S_ISDIR(
                current.st_mode
            ):
                raise TreeError("final-root-identity-drift")
            os.rmdir(leaf, dir_fd=parent_fd)
        finally:
            os.close(root_fd)
    finally:
        os.close(parent_fd)


def main() -> None:
    validate_runtime()
    if len(sys.argv) == 4 and sys.argv[1] == "capture":
        capture(sys.argv[2], sys.argv[3])
        return
    if len(sys.argv) == 5 and sys.argv[1] == "remove":
        remove(sys.argv[2], sys.argv[3], sys.argv[4])
        return
    fail("F01_TEMP_TREE_USAGE", "capture|remove root prefix [token]", 64)


if __name__ == "__main__":
    try:
        main()
    except TreeError as error:
        fail("F01_TEMP_TREE_RETAINED", str(error))
    except OSError as error:
        fail("F01_TEMP_TREE_RETAINED", error.__class__.__name__)
