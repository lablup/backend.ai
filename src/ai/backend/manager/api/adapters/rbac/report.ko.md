## rbac

[배경](/src/ai/backend/manager/api/adapters/rbac/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/rbac/adapter.py)

시나리오: 미완성 11 / 37

- ops 구성 (22)
  - admin_search_permissions_gql: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search_roles_gql: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_permissions_by_ids: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - batch_load_permissions_by_role_ids: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_roles_by_ids: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - bulk_add_role_permissions: 대표 성공 ✓ · 대표 거부 ✓
  - bulk_remove_role_permissions: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - create_permission: 대표 성공 ✓ · 대표 거부 ✓
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - my_search_roles: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_delete: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_restore: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - purge_permission: 대표 성공 ✓ · 대표 거부 ✓
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - search_role_permissions: 대표 성공 ✓ · 대표 거부 ✓
  - search_roles_in_scope: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
  - update_permission: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (15)
  - admin_search_role_assignments: 성공 있음 1 · 거부 있음 1 (global_scope)
  - assign_role: 성공 있음 1 · 거부 있음 2 (relation)
  - batch_load_role_assignments_by_ids: 성공 있음 1 · 거부 없음 (scope): SCENARIO-GAP
  - bulk_assign_role: 성공 있음 2 · 거부 있음 1 (relation)
  - bulk_revoke_role: 성공 있음 2 · 거부 있음 1 (relation)
  - get: 성공 있음 1 · 거부 있음 1 (single_entity)
  - get_entity_operation_combinations: 성공 있음 1 · 거부 없음 (public): SCENARIO-GAP
  - get_permission_matrix: 성공 있음 1 · 거부 없음 (public): SCENARIO-GAP
  - get_scope_entity_combinations: 성공 있음 1 · 거부 없음 (public): SCENARIO-GAP
  - my_atomic_bulk_scope_permissions: 성공 있음 1 · 거부 있음 1 (scope)
  - my_scope_permissions: 성공 있음 1 · 거부 있음 1 (scope)
  - my_search_role_assignments: 성공 있음 1 · 거부 있음 1 (scope)
  - replace_role_permissions: 성공 있음 1 · 거부 있음 2 (single_entity)
  - revoke_role: 성공 있음 1 · 거부 있음 2 (relation)
  - search_role_assignments_in_scope: 성공 있음 1 · 거부 있음 1 (scope)

