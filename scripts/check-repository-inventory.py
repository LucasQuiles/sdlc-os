#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED_CORE_AGENTS = 29
SUMMARY_PATTERN = re.compile(r"Claude Code plugin:\s*(\d+) skills,\s*(\d+) agents")
SKILL_LAYOUT_PATTERN = re.compile(
    r"^\s*skills/\s+—\s+(\d+)\s+SDLC skills", re.MULTILINE
)
AGENT_LAYOUT_PATTERN = re.compile(
    r"^\s*agents/\s+—\s+(\d+)\s+agent prompts", re.MULTILINE
)
CORE_HEADING_PATTERN = re.compile(r"^### Core-Agent Subset \((\d+)\)$", re.MULTILINE)
CATEGORY_PATTERN = re.compile(r"^\*\*[^*]+:\*\*\s+(.+)$", re.MULTILINE)
AGENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


class InventoryError(Exception):
    pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise InventoryError(f"cannot read {path}: {error}") from error


def require_count(pattern: re.Pattern[str], text: str, label: str) -> int:
    match = pattern.search(text)
    if match is None:
        raise InventoryError(f"missing {label} projection")
    return int(match.group(1))


def count_repository(root: Path) -> tuple[int, int]:
    agents_dir = root / "agents"
    skills_dir = root / "skills"
    try:
        agent_count = sum(
            entry.is_file() and not entry.is_symlink()
            for entry in agents_dir.glob("*.md")
        )
        skill_count = sum(
            entry.is_dir()
            and not entry.is_symlink()
            and (entry / "SKILL.md").is_file()
            and not (entry / "SKILL.md").is_symlink()
            for entry in skills_dir.iterdir()
        )
    except OSError as error:
        raise InventoryError(
            f"cannot enumerate repository inventory: {error}"
        ) from error
    return agent_count, skill_count


def parse_readme_core_agents(readme: str) -> tuple[int, list[str]]:
    heading = CORE_HEADING_PATTERN.search(readme)
    if heading is None:
        raise InventoryError("README must label its roster as a core-agent subset")
    section_tail = readme[heading.end() :]
    next_heading = re.search(r"^### ", section_tail, re.MULTILINE)
    section = section_tail[: next_heading.start()] if next_heading else section_tail

    names: list[str] = []
    for match in CATEGORY_PATTERN.finditer(section):
        body = re.sub(r"\s+\([^)]*\)\s*$", "", match.group(1))
        names.extend(name.strip() for name in body.split(",") if name.strip())
    invalid = [name for name in names if not AGENT_NAME_PATTERN.fullmatch(name)]
    if invalid:
        raise InventoryError(f"README contains invalid core-agent names: {invalid}")
    if len(set(names)) != len(names):
        raise InventoryError("README core-agent subset contains duplicate names")
    return int(heading.group(1)), names


def check_inventory(root: Path) -> dict[str, int]:
    repository_agents, repository_skills = count_repository(root)
    claude_text = read_text(root / ".claude" / "CLAUDE.md")
    readme_text = read_text(root / "README.md")

    summary = SUMMARY_PATTERN.search(claude_text)
    if summary is None:
        raise InventoryError("missing CLAUDE.md repository summary projection")
    summary_skills, summary_agents = map(int, summary.groups())
    layout_skills = require_count(
        SKILL_LAYOUT_PATTERN, claude_text, "CLAUDE.md skill-layout"
    )
    layout_agents = require_count(
        AGENT_LAYOUT_PATTERN, claude_text, "CLAUDE.md agent-layout"
    )
    expected = (repository_skills, repository_agents)
    if (summary_skills, summary_agents) != expected:
        raise InventoryError(
            "CLAUDE.md summary projects "
            f"{summary_agents} agents/{summary_skills} skills; repository has "
            f"{repository_agents} agents/{repository_skills} skills"
        )
    if (layout_skills, layout_agents) != expected:
        raise InventoryError(
            "CLAUDE.md layout projects "
            f"{layout_agents} agents/{layout_skills} skills; repository has "
            f"{repository_agents} agents/{repository_skills} skills"
        )

    heading_count, core_agents = parse_readme_core_agents(readme_text)
    if heading_count != len(core_agents) or heading_count != EXPECTED_CORE_AGENTS:
        raise InventoryError(
            "README core-agent subset projects "
            f"{heading_count}, enumerates {len(core_agents)}, and must equal "
            f"{EXPECTED_CORE_AGENTS}"
        )
    projection = (
        f"The repository contains {repository_agents} agent files and "
        f"{repository_skills} skill directories; runtime composition is reported "
        "separately because it may include non-repository skills."
    )
    if projection not in readme_text:
        raise InventoryError(
            "README must distinguish repository inventory from runtime composition"
        )

    return {
        "readme_core_agents": len(core_agents),
        "repository_agents": repository_agents,
        "repository_skills": repository_skills,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate repository agent and skill inventory projections."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise InventoryError(f"repository root is not a directory: {root}")
        result = check_inventory(root)
    except (InventoryError, OSError) as error:
        print(f"INVENTORY_DRIFT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
