---
name: refactor
description: "Refactor existing code — preserve behavior, improve structure, continuous equivalence proof"
arguments:
  - name: scope
    description: "What to refactor — file path, pattern, or description"
    required: true
---

Enter refactor mode using the `sdlc-os:sdlc-refactor` skill.

1. Establish baseline (run tests, record pass/fail counts)
2. Characterize existing code via LSP (callers, callees, types, consumers)
3. Plan atomic transformation steps (extract → redirect → delete)
4. Execute with continuous proof (tsc + tests after every step)
5. Verify equivalence (Oracle compares final state to baseline)
