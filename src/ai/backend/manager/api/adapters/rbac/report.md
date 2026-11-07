## rbac

[background](/src/ai/backend/manager/api/adapters/rbac/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/rbac/adapter.py)

Scenario: incomplete 11 / 37

- built from ops (22)
  - admin_search_permissions_gql: representative success ✓ · representative rejection ✓
  - admin_search_roles_gql: representative success ✓ · representative rejection ✓
  - batch_load_permissions_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - batch_load_permissions_by_role_ids: representative success ✓ · representative rejection ✓
  - batch_load_roles_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - bulk_add_role_permissions: representative success ✓ · representative rejection ✓
  - bulk_remove_role_permissions: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✓ · representative rejection ✓
  - create_permission: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - my_search_roles: representative success ✓ · representative rejection ✓
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - purge_permission: representative success ✓ · representative rejection ✓
  - restore: representative success ✓ · representative rejection ✓
  - search_role_permissions: representative success ✓ · representative rejection ✓
  - search_roles_in_scope: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
  - update_permission: representative success ✓ · representative rejection ✓
- direct implementation (15)
  - admin_search_role_assignments: success present 1 · rejection present 1 (global_scope)
  - assign_role: success present 1 · rejection present 2 (relation)
  - batch_load_role_assignments_by_ids: success present 1 · rejection absent (scope): SCENARIO-GAP
  - bulk_assign_role: success present 2 · rejection present 1 (relation)
  - bulk_revoke_role: success present 2 · rejection present 1 (relation)
  - get: success present 1 · rejection present 1 (single_entity)
  - get_entity_operation_combinations: success present 1 · rejection absent (public): SCENARIO-GAP
  - get_permission_matrix: success present 1 · rejection absent (public): SCENARIO-GAP
  - get_scope_entity_combinations: success present 1 · rejection absent (public): SCENARIO-GAP
  - my_atomic_bulk_scope_permissions: success present 1 · rejection present 1 (scope)
  - my_scope_permissions: success present 1 · rejection present 1 (scope)
  - my_search_role_assignments: success present 1 · rejection present 1 (scope)
  - replace_role_permissions: success present 1 · rejection present 2 (single_entity)
  - revoke_role: success present 1 · rejection present 2 (relation)
  - search_role_assignments_in_scope: success present 1 · rejection present 1 (scope)

**admin_search_permissions_gql**

