# Fitness Function Catalog

Concrete checks that validate architectural properties. Each check can be run by a guppy, drift-detector, or as part of the /audit command.

---

### Check: No Math.random() for IDs
**Type:** convention
**What:** Production code must use `generateId()` from `lib/utils/id-generator.ts`, not `Math.random()`
**How:** `grep -rn "Math.random()" lib/ --include="*.ts" --exclude-dir="__tests__"`
**Pass:** Zero matches in production code (test files excluded)
**Fail action:** L1 correction — replace with generateId()

### Check: StorageError in storage layer
**Type:** convention
**What:** Storage files must throw `StorageError`, not raw `throw new Error()`
**How:** `grep -rn "throw new Error" lib/storage/ --include="*.ts" --exclude-dir="__tests__"`
**Pass:** Zero matches (excluding catch-and-rethrow patterns)
**Fail action:** L1 correction — replace with appropriate StorageError static method

### Check: safeToast for notifications
**Type:** convention
**What:** Components must use `safeToast` from `lib/utils/safe-toast`, not raw `alert()` or `toast()` from sonner
**How:** `grep -rn "alert(" components/ --include="*.tsx"` and `grep -rn "from 'sonner'" components/`
**Pass:** Zero matches
**Fail action:** L1 correction — replace with safeToast

### Check: requirePermission for API routes
**Type:** boundary
**What:** API routes must use `requirePermission()` middleware, not raw session/role checks
**How:** `grep -rn "session.user.role" app/api/ --include="*.ts"` (should use ROLES constant or permission check)
**Pass:** All routes wrapped in requirePermission()
**Fail action:** WARNING — requires design decision on permission model

### Check: No circular dependencies
**Type:** structural
**What:** Import graph has no circular references
**How:** LSP incomingCalls/outgoingCalls chain — or `madge --circular --extensions ts lib/`
**Pass:** No cycles detected
**Fail action:** BLOCKING — must break the cycle

### Check: Storage layer isolation
**Type:** boundary
**What:** API routes must not call `getDatabase()` directly — must go through storage functions
**How:** `grep -rn "getDatabase()" app/api/ --include="*.ts"`
**Pass:** Zero matches in API routes (storage files are OK)
**Fail action:** WARNING — move DB access to storage layer

### Check: Soft-delete filter on tables with deleted_at
**Type:** structural
**What:** SELECT queries on tables with `deleted_at` column must include `deleted_at IS NULL`
**How:** Cross-reference table schema (PRAGMA table_info) with query builders
**Pass:** All queries on soft-delete tables include the filter
**Fail action:** BLOCKING — data leakage risk

### Check: Test assertions are real (VORP)
**Type:** coverage
**What:** Test files must not contain vacuous assertions (`expect(true).toBe(true)`)
**How:** `grep -rn "expect(true)" __tests__/ e2e/ --include="*.ts"`
**Pass:** Zero vacuous assertions
**Fail action:** L2 Oracle correction — replace with behavioral assertions

### Check: No hardcoded localhost in production paths
**Type:** convention
**What:** Production code must not fall back to `localhost:3001` without a production guard
**How:** `grep -rn "localhost:3001" lib/ app/ --include="*.ts"`
**Pass:** All matches have `NODE_ENV === 'production'` guard or throw
**Fail action:** WARNING — add production guard

### Check: HMAC for API key hashing
**Type:** security
**What:** API key hashing must use HMAC-SHA256, not plain SHA-256
**How:** `grep -rn "createHash('sha256')" lib/storage/api-keys-storage.ts`
**Pass:** Uses createHmac, not createHash (or has ENCRYPTION_KEY guard)
**Fail action:** BLOCKING — security vulnerability

### Check: Duplicate function count ratchet
**Type:** structural
**What:** PROMOTE-classified duplicate count must not exceed prior Evolve scan baseline
**How:** debt-crawler evaluates during Evolve bead #19; compares current PROMOTE count against previous in `docs/sdlc/debt-scan-report.md`
**Pass:** PROMOTE count <= previous scan count
**Fail action:** BLOCKING within Evolve — debt-crawler writes FAIL to system health report; Conductor must acknowledge and either fix or document justification before Evolve cycle completes
**Scope:** Evaluated by debt-crawler during Evolve bead #19 only. Does NOT run in per-bead sdlc-fitness checks.
**Note:** WATCH count is tracked and trended but advisory only

### Check: Bare suppression ratchet
**Type:** governance
**What:** Bare eslint-disable count (score 0) must not increase between Evolve scans
**How:** standards-curator compares current bare count from `docs/sdlc/active/{task-id}/rule-governance-profile.md` against the most recent prior profile found via the Evolve lookback contract (`active/*/rule-governance-profile.md` + `completed/*/rule-governance-profile.md`, last 10 tasks or 30 days)
**Pass:** Bare count <= previous
**Fail action:** WARNING — flag in system health report for Conductor review
**Scope:** Evaluated by standards-curator during Evolve step #15 only
