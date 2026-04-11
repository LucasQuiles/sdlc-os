# sdlc-os — Multi-Agent SDLC Orchestration Plugin

## What This Is
Claude Code plugin: 15 skills, 45 agents, quality-gated delivery through beads, L0-L5 correction loops, adversarial quality review. Includes the Colony Runtime for persistent multi-agent orchestration.

## Project Layout

    skills/        — 15 SDLC skills (orchestrate, normalize, adversarial, etc.)
    agents/        — 45 agent prompts (sonnet-implementer, oracle-*, red-*, blue-*, etc.)
    colony/        — Colony Runtime (Deacon, Bridge, Clone Manager)
    hooks/         — Event hooks (naming, AQS, bead status, etc.)
    commands/      — Slash commands
    docs/          — Specs, plans, research, SDLC state
    references/    — FFT decision trees, safety constraints, conventions

## Colony Runtime — Hard Rules

### Safety Constraints (19 enforced in code and tested)
- SC-COL-15: Compare-and-swap on bead status — no skipping levels
- SC-COL-22: Output must exist, >100 bytes, contain completion sentinel
- SC-COL-28: Atomic writes via temp+rename — never in-place
- SC-COL-29: git add -- specific-file only — never git add -A
- SC-COL-31: Clone prune requires zero active tasks sharing clone_dir
- SC-COL-35: Watchdog forces RECOVERING if state exceeds max duration
- SC-COL-36: Escalation alerts must not block Deacon main loop
- SC-COL-37: Bridge lock deferral has max count before force-kill

### Never Do
- Never modify bead files in-place — always atomic temp+rename
- Never git add -A in bridge operations
- Never restart the Deacon from agent code — escalate to human
- Never bypass the quality loop (L0-L1-L2-L2.5-L2.75) for any bead
- Never delete a clone_dir without checking bridge_synced AND active task count

### Testing — Required Before Any Commit to colony/

    cd colony && npx tsc --noEmit            # TypeScript: 0 errors
    cd colony && npx vitest run              # 40 tests pass
    cd colony && python3 -m pytest deacon_test.py -q  # 84 tests pass
    cd colony && bash clone-manager.test.sh  # 24 tests pass
    cd colony && bash smoke-test.sh          # 7/7 PASS

All must pass. No exceptions.

### Telemetry — 3 Structured Log Channels
- colony-sessions.log: JSON per Conductor session (cost, bead_ids, wall_clock)
- /tmp/sdlc-colony/colony-bridge.log: JSON per bridge call (action, elapsed_ms, SC-COL hits)
- /tmp/sdlc-colony/clone-events.log: JSON per clone operation (create, verify, prune)
- Dashboard: bash colony/audit-metrics.sh

## Agent Runtime Constraints

7 agents have enriched frontmatter with runtime-enforced fields (Phase 1, 2026-04-10):

| Agent | tools | isolation | memory | effort | background |
|-------|-------|-----------|--------|--------|------------|
| guppy | Read,Grep,Glob,LS | — | — | low | true |
| reuse-scout | Read,Grep,Glob,LS,LSP,Pinecone,episodic-memory | — | — | low | true |
| sonnet-reviewer | Read,Grep,Glob,LS,LSP | — | — | high | — |
| sonnet-designer | Read,Grep,Glob,LS,LSP,Skill | — | — | high | — |
| sonnet-investigator | Read,Grep,Glob,LS,LSP,Skill | — | — | high | true |
| sonnet-implementer | Read,Write,Edit,Grep,Glob,LS,Bash,Skill | worktree | local | — | — |

Key constraints:
- tools: allowlists are enforced at session startup only (not after /reload-plugins)
- Read-only agents cannot Bash, Write, or Edit
- Write-capable agents get worktree isolation and local memory
- Phase 2 (hooks, mcpServers, permissionMode) requires promotion to ~/.claude/agents/

## Development Conventions
- TypeScript: strict mode, vitest, ES2022
- Python: 3.12, type hints, pytest, asyncio
- Bash: set -euo pipefail
- Git: conventional commits (feat:, fix:, test:, docs:, refactor:)

## Key Docs
- colony/README.md — Architecture, usage, operations (520 lines)
- docs/specs/2026-04-03-colony-runtime-design.md — Phase 1 spec (681 lines)
- docs/specs/2026-04-03-colony-phase2-design.md — Phase 2 spec (219 lines)
- docs/sdlc/colony-deferred.md — Deferred items with rationale and re-eval triggers
