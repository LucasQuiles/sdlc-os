# Actionable Dedup Triage — lib/storage/ (2026-04-12)

**Pipeline:** 3,349 functions → 11 detectors → 2.2M raw pairs → 101 actionable (Type 1, HIGH, >= 20L body)
**Report:** 2,954 lines, 84KB — passes 5,000-line / 5MB budget

## Top-20 Classification

| # | Pair | Class | Why it survived suppression |
|---|------|-------|---------------------------|
| 1 | getClockEntriesByUserId ↔ getAttachmentsForComment | FALSE POSITIVE | Different domains, different result types. Shape match only. |
| 2 | getClockedInUsers ↔ getTopNotificationRecipients | FALSE POSITIVE | Different queries and aggregation logic. Shape match only. |
| 3 | restoreCompanyEvent ↔ restoreCompanyNews | **REAL** | Identical restore pattern: UPDATE deleted_at, check changes, fetch. Extractable generic restore helper. |
| 4 | getBudgetProjection ↔ getBudgetById | **REAL** | Same table, identical SELECT/mapping. Only WHERE differs. Shared base query. |
| 5 | getCompanyBuildings ↔ getProgramMeasures | STRUCTURAL PARALLEL | Same "get related entities for parent ID" pattern, different domains. |
| 6 | getGroupMemberDetails ↔ getGrantedPermissionDetails | STRUCTURAL PARALLEL | Same single-ID-with-JOINs pattern, different entities. |
| 7 | getGroupMembersDetailed ↔ getGroupPermissionsDetailed | **REAL** | Near-identical queries against the same domain (groups). Shared query builder viable. |
| 8 | getDamageReportById ↔ getVehicleIssueById | STRUCTURAL PARALLEL | Same vehicle-domain pattern with date calcs. Different fields. |
| 9 | getCompanyNewsWithAuthor ↔ getRecognitionWithUsers | STRUCTURAL PARALLEL | Same get-by-ID-with-user-JOINs pattern, different cardinalities. |
| 10 | getActiveBudget ↔ getBudgetProjection | **REAL** | Same table + mapping as #4. Budget query cluster. |
| 11 | getCompanyBuildings ↔ getSupplierComplianceSelfContained | FALSE POSITIVE | Different tables and logic. |
| 12 | getChildCompanies ↔ getItemTiersSelfContained | FALSE POSITIVE | Unrelated tables, same shape. |
| 13 | getProgramMeasures ↔ getSupplierComplianceSelfContained | FALSE POSITIVE | Different domain entities. |
| 14 | getGroupMembers ↔ getGroupPermissionsDetailed | FALSE POSITIVE | Members vs permissions — different domains despite same file. |
| 15 | getGroupMembers ↔ getUserGroups | STRUCTURAL PARALLEL | Same relation, inverse direction. |
| 16 | getGroupMembersDetailed ↔ getUserGroups | STRUCTURAL PARALLEL | Same as #15, different accessor. |
| 17 | getNotificationById ↔ getTemplateById | STRUCTURAL PARALLEL | Identical single-row-by-ID pattern, different tables. |
| 18 | getAliasesBySupplier ↔ getPaymentsByInvoice | STRUCTURAL PARALLEL | Same list-by-parent-ID pattern. |
| 19 | getAccessRequestDetails ↔ getActiveInviteToken | FALSE POSITIVE | Different structure and logic. |
| 20 | getClickUpTasksByBuilding ↔ getBuildingCompanies | FALSE POSITIVE | Different entity relationships. |

## Summary

| Classification | Count |
|---------------|-------|
| **REAL** | 4 (#3, #4, #7, #10) |
| STRUCTURAL PARALLEL | 7 |
| FALSE POSITIVE | 9 |

## REAL findings detail

1. **restoreCompanyEvent ↔ restoreCompanyNews** (#3) — Extract a generic `restoreSoftDeleted(table, id)` helper (one already exists in `lib/storage/patterns/soft-delete.ts` — check if these functions can use it directly).

2. **getBudgetProjection ↔ getBudgetById ↔ getActiveBudget** (#4, #10) — Budget query cluster in `contractor-budget-storage.ts`. Three functions with identical SELECT/mapping, different WHERE conditions. Extract shared `baseBudgetQuery()` helper.

3. **getGroupMembersDetailed ↔ getGroupPermissionsDetailed** (#7) — Near-identical queries in `groups-storage.ts`. Shared query builder with parameterized table/columns.

## Why false positives survive

The remaining false positives share structural patterns (SELECT → JOIN → WHERE → map) that are common across all storage modules. The 20-body-line minimum successfully filters trivial wrappers, but substantial functions that happen to follow the same coding pattern still match at score 1.0 from 9+ strategies. Further reduction would require semantic analysis (understanding that the queries target different schemas), which is beyond the current classical-detector pipeline.

## Next actions (prioritized)

1. Check if `restoreCompanyEvent`/`restoreCompanyNews` can delegate to existing `restoreSoftDeleted()` in `soft-delete.ts`
2. Extract `baseBudgetQuery()` in `contractor-budget-storage.ts` for the 3-function cluster
3. Consider a shared group-entity query builder in `groups-storage.ts`
