# Domain Attack Libraries

Attack vectors and example probes organized by domain. Red team commanders draw from these libraries when designing strike guppy directives. Each category includes specific inputs and scenarios — not just labels.

---

## 1. Functionality Attack Library

### Input Coverage

Probe all input states the code may receive, including those the developer did not intend to handle.

- **Empty / null inputs:** Pass `null`, `undefined`, `""`, `0`, `[]`, `{}` to every parameter. Does the code crash, produce wrong output, or silently succeed with corrupt state?
- **Boundary values:** For numeric ranges, test `min - 1`, `min`, `min + 1`, `max - 1`, `max`, `max + 1`. For strings, test length exactly at limit, one over, one under.
- **Type mismatches:** Pass a string where an integer is expected, an array where an object is expected, a boolean where a string is expected. In dynamically typed languages, callers can do this without compiler enforcement.
- **Unicode and encoding edge cases:** Pass `"\u0000"` (null byte), `"\uFFFD"` (replacement char), right-to-left override character `"\u202E"`, emoji sequences (multi-codepoint), strings with NFC vs NFD normalization differences. Does the code produce consistent length calculations and comparisons?
- **Nested / deeply structured inputs:** Pass objects 10 levels deep. Pass arrays with 10,000 elements. Does the code blow the call stack or time out?
- **Concurrent / interleaved inputs:** If the function processes a queue or shared structure, what happens if two callers invoke it simultaneously with overlapping data?

### Logic Path Coverage

Verify that all branches execute correctly — not just the happy path.

- **If/else branches:** Identify every boolean condition. Supply inputs that make each branch true and false independently. Never assume tests have already done this.
- **Switch / match with default:** What does the default or `otherwise` branch do? Is it a silent no-op, a panic, or a fallback? Probe with an input that hits only the default.
- **Short-circuit evaluation:** If `a && b`, what happens when `a` is false and `b` would throw? Does the short-circuit prevent an error that masks a real bug elsewhere?
- **Ternary expressions:** Probe both arms. Look for ternaries where one arm returns `null` or mutates state silently.
- **Early returns:** Functions with multiple return points often have paths where postconditions (logging, cleanup, metric recording) are skipped. Identify every early return and check what it skips.
- **Loop boundaries:** Test loops with zero iterations, one iteration, and exactly `n` iterations where `n` is the documented or inferred limit. Test infinite-loop conditions (break never fires, counter never increments).

### State Machine Coverage

When the code manages explicit or implicit state, probe illegal transitions and boundary conditions.

- **Invalid transitions:** Attempt to move from state A directly to state C when the spec requires A → B → C. Does the code reject, corrupt, or silently allow it?
- **Duplicate events:** Submit the same event twice (e.g., `order.placed` twice). Does the state machine detect idempotency or double-process?
- **Out-of-order events:** Deliver event B before event A. Does the system queue, reject, or corrupt?
- **Concurrent state changes:** Two callers attempt conflicting transitions simultaneously. Which wins? Is a race condition possible?
- **Missing terminal state:** Is there a path through the state machine where no terminal state is ever reached? Can an entity get stuck in a non-terminal state indefinitely?

### Contract Verification

Check that the code does exactly what the spec or documentation claims.

- **Spec-code alignment:** Read every behavior claim in the spec, docstring, or README. Test each one directly. Pay special attention to claims about ordering, idempotency, atomicity, and error conditions.
- **Undocumented behaviors:** Look for behaviors the code exhibits that are NOT in the spec. These are contract landmines — callers may depend on them, but they could change without warning.
- **Return value contracts:** If the spec says the function returns a sorted list, verify it is sorted under all input orderings, not just one.
- **Side effect contracts:** If the spec says the function has no side effects, check whether it mutates arguments, writes to shared state, or logs.

### Regression Surface

Ensure existing callers are not broken by the bead's changes.

- **Existing callers:** Identify every caller of changed functions or modified APIs. For each one, verify the call still works with the new signature, return type, and behavior.
- **Backward compatibility:** If a parameter was renamed, reordered, or had its type changed, will old call sites with positional arguments still work? Will serialized data (JSON, database rows) with old field names still deserialize correctly?
- **Implicit contracts from test suite:** Look for tests that were written against old behavior and now pass for the wrong reason (e.g., the assertion is too loose).

