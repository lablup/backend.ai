# Plan: BA-5352 — Add PermissionNestedFilterGQL for my_roles / role assignment filtering

## Success Criteria
### PermissionNestedFilterGQL Type Definition
- [x] `PermissionNestedFilterGQL` strawberry input type exists with fields: `scope_id` (str), `scope_type` (RBACElementTypeGQL), `entity_type` (RBACElementTypeGQL), `operation` (OperationTypeGQL), all optional
- [x] AND/OR/NOT logical operators (list[Self]) are supported on the GQL type
- [x] Backing DTO `PermissionNestedFilter` exists in `common/dto/manager/v2/rbac/request.py` with matching fields and AND/OR/NOT

### RoleAssignmentFilter Integration
- [x] `RoleAssignmentFilter` GQL type has a `permission: PermissionNestedFilterGQL | None` field
- [x] `RoleAssignmentFilterDTO` has a corresponding `permission: PermissionNestedFilter | None` field
- [x] Query `{ role_assignments(filter: { permission: { entity_type: USER, operation: READ } }) }` is accepted by the schema (no GQL validation error)

### Adapter Wiring
- [x] `_convert_permission_nested_filter` method added to the RBAC adapter, converts DTO fields to `PermissionConditions.by_scope_id/by_scope_types/by_entity_types/by_operations` conditions
- [x] Raw conditions are wrapped via `AssignedUserConditions.exists_permission_combined(raw_conditions)` to produce an EXISTS subquery correlated to `UserRoleRow`
- [x] `_convert_assignment_filter` calls `_convert_permission_nested_filter` when `f.permission is not None`
- [x] AND/OR/NOT on the permission nested filter are handled recursively (same pattern as `_convert_role_nested_filter`)

### Common
- [x] pants check passes for affected packages (`manager`, `common`)
- [x] pants lint passes for affected packages

## Tasks
- [x] Task 1: Add `PermissionNestedFilter` DTO to `common/dto/manager/v2/rbac/request.py` with fields (scope_id: str, scope_type: str, entity_type: str, operation: str) + AND/OR/NOT + `model_rebuild()`. Add `permission: PermissionNestedFilter | None = None` to `RoleAssignmentFilter` DTO.
- [x] Task 2: Add `PermissionNestedFilterGQL` strawberry input type in `manager/api/gql/rbac/types/role.py` with `@gql_pydantic_input` decorator, `PydanticInputMixin[PermissionNestedFilterDTO]`, fields (scope_id: str, scope_type: RBACElementTypeGQL, entity_type: RBACElementTypeGQL, operation: OperationTypeGQL) + AND/OR/NOT. Add `permission: PermissionNestedFilterGQL | None = None` to `RoleAssignmentFilter` GQL type. Export from `__init__.py`.
- [x] Task 3: Add `_convert_permission_nested_filter` method to RBAC adapter (`manager/api/adapters/rbac.py`). Build raw conditions from PermissionConditions factories, wrap with `exists_permission_combined`, handle AND/OR/NOT recursively. Wire into `_convert_assignment_filter`.
- [x] Task 4: Run `pants check` and `pants lint` on affected packages and fix any issues.
