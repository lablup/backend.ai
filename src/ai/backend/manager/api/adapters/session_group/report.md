## session_group

[background](/src/ai/backend/manager/api/adapters/session_group/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/session_group/adapter.py)

Scenario: complete

- built from ops (5)
  - create: representative success ✓ · representative rejection ✓
  - global_search: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - bulk_get_ids: success present 2 · rejection present 1 (partial_bulk)
  - get: success present 1 · rejection present 2 (single_entity)

**create**

| scenario | verdict |
|---|---|
| [when a user granted session group create in a project creates a session group in that project, a session group owned by that user and holding the placement policy that was given comes back](#creating-a-user-granted-create-in-a-project-creates-a-session-group-there) | answered |
| [when a user granted session group create only in another project creates a session group in that project, the call is rejected for lack of permission and no session group is created](#creating-a-user-granted-create-only-in-another-project-may-not-create-a-session-group) | rejected |
| [when a user granted only session group read in a project creates a session group in that project, the call is rejected for lack of permission and no session group is created](#creating-a-user-granted-only-read-in-a-project-may-not-create-a-session-group) | rejected |

**global_search**

| scenario | verdict |
|---|---|
| [when a superadmin with no grant searches everything filtered by one project, the session group the user created in that project and the session group held by the deployment's replica group both come back; a role checks this operation, so the requesting user is a superadmin](#searching-the-superadmin-finds-a-users-group-and-a-deployments-group) | answered |
| [when a user granted session group read in that project but not a superadmin searches everything, the role rejects it](#searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted session group purge in their own scope deletes the session group they created, the id of that session group comes back and the member sessions stay with their session group cleared](#purging-the-owner-purges-a-users-session-group-keeping-its-members) | answered |
| [when a user granted session group purge in their own scope deletes the session group held by the deployment's replica group, the call is rejected because the replica group is using it and the session group stays](#purging-a-deployments-session-group-is-refused-as-in-use) | rejected |
| [when a user with no grant deletes the session group they created, the call is rejected for lack of permission and the session group stays](#purging-a-user-granted-nothing-may-not-purge-a-session-group) | rejected |
| [when a user granted only session group read in their own scope deletes the session group they created, the call is rejected for lack of permission and the session group stays](#purging-a-user-granted-only-read-may-not-purge-a-session-group) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted session group read only in that project searches in that project's scope, the session group held by the deployment's replica group and the session groups of the other project are left out and only the session group the user created in that project comes back](#scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project) | answered |
| [when a user granted session group read in their own scope and in another project searches with both scopes together, the session groups they created and the session groups other users created in that project come back together and the session group held by the deployment's replica group is left out](#scoped_searching-a-user-scope-and-a-project-scope-are-joined) | answered |
| [when a user granted session group read in their own scope searches in their own scope, the session groups they created in two projects come back and the session group held by the deployment's replica group and the session groups other users created are left out](#scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope) | answered |
| [when a user granted session group read only in another project searches in the scope of the project that holds the session groups, the call is rejected for lack of permission](#scoped_searching-searching-a-project-not-granted-is-refused) | rejected |
| [when a user granted session group read only in the project that holds the session groups searches in the scope of the user who created them, the call is rejected for lack of permission](#scoped_searching-searching-another-users-scope-is-refused) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted session group update in their own scope changes only the direction of the session group they created, that session group comes back with the enforcement left as it was](#updating-an-owner-changes-only-the-direction) | answered |
| [when a user granted session group update in their own scope changes the direction and the enforcement of the session group they created, that session group comes back with both items changed](#updating-an-owner-changes-the-direction-and-the-enforcement) | answered |
| [when a user granted session group update in their own scope changes the policy of the session group held by their own deployment's replica group, the call is rejected as in use rather than for permission](#updating-a-deployments-session-group-is-refused-as-in-use) | rejected |
| [when a user granted only session group read in their own scope changes the policy of the session group they created, the call is rejected for lack of permission](#updating-an-owner-granted-only-read-may-not-update) | rejected |

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user granted session group read in that project reads the session group the user created and the session group held by the deployment's replica group together, that session group and an empty entry come back in the requested order](#bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group) | answered |
| [when a superadmin bulk reads an id that holds no session group, that entry comes back empty; only someone who passes the permission check can see the answer of a read, so the requesting user is a superadmin](#bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty) | answered |
| [when a user with no grant bulk reads the session group the user created by id, that entry is rejected for lack of permission](#bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted session group read in that project reads the session group the user created by id, that session group comes back](#reading-a-granted-user-reads-a-users-session-group) | answered |
| [when a user granted session group read in that project reads the session group held by the deployment's replica group by id, the call is rejected as not found rather than for permission](#reading-a-deployments-session-group-is-not-found-even-when-granted) | rejected |
| [when a user with no grant reads the session group the user created by id, the call is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-a-session-group) | rejected |

### create

<a id="creating-a-user-granted-create-in-a-project-creates-a-session-group-there"></a>

#### [a-user-granted-create-in-a-project-creates-a-session-group-there](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

when a user granted session group create in a project creates a session group in that project, a session group owned by that user and holding the placement policy that was given comes back

Given

- two projects in one domain, and one user granted create a session group in the project it goes in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare a user granted the session group create permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-creator-1: applies only within the scope it is granted in
    - Role session-group-creator-1: CREATE allowed on every session_group
    - regular user user-1: holds Role session-group-creator-1

When

- SessionGroupAdapter.create: user-1 creates a session group in that project with direction spread and enforcement preferred

Then

- the whole session group comes back, owned by the user who created it and holding the placement policy that was given
  - id: skipped: the database generates it
  - entity_id: same as id
  - domain_id: same as the id of that domain
  - project_id: same as the id of that project
  - owner_user_id: same as the id of the user who created it
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.PREFERRED: 'preferred'>
  - created_at: the time this run wrote
  - deleted_at = None

<a id="creating-a-user-granted-create-only-in-another-project-may-not-create-a-session-group"></a>

#### [a-user-granted-create-only-in-another-project-may-not-create-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

when a user granted session group create only in another project creates a session group in that project, the call is rejected for lack of permission and no session group is created

Given

- two projects in one domain, and one user granted create a session group only in the other project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare a user granted the session group create permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-creator-1: applies only within the scope it is granted in
    - Role session-group-creator-1: CREATE allowed on every session_group
    - regular user user-1: holds Role session-group-creator-1

When

- SessionGroupAdapter.create: user-1 creates a session group in that project with direction spread and enforcement preferred

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="creating-a-user-granted-only-read-in-a-project-may-not-create-a-session-group"></a>

#### [a-user-granted-only-read-in-a-project-may-not-create-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_creating.py): pass

when a user granted only session group read in a project creates a session group in that project, the call is rejected for lack of permission and no session group is created

Given

- two projects in one domain, and one user granted read a session group in the project it goes in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-reader-1

When

- SessionGroupAdapter.create: user-1 creates a session group in that project with direction spread and enforcement preferred

Then

- the call is rejected
  - rejected: NotEnoughPermission

### global_search

<a id="searching-the-superadmin-finds-a-users-group-and-a-deployments-group"></a>

#### [the-superadmin-finds-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

when a superadmin with no grant searches everything filtered by one project, the session group the user created in that project and the session group held by the deployment's replica group both come back; a role checks this operation, so the requesting user is a superadmin

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one superadmin holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.global_search: user-3 searches everything filtered by the project team-1

Then

- the session group the user created in that project and the session group held by the deployment's replica group both come back
  - items: the session group the user created and the session group held by the deployment's replica group
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-a-superadmin-may-not-search-every-session-group"></a>

#### [a-user-who-is-not-a-superadmin-may-not-search-every-session-group](/tests/scenario/bai_scenario/manager/session_group/test_searching.py): pass

when a user granted session group read in that project but not a superadmin searches everything, the role rejects it

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.global_search: user-3 searches everything filtered by the project team-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### purge

<a id="purging-the-owner-purges-a-users-session-group-keeping-its-members"></a>

#### [the-owner-purges-a-users-session-group-keeping-its-members](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

when a user granted session group purge in their own scope deletes the session group they created, the id of that session group comes back and the member sessions stay with their session group cleared

Given

- the session group a user made with two member sessions in one project and the session group the deployment's replica group holds, and the user who made those session groups, granted the session group purge permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group purge permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: HARD_DELETE allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session session-1: waiting to be scheduled as a member of the session group
  - Session session-2: waiting to be scheduled as a member of the session group
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.purge: user-1 purges the session group the user created

Then

- the id of the purged session group the user created comes back
  - entity_id: same as the id of the session group the user created

<a id="purging-a-deployments-session-group-is-refused-as-in-use"></a>

#### [a-deployments-session-group-is-refused-as-in-use](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

when a user granted session group purge in their own scope deletes the session group held by the deployment's replica group, the call is rejected because the replica group is using it and the session group stays

Given

- the session group a user made with two member sessions in one project and the session group the deployment's replica group holds, and the user who made those session groups, granted the session group purge permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group purge permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: HARD_DELETE allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session session-1: waiting to be scheduled as a member of the session group
  - Session session-2: waiting to be scheduled as a member of the session group
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.purge: user-1 purges the session group held by the deployment's replica group

Then

- the call is rejected
  - rejected: SessionGroupInUse

<a id="purging-a-user-granted-nothing-may-not-purge-a-session-group"></a>

#### [a-user-granted-nothing-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

when a user with no grant deletes the session group they created, the call is rejected for lack of permission and the session group stays

Given

- the session group a user made with two member sessions in one project and the session group the deployment's replica group holds, and the user who made those session groups, holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session session-1: waiting to be scheduled as a member of the session group
  - Session session-2: waiting to be scheduled as a member of the session group
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.purge: user-1 purges the session group the user created

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-a-user-granted-only-read-may-not-purge-a-session-group"></a>

#### [a-user-granted-only-read-may-not-purge-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_purging.py): pass

when a user granted only session group read in their own scope deletes the session group they created, the call is rejected for lack of permission and the session group stays

Given

- the session group a user made with two member sessions in one project and the session group the deployment's replica group holds, and the user who made those session groups, granted the session group read permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group read permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session session-1: waiting to be scheduled as a member of the session group
  - Session session-2: waiting to be scheduled as a member of the session group
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.purge: user-1 purges the session group the user created

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-granted-user-finds-only-the-users-group-of-the-project"></a>

#### [a-granted-user-finds-only-the-users-group-of-the-project](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

when a user granted session group read only in that project searches in that project's scope, the session group held by the deployment's replica group and the session groups of the other project are left out and only the session group the user created in that project comes back

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.scoped_search: user-3 searches in the scope of the project team-1

Then

- only the session group the user created in that project stays
  - items: the session group the user created in that project
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-scope-and-a-project-scope-are-joined"></a>

#### [a-user-scope-and-a-project-scope-are-joined](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

when a user granted session group read in their own scope and in another project searches with both scopes together, the session groups they created and the session groups other users created in that project come back together and the session group held by the deployment's replica group is left out

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group read permission in their own scope and the other project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group read permission in their own scope and in one project
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-reader-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.scoped_search: user-1 searches their own scope and the scope of the project other-1 together

Then

- the session groups the user created and the session groups of the other project stay together
  - items: the session groups the user created and the session groups of the other project
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-an-owner-finds-the-groups-they-made-in-their-own-scope"></a>

#### [an-owner-finds-the-groups-they-made-in-their-own-scope](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

when a user granted session group read in their own scope searches in their own scope, the session groups they created in two projects come back and the session group held by the deployment's replica group and the session groups other users created are left out

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group read permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group read permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.scoped_search: user-1 searches in their own scope

Then

- only the session groups the user created in two projects stay
  - items: the session groups the user created in two projects
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-searching-a-project-not-granted-is-refused"></a>

#### [searching-a-project-not-granted-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

when a user granted session group read only in another project searches in the scope of the project that holds the session groups, the call is rejected for lack of permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission only in the other project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.scoped_search: user-3 searches in the scope of the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-searching-another-users-scope-is-refused"></a>

#### [searching-another-users-scope-is-refused](/tests/scenario/bai_scenario/manager/session_group/test_scoped_searching.py): pass

when a user granted session group read only in the project that holds the session groups searches in the scope of the user who created them, the call is rejected for lack of permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.scoped_search: user-3 searches in the scope of user-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="updating-an-owner-changes-only-the-direction"></a>

#### [an-owner-changes-only-the-direction](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

when a user granted session group update in their own scope changes only the direction of the session group they created, that session group comes back with the enforcement left as it was

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group update permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group update permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: UPDATE allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.update: user-1 changes only the direction of the session group the user created to spread

Then

- the whole session group with only the direction changed and the enforcement left as it was comes back
  - id: skipped: the database generates it
  - entity_id: same as the id of the session group the user made
  - domain_id: same as the id of that domain
  - project_id: same as the id of that project
  - owner_user_id: same as the id of the user who created it
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - created_at: the time this run wrote
  - deleted_at = None

<a id="updating-an-owner-changes-the-direction-and-the-enforcement"></a>

#### [an-owner-changes-the-direction-and-the-enforcement](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

when a user granted session group update in their own scope changes the direction and the enforcement of the session group they created, that session group comes back with both items changed

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group update permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group update permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: UPDATE allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.update: user-1 changes the direction of the session group the user created to spread and its enforcement to preferred

Then

- the whole session group with both items changed comes back
  - id: skipped: the database generates it
  - entity_id: same as the id of the session group the user made
  - domain_id: same as the id of that domain
  - project_id: same as the id of that project
  - owner_user_id: same as the id of the user who created it
  - placement_direction = <SessionGroupPlacementDirectionEnum.SPREAD: 'spread'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.PREFERRED: 'preferred'>
  - created_at: the time this run wrote
  - deleted_at = None

<a id="updating-a-deployments-session-group-is-refused-as-in-use"></a>

#### [a-deployments-session-group-is-refused-as-in-use](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

when a user granted session group update in their own scope changes the policy of the session group held by their own deployment's replica group, the call is rejected as in use rather than for permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group update permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group update permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: UPDATE allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.update: user-1 changes the direction of the session group held by the deployment's replica group to spread and its enforcement to preferred

Then

- the call is rejected
  - rejected: SessionGroupInUseForUpdate

<a id="updating-an-owner-granted-only-read-may-not-update"></a>

#### [an-owner-granted-only-read-may-not-update](/tests/scenario/bai_scenario/manager/session_group/test_updating.py): pass

when a user granted only session group read in their own scope changes the policy of the session group they created, the call is rejected for lack of permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and the user who made those session groups, granted the session group read permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the session group read permission in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role session-group-owner-1: applies only within the scope it is granted in
    - Role session-group-owner-1: READ allowed on every session_group
    - regular user user-1: holds Role session-group-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.update: user-1 changes the direction of the session group the user created to spread and its enforcement to preferred

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_get_ids

<a id="bulk_reading-a-granted-user-bulk-reads-a-users-group-and-a-deployments-group"></a>

#### [a-granted-user-bulk-reads-a-users-group-and-a-deployments-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

when a user granted session group read in that project reads the session group the user created and the session group held by the deployment's replica group together, that session group and an empty entry come back in the requested order

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.bulk_get_ids: user-3 bulk reads the session group the user created and then the session group held by the deployment's replica group, in that order

Then

- the whole session group the user created comes back in the first entry and the entry for the session group held by the deployment's replica group is empty
  - [0].id: skipped: the database generates it
  - [0].entity_id: same as the id of the session group the user made
  - [0].domain_id: same as the id of that domain
  - [0].project_id: same as the id of that project
  - [0].owner_user_id: same as the id of the user who created it
  - [0].placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - [0].placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - [0].created_at: the time this run wrote
  - [0].deleted_at = None

<a id="bulk_reading-the-superadmin-bulk-reads-a-missing-id-as-empty"></a>

#### [the-superadmin-bulk-reads-a-missing-id-as-empty](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

when a superadmin bulk reads an id that holds no session group, that entry comes back empty; only someone who passes the permission check can see the answer of a read, so the requesting user is a superadmin

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one superadmin holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.bulk_get_ids: user-3 bulk reads an id that holds no session group

Then

- the requested entry is empty
  - answers = ['NoneType']

<a id="bulk_reading-a-user-granted-nothing-may-not-bulk-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-bulk-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_bulk_reading.py): pass

when a user with no grant bulk reads the session group the user created by id, that entry is rejected for lack of permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.bulk_get_ids: user-3 bulk reads the session group the user created by id

Then

- the requested entry is rejected
  - rejected: NotEnoughPermission

### get

<a id="reading-a-granted-user-reads-a-users-session-group"></a>

#### [a-granted-user-reads-a-users-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

when a user granted session group read in that project reads the session group the user created by id, that session group comes back

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.get: user-3 reads the session group the user created by id

Then

- the whole session group the user created comes back
  - id: skipped: the database generates it
  - entity_id: same as the id of the session group the user made
  - domain_id: same as the id of that domain
  - project_id: same as the id of that project
  - owner_user_id: same as the id of the user who created it
  - placement_direction = <SessionGroupPlacementDirectionEnum.PACK: 'pack'>
  - placement_enforcement = <SessionGroupPlacementEnforcementEnum.STRICT: 'strict'>
  - created_at: the time this run wrote
  - deleted_at = None

<a id="reading-a-deployments-session-group-is-not-found-even-when-granted"></a>

#### [a-deployments-session-group-is-not-found-even-when-granted](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

when a user granted session group read in that project reads the session group held by the deployment's replica group by id, the call is rejected as not found rather than for permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user granted the session group read permission in the project the session groups are in
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Prepare a user granted the session group read permission in the project
    - Prepare one user in the domain
      - User resource policy user-policy-3: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-3: has their own keypair and personal project
    - Role session-group-reader-1: applies only within the scope it is granted in
    - Role session-group-reader-1: READ allowed on every session_group
    - regular user user-3: holds Role session-group-reader-1

When

- SessionGroupAdapter.get: user-3 reads the session group held by the deployment's replica group by id

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="reading-a-user-granted-nothing-may-not-read-a-session-group"></a>

#### [a-user-granted-nothing-may-not-read-a-session-group](/tests/scenario/bai_scenario/manager/session_group/test_reading.py): pass

when a user with no grant reads the session group the user created by id, the call is rejected for lack of permission

Given

- the session group a user made in one project and the session group the deployment's replica group holds, the session group the same user made in another project, and the session group another user made, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Session group a user made session-group-1: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-2: packs its members onto one agent and enforces it strictly
  - Session group a user made session-group-3: packs its members onto one agent and enforces it strictly
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group

When

- SessionGroupAdapter.get: user-3 reads the session group the user created by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