---

## 2. Security Attack Library

### Injection — OWASP A03:2021

Probe every path where external input reaches an interpreter, query builder, or command executor without full sanitization.

- **SQL injection:** Try `' OR '1'='1`, `'; DROP TABLE users; --`, `1 UNION SELECT username, password FROM users --`. Also test numeric parameters with `1 OR 1=1`. Check ORM usage — does the code use raw queries, `query()` with string concatenation, or `execute()` with format strings anywhere?
- **NoSQL injection:** Try `{"$gt": ""}` in MongoDB filter fields. Try `{"$where": "1==1"}`. Check if user-supplied JSON is passed directly into a query object.
- **Command injection:** Try `; ls -la`, `| cat /etc/passwd`, backtick-wrapped `whoami`, `$(id)` in any parameter that reaches `exec()`, `spawn()`, `system()`, `popen()`, or shell invocations. Also try newlines `\n` and null bytes `\0` to break argument parsing.
- **XSS — reflected:** In any parameter rendered into an HTML response, try `<script>alert(1)</script>`, `"><img src=x onerror=alert(1)>`, `javascript:alert(1)` in href attributes.
- **XSS — stored:** If user input is persisted and later rendered to other users, does it survive sanitization between write and read? Try the same payloads with double encoding such as `&lt;script&gt;`.
- **XSS — DOM-based:** Does the code set `innerHTML`, `document.write()`, or `location.href` from user-controlled sources (URL params, `postMessage`, `localStorage`)?
- **Template injection:** If a templating engine is in use (Jinja2, Handlebars, Pebble, Twig), try `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`. A `49` in the output confirms server-side template injection.
- **Path traversal:** Try `../../../etc/passwd`, `..%2F..%2Fetc%2Fpasswd`, `....//....//etc/passwd` in any file path parameter. Also try absolute paths like `/etc/passwd` directly.
- **Header injection:** Try `\r\nX-Injected-Header: evil` in parameters that end up in HTTP response headers (Location, Set-Cookie, etc.).
- **LDAP injection:** Try `*)(uid=*))(|(uid=*`, `)(!` in LDAP filter parameters to escape the query structure.

### Authentication — OWASP A07:2021

- **Missing auth checks:** Identify every route, function, or API endpoint in the bead. For each one, check whether authentication is enforced by the framework, middleware, or the function itself. Look for routes that rely on "being hard to find" rather than actual checks.
- **JWT issues:** Check whether JWT signature is verified (not just decoded). Try the `alg: none` attack (remove signature, set algorithm to none). Try changing the `sub` or `role` claim without re-signing — does the server accept it? Check if the secret is weak or hardcoded.
- **Session fixation:** Does the server issue a new session token after login, or reuse the pre-login session ID?
- **Rate limiting:** Are login, password-reset, and MFA endpoints rate-limited? Try 100 requests per second against them.
- **Credential handling:** Are passwords compared with a constant-time function? Are they stored as bcrypt/argon2/scrypt hashes? Is there any place where a plaintext password appears in a log, error message, or URL parameter?

### Authorization — OWASP A01:2021

- **Horizontal privilege escalation (IDOR):** Does accessing `/api/orders/123` require that the authenticated user owns order 123? Try substituting another user's ID directly in the path or query param. Check whether the code validates ownership or just validates authentication.
- **Vertical privilege escalation:** Can a regular user perform admin actions by changing a role parameter in the request body, query string, or cookie?
- **IDOR via indirect references:** Check every place where a user-supplied ID (numeric, UUID, or slug) is used to look up a database record. Is ownership validated before the record is returned or modified?
- **Ownership enforcement:** When updating a resource, does the update query filter by both the resource ID and the owner's user ID? Or does it trust a user-supplied `ownerId` field in the request body?
- **Role confusion:** If the system has multiple roles (admin, manager, user, guest), try performing operations from a lower-privilege role. Pay attention to endpoints that check role presence but not role sufficiency (e.g., `hasRole('manager')` when the operation requires `admin`).

