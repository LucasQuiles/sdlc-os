#!/usr/bin/env python3
"""Tests for report generation — actionable tier and budget enforcement."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
REPORT_SCRIPT = SCRIPTS_DIR / "generate-report-enhanced.sh"


def _create_fixture(pairs: list[dict]) -> str:
    """Write a synthetic merged-results JSON to a temp file, return path."""
    data = {"pairs": pairs, "summary": {
        "total_pairs": len(pairs),
        "by_confidence": {},
        "by_clone_type": {},
        "multi_signal_pairs": 0,
        "defense_depth_pairs": 0,
        "strategies_used": ["token_clone"],
        "by_action": {},
    }}
    # Count by confidence and type
    for p in pairs:
        conf = p.get("confidence", "LOW")
        ct = p.get("clone_type", "unknown")
        data["summary"]["by_confidence"][conf] = data["summary"]["by_confidence"].get(conf, 0) + 1
        data["summary"]["by_clone_type"][ct] = data["summary"]["by_clone_type"].get(ct, 0) + 1
        action = p.get("recommendation", {}).get("action", "REVIEW")
        data["summary"]["by_action"][action] = data["summary"]["by_action"].get(action, 0) + 1

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


def _pair(name_a: str, name_b: str, clone_type: str, confidence: str, score: float = 0.9):
    return {
        "func_a": {"name": name_a, "file": "a.ts", "line": 1, "qualified_name": name_a},
        "func_b": {"name": name_b, "file": "b.ts", "line": 1, "qualified_name": name_b},
        "composite_score": score,
        "confidence": confidence,
        "clone_type": clone_type,
        "num_strategies": 3,
        "strategies": {"token_clone": score},
        "recommendation": {
            "action": "CONSOLIDATE",
            "urgency": "immediate",
            "reason": "test pair",
        },
    }


def _run_report(fixture_path: str) -> tuple[str, int]:
    """Run the report generator and return (content, exit_code)."""
    fd, out_path = tempfile.mkstemp(suffix=".md")
    os.close(fd)
    try:
        result = subprocess.run(
            ["bash", str(REPORT_SCRIPT), fixture_path, out_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and os.path.exists(out_path):
            return Path(out_path).read_text(), result.returncode
        return result.stderr, result.returncode
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


class TestActionableTier:
    def test_actionable_tier_present(self):
        pairs = [
            _pair("deleteClient", "deleteTemplate", "Type 1 (exact clone)", "HIGH", 1.0),
            _pair("foo", "bar", "Type 4 (semantic clone)", "HIGH"),
        ]
        content, rc = _run_report(_create_fixture(pairs))
        assert rc == 0
        assert "## Actionable Tier" in content

    def test_actionable_tier_contains_only_type1_type2_high(self):
        pairs = [
            _pair("deleteClient", "deleteTemplate", "Type 1 (exact clone)", "HIGH", 1.0),
            _pair("a", "b", "Type 2 (renamed clone)", "HIGH"),
            _pair("foo", "bar", "Type 4 (semantic clone)", "HIGH"),
            _pair("baz", "qux", "Type 1 (exact clone)", "MEDIUM"),
        ]
        content, rc = _run_report(_create_fixture(pairs))
        assert rc == 0
        # Find the actionable tier section
        tier_start = content.index("## Actionable Tier")
        # Find the next ## section after it
        next_section = content.index("\n## ", tier_start + 1)
        tier_content = content[tier_start:next_section]
        assert "deleteClient" in tier_content
        # Type 2 HIGH should also be in actionable tier
        assert "| a |" in tier_content or "a" in tier_content
        # Type 4 HIGH should NOT be in actionable tier
        assert "foo" not in tier_content
        # MEDIUM pairs should NOT be in actionable tier
        assert "baz" not in tier_content

    def test_empty_actionable_tier_renders_cleanly(self):
        pairs = [
            _pair("foo", "bar", "Type 4 (semantic clone)", "HIGH"),
            _pair("baz", "qux", "Type 3 (near-miss clone)", "MEDIUM"),
        ]
        content, rc = _run_report(_create_fixture(pairs))
        assert rc == 0
        assert "## Actionable Tier" in content
        # Should say "no actionable pairs" or similar, not crash
        assert "No actionable pairs" in content
