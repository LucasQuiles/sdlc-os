"""Incremental JSON readers and an atomic text writer (standard library only).

Why this exists: on 2026-08-22 a 2.05 GB ``merged-results.json`` was parsed
whole by ``jq`` (22.7 GB task footprint) and by ``json.load`` (5.25 GB) on a
36 GB host, which exhausted the VM compressor and swap. Every reader of
detector/merge artifacts now streams one element at a time with a bounded
buffer, and every writer publishes atomically so a failed run can never leave
a half-written artifact under the success filename.

Public API
----------
iter_json_array(path, *, chunk_size, max_element_bytes)          -> Iterator[Any]
iter_object_member_array(path, key, *, chunk_size, max_element_bytes) -> Iterator[Any]
load_object_member(path, key, *, chunk_size, max_bytes)          -> Any
iter_jsonl(path, *, max_line_bytes)                              -> Iterator[dict]
detect_format(path)                                              -> "array"|"jsonl"|"object"|"empty"
atomic_write_text(path, writer, *, encoding="utf-8")             -> int (bytes published)
JSONStreamError(ValueError)
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Callable, Iterator, TextIO

__all__ = [
    "JSONStreamError",
    "iter_json_array",
    "iter_object_member_array",
    "load_object_member",
    "iter_jsonl",
    "detect_format",
    "atomic_write_text",
]

DEFAULT_CHUNK_SIZE = 1 << 20          # 1 MiB read granularity
DEFAULT_MAX_ELEMENT_BYTES = 64 << 20  # one array element / member may not exceed 64 MiB
DEFAULT_MAX_LINE_BYTES = 64 << 20

_WS = " \t\r\n"
_DECODER = json.JSONDecoder()


class JSONStreamError(ValueError):
    """Malformed, truncated, oversized, or wrongly-shaped JSON input."""


def _decode_next(buf: str, pos: int):
    """Decode one JSON value starting at ``buf[pos]``.

    Module-level so tests can observe buffer growth. Raises
    json.JSONDecodeError when the value is incomplete or invalid.
    """
    return _DECODER.raw_decode(buf, pos)


class _Cursor:
    """A forward-only reader over a text file with a bounded, compacting buffer."""

    def __init__(self, fh: TextIO, path: str, chunk_size: int, max_element_bytes: int) -> None:
        if chunk_size <= 0 or max_element_bytes <= 0:
            raise JSONStreamError("chunk_size and max_element_bytes must be positive")
        self.fh = fh
        self.path = path
        self.chunk_size = chunk_size
        self.max_element_bytes = max_element_bytes
        self.buf = ""
        self.pos = 0
        self.eof = False

    # -- buffer management ---------------------------------------------------
    def fill(self) -> None:
        if self.pos:
            self.buf = self.buf[self.pos:]
            self.pos = 0
        chunk = self.fh.read(self.chunk_size)
        if chunk:
            self.buf += chunk
        else:
            self.eof = True

    def skip_ws(self, context: str) -> str:
        """Advance past whitespace and return the next character (never EOF)."""
        while True:
            buf, pos = self.buf, self.pos
            while pos < len(buf) and buf[pos] in _WS:
                pos += 1
            self.pos = pos
            if pos < len(buf):
                return buf[pos]
            if self.eof:
                raise JSONStreamError(f"{self.path}: unexpected end of input {context}")
            self.fill()

    def peek_ws_or_eof(self) -> str | None:
        """Like skip_ws but returns None at EOF instead of raising."""
        while True:
            buf, pos = self.buf, self.pos
            while pos < len(buf) and buf[pos] in _WS:
                pos += 1
            self.pos = pos
            if pos < len(buf):
                return buf[pos]
            if self.eof:
                return None
            self.fill()

    def expect(self, ch: str, context: str) -> None:
        got = self.skip_ws(context)
        if got != ch:
            raise JSONStreamError(f"{self.path}: expected {ch!r} {context}, found {got!r}")
        self.pos += 1

    # -- values ----------------------------------------------------------------
    def decode_value(self, context: str) -> Any:
        """Decode one complete JSON value at the cursor, pulling data as needed."""
        while True:
            buf, pos = self.buf, self.pos
            try:
                obj, end = _decode_next(buf, pos)
            except json.JSONDecodeError as exc:
                if self.eof:
                    raise JSONStreamError(
                        f"{self.path}: {context} is malformed or truncated: {exc.msg}"
                    ) from None
                if len(buf) - pos > self.max_element_bytes:
                    raise JSONStreamError(
                        f"{self.path}: {context} exceeds max_element_bytes={self.max_element_bytes}"
                    )
                self.fill()
                continue
            if end - pos > self.max_element_bytes:
                raise JSONStreamError(
                    f"{self.path}: {context} exceeds max_element_bytes={self.max_element_bytes}"
                )
            if end == len(buf) and not self.eof:
                # A scalar might continue in the next chunk (e.g. "12" of "123").
                self.fill()
                continue
            self.pos = end
            return obj

    def iter_array(self, context: str) -> Iterator[Any]:
        """Cursor must sit at '['. Yields elements; consumes through ']'."""
        self.expect("[", context)
        index = 0
        expect = "first"  # first | value | separator
        while True:
            c = self.skip_ws(f"inside array ({context}) after element {index}")
            if c == "]" and expect in ("first", "separator"):
                self.pos += 1
                return
            if expect == "separator":
                if c != ",":
                    raise JSONStreamError(
                        f"{self.path}: expected ',' or ']' after element {index} ({context}), found {c!r}"
                    )
                self.pos += 1
                expect = "value"
                continue
            if c == "]":
                raise JSONStreamError(
                    f"{self.path}: trailing comma before ']' after element {index} ({context})"
                )
            obj = self.decode_value(f"element {index} ({context})")
            index += 1
            expect = "separator"
            yield obj

    def skip_value(self, context: str) -> None:
        """Consume and discard one value. Arrays are skipped element-wise."""
        c = self.skip_ws(context)
        if c == "[":
            for _ in self.iter_array(context):
                pass
            return
        self.decode_value(context)

    def assert_only_trailing_ws(self) -> None:
        c = self.peek_ws_or_eof()
        if c is not None:
            raise JSONStreamError(
                f"{self.path}: trailing content after top-level value ({self.buf[self.pos:self.pos + 20]!r})"
            )

    def iter_object_members(self, context: str) -> Iterator[str]:
        """Cursor must sit at '{'. Yields each member key with the cursor left at
        the member's value; the caller MUST consume the value (decode_value /
        iter_array / skip_value) before advancing the generator."""
        self.expect("{", context)
        expect = "first"
        while True:
            c = self.skip_ws(f"inside object ({context})")
            if c == "}" and expect in ("first", "separator"):
                self.pos += 1
                return
            if expect == "separator":
                if c != ",":
                    raise JSONStreamError(
                        f"{self.path}: expected ',' or '}}' in object ({context}), found {c!r}"
                    )
                self.pos += 1
                expect = "key"
                continue
            if c == "}":
                raise JSONStreamError(f"{self.path}: trailing comma in object ({context})")
            key = self.decode_value(f"object key ({context})")
            if not isinstance(key, str):
                raise JSONStreamError(f"{self.path}: object key is not a string ({context})")
            self.expect(":", f"after key {key!r} ({context})")
            self.skip_ws(f"before value of {key!r} ({context})")
            yield key
            expect = "separator"


def _open_cursor(path: str, chunk_size: int, max_element_bytes: int):
    fh = open(path, "r", encoding="utf-8")
    return fh, _Cursor(fh, path, chunk_size, max_element_bytes)


def iter_json_array(
    path: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_element_bytes: int = DEFAULT_MAX_ELEMENT_BYTES,
) -> Iterator[Any]:
    """Yield the elements of a top-level JSON array without loading the file.

    Fails closed (JSONStreamError) on a non-array document, a truncated or
    malformed element, trailing content, or an element larger than
    ``max_element_bytes`` — possibly after earlier elements were yielded, so
    consumers needing all-or-nothing semantics must stage their output.
    """
    fh, cur = _open_cursor(path, chunk_size, max_element_bytes)
    with fh:
        first = cur.peek_ws_or_eof()
        if first is None:
            raise JSONStreamError(f"{path}: empty input, expected a JSON array")
        if first != "[":
            raise JSONStreamError(f"{path}: expected top-level JSON array, found {first!r}")
        yield from cur.iter_array("top-level array")
        cur.assert_only_trailing_ws()


def iter_object_member_array(
    path: str,
    key: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_element_bytes: int = DEFAULT_MAX_ELEMENT_BYTES,
) -> Iterator[Any]:
    """Stream the elements of top-level object member ``key`` (an array).

    Other members are skipped element-wise (arrays) or decoded-and-discarded
    under ``max_element_bytes``. Raises JSONStreamError if the document is not
    an object, the member is absent, or its value is not an array.
    """
    fh, cur = _open_cursor(path, chunk_size, max_element_bytes)
    with fh:
        first = cur.peek_ws_or_eof()
        if first is None:
            raise JSONStreamError(f"{path}: empty input, expected a JSON object")
        if first != "{":
            raise JSONStreamError(f"{path}: expected top-level JSON object, found {first!r}")
        members = cur.iter_object_members("top-level object")
        for member in members:
            if member == key:
                c = cur.skip_ws(f"value of {key!r}")
                if c != "[":
                    raise JSONStreamError(f"{path}: member {key!r} is not an array (found {c!r})")
                yield from cur.iter_array(f"member {key!r}")
                return
            cur.skip_value(f"member {member!r}")
        raise JSONStreamError(f"{path}: top-level object has no member {key!r}")


def load_object_member(
    path: str,
    key: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_bytes: int = DEFAULT_MAX_ELEMENT_BYTES,
) -> Any:
    """Return the decoded value of top-level object member ``key`` (bounded by
    ``max_bytes``); array-valued siblings are skipped element-wise."""
    fh, cur = _open_cursor(path, chunk_size, max_bytes)
    with fh:
        first = cur.peek_ws_or_eof()
        if first is None:
            raise JSONStreamError(f"{path}: empty input, expected a JSON object")
        if first != "{":
            raise JSONStreamError(f"{path}: expected top-level JSON object, found {first!r}")
        for member in cur.iter_object_members("top-level object"):
            if member == key:
                return cur.decode_value(f"member {key!r}")
            cur.skip_value(f"member {member!r}")
        raise JSONStreamError(f"{path}: top-level object has no member {key!r}")


def iter_jsonl(path: str, *, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES) -> Iterator[dict]:
    """Yield one JSON object per non-blank line. Any bad line fails closed."""
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if len(line) > max_line_bytes:
                raise JSONStreamError(f"{path}: line {lineno} exceeds max_line_bytes={max_line_bytes}")
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise JSONStreamError(f"{path}: line {lineno} is not valid JSON: {exc.msg}") from None
            if not isinstance(obj, dict):
                raise JSONStreamError(
                    f"{path}: line {lineno} is a JSON {type(obj).__name__}, expected an object"
                )
            yield obj


def detect_format(path: str) -> str:
    """Classify a file as 'array', 'jsonl', 'object', or 'empty'.

    ``.jsonl`` files are JSON Lines by declaration. Otherwise the first
    non-whitespace character decides: '[' → array, '{' → object.
    """
    if path.endswith(".jsonl"):
        return "jsonl"
    with open(path, "r", encoding="utf-8") as fh:
        while True:
            chunk = fh.read(4096)
            if not chunk:
                return "empty"
            for ch in chunk:
                if ch in _WS:
                    continue
                if ch == "[":
                    return "array"
                if ch == "{":
                    return "object"
                raise JSONStreamError(f"{path}: unexpected leading character {ch!r}")


def atomic_write_text(
    path: str,
    writer: Callable[[TextIO], None],
    *,
    encoding: str = "utf-8",
) -> int:
    """Write via ``writer(fh)`` to a sibling temp file, fsync, then os.replace.

    On any exception the temp file is removed and the previous artifact (if
    any) is left untouched. Returns the number of bytes published.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    base = os.path.basename(path)
    fd, tmp = tempfile.mkstemp(prefix=f"{base}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            writer(fh)
            fh.flush()
            os.fsync(fh.fileno())
        size = os.path.getsize(tmp)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    try:  # best effort: make the rename durable
        dfd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass
    return size
