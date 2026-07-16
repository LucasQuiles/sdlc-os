#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SEMANTIC_VERSION = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


class MetadataError(Exception):
    pass


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MetadataError(f"cannot read valid JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise MetadataError(f"expected a JSON object in {path}")
    return value


def check_metadata(root: Path) -> dict[str, str]:
    plugin = load_object(root / ".claude-plugin" / "plugin.json")
    marketplace = load_object(root / ".claude-plugin" / "marketplace.json")

    plugin_name = plugin.get("name")
    plugin_version = plugin.get("version")
    if not isinstance(plugin_name, str) or not plugin_name.strip():
        raise MetadataError("plugin manifest name must be a nonempty string")
    if not isinstance(plugin_version, str) or not SEMANTIC_VERSION.fullmatch(
        plugin_version
    ):
        raise MetadataError("plugin manifest version must be a semantic version")

    description = marketplace.get("description")
    if not isinstance(description, str) or not description.strip():
        raise MetadataError("marketplace description must be a nonempty string")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise MetadataError("marketplace plugins must be an array")
    matching = [
        entry
        for entry in plugins
        if isinstance(entry, dict) and entry.get("name") == plugin_name
    ]
    if len(matching) != 1:
        raise MetadataError(
            f"marketplace must contain exactly one plugin named {plugin_name!r}"
        )
    if "version" in matching[0]:
        raise MetadataError(
            "marketplace plugin entry must not declare version; "
            f"plugin manifest {plugin_version} is the sole authority"
        )

    return {
        "marketplace_version_authority": "plugin_manifest",
        "plugin_version": plugin_version,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate SDLC-OS plugin and marketplace metadata authority."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise MetadataError(f"repository root is not a directory: {root}")
        result = check_metadata(root)
    except (MetadataError, OSError) as error:
        print(f"PLUGIN_METADATA_DRIFT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
