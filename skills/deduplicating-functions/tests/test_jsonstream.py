"""Contract tests for scripts/lib/jsonstream.py — stdlib incremental JSON readers.

The 2026-08-22 incident: a 2.05 GB merged-results.json was parsed whole by jq
(22.7 GB footprint) and by json.load (5.25 GB). Every reader in the pipeline
must now be incremental and fail closed on malformed input.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).parent.parent / "scripts" / "lib"
sys.path.insert(0, str(_LIB))

import jsonstream  # noqa: E402


def test_module_importable():
    assert hasattr(jsonstream, "iter_json_array")
    assert hasattr(jsonstream, "iter_jsonl")
    assert hasattr(jsonstream, "JSONStreamError")


def _write(tmp_path: Path, name: str, text: str) -> str:
    p = tmp_path / name
    p.write_text(text)
    return str(p)


@pytest.mark.parametrize("indent", [None, 2])
def test_iter_json_array_yields_every_element_in_order(tmp_path, indent):
    objs = [{"i": i, "s": "x" * i, "nested": {"a": [i, i + 1]}} for i in range(50)]
    path = _write(tmp_path, "arr.json", json.dumps(objs, indent=indent))
    got = list(jsonstream.iter_json_array(path))
    assert got == objs


def test_iter_json_array_small_chunks_cross_boundaries(tmp_path):
    """Elements that straddle read-chunk boundaries must still decode."""
    objs = [{"k": "v" * 300, "n": i} for i in range(40)]
    path = _write(tmp_path, "arr.json", json.dumps(objs, indent=2))
    got = list(jsonstream.iter_json_array(path, chunk_size=7))
    assert got == objs


def test_iter_json_array_empty_array(tmp_path):
    path = _write(tmp_path, "empty.json", "[]")
    assert list(jsonstream.iter_json_array(path)) == []
    path2 = _write(tmp_path, "empty2.json", "  [ \n ]\n")
    assert list(jsonstream.iter_json_array(path2)) == []


def test_iter_json_array_rejects_non_array(tmp_path):
    path = _write(tmp_path, "obj.json", '{"pairs": []}')
    with pytest.raises(jsonstream.JSONStreamError):
        list(jsonstream.iter_json_array(path))


def test_iter_json_array_rejects_truncated_final_element(tmp_path):
    objs = [{"i": 1}, {"i": 2}, {"i": 3}]
    text = json.dumps(objs)[:-4]  # cut inside the last object
    path = _write(tmp_path, "trunc.json", text)
    it = jsonstream.iter_json_array(path)
    assert next(it) == {"i": 1}
    with pytest.raises(jsonstream.JSONStreamError):
        list(it)


def test_iter_json_array_rejects_trailing_garbage(tmp_path):
    path = _write(tmp_path, "trail.json", '[{"i": 1}] xyz')
    with pytest.raises(jsonstream.JSONStreamError):
        list(jsonstream.iter_json_array(path))


def test_iter_json_array_rejects_oversized_element(tmp_path):
    objs = [{"i": 1}, {"big": "x" * 5000}]
    path = _write(tmp_path, "big.json", json.dumps(objs))
    with pytest.raises(jsonstream.JSONStreamError):
        list(jsonstream.iter_json_array(path, max_element_bytes=1024))


def test_iter_json_array_does_not_read_whole_file(tmp_path, monkeypatch):
    """Peak buffer must stay near chunk size, not file size."""
    objs = [{"i": i, "pad": "p" * 200} for i in range(2000)]
    path = _write(tmp_path, "arr.json", json.dumps(objs))
    size = os.path.getsize(path)
    peak = {"buf": 0}
    orig = jsonstream._decode_next
    def spy(buf, pos):
        peak["buf"] = max(peak["buf"], len(buf))
        return orig(buf, pos)
    monkeypatch.setattr(jsonstream, "_decode_next", spy)
    n = sum(1 for _ in jsonstream.iter_json_array(path, chunk_size=4096))
    assert n == 2000
    assert peak["buf"] < size // 10, f"buffer grew to {peak['buf']} of {size}"


def test_iter_jsonl_yields_objects_and_rejects_bad_line(tmp_path):
    good = [{"a": 1}, {"b": [1, 2]}]
    path = _write(tmp_path, "ok.jsonl", "\n".join(json.dumps(o) for o in good) + "\n")
    assert list(jsonstream.iter_jsonl(path)) == good
    bad = _write(tmp_path, "bad.jsonl", '{"a": 1}\n{"broken": \n{"c": 3}\n')
    it = jsonstream.iter_jsonl(bad)
    assert next(it) == {"a": 1}
    with pytest.raises(jsonstream.JSONStreamError) as ei:
        list(it)
    assert "line 2" in str(ei.value)


def test_iter_jsonl_rejects_non_object_line(tmp_path):
    path = _write(tmp_path, "arr.jsonl", '{"a": 1}\n[1,2]\n')
    with pytest.raises(jsonstream.JSONStreamError):
        list(jsonstream.iter_jsonl(path))


def test_detect_format(tmp_path):
    a = _write(tmp_path, "a.json", "\n [ {\"x\":1} ]")
    j = _write(tmp_path, "j.jsonl", '{"x":1}\n{"x":2}\n')
    e = _write(tmp_path, "e.json", "   ")
    o = _write(tmp_path, "o.json", '{"pairs": []}')
    assert jsonstream.detect_format(a) == "array"
    assert jsonstream.detect_format(j) == "jsonl"
    assert jsonstream.detect_format(e) == "empty"
    assert jsonstream.detect_format(o) == "object"


def test_atomic_write_replaces_only_on_success(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("old")
    def ok(fh):
        fh.write("new")
    jsonstream.atomic_write_text(str(target), ok)
    assert target.read_text() == "new"
    def boom(fh):
        fh.write("partial")
        raise OSError(28, "No space left on device")
    with pytest.raises(OSError):
        jsonstream.atomic_write_text(str(target), boom)
    assert target.read_text() == "new", "failed write must not clobber the previous artifact"
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith("out.txt.")]
    assert leftovers == [], f"temp file leaked: {leftovers}"
