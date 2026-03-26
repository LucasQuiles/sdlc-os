# SDLC Task: v3-research-upgrade-20260325

**Status:** active
**Phase:** execute
**Cynefin domain:** complicated
**Created:** 2026-03-25

## Mission Brief

Implement 14 research-driven concepts into the SDLC OS plugin across 5 parallel streams. All changes are markdown prompt engineering edits to files under `/Users/q/.claude/plugins/sdlc-os/`.

**Objective:** Reduce bugs, reduce drift, reduce human supervision, improve production readiness.

**Source plan:** `docs/plans/2026-03-25-v3-research-upgrade.md`

**Success criteria:**
- All 19 files modified/created per plan
- No cross-reference inconsistencies
- All new content integrates cleanly with existing content
- 5 stream commits + 1 final verification commit

## Beads

| ID | Stream | Type | Status | Files |
|----|--------|------|--------|-------|
| stream-a | Adversarial cycle | implement | pending | `sdlc-adversarial/SKILL.md`, `adversarial-quality.md` |
| stream-b | Arbiter + precedent | implement | pending | `arbitration-protocol.md`, `arbiter.md`, NEW `precedent-system.md` |
| stream-c | Agent prompts | implement | pending | 4x `red-*.md`, 4x `blue-*.md` |
| stream-d | Classification + orchestration | implement | pending | `scaling-heuristics.md`, `sdlc-orchestrate/SKILL.md`, NEW `quality-slos.md` |
| stream-e | Monitoring + new agents | implement | pending | `sdlc-loop/SKILL.md`, `oracle-adversarial-auditor.md`, NEW 3 files |

## Quality Budget

**Current state:** healthy (first task — baseline)