### Data Exposure — OWASP A02:2021

- **Stack traces in responses:** Trigger an error (pass malformed input, cause a 500) and check whether the error response includes a stack trace, internal file paths, SQL query text, or environment variable values.
- **Internal paths and version disclosure:** Check response headers and error messages for server version strings, framework names, internal directory structure, and database schema names.
- **PII in logs:** Identify every log statement in the changed code. Does any log statement include passwords, tokens, SSNs, credit card numbers, email addresses, or health data? Check structured logging too — is the entire request object logged, including authorization headers?
- **Secrets in responses:** Does any API response include fields that should be write-only (e.g., `passwordHash`, `secretKey`, `internalId`)? Check serialization configurations.
- **Secrets in source or config:** Does the changed code introduce any hardcoded credentials, API keys, private keys, or tokens? Check for `password =`, `secret =`, `key =`, `token =` patterns.

### Configuration — OWASP A05:2021

- **CORS:** Check the `Access-Control-Allow-Origin` header. Is it set to `*`? Is it reflecting the request's `Origin` header without validation? This allows any website to make credentialed cross-origin requests.
- **CSP:** Is a Content Security Policy header set? Does it include `unsafe-inline` or `unsafe-eval`? Is it missing `default-src`?
- **Security headers:** Check for presence of `X-Frame-Options` (or `frame-ancestors` in CSP), `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, `Referrer-Policy`.
- **Debug mode / verbose errors:** Is debug mode disabled in production config? Are detailed error messages (full stack traces) suppressed from external responses?
- **Insecure defaults:** Does the bead introduce any new configuration that has an insecure default (e.g., auth disabled, TLS verification off, wildcard permissions)?

---

## 3. Usability Attack Library

### API Consistency

The bead's API should follow the conventions established in the rest of the codebase — not its own invented conventions.

- **Naming conventions:** Does the new function/method/endpoint name follow existing patterns? If the codebase uses `getUserById`, does the new code use `fetchUser` or `getUser`? If REST endpoints are plural nouns, does the new endpoint follow that?
- **Parameter ordering:** If similar functions in the codebase put `(id, options)`, does the new function put `(options, id)`? Inconsistent parameter ordering causes silent bugs at call sites.
- **Return shapes:** If similar functions return `{ data, error }`, does the new function return the raw value or throw? Check that success and error shapes are consistent with their siblings.
- **Null/undefined handling:** If the codebase conventionally returns `null` when a record is not found, does the new code throw, return `undefined`, return an empty object, or return `null` consistently?
- **Async patterns:** If the codebase uses async/await throughout, does the new code return raw Promises without `await`? Does it mix callback-style and promise-style in the same module?

### Error Messages

Error messages must answer three questions: what happened, why it happened, and how to fix it.

- **Missing "what":** Is the error message so generic that the user cannot tell which operation failed? Example: "An error occurred." is not useful.
- **Missing "why":** Does the error explain the cause? "Validation failed" does not tell the user which field failed or what constraint was violated.
- **Missing "how to fix":** Does the error give the user actionable guidance? "Invalid format" should specify what format is expected.
- **Error codes:** If the system uses error codes, are new errors assigned codes? Are they documented? Are they consistent with the existing code namespace?
- **Context loss:** When an error is caught and re-thrown, is the original error message and stack preserved, or is it replaced with a generic wrapper that discards context?

### Interface Predictability

The interface should behave the way a developer expects it to behave, based on its name and the codebase conventions.

- **Hidden side effects:** Does a function that looks like a read operation also write, delete, or mutate state? Example: `getUser()` that also increments a view counter without documenting it.
- **Argument mutation:** Does the function modify any of its input arguments? If so, is this documented? In most codebases, mutation of arguments is surprising and bug-prone.
- **Implicit state requirements:** Does the function require some global or module-level state to be set up before it can be called? Is this dependency obvious from the function signature, or does it fail silently when the state is missing?
- **Surprising defaults:** Does the function have default parameter values that could cause silent data loss or incorrect behavior if not overridden? Example: a `limit` parameter defaulting to 10 when callers expect unlimited results.

### Documentation Accuracy

Documentation that does not match code behavior is worse than no documentation — it actively misleads.

- **Parameter documentation:** Does the docstring accurately describe every parameter, including type, valid range, and what happens if it is omitted?
- **Return type documentation:** Does the documented return type match the actual return type in all code paths? Check especially the error path — does the function throw, return null, or return an error object?
- **Comment-code divergence:** Identify inline comments that describe what the code does. Do they still match the code after the bead's changes? Stale comments are a maintenance hazard.
- **README accuracy:** If the bead updates a component with a README, does the README still accurately describe the component's behavior, configuration options, and usage examples?

### Accessibility

For any user-facing component, probe WCAG 2.1 AA compliance patterns.

- **Form labels:** Does every form input have an associated `<label>` element (via `for`/`id` or `aria-label` or `aria-labelledby`)? Placeholder text is not a substitute for a label.
- **Keyboard navigation:** Can all interactive elements (buttons, links, inputs, custom controls) be reached and activated using only a keyboard? Is the tab order logical?
- **Focus management:** When a modal or dialog opens, is focus moved to it? When it closes, is focus returned to the element that triggered it?
- **Color contrast:** Do text and background color combinations meet the 4.5:1 contrast ratio (AA)? Check both light and dark themes if applicable.
- **Screen reader compatibility:** Do interactive elements have meaningful accessible names? Are icon-only buttons labeled with `aria-label`? Are status messages announced via `aria-live`?
- **ARIA usage:** Is ARIA used correctly? Common mistakes: `aria-label` on elements that already have visible text (override), `role="button"` on a `<div>` without keyboard event handlers, `aria-hidden="true"` on focusable elements.

### Developer Experience

Consider the friction a developer faces when using this code for the first time.

- **Steps to use:** How many steps does it take to use this function from scratch? If it requires 5 setup steps, 3 imports, and a specific initialization order, the DX score is low.
- **Cognitive load:** Does the function name require domain expertise to understand? Are there multiple overloaded parameters with different behavior depending on type? Magic boolean flags (`processData(true, false, true)`) are high cognitive load.
- **Magic values:** Does the code use unexplained numeric or string literals? `if (status === 3)` is worse than `if (status === ORDER_STATUS.SHIPPED)`.
- **TypeScript / type safety:** If the project uses TypeScript, does the new code have `any` types, missing generics, or incorrect type assertions that remove type safety at the boundary?

---

## 4. Resilience Attack Library

### Dependency Failure

Simulate each dependency failing in realistic ways — not just "unavailable" but the full range of failure modes.

- **Database failure modes:** Connection refused (database down), connection timeout (database overloaded), query timeout (table lock), deadlock (concurrent writers), connection pool exhaustion (too many concurrent requests), read replica lag causing stale reads.
- **External API failure modes:** HTTP 500 (server error), HTTP 429 (rate limit exceeded), HTTP 503 (service unavailable), connection timeout (slow network), empty response body (truncated), malformed JSON response (encoding error), certificate error (expired TLS cert).
- **Cache failure modes:** Cache miss (not populated), cache corruption (wrong value returned), cache connection refused (Redis down), cache timeout (overloaded), stale cache (TTL not enforced).
- **Message queue failure modes:** Message rejected (queue full), consumer group lag (processor too slow), message duplication (at-least-once delivery), out-of-order delivery, poison message (handler crashes on this message repeatedly).
- **Filesystem failure modes:** File not found, permission denied, disk full, network filesystem timeout, concurrent write conflict, file locked by another process.

### Error Propagation

Check whether errors are propagated correctly and with enough context for diagnosis.

- **Cause chaining:** When a low-level error is caught and re-thrown, is the original error attached as a cause? Example: `throw new Error("Failed to save order", { cause: originalError })`. Without cause chaining, the original stack trace is lost.
- **Broad catch blocks:** Does `catch(e)` or `except Exception` catch errors it should not — including programmer errors like `TypeError`, `ReferenceError`, `NameError`? Broad catches that swallow all exceptions hide bugs.
- **Silently swallowed errors:** Does any `catch` block log and continue without re-throwing or propagating the error? This can cause the calling code to believe an operation succeeded when it failed.
- **Context loss on propagation:** When an error passes through multiple function calls, does each layer add context (which operation failed, what the input was) or does the error lose its context as it propagates up?

### Resource Management

Verify that all acquired resources are released, regardless of the code path.

- **Database connection release:** Is every acquired connection returned to the pool in all code paths, including error paths? An unclosed connection on error will leak connections until the pool is exhausted.
- **File handle release:** Are file handles closed in a `finally` block, `using` statement, or context manager? A file handle left open on error prevents future opens on some systems.
- **Event listener cleanup:** Are event listeners registered in component setup or `addEventListener` removed in the corresponding cleanup? Unremoved listeners accumulate across component re-mounts, causing memory leaks and duplicate event handling.
- **Timer cleanup:** Are interval and timeout calls cleared when the component or context they belong to is destroyed? Orphaned timers continue running and may reference garbage-collected objects.
- **Memory growth:** Does the code append to a collection (array, map, set, queue) without a mechanism to bound its size? A cache without eviction, a log without rotation, or a queue without backpressure will grow unboundedly.
- **Unbounded in-memory collections:** Is there any HashMap, List, Set, or equivalent that grows proportionally with request volume, user count, or time — without a limit?

### Timeout and Retry

All I/O operations must have timeouts. All retry logic must be bounded and safe.

- **Missing timeouts:** Does every HTTP client call, database query, file read, and socket operation specify a timeout? Operations without timeouts can hang indefinitely, blocking threads or async tasks.
- **Timeout values too high:** A 60-second timeout on a database query that should complete in 100ms will keep a thread/connection occupied for a minute when the database is slow. Are timeouts calibrated to realistic SLA expectations?
- **Unbounded retry loops:** Does any retry logic loop forever? Is there a maximum retry count? Is there a circuit breaker that stops retrying after repeated failures?
- **No exponential backoff:** Does retry logic retry immediately, without delay, between attempts? Immediate retries on a rate-limited or overloaded service generate a retry storm that worsens the outage.
- **Retrying non-idempotent operations:** Is a mutation (write, delete, charge) being retried without idempotency protection? If the first attempt succeeded but the response was lost, retrying will execute the operation twice. Writes must be idempotent (via idempotency keys) before being retried automatically.

### Cascading Failure

One failing dependency should not take down the entire system.

- **Slow dependency causes thread exhaustion:** If a downstream service starts responding slowly (2s instead of 100ms), do all threads/goroutines/async tasks fill up waiting for it, starving other requests? Is there a timeout short enough to prevent this?
- **Retry storm amplification:** If many clients all hit a failing service and retry simultaneously, the retry traffic can exceed the original load. Is there jitter in the backoff? Is there a circuit breaker that stops sending requests when the failure rate is high?
- **Health check cascade:** If the service's health check endpoint performs actual dependency checks (database ping, cache ping), a slow dependency will cause health checks to timeout, causing the load balancer to remove healthy instances — making the problem worse. Should the health check be a shallow ping?
- **Backpressure missing:** If this service calls a downstream service faster than it can process, does it apply backpressure (rate limit itself) or does it flood the downstream until it falls over?

### Graceful Degradation

The system should remain partially functional when dependencies are unavailable.

- **Cache fallback to source:** If the cache is unavailable, does the code fall back to the source of truth (database, API), or does it fail completely? Is the fallback path tested?
- **Search fallback to browse:** If a search service is unavailable, can users still browse or view content directly, or does the search failure block all user activity?
- **Non-critical path isolation:** If a non-critical feature (analytics, recommendations, audit logging) fails, does it cause the main user flow to fail? Non-critical paths must be isolated so their failures do not propagate to critical paths.
- **Feature flag or degraded mode:** Does the code have a mechanism to disable a failing feature without a deployment? Can a feature be turned off at runtime to restore service?
