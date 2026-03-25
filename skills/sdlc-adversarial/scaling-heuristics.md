# AQS Scaling Heuristics

Rules for when to activate AQS, which domains to select, how to allocate guppy budget, and when to abort. Applied by the Conductor during Phase 1.

---

## Complexity Assessment

Map each bead to a complexity tier before activating any domains. The tier determines the overall AQS behavior.

| Tier | AQS Behavior | Rationale |
|---|---|---|
| **Trivial** | Skip entirely — bead goes `proven → merged` directly | Cost of AQS exceeds value for minimal-risk changes. Oracle coverage is sufficient. |
| **Moderate** | Recon burst fires (all 8 guppies). Conductor selects 1–2 most relevant domains. Only HIGH/MED priority domains get directed strike. | Right-sized investment. Catches the most likely failure mode without full engagement. |
| **Complex** | All four domains active. Full directed strike on HIGH/MED. Light sweep on LOW. Cycle 2 mandatory if Cycle 1 produced accepted or sustained fixes. | High change surface justifies full adversarial coverage. |
| **Security-sensitive** | All four domains active regardless of file count or complexity. Security domain always HIGH. Cycle 2 mandatory. | Security failures compound — incomplete hardening is worse than no hardening because it creates false confidence. |

Security-sensitive overrides all other tier assessments. A 1-line change that touches auth is security-sensitive. A 50-file refactor that touches only internal types is Moderate.

---

## Complexity Signals

Use these signals to assign the complexity tier. Check top-down — security-sensitive signals override everything else.

### Trivial signals (ALL must be true — one exception lifts the tier)
- Single file changed
- Fewer than 50 lines changed
- No new I/O operations introduced (no new database calls, HTTP calls, file reads/writes)
- Internal refactor only — no changes to public API or exported interface
- Documentation-only changes (comments, README, docstrings with no behavioral impact)

### Moderate signals (any one is sufficient)
- 2–5 files changed
- New function or module introduced that is not externally exposed
- New error handling paths added to existing code
- New API endpoint or function exported for use by other modules

### Complex signals (any one is sufficient)
- 5 or more files changed
- New external integration introduced (new HTTP client, new database, new third-party service)
- Changes to authentication or authorization logic
- Changes to data model (new tables, new schema fields, new serialization format)
- New asynchronous patterns introduced (new queues, new event emitters, new background jobs)

### Security-sensitive overrides (any one forces security-sensitive tier regardless of file count)
- Any user-supplied input reaches a new code path (new route, new parameter, new field)
- Changes to authentication logic (login, token validation, session management)
- Changes to authorization logic (permission checks, role validation, ownership checks)
- New credential handling (storing, transmitting, or validating passwords, API keys, tokens)
- New data exposure paths (new API response fields, new log statements touching sensitive data)
- New filesystem or command execution operations
- New cross-origin request handling (CORS configuration, postMessage handlers)

---

## Domain Selection Heuristics

The Conductor applies these heuristics to assign preliminary domain priority before recon results are available. Recon results may override the Conductor's judgment in either direction.

### Functionality
**Activate when:**
- Bead implements business logic (calculations, state transitions, workflow steps)
- Bead changes the behavior of an existing function (not just its implementation)
- Bead introduces new conditional paths (new if/else, new switch cases, new state branches)
- Bead changes how data is transformed, validated, or processed

**Do not activate when:**
- Bead is infrastructure-only (logging, monitoring, config) with no business logic
- Bead is documentation or comment-only

### Security
**Activate when:**
- Bead touches any external input path (user input, API parameters, file uploads)
- Bead changes authentication or authorization logic
- Bead introduces new data persistence or retrieval
- Bead adds or modifies API endpoints or public interfaces
- Security-sensitive override was triggered (always active)

**Do not activate when:**
- Bead is internal-only refactor with no change to input handling or data access

### Usability
**Activate when:**
- Bead creates or modifies a user-facing interface (UI component, API contract, CLI)
- Bead changes error messages, response shapes, or status codes
- Bead introduces a new public API (function signatures, method names, parameter names)
- Bead changes developer-facing documentation, types, or interfaces

**Do not activate when:**
- Bead has no user-facing or developer-facing interface changes (pure internal logic)

### Resilience
**Activate when:**
- Bead touches error handling code (try/catch, error callbacks, error middleware)
- Bead introduces new I/O operations (database, HTTP, filesystem, queue)
- Bead changes retry logic, timeout configuration, or circuit breaker settings
- Bead adds new external service dependencies
- Bead changes resource lifecycle management (connection pools, file handles, event listeners)

**Do not activate when:**
- Bead has no I/O operations and no error handling changes

### Multi-Domain Activation Patterns

Common bead types and their expected domain activation:

