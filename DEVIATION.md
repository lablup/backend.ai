# Deviation Report: BA-4897

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| CheckPermissionAction component test | Alternative applied | `check_permission` is not exposed via REST API or client SDK v2. Lifecycle test verifies assignment/revocation via `search_assigned_users` instead. |
| Scope chain (GLOBAL/DOMAIN/USER inheritance through AUTO edges) | Not implemented | Scope chain inheritance is internal service/repository behavior not testable at the HTTP API layer. Scope type discovery is tested instead. |
| Domain + permission integration (cascade behavior) | Alternative applied | Permission CRUD APIs (create_permission, update_role_permissions) are not exposed via REST API. Domain creation requires separate route registration not available in RBAC conftest. Role lifecycle with soft-delete exclusion from search is tested as alternative. |
| GetRoleAction unit test | Not implemented | `PermissionControllerService` has no `get_role` method — only `get_role_detail` exists. `GetRoleDetailAction` is tested instead. |
| CheckPermissionAction unit test | Not implemented | `PermissionControllerService.check_permission` is not a simple service method — it requires complex repository graph traversal that cannot be unit-tested with mocks. |
