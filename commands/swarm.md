---
name: swarm
description: "Launch a guppy swarm at a problem — decompose, dispatch haiku micro-agents in parallel, synthesize findings"
arguments:
  - name: problem
    description: "The problem to swarm (e.g., 'which storage functions are missing soft-delete filters?')"
    required: true
---

Launch a guppy swarm using the `sdlc-os:sdlc-swarm` skill.

1. Decompose the problem into independent micro-directives
2. Dispatch haiku guppies in parallel — one per directive
3. Harvest and synthesize findings
4. Re-swarm on gaps if needed (max 3 waves)
5. Report consolidated results
