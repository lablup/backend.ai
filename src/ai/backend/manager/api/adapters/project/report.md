## project

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/project/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/project/adapter.py)

<<<<<<< HEAD
Not exercised by any scenario: admin_delete, admin_purge, admin_restore, admin_search, admin_update, batch_load_by_ids, batch_load_fields, get, scoped_search, search_by_domain_name, search_by_user, unassign_users.

### project
=======
Scenario: incomplete 13 / 17

- built from ops (10)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✓ · representative rejection ✓
  - search_by_domain_name: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_by_user: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (4)
  - assign_users: success present 1 · rejection present 2 (atomic_bulk_get_ops, scope)
  - partial_bulk_update: success present 3 · rejection absent (partial_bulk, partial_bulk_delete_ops, partial_bulk_restore_ops): SCENARIO-GAP
  - unassign_users: success absent · rejection absent (atomic_bulk_get_ops, scope): SCENARIO-GAP
  - update: success present 2 · rejection absent (single_delete_ops, single_entity, single_restore_ops): SCENARIO-GAP
- direct implementation (3)
  - admin_create: success present 1 · rejection present 1 (scope)
  - admin_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - batch_load_registries: success present 3 · rejection present 1 (partial_bulk)
>>>>>>> 9338bcb3 (fix(BAI-930): search projects by the resource group scope (#17348))

#### [a-user-granted-nothing-may-not-make-a-project](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

<<<<<<< HEAD
프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, 아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다
=======
| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several projects in one call, none is soft deleted and all come back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-projects) | answered |
| [when two active projects and a missing id are soft deleted in one call, the two come back inactive and the missing id comes back in the failed list because no target answers to it](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted projects are restored in one call, all come back active](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted the project read role in a resource group scope searches in that scope, the same projects as the superadmin sees come back](#scoped_searching_by_resource_group-a-user-granted-read-in-the-group-searches-its-projects) | answered |
| [when the superadmin searches in a resource group scope, only the projects that can use the group come back](#scoped_searching_by_resource_group-the-superadmin-searches-the-projects-of-a-resource-group) | answered |
| [when a user granted nothing searches in a resource group scope, the call is rejected for lack of permission](#scoped_searching_by_resource_group-a-user-granted-nothing-may-not-search-the-projects-of-a-resource-group) | rejected |

**assign_users**

| scenario | verdict |
|---|---|
| [when a project and a role in its scope are in place and a user is assigned, the user is put on the roster](#project-assigning-a-user-to-a-project-puts-them-on-its-roster) | answered |
| [an assignment is guarded by the permission to add users to the project, so a user granted only the permission to read users is rejected for lack of permission](#project-a-user-who-only-reads-users-may-not-assign-a-user-to-the-project) | rejected |
| [assigning a user with a role in another project's scope is rejected, because the role is not one of the roles of the project assigned to](#project-assigning-a-user-with-a-role-of-another-project-is-refused) | rejected |

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
>>>>>>> 9338bcb3 (fix(BAI-930): search projects by the resource group scope (#17348))

Given

- 도메인 하나와 프로젝트 정책, 그리고 user 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — user-1이 home-1 아래에 refused을 만듦

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [assigning-a-user-to-a-project-puts-them-on-its-roster](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, 그 사용자가 명부에 오른다

Given

- 프로젝트 하나와 그 프로젝트 스코프의 역할, 올릴 사용자, 그리고 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 research-1
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 역할 project-member-1: 이 역할이 앉은 스코프 안에서만 통한다

When

- ProjectAdapter.assign_users — user-2이 user-1을 research-1에 배정

Then

- 명부에 배정한 사람만 올라 있다
  - items: 배정한 사람 하나와 같다

#### [the-superadmin-makes-a-project-in-a-domain](/tests/scenario/bai_scenario/manager/project/test_project.py) — pass

도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, 그 이름의 프로젝트가 그 도메인 아래에 생긴다

Given

- 도메인 하나와 프로젝트 정책, 그리고 superadmin 한 명
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ProjectAdapter.admin_create — user-1이 home-1 아래에 research을 만듦

Then

<<<<<<< HEAD
- 만든 프로젝트 전체가 온다
=======
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

### scoped_search

<a id="scoped_searching_by_resource_group-a-user-granted-read-in-the-group-searches-its-projects"></a>

#### [a-user-granted-read-in-the-group-searches-its-projects](/tests/scenario/bai_scenario/manager/project/test_scoped_searching_by_resource_group.py): pass

when a user granted the project read role in a resource group scope searches in that scope, the same projects as the superadmin sees come back

Given

- one resource group, two projects that can use it and one that cannot, and the user granted the project read role in the resource group scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Resource group resource-group-1: uses the fifo scheduler
  - Project linked-1
  - Project linked-2
  - Project unlinked-1
  - Project linked-1 whose sessions can use Resource group resource-group-1
  - Project linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the project read role in the resource group scope
    - Role project-reader-1: applies only within the scope it is granted in
    - Role project-reader-1: READ allowed on every project
    - regular user user-1: holds Role project-reader-1

When

- ProjectAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- only the projects that can use the group are left
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_by_resource_group-the-superadmin-searches-the-projects-of-a-resource-group"></a>

#### [the-superadmin-searches-the-projects-of-a-resource-group](/tests/scenario/bai_scenario/manager/project/test_scoped_searching_by_resource_group.py): pass

when the superadmin searches in a resource group scope, only the projects that can use the group come back

Given

- one resource group, two projects that can use it and one that cannot, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Resource group resource-group-1: uses the fifo scheduler
  - Project linked-1
  - Project linked-2
  - Project unlinked-1
  - Project linked-1 whose sessions can use Resource group resource-group-1
  - Project linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ProjectAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- only the projects that can use the group are left
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_by_resource_group-a-user-granted-nothing-may-not-search-the-projects-of-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-search-the-projects-of-a-resource-group](/tests/scenario/bai_scenario/manager/project/test_scoped_searching_by_resource_group.py): pass

when a user granted nothing searches in a resource group scope, the call is rejected for lack of permission

Given

- one resource group, two projects that can use it and one that cannot, and one user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Resource group resource-group-1: uses the fifo scheduler
  - Project linked-1
  - Project linked-2
  - Project unlinked-1
  - Project linked-1 whose sessions can use Resource group resource-group-1
  - Project linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ProjectAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

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

<a id="project-a-user-who-only-reads-users-may-not-assign-a-user-to-the-project"></a>

#### [a-user-who-only-reads-users-may-not-assign-a-user-to-the-project](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

an assignment is guarded by the permission to add users to the project, so a user granted only the permission to read users is rejected for lack of permission

Given

- one project, the role in its scope, the user to assign, and a regular user granted only the permission to read users in that domain
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project research-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Role project-member-1: applies only within the scope it is granted in
  - Role user-reader-1: applies only within the scope it is granted in
  - Role user-reader-1: READ allowed on every user
  - regular user user-2: holds Role user-reader-1

When

- ProjectAdapter.assign_users: user-2 assigns user-1 to research-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="project-assigning-a-user-with-a-role-of-another-project-is-refused"></a>

#### [assigning-a-user-with-a-role-of-another-project-is-refused](/tests/scenario/bai_scenario/manager/project/test_project.py): pass

assigning a user with a role in another project's scope is rejected, because the role is not one of the roles of the project assigned to

Given

- one project, a role in another project's scope, the user to assign, and the superadmin
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
  - Project other-1
  - Role project-member-1: applies only within the scope it is granted in

When

- ProjectAdapter.assign_users: user-2 assigns user-1 to research-1

Then

- the call is rejected
  - rejected: RoleNotFound

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
>>>>>>> 9338bcb3 (fix(BAI-930): search projects by the resource group scope (#17348))
  - basic_info.name = 'research'
  - basic_info.description = None
  - basic_info.integration_name = None
  - organization.domain_name = 'home-1'
  - organization.resource_policy = 'default'
  - storage.allowed_vfolder_hosts = []
  - lifecycle.is_active = True
  - id: 무시함 — 데이터베이스가 만든다
  - basic_info.type: 무시함 — 타입이 이미 값을 못박는다
  - lifecycle.created_at: 이 실행이 쓴 시각
  - lifecycle.modified_at: 이 실행이 쓴 시각

