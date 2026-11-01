## rbac

[background](/src/ai/backend/manager/api/adapters/rbac/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/rbac/adapter.py)

Scenario: incomplete 33 / 37

- built from ops (22)
  - admin_search_permissions_gql: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - admin_search_roles_gql: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_permissions_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_permissions_by_role_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_roles_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_add_role_permissions: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_remove_role_permissions: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create_permission: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✓ · representative rejection ✓
  - my_search_roles: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - purge_permission: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✓ · representative rejection ✓
  - search_role_permissions: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_roles_in_scope: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - update: representative success ✓ · representative rejection ✓
  - update_permission: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (15)
  - admin_search_role_assignments: success absent · rejection absent (global_scope): SCENARIO-GAP
  - assign_role: success absent · rejection absent (relation): SCENARIO-GAP
  - batch_load_role_assignments_by_ids: success absent · rejection absent (scope): SCENARIO-GAP
  - bulk_assign_role: success absent · rejection absent (relation): SCENARIO-GAP
  - bulk_revoke_role: success absent · rejection absent (relation): SCENARIO-GAP
  - get: success absent · rejection absent (single_entity): SCENARIO-GAP
  - get_entity_operation_combinations: success absent · rejection absent (public): SCENARIO-GAP
  - get_permission_matrix: success absent · rejection absent (public): SCENARIO-GAP
  - get_scope_entity_combinations: success absent · rejection absent (public): SCENARIO-GAP
  - my_atomic_bulk_scope_permissions: success absent · rejection absent (scope): SCENARIO-GAP
  - my_scope_permissions: success absent · rejection absent (scope): SCENARIO-GAP
  - my_search_role_assignments: success absent · rejection absent (scope): SCENARIO-GAP
  - replace_role_permissions: success absent · rejection absent (single_entity): SCENARIO-GAP
  - revoke_role: success absent · rejection absent (relation): SCENARIO-GAP
  - search_role_assignments_in_scope: success absent · rejection absent (scope): SCENARIO-GAP

**delete**

