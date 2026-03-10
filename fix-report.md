# Fix Report: BA-3057 Review Items

## Fix Items

| # | Item | Status | Details |
|---|------|--------|---------|
| 1 | ScalingGroupSchedulerOptions fields need defaults | ✅ Fixed | Added `preemptible_priority: int = 5`, `preemption_order: PreemptionOrder = PreemptionOrder.OLDEST`, `preemption_mode: PreemptionMode = PreemptionMode.TERMINATE` to `data/scaling_group/types.py` |
| 2 | Match exhaustiveness in from_preemption_mode/from_preemption_order | ✅ Fixed | Added `case _: assert_never(mode/order)` fallback branches to both classmethods in `api/gql/resource_group/types.py`. Imported `assert_never` from `typing`. |
| 3 | IndexError risk in resolver.py | ✅ Fixed | Added `if not current_result.scaling_groups: raise ScalingGroupNotFound(input.resource_group_name)` guard before `current_result.scaling_groups[0]` in `admin_update_resource_group`. Added import for `ScalingGroupNotFound`. |

Also fixed: `tests/unit/manager/api/gql/resource_group/test_resource_info.py` fixture was constructing `ResourceGroupSchedulerConfigGQL(type=SchedulerTypeGQL.FIFO)` without the 3 new required fields, causing 3 test errors. Added `preemptible_priority=5`, `preemption_order=PreemptionOrderGQL.OLDEST`, `preemption_mode=PreemptionModeGQL.TERMINATE`.

## Verification Results

| Criterion | Result |
|-----------|--------|
| `pants check src/ai/backend/manager/data/scaling_group/types.py src/ai/backend/manager/api/gql/resource_group/types.py src/ai/backend/manager/api/gql/resource_group/resolver.py tests/unit/manager/api/gql/resource_group/test_resource_info.py` | ✅ No new errors (49 pre-existing `import-not-found` errors in `processors.py` unchanged from main) |
| `pants test tests/unit/manager/data/scaling_group/::` | ✅ Passed (3 tests) |
| `pants test tests/unit/manager/services/scaling_group/::` | ✅ Passed (13+ tests) |
| `pants test tests/unit/manager/api/gql/resource_group/::` | ✅ Passed (10 tests, previously 3 errors) |
| `pants lint src/ai/backend/manager/api/gql/resource_group/::` | ✅ Passed |
