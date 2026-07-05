#!/bin/bash
# test-agent-frontmatter.sh — deterministic gate over agents/*.md frontmatter
# and skill-heading references.
#
# Origin: estate wave-7 remediation (2026-07-05). This gate exists because
# 2026-07-05 commit 4278ef0 shipped four YAML-invalid agent frontmatters
# (unquoted ': ' in descriptions) that nothing asserted.
#
# Overrides (for scratch red-green; defaults = live repo):
#   SDLC_OS_ROOT  — repo root (default: parent of this script's dir)
#   AGENTS_DIR    — agents dir (default: $SDLC_OS_ROOT/agents)
#   SKILLS_DIR    — skills dir (default: $SDLC_OS_ROOT/skills)
#   PYBIN         — python with PyYAML (default: /opt/homebrew/opt/python@3.12/bin/python3.12;
#                   bare python3 is PATH-dependent and lacks yaml under launchd — see
#                   wave-7 baseline/dependency-probes.txt)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDLC_OS_ROOT="${SDLC_OS_ROOT:-$(dirname "$SCRIPT_DIR")}"
AGENTS_DIR="${AGENTS_DIR:-$SDLC_OS_ROOT/agents}"
SKILLS_DIR="${SKILLS_DIR:-$SDLC_OS_ROOT/skills}"
PYBIN="${PYBIN:-/opt/homebrew/opt/python@3.12/bin/python3.12}"

PASS=0
FAIL=0

if [ ! -x "$PYBIN" ]; then
  echo "FAIL  E-TOOLING: PYBIN not executable: $PYBIN"
  echo "AGENT-FRONTMATTER-GATE SUMMARY: PASS=0 FAIL=1 (tooling)"
  exit 1
fi
if ! "$PYBIN" -c "import yaml" 2>/dev/null; then
  echo "FAIL  E-TOOLING: $PYBIN cannot import yaml"
  echo "AGENT-FRONTMATTER-GATE SUMMARY: PASS=0 FAIL=1 (tooling)"
  exit 1
fi
if [ ! -d "$AGENTS_DIR" ]; then
  echo "FAIL  E-CONTRACT: AGENTS_DIR missing: $AGENTS_DIR"
  echo "AGENT-FRONTMATTER-GATE SUMMARY: PASS=0 FAIL=1 (contract)"
  exit 1
fi

# The python part emits one line per check: "PASS <check>" or "FAIL <check>: detail".
# NOTE: output goes through a temp file, NOT $(...) capture — a heredoc inside
# command substitution fails to parse under Apple bash 3.2.57, which is what
# launchd's minimal PATH resolves (proven by the wave-7 supervised fire).
RESULT_FILE="$(mktemp /tmp/agent-frontmatter-gate.XXXXXX)"
trap 'rm -f "$RESULT_FILE"' EXIT
"$PYBIN" - "$AGENTS_DIR" "$SKILLS_DIR" > "$RESULT_FILE" <<'PYEOF'
import pathlib, re, sys
import yaml

agents_dir = pathlib.Path(sys.argv[1])
skills_dir = pathlib.Path(sys.argv[2])

# Live MCP prefixes on this estate (source: wave-7 baseline dependency probes +
# session tool inventory 2026-07-05). Non-MCP tool names are free-form strings.
LIVE_MCP_PREFIXES = (
    "mcp__plugin_pinecone_pinecone__",
    "mcp__plugin_episodic-memory_episodic-memory__",
    "mcp__plugin_microsoft_365_microsoft_365__",
    "mcp__plugin_tmup_tmup__",
    "mcp__plugin_superpowers-chrome_chrome__",
    "mcp__email__",
    "mcp__claude_ai_",
    "mcp__playwright__",  # user+project scope registration 2026-07-05 (wave-5)
)
# Declared compatibility exceptions: prefix -> justifying artifact.
# A new entry REQUIRES an artifact reference (E-TOOLING otherwise).
DECLARED_COMPAT = {
    # none for sdlc-os agents as of 2026-07-05 (tmup dual-prefix compat is a
    # tmup-repo concern, asserted by tmup's own system-inventory-parity test)
}

# Skill-heading references that must exist verbatim (heading, target file,
# referencing surfaces). Source: wave-6 review — wave-definitions.md and
# .claude/CLAUDE.md point at SKILL.md's "How to Dispatch Runners".
HEADING_REFS = [
    ("How to Dispatch Runners", "sdlc-orchestrate/SKILL.md",
     ["sdlc-orchestrate/wave-definitions.md"]),
]

failures = []
passes = []

files = sorted(agents_dir.glob("*.md"))
if not files:
    failures.append(f"no-agents: {agents_dir} contains no *.md")

for f in files:
    text = f.read_text(errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        failures.append(f"frontmatter parse: {f.name}: no frontmatter fence")
        continue
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        failures.append(f"frontmatter parse: {f.name}: {str(e).splitlines()[0]}")
        continue
    if not isinstance(fm, dict):
        failures.append(f"frontmatter parse: {f.name}: not a mapping")
        continue
    name = fm.get("name")
    if name != f.stem:
        failures.append(f"name mismatch: {f.name}: name={name!r} != stem={f.stem!r}")
        continue
    desc = fm.get("description")
    if not isinstance(desc, str):
        failures.append(f"description type: {f.name}: {type(desc).__name__}")
        continue
    if desc.rstrip().endswith("…"):
        failures.append(f"description ellipsis: {f.name}")
        continue
    if len(desc) > 165:
        failures.append(f"description length: {f.name}: {len(desc)} > 165")
        continue
    tools_raw = fm.get("tools")
    if tools_raw is not None:
        if isinstance(tools_raw, str):
            tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
        elif isinstance(tools_raw, list):
            tools = []
            ok = True
            for t in tools_raw:
                if not isinstance(t, str):
                    failures.append(f"tools entry type: {f.name}: {t!r}")
                    ok = False
                    break
                tools.append(t.strip())
            if not ok:
                continue
        else:
            failures.append(f"tools type: {f.name}: {type(tools_raw).__name__}")
            continue
        bad = None
        for t in tools:
            if t.startswith("mcp__"):
                if not (t.startswith(LIVE_MCP_PREFIXES) or
                        any(t.startswith(p) for p in DECLARED_COMPAT)):
                    bad = t
                    break
        if bad:
            failures.append(f"unknown tool: {f.name}: {bad}")
            continue
    passes.append(f.name)

print(f"PASS agents-clean-count {len(passes)}")

for heading, target_rel, referencers in HEADING_REFS:
    target = skills_dir / target_rel
    if not target.exists():
        failures.append(f"heading not found: target missing: {target_rel}")
        continue
    if not re.search(rf"^#+\s+{re.escape(heading)}\s*$", target.read_text(errors='replace'), re.M):
        failures.append(f"heading not found: '{heading}' not a heading in {target_rel}")
        continue
    for ref_rel in referencers:
        ref = skills_dir / ref_rel
        if ref.exists() and heading not in ref.read_text(errors="replace"):
            # referencing surface no longer mentions it: not a failure, note only
            print(f"PASS heading-ref-note {ref_rel} no longer references '{heading}'")
    print(f"PASS heading '{heading}' in {target_rel}")

for fail in failures:
    print(f"FAIL {fail}")
PYEOF

while IFS= read -r line; do
  case "$line" in
    PASS*) PASS=$((PASS+1)); echo "$line" ;;
    FAIL*) FAIL=$((FAIL+1)); echo "$line" ;;
    *) echo "$line" ;;
  esac
done < "$RESULT_FILE"

echo "AGENT-FRONTMATTER-GATE SUMMARY: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