| scenario | verdict |
|---|---|
| [슈퍼관리자가 역할을 soft delete 하면, 그 역할의 id 가 온다](#deleting-the-superadmin-soft-deletes-a-role) | answered |
| [아무 권한도 받지 않은 사용자는 역할을 soft delete 할 수 없다](#deleting-a-user-granted-nothing-may-not-soft-delete-a-role) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles) | answered |
| [활성 역할 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles) | answered |
| [슈퍼관리자가 역할 여럿을 한 번에 purge 하면, 모두 처리된 목록에 오고 실패한 것은 없다](#partial_bulk_deleting-the-superadmin-purges-several-roles-at-once) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [soft delete 된 역할 여럿을 한 번에 restore 하면, 모두 활성으로 온다](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles) | answered |
| [soft delete 된 역할 여럿의 status 를 한 번에 ACTIVE 로 고치면, restore 되어 모두 활성으로 온다](#partial_bulk_editing-editing-status-to-active-restores-several-roles) | answered |
| [슈퍼관리자가 역할 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-roles-at-once) | answered |

**purge**

| scenario | verdict |
|---|---|
| [슈퍼관리자가 역할을 purge 하면, 그 역할의 id 가 온다](#deleting-the-superadmin-purges-a-role) | answered |
| [아무 권한도 받지 않은 사용자는 역할을 purge 할 수 없다](#deleting-a-user-granted-nothing-may-not-purge-a-role) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [soft delete 된 역할을 restore 하면, 그 역할의 id 가 온다](#deleting-restoring-a-soft-deleted-role) | answered |
| [아무 권한도 받지 않은 사용자는 역할을 restore 할 수 없다](#deleting-a-user-granted-nothing-may-not-restore-a-role) | rejected |

**update**

| scenario | verdict |
|---|---|
| [슈퍼관리자가 역할의 status 를 DELETED 로 고치면, soft delete 되어 삭제 상태로 온다](#editing-editing-status-to-deleted-soft-deletes-the-role) | answered |
| [슈퍼관리자가 역할의 설명을 바꾸면, 새 설명을 실은 역할 전체가 온다](#editing-the-superadmin-edits-a-role) | answered |
| [아무 권한도 받지 않은 사용자는 역할을 수정할 수 없다](#editing-a-user-granted-nothing-may-not-edit-a-role) | rejected |

### delete

<a id="deleting-the-superadmin-soft-deletes-a-role"></a>

#### [the-superadmin-soft-deletes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

슈퍼관리자가 역할을 soft delete 하면, 그 역할의 id 가 온다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.delete: user-1이 role-1을 soft delete 함

Then

- 그 역할의 id 가 온다
  - id: 대상 역할의 id와 같다

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-role"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 soft delete 할 수 없다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.delete: user-1이 role-1을 soft delete 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 soft delete 하려 하면, soft delete 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_delete: user-1이 역할 2개를 한 번에 soft delete 함

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

활성 역할 둘과 없는 id 하나를 한 번에 soft delete 하면, 둘은 삭제 상태로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_delete: user-1이 역할 2개 와 없는 id 하나를 한 번에 soft delete 함

Then

- 역할이 모두 삭제 상태로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].entity_id: 미리 만든 역할의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at: 이 실행이 쓴 시각
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].entity_id: 미리 만든 역할의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles"></a>

#### [a-user-granted-nothing-purges-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_purge: user-1이 역할 2개를 한 번에 purge 함

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_deleting-the-superadmin-purges-several-roles-at-once"></a>

#### [the-superadmin-purges-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

슈퍼관리자가 역할 여럿을 한 번에 purge 하면, 모두 처리된 목록에 오고 실패한 것은 없다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_purge: user-1이 역할 2개를 한 번에 purge 함

Then

- 역할이 모두 활성로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].entity_id: 미리 만든 역할의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].entity_id: 미리 만든 역할의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

soft delete 된 역할 여럿을 한 번에 restore 하면, 모두 활성으로 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_restore: user-1이 역할 2개를 한 번에 soft delete 했다가 한 번에 restore 함

Then

- 역할이 모두 활성로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].entity_id: 미리 만든 역할의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].entity_id: 미리 만든 역할의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles"></a>

#### [a-user-granted-nothing-edits-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 역할 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개의 설명을 한 번에 고침

Then

- 처리된 역할 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 역할의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 역할의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-editing-status-to-active-restores-several-roles"></a>

#### [editing-status-to-active-restores-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

soft delete 된 역할 여럿의 status 를 한 번에 ACTIVE 로 고치면, restore 되어 모두 활성으로 온다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개를 한 번에 soft delete 했다가 status 를 ACTIVE 로 한 번에 고침

Then

- 역할이 모두 활성으로 오고, 실패한 것은 없다
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].entity_id: 미리 만든 역할의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].entity_id: 미리 만든 역할의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None

<a id="partial_bulk_editing-the-superadmin-edits-several-roles-at-once"></a>

#### [the-superadmin-edits-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

슈퍼관리자가 역할 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다

Given

- 한 도메인에 둔 커스텀 역할 2개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 역할 role-2: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.partial_bulk_update: user-1이 역할 2개의 설명을 한 번에 고침

Then

- 역할이 모두 새 설명으로 오고, 실패한 것은 없다
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = '한 번에 고친 설명'
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[0].role_preset_id = None
  - successes[0].id: 무시함: 데이터베이스가 만든다
  - successes[0].entity_id: 미리 만든 역할의 id와 같다
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = '한 번에 고친 설명'
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: 역할을 둔 도메인의 id와 같다
  - successes[1].role_preset_id = None
  - successes[1].id: 무시함: 데이터베이스가 만든다
  - successes[1].entity_id: 미리 만든 역할의 id와 같다
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - successes[1].deleted_at = None

### purge

<a id="deleting-the-superadmin-purges-a-role"></a>

#### [the-superadmin-purges-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

슈퍼관리자가 역할을 purge 하면, 그 역할의 id 가 온다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.purge: user-1이 role-1을 purge 함

Then

- 그 역할의 id 가 온다
  - id: 대상 역할의 id와 같다

<a id="deleting-a-user-granted-nothing-may-not-purge-a-role"></a>

#### [a-user-granted-nothing-may-not-purge-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 purge 할 수 없다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.purge: user-1이 role-1을 purge 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### restore

<a id="deleting-restoring-a-soft-deleted-role"></a>

#### [restoring-a-soft-deleted-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

soft delete 된 역할을 restore 하면, 그 역할의 id 가 온다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.restore: user-1이 role-1을 soft delete 했다가 restore 함

Then

- 그 역할의 id 가 온다
  - id: 대상 역할의 id와 같다

<a id="deleting-a-user-granted-nothing-may-not-restore-a-role"></a>

#### [a-user-granted-nothing-may-not-restore-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

아무 권한도 받지 않은 사용자는 역할을 restore 할 수 없다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.restore: user-1이 role-1을 restore 함

Then

- 거부된다
  - 거부: NotEnoughPermission

### update

<a id="editing-editing-status-to-deleted-soft-deletes-the-role"></a>

#### [editing-status-to-deleted-soft-deletes-the-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

슈퍼관리자가 역할의 status 를 DELETED 로 고치면, soft delete 되어 삭제 상태로 온다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.update: user-1이 role-1의 status 를 DELETED 로 고침

Then

- 삭제 상태의 역할 전체가 온다
  - name = 'role-1'
  - description = None
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.DELETED: 'deleted'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id와 같다
  - role_preset_id = None
  - id: 무시함: 데이터베이스가 만든다
  - entity_id: 미리 만든 역할의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at: 이 실행이 쓴 시각

<a id="editing-the-superadmin-edits-a-role"></a>

#### [the-superadmin-edits-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

슈퍼관리자가 역할의 설명을 바꾸면, 새 설명을 실은 역할 전체가 온다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 superadmin 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.update: user-1이 role-1의 설명을 고침

Then

- 새 설명을 실은 역할 전체가 온다
  - name = 'role-1'
  - description = '고친 설명'
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: 역할을 둔 도메인의 id와 같다
  - role_preset_id = None
  - id: 무시함: 데이터베이스가 만든다
  - entity_id: 미리 만든 역할의 id와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-role"></a>

#### [a-user-granted-nothing-may-not-edit-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

아무 권한도 받지 않은 사용자는 역할을 수정할 수 없다

Given

- 한 도메인에 둔 커스텀 역할 1개와, 다른 도메인에 사는 user 한 명
  - 도메인 home-1
  - 도메인 target-1
  - 역할 role-1: 이 역할이 앉은 스코프 안에서만 통한다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- RBACAdapter.update: user-1이 role-1의 설명을 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

