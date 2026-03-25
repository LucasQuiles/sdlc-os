# Reuse Patterns Registry

The canonical source registry — the "phone book" of reusable patterns. When an agent needs functionality, check here first.

---

### Pattern: ID Generation
**Canonical source:** `lib/utils/id-generator.ts`
**What it provides:** `generateId(prefix, randomLength?)` — cryptographically secure IDs
**How to use:** `import { generateId } from '@/lib/utils/id-generator'`
**Also available:** Entity-specific helpers: `generateCustomerId()`, `generateInvoiceId()`, etc.
**Common misuse:** `Math.random().toString(36)` — insecure, collision-prone

### Pattern: Error Messages
**Canonical source:** `lib/utils/error-utils.ts`
**What it provides:** `getErrorMessage(error)` — safely extract message from unknown error
**How to use:** `import { getErrorMessage } from '@/lib/utils/error-utils'`
**Common misuse:** Duplicating the function in each storage file

### Pattern: Storage Errors
**Canonical source:** `lib/storage/storage-error.ts`
**What it provides:** `StorageError.notFound()`, `.conflict()`, `.internal()` — typed storage errors
**How to use:** `import { StorageError } from '@/lib/storage/storage-error'`
**Common misuse:** `throw new Error('not found')` — loses type information

### Pattern: Toast Notifications
**Canonical source:** `lib/utils/safe-toast.ts`
**What it provides:** `safeToast.success()`, `.error()`, `.info()` — safe notification wrapper
**How to use:** `import { safeToast } from '@/lib/utils/safe-toast'` or `import { safeToast as toast } from ...`
**Common misuse:** `alert()` or direct `import { toast } from 'sonner'`

### Pattern: Currency Formatting
**Canonical source:** `lib/utils/currency-utils.ts`
**What it provides:** `formatCurrency(amount, opts?)` — locale-aware currency display
**How to use:** `import { formatCurrency } from '@/lib/utils/currency-utils'`
**Common misuse:** `new Intl.NumberFormat(...)` inline in components

### Pattern: Percentage Formatting
**Canonical source:** `lib/utils/formatting.ts`
**What it provides:** `formatPercentage(value, opts?)` — handles null/undefined, decimal vs percentage
**How to use:** `import { formatPercentage } from '@/lib/utils/formatting'`
**Common misuse:** Inline `${value.toFixed(1)}%` patterns

### Pattern: Role Checking
**Canonical source:** `lib/permissions/shared.ts`
**What it provides:** `ROLES` constant, `canManageRole()`, `getRoleDisplayName()`
**How to use:** `import { ROLES } from '@/lib/permissions/shared'`
**Common misuse:** String comparison `role === 'user'` instead of `role === ROLES.USER`

### Pattern: API Route Permission
**Canonical source:** `lib/middleware/permissions.ts`
**What it provides:** `requirePermission(PERMISSION_CONSTANT)` — HOF wrapper for API routes
**How to use:** `export const GET = requirePermission(VIEW_PERMISSION)(async (req, ctx) => { ... })`
**Common misuse:** Inline `session.user.role` checks in route handlers

### Pattern: Database Transactions
**Canonical source:** `lib/db/transaction-helper.ts`
**What it provides:** `withTransaction()`, `calculateBackoffDelay()` — transaction wrapper with retry
**How to use:** `import { withTransaction } from '@/lib/db/transaction-helper'`
**Common misuse:** `db.transaction(() => { ... })` without retry logic

### Pattern: Scoped Logging
**Canonical source:** `lib/utils/api-logger-helpers.ts`
**What it provides:** `createScopedLogger(request)` — request-scoped structured logging
**How to use:** `const log = createScopedLogger(request)`
**Common misuse:** `console.log()` in API routes
