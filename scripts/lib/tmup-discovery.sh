#!/bin/bash

discover_tmup_entry() {
  local plugin_root="${1:?discover_tmup_entry: tmup plugin root required}"
  local python_bin="${PYTHON_BIN:-python3.12}"

  "$python_bin" - "$plugin_root" <<'PY'
import json
import sys
from pathlib import Path

try:
    plugin_root = Path(sys.argv[1]).resolve(strict=True)
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    with manifest_path.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    args = manifest["mcpServers"]["tmup"]["args"]
except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
    raise SystemExit(1)

if not isinstance(args, list):
    raise SystemExit(1)

prefix = "${CLAUDE_PLUGIN_ROOT}/"
for argument in args:
    if not isinstance(argument, str) or not argument.startswith(prefix):
        continue
    try:
        entry = (plugin_root / argument[len(prefix) :]).resolve(strict=True)
        entry.relative_to(plugin_root)
    except (OSError, ValueError):
        continue
    if entry.is_file() and entry.suffix == ".js":
        print(entry)
        raise SystemExit(0)

raise SystemExit(1)
PY
}
