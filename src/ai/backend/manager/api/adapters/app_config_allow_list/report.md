## app_config_allow_list

[background](/src/ai/backend/manager/api/adapters/app_config_allow_list/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/app_config_allow_list/adapter.py)

Scenario: incomplete 2 / 8

- built from ops (6)
  - admin_create: representative success ✓ · representative rejection ✓
  - admin_get: representative success ✓ · representative rejection ✓
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - partial_bulk_purge: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 2 · rejection present 2 (single_entity)

**admin_create**

| scenario | verdict |
|---|---|
| [when the superadmin creates an allow_list with a rank given, the value is stored as given](#creating-a-rank-given-in-the-request-is-kept-as-is) | answered |
| [when the superadmin creates an allow_list of the domain scope kind with no rank, rank 200 applies](#creating-leaving-the-rank-out-opens-the-domain-kind-at-its-default-rank) | answered |
| [when the superadmin creates an allow_list of the public scope kind with no rank, rank 100 applies](#creating-leaving-the-rank-out-opens-the-public-kind-at-its-default-rank) | answered |
| [when the superadmin creates an allow_list of the user scope kind with no rank, rank 300 applies](#creating-leaving-the-rank-out-opens-the-user-kind-at-its-default-rank) | answered |
| [when the superadmin creates an allow_list with a config name nothing registers, the definition-not-found error comes back](#creating-a-name-nothing-registers-cannot-be-opened) | rejected |
| [when a plain user creates an allow_list, the call is rejected because the user is not the superadmin](#creating-a-user-who-is-not-the-superadmin-may-not-open-a-name) | rejected |
| [when the superadmin creates an allow_list again with the same config name and scope kind, the database's unique constraint error comes back](#creating-opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation) | rejected |
| [turning RBAC enforcement off still rejects an allow_list creation by a plain user](#creating-turning-enforcement-off-still-does-not-let-a-user-open-a-name) | rejected |

**admin_get**

| scenario | verdict |
|---|---|
| [with one allow_list laid, when the superadmin reads it by ID, every field of that allow_list comes back](#reading-the-superadmin-reads-an-entry-by-id) | answered |
| [turning RBAC enforcement off lets a plain user without permission read an allow_list](#reading-turning-enforcement-off-lets-a-plain-user-read) | answered |
| [when a plain user without permission reads the same allow_list, the call is rejected because the user has no entity read permission](#reading-a-user-who-is-not-the-superadmin-may-not-read-an-entry) | rejected |
| [when the superadmin reads a missing ID, the call is rejected because there is no such target. Only a user who passes the permission check sees this answer](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [with four allow_lists that all share the same creation time, when the superadmin searches for one entry after the cursor of the first item in the default order, the answer is the allow_list right after it and says there are pages both before and after](#searching-a-forward-cursor-answers-the-one-right-after-it) | answered |
| [with four allow_lists across two config names, when the superadmin searches without a filter, all four allow_lists come back](#searching-the-superadmin-counts-every-entry) | answered |
| [when a plain user searches allow_lists, the call is rejected because the user is not the superadmin](#searching-a-user-who-is-not-the-superadmin-may-not-search-entries) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [loading with an empty ID list answers an empty list](#reading_many-an-empty-id-list-answers-empty) | answered |
| [when the superadmin loads the ID of the same allow_list twice, the same node comes back at both positions](#reading_many-duplicate-ids-keep-their-input-positions) | answered |
| [when the superadmin loads both allow_lists and one missing ID together, two nodes and None come back in input order](#reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty) | answered |
| [when a plain user without permission loads both allow_lists and one missing ID together, an entity read permission error comes back at each input position](#reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a plain user without permission tries to change the rank of both allow_lists in one call, none is changed and both come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-reranks-none-of-several-entries) | answered |
| [when a regular user granted the update permission on allow-list entries in the global scope changes the rank of both allow_lists in one call, both come back with the new rank and none failed](#partial_bulk_editing-a-user-granted-update-in-global-reranks-both-entries-at-once) | answered |
| [when the superadmin changes the rank of both allow_lists in one call, both come back with the new rank and none failed](#partial_bulk_editing-the-superadmin-reranks-several-entries-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin edits without naming any value, the node comes back with nothing changed](#editing-an-edit-carrying-no-value-changes-nothing) | answered |
| [with one allow_list laid, when the superadmin changes the rank, only the rank changes and the config name and scope kind stay the same](#editing-the-superadmin-changes-an-entrys-rank) | answered |
| [when a plain user without permission edits the same allow_list, the call is rejected because the user has no entity update permission](#editing-a-user-who-is-not-the-superadmin-may-not-change-a-rank) | rejected |
| [when the superadmin edits the rank of a missing ID, the call is rejected because there is no such target](#editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a plain user without permission tries to purge both allow_lists in one call, none is deleted and both come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-entries) | answered |
| [when a regular user granted the purge permission on allow-list entries in the global scope purges both allow_lists in one call, both come back in the processed list and none failed](#partial_bulk_purging-a-user-granted-purge-in-global-purges-both-entries-at-once) | answered |
| [when the superadmin purges both allow_lists and a missing ID in one call, the two come back in the processed list and the missing ID comes back in the failed list because there is no such target](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges an allow_list that has a config fragment, the fragment does not block it and the ID of the allow_list comes back](#purging-an-entry-holding-a-fragment-is-still-purged) | answered |
| [when the superadmin purges an allow_list with no config fragment, the ID of the purged allow_list comes back](#purging-the-superadmin-purges-an-entry) | answered |
| [when a plain user without permission purges the same allow_list, the call is rejected because the user has no entity delete permission](#purging-a-user-who-is-not-the-superadmin-may-not-purge-an-entry) | rejected |
| [when the superadmin purges a missing ID, the call is rejected because there is no such target](#purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

### admin_create

<a id="creating-a-rank-given-in-the-request-is-kept-as-is"></a>

#### [a-rank-given-in-the-request-is-kept-as-is](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list with a rank given, the value is stored as given

Given

- one config definition without an allow list, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the domain allow_list for config-1 (rank 250)

Then

- every field of the created allow-list entry comes back
  - id: skipped: the database generates it
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 250
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-leaving-the-rank-out-opens-the-domain-kind-at-its-default-rank"></a>

#### [leaving-the-rank-out-opens-the-domain-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list of the domain scope kind with no rank, rank 200 applies

Given

- one config definition without an allow list, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the domain allow_list for config-1 (rank omitted)

Then

- every field of the created allow-list entry comes back
  - id: skipped: the database generates it
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 200
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-leaving-the-rank-out-opens-the-public-kind-at-its-default-rank"></a>

#### [leaving-the-rank-out-opens-the-public-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list of the public scope kind with no rank, rank 100 applies

Given

- one config definition without an allow list, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the public allow_list for config-1 (rank omitted)

Then

- every field of the created allow-list entry comes back
  - id: skipped: the database generates it
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - rank = 100
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-leaving-the-rank-out-opens-the-user-kind-at-its-default-rank"></a>

#### [leaving-the-rank-out-opens-the-user-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list of the user scope kind with no rank, rank 300 applies

Given

- one config definition without an allow list, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the user allow_list for config-1 (rank omitted)

Then

- every field of the created allow-list entry comes back
  - id: skipped: the database generates it
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-name-nothing-registers-cannot-be-opened"></a>

#### [a-name-nothing-registers-cannot-be-opened](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list with a config name nothing registers, the definition-not-found error comes back

Given

- an unregistered config name and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the public allow_list for unregistered (rank omitted)

Then

- the call is rejected
  - rejected: AppConfigDefinitionNotFound

<a id="creating-a-user-who-is-not-the-superadmin-may-not-open-a-name"></a>

#### [a-user-who-is-not-the-superadmin-may-not-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when a plain user creates an allow_list, the call is rejected because the user is not the superadmin

Given

- one config definition without an allow list, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the public allow_list for config-1 (rank omitted)

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation"></a>

#### [opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

when the superadmin creates an allow_list again with the same config name and scope kind, the database's unique constraint error comes back

Given

- one allow-list entry of the public scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the public allow_list for config-1 (rank omitted)

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-open-a-name"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py): pass

turning RBAC enforcement off still rejects an allow_list creation by a plain user

Given

- one config definition without an allow list, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered

When

- AppConfigAllowListAdapter.admin_create: user-1 creates the public allow_list for config-1 (rank omitted)

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_get

<a id="reading-the-superadmin-reads-an-entry-by-id"></a>

#### [the-superadmin-reads-an-entry-by-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py): pass

with one allow_list laid, when the superadmin reads it by ID, every field of that allow_list comes back

Given

- one allow-list entry of the user scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.admin_get: user-1 reads the allow_list of config-1

Then

- every field of the prepared allow-list entry comes back
  - id: same as the prepared id
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-turning-enforcement-off-lets-a-plain-user-read"></a>

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py): pass

turning RBAC enforcement off lets a plain user without permission read an allow_list

Given

- one allow-list entry of the user scope kind, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.admin_get: user-1 reads the allow_list of config-1

Then

- every field of the prepared allow-list entry comes back
  - id: same as the prepared id
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-an-entry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py): pass

when a plain user without permission reads the same allow_list, the call is rejected because the user has no entity read permission

Given

- one allow-list entry of the user scope kind, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.admin_get: user-1 reads the allow_list of config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py): pass

when the superadmin reads a missing ID, the call is rejected because there is no such target. Only a user who passes the permission check sees this answer

Given

- one allow-list entry of the public scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.admin_get: user-1 reads a missing ID

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_search

<a id="searching-a-forward-cursor-answers-the-one-right-after-it"></a>

#### [a-forward-cursor-answers-the-one-right-after-it](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py): pass

with four allow_lists that all share the same creation time, when the superadmin searches for one entry after the cursor of the first item in the default order, the answer is the allow_list right after it and says there are pages both before and after

Given

- 4 config names each with an allow-list entry of the public scope kind, and one superadmin
  - Domain home-1
  - Config definition definition-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Config definition definition-2: the config of this name is registered
  - Allow-list entry entry-2: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Config definition definition-3: the config of this name is registered
  - Allow-list entry entry-3: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Config definition definition-4: the config of this name is registered
  - Allow-list entry entry-4: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.admin_search: user-1 searches for one entry after the cursor of the first item in the default order

Then

- one allow-list entry after the cursor comes back and the answer says pages exist on both sides
  - items: same as the one allow-list entry after the cursor
  - total_count = 4
  - has_next_page = True
  - has_previous_page = True

<a id="searching-the-superadmin-counts-every-entry"></a>

#### [the-superadmin-counts-every-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py): pass

with four allow_lists across two config names, when the superadmin searches without a filter, all four allow_lists come back

Given

- 2 config names each with an allow-list entry of the public, user scope kind, and one superadmin
  - Domain home-1
  - Config definition definition-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Config definition definition-2: the config of this name is registered
  - Allow-list entry entry-3: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry entry-4: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.admin_search: user-1 searches every entry without a filter

Then

- every prepared allow-list entry comes back, and only those
  - items = [('definition-1', <AppConfigScopeType.PUBLIC: 'public'>), ('definition-1', <AppConfigScopeType.USER: 'user'>), ('definition-2', <AppConfigScopeType.PUBLIC: 'public'>), ('definition-2', <AppConfigScopeType.USER: 'user'>)]
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-entries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py): pass

when a plain user searches allow_lists, the call is rejected because the user is not the superadmin

Given

- 2 config names each with an allow-list entry of the public scope kind, and one Regular user with no permission
  - Domain home-1
  - Config definition definition-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Config definition definition-2: the config of this name is registered
  - Allow-list entry entry-2: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.admin_search: user-1 searches every entry without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading_many-an-empty-id-list-answers-empty"></a>

#### [an-empty-id-list-answers-empty](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py): pass

loading with an empty ID list answers an empty list

Given

- the PUBLIC and USER allow-list entries of one config name, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.batch_load_by_ids: user-1 loads with an empty ID list

Then

- an empty response comes back
  - items = []

<a id="reading_many-duplicate-ids-keep-their-input-positions"></a>

#### [duplicate-ids-keep-their-input-positions](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py): pass

when the superadmin loads the ID of the same allow_list twice, the same node comes back at both positions

Given

- the PUBLIC and USER allow-list entries of one config name, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.batch_load_by_ids: user-1 loads the ID of the first allow_list twice

Then

- the same allow_list comes back at both positions of the duplicate ID
  - items = 2
  - items[0].id: same as the first ID seeded in advance
  - items[1].id: same as the first ID seeded in advance

<a id="reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty"></a>

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py): pass

when the superadmin loads both allow_lists and one missing ID together, two nodes and None come back in input order

Given

- the PUBLIC and USER allow-list entries of one config name, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.batch_load_by_ids: user-1 loads both allow_lists and a missing ID in one call

Then

- the two existing IDs come back as nodes and the missing ID as None
  - items = 3
  - items[0].id: same as the first ID seeded in advance
  - items[1].id: same as the second ID seeded in advance
  - items[2] = None

<a id="reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id"></a>

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py): pass

when a plain user without permission loads both allow_lists and one missing ID together, an entity read permission error comes back at each input position

Given

- the PUBLIC and USER allow-list entries of one config name, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.batch_load_by_ids: user-1 loads both allow_lists and a missing ID in one call

Then

- a permission error comes back at each position, for the two existing IDs and the missing ID alike
  - items = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-reranks-none-of-several-entries"></a>

#### [a-user-granted-nothing-reranks-none-of-several-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_editing.py): pass

when a plain user without permission tries to change the rank of both allow_lists in one call, none is changed and both come back in the failed list for lack of permission

Given

- the PUBLIC and USER allow-list entries of one config name, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.partial_bulk_update: user-1 changes the rank of both allow_lists to 150 in one call

Then

- no allow_list is processed and both come back in the failed list for lack of permission
  - successes = []
  - failed count = 2
  - failed[0].id: same as the ID seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the ID seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-a-user-granted-update-in-global-reranks-both-entries-at-once"></a>

#### [a-user-granted-update-in-global-reranks-both-entries-at-once](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_editing.py): pass

when a regular user granted the update permission on allow-list entries in the global scope changes the rank of both allow_lists in one call, both come back with the new rank and none failed

Given

- the PUBLIC and USER allow-list entries of one config name, and one regular user granted the UPDATE permission on allow-list entries in the global scope
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a user granted the UPDATE permission on allow-list entry in the global scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role global-1: applies only within the scope it is granted in
    - Role global-1: UPDATE allowed on every app_config_allow_list
    - regular user user-1: holds Role global-1

When

- AppConfigAllowListAdapter.partial_bulk_update: user-1 changes the rank of both allow_lists to 150 in one call

Then

- both allow_lists come back with the new rank and none failed
  - successes count = 2
  - failed = []
  - successes[0].id: same as the ID seeded in advance
  - successes[0].config_name = 'config-1'
  - successes[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - successes[0].rank = 150
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the ID seeded in advance
  - successes[1].config_name = 'config-1'
  - successes[1].scope_type = <AppConfigScopeType.USER: 'user'>
  - successes[1].rank = 150
  - successes[1].updated_at: the time this run wrote

<a id="partial_bulk_editing-the-superadmin-reranks-several-entries-at-once"></a>

#### [the-superadmin-reranks-several-entries-at-once](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_editing.py): pass

when the superadmin changes the rank of both allow_lists in one call, both come back with the new rank and none failed

Given

- the PUBLIC and USER allow-list entries of one config name, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.partial_bulk_update: user-1 changes the rank of both allow_lists to 150 in one call

Then

- both allow_lists come back with the new rank and none failed
  - successes count = 2
  - failed = []
  - successes[0].id: same as the ID seeded in advance
  - successes[0].config_name = 'config-1'
  - successes[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - successes[0].rank = 150
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the ID seeded in advance
  - successes[1].config_name = 'config-1'
  - successes[1].scope_type = <AppConfigScopeType.USER: 'user'>
  - successes[1].rank = 150
  - successes[1].updated_at: the time this run wrote

### update

<a id="editing-an-edit-carrying-no-value-changes-nothing"></a>

#### [an-edit-carrying-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py): pass

when the superadmin edits without naming any value, the node comes back with nothing changed

Given

- one allow-list entry of the user scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.update: user-1 edits the allow_list of config-1 (an empty request)

Then

- every field of the prepared allow-list entry comes back
  - id: same as the prepared id
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-the-superadmin-changes-an-entrys-rank"></a>

#### [the-superadmin-changes-an-entrys-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py): pass

with one allow_list laid, when the superadmin changes the rank, only the rank changes and the config name and scope kind stay the same

Given

- one allow-list entry of the user scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.update: user-1 edits the allow_list of config-1 (rank to 150)

Then

- every field of the prepared allow-list entry comes back
  - id: same as the prepared id
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 150
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-who-is-not-the-superadmin-may-not-change-a-rank"></a>

#### [a-user-who-is-not-the-superadmin-may-not-change-a-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py): pass

when a plain user without permission edits the same allow_list, the call is rejected because the user has no entity update permission

Given

- one allow-list entry of the user scope kind, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.update: user-1 edits the allow_list of config-1 (rank to 150)

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py): pass

when the superadmin edits the rank of a missing ID, the call is rejected because there is no such target

Given

- one allow-list entry of the public scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.update: user-1 edits a missing ID (rank to 150)

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-entries"></a>

#### [a-user-granted-nothing-purges-none-of-several-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_purging.py): pass

when a plain user without permission tries to purge both allow_lists in one call, none is deleted and both come back in the failed list for lack of permission

Given

- the PUBLIC and USER allow-list entries of one config name, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.partial_bulk_purge: user-1 purges both allow_lists in one call

Then

- no allow_list is processed and both come back in the failed list for lack of permission
  - successes = []
  - failed count = 2
  - failed[0].id: same as the ID seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the ID seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-a-user-granted-purge-in-global-purges-both-entries-at-once"></a>

#### [a-user-granted-purge-in-global-purges-both-entries-at-once](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_purging.py): pass

when a regular user granted the purge permission on allow-list entries in the global scope purges both allow_lists in one call, both come back in the processed list and none failed

Given

- the PUBLIC and USER allow-list entries of one config name, and one regular user granted the HARD_DELETE permission on allow-list entries in the global scope
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a user granted the HARD_DELETE permission on allow-list entry in the global scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role global-1: applies only within the scope it is granted in
    - Role global-1: HARD_DELETE allowed on every app_config_allow_list
    - regular user user-1: holds Role global-1

When

- AppConfigAllowListAdapter.partial_bulk_purge: user-1 purges both allow_lists in one call

Then

- both allow_lists come back in the processed list and none failed
  - successes count = 2
  - successes: same as the two IDs seeded in advance
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_partial_bulk_purging.py): pass

when the superadmin purges both allow_lists and a missing ID in one call, the two come back in the processed list and the missing ID comes back in the failed list because there is no such target

Given

- the PUBLIC and USER allow-list entries of one config name, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry first-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Allow-list entry second-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigAllowListAdapter.partial_bulk_purge: user-1 purges both allow_lists and a missing ID in one call

Then

- both allow_lists come back in the processed list, and the missing ID comes back in the failed list because there is no such target
  - successes: same as the two IDs seeded in advance
  - failed count = 1
  - failed[0].id: same as the missing ID in the request
  - failed[0].message: a reason containing 'not found'

### purge

<a id="purging-an-entry-holding-a-fragment-is-still-purged"></a>

#### [an-entry-holding-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py): pass

when the superadmin purges an allow_list that has a config fragment, the fragment does not block it and the ID of the allow_list comes back

Given

- one allow-list entry of the public scope kind holding a config fragment, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light'}

When

- AppConfigAllowListAdapter.purge: user-1 purges the allow_list of config-1

Then

- the ID of the purged allow_list comes back
  - id: same as the ID seeded in advance

<a id="purging-the-superadmin-purges-an-entry"></a>

#### [the-superadmin-purges-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py): pass

when the superadmin purges an allow_list with no config fragment, the ID of the purged allow_list comes back

Given

- one allow-list entry of the user scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.purge: user-1 purges the allow_list of config-1

Then

- the ID of the purged allow_list comes back
  - id: same as the ID seeded in advance

<a id="purging-a-user-who-is-not-the-superadmin-may-not-purge-an-entry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py): pass

when a plain user without permission purges the same allow_list, the call is rejected because the user has no entity delete permission

Given

- one allow-list entry of the user scope kind, and one Regular user with no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.purge: user-1 purges the allow_list of config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py): pass

when the superadmin purges a missing ID, the call is rejected because there is no such target

Given

- one allow-list entry of the public scope kind, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind

When

- AppConfigAllowListAdapter.purge: user-1 purges a missing ID

Then

- the call is rejected
  - rejected: EntityNotFoundError

