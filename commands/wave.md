---
name: wave
description: "SDLC phase operations — check status, advance, or recover"
arguments:
  - name: action
    description: "status | health | recover [bead-id]"
    required: true
---

Operations on the active SDLC workflow:

- `status` — Show current phase, bead progress, sentinel alerts (uses `sdlc-os:sdlc-status`)
- `health` — Run lightweight health check on current phase (uses `sdlc-os:sdlc-gate`)
- `recover {bead-id}` — Re-dispatch a stuck or failed bead with fresh context
