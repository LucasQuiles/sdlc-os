"""JSON Schema validation for detector and merge outputs.

Locks the output contract so schema drift is caught at test time
rather than breaking downstream consumers. Schemas live in
`schemas/` at the repo root.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

jsonschema = pytest.importorskip("jsonschema")

PYTHON = sys.executable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
SCHEMAS = os.path.join(BASE, "schemas")
CORPUS = os.path.join(BASE, "tests", "fixtures", "adversarial-corpus.json")

DETECTOR_SCHEMA_PATH = os.path.join(SCHEMAS, "detector-output.schema.json")
MERGE_SCHEMA_PATH = os.path.join(SCHEMAS, "merge-output.schema.json")


@pytest.fixture(scope="module")
def detector_schema():
    with open(DETECTOR_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def merge_schema():
    with open(MERGE_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def adversarial_catalog(tmp_path_factory):
    """Write corpus functions to a temp catalog for detectors."""
    tmp = tmp_path_factory.mktemp("catalog")
    with open(CORPUS) as f:
        data = json.load(f)
    path = tmp / "catalog.json"
    with open(path, "w") as f:
        json.dump(data["functions"], f)
    return str(path)


# Map detector script filename to the output filename run_pipeline.py uses.
# Several detectors use a singular name for the output even when the script
# is plural, so the mapping is not mechanical.
DETECTOR_OUTPUT_MAP = {
    "detect-fuzzy-names.py": "fuzzy-name-results.json",
    "detect-signature-match.py": "signature-match-results.json",
    "detect-token-clones.py": "token-clone-results.json",
    "detect-ast-similarity.py": "ast-similarity-results.json",
    "detect-metric-similarity.py": "metric-similarity-results.json",
    "detect-tfidf-index.py": "tfidf-index-results.json",
    "detect-winnowing.py": "winnowing-results.json",
    "detect-lsh-ast.py": "lsh-ast-results.json",
    "detect-bag-of-ast.py": "bag-of-ast-results.json",
    "detect-pdg-semantic.py": "pdg-semantic-results.json",
    "detect-code-embedding.py": "code-embedding-results.json",
}
ALL_DETECTORS = list(DETECTOR_OUTPUT_MAP.keys())


def test_detector_schema_is_valid_jsonschema(detector_schema):
    """The detector schema itself must be a valid JSON Schema document."""
    jsonschema.Draft202012Validator.check_schema(detector_schema)


def test_merge_schema_is_valid_jsonschema(merge_schema):
    """The merge schema itself must be a valid JSON Schema document."""
    jsonschema.Draft202012Validator.check_schema(merge_schema)


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_detector_output_validates_against_schema(
    detector, adversarial_catalog, detector_schema, tmp_path
):
    """Each detector's output must conform to the detector schema."""
    script = os.path.join(SCRIPTS, detector)
    if not os.path.exists(script):
        pytest.skip(f"{detector} not found")

    out_path = tmp_path / f"{detector}.json"
    result = subprocess.run(
        [PYTHON, script, adversarial_catalog, "-o", str(out_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"{detector} failed: {result.stderr[-500:]}"
    )
    assert out_path.exists(), f"{detector} produced no output"

    with open(out_path) as f:
        data = json.load(f)

    # Validate — will raise ValidationError on drift
    try:
        jsonschema.validate(instance=data, schema=detector_schema)
    except jsonschema.ValidationError as e:
        pytest.fail(
            f"{detector} output does not match schema:\n"
            f"  path: {list(e.absolute_path)}\n"
            f"  message: {e.message}\n"
            f"  instance: {str(e.instance)[:200]}"
        )


def test_merge_output_validates_against_schema(
    adversarial_catalog, detector_schema, merge_schema, tmp_path
):
    """The merged pipeline output must conform to the merge schema."""
    # Run all detectors first
    detect_dir = tmp_path / "detect"
    detect_dir.mkdir()
    for detector, out_name in DETECTOR_OUTPUT_MAP.items():
        script = os.path.join(SCRIPTS, detector)
        if not os.path.exists(script):
            continue
        subprocess.run(
            [PYTHON, script, adversarial_catalog, "-o", str(detect_dir / out_name)],
            capture_output=True, text=True, timeout=30,
        )

    # Run merge-signals
    merge_script = os.path.join(SCRIPTS, "merge-signals.py")
    merged_out = tmp_path / "merged.json"
    result = subprocess.run(
        [PYTHON, merge_script, str(detect_dir), "-o", str(merged_out), "--include-summary"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"merge-signals failed: {result.stderr[-500:]}"

    with open(merged_out) as f:
        data = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=merge_schema)
    except jsonschema.ValidationError as e:
        pytest.fail(
            f"merge-signals output does not match schema:\n"
            f"  path: {list(e.absolute_path)}\n"
            f"  message: {e.message}\n"
            f"  instance: {str(e.instance)[:200]}"
        )


def test_checked_in_baseline_validates_against_schema(merge_schema):
    """The committed output/merge baseline must conform to the schema.

    Catches silent schema drift in the checked-in sample.
    """
    baseline = os.path.join(BASE, "output", "merge", "merged-results.json")
    if not os.path.exists(baseline):
        pytest.skip("no checked-in baseline")

    with open(baseline) as f:
        data = json.load(f)

    jsonschema.validate(instance=data, schema=merge_schema)


@pytest.mark.parametrize("detector", ALL_DETECTORS)
def test_checked_in_detector_outputs_validate(detector, detector_schema):
    """Every committed per-detector output must conform to the detector schema."""
    name = DETECTOR_OUTPUT_MAP[detector]
    path = os.path.join(BASE, "output", "detect", name)
    if not os.path.exists(path):
        pytest.skip(f"no checked-in {name}")

    with open(path) as f:
        data = json.load(f)

    jsonschema.validate(instance=data, schema=detector_schema)
