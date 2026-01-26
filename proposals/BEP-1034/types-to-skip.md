# KernelV2 GQL - Types to Skip

These types are **not to be implemented**. They have been decided to be replaced by other designs.

---

## Summary

| Type | Location | Reason |
|------|----------|--------|
| `SchedulerPredicateGQL` | `common/types.py` | Replaced by new scheduler design |
| `SchedulerInfoGQL` | `common/types.py` | Replaced by new scheduler design |
| `KernelStatusHistoryEntryGQL` | `kernel/types.py` | Replaced by new status tracking design |
| `KernelStatusHistoryGQL` | `kernel/types.py` | Replaced by new status tracking design |

---

## Scheduler Types

### SchedulerPredicateGQL

**Action**: Do not implement. Will be replaced by new scheduler design.

### SchedulerInfoGQL

**Action**: Do not implement. Will be replaced by new scheduler design.

---

## Status History Types

### KernelStatusHistoryEntryGQL

**Action**: Do not implement. Status history design will be revisited.

### KernelStatusHistoryGQL

**Action**: Do not implement. Status history design will be revisited.

---

## Affected Parent Types

The following types need modification to remove references to skipped types:

### KernelLifecycleInfoGQL

Remove `status_history`, `status_info`, `status_data`, `status_changed` fields.
