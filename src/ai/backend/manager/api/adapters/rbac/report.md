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
| [when the superadmin soft deletes a role, the id of that role comes back](#deleting-the-superadmin-soft-deletes-a-role) | answered |
| [a user granted nothing cannot soft delete a role](#deleting-a-user-granted-nothing-may-not-soft-delete-a-role) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several roles in one call, none is soft deleted and all come back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles) | answered |
| [when two active roles and a missing id are soft deleted in one call, the two come back in the deleted state and the missing id comes back in the failed list because no target answers to it](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several roles in one call, none is purged and all come back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles) | answered |
| [when the superadmin purges several roles in one call, all come back in the processed list and nothing failed](#partial_bulk_deleting-the-superadmin-purges-several-roles-at-once) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted roles are restored in one call, all come back active](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several roles in one call, none is edited and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles) | answered |
| [when the status of several soft-deleted roles is changed to ACTIVE in one call, they are restored and all come back active](#partial_bulk_editing-editing-status-to-active-restores-several-roles) | answered |
| [when the superadmin changes the description of several roles in one call, all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-roles-at-once) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a role, the id of that role comes back](#deleting-the-superadmin-purges-a-role) | answered |
| [a user granted nothing cannot purge a role](#deleting-a-user-granted-nothing-may-not-purge-a-role) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when a soft-deleted role is restored, the id of that role comes back](#deleting-restoring-a-soft-deleted-role) | answered |
| [a user granted nothing cannot restore a role](#deleting-a-user-granted-nothing-may-not-restore-a-role) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the status of a role to DELETED, it is soft deleted and comes back in the deleted state](#editing-editing-status-to-deleted-soft-deletes-the-role) | answered |
| [when the superadmin changes the description of a role, the whole role carrying the new description comes back](#editing-the-superadmin-edits-a-role) | answered |
| [a user granted nothing cannot edit a role](#editing-a-user-granted-nothing-may-not-edit-a-role) | rejected |

### delete

<a id="deleting-the-superadmin-soft-deletes-a-role"></a>

#### [the-superadmin-soft-deletes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

when the superadmin soft deletes a role, the id of that role comes back

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.delete: user-1 soft deletes role-1

Then

- the id of that role comes back
  - id: same as the id of the target role

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-role"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

a user granted nothing cannot soft delete a role

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.delete: user-1 soft deletes role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-roles"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to soft delete several roles in one call, none is soft deleted and all come back in the failed list for lack of permission

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_delete: user-1 soft deletes 2 roles in one call

Then

- no role is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target role
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target role
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

when two active roles and a missing id are soft deleted in one call, the two come back in the deleted state and the missing id comes back in the failed list because no target answers to it

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_delete: user-1 soft deletes 2 roles and a missing id in one call

Then

- every role comes back in the deleted state and the missing id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: same as the id of the domain the role sits in
  - successes[0].role_preset_id = None
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the role seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[0].deleted_at: the time this run wrote
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.DELETED: 'deleted'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: same as the id of the domain the role sits in
  - successes[1].role_preset_id = None
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the role seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - successes[1].deleted_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id given in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-roles"></a>

#### [a-user-granted-nothing-purges-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to purge several roles in one call, none is purged and all come back in the failed list for lack of permission

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_purge: user-1 purges 2 roles in one call

Then

- no role is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target role
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target role
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-the-superadmin-purges-several-roles-at-once"></a>

#### [the-superadmin-purges-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

when the superadmin purges several roles in one call, all come back in the processed list and nothing failed

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_purge: user-1 purges 2 roles in one call

Then

- every role comes back active and nothing failed
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: same as the id of the domain the role sits in
  - successes[0].role_preset_id = None
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the role seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: same as the id of the domain the role sits in
  - successes[1].role_preset_id = None
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the role seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_deleting.py): pass

when several soft-deleted roles are restored in one call, all come back active

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_restore: user-1 soft deletes 2 roles in one call and then restores them in one call

Then

- every role comes back active and nothing failed
  - successes count = 2
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: same as the id of the domain the role sits in
  - successes[0].role_preset_id = None
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the role seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: same as the id of the domain the role sits in
  - successes[1].role_preset_id = None
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the role seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - successes[1].deleted_at = None
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-roles"></a>

#### [a-user-granted-nothing-edits-none-of-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several roles in one call, none is edited and all come back in the failed list for lack of permission

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_update: user-1 edits the description of 2 roles in one call

Then

- no role is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target role
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target role
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-editing-status-to-active-restores-several-roles"></a>

#### [editing-status-to-active-restores-several-roles](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

when the status of several soft-deleted roles is changed to ACTIVE in one call, they are restored and all come back active

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_update: user-1 soft deletes 2 roles in one call and then changes their status to ACTIVE in one call

Then

- every role comes back active and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = None
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: same as the id of the domain the role sits in
  - successes[0].role_preset_id = None
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the role seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = None
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: same as the id of the domain the role sits in
  - successes[1].role_preset_id = None
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the role seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - successes[1].deleted_at = None

<a id="partial_bulk_editing-the-superadmin-edits-several-roles-at-once"></a>

#### [the-superadmin-edits-several-roles-at-once](/tests/scenario/bai_scenario/manager/rbac/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several roles in one call, all come back with the new description and nothing failed

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.partial_bulk_update: user-1 edits the description of 2 roles in one call

Then

- every role comes back with the new description and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].name = 'role-1'
  - successes[0].description = 'the description edited in one call'
  - successes[0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[0].auto_assign = False
  - successes[0].scope_type = 'domain'
  - successes[0].scope_id: same as the id of the domain the role sits in
  - successes[0].role_preset_id = None
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the role seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[0].deleted_at = None
  - successes[1].name = 'role-2'
  - successes[1].description = 'the description edited in one call'
  - successes[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - successes[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - successes[1].auto_assign = False
  - successes[1].scope_type = 'domain'
  - successes[1].scope_id: same as the id of the domain the role sits in
  - successes[1].role_preset_id = None
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the role seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - successes[1].deleted_at = None

### purge

<a id="deleting-the-superadmin-purges-a-role"></a>

#### [the-superadmin-purges-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

when the superadmin purges a role, the id of that role comes back

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.purge: user-1 purges role-1

Then

- the id of that role comes back
  - id: same as the id of the target role

<a id="deleting-a-user-granted-nothing-may-not-purge-a-role"></a>

#### [a-user-granted-nothing-may-not-purge-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

a user granted nothing cannot purge a role

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.purge: user-1 purges role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### restore

<a id="deleting-restoring-a-soft-deleted-role"></a>

#### [restoring-a-soft-deleted-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

when a soft-deleted role is restored, the id of that role comes back

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.restore: user-1 soft deletes role-1 and then restores it

Then

- the id of that role comes back
  - id: same as the id of the target role

<a id="deleting-a-user-granted-nothing-may-not-restore-a-role"></a>

#### [a-user-granted-nothing-may-not-restore-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

a user granted nothing cannot restore a role

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.restore: user-1 restores role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-editing-status-to-deleted-soft-deletes-the-role"></a>

#### [editing-status-to-deleted-soft-deletes-the-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

when the superadmin changes the status of a role to DELETED, it is soft deleted and comes back in the deleted state

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.update: user-1 changes the status of role-1 to DELETED

Then

- the whole role in the deleted state comes back
  - name = 'role-1'
  - description = None
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.DELETED: 'deleted'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: same as the id of the domain the role sits in
  - role_preset_id = None
  - id: skipped: the database generates it
  - entity_id: same as the id of the role seeded in advance
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at: the time this run wrote

<a id="editing-the-superadmin-edits-a-role"></a>

#### [the-superadmin-edits-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

when the superadmin changes the description of a role, the whole role carrying the new description comes back

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.update: user-1 edits the description of role-1

Then

- the whole role carrying the new description comes back
  - name = 'role-1'
  - description = 'the edited description'
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: same as the id of the domain the role sits in
  - role_preset_id = None
  - id: skipped: the database generates it
  - entity_id: same as the id of the role seeded in advance
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-role"></a>

#### [a-user-granted-nothing-may-not-edit-a-role](/tests/scenario/bai_scenario/manager/rbac/test_editing.py): pass

a user granted nothing cannot edit a role

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.update: user-1 edits the description of role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