**admin_search_permissions_gql**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 모든 권한을 검색하면, 미리 저장한 권한 행이 모두 옵니다](#searching_permissions-the-superadmin-searches-every-permission) | 성공 |
| [아무 권한도 받지 않은 사용자는 모든 권한을 검색할 수 없습니다](#searching_permissions-a-user-granted-nothing-may-not-search-every-permission) | 거부 |

**admin_search_roles_gql**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 모든 역할을 검색하면, 미리 저장한 역할이 이름 순으로 모두 옵니다](#searching-the-superadmin-searches-every-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 모든 역할을 검색할 수 없습니다](#searching-a-user-granted-nothing-may-not-search-every-role) | 거부 |

**batch_load_permissions_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 권한 둘과 없는 id 하나를 한 번에 읽으면, 권한 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다](#loading-the-superadmin-loads-two-permissions-and-a-missing-id) | 성공 |

**batch_load_permissions_by_role_ids**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 id 로 권한을 한 번에 읽으면, 그 역할이 가진 권한이 옵니다](#loading-a-user-granted-role-read-loads-the-permissions-of-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할 id 로 권한을 한 번에 읽을 수 없습니다](#loading-a-user-granted-nothing-may-not-load-permissions-by-role-id) | 거부 |

**batch_load_roles_by_ids**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 둘과 없는 id 하나를 한 번에 읽으면, 모든 자리가 빈 값으로 옵니다](#loading-a-user-granted-nothing-loads-roles-and-gets-empty-entries) | 성공 |
| [superadmin 이 역할 둘과 없는 id 하나를 한 번에 읽으면, 역할 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다](#loading-the-superadmin-loads-two-roles-and-a-missing-id) | 성공 |

**bulk_add_role_permissions**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 이미 가진 권한과 새 권한을 한 번에 더하면, 새 권한만 더해지고 이미 가진 권한은 실패 목록에 옵니다](#permission_writing-a-user-granted-role-write-adds-one-permission-it-already-holds) | 성공 |
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 더하면, 더한 권한 행이 모두 오고 실패가 없습니다](#permission_writing-a-user-granted-role-write-adds-several-permissions) | 성공 |
| [아무 권한도 받지 않은 사용자는 권한을 한 번에 더할 수 없습니다](#permission_writing-a-user-granted-nothing-may-not-add-permissions) | 거부 |

**bulk_remove_role_permissions**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 권한 둘을 한 번에 빼면, 하나도 빠지지 않고 모두 실패 목록에 옵니다](#permission_writing-a-user-granted-nothing-removes-no-permission) | 성공 |
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 빼면, 뺀 권한 행이 모두 오고 실패가 없습니다](#permission_writing-a-user-granted-role-write-removes-several-permissions) | 성공 |

**create**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 생성 권한을 받은 사용자가 역할을 만들면, 만든 역할 전체가 응답으로 옵니다](#creating-a-user-granted-create-makes-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 만들 수 없습니다](#creating-a-user-granted-nothing-may-not-create-a-role) | 거부 |

**create_permission**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 만들면, 만든 권한 행 전체가 옵니다](#permission_writing-a-user-granted-role-write-creates-a-permission) | 성공 |
| [아무 권한도 받지 않은 사용자는 권한을 만들 수 없습니다](#permission_writing-a-user-granted-nothing-may-not-create-a-permission) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 역할을 soft delete 하면, 그 역할의 id 가 옵니다](#deleting-the-superadmin-soft-deletes-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 soft delete 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-role) | 거부 |
| [대상 도메인에서 역할 수정 권한만 받은 사용자는 역할을 soft delete 할 수 없습니다](#deleting-a-user-granted-update-only-may-not-soft-delete-a-role) | 거부 |

**my_search_roles**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 가진 역할을 검색하면, 그 역할이 옵니다](#searching-a-user-holding-a-role-searches-it) | 성공 |
| [아무 역할도 가진 것이 없는 사용자는 자기가 가진 역할을 검색할 수 없습니다](#searching-a-user-granted-nothing-may-not-search-their-roles) | 거부 |

**partial_bulk_delete**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles) | 성공 |
| [활성 역할 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | 성공 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles) | 성공 |
| [superadmin 이 역할 여럿을 한 번에 purge 하면, 모두 처리된 목록에 오고 실패한 것은 없습니다](#partial_bulk_deleting-the-superadmin-purges-several-roles-at-once) | 성공 |

**partial_bulk_restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 역할 여럿을 한 번에 restore 하면, 모두 활성으로 옵니다](#partial_bulk_deleting-restoring-several-brings-them-back) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles) | 성공 |
| [soft delete 된 역할 여럿의 status 를 한 번에 ACTIVE 로 변경하면, restore 되어 모두 활성으로 옵니다](#partial_bulk_editing-editing-status-to-active-restores-several-roles) | 성공 |
| [superadmin 이 역할 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-roles-at-once) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 역할을 purge 하면, 그 역할의 id 가 옵니다](#deleting-the-superadmin-purges-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 purge 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-purge-a-role) | 거부 |
| [대상 도메인에서 역할 soft delete 권한만 받은 사용자는 역할을 purge 할 수 없습니다](#deleting-a-user-granted-soft-delete-only-may-not-purge-a-role) | 거부 |

**purge_permission**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 purge 하면, 그 권한 행의 id 가 옵니다](#permission_writing-a-user-granted-role-write-purges-a-permission) | 성공 |
| [아무 권한도 받지 않은 사용자는 권한을 purge 할 수 없습니다](#permission_writing-a-user-granted-nothing-may-not-purge-a-permission) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [soft delete 된 역할을 restore 하면, 그 역할의 id 가 옵니다](#deleting-restoring-a-soft-deleted-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 restore 할 수 없습니다](#deleting-a-user-granted-nothing-may-not-restore-a-role) | 거부 |

**search_role_permissions**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할이 가진 권한을 검색하면, 그 역할의 권한 행이 모두 옵니다](#searching_permissions-a-user-granted-role-read-searches-the-permissions-of-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할이 가진 권한을 검색할 수 없습니다](#searching_permissions-a-user-granted-nothing-may-not-search-the-permissions-of-a-role) | 거부 |

**search_roles_in_scope**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기 권한을 받은 사용자가 그 도메인의 역할을 검색하면, 그 도메인의 역할이 모두 옵니다](#searching-a-user-granted-role-read-searches-a-domain) | 성공 |
| [아무 권한도 받지 않은 사용자는 도메인의 역할을 검색할 수 없습니다](#searching-a-user-granted-nothing-may-not-search-a-domain) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 역할의 status 를 DELETED 로 변경하면, soft delete 되어 삭제 상태로 옵니다](#editing-editing-status-to-deleted-soft-deletes-the-role) | 성공 |
| [superadmin 이 역할의 설명을 변경하면, 새 설명을 담은 역할 전체가 응답으로 옵니다](#editing-the-superadmin-edits-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 수정할 수 없습니다](#editing-a-user-granted-nothing-may-not-edit-a-role) | 거부 |
| [대상 도메인에서 역할 조회 권한만 받은 사용자는 역할을 수정할 수 없습니다](#editing-a-user-granted-read-only-may-not-edit-a-role) | 거부 |

**update_permission**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 고치면, 고친 권한 행 전체가 옵니다](#permission_writing-a-user-granted-role-write-updates-a-permission) | 성공 |
| [아무 권한도 받지 않은 사용자는 권한을 고칠 수 없습니다](#permission_writing-a-user-granted-nothing-may-not-update-a-permission) | 거부 |

**admin_search_role_assignments**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 모든 역할 배정을 검색하면, 미리 저장한 사람들의 배정이 모두 옵니다](#searching_assignments-the-superadmin-searches-every-role-assignment) | 성공 |
| [아무 권한도 받지 않은 사용자는 모든 역할 배정을 검색할 수 없습니다](#searching_assignments-a-user-granted-nothing-may-not-search-every-role-assignment) | 거부 |

**assign_role**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 주면, 그 배정 전체가 옵니다](#assigning-a-user-granted-assignment-writes-assigns-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 줄 수 없습니다](#assigning-a-user-granted-nothing-may-not-assign-a-role) | 거부 |
| [이미 역할을 가진 사람에게 같은 역할을 다시 주면 거부됩니다](#assigning-assigning-a-role-the-user-already-holds-is-refused) | 거부 |

**batch_load_role_assignments_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 배정과 없는 id 하나를 한 번에 읽으면, 배정은 노드로, 없는 id 자리는 빈 값으로 옵니다](#loading-the-superadmin-loads-the-assignments-by-id) | 성공 |

**bulk_assign_role**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 여럿에게 한 번에 주면, 모두 배정되고 실패가 없습니다](#assigning-a-user-granted-assignment-writes-assigns-a-role-to-everyone) | 성공 |
| [여럿에게 역할을 한 번에 줄 때 이미 역할을 가진 사람은 실패 목록에 오고 나머지는 배정됩니다](#assigning-assigning-to-several-users-answers-for-the-one-already-holding) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 여럿에게 한 번에 줄 수 없습니다](#assigning-a-user-granted-nothing-may-not-assign-a-role-to-several-users) | 거부 |

**bulk_revoke_role**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 여럿에게서 한 번에 회수하면, 모두 회수되고 실패가 없습니다](#assigning-a-user-granted-revocation-writes-revokes-a-role-from-everyone) | 성공 |
| [여럿에게서 역할을 한 번에 회수할 때 역할을 가지지 않은 사람은 실패 목록에 오고 나머지는 회수됩니다](#assigning-revoking-from-several-users-answers-for-the-one-not-holding) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 여럿에게서 한 번에 회수할 수 없습니다](#assigning-a-user-granted-nothing-may-not-revoke-a-role-from-several-users) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 조회 권한을 받은 사용자가 역할을 읽으면, 미리 저장한 역할 전체가 응답으로 옵니다](#reading-a-user-granted-read-reads-the-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 읽을 수 없습니다](#reading-a-user-granted-nothing-may-not-read-a-role) | 거부 |

**get_entity_operation_combinations**

| 시나리오 | 판정 |
|---|---|
| [아무 역할도 가진 것이 없는 사용자도 역할이 허용할 수 있는 엔티티와 연산을 읽을 수 있습니다](#held_permissions-any-user-reads-the-entity-operation-combinations) | 성공 |

**get_permission_matrix**

| 시나리오 | 판정 |
|---|---|
| [아무 역할도 가진 것이 없는 사용자도 역할 편집기의 권한 표를 읽을 수 있습니다](#held_permissions-any-user-reads-the-permission-matrix) | 성공 |

**get_scope_entity_combinations**

| 시나리오 | 판정 |
|---|---|
| [아무 역할도 가진 것이 없는 사용자도 스코프마다 권한이 지목할 수 있는 엔티티를 읽을 수 있습니다](#held_permissions-any-user-reads-the-scope-entity-combinations) | 성공 |

**my_atomic_bulk_scope_permissions**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프의 역할과 대상 도메인의 세션에 대해 가진 권한을 한 번에 물으면, 자리마다 그 비트가 옵니다](#held_permissions-a-user-holding-a-role-asks-several-scopes-at-once) | 성공 |
| [아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 한 번에 물을 수 없습니다](#held_permissions-a-user-granted-nothing-may-not-ask-several-scopes) | 거부 |

**my_scope_permissions**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프에서 역할에 대해 가진 권한을 물으면, 그 비트가 옵니다](#held_permissions-a-user-holding-a-role-asks-what-they-hold-in-their-own-scope) | 성공 |
| [아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 물을 수 없습니다](#held_permissions-a-user-granted-nothing-may-not-ask-what-they-hold) | 거부 |

**my_search_role_assignments**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기의 역할 배정을 검색하면, 그 배정이 옵니다](#searching_assignments-a-user-holding-a-role-searches-their-assignment) | 성공 |
| [아무 역할도 가진 것이 없는 사용자는 자기의 역할 배정을 검색할 수 없습니다](#searching_assignments-a-user-granted-nothing-may-not-search-their-role-assignment) | 거부 |

**replace_role_permissions**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 역할의 권한을 통째로 바꾸면, 새 권한 행이 모두 오고 실패가 없습니다](#permission_writing-a-user-granted-role-write-replaces-the-permissions) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할의 권한을 통째로 바꿀 수 없습니다](#permission_writing-a-user-granted-nothing-may-not-replace-the-permissions) | 거부 |
| [요청한 역할과 다른 역할의 id 를 단 항목으로 권한을 바꾸려 하면, 요청 전체가 거부됩니다](#permission_writing-replacing-with-an-entry-of-another-role-is-refused) | 거부 |

**revoke_role**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 회수하면, 그 배정 전체가 옵니다](#assigning-a-user-granted-revocation-writes-revokes-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할을 회수할 수 없습니다](#assigning-a-user-granted-nothing-may-not-revoke-a-role) | 거부 |
| [역할을 가지지 않은 사람에게서 그 역할을 회수하면 거부됩니다](#assigning-revoking-a-role-the-user-does-not-hold-is-refused) | 거부 |

**search_role_assignments_in_scope**

| 시나리오 | 판정 |
|---|---|
| [대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 하나의 배정을 검색하면, 그 역할을 받은 사람들의 배정이 모두 옵니다](#searching_assignments-a-user-granted-role-read-searches-the-assignments-of-a-role) | 성공 |
| [아무 권한도 받지 않은 사용자는 역할 하나의 배정을 검색할 수 없습니다](#searching_assignments-a-user-granted-nothing-may-not-search-the-assignments-of-a-role) | 거부 |

### admin_search_permissions_gql

<a id="searching_permissions-the-superadmin-searches-every-permission"></a>

#### [the-superadmin-searches-every-permission](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

superadmin 이 모든 권한을 검색하면, 미리 저장한 권한 행이 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.admin_search_permissions_gql: user-1이 모든 권한을 검색합니다

Then

- 미리 저장한 권한 행이 모두 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].entity_type = 'vfolder'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: 이 실행이 쓴 시각

<a id="searching_permissions-a-user-granted-nothing-may-not-search-every-permission"></a>

#### [a-user-granted-nothing-may-not-search-every-permission](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

아무 권한도 받지 않은 사용자는 모든 권한을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.admin_search_permissions_gql: user-1이 모든 권한을 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_search_roles_gql

<a id="searching-the-superadmin-searches-every-role"></a>

#### [the-superadmin-searches-every-role](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

superadmin 이 모든 역할을 검색하면, 미리 저장한 역할이 이름 순으로 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.admin_search_roles_gql: user-1이 모든 역할을 검색합니다

Then

- 미리 저장한 역할이 이름 순으로 모두 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].name = 'role-1'
  - items[0].description = None
  - items[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[0].auto_assign = False
  - items[0].scope_type = 'domain'
  - items[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - items[0].role_preset_id = None
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].entity_id: 미리 저장한 역할의 id 와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].deleted_at = None
  - items[1].name = 'role-2'
  - items[1].description = None
  - items[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[1].auto_assign = False
  - items[1].scope_type = 'domain'
  - items[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - items[1].role_preset_id = None
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].entity_id: 미리 저장한 역할의 id 와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-every-role"></a>

#### [a-user-granted-nothing-may-not-search-every-role](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

아무 권한도 받지 않은 사용자는 모든 역할을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.admin_search_roles_gql: user-1이 모든 역할을 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_permissions_by_ids

<a id="loading-the-superadmin-loads-two-permissions-and-a-missing-id"></a>

#### [the-superadmin-loads-two-permissions-and-a-missing-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

superadmin 이 권한 둘과 없는 id 하나를 한 번에 읽으면, 권한 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.batch_load_permissions_by_ids: user-1이 권한 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 미리 저장한 권한 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 3
  - [0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - [0].role_id: 미리 저장한 역할의 id 와 같다
  - [0].entity_type = 'session'
  - [0].permission = <PermissionBitDTO.READ: 'read'>
  - [0].created_at: 이 실행이 쓴 시각
  - [1].id: 건너뜀: 데이터베이스가 생성합니다
  - [1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - [1].role_id: 미리 저장한 역할의 id 와 같다
  - [1].entity_type = 'vfolder'
  - [1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [1].created_at: 이 실행이 쓴 시각
  - [2] = None

### batch_load_permissions_by_role_ids

<a id="loading-a-user-granted-role-read-loads-the-permissions-of-a-role"></a>

#### [a-user-granted-role-read-loads-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 id 로 권한을 한 번에 읽으면, 그 역할이 가진 권한이 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.batch_load_permissions_by_role_ids: user-1이 role-1 이 가진 권한을 역할 id 로 한 번에 읽습니다

Then

- 그 역할이 가진 권한이 역할 하나 몫으로 옵니다
  - length = 1
  - [0] length = 2
  - [0][0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0][0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - [0][0].role_id: 미리 저장한 역할의 id 와 같다
  - [0][0].entity_type = 'session'
  - [0][0].permission = <PermissionBitDTO.READ: 'read'>
  - [0][0].created_at: 이 실행이 쓴 시각
  - [0][1].id: 건너뜀: 데이터베이스가 생성합니다
  - [0][1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - [0][1].role_id: 미리 저장한 역할의 id 와 같다
  - [0][1].entity_type = 'vfolder'
  - [0][1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [0][1].created_at: 이 실행이 쓴 시각

<a id="loading-a-user-granted-nothing-may-not-load-permissions-by-role-id"></a>

#### [a-user-granted-nothing-may-not-load-permissions-by-role-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

아무 권한도 받지 않은 사용자는 역할 id 로 권한을 한 번에 읽을 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.batch_load_permissions_by_role_ids: user-1이 role-1 이 가진 권한을 역할 id 로 한 번에 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### batch_load_roles_by_ids

<a id="loading-a-user-granted-nothing-loads-roles-and-gets-empty-entries"></a>

#### [a-user-granted-nothing-loads-roles-and-gets-empty-entries](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

아무 권한도 받지 않은 사용자가 역할 둘과 없는 id 하나를 한 번에 읽으면, 모든 자리가 빈 값으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.batch_load_roles_by_ids: user-1이 역할 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 모든 자리가 빈 값으로 옵니다
  - loaded = [None, None, None]

<a id="loading-the-superadmin-loads-two-roles-and-a-missing-id"></a>

#### [the-superadmin-loads-two-roles-and-a-missing-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

superadmin 이 역할 둘과 없는 id 하나를 한 번에 읽으면, 역할 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.batch_load_roles_by_ids: user-1이 역할 둘과 없는 id 하나를 한 번에 읽습니다

Then

- 미리 저장한 역할 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 3
  - [0].name = 'role-1'
  - [0].description = None
  - [0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - [0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - [0].auto_assign = False
  - [0].scope_type = 'domain'
  - [0].scope_id: 역할을 둔 도메인의 id 와 같다
  - [0].role_preset_id = None
  - [0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0].entity_id: 미리 저장한 역할의 id 와 같다
  - [0].created_at: 이 실행이 쓴 시각
  - [0].updated_at: 이 실행이 쓴 시각
  - [0].deleted_at = None
  - [1].name = 'role-2'
  - [1].description = None
  - [1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - [1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - [1].auto_assign = False
  - [1].scope_type = 'domain'
  - [1].scope_id: 역할을 둔 도메인의 id 와 같다
  - [1].role_preset_id = None
  - [1].id: 건너뜀: 데이터베이스가 생성합니다
  - [1].entity_id: 미리 저장한 역할의 id 와 같다
  - [1].created_at: 이 실행이 쓴 시각
  - [1].updated_at: 이 실행이 쓴 시각
  - [1].deleted_at = None
  - [2] = None

### bulk_add_role_permissions

<a id="permission_writing-a-user-granted-role-write-adds-one-permission-it-already-holds"></a>

#### [a-user-granted-role-write-adds-one-permission-it-already-holds](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 이미 가진 권한과 새 권한을 한 번에 더하면, 새 권한만 더해지고 이미 가진 권한은 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_add_role_permissions: user-1이 role-1 에 이미 가진 세션 읽기 권한과 도메인 만들기 권한을 한 번에 더합니다

Then

- 새 권한만 더해지고 이미 가진 권한은 실패 목록에 옵니다
  - items count = 1
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].entity_type = 'session'
  - failed[0].permission = <PermissionBitDTO.READ: 'read'>
  - failed[0].message: 'Duplicate permission'를 담은 이유

<a id="permission_writing-a-user-granted-role-write-adds-several-permissions"></a>

#### [a-user-granted-role-write-adds-several-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 더하면, 더한 권한 행이 모두 오고 실패가 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_add_role_permissions: user-1이 role-1 에 도메인 만들기와 프로젝트 읽기 권한을 한 번에 더합니다

Then

- 더한 권한 행이 모두 오고 실패가 없습니다
  - items count = 2
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.READ: 'read'>
  - items[1].created_at: 이 실행이 쓴 시각
  - failed = []

<a id="permission_writing-a-user-granted-nothing-may-not-add-permissions"></a>

#### [a-user-granted-nothing-may-not-add-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자는 권한을 한 번에 더할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.bulk_add_role_permissions: user-1이 role-1 에 도메인 만들기와 프로젝트 읽기 권한을 한 번에 더합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### bulk_remove_role_permissions

<a id="permission_writing-a-user-granted-nothing-removes-no-permission"></a>

#### [a-user-granted-nothing-removes-no-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자가 권한 둘을 한 번에 빼면, 하나도 빠지지 않고 모두 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.bulk_remove_role_permissions: user-1이 role-1 의 권한 둘을 한 번에 뺍니다

Then

- 아무 권한 행도 빠지지 않고 대상이 모두 실패 목록에 옵니다
  - items = []
  - failed count = 2
  - failed[0].permission_id: 미리 저장한 권한 행의 id 와 같다
  - failed[0].message: 'permission'를 담은 이유
  - failed[1].permission_id: 미리 저장한 권한 행의 id 와 같다
  - failed[1].message: 'permission'를 담은 이유

<a id="permission_writing-a-user-granted-role-write-removes-several-permissions"></a>

#### [a-user-granted-role-write-removes-several-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 빼면, 뺀 권한 행이 모두 오고 실패가 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_remove_role_permissions: user-1이 role-1 의 권한 둘을 한 번에 뺍니다

Then

- 뺀 권한 행이 모두 오고 실패가 없습니다
  - items count = 2
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].entity_type = 'vfolder'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: 이 실행이 쓴 시각
  - failed = []

### create

<a id="creating-a-user-granted-create-makes-a-role"></a>

#### [a-user-granted-create-makes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_creating.py): pass

대상 도메인에서 역할 생성 권한을 받은 사용자가 역할을 만들면, 만든 역할 전체가 응답으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.create: user-1이 도메인 target-1 에 made-role 역할을 만듭니다

Then

- 만든 역할 전체가 응답으로 옵니다
  - name = 'made-role'
  - description = '새로 만든 역할'
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id 와 같다
  - role_preset_id = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 응답이 실은 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-create-a-role"></a>

#### [a-user-granted-nothing-may-not-create-a-role](/tests/scenario/bai_scenario/manager/rbac/test_creating.py): pass

아무 권한도 받지 않은 사용자는 역할을 만들 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.create: user-1이 도메인 target-1 에 made-role 역할을 만듭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### create_permission

<a id="permission_writing-a-user-granted-role-write-creates-a-permission"></a>

#### [a-user-granted-role-write-creates-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 만들면, 만든 권한 행 전체가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.create_permission: user-1이 role-1 에 세션 soft delete 권한을 더합니다

Then

- 만든 권한 행 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - field_id: 건너뜀: 데이터베이스가 생성합니다
  - role_id: 미리 저장한 역할의 id 와 같다
  - entity_type = 'session'
  - permission = <PermissionBitDTO.SOFT_DELETE: 'soft_delete'>
  - created_at: 이 실행이 쓴 시각

<a id="permission_writing-a-user-granted-nothing-may-not-create-a-permission"></a>

#### [a-user-granted-nothing-may-not-create-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자는 권한을 만들 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.create_permission: user-1이 role-1 에 세션 soft delete 권한을 더합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### delete

<a id="deleting-the-superadmin-soft-deletes-a-role"></a>

#### [the-superadmin-soft-deletes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

superadmin 이 역할을 soft delete 하면, 그 역할의 id 가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.delete: user-1이 role-1 을 soft delete 합니다

Then

- 그 역할의 id 가 옵니다
  - id: 대상 역할의 id 와 같다

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-role"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 soft delete 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.delete: user-1이 role-1 을 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-a-user-granted-update-only-may-not-soft-delete-a-role"></a>

#### [a-user-granted-update-only-may-not-soft-delete-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

대상 도메인에서 역할 수정 권한만 받은 사용자는 역할을 soft delete 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.delete: user-1이 role-1 을 soft delete 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_search_roles

<a id="searching-a-user-holding-a-role-searches-it"></a>

#### [a-user-holding-a-role-searches-it](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 가진 역할을 검색하면, 그 역할이 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 self-role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 self-role-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 self-role-1 보유

When

- RBACAdapter.my_search_roles: user-1이 자기가 가진 역할을 검색합니다

Then

- 호출자가 가진 역할 하나가 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].name = 'self-role-1'
  - items[0].description = None
  - items[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[0].auto_assign = False
  - items[0].scope_type = 'user'
  - items[0].scope_id: 호출자의 id 와 같다
  - items[0].role_preset_id = None
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].entity_id: 미리 저장한 역할의 id 와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-their-roles"></a>

#### [a-user-granted-nothing-may-not-search-their-roles](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

아무 역할도 가진 것이 없는 사용자는 자기가 가진 역할을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.my_search_roles: user-1이 자기가 가진 역할을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_delete: user-1이 역할 2개를 한 번에 soft delete 합니다

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

활성 역할 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_delete: user-1이 역할 2개 와 없는 id 하나를 한 번에 soft delete 합니다

Then

- 역할이 모두 삭제 상태로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at: 이 실행이 쓴 시각
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles"></a>

#### [a-user-granted-nothing-purges-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_purge: user-1이 역할 2개를 한 번에 purge 합니다

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-the-superadmin-purges-several-roles-at-once"></a>

#### [the-superadmin-purges-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

superadmin 이 역할 여럿을 한 번에 purge 하면, 모두 처리된 목록에 오고 실패한 것은 없습니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_purge: user-1이 역할 2개를 한 번에 purge 합니다

Then

- 역할이 모두 활성로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

soft delete 된 역할 여럿을 한 번에 restore 하면, 모두 활성으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_restore: user-1이 역할 2개를 한 번에 soft delete 했다가 한 번에 restore 합니다

Then

- 역할이 모두 활성로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles"></a>

#### [a-user-granted-nothing-edits-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개의 설명을 한 번에 수정합니다

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-editing-status-to-active-restores-several-roles"></a>

#### [editing-status-to-active-restores-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

soft delete 된 역할 여럿의 status 를 한 번에 ACTIVE 로 변경하면, restore 되어 모두 활성으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개를 한 번에 soft delete 했다가 status 를 ACTIVE 로 한 번에 변경합니다

Then

- 역할이 모두 활성으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None

<a id="partial_bulk_editing-the-superadmin-edits-several-roles-at-once"></a>

#### [the-superadmin-edits-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

superadmin 이 역할 여럿의 설명을 한 번에 변경하면, 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개의 설명을 한 번에 수정합니다

Then

- 역할이 모두 새 설명으로 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = '한 번에 수정한 설명'
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[0].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = '한 번에 수정한 설명'
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 건너뜀: 데이터베이스가 생성합니다
  - successes[1].entity_id: 미리 저장한 역할의 id 와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None

### purge

<a id="deleting-the-superadmin-purges-a-role"></a>

#### [the-superadmin-purges-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

superadmin 이 역할을 purge 하면, 그 역할의 id 가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.purge: user-1이 role-1 을 purge 합니다

Then

- 그 역할의 id 가 옵니다
  - id: 대상 역할의 id 와 같다

<a id="deleting-a-user-granted-nothing-may-not-purge-a-role"></a>

#### [a-user-granted-nothing-may-not-purge-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 purge 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.purge: user-1이 role-1 을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-a-user-granted-soft-delete-only-may-not-purge-a-role"></a>

#### [a-user-granted-soft-delete-only-may-not-purge-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

대상 도메인에서 역할 soft delete 권한만 받은 사용자는 역할을 purge 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.purge: user-1이 role-1 을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### purge_permission

<a id="permission_writing-a-user-granted-role-write-purges-a-permission"></a>

#### [a-user-granted-role-write-purges-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 purge 하면, 그 권한 행의 id 가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.purge_permission: user-1이 role-1 의 첫 권한을 purge 합니다

Then

- purge 한 권한 행의 id 가 옵니다
  - id: 미리 저장한 권한 행의 id 와 같다
  - field_id: 미리 저장한 권한 행의 id 와 같다

<a id="permission_writing-a-user-granted-nothing-may-not-purge-a-permission"></a>

#### [a-user-granted-nothing-may-not-purge-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자는 권한을 purge 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.purge_permission: user-1이 role-1 의 첫 권한을 purge 합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### restore

<a id="deleting-restoring-a-soft-deleted-role"></a>

#### [restoring-a-soft-deleted-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

soft delete 된 역할을 restore 하면, 그 역할의 id 가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.restore: user-1이 role-1 을 soft delete 했다가 restore 합니다

Then

- 그 역할의 id 가 옵니다
  - id: 대상 역할의 id 와 같다

<a id="deleting-a-user-granted-nothing-may-not-restore-a-role"></a>

#### [a-user-granted-nothing-may-not-restore-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 restore 할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.restore: user-1이 role-1 을 restore 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_role_permissions

<a id="searching_permissions-a-user-granted-role-read-searches-the-permissions-of-a-role"></a>

#### [a-user-granted-role-read-searches-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할이 가진 권한을 검색하면, 그 역할의 권한 행이 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.search_role_permissions: user-1이 role-1 이 가진 권한을 검색합니다

Then

- 그 역할이 가진 권한 행이 모두 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].entity_type = 'vfolder'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: 이 실행이 쓴 시각

<a id="searching_permissions-a-user-granted-nothing-may-not-search-the-permissions-of-a-role"></a>

#### [a-user-granted-nothing-may-not-search-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

아무 권한도 받지 않은 사용자는 역할이 가진 권한을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.search_role_permissions: user-1이 role-1 이 가진 권한을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### search_roles_in_scope

<a id="searching-a-user-granted-role-read-searches-a-domain"></a>

#### [a-user-granted-role-read-searches-a-domain](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

대상 도메인에서 역할 읽기 권한을 받은 사용자가 그 도메인의 역할을 검색하면, 그 도메인의 역할이 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.search_roles_in_scope: user-1이 도메인 target-1 의 역할을 검색합니다

Then

- 미리 저장한 역할이 이름 순으로 모두 옵니다
  - items count = 3
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False
  - items[0].name = 'grant-1'
  - items[0].description = None
  - items[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[0].auto_assign = False
  - items[0].scope_type = 'domain'
  - items[0].scope_id: 역할을 둔 도메인의 id 와 같다
  - items[0].role_preset_id = None
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].entity_id: 미리 저장한 역할의 id 와 같다
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[0].deleted_at = None
  - items[1].name = 'role-1'
  - items[1].description = None
  - items[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[1].auto_assign = False
  - items[1].scope_type = 'domain'
  - items[1].scope_id: 역할을 둔 도메인의 id 와 같다
  - items[1].role_preset_id = None
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].entity_id: 미리 저장한 역할의 id 와 같다
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각
  - items[1].deleted_at = None
  - items[2].name = 'role-2'
  - items[2].description = None
  - items[2].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[2].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[2].auto_assign = False
  - items[2].scope_type = 'domain'
  - items[2].scope_id: 역할을 둔 도메인의 id 와 같다
  - items[2].role_preset_id = None
  - items[2].id: 건너뜀: 데이터베이스가 생성합니다
  - items[2].entity_id: 미리 저장한 역할의 id 와 같다
  - items[2].created_at: 이 실행이 쓴 시각
  - items[2].updated_at: 이 실행이 쓴 시각
  - items[2].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-a-domain"></a>

#### [a-user-granted-nothing-may-not-search-a-domain](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

아무 권한도 받지 않은 사용자는 도메인의 역할을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.search_roles_in_scope: user-1이 도메인 target-1 의 역할을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-editing-status-to-deleted-soft-deletes-the-role"></a>

#### [editing-status-to-deleted-soft-deletes-the-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

superadmin 이 역할의 status 를 DELETED 로 변경하면, soft delete 되어 삭제 상태로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.update: user-1이 role-1 의 status 를 DELETED 로 변경합니다

Then

- 삭제 상태의 역할 전체가 응답으로 옵니다
  - name = 'role-1'
  - description = None
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.DELETED: 'deleted'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id 와 같다
  - role_preset_id = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 역할의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at: 이 실행이 쓴 시각

<a id="editing-the-superadmin-edits-a-role"></a>

#### [the-superadmin-edits-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

superadmin 이 역할의 설명을 변경하면, 새 설명을 담은 역할 전체가 응답으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.update: user-1이 role-1 의 설명을 수정합니다

Then

- 새 설명을 담은 역할 전체가 응답으로 옵니다
  - name = 'role-1'
  - description = '수정한 설명'
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id 와 같다
  - role_preset_id = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 역할의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-role"></a>

#### [a-user-granted-nothing-may-not-edit-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

아무 권한도 받지 않은 사용자는 역할을 수정할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.update: user-1이 role-1 의 설명을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-a-user-granted-read-only-may-not-edit-a-role"></a>

#### [a-user-granted-read-only-may-not-edit-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

대상 도메인에서 역할 조회 권한만 받은 사용자는 역할을 수정할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.update: user-1이 role-1 의 설명을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update_permission

<a id="permission_writing-a-user-granted-role-write-updates-a-permission"></a>

#### [a-user-granted-role-write-updates-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 고치면, 고친 권한 행 전체가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.update_permission: user-1이 role-1 의 첫 권한을 soft delete 로 바꿉니다

Then

- 고친 권한 행 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - field_id: 건너뜀: 데이터베이스가 생성합니다
  - role_id: 미리 저장한 역할의 id 와 같다
  - entity_type = 'session'
  - permission = <PermissionBitDTO.SOFT_DELETE: 'soft_delete'>
  - created_at: 이 실행이 쓴 시각

<a id="permission_writing-a-user-granted-nothing-may-not-update-a-permission"></a>

#### [a-user-granted-nothing-may-not-update-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자는 권한을 고칠 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.update_permission: user-1이 role-1 의 첫 권한을 soft delete 로 바꿉니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### admin_search_role_assignments

<a id="searching_assignments-the-superadmin-searches-every-role-assignment"></a>

#### [the-superadmin-searches-every-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

superadmin 이 모든 역할 배정을 검색하면, 미리 저장한 사람들의 배정이 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.admin_search_role_assignments: user-1이 모든 역할 배정을 검색합니다

Then

- 미리 저장한 사람들의 역할 배정이 모두 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].user_id: 미리 저장한 사용자의 id 와 같다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].granted_by = None
  - items[0].granted_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].user_id: 미리 저장한 사용자의 id 와 같다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].granted_by = None
  - items[1].granted_at: 이 실행이 쓴 시각

<a id="searching_assignments-a-user-granted-nothing-may-not-search-every-role-assignment"></a>

#### [a-user-granted-nothing-may-not-search-every-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

아무 권한도 받지 않은 사용자는 모든 역할 배정을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유

When

- RBACAdapter.admin_search_role_assignments: user-1이 모든 역할 배정을 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### assign_role

<a id="assigning-a-user-granted-assignment-writes-assigns-a-role"></a>

#### [a-user-granted-assignment-writes-assigns-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 주면, 그 배정 전체가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 CREATE 허용
  - 역할 grant-1: user 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.assign_role: user-1이 user-2 에게 role-1 을 줍니다

Then

- 그 사람과 역할을 잇는 배정 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - user_id: 미리 저장한 사용자의 id 와 같다
  - role_id: 미리 저장한 역할의 id 와 같다
  - granted_by: 역할을 준 사람와 같다
  - granted_at: 이 실행이 쓴 시각

<a id="assigning-a-user-granted-nothing-may-not-assign-a-role"></a>

#### [a-user-granted-nothing-may-not-assign-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

아무 권한도 받지 않은 사용자는 역할을 줄 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.assign_role: user-1이 user-2 에게 role-1 을 줍니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="assigning-assigning-a-role-the-user-already-holds-is-refused"></a>

#### [assigning-a-role-the-user-already-holds-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

이미 역할을 가진 사람에게 같은 역할을 다시 주면 거부됩니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 CREATE 허용
  - 역할 grant-1: user 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.assign_role: user-1이 user-2 에게 role-1 을 줍니다

Then

- 거부됩니다
  - 거부: RoleAlreadyAssigned

### batch_load_role_assignments_by_ids

<a id="loading-the-superadmin-loads-the-assignments-by-id"></a>

#### [the-superadmin-loads-the-assignments-by-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

superadmin 이 미리 저장한 배정과 없는 id 하나를 한 번에 읽으면, 배정은 노드로, 없는 id 자리는 빈 값으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-2: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.batch_load_role_assignments_by_ids: user-1이 미리 저장한 배정을 id 로 한 번에 읽습니다

Then

- 미리 저장한 배정은 노드로, 없는 id 자리는 빈 값으로 옵니다
  - length = 3
  - [0].id: 건너뜀: 데이터베이스가 생성합니다
  - [0].user_id: 미리 저장한 사용자의 id 와 같다
  - [0].role_id: 미리 저장한 역할의 id 와 같다
  - [0].granted_by = None
  - [0].granted_at: 이 실행이 쓴 시각
  - [1].id: 건너뜀: 데이터베이스가 생성합니다
  - [1].user_id: 미리 저장한 사용자의 id 와 같다
  - [1].role_id: 미리 저장한 역할의 id 와 같다
  - [1].granted_by = None
  - [1].granted_at: 이 실행이 쓴 시각
  - [2] = None

### bulk_assign_role

<a id="assigning-a-user-granted-assignment-writes-assigns-a-role-to-everyone"></a>

#### [a-user-granted-assignment-writes-assigns-a-role-to-everyone](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

대상 도메인에서 역할과 사용자에 대한 쓰기 권한을 받은 사용자가 역할을 여럿에게 한 번에 주면, 모두 배정되고 실패가 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 CREATE 허용
  - 역할 grant-1: user 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_assign_role: user-1이 role-1 을 미리 저장한 사람들에게 한 번에 줍니다

Then

- 미리 저장한 사람 모두에게 배정이 가고 실패가 없습니다
  - assigned count = 2
  - failed = []
  - assigned[0].id: 건너뜀: 데이터베이스가 생성합니다
  - assigned[0].user_id: 미리 저장한 사용자의 id 와 같다
  - assigned[0].role_id: 미리 저장한 역할의 id 와 같다
  - assigned[0].granted_by: 역할을 준 사람와 같다
  - assigned[0].granted_at: 이 실행이 쓴 시각
  - assigned[1].id: 건너뜀: 데이터베이스가 생성합니다
  - assigned[1].user_id: 미리 저장한 사용자의 id 와 같다
  - assigned[1].role_id: 미리 저장한 역할의 id 와 같다
  - assigned[1].granted_by: 역할을 준 사람와 같다
  - assigned[1].granted_at: 이 실행이 쓴 시각

<a id="assigning-assigning-to-several-users-answers-for-the-one-already-holding"></a>

#### [assigning-to-several-users-answers-for-the-one-already-holding](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

여럿에게 역할을 한 번에 줄 때 이미 역할을 가진 사람은 실패 목록에 오고 나머지는 배정됩니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 CREATE 허용
  - 역할 grant-1: user 전체에 CREATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_assign_role: user-1이 role-1 을 미리 저장한 사람들에게 한 번에 줍니다

Then

- 역할을 이미 가진 사람만 실패 목록에 오고 나머지는 배정됩니다
  - assigned count = 1
  - failed count = 1
  - assigned[0].id: 건너뜀: 데이터베이스가 생성합니다
  - assigned[0].user_id: 미리 저장한 사용자의 id 와 같다
  - assigned[0].role_id: 미리 저장한 역할의 id 와 같다
  - assigned[0].granted_by: 역할을 준 사람와 같다
  - assigned[0].granted_at: 이 실행이 쓴 시각
  - failed[0].user_id: 미리 저장한 사용자의 id 와 같다
  - failed[0].message: 'already assigned'를 담은 이유

<a id="assigning-a-user-granted-nothing-may-not-assign-a-role-to-several-users"></a>

#### [a-user-granted-nothing-may-not-assign-a-role-to-several-users](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

아무 권한도 받지 않은 사용자는 역할을 여럿에게 한 번에 줄 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.bulk_assign_role: user-1이 role-1 을 미리 저장한 사람들에게 한 번에 줍니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### bulk_revoke_role

<a id="assigning-a-user-granted-revocation-writes-revokes-a-role-from-everyone"></a>

#### [a-user-granted-revocation-writes-revokes-a-role-from-everyone](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 여럿에게서 한 번에 회수하면, 모두 회수되고 실패가 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 SOFT_DELETE 허용
  - 역할 grant-1: user 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_revoke_role: user-1이 role-1 을 미리 저장한 사람들에게서 한 번에 회수합니다

Then

- 미리 저장한 사람 모두에게서 회수되고 실패가 없습니다
  - revoked count = 2
  - failed = []
  - revoked[0].id: 건너뜀: 데이터베이스가 생성합니다
  - revoked[0].user_id: 미리 저장한 사용자의 id 와 같다
  - revoked[0].role_id: 미리 저장한 역할의 id 와 같다
  - revoked[0].granted_by = None
  - revoked[0].granted_at: 이 실행이 쓴 시각
  - revoked[1].id: 건너뜀: 데이터베이스가 생성합니다
  - revoked[1].user_id: 미리 저장한 사용자의 id 와 같다
  - revoked[1].role_id: 미리 저장한 역할의 id 와 같다
  - revoked[1].granted_by = None
  - revoked[1].granted_at: 이 실행이 쓴 시각

<a id="assigning-revoking-from-several-users-answers-for-the-one-not-holding"></a>

#### [revoking-from-several-users-answers-for-the-one-not-holding](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

여럿에게서 역할을 한 번에 회수할 때 역할을 가지지 않은 사람은 실패 목록에 오고 나머지는 회수됩니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 SOFT_DELETE 허용
  - 역할 grant-1: user 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.bulk_revoke_role: user-1이 role-1 을 미리 저장한 사람들에게서 한 번에 회수합니다

Then

- 역할을 가지지 않은 사람만 실패 목록에 오고 나머지는 회수됩니다
  - revoked count = 1
  - failed count = 1
  - failed[0].user_id: 미리 저장한 사용자의 id 와 같다
  - failed[0].message: 'not assigned'를 담은 이유
  - revoked[0].id: 건너뜀: 데이터베이스가 생성합니다
  - revoked[0].user_id: 미리 저장한 사용자의 id 와 같다
  - revoked[0].role_id: 미리 저장한 역할의 id 와 같다
  - revoked[0].granted_by = None
  - revoked[0].granted_at: 이 실행이 쓴 시각

<a id="assigning-a-user-granted-nothing-may-not-revoke-a-role-from-several-users"></a>

#### [a-user-granted-nothing-may-not-revoke-a-role-from-several-users](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

아무 권한도 받지 않은 사용자는 역할을 여럿에게서 한 번에 회수할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유

When

- RBACAdapter.bulk_revoke_role: user-1이 role-1 을 미리 저장한 사람들에게서 한 번에 회수합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-the-role"></a>

#### [a-user-granted-read-reads-the-role](/tests/scenario/bai_scenario/manager/rbac/test_reading.py): pass

대상 도메인에서 역할 조회 권한을 받은 사용자가 역할을 읽으면, 미리 저장한 역할 전체가 응답으로 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.get: user-1이 role-1 의 id 로 역할을 읽습니다

Then

- 미리 저장한 역할 전체가 응답으로 옵니다
  - name = 'role-1'
  - description = None
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id 와 같다
  - role_preset_id = None
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 미리 저장한 역할의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="reading-a-user-granted-nothing-may-not-read-a-role"></a>

#### [a-user-granted-nothing-may-not-read-a-role](/tests/scenario/bai_scenario/manager/rbac/test_reading.py): pass

아무 권한도 받지 않은 사용자는 역할을 읽을 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.get: user-1이 role-1 의 id 로 역할을 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### get_entity_operation_combinations

<a id="held_permissions-any-user-reads-the-entity-operation-combinations"></a>

#### [any-user-reads-the-entity-operation-combinations](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

아무 역할도 가진 것이 없는 사용자도 역할이 허용할 수 있는 엔티티와 연산을 읽을 수 있습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.get_entity_operation_combinations: user-1이 역할이 허용할 수 있는 엔티티와 연산을 읽습니다

Then

- 배선된 엔티티와 그 연산이 이름 순으로 옵니다
  - items: 배선된 엔티티와 그 연산을 모두 싣고 이름 순인 목록

### get_permission_matrix

<a id="held_permissions-any-user-reads-the-permission-matrix"></a>

#### [any-user-reads-the-permission-matrix](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

아무 역할도 가진 것이 없는 사용자도 역할 편집기의 권한 표를 읽을 수 있습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.get_permission_matrix: user-1이 역할 편집기의 권한 표를 읽습니다

Then

- 배선된 스코프와 엔티티, 연산을 모두 실은 표가 옵니다
  - items: 배선된 스코프와 엔티티, 연산을 모두 실은 표

### get_scope_entity_combinations

<a id="held_permissions-any-user-reads-the-scope-entity-combinations"></a>

#### [any-user-reads-the-scope-entity-combinations](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

아무 역할도 가진 것이 없는 사용자도 스코프마다 권한이 지목할 수 있는 엔티티를 읽을 수 있습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.get_scope_entity_combinations: user-1이 스코프마다 권한이 지목할 수 있는 엔티티를 읽습니다

Then

- 스코프마다 지목할 수 있는 엔티티가 이름 순으로 옵니다
  - items: 스코프마다 지목할 수 있는 엔티티를 모두 싣고 이름 순인 목록

### my_atomic_bulk_scope_permissions

<a id="held_permissions-a-user-holding-a-role-asks-several-scopes-at-once"></a>

#### [a-user-holding-a-role-asks-several-scopes-at-once](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프의 역할과 대상 도메인의 세션에 대해 가진 권한을 한 번에 물으면, 자리마다 그 비트가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 self-role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 self-role-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 self-role-1 보유

When

- RBACAdapter.my_atomic_bulk_scope_permissions: user-1이 자기 스코프의 역할과 도메인 target-1 의 세션에 대해 가진 권한을 한 번에 묻습니다

Then

- 대상마다 자리와 호출자가 가진 비트가 옵니다
  - items count = 2
  - items[0].scope_type = 'user'
  - items[0].scope_id: 호출자의 id 와 같다
  - items[0].entity_type = 'role'
  - items[0].permissions = [<PermissionBitDTO.READ: 'read'>]
  - items[1].scope_type = 'domain'
  - items[1].scope_id: 대상 도메인의 id 와 같다
  - items[1].entity_type = 'session'
  - items[1].permissions = []

<a id="held_permissions-a-user-granted-nothing-may-not-ask-several-scopes"></a>

#### [a-user-granted-nothing-may-not-ask-several-scopes](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 한 번에 물을 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.my_atomic_bulk_scope_permissions: user-1이 자기 스코프의 역할과 도메인 target-1 의 세션에 대해 가진 권한을 한 번에 묻습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_scope_permissions

<a id="held_permissions-a-user-holding-a-role-asks-what-they-hold-in-their-own-scope"></a>

#### [a-user-holding-a-role-asks-what-they-hold-in-their-own-scope](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프에서 역할에 대해 가진 권한을 물으면, 그 비트가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 self-role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 self-role-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 self-role-1 보유

When

- RBACAdapter.my_scope_permissions: user-1이 자기 스코프에서 역할에 대해 가진 권한을 묻습니다

Then

- 묻는 대상과 호출자가 가진 비트가 옵니다
  - scope_type = 'user'
  - scope_id: 호출자의 id 와 같다
  - entity_type = 'role'
  - permissions = [<PermissionBitDTO.READ: 'read'>]

<a id="held_permissions-a-user-granted-nothing-may-not-ask-what-they-hold"></a>

#### [a-user-granted-nothing-may-not-ask-what-they-hold](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 물을 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.my_scope_permissions: user-1이 자기 스코프에서 역할에 대해 가진 권한을 묻습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### my_search_role_assignments

<a id="searching_assignments-a-user-holding-a-role-searches-their-assignment"></a>

#### [a-user-holding-a-role-searches-their-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기의 역할 배정을 검색하면, 그 배정이 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 self-role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 self-role-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 self-role-1 보유

When

- RBACAdapter.my_search_role_assignments: user-1이 자기의 역할 배정을 검색합니다

Then

- 호출자가 가진 역할의 배정 하나가 옵니다
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].user_id: 미리 저장한 사용자의 id 와 같다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].granted_by = None
  - items[0].granted_at: 이 실행이 쓴 시각

<a id="searching_assignments-a-user-granted-nothing-may-not-search-their-role-assignment"></a>

#### [a-user-granted-nothing-may-not-search-their-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

아무 역할도 가진 것이 없는 사용자는 자기의 역할 배정을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.my_search_role_assignments: user-1이 자기의 역할 배정을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### replace_role_permissions

<a id="permission_writing-a-user-granted-role-write-replaces-the-permissions"></a>

#### [a-user-granted-role-write-replaces-the-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 역할의 권한을 통째로 바꾸면, 새 권한 행이 모두 오고 실패가 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.replace_role_permissions: user-1이 role-1 의 권한을 도메인 만들기와 프로젝트 읽기로 바꿉니다

Then

- 바꾼 권한 행이 모두 오고 실패가 없습니다
  - items count = 2
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].field_id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.READ: 'read'>
  - items[1].created_at: 이 실행이 쓴 시각
  - failed = []

<a id="permission_writing-a-user-granted-nothing-may-not-replace-the-permissions"></a>

#### [a-user-granted-nothing-may-not-replace-the-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

아무 권한도 받지 않은 사용자는 역할의 권한을 통째로 바꿀 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- RBACAdapter.replace_role_permissions: user-1이 role-1 의 권한을 도메인 만들기와 프로젝트 읽기로 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="permission_writing-replacing-with-an-entry-of-another-role-is-refused"></a>

#### [replacing-with-an-entry-of-another-role-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

요청한 역할과 다른 역할의 id 를 단 항목으로 권한을 바꾸려 하면, 요청 전체가 거부됩니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 role-1: session 전체에 READ 허용
  - 역할 role-1: vfolder 전체에 UPDATE 허용
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 역할 grant-1: role 전체에 UPDATE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.replace_role_permissions: user-1이 role-1 의 권한을 다른 역할의 id 를 단 항목으로 바꾸려 합니다

Then

- 거부됩니다
  - 거부: ReplaceRolePermissionRoleIdMismatch

### revoke_role

<a id="assigning-a-user-granted-revocation-writes-revokes-a-role"></a>

#### [a-user-granted-revocation-writes-revokes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

대상 도메인에서 역할과 사용자에 대한 지우기 권한을 받은 사용자가 역할을 회수하면, 그 배정 전체가 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 SOFT_DELETE 허용
  - 역할 grant-1: user 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.revoke_role: user-1이 user-2 에게서 role-1 을 회수합니다

Then

- 그 사람과 역할을 잇는 배정 전체가 옵니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - user_id: 미리 저장한 사용자의 id 와 같다
  - role_id: 미리 저장한 역할의 id 와 같다
  - granted_by = None
  - granted_at: 이 실행이 쓴 시각

<a id="assigning-a-user-granted-nothing-may-not-revoke-a-role"></a>

#### [a-user-granted-nothing-may-not-revoke-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

아무 권한도 받지 않은 사용자는 역할을 회수할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유

When

- RBACAdapter.revoke_role: user-1이 user-2 에게서 role-1 을 회수합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="assigning-revoking-a-role-the-user-does-not-hold-is-refused"></a>

#### [revoking-a-role-the-user-does-not-hold-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

역할을 가지지 않은 사람에게서 그 역할을 회수하면 거부됩니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 SOFT_DELETE 허용
  - 역할 grant-1: user 전체에 SOFT_DELETE 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.revoke_role: user-1이 user-2 에게서 role-1 을 회수합니다

Then

- 거부됩니다
  - 거부: RoleNotAssigned

### search_role_assignments_in_scope

<a id="searching_assignments-a-user-granted-role-read-searches-the-assignments-of-a-role"></a>

#### [a-user-granted-role-read-searches-the-assignments-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 하나의 배정을 검색하면, 그 역할을 받은 사람들의 배정이 모두 옵니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-3: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 일반 사용자 user-3: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유
  - 일반 사용자 user-3: 역할 role-1 보유
  - 역할 grant-1: 부여된 스코프 안에서만 적용됩니다
  - 역할 grant-1: role 전체에 READ 허용
  - 일반 사용자 user-1: 역할 grant-1 보유

When

- RBACAdapter.search_role_assignments_in_scope: user-1이 role-1 의 역할 배정을 검색합니다

Then

- 그 역할을 받은 사람들의 배정이 모두 옵니다
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: 건너뜀: 데이터베이스가 생성합니다
  - items[0].user_id: 미리 저장한 사용자의 id 와 같다
  - items[0].role_id: 미리 저장한 역할의 id 와 같다
  - items[0].granted_by = None
  - items[0].granted_at: 이 실행이 쓴 시각
  - items[1].id: 건너뜀: 데이터베이스가 생성합니다
  - items[1].user_id: 미리 저장한 사용자의 id 와 같다
  - items[1].role_id: 미리 저장한 역할의 id 와 같다
  - items[1].granted_by = None
  - items[1].granted_at: 이 실행이 쓴 시각

<a id="searching_assignments-a-user-granted-nothing-may-not-search-the-assignments-of-a-role"></a>

#### [a-user-granted-nothing-may-not-search-the-assignments-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

아무 권한도 받지 않은 사용자는 역할 하나의 배정을 검색할 수 없습니다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 부여된 스코프 안에서만 적용됩니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 일반 사용자 user-2: 역할 role-1 보유

When

- RBACAdapter.search_role_assignments_in_scope: user-1이 role-1 의 역할 배정을 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

