---
name: normalize
description: "Assess current project state, produce convention map if missing, generate alignment directives for mid-stream pickup or convention refresh"
arguments: []
---

Run normalization using the `sdlc-os:sdlc-normalize` skill.

1. Dispatch normalizer agent to detect project state (clean / resume / unstructured changes)
2. If Convention Map missing, dispatch convention-scanner to produce one
3. Assess all changes against Convention Map + code-constitution
4. Produce normalization directives with specific file renames, moves, and pattern fixes
5. Present directives to user for approval before execution
6. If full normalization, dispatch gap-analyst in Finder mode on existing work
