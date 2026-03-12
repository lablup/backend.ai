# Deviation Report: BA-4999

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Purge with active sessions → blocked with error | Not implemented | The current `purge_scaling_group` implementation (db_source.py) forcefully deletes all sessions, kernels, and endpoints before deleting the scaling group. There is no guard that blocks purge when active sessions exist. The test scenario was based on an assumed future constraint that is not present in the codebase. |
| Regular user cannot create/purge scaling group → 403 | Alternative applied | Scaling group CRUD (create/modify/purge) is only exposed through the legacy GraphQL API, which enforces `allowed_roles = (UserRole.SUPERADMIN,)`. The REST API v2 has no create/modify/purge endpoints, so 403 testing at the REST layer is not applicable. `TestScalingGroupPermissions` documents this contract and verifies that list operations work correctly for regular users (the only REST-exposed read endpoint). |
