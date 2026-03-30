# Canonical Registry

Static, declarative registry of canonical utilities. The debt-crawler agent constructs
grep/LSP/AST queries from these fields — no raw shell commands are stored here.

Mutable scan history (violation counts, trends) is stored in `docs/sdlc/debt-scan-report.md`,
NOT in this file.

## Canonical Path Prefixes

Any new export in a path starting with these prefixes triggers the migration plan gate
(Architect Phase 3 check + drift-detector L1 check).

```yaml
canonical_path_prefixes:
  - lib/utils/
  - lib/storage/patterns/
  - lib/hooks/
  - lib/db/
```

---

### Entry: withSoftDeleteFilter

- **canonical_id:** CANON-001
- **canonical_path:** `lib/storage/patterns/soft-delete.ts`
- **canonical_usage:** `import { withSoftDeleteFilter } from '@/lib/storage/patterns/soft-delete'`
- **match_type:** literal
- **pattern:** `deleted_at IS NULL`
- **include_paths:** `lib/storage/`, `app/api/`
- **exclude_paths:** `__tests__/`, `lib/storage/patterns/soft-delete.ts`
- **allowed_variants:** []
- **related_rules:** ['no-raw-soft-delete', 'storage/use-soft-delete-filter']
- **migration_rule:** Replace raw `deleted_at IS NULL` WHERE clause with `withSoftDeleteFilter(query)` call
- **owner_domain:** storage
- **introduced_by:** 2026-01-15
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: generateId

- **canonical_id:** CANON-002
- **canonical_path:** `lib/utils/id-generator.ts`
- **canonical_usage:** `import { generateId } from '@/lib/utils/id-generator'`
- **match_type:** regex
- **pattern:** `Math\.random|crypto\.randomUUID`
- **include_paths:** `lib/`, `app/`, `components/`
- **exclude_paths:** `__tests__/`, `node_modules/`, `lib/utils/id-generator.ts`
- **allowed_variants:** []
- **related_rules:** ['no-math-random-id']
- **migration_rule:** Replace with `generateId()` import and call
- **owner_domain:** infra
- **introduced_by:** 2026-01-10
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: useFetch

- **canonical_id:** CANON-003
- **canonical_path:** `lib/hooks/use-fetch.ts`
- **canonical_usage:** `import { useFetch } from '@/lib/hooks/use-fetch'`
- **match_type:** regex
- **pattern:** `useEffect\s*\([^)]*\)\s*\{[^}]*fetch\(`
- **include_paths:** `components/`, `app/`
- **exclude_paths:** `__tests__/`, `lib/hooks/use-fetch.ts`
- **allowed_variants:** []
- **related_rules:** ['no-inline-fetch']
- **migration_rule:** Replace inline useEffect+fetch with useFetch hook
- **owner_domain:** frontend
- **introduced_by:** 2026-02-01
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: BaseModal

- **canonical_id:** CANON-004
- **canonical_path:** `components/ui/base-modal.tsx`
- **canonical_usage:** `import { BaseModal } from '@/components/ui/base-modal'`
- **match_type:** regex
- **pattern:** `LegacyModalShell|ResponsiveModal|GlobalModal|import.*from.*['"]@radix-ui/react-dialog['"]`
- **include_paths:** `components/`, `app/`
- **exclude_paths:** `__tests__/`, `components/ui/base-modal.tsx`
- **allowed_variants:** []
- **related_rules:** ['no-legacy-modal']
- **migration_rule:** Replace with BaseModal component
- **owner_domain:** frontend
- **introduced_by:** 2026-01-20
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived

---

### Entry: hashToken

- **canonical_id:** CANON-005
- **canonical_path:** `lib/utils/hash.ts`
- **canonical_usage:** `import { hashToken } from '@/lib/utils/hash'`
- **match_type:** regex
- **pattern:** `createHash\(['"]sha256['"]\)\.update\(.*\)\.digest\(['"]hex['"]\)`
- **include_paths:** `lib/`, `app/`
- **exclude_paths:** `__tests__/`, `lib/utils/hash.ts`
- **allowed_variants:** ['lib/storage/api-keys-storage.ts']
- **related_rules:** []
- **migration_rule:** Replace inline SHA-256 hash with hashToken() import
- **owner_domain:** auth
- **introduced_by:** 2026-01-05
- **sunset_condition:** Violation count reaches 0 for 2 consecutive scans -> entry archived
