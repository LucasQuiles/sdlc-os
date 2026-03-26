# Recon Guppy Directives

Eight complete guppy prompt templates — two per domain — for the Phase 1 recon burst. Each template is copy-paste-ready. The only placeholder is `{bead file list}`.

---

## How to Use

Dispatch all 8 recon guppies in parallel at the start of Phase 1. Use the Agent tool with:

- `subagent_type: general-purpose`
- `model: haiku`
- `mode: auto`
- `name: recon-{domain}-{n}-{bead-id}` (e.g., `recon-functionality-1-bead-042`)

Each guppy produces exactly one output: `SIGNAL: {one-line description}` or `NO_SIGNAL`.

Collect all 8 results and feed them into the Phase 2 cross-reference alongside Conductor's preliminary domain selections.

---

## Functionality Recon

### F1 — Input State Coverage

```
You are a recon probe for the functionality domain.

## Bead Files
{bead file list}

## Your Question
What input states does this code NOT handle?

Look for:
- Parameters that are accepted but never checked for null, undefined, or empty
- Numeric inputs with no boundary validation
- String inputs with no length or format checks
- Arrays or objects passed in where the code assumes a specific shape without
  verifying it
- Inputs that reach conditional logic and could produce an unhandled branch

Read the code carefully. Think about what a caller could legally pass in
(given the signature) that the code would mishandle.

Output format:
- SIGNAL: {one-line description of the unhandled input state found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

### F2 — Spec-Code Alignment

```
You are a recon probe for the functionality domain.

## Bead Files
{bead file list}

## Your Question
Does the implementation match every behavior claimed in the spec, docstrings,
or comments?

Look for:
- Functions or classes with docstrings or inline comments describing behavior —
  does the actual code do what they say?
- Spec documents referenced in the bead objective — does the code implement
  every stated requirement?
- Return value claims (e.g., "returns sorted list", "returns null if not found")
  — check all code paths, not just the happy path
- Side effect claims (e.g., "has no side effects", "does not mutate input") —
  verify these hold in the implementation
- Error behavior claims (e.g., "throws if id is invalid") — check whether the
  error actually fires under those conditions

Output format:
- SIGNAL: {one-line description of the spec-code mismatch found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

---

## Security Recon

### S1 — Unsanitized External Input Paths

```
You are a recon probe for the security domain.

## Bead Files
{bead file list}

## Your Question
Are there external inputs that reach data operations, interpreters, or
output sinks without sanitization or validation?

Look for:
- HTTP request parameters, headers, body fields, or query strings that are
  read from the request and used in database queries, filesystem operations,
  shell invocations, template rendering, or HTML output without sanitization
- Function parameters that accept user-supplied strings and pass them directly
  into SQL, NoSQL queries, file paths, or log statements
- Any place where input is used before it is validated — validation that comes
  AFTER use does not count
- Dynamic query construction using string concatenation with external values
- File path construction that includes user-supplied segments without
  canonicalization or allowlist checking

Output format:
- SIGNAL: {one-line description of the unsanitized input path found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

### S2 — Secrets, Credential Exposure, and Auth Gaps

```
You are a recon probe for the security domain.

## Bead Files
{bead file list}

## Your Question
Are there secrets, credentials, or authentication gaps in this code?

Look for:
- Hardcoded API keys, tokens, passwords, private keys, or connection strings
  in source code or config files added by this bead
- Variables named password, secret, key, token, credential that are assigned
  literal string values
- Passwords or tokens logged, included in error messages, or returned in API
  responses
- Endpoints or functions that perform sensitive operations without checking
  whether the caller is authenticated
- JWT or session token handling that skips signature verification
- Password comparison using equality operators instead of constant-time
  comparison functions
- Credentials stored in plaintext rather than as hashed values

Output format:
- SIGNAL: {one-line description of the secret exposure or auth gap found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

---

## Usability Recon

### U1 — Error Message Quality

```
You are a recon probe for the usability domain.

## Bead Files
{bead file list}

## Your Question
Are the error messages in this code clear, actionable, and complete?

Look for:
- Error messages that say only "error", "failed", "invalid", or "bad request"
  without specifying what failed, why it failed, or what the caller should do
- Validation errors that say "invalid input" without identifying which field
  or what constraint was violated
- Exceptions that are caught and re-thrown with a generic message, discarding
  the original error's context and cause
- Error codes that are numeric or opaque without a mapping to human-readable
  descriptions
- Error responses that expose internal implementation details (stack traces,
  SQL queries, file paths) that a user should not see

A good error message answers: what happened, why it happened, and how to fix it.

Output format:
- SIGNAL: {one-line description of the error message quality problem found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

### U2 — API Consistency with Codebase Conventions

```
You are a recon probe for the usability domain.

## Bead Files
{bead file list}

## Your Question
Does this code's API follow the conventions already established in the codebase?

Look for:
- Function or method names that use a different naming pattern from similar
  functions elsewhere (e.g., getX vs fetchX vs loadX when the codebase
  already uses one pattern consistently)
- Parameter ordering that differs from similar functions (e.g., (id, options)
  vs (options, id) when sibling functions use one order)
- Return shapes that differ from similar functions (e.g., returning raw value
  when siblings return {data, error}, or throwing when siblings return null)
- Async/sync patterns that differ from sibling functions in the same module
- Null/undefined handling that differs from the codebase convention

You may need to read a small amount of surrounding code to establish the
convention. Focus on the specific interface introduced or modified by this bead.

Output format:
- SIGNAL: {one-line description of the API consistency deviation found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

---

## Resilience Recon

### R1 — Failure Handling Gaps

```
You are a recon probe for the resilience domain.

## Bead Files
{bead file list}

## Your Question
Are there I/O operations, external calls, or dependency invocations that lack
error handling or timeouts?

Look for:
- Database queries, HTTP requests, file reads/writes, cache operations, or
  message queue operations that are not wrapped in try/catch or equivalent
  error handling
- Operations that have no timeout configured — database calls, HTTP client
  calls, socket operations
- Catch blocks that swallow errors silently (catch the error, log it, and
  continue without propagating or failing)
- Operations that assume success without checking the return value or result
  status
- Error paths where resources (connections, file handles) acquired before the
  failure are not released in a finally block or equivalent cleanup

Output format:
- SIGNAL: {one-line description of the failure handling gap found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```

### R2 — Unbounded Growth

```
You are a recon probe for the resilience domain.

## Bead Files
{bead file list}

## Your Question
Are there collections, caches, queues, or resources that can grow without
bound?

Look for:
- Arrays, maps, sets, or lists that are appended to in a loop or per-request
  context without a maximum size limit or eviction policy
- In-memory caches with no TTL, no max-size, and no eviction — anything that
  accumulates across requests without a cleanup mechanism
- Event listeners or subscriptions that are registered repeatedly (e.g., on
  each function call or request) without being removed
- Timers or intervals that are started but never cleared, accumulating over
  the lifetime of the process
- Database result sets fetched entirely into memory without pagination when
  the result set could be large
- Retry or polling loops with no maximum attempt count or total time limit

Output format:
- SIGNAL: {one-line description of the unbounded growth risk found}
- NO_SIGNAL

One line only. No explanation beyond the signal description.
```
