---
name: audit
description: "Run architectural fitness checks — detect DRY violations, pattern drift, boundary violations, and missing tests"
arguments:
  - name: scope
    description: "full | changed | <file path> — what to audit (default: changed files since last commit)"
    required: false
---

Run fitness checks using the `sdlc-os:sdlc-fitness` skill.

1. Determine scope (changed files, full codebase, or specific path)
2. Dispatch reuse-scout + drift-detector with the scope
3. Swarm guppies for breadth checks across fitness dimensions
4. Aggregate into fitness report with scores per dimension
5. Flag BLOCKING issues that need immediate attention