| Bead Type | Functionality | Security | Usability | Resilience |
|---|---|---|---|---|
| New REST endpoint | HIGH | HIGH | HIGH | MED |
| Auth change | MED | HIGH | LOW | LOW |
| Database schema + query changes | HIGH | HIGH | LOW | HIGH |
| UI component | MED | LOW | HIGH | LOW |
| Background job / worker | HIGH | LOW | LOW | HIGH |
| Internal refactor (no API change) | HIGH | LOW | LOW | LOW |
| Config / infrastructure change | LOW | MED | LOW | MED |
| Third-party integration | MED | HIGH | MED | HIGH |
| Error handling improvement | LOW | LOW | MED | HIGH |

These are starting points, not rules. Recon signals and bead content override the pattern.

---

## Budget Management

### Guppy Budget by Priority

| Domain Priority | Strike Guppies | Notes |
|---|---|---|
| **HIGH** | 20–40 | Full attack across all applicable attack vectors in the domain library |
| **MED** | 10–20 | Focused on the specific signals raised by recon |
| **LOW** | 5–10 | Light sweep; close immediately if clean |
| **SKIP** | 0 | No strike |

### Arbiter Budget

**Maximum 3 arbiter invocations per bead.** If more than 3 findings reach `disputed` status, halt and recalibrate the red/blue pair before proceeding. See `arbitration-protocol.md` for the recalibration trigger.

Each arbiter invocation uses Opus. Budget accordingly — Opus invocations are expensive. The Conductor should note if a bead is consuming disproportionate arbiter budget and flag it.

### Cycle Budget

**Maximum 2 full cycles per bead.**

- Cycle 1 always runs when AQS is active.
- Cycle 2 runs only if Cycle 1 produced at least one accepted or arbiter-sustained fix (i.e., code was changed). Re-attacks the hardened code to verify fixes hold and no new attack surface was introduced.
- If Cycle 1 produces no findings (all domains clean), AQS completes immediately without Cycle 2.
- After 2 cycles, any unresolved findings are escalated to the Conductor with the adversarial report. The bead is marked `DEFERRED` or `PARTIALLY_HARDENED`.

---

## Cross-Reference Decision Matrix

Applied after Phase 1 (Conductor selection + recon burst) completes. Determines final strike priority per domain.

```
for each domain in [functionality, security, usability, resilience]:

  conductor_selected = Conductor marked this domain as relevant
  recon_signal       = At least one recon guppy for this domain returned SIGNAL

  if conductor_selected AND recon_signal:
    priority = HIGH          # Both agree: most important — full strike
    strike_volume = 20-40 guppies

  elif (NOT conductor_selected) AND recon_signal:
    priority = MED           # Recon surfaced a blind spot — Conductor reconsiders
    strike_volume = 10-20 guppies
    note: "Recon overrode Conductor — review why this was missed in Phase 1"

  elif conductor_selected AND (NOT recon_signal):
    priority = LOW           # Conductor intuition not confirmed by recon — light sweep
    strike_volume = 5-10 guppies
    note: "If strike finds nothing, close domain as clean"

  elif (NOT conductor_selected) AND (NOT recon_signal):
    priority = SKIP
    strike_volume = 0
```

The `recon-only = MED` case is the most important. It catches Conductor blind spots. The Conductor must document why recon found a signal the Conductor missed — this is calibration feedback.

---

## When to Abort AQS

Stop the AQS cycle and close the domain or the entire engagement under these conditions:

**Domain-level abort:**
- The domain produced 0 guppy hits after a full strike (all guppies returned MISS or NO_SIGNAL). Close the domain as clean. Do not fire Cycle 2 for this domain.
- The domain is LOW priority and the light sweep produced 0 hits. Close immediately without escalating to full strike.

**Engagement-level abort:**
- **All-domain NO_SIGNAL confirmed:** All 8 recon guppies returned NO_SIGNAL and the Conductor independently assessed all domains as SKIP. AQS completes immediately without any strike. This is a valid and expected outcome for well-constructed beads.
- **Blocked by external dependencies:** The bead's code cannot be meaningfully analyzed without access to a running environment, production data, or external services that are not available. Document what was blocked and why, then close with `DEFERRED`.
- **Already human-reviewed:** The bead has already undergone a live security review, penetration test, or formal audit covering the same scope within the current sprint. AQS would be redundant. Document the existing review and close with `HARDENED` (crediting the external review). This requires Conductor verification — do not self-certify.

**Do not abort for:**
- Time pressure (AQS budget is fixed; if it is too expensive, adjust complexity tier thresholds, not individual engagements)
- Low confidence in findings (low-confidence findings should be downgraded to Assumed, not dropped)
- Red team frustration with blue team responses (that is what the Arbiter is for)
