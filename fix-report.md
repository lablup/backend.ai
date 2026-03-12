# Fix Report: BA-4999

## Summary

The previous fix left processor/service imports in the component test file and unit test conftest had DB setup issues.

## Fix Items

| Item | Result | Notes |
|------|--------|-------|
| Remove `ScalingGroupProcessors` imports from component test | ✅ Fixed | Replaced with direct DB inserts via `db_engine` + SA tables |
| Remove `_create_sgroup`/`_purge_sgroup` helpers from component test | ✅ Fixed | Added `private_sgroup_for_visibility` fixture using SA table inserts |
| Remove `scaling_group_repository` from component conftest | ✅ Fixed | Unused by remaining component tests |
| Add stub tables to unit test `database_fixture` | ✅ Fixed | sessions/kernels/endpoints/routings created with minimal schemas |
| Add `AssociationScopesEntitiesRow` to `with_tables` | ✅ Fixed | Domain association tests need this table |
| Fix `role="superadmin"` plain string in unit conftest | ✅ Fixed | Use `UserRole.SUPERADMIN` / `UserRole.USER` enum members |

## Verification Results

| Criterion | Status |
|-----------|--------|
| `pants lint tests/component/scaling_group/::` | ✅ Pass |
| `pants check tests/component/scaling_group/::` | ✅ Pass |
| `pants lint tests/unit/manager/services/scaling_group/::` | ✅ Pass |
| `pants check tests/unit/manager/services/scaling_group/::` | ✅ Pass |
| No `ScalingGroupProcessors` or `scaling_group.actions.*` in component test | ✅ Pass |
| `pants test tests/unit/manager/services/scaling_group/test_scaling_group_crud.py` | ✅ Pass (14/14) |
