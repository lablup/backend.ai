## project

[background](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/project/adapter.py)

Scenario: incomplete 15 / 17

- built from ops (10)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_by_domain_name: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_by_user: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (4)
  - assign_users: success present 1 · rejection absent (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - partial_bulk_update: success present 3 · rejection absent (partial_bulk, partial_bulk_delete_ops, partial_bulk_restore_ops): SCENARIO-GAP
  - unassign_users: success absent · rejection absent (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - update: success present 2 · rejection absent (single_delete_ops, single_entity, single_restore_ops): SCENARIO-GAP
- direct implementation (3)
  - admin_create: success present 1 · rejection present 1 (scope)
  - admin_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - batch_load_registries: success present 3 · rejection present 1 (partial_bulk)

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several projects in one call, none is soft deleted and all come back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects) | answered |
| [when two active projects and a missing id are soft deleted in one call, the two come back inactive and the missing id comes back in the failed list because no target answers to it](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted projects are restored in one call, all come back active](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**assign_users**

| scenario | verdict |
|---|---|
| [when a project and a role in its scope are in place and a user is assigned, the user is put on the roster](#project-assigning-a-user-to-a-project-puts-them-on-its-roster) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several projects in one call, none is edited and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects) | answered |
| [when several projects are edited in one call with a mix of active flags and descriptions, the one whose flag is cleared is soft deleted and the one whose flag is raised is restored, both come back with the new description, and the missing id comes back in the failed list because no target answers to it](#partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects) | answered |
| [when the superadmin changes the description of several projects in one call, all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-projects-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [an edit that clears the active flag soft deletes the project and the response carries the inactive state](#editing-clearing-the-active-flag-soft-deletes-a-project) | answered |
| [an edit that raises the active flag of a soft-deleted project restores the project and the response carries the active state](#editing-raising-the-active-flag-restores-a-soft-deleted-project) | answered |

**admin_create**

| scenario | verdict |
|---|---|
| [when a domain and a project policy are in place and the superadmin creates a project, a project with that name appears under the domain](#project-the-superadmin-makes-a-project-in-a-domain) | answered |
| [project creation is guarded by permission in the domain scope rather than by a role, so a user granted nothing is rejected for lack of permission](#project-a-user-granted-nothing-may-not-make-a-project) | rejected |

**batch_load_registries**

| scenario | verdict |
|---|---|
| [with read permission, answers a container registry allowed but not as the default with a flag saying it is not the default](#registries-read-allowed-registry) | answered |
| [with read permission, answers the container registry allowed as the default with a flag saying it is the default](#registries-read-default-registry) | answered |
| [with read permission and no allowed container registry, answers an empty list](#registries-read-no-registry) | answered |
| [without read permission, rejects the read of allowed container registries](#registries-registries-read-requires-permission) | rejected |

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to soft delete several projects in one call, none is soft deleted and all come back in the failed list for lack of permission

Given

- 2 projects under one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_delete: user-1 soft deletes 2 projects in one call

Then

- no project is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target project
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target project
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

when two active projects and a missing id are soft deleted in one call, the two come back inactive and the missing id comes back in the failed list because no target answers to it

Given

- 2 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_delete: user-1 soft deletes 2 projects and a missing id in one call

Then

- every target project comes back inactive and the missing id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: skipped: the database generates it
  - successes[0].type: skipped: the type already fixes the value
  - successes[0].entity_id: same as the id of the project seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = False
  - successes[1].id: skipped: the database generates it
  - successes[1].type: skipped: the type already fixes the value
  - successes[1].entity_id: same as the id of the project seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id given in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_deleting.py): pass

when several soft-deleted projects are restored in one call, all come back active

Given

- 2 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_restore: user-1 soft deletes 2 projects in one call and then restores them in one call

Then

- every target project comes back active and nothing failed
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'team-1 was already here'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: skipped: the database generates it
  - successes[0].type: skipped: the type already fixes the value
  - successes[0].entity_id: same as the id of the project seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'team-2'
  - successes[1].description = 'team-2 was already here'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: skipped: the database generates it
  - successes[1].type: skipped: the type already fixes the value
  - successes[1].entity_id: same as the id of the project seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed = []

### assign_users

<a id="project-assigning-a-user-to-a-project-puts-them-on-its-roster"></a>

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

when a project and a role in its scope are in place and a user is assigned, the user is put on the roster

Given

- one project, the role in its scope, the user to assign, and the superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Role project-member-1: applies only within the scope it is granted in

When

- ProjectAdapter.assign_users: user-2 assigns user-1 to research-1

Then

- the roster holds the user assigned, and no one else
  - items: same as the one user assigned

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-projects"></a>

#### [a-user-granted-nothing-edits-none-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several projects in one call, none is edited and all come back in the failed list for lack of permission

Given

- 2 projects under one domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_update: user-1 edits the description of 2 projects in one call

Then

- no project is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target project
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target project
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-projects"></a>

#### [the-active-flag-soft-deletes-or-restores-each-of-several-projects](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

when several projects are edited in one call with a mix of active flags and descriptions, the one whose flag is cleared is soft deleted and the one whose flag is raised is restored, both come back with the new description, and the missing id comes back in the failed list because no target answers to it

Given

- 2 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_update: user-1 soft deletes the second project and then, in one call, clears the active flag of the first, raises it for the second, changes both descriptions, and clears the active flag of a missing id

Then

- both come back with the new description, the first inactive and the second active, and the missing id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].name = 'team-1'
  - successes[0].description = 'the description edited in one call'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = False
  - successes[0].id: skipped: the database generates it
  - successes[0].type: skipped: the type already fixes the value
  - successes[0].entity_id: same as the id of the project seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'team-2'
  - successes[1].description = 'the description edited in one call'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: skipped: the database generates it
  - successes[1].type: skipped: the type already fixes the value
  - successes[1].entity_id: same as the id of the project seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id given in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_editing-the-superadmin-edits-several-projects-at-once"></a>

#### [the-superadmin-edits-several-projects-at-once](/tests/scenario/bai_scenario/manager/project/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several projects in one call, all come back with the new description and nothing failed

Given

- 2 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.partial_bulk_update: user-1 edits the description of 2 projects in one call

Then

- every target project comes back with the new description and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].name = 'team-1'
  - successes[0].description = 'the description edited in one call'
  - successes[0].integration_name = None
  - successes[0].domain_name = 'target-1'
  - successes[0].resource_policy = 'default'
  - successes[0].allowed_vfolder_hosts = []
  - successes[0].is_active = True
  - successes[0].id: skipped: the database generates it
  - successes[0].type: skipped: the type already fixes the value
  - successes[0].entity_id: same as the id of the project seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'team-2'
  - successes[1].description = 'the description edited in one call'
  - successes[1].integration_name = None
  - successes[1].domain_name = 'target-1'
  - successes[1].resource_policy = 'default'
  - successes[1].allowed_vfolder_hosts = []
  - successes[1].is_active = True
  - successes[1].id: skipped: the database generates it
  - successes[1].type: skipped: the type already fixes the value
  - successes[1].entity_id: same as the id of the project seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote

### update

<a id="editing-clearing-the-active-flag-soft-deletes-a-project"></a>

#### [clearing-the-active-flag-soft-deletes-a-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

an edit that clears the active flag soft deletes the project and the response carries the inactive state

Given

- 1 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.update: user-1 edits the active flag of team-1

Then

- the whole project seeded in advance comes back
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = False
  - id: skipped: the database generates it
  - type: skipped: the type already fixes the value
  - entity_id: same as the id of the project seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-raising-the-active-flag-restores-a-soft-deleted-project"></a>

#### [raising-the-active-flag-restores-a-soft-deleted-project](/tests/scenario/bai_scenario/manager/project/test_editing.py): pass

an edit that raises the active flag of a soft-deleted project restores the project and the response carries the active state

Given

- 1 projects under one domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.update: user-1 soft deletes team-1 and then edits the active flag

Then

- the whole project seeded in advance comes back
  - name = 'team-1'
  - description = 'team-1 was already here'
  - integration_name = None
  - domain_name = 'target-1'
  - resource_policy = 'default'
  - allowed_vfolder_hosts = []
  - is_active = True
  - id: skipped: the database generates it
  - type: skipped: the type already fixes the value
  - entity_id: same as the id of the project seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

### admin_create

<a id="project-the-superadmin-makes-a-project-in-a-domain"></a>

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

when a domain and a project policy are in place and the superadmin creates a project, a project with that name appears under the domain

Given

- one domain, the project policy, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.admin_create: user-1 creates research under home-1

Then

- the whole project just created comes back
  - basic_info.name = 'research'
  - basic_info.description = None
  - basic_info.integration_name = None
  - organization.domain_name = 'home-1'
  - organization.resource_policy = 'default'
  - storage.allowed_vfolder_hosts = []
  - lifecycle.is_active = True
  - id: skipped: the database generates it
  - basic_info.type: skipped: the type already fixes the value
  - lifecycle.created_at: the time this run wrote
  - lifecycle.modified_at: the time this run wrote

<a id="project-a-user-granted-nothing-may-not-make-a-project"></a>

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

project creation is guarded by permission in the domain scope rather than by a role, so a user granted nothing is rejected for lack of permission

Given

- one domain, the project policy, and one user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ProjectAdapter.admin_create: user-1 creates refused under home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### batch_load_registries

<a id="registries-read-allowed-registry"></a>

#### [read-allowed-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

with read permission, answers a container registry allowed but not as the default with a flag saying it is not the default

Given

- the project is allowed on the registry but not as the default. A regular user has read permission on the project.
  - Domain domain-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry registry-1: image source, project images
  - Project project-1 allows Container registry registry-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every project
  - regular user user-1: holds Role role-1

When

- ProjectAdapter.batch_load_registries: asks for the allowed container registries of the same project twice

Then

- answers each request with the allowed container registries or a permission rejection
  - count = 2
  - [0] count = 1
  - [0][0].registry: same as the registry seeded in advance
  - [0][0].is_default = False
  - [1] count = 1
  - [1][0].registry: same as the registry seeded in advance
  - [1][0].is_default = False

<a id="registries-read-default-registry"></a>

#### [read-default-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

with read permission, answers the container registry allowed as the default with a flag saying it is the default

Given

- the project is allowed on the registry as the default. A regular user has read permission on the project.
  - Domain domain-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry registry-1: image source, project images
  - Project project-1 defaults to Container registry registry-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every project
  - regular user user-1: holds Role role-1

When

- ProjectAdapter.batch_load_registries: asks for the allowed container registries of the same project twice

Then

- answers each request with the allowed container registries or a permission rejection
  - count = 2
  - [0] count = 1
  - [0][0].registry: same as the registry seeded in advance
  - [0][0].is_default = True
  - [1] count = 1
  - [1][0].registry: same as the registry seeded in advance
  - [1][0].is_default = True

<a id="registries-read-no-registry"></a>

#### [read-no-registry](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

with read permission and no allowed container registry, answers an empty list

Given

- the project has no allowed registry. A regular user has read permission on the project.
  - Domain domain-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry registry-1: image source, project images
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role role-1: applies only within the scope it is granted in
  - Role role-1: READ allowed on every project
  - regular user user-1: holds Role role-1

When

- ProjectAdapter.batch_load_registries: asks for the allowed container registries of the same project twice

Then

- answers each request with the allowed container registries or a permission rejection
  - count = 2
  - [0] count = 0
  - [1] count = 0

<a id="registries-registries-read-requires-permission"></a>

#### [registries-read-requires-permission](/tests/scenario/bai_scenario/manager/project/test_registries.py): pass

without read permission, rejects the read of allowed container registries

Given

- the project has no allowed registry. A regular user has no read permission on the project.
  - Domain domain-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry registry-1: image source, project images
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ProjectAdapter.batch_load_registries: asks for the allowed container registries of the same project twice

Then

- answers each request with the allowed container registries or a permission rejection
  - count = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

