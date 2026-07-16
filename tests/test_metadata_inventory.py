from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
METADATA_CHECKER = REPOSITORY_ROOT / "scripts" / "check-plugin-metadata.py"
INVENTORY_CHECKER = REPOSITORY_ROOT / "scripts" / "check-repository-inventory.py"


class MetadataInventoryTests(unittest.TestCase):
    def run_checker(
        self, checker: Path, root: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(checker), "--root", str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def make_metadata_fixture(self, parent: Path) -> Path:
        root = parent / "metadata"
        shutil.copytree(REPOSITORY_ROOT / ".claude-plugin", root / ".claude-plugin")
        marketplace_path = root / ".claude-plugin" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        marketplace["description"] = "Local marketplace for SDLC-OS plugin development"
        for plugin in marketplace["plugins"]:
            if plugin.get("name") == "sdlc-os":
                plugin.pop("version", None)
        marketplace_path.write_text(
            json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return root

    def make_inventory_fixture(self, parent: Path) -> Path:
        root = parent / "inventory"
        shutil.copytree(REPOSITORY_ROOT / "agents", root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
        (root / ".claude").mkdir(parents=True)
        shutil.copy2(
            REPOSITORY_ROOT / ".claude" / "CLAUDE.md",
            root / ".claude" / "CLAUDE.md",
        )
        shutil.copy2(REPOSITORY_ROOT / "README.md", root / "README.md")

        claude_path = root / ".claude" / "CLAUDE.md"
        claude_text = claude_path.read_text(encoding="utf-8")
        claude_text = re.sub(
            r"Claude Code plugin: \d+ skills, \d+ agents",
            "Claude Code plugin: 16 skills, 46 agents",
            claude_text,
            count=1,
        )
        claude_text = re.sub(
            r"^(\s*skills/\s+—\s+)\d+(\s+SDLC skills)",
            r"\g<1>16\g<2>",
            claude_text,
            count=1,
            flags=re.MULTILINE,
        )
        claude_text = re.sub(
            r"^(\s*agents/\s+—\s+)\d+(\s+agent prompts)",
            r"\g<1>46\g<2>",
            claude_text,
            count=1,
            flags=re.MULTILINE,
        )
        claude_path.write_text(claude_text, encoding="utf-8")

        readme_path = root / "README.md"
        readme_text = readme_path.read_text(encoding="utf-8")
        readme_text = re.sub(
            r"^### (?:Agents|Core-Agent Subset) \(\d+\)$",
            "### Core-Agent Subset (29)",
            readme_text,
            count=1,
            flags=re.MULTILINE,
        )
        projection = (
            "The repository contains 46 agent files and 16 skill directories; "
            "runtime composition is reported separately because it may include "
            "non-repository skills."
        )
        if projection not in readme_text:
            readme_text = readme_text.replace(
                "### Core-Agent Subset (29)\n",
                f"### Core-Agent Subset (29)\n\n{projection}\n",
                1,
            )
        readme_path.write_text(readme_text, encoding="utf-8")
        return root

    def test_current_repository_contract(self) -> None:
        metadata = self.run_checker(METADATA_CHECKER, REPOSITORY_ROOT)
        self.assertEqual(metadata.returncode, 0, metadata.stderr)
        self.assertEqual(
            json.loads(metadata.stdout),
            {
                "marketplace_version_authority": "plugin_manifest",
                "plugin_version": "10.0.0",
            },
        )

        inventory = self.run_checker(INVENTORY_CHECKER, REPOSITORY_ROOT)
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        self.assertEqual(
            json.loads(inventory.stdout),
            {
                "readme_core_agents": 29,
                "repository_agents": 46,
                "repository_skills": 16,
            },
        )

    def test_current_bytes_project_the_approved_inventory(self) -> None:
        marketplace = json.loads(
            (REPOSITORY_ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        matching = [
            plugin
            for plugin in marketplace["plugins"]
            if plugin.get("name") == "sdlc-os"
        ]
        with self.subTest("marketplace description"):
            self.assertTrue(marketplace.get("description"))
        with self.subTest("sole version authority"):
            self.assertNotIn("version", matching[0])

        claude_text = (REPOSITORY_ROOT / ".claude" / "CLAUDE.md").read_text(
            encoding="utf-8"
        )
        with self.subTest("repository totals"):
            self.assertIn("Claude Code plugin: 16 skills, 46 agents", claude_text)

        readme_text = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        with self.subTest("README subset heading"):
            self.assertIn("### Core-Agent Subset (29)", readme_text)
        with self.subTest("README runtime distinction"):
            self.assertIn("runtime composition is reported separately", readme_text)

    def test_missing_marketplace_description_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_metadata_fixture(Path(temp_dir))
            path = root / ".claude-plugin" / "marketplace.json"
            marketplace = json.loads(path.read_text(encoding="utf-8"))
            del marketplace["description"]
            path.write_text(json.dumps(marketplace) + "\n", encoding="utf-8")

            result = self.run_checker(METADATA_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("PLUGIN_METADATA_DRIFT", result.stderr)
            self.assertIn("description", result.stderr)

    def test_duplicate_marketplace_version_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_metadata_fixture(Path(temp_dir))
            path = root / ".claude-plugin" / "marketplace.json"
            marketplace = json.loads(path.read_text(encoding="utf-8"))
            marketplace["plugins"][0]["version"] = "4.0.0"
            path.write_text(json.dumps(marketplace) + "\n", encoding="utf-8")

            result = self.run_checker(METADATA_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("PLUGIN_METADATA_DRIFT", result.stderr)
            self.assertIn("version", result.stderr)

    def test_invalid_plugin_semantic_version_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_metadata_fixture(Path(temp_dir))
            path = root / ".claude-plugin" / "plugin.json"
            plugin = json.loads(path.read_text(encoding="utf-8"))
            plugin["version"] = "release-ten"
            path.write_text(json.dumps(plugin) + "\n", encoding="utf-8")

            result = self.run_checker(METADATA_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("PLUGIN_METADATA_DRIFT", result.stderr)
            self.assertIn("semantic version", result.stderr)

    def test_removed_agent_fails_inventory_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_inventory_fixture(Path(temp_dir))
            next((root / "agents").glob("*.md")).unlink()

            result = self.run_checker(INVENTORY_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("INVENTORY_DRIFT", result.stderr)
            self.assertIn("45", result.stderr)
            self.assertIn("46", result.stderr)

    def test_stale_claude_projection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_inventory_fixture(Path(temp_dir))
            path = root / ".claude" / "CLAUDE.md"
            text = path.read_text(encoding="utf-8").replace(
                "Claude Code plugin: 16 skills, 46 agents",
                "Claude Code plugin: 16 skills, 45 agents",
                1,
            )
            path.write_text(text, encoding="utf-8")

            result = self.run_checker(INVENTORY_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("INVENTORY_DRIFT", result.stderr)
            self.assertIn("45", result.stderr)
            self.assertIn("46", result.stderr)

    def test_readme_installed_total_label_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.make_inventory_fixture(Path(temp_dir))
            path = root / "README.md"
            text = path.read_text(encoding="utf-8").replace(
                "### Core-Agent Subset (29)", "### Agents (29)", 1
            )
            path.write_text(text, encoding="utf-8")

            result = self.run_checker(INVENTORY_CHECKER, root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("INVENTORY_DRIFT", result.stderr)
            self.assertIn("core-agent subset", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
