from __future__ import annotations

import json
from pathlib import Path


def latest_run(root: str | Path) -> Path:
    root = Path(root)
    pointer = json.loads((root / "latest-complete.json").read_text())
    assert pointer["schema_version"] == 1
    path = root / pointer["relative_path"]
    assert path.is_dir()
    return path


def only_attempt(root: str | Path) -> Path:
    root = Path(root)
    candidates = list((root / ".inflight").glob("*")) + list((root / "runs").glob("*"))
    assert len(candidates) == 1, candidates
    return candidates[0]