| scenario | verdict |
|---|---|
| [when the superadmin searches every permission filtered to one entity type, every permission row the filter keeps comes back. The global role gates this search](#searching_permissions-the-superadmin-searches-every-permission) | answered |
| [a user granted nothing cannot search every permission](#searching_permissions-a-user-granted-nothing-may-not-search-every-permission) | rejected |

**admin_search_roles_gql**

| scenario | verdict |
|---|---|
| [when the superadmin searches roles leaving one role's name out, the roles the filter keeps come back in name order. The global role gates this search](#searching-the-superadmin-searches-every-role) | answered |
| [a user granted nothing cannot search every role](#searching-a-user-granted-nothing-may-not-search-every-role) | rejected |

**batch_load_permissions_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted nothing loads two permission rows and one missing id in one call, every entry comes back empty](#loading-a-user-granted-nothing-loads-permissions-and-gets-empty-entries) | answered |
| [when the superadmin loads two permission rows and one missing id in one call, the two rows come back as nodes and the missing id as an empty value](#loading-the-superadmin-loads-two-permissions-and-a-missing-id) | answered |

**batch_load_permissions_by_role_ids**

| scenario | verdict |
|---|---|
| [when a user granted role read permission in a domain loads permissions by role id, the permissions that role holds come back](#loading-a-user-granted-role-read-loads-the-permissions-of-a-role) | answered |
| [a user granted nothing cannot load permissions by role id](#loading-a-user-granted-nothing-may-not-load-permissions-by-role-id) | rejected |

**batch_load_roles_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted nothing loads two roles and one missing id in one call, every entry comes back empty](#loading-a-user-granted-nothing-loads-roles-and-gets-empty-entries) | answered |
| [when the superadmin loads two roles and one missing id in one call, the two roles come back as nodes and the missing id as an empty value](#loading-the-superadmin-loads-two-roles-and-a-missing-id) | answered |

**bulk_add_role_permissions**

| scenario | verdict |
|---|---|
| [when a user granted role read and update permissions in a domain adds a permission the role already holds and a new one in one call, only the new one is added and the one already held comes back failed](#permission_writing-a-user-granted-role-write-adds-one-permission-it-already-holds) | answered |
| [when a user granted role read and update permissions in a domain adds two permissions in one call, every row added comes back and nothing failed](#permission_writing-a-user-granted-role-write-adds-several-permissions) | answered |
| [a user granted only role read permission in a domain cannot add permissions in one call](#permission_writing-a-user-granted-read-only-may-not-add-permissions) | rejected |

**bulk_remove_role_permissions**

| scenario | verdict |
|---|---|
| [when a user granted only role read permission in a domain removes two permissions in one call, none is removed and both come back in the failed list](#permission_writing-a-user-granted-read-only-removes-no-permission) | answered |
| [when a user granted role read and update permissions in a domain removes two permissions in one call, every row removed comes back and nothing failed](#permission_writing-a-user-granted-role-write-removes-several-permissions) | answered |

**create**

| scenario | verdict |
|---|---|
| [when a user granted role create permission in a domain creates a role, the whole role just created comes back](#creating-a-user-granted-create-makes-a-role) | answered |
| [a user granted nothing cannot create a role](#creating-a-user-granted-nothing-may-not-create-a-role) | rejected |

**create_permission**

| scenario | verdict |
|---|---|
| [when a user granted role read and update permissions in a domain creates a permission, the whole permission row just created comes back](#permission_writing-a-user-granted-role-write-creates-a-permission) | answered |
| [a user granted only role read permission in a domain cannot create a permission](#permission_writing-a-user-granted-read-only-may-not-create-a-permission) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes a role, the id of that role comes back](#deleting-the-superadmin-soft-deletes-a-role) | answered |
| [a user granted nothing cannot soft delete a role](#deleting-a-user-granted-nothing-may-not-soft-delete-a-role) | rejected |
| [a user granted only role update permission in a domain cannot soft delete a role](#deleting-a-user-granted-update-only-may-not-soft-delete-a-role) | rejected |

**my_search_roles**

| scenario | verdict |
|---|---|
| [when a user holding a role with role read permission in their own scope searches the roles they hold by one name, that role comes back and neither the other user's role nor the other held role is listed](#searching-a-user-holding-a-role-searches-it) | answered |
| [a user holding no role cannot search the roles they hold](#searching-a-user-granted-nothing-may-not-search-their-roles) | rejected |

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
| [a user granted only role soft delete permission in a domain cannot purge a role](#deleting-a-user-granted-soft-delete-only-may-not-purge-a-role) | rejected |

**purge_permission**

| scenario | verdict |
|---|---|
| [when a user granted role read and update permissions in a domain purges a permission, the id of that permission row comes back](#permission_writing-a-user-granted-role-write-purges-a-permission) | answered |
| [a user granted only role read permission in a domain cannot purge a permission](#permission_writing-a-user-granted-read-only-may-not-purge-a-permission) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when a soft-deleted role is restored, the id of that role comes back](#deleting-restoring-a-soft-deleted-role) | answered |
| [a user granted nothing cannot restore a role](#deleting-a-user-granted-nothing-may-not-restore-a-role) | rejected |

**search_role_permissions**

| scenario | verdict |
|---|---|
| [when a user granted role read permission in a domain searches the permissions a role holds filtered to one entity type, every permission row the filter keeps comes back](#searching_permissions-a-user-granted-role-read-searches-the-permissions-of-a-role) | answered |
| [a user granted nothing cannot search the permissions a role holds](#searching_permissions-a-user-granted-nothing-may-not-search-the-permissions-of-a-role) | rejected |

**search_roles_in_scope**

| scenario | verdict |
|---|---|
| [when a user granted role read permission in a domain searches the roles of that domain leaving one role's name out, the roles the filter keeps come back in name order](#searching-a-user-granted-role-read-searches-a-domain) | answered |
| [a user granted nothing cannot search the roles of a domain](#searching-a-user-granted-nothing-may-not-search-a-domain) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the status of a role to DELETED, it is soft deleted and comes back in the deleted state](#editing-editing-status-to-deleted-soft-deletes-the-role) | answered |
| [when the superadmin changes the description of a role, the whole role carrying the new description comes back](#editing-the-superadmin-edits-a-role) | answered |
| [a user granted nothing cannot edit a role](#editing-a-user-granted-nothing-may-not-edit-a-role) | rejected |

**update_permission**

| scenario | verdict |
|---|---|
| [when a user granted role read and update permissions in a domain changes a permission, the whole permission row just changed comes back](#permission_writing-a-user-granted-role-write-updates-a-permission) | answered |
| [a user granted only role read permission in a domain cannot change a permission](#permission_writing-a-user-granted-read-only-may-not-update-a-permission) | rejected |

**admin_search_role_assignments**

| scenario | verdict |
|---|---|
| [when the superadmin searches role assignments naming one seeded user, only that user's assignment comes back. The global role gates this search](#searching_assignments-the-superadmin-searches-every-role-assignment) | answered |
| [a user granted nothing cannot search every role assignment](#searching_assignments-a-user-granted-nothing-may-not-search-every-role-assignment) | rejected |

**assign_role**

| scenario | verdict |
|---|---|
| [when a user granted write permission on the role and the user gives a role, the whole assignment comes back](#assigning-a-user-granted-assignment-writes-assigns-a-role) | answered |
| [a user granted nothing cannot give a role](#assigning-a-user-granted-nothing-may-not-assign-a-role) | rejected |
| [giving a role to a user who already holds it is rejected](#assigning-assigning-a-role-the-user-already-holds-is-refused) | rejected |

**batch_load_role_assignments_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin loads the assignments seeded in advance and one missing id in one call, the assignments come back as nodes and the missing id as an empty value](#loading-the-superadmin-loads-the-assignments-by-id) | answered |

**bulk_assign_role**

| scenario | verdict |
|---|---|
| [when a user granted write permission on the role and the users gives a role to several users in one call, everyone is assigned and nothing failed](#assigning-a-user-granted-assignment-writes-assigns-a-role-to-everyone) | answered |
| [when a role is given to several users in one call, the user who already holds it comes back failed and the rest are assigned](#assigning-assigning-to-several-users-answers-for-the-one-already-holding) | answered |
| [a user granted nothing cannot give a role to several users in one call](#assigning-a-user-granted-nothing-may-not-assign-a-role-to-several-users) | rejected |

**bulk_revoke_role**

| scenario | verdict |
|---|---|
| [when a user granted delete permission on the role and the users takes a role back from several users in one call, everyone is revoked and nothing failed](#assigning-a-user-granted-revocation-writes-revokes-a-role-from-everyone) | answered |
| [when a role is taken back from several users in one call, the user who did not hold it comes back failed and the rest are taken back](#assigning-revoking-from-several-users-answers-for-the-one-not-holding) | answered |
| [a user granted nothing cannot take a role back from several users in one call](#assigning-a-user-granted-nothing-may-not-revoke-a-role-from-several-users) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted role read permission in a domain reads a role, the whole role seeded in advance comes back](#reading-a-user-granted-read-reads-the-role) | answered |
| [a user granted nothing cannot read a role](#reading-a-user-granted-nothing-may-not-read-a-role) | rejected |

**get_entity_operation_combinations**

| scenario | verdict |
|---|---|
| [a user holding no role can still read the entities and operations a role may permit](#held_permissions-any-user-reads-the-entity-operation-combinations) | answered |

**get_permission_matrix**

| scenario | verdict |
|---|---|
| [a user holding no role can still read the permission matrix of the role editor](#held_permissions-any-user-reads-the-permission-matrix) | answered |

**get_scope_entity_combinations**

| scenario | verdict |
|---|---|
| [a user holding no role can still read the entities a permission may name in each scope](#held_permissions-any-user-reads-the-scope-entity-combinations) | answered |

**my_atomic_bulk_scope_permissions**

| scenario | verdict |
|---|---|
| [when a user holding a role with role read permission in their own scope asks in one call about roles there and sessions in a target domain, the bits come back for each target](#held_permissions-a-user-holding-a-role-asks-several-scopes-at-once) | answered |
| [a user holding no role cannot ask in one call what permissions they hold in their own scope](#held_permissions-a-user-granted-nothing-may-not-ask-several-scopes) | rejected |

**my_scope_permissions**

| scenario | verdict |
|---|---|
| [when a user holding a role with role read permission in their own scope asks what they hold on roles there, that bit comes back](#held_permissions-a-user-holding-a-role-asks-what-they-hold-in-their-own-scope) | answered |
| [a user holding no role cannot ask what permissions they hold in their own scope](#held_permissions-a-user-granted-nothing-may-not-ask-what-they-hold) | rejected |

**my_search_role_assignments**

| scenario | verdict |
|---|---|
| [when a user holding a role with role read permission in their own scope searches their own role assignments filtered to one role, that assignment comes back and neither their other role nor another user's assignment is listed](#searching_assignments-a-user-holding-a-role-searches-their-assignment) | answered |
| [a user holding no role cannot search their own role assignments](#searching_assignments-a-user-granted-nothing-may-not-search-their-role-assignment) | rejected |

**replace_role_permissions**

| scenario | verdict |
|---|---|
| [when a user granted role read and update permissions in a domain replaces the permission set of a role, every new permission row comes back and nothing failed](#permission_writing-a-user-granted-role-write-replaces-the-permissions) | answered |
| [a user granted only role read permission in a domain cannot replace the permission set of a role](#permission_writing-a-user-granted-read-only-may-not-replace-the-permissions) | rejected |
| [when the request names one role and an entry names another, the whole request is rejected](#permission_writing-replacing-with-an-entry-of-another-role-is-refused) | rejected |

**revoke_role**

| scenario | verdict |
|---|---|
| [when a user granted delete permission on the role and the user takes a role back, the whole assignment comes back](#assigning-a-user-granted-revocation-writes-revokes-a-role) | answered |
| [a user granted nothing cannot take a role back](#assigning-a-user-granted-nothing-may-not-revoke-a-role) | rejected |
| [taking a role back from a user who does not hold it is rejected](#assigning-revoking-a-role-the-user-does-not-hold-is-refused) | rejected |

**search_role_assignments_in_scope**

| scenario | verdict |
|---|---|
| [when a user granted role read permission in a domain searches the assignments of one role naming one seeded user, only that user's assignment comes back](#searching_assignments-a-user-granted-role-read-searches-the-assignments-of-a-role) | answered |
| [a user granted nothing cannot search the assignments of a role](#searching_assignments-a-user-granted-nothing-may-not-search-the-assignments-of-a-role) | rejected |

### admin_search_permissions_gql

<a id="searching_permissions-the-superadmin-searches-every-permission"></a>

#### [the-superadmin-searches-every-permission](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

when the superadmin searches every permission filtered to one entity type, every permission row the filter keeps comes back. The global role gates this search

Given

- 1 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.admin_search_permissions_gql: user-1 searches every permission

Then

- every permission row the filter keeps comes back
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: the time this run wrote

<a id="searching_permissions-a-user-granted-nothing-may-not-search-every-permission"></a>

#### [a-user-granted-nothing-may-not-search-every-permission](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

a user granted nothing cannot search every permission

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.admin_search_permissions_gql: user-1 searches every permission

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_roles_gql

<a id="searching-the-superadmin-searches-every-role"></a>

#### [the-superadmin-searches-every-role](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

when the superadmin searches roles leaving one role's name out, the roles the filter keeps come back in name order. The global role gates this search

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role excluded-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RBACAdapter.admin_search_roles_gql: user-1 searches every role

Then

- the roles the filter keeps come back in name order
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
  - items[0].scope_id: same as the id of the domain the role sits in
  - items[0].role_preset_id = None
  - items[0].id: skipped: the database generates it
  - items[0].entity_id: same as the id of the role seeded in advance
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].deleted_at = None
  - items[1].name = 'role-2'
  - items[1].description = None
  - items[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[1].auto_assign = False
  - items[1].scope_type = 'domain'
  - items[1].scope_id: same as the id of the domain the role sits in
  - items[1].role_preset_id = None
  - items[1].id: skipped: the database generates it
  - items[1].entity_id: same as the id of the role seeded in advance
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-every-role"></a>

#### [a-user-granted-nothing-may-not-search-every-role](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

a user granted nothing cannot search every role

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

- RBACAdapter.admin_search_roles_gql: user-1 searches every role

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_permissions_by_ids

<a id="loading-a-user-granted-nothing-loads-permissions-and-gets-empty-entries"></a>

#### [a-user-granted-nothing-loads-permissions-and-gets-empty-entries](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when a user granted nothing loads two permission rows and one missing id in one call, every entry comes back empty

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_permissions_by_ids: user-1 loads two permission rows and one missing id in one call

Then

- every entry comes back empty
  - loaded = [None, None, None]

<a id="loading-the-superadmin-loads-two-permissions-and-a-missing-id"></a>

#### [the-superadmin-loads-two-permissions-and-a-missing-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when the superadmin loads two permission rows and one missing id in one call, the two rows come back as nodes and the missing id as an empty value

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_permissions_by_ids: user-1 loads two permission rows and one missing id in one call

Then

- the two permission rows seeded in advance come back as nodes and the missing id as an empty value
  - length = 3
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].role_id: same as the id of the role seeded in advance
  - [0].entity_type = 'session'
  - [0].permission = <PermissionBitDTO.READ: 'read'>
  - [0].created_at: the time this run wrote
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].role_id: same as the id of the role seeded in advance
  - [1].entity_type = 'vfolder'
  - [1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [1].created_at: the time this run wrote
  - [2] = None

### batch_load_permissions_by_role_ids

<a id="loading-a-user-granted-role-read-loads-the-permissions-of-a-role"></a>

#### [a-user-granted-role-read-loads-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when a user granted role read permission in a domain loads permissions by role id, the permissions that role holds come back

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.batch_load_permissions_by_role_ids: user-1 loads the permissions of role-1 by role id in one call

Then

- the permissions that role holds come back as the one role's list
  - length = 1
  - [0] length = 2
  - [0][0].id: skipped: the database generates it
  - [0][0].field_id: skipped: the database generates it
  - [0][0].role_id: same as the id of the role seeded in advance
  - [0][0].entity_type = 'session'
  - [0][0].permission = <PermissionBitDTO.READ: 'read'>
  - [0][0].created_at: the time this run wrote
  - [0][1].id: skipped: the database generates it
  - [0][1].field_id: skipped: the database generates it
  - [0][1].role_id: same as the id of the role seeded in advance
  - [0][1].entity_type = 'vfolder'
  - [0][1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [0][1].created_at: the time this run wrote

<a id="loading-a-user-granted-nothing-may-not-load-permissions-by-role-id"></a>

#### [a-user-granted-nothing-may-not-load-permissions-by-role-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

a user granted nothing cannot load permissions by role id

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_permissions_by_role_ids: user-1 loads the permissions of role-1 by role id in one call

Then

- the call is rejected
  - rejected: NotEnoughPermission

### batch_load_roles_by_ids

<a id="loading-a-user-granted-nothing-loads-roles-and-gets-empty-entries"></a>

#### [a-user-granted-nothing-loads-roles-and-gets-empty-entries](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when a user granted nothing loads two roles and one missing id in one call, every entry comes back empty

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_roles_by_ids: user-1 loads two roles and one missing id in one call

Then

- every entry comes back empty
  - loaded = [None, None, None]

<a id="loading-the-superadmin-loads-two-roles-and-a-missing-id"></a>

#### [the-superadmin-loads-two-roles-and-a-missing-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when the superadmin loads two roles and one missing id in one call, the two roles come back as nodes and the missing id as an empty value

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_roles_by_ids: user-1 loads two roles and one missing id in one call

Then

- the two roles seeded in advance come back as nodes and the missing id as an empty value
  - length = 3
  - [0].name = 'role-1'
  - [0].description = None
  - [0].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - [0].status = <RoleStatusDTO.ACTIVE: 'active'>
  - [0].auto_assign = False
  - [0].scope_type = 'domain'
  - [0].scope_id: same as the id of the domain the role sits in
  - [0].role_preset_id = None
  - [0].id: skipped: the database generates it
  - [0].entity_id: same as the id of the role seeded in advance
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [0].deleted_at = None
  - [1].name = 'role-2'
  - [1].description = None
  - [1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - [1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - [1].auto_assign = False
  - [1].scope_type = 'domain'
  - [1].scope_id: same as the id of the domain the role sits in
  - [1].role_preset_id = None
  - [1].id: skipped: the database generates it
  - [1].entity_id: same as the id of the role seeded in advance
  - [1].created_at: the time this run wrote
  - [1].updated_at: the time this run wrote
  - [1].deleted_at = None
  - [2] = None

### bulk_add_role_permissions

<a id="permission_writing-a-user-granted-role-write-adds-one-permission-it-already-holds"></a>

#### [a-user-granted-role-write-adds-one-permission-it-already-holds](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain adds a permission the role already holds and a new one in one call, only the new one is added and the one already held comes back failed

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_add_role_permissions: user-1 adds a session read permission the role already holds and a domain create permission to role-1 in one call

Then

- only the new permission is added and the one already held comes back failed
  - items count = 1
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: the time this run wrote
  - failed count = 1
  - failed[0].entity_type = 'session'
  - failed[0].permission = <PermissionBitDTO.READ: 'read'>
  - failed[0].message: a reason containing 'Duplicate permission'

<a id="permission_writing-a-user-granted-role-write-adds-several-permissions"></a>

#### [a-user-granted-role-write-adds-several-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain adds two permissions in one call, every row added comes back and nothing failed

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_add_role_permissions: user-1 adds domain create and project read permissions to role-1 in one call

Then

- every permission row added comes back and nothing failed
  - items count = 2
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: skipped: the database generates it
  - items[1].role_id: same as the id of the role seeded in advance
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.READ: 'read'>
  - items[1].created_at: the time this run wrote
  - failed = []

<a id="permission_writing-a-user-granted-read-only-may-not-add-permissions"></a>

#### [a-user-granted-read-only-may-not-add-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

a user granted only role read permission in a domain cannot add permissions in one call

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_add_role_permissions: user-1 adds domain create and project read permissions to role-1 in one call

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_remove_role_permissions

<a id="permission_writing-a-user-granted-read-only-removes-no-permission"></a>

#### [a-user-granted-read-only-removes-no-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted only role read permission in a domain removes two permissions in one call, none is removed and both come back in the failed list

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_remove_role_permissions: user-1 removes both permissions of role-1 in one call

Then

- no permission row is removed and every target comes back in the failed list
  - items = []
  - failed count = 2
  - failed[0].permission_id: same as the id of the permission row seeded in advance
  - failed[0].message: a reason containing 'permission'
  - failed[1].permission_id: same as the id of the permission row seeded in advance
  - failed[1].message: a reason containing 'permission'

<a id="permission_writing-a-user-granted-role-write-removes-several-permissions"></a>

#### [a-user-granted-role-write-removes-several-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain removes two permissions in one call, every row removed comes back and nothing failed

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_remove_role_permissions: user-1 removes both permissions of role-1 in one call

Then

- every permission row removed comes back and nothing failed
  - items count = 2
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: skipped: the database generates it
  - items[1].role_id: same as the id of the role seeded in advance
  - items[1].entity_type = 'vfolder'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: the time this run wrote
  - failed = []

### create

<a id="creating-a-user-granted-create-makes-a-role"></a>

#### [a-user-granted-create-makes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_creating.py): pass

when a user granted role create permission in a domain creates a role, the whole role just created comes back

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
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: CREATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.create: user-1 creates the role made-role in domain target-1

Then

- the whole role just created comes back
  - name = 'made-role'
  - description = 'a role made by this call'
  - source = <RoleSourceDTO.CUSTOM: 'custom'>
  - status = <RoleStatusDTO.ACTIVE: 'active'>
  - auto_assign = False
  - scope_type = 'domain'
  - scope_id: same as the id of the domain the role sits in
  - role_preset_id = None
  - id: skipped: the database generates it
  - entity_id: same as the id the response carries
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-create-a-role"></a>

#### [a-user-granted-nothing-may-not-create-a-role](/tests/scenario/bai_scenario/manager/rbac/test_creating.py): pass

a user granted nothing cannot create a role

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

- RBACAdapter.create: user-1 creates the role made-role in domain target-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create_permission

<a id="permission_writing-a-user-granted-role-write-creates-a-permission"></a>

#### [a-user-granted-role-write-creates-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain creates a permission, the whole permission row just created comes back

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.create_permission: user-1 adds a session soft delete permission to role-1

Then

- the whole permission row just created comes back
  - id: skipped: the database generates it
  - field_id: skipped: the database generates it
  - role_id: same as the id of the role seeded in advance
  - entity_type = 'session'
  - permission = <PermissionBitDTO.SOFT_DELETE: 'soft_delete'>
  - created_at: the time this run wrote

<a id="permission_writing-a-user-granted-read-only-may-not-create-a-permission"></a>

#### [a-user-granted-read-only-may-not-create-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

a user granted only role read permission in a domain cannot create a permission

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.create_permission: user-1 adds a session soft delete permission to role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

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

<a id="deleting-a-user-granted-update-only-may-not-soft-delete-a-role"></a>

#### [a-user-granted-update-only-may-not-soft-delete-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

a user granted only role update permission in a domain cannot soft delete a role

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
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.delete: user-1 soft deletes role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_search_roles

<a id="searching-a-user-holding-a-role-searches-it"></a>

#### [a-user-holding-a-role-searches-it](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

when a user holding a role with role read permission in their own scope searches the roles they hold by one name, that role comes back and neither the other user's role nor the other held role is listed

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role self-role-1: applies only within the scope it is granted in
  - Role self-role-1: READ allowed on every role
  - regular user user-1: holds Role self-role-1
  - Role self-role-2: applies only within the scope it is granted in
  - Role self-role-2: READ allowed on every role
  - regular user user-1: holds Role self-role-2

When

- RBACAdapter.my_search_roles: user-1 searches the roles they hold

Then

- the one role the caller holds comes back
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
  - items[0].scope_id: same as the id of the caller
  - items[0].role_preset_id = None
  - items[0].id: skipped: the database generates it
  - items[0].entity_id: same as the id of the role seeded in advance
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-their-roles"></a>

#### [a-user-granted-nothing-may-not-search-their-roles](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

a user holding no role cannot search the roles they hold

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

- RBACAdapter.my_search_roles: user-1 searches the roles they hold

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

<a id="deleting-a-user-granted-soft-delete-only-may-not-purge-a-role"></a>

#### [a-user-granted-soft-delete-only-may-not-purge-a-role](/tests/scenario/bai_scenario/manager/rbac/test_deleting.py): pass

a user granted only role soft delete permission in a domain cannot purge a role

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
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: SOFT_DELETE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.purge: user-1 purges role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### purge_permission

<a id="permission_writing-a-user-granted-role-write-purges-a-permission"></a>

#### [a-user-granted-role-write-purges-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain purges a permission, the id of that permission row comes back

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.purge_permission: user-1 purges the first permission of role-1

Then

- the id of the purged permission row comes back
  - id: same as the id of the permission row seeded in advance
  - field_id: same as the id of the permission row seeded in advance

<a id="permission_writing-a-user-granted-read-only-may-not-purge-a-permission"></a>

#### [a-user-granted-read-only-may-not-purge-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

a user granted only role read permission in a domain cannot purge a permission

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.purge_permission: user-1 purges the first permission of role-1

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

### search_role_permissions

<a id="searching_permissions-a-user-granted-role-read-searches-the-permissions-of-a-role"></a>

#### [a-user-granted-role-read-searches-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

when a user granted role read permission in a domain searches the permissions a role holds filtered to one entity type, every permission row the filter keeps comes back

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Role role-2: READ allowed on every project
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.search_role_permissions: user-1 searches the permissions role-1 holds

Then

- every permission row the filter keeps comes back
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'session'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: the time this run wrote

<a id="searching_permissions-a-user-granted-nothing-may-not-search-the-permissions-of-a-role"></a>

#### [a-user-granted-nothing-may-not-search-the-permissions-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_permissions.py): pass

a user granted nothing cannot search the permissions a role holds

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RBACAdapter.search_role_permissions: user-1 searches the permissions role-1 holds

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_roles_in_scope

<a id="searching-a-user-granted-role-read-searches-a-domain"></a>

#### [a-user-granted-role-read-searches-a-domain](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

when a user granted role read permission in a domain searches the roles of that domain leaving one role's name out, the roles the filter keeps come back in name order

Given

- 2 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role beyond-1: applies only within the scope it is granted in
  - Role excluded-1: applies only within the scope it is granted in
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.search_roles_in_scope: user-1 searches the roles of domain target-1

Then

- the roles the filter keeps come back in name order
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
  - items[0].scope_id: same as the id of the domain the role sits in
  - items[0].role_preset_id = None
  - items[0].id: skipped: the database generates it
  - items[0].entity_id: same as the id of the role seeded in advance
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].deleted_at = None
  - items[1].name = 'role-1'
  - items[1].description = None
  - items[1].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[1].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[1].auto_assign = False
  - items[1].scope_type = 'domain'
  - items[1].scope_id: same as the id of the domain the role sits in
  - items[1].role_preset_id = None
  - items[1].id: skipped: the database generates it
  - items[1].entity_id: same as the id of the role seeded in advance
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].deleted_at = None
  - items[2].name = 'role-2'
  - items[2].description = None
  - items[2].source = <RoleSourceDTO.CUSTOM: 'custom'>
  - items[2].status = <RoleStatusDTO.ACTIVE: 'active'>
  - items[2].auto_assign = False
  - items[2].scope_type = 'domain'
  - items[2].scope_id: same as the id of the domain the role sits in
  - items[2].role_preset_id = None
  - items[2].id: skipped: the database generates it
  - items[2].entity_id: same as the id of the role seeded in advance
  - items[2].created_at: the time this run wrote
  - items[2].updated_at: the time this run wrote
  - items[2].deleted_at = None

<a id="searching-a-user-granted-nothing-may-not-search-a-domain"></a>

#### [a-user-granted-nothing-may-not-search-a-domain](/tests/scenario/bai_scenario/manager/rbac/test_searching.py): pass

a user granted nothing cannot search the roles of a domain

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

- RBACAdapter.search_roles_in_scope: user-1 searches the roles of domain target-1

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

### update_permission

<a id="permission_writing-a-user-granted-role-write-updates-a-permission"></a>

#### [a-user-granted-role-write-updates-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain changes a permission, the whole permission row just changed comes back

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.update_permission: user-1 changes the first permission of role-1 to soft delete

Then

- the whole permission row just changed comes back
  - id: skipped: the database generates it
  - field_id: skipped: the database generates it
  - role_id: same as the id of the role seeded in advance
  - entity_type = 'session'
  - permission = <PermissionBitDTO.SOFT_DELETE: 'soft_delete'>
  - created_at: the time this run wrote

<a id="permission_writing-a-user-granted-read-only-may-not-update-a-permission"></a>

#### [a-user-granted-read-only-may-not-update-a-permission](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

a user granted only role read permission in a domain cannot change a permission

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.update_permission: user-1 changes the first permission of role-1 to soft delete

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_search_role_assignments

<a id="searching_assignments-the-superadmin-searches-every-role-assignment"></a>

#### [the-superadmin-searches-every-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

when the superadmin searches role assignments naming one seeded user, only that user's assignment comes back. The global role gates this search

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.admin_search_role_assignments: user-1 searches every role assignment

Then

- only the assignment of the user the filter names comes back
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: skipped: the database generates it
  - items[0].user_id: same as the id of the user seeded in advance
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].granted_by = None
  - items[0].granted_at: the time this run wrote

<a id="searching_assignments-a-user-granted-nothing-may-not-search-every-role-assignment"></a>

#### [a-user-granted-nothing-may-not-search-every-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

a user granted nothing cannot search every role assignment

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1

When

- RBACAdapter.admin_search_role_assignments: user-1 searches every role assignment

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### assign_role

<a id="assigning-a-user-granted-assignment-writes-assigns-a-role"></a>

#### [a-user-granted-assignment-writes-assigns-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a user granted write permission on the role and the user gives a role, the whole assignment comes back

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: CREATE allowed on every role
  - Role grant-1: CREATE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.assign_role: user-1 gives role-1 to user-2

Then

- the whole assignment joining that user and role comes back
  - id: skipped: the database generates it
  - user_id: same as the id of the user seeded in advance
  - role_id: same as the id of the role seeded in advance
  - granted_by: same as the one who granted the role
  - granted_at: the time this run wrote

<a id="assigning-a-user-granted-nothing-may-not-assign-a-role"></a>

#### [a-user-granted-nothing-may-not-assign-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

a user granted nothing cannot give a role

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- RBACAdapter.assign_role: user-1 gives role-1 to user-2

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="assigning-assigning-a-role-the-user-already-holds-is-refused"></a>

#### [assigning-a-role-the-user-already-holds-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

giving a role to a user who already holds it is rejected

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: CREATE allowed on every role
  - Role grant-1: CREATE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.assign_role: user-1 gives role-1 to user-2

Then

- the call is rejected
  - rejected: RoleAlreadyAssigned

### batch_load_role_assignments_by_ids

<a id="loading-the-superadmin-loads-the-assignments-by-id"></a>

#### [the-superadmin-loads-the-assignments-by-id](/tests/scenario/bai_scenario/manager/rbac/test_loading.py): pass

when the superadmin loads the assignments seeded in advance and one missing id in one call, the assignments come back as nodes and the missing id as an empty value

Given

- 2 custom roles in one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-2: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.batch_load_role_assignments_by_ids: user-1 loads the assignments seeded in advance by id in one call

Then

- the assignments seeded in advance come back as nodes and the missing id as an empty value
  - length = 3
  - [0].id: skipped: the database generates it
  - [0].user_id: same as the id of the user seeded in advance
  - [0].role_id: same as the id of the role seeded in advance
  - [0].granted_by = None
  - [0].granted_at: the time this run wrote
  - [1].id: skipped: the database generates it
  - [1].user_id: same as the id of the user seeded in advance
  - [1].role_id: same as the id of the role seeded in advance
  - [1].granted_by = None
  - [1].granted_at: the time this run wrote
  - [2] = None

### bulk_assign_role

<a id="assigning-a-user-granted-assignment-writes-assigns-a-role-to-everyone"></a>

#### [a-user-granted-assignment-writes-assigns-a-role-to-everyone](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a user granted write permission on the role and the users gives a role to several users in one call, everyone is assigned and nothing failed

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: CREATE allowed on every role
  - Role grant-1: CREATE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_assign_role: user-1 gives role-1 to every user seeded in advance in one call

Then

- every user seeded in advance is assigned and nothing failed
  - assigned count = 2
  - failed = []
  - assigned[0].id: skipped: the database generates it
  - assigned[0].user_id: same as the id of the user seeded in advance
  - assigned[0].role_id: same as the id of the role seeded in advance
  - assigned[0].granted_by: same as the one who granted the role
  - assigned[0].granted_at: the time this run wrote
  - assigned[1].id: skipped: the database generates it
  - assigned[1].user_id: same as the id of the user seeded in advance
  - assigned[1].role_id: same as the id of the role seeded in advance
  - assigned[1].granted_by: same as the one who granted the role
  - assigned[1].granted_at: the time this run wrote

<a id="assigning-assigning-to-several-users-answers-for-the-one-already-holding"></a>

#### [assigning-to-several-users-answers-for-the-one-already-holding](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a role is given to several users in one call, the user who already holds it comes back failed and the rest are assigned

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: CREATE allowed on every role
  - Role grant-1: CREATE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_assign_role: user-1 gives role-1 to every user seeded in advance in one call

Then

- only the user who already holds the role comes back failed and the rest are assigned
  - assigned count = 1
  - failed count = 1
  - assigned[0].id: skipped: the database generates it
  - assigned[0].user_id: same as the id of the user seeded in advance
  - assigned[0].role_id: same as the id of the role seeded in advance
  - assigned[0].granted_by: same as the one who granted the role
  - assigned[0].granted_at: the time this run wrote
  - failed[0].user_id: same as the id of the user seeded in advance
  - failed[0].message: a reason containing 'already assigned'

<a id="assigning-a-user-granted-nothing-may-not-assign-a-role-to-several-users"></a>

#### [a-user-granted-nothing-may-not-assign-a-role-to-several-users](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

a user granted nothing cannot give a role to several users in one call

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project

When

- RBACAdapter.bulk_assign_role: user-1 gives role-1 to every user seeded in advance in one call

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_revoke_role

<a id="assigning-a-user-granted-revocation-writes-revokes-a-role-from-everyone"></a>

#### [a-user-granted-revocation-writes-revokes-a-role-from-everyone](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a user granted delete permission on the role and the users takes a role back from several users in one call, everyone is revoked and nothing failed

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: SOFT_DELETE allowed on every role
  - Role grant-1: SOFT_DELETE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_revoke_role: user-1 takes role-1 back from every user seeded in advance in one call

Then

- the role is taken back from every user seeded in advance and nothing failed
  - revoked count = 2
  - failed = []
  - revoked[0].id: skipped: the database generates it
  - revoked[0].user_id: same as the id of the user seeded in advance
  - revoked[0].role_id: same as the id of the role seeded in advance
  - revoked[0].granted_by = None
  - revoked[0].granted_at: the time this run wrote
  - revoked[1].id: skipped: the database generates it
  - revoked[1].user_id: same as the id of the user seeded in advance
  - revoked[1].role_id: same as the id of the role seeded in advance
  - revoked[1].granted_by = None
  - revoked[1].granted_at: the time this run wrote

<a id="assigning-revoking-from-several-users-answers-for-the-one-not-holding"></a>

#### [revoking-from-several-users-answers-for-the-one-not-holding](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a role is taken back from several users in one call, the user who did not hold it comes back failed and the rest are taken back

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: SOFT_DELETE allowed on every role
  - Role grant-1: SOFT_DELETE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.bulk_revoke_role: user-1 takes role-1 back from every user seeded in advance in one call

Then

- only the user who did not hold the role comes back failed and the rest are taken back
  - revoked count = 1
  - failed count = 1
  - failed[0].user_id: same as the id of the user seeded in advance
  - failed[0].message: a reason containing 'not assigned'
  - revoked[0].id: skipped: the database generates it
  - revoked[0].user_id: same as the id of the user seeded in advance
  - revoked[0].role_id: same as the id of the role seeded in advance
  - revoked[0].granted_by = None
  - revoked[0].granted_at: the time this run wrote

<a id="assigning-a-user-granted-nothing-may-not-revoke-a-role-from-several-users"></a>

#### [a-user-granted-nothing-may-not-revoke-a-role-from-several-users](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

a user granted nothing cannot take a role back from several users in one call

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1

When

- RBACAdapter.bulk_revoke_role: user-1 takes role-1 back from every user seeded in advance in one call

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-the-role"></a>

#### [a-user-granted-read-reads-the-role](/tests/scenario/bai_scenario/manager/rbac/test_reading.py): pass

when a user granted role read permission in a domain reads a role, the whole role seeded in advance comes back

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
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.get: user-1 reads role-1 by id

Then

- the whole role seeded in advance comes back
  - name = 'role-1'
  - description = None
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

<a id="reading-a-user-granted-nothing-may-not-read-a-role"></a>

#### [a-user-granted-nothing-may-not-read-a-role](/tests/scenario/bai_scenario/manager/rbac/test_reading.py): pass

a user granted nothing cannot read a role

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

- RBACAdapter.get: user-1 reads role-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_entity_operation_combinations

<a id="held_permissions-any-user-reads-the-entity-operation-combinations"></a>

#### [any-user-reads-the-entity-operation-combinations](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

a user holding no role can still read the entities and operations a role may permit

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

- RBACAdapter.get_entity_operation_combinations: user-1 reads the entities and operations a role may permit

Then

- every wired entity with its operations comes back in name order
  - items: the list carrying the entities, operations and bits the scenario states, each in name order

### get_permission_matrix

<a id="held_permissions-any-user-reads-the-permission-matrix"></a>

#### [any-user-reads-the-permission-matrix](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

a user holding no role can still read the permission matrix of the role editor

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

- RBACAdapter.get_permission_matrix: user-1 reads the permission matrix of the role editor

Then

- the table carrying every wired scope, entity and operation comes back
  - items: the table carrying the scopes, entities, operations and bits the scenario states

### get_scope_entity_combinations

<a id="held_permissions-any-user-reads-the-scope-entity-combinations"></a>

#### [any-user-reads-the-scope-entity-combinations](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

a user holding no role can still read the entities a permission may name in each scope

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

- RBACAdapter.get_scope_entity_combinations: user-1 reads the entities a permission may name in each scope

Then

- every scope comes back with the entities it may name, in name order
  - items: each scope the scenario states, with the entities it may name

### my_atomic_bulk_scope_permissions

<a id="held_permissions-a-user-holding-a-role-asks-several-scopes-at-once"></a>

#### [a-user-holding-a-role-asks-several-scopes-at-once](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

when a user holding a role with role read permission in their own scope asks in one call about roles there and sessions in a target domain, the bits come back for each target

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
  - Role self-role-1: applies only within the scope it is granted in
  - Role self-role-1: READ allowed on every role
  - regular user user-1: holds Role self-role-1

When

- RBACAdapter.my_atomic_bulk_scope_permissions: user-1 asks in one call what permissions they hold on roles in their own scope and on sessions in domain target-1

Then

- each target comes back with the bits the caller holds there
  - items count = 2
  - items[0].scope_type = 'user'
  - items[0].scope_id: same as the id of the caller
  - items[0].entity_type = 'role'
  - items[0].permissions = [<PermissionBitDTO.READ: 'read'>]
  - items[1].scope_type = 'domain'
  - items[1].scope_id: same as the id of the target domain
  - items[1].entity_type = 'session'
  - items[1].permissions = []

<a id="held_permissions-a-user-granted-nothing-may-not-ask-several-scopes"></a>

#### [a-user-granted-nothing-may-not-ask-several-scopes](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

a user holding no role cannot ask in one call what permissions they hold in their own scope

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

- RBACAdapter.my_atomic_bulk_scope_permissions: user-1 asks in one call what permissions they hold on roles in their own scope and on sessions in domain target-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_scope_permissions

<a id="held_permissions-a-user-holding-a-role-asks-what-they-hold-in-their-own-scope"></a>

#### [a-user-holding-a-role-asks-what-they-hold-in-their-own-scope](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

when a user holding a role with role read permission in their own scope asks what they hold on roles there, that bit comes back

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
  - Role self-role-1: applies only within the scope it is granted in
  - Role self-role-1: READ allowed on every role
  - regular user user-1: holds Role self-role-1

When

- RBACAdapter.my_scope_permissions: user-1 asks what permissions they hold on roles in their own scope

Then

- the target asked about and the bits the caller holds come back
  - scope_type = 'user'
  - scope_id: same as the id of the caller
  - entity_type = 'role'
  - permissions = [<PermissionBitDTO.READ: 'read'>]

<a id="held_permissions-a-user-granted-nothing-may-not-ask-what-they-hold"></a>

#### [a-user-granted-nothing-may-not-ask-what-they-hold](/tests/scenario/bai_scenario/manager/rbac/test_held_permissions.py): pass

a user holding no role cannot ask what permissions they hold in their own scope

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

- RBACAdapter.my_scope_permissions: user-1 asks what permissions they hold on roles in their own scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_search_role_assignments

<a id="searching_assignments-a-user-holding-a-role-searches-their-assignment"></a>

#### [a-user-holding-a-role-searches-their-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

when a user holding a role with role read permission in their own scope searches their own role assignments filtered to one role, that assignment comes back and neither their other role nor another user's assignment is listed

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role self-role-1: applies only within the scope it is granted in
  - Role self-role-1: READ allowed on every role
  - regular user user-1: holds Role self-role-1
  - Role self-role-2: applies only within the scope it is granted in
  - Role self-role-2: READ allowed on every role
  - regular user user-1: holds Role self-role-2

When

- RBACAdapter.my_search_role_assignments: user-1 searches their own role assignments

Then

- the one assignment of the role the caller holds comes back
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: skipped: the database generates it
  - items[0].user_id: same as the id of the user seeded in advance
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].granted_by = None
  - items[0].granted_at: the time this run wrote

<a id="searching_assignments-a-user-granted-nothing-may-not-search-their-role-assignment"></a>

#### [a-user-granted-nothing-may-not-search-their-role-assignment](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

a user holding no role cannot search their own role assignments

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

- RBACAdapter.my_search_role_assignments: user-1 searches their own role assignments

Then

- the call is rejected
  - rejected: NotEnoughPermission

### replace_role_permissions

<a id="permission_writing-a-user-granted-role-write-replaces-the-permissions"></a>

#### [a-user-granted-role-write-replaces-the-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when a user granted role read and update permissions in a domain replaces the permission set of a role, every new permission row comes back and nothing failed

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.replace_role_permissions: user-1 replaces the permissions of role-1 with domain create and project read

Then

- the whole permission set that took over comes back and nothing failed
  - items count = 2
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.CREATE: 'create'>
  - items[0].created_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: skipped: the database generates it
  - items[1].role_id: same as the id of the role seeded in advance
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.READ: 'read'>
  - items[1].created_at: the time this run wrote
  - failed = []

<a id="permission_writing-a-user-granted-read-only-may-not-replace-the-permissions"></a>

#### [a-user-granted-read-only-may-not-replace-the-permissions](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

a user granted only role read permission in a domain cannot replace the permission set of a role

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.replace_role_permissions: user-1 replaces the permissions of role-1 with domain create and project read

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="permission_writing-replacing-with-an-entry-of-another-role-is-refused"></a>

#### [replacing-with-an-entry-of-another-role-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_permission_writing.py): pass

when the request names one role and an entry names another, the whole request is rejected

Given

- 1 custom roles in one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every session
  - Role role-1: UPDATE allowed on every vfolder
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - Role grant-1: UPDATE allowed on every role
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.replace_role_permissions: user-1 tries to replace the permissions of role-1 with an entry naming another role

Then

- the call is rejected
  - rejected: ReplaceRolePermissionRoleIdMismatch

### revoke_role

<a id="assigning-a-user-granted-revocation-writes-revokes-a-role"></a>

#### [a-user-granted-revocation-writes-revokes-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

when a user granted delete permission on the role and the user takes a role back, the whole assignment comes back

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: SOFT_DELETE allowed on every role
  - Role grant-1: SOFT_DELETE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.revoke_role: user-1 takes role-1 back from user-2

Then

- the whole assignment joining that user and role comes back
  - id: skipped: the database generates it
  - user_id: same as the id of the user seeded in advance
  - role_id: same as the id of the role seeded in advance
  - granted_by = None
  - granted_at: the time this run wrote

<a id="assigning-a-user-granted-nothing-may-not-revoke-a-role"></a>

#### [a-user-granted-nothing-may-not-revoke-a-role](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

a user granted nothing cannot take a role back

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1

When

- RBACAdapter.revoke_role: user-1 takes role-1 back from user-2

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="assigning-revoking-a-role-the-user-does-not-hold-is-refused"></a>

#### [revoking-a-role-the-user-does-not-hold-is-refused](/tests/scenario/bai_scenario/manager/rbac/test_assigning.py): pass

taking a role back from a user who does not hold it is rejected

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: SOFT_DELETE allowed on every role
  - Role grant-1: SOFT_DELETE allowed on every user
  - regular user user-1: holds Role grant-1

When

- RBACAdapter.revoke_role: user-1 takes role-1 back from user-2

Then

- the call is rejected
  - rejected: RoleNotAssigned

### search_role_assignments_in_scope

<a id="searching_assignments-a-user-granted-role-read-searches-the-assignments-of-a-role"></a>

#### [a-user-granted-role-read-searches-the-assignments-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

when a user granted role read permission in a domain searches the assignments of one role naming one seeded user, only that user's assignment comes back

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-2: holds Role role-1
  - regular user user-3: holds Role role-1
  - Role grant-1: applies only within the scope it is granted in
  - Role grant-1: READ allowed on every role
  - regular user user-1: holds Role grant-1
  - Role self-role-1: applies only within the scope it is granted in
  - Role self-role-1: READ allowed on every role
  - regular user user-1: holds Role self-role-1

When

- RBACAdapter.search_role_assignments_in_scope: user-1 searches the assignments of role-1

Then

- only the assignment of the user the filter names comes back
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: skipped: the database generates it
  - items[0].user_id: same as the id of the user seeded in advance
  - items[0].role_id: same as the id of the role seeded in advance
  - items[0].granted_by = None
  - items[0].granted_at: the time this run wrote

<a id="searching_assignments-a-user-granted-nothing-may-not-search-the-assignments-of-a-role"></a>

#### [a-user-granted-nothing-may-not-search-the-assignments-of-a-role](/tests/scenario/bai_scenario/manager/rbac/test_searching_assignments.py): pass

a user granted nothing cannot search the assignments of a role

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
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-2: holds Role role-1

When

- RBACAdapter.search_role_assignments_in_scope: user-1 searches the assignments of role-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

