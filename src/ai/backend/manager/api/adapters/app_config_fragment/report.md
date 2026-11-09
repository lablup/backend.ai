## app_config_fragment

[background](/src/ai/backend/manager/api/adapters/app_config_fragment/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/app_config_fragment/adapter.py)

Scenario: incomplete 1 / 10

- built from ops (10)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - my_app_config_fragments_by_names: representative success ✓ · representative rejection ✓
  - my_atomic_bulk_upsert: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - scoped_app_config_fragments_by_names: representative success ✓ · representative rejection ✓
  - scoped_atomic_bulk_upsert: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓

**admin_search**

| scenario | verdict |
|---|---|
| [when four fragments exist across the public, domain and user scopes and the superadmin searches everything, all four are counted. The global search checks whether the caller is the superadmin](#searching-the-superadmin-counts-every-fragment-across-scopes) | answered |
| [when a user granted read permission on their own domain scope but who is not the superadmin searches everything, it is rejected for lack of role. Searching one scope and searching everything take different paths](#searching-a-user-granted-read-may-not-search-every-fragment) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [an empty id list answers empty without calling anything below](#reading_many-an-empty-id-list-answers-empty-without-calling-anything) | answered |
| [when the superadmin reads two fragments and one missing id at once, the two come back as nodes and the item for the missing id is empty. Only a user who passes the permission check sees an empty item](#reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty) | answered |
| [when a user granted read permission only on their own scope reads their own fragment, another user's fragment and a missing id at once, in list order the own one comes back as a node and the others are rejected for that item alone for lack of permission](#reading_many-mine-anothers-and-a-missing-id-are-each-answered-in-order-for-a-plain-user) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user with one own fragment and read permission on their own scope reads by id, the whole fragment comes back](#reading-a-user-granted-read-on-their-own-scope-reads-their-fragment-by-id) | answered |
| [when a user granted read permission only on their own scope reads another user's fragment by id, it is rejected for lack of permission](#reading-a-user-granted-read-on-their-own-scope-may-not-read-another-users-fragment) | rejected |
| [when the superadmin reads by a missing id, it is rejected because no such target exists. Only a user who passes the permission check sees this answer](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted read permission on their own scope reads a missing id, it is rejected for lack of permission, not for a missing target, because a row that does not exist holds no permission either](#reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user) | rejected |

**my_app_config_fragments_by_names**

| scenario | verdict |
|---|---|
| [even when another user's fragment has the same name, reading the user's own fragments answers only their own](#reading_by_names-another-users-fragment-under-the-same-name-is-not-answered) | answered |
| [even when a fragment of the user's own domain has the same name, reading the user's own fragments answers only their own. This read sees the user scope alone](#reading_by_names-the-domains-fragment-under-the-same-name-is-not-answered) | answered |
| [when two of the three names opened to the user scope hold the user's own fragment and a user granted read permission reads the three names, three items come back in request order and the item without a fragment is empty](#reading_by_names-three-names-answer-a-fragment-or-an-empty-slot-each-in-request-order) | answered |
| [even when the user has their own fragment, a user with no permission reading by name is rejected for lack of permission](#reading_by_names-a-user-granted-nothing-may-not-read-their-own-fragments) | rejected |

**my_atomic_bulk_upsert**

| scenario | verdict |
|---|---|
| [when a user granted write permission writes their own fragment for the first time, the node comes back with the owner and scope kind the request left out filled from the caller](#writing-a-user-granted-write-writes-their-first-own-fragment) | answered |
| [when two names opened to the user scope are written at once, both are written and come back in request order](#writing-several-names-are-written-at-once-in-request-order) | answered |
| [turning the permission check off lets a user with no permission write their own fragment](#writing-turning-enforcement-off-lets-a-user-granted-nothing-write) | answered |
| [when a name that already holds the user's own fragment is written again with different keys, the id stays the same and the value holds the new value alone. The earlier keys do not remain](#writing-writing-the-same-name-again-replaces-the-value-whole) | answered |
| [when a user granted write permission writes to an unregistered name, it is rejected as write not allowed](#writing-a-name-nothing-registers-cannot-be-written) | rejected |
| [when a user granted write permission writes their own fragment to a name opened only to the domain kind, it is rejected as write not allowed. It is the same check as for an unregistered name](#writing-a-name-opened-only-to-the-domain-kind-cannot-be-written-by-a-user) | rejected |
| [when a user who holds only create permission on their own scope and no update permission writes, it is rejected for lack of permission. A write requires both create and update permission](#writing-a-user-granted-create-alone-may-not-write) | rejected |
| [when a user with no permission writes to a name opened to the user kind, it is rejected for lack of permission](#writing-a-user-granted-nothing-may-not-write-their-own-fragment) | rejected |
| [when an opened name and an unopened name are written together, it is rejected as write not allowed. A write is all or nothing](#writing-one-name-not-opened-to-the-user-kind-refuses-the-whole-write) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted delete permission only on their own scope deletes two own fragments, another user's fragment and a missing id at once, the two own fragments come back in the succeeded list and the others come back in the failed list together with the reason](#purging-mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user) | answered |
| [when the superadmin deletes two fragments and one missing id at once, the two come back in the succeeded list and the missing id comes back in the failed list](#purging-the-superadmin-purges-both-and-a-missing-id-fails-alone) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a user with one own fragment and delete permission on their own scope deletes it, an answer holding the deleted id comes back](#purging-a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment) | answered |
| [when a user granted delete permission only on their own scope deletes another user's fragment, it is rejected for lack of permission](#purging-a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment) | rejected |
| [when a user granted only read permission on their own fragment deletes it, it is rejected for lack of permission. Delete checks a permission other than read](#purging-a-user-granted-read-alone-may-not-purge-their-fragment) | rejected |
| [when the superadmin deletes a missing id, it is rejected because no such target exists](#purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**scoped_app_config_fragments_by_names**

| scenario | verdict |
|---|---|
| [when a domain fragment exists and a user granted read permission on that domain scope reads by naming the domain, that fragment comes back](#reading_by_names-a-user-granted-read-on-the-domain-reads-its-fragment-by-name) | answered |
| [when a public fragment exists and a user with no permission reads by naming the public scope, that fragment comes back. A public fragment has no scope to protect](#reading_by_names-anyone-signed-in-reads-a-public-fragment-by-name) | answered |
| [when the superadmin reads by naming an id that belongs to no domain, it is rejected because no such target exists. Only a user who passes the permission check sees this answer](#reading_by_names-a-domain-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted read permission on their own domain reads by naming an id that belongs to no domain, it is rejected for lack of permission, not for a missing target](#reading_by_names-a-domain-nothing-answers-to-is-refused-as-permission-for-a-plain-user) | rejected |
| [when a user granted read permission only on their own scope reads by naming another user, it is rejected for lack of permission](#reading_by_names-a-user-granted-read-on-their-own-scope-may-not-read-another-users) | rejected |

**scoped_atomic_bulk_upsert**

| scenario | verdict |
|---|---|
| [when a user granted write permission on their own domain scope writes by naming the domain, the scope kind is domain and the owner is that domain](#writing-a-user-granted-write-on-the-domain-writes-a-domain-fragment) | answered |
| [when the superadmin writes by naming the public scope, the scope kind is public and the owner field is empty. A public write checks whether the caller is the superadmin](#writing-the-superadmin-writes-a-public-fragment-owned-by-no-one) | answered |
| [when a user granted write permission only on their own scope writes by naming another user, it is rejected for lack of permission](#writing-a-user-granted-write-on-their-own-scope-may-not-write-at-another-users) | rejected |
| [when a user who is not the superadmin, even with write permission on their own domain scope, writes by naming the public scope, it is rejected for lack of role. A public fragment has no corresponding scope](#writing-a-user-who-is-not-the-superadmin-may-not-write-a-public-fragment) | rejected |
| [when the superadmin writes by naming an id that belongs to no user as the owner, it is rejected as no such owner. Whether an owner exists is checked in the permission graph](#writing-the-superadmin-naming-an-owner-nothing-answers-to-is-refused) | rejected |
| [turning the permission check off still does not let a user who is not the superadmin write a public fragment](#writing-turning-enforcement-off-still-does-not-let-a-user-write-a-public-fragment) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when two public fragments exist and a user with no permission searches by naming the public scope, both are counted. A public fragment has no scope to protect](#searching-anyone-signed-in-searches-the-public-scope) | answered |
| [when two own fragments and one fragment of another user exist and a user granted read permission on their own scope searches their own scope, only the two own fragments are counted](#searching-searching-my-own-scope-counts-only-my-fragments) | answered |
| [when the superadmin searches by naming an id that belongs to no domain, it is rejected because no such target exists](#searching-a-domain-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted read permission only on their own scope searches by naming another user, it is rejected for lack of permission](#searching-a-user-granted-read-on-their-own-scope-may-not-search-another-users) | rejected |
| [when a user granted read permission searches by naming a domain and a user together, it is rejected as bad input. This search runs in one scope only](#searching-naming-two-scopes-at-once-is-refused-as-bad-input) | rejected |

### admin_search

<a id="searching-the-superadmin-counts-every-fragment-across-scopes"></a>

#### [the-superadmin-counts-every-fragment-across-scopes](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when four fragments exist across the public, domain and user scopes and the superadmin searches everything, all four are counted. The global search checks whether the caller is the superadmin

Given

- 2 fragments of their own, 1 fragments of their own domain, 1 public fragments, and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition mine-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment own-fragment-2: value {'mine': 1}
  - Prepare a config name opened in the domain scope
    - Config definition domains-1: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - app config fragment domain-fragment-1: value {'domains': 0}
  - Prepare a config name opened in the public scope
    - Config definition publics-1: the config of this name is registered
    - Allow-list entry entry-4: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'publics': 0}

When

- AppConfigFragmentAdapter.admin_search: user-1 reads everything without a filter

Then

- every fragment made in advance is counted across scopes
  - items = 4
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-read-may-not-search-every-fragment"></a>

#### [a-user-granted-read-may-not-search-every-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when a user granted read permission on their own domain scope but who is not the superadmin searches everything, it is rejected for lack of role. Searching one scope and searching everything take different paths

Given

- 1 fragments of their own domain, and one user granted the READ permission on config fragments in their own domain
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in Domain home-1
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role seated-1: applies only within the scope it is granted in
    - Role seated-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role seated-1
  - Prepare a config name opened in the domain scope
    - Config definition domains-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - app config fragment domain-fragment-1: value {'domains': 0}

When

- AppConfigFragmentAdapter.admin_search: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading_many-an-empty-id-list-answers-empty-without-calling-anything"></a>

#### [an-empty-id-list-answers-empty-without-calling-anything](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py): pass

an empty id list answers empty without calling anything below

Given

- 1 fragments of their own, one fragment of another user, and one user with no config fragment permission
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty"></a>

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py): pass

when the superadmin reads two fragments and one missing id at once, the two come back as nodes and the item for the missing id is empty. Only a user who passes the permission check sees an empty item

Given

- 1 fragments of their own, one fragment of another user, and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids: user-1 reads their own fragment, another user's fragment and a missing id at once

Then

- the two existing items come back as nodes and the item for the missing id is empty
  - items = 3
  - items[0].id: same as the user's own fragment made in advance
  - items[1].id: same as another user's fragment made in advance
  - items[2] = None

<a id="reading_many-mine-anothers-and-a-missing-id-are-each-answered-in-order-for-a-plain-user"></a>

#### [mine-anothers-and-a-missing-id-are-each-answered-in-order-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_many.py): pass

when a user granted read permission only on their own scope reads their own fragment, another user's fragment and a missing id at once, in list order the own one comes back as a node and the others are rejected for that item alone for lack of permission

Given

- 1 fragments of their own, one fragment of another user, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.batch_load_by_ids: user-1 reads their own fragment, another user's fragment and a missing id at once

Then

- the user's own comes back as a node, and another user's and the missing id are rejected for that item alone
  - items = 3
  - items[0].id: same as the user's own fragment made in advance
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-on-their-own-scope-reads-their-fragment-by-id"></a>

#### [a-user-granted-read-on-their-own-scope-reads-their-fragment-by-id](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py): pass

when a user with one own fragment and read permission on their own scope reads by id, the whole fragment comes back

Given

- their own fragment and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get: user-1 reads the fragment of config-1

Then

- the whole config fragment made in advance comes back
  - id: same as the fragment made in advance
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - scope_id: same as the owner of the fragment made in advance
  - config = {'theme': 'mine'}
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-user-granted-read-on-their-own-scope-may-not-read-another-users-fragment"></a>

#### [a-user-granted-read-on-their-own-scope-may-not-read-another-users-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py): pass

when a user granted read permission only on their own scope reads another user's fragment by id, it is rejected for lack of permission

Given

- another user's fragment and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - app config fragment anothers-fragment-1: value {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.get: user-1 reads the fragment of config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py): pass

when the superadmin reads by a missing id, it is rejected because no such target exists. Only a user who passes the permission check sees this answer

Given

- their own fragment and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get: user-1 reads by a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"></a>

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading.py): pass

when a user granted read permission on their own scope reads a missing id, it is rejected for lack of permission, not for a missing target, because a row that does not exist holds no permission either

Given

- their own fragment and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.get: user-1 reads by a missing id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_app_config_fragments_by_names

<a id="reading_by_names-another-users-fragment-under-the-same-name-is-not-answered"></a>

#### [another-users-fragment-under-the-same-name-is-not-answered](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

even when another user's fragment has the same name, reading the user's own fragments answers only their own

Given

- their own fragments on 1 of 1 config names opened in the user scope, another user's fragment of the same name, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'slot': 0}
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - app config fragment anothers-fragment-1: value {'theirs': True}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names: user-1 reads their own fragments for config-1

Then

- for each name, their own fragment if one exists and an empty item otherwise, in request order
  - items = 1
  - items[0].id: same as the fragment of their own made in advance
  - items[0].config = {'slot': 0}

<a id="reading_by_names-the-domains-fragment-under-the-same-name-is-not-answered"></a>

#### [the-domains-fragment-under-the-same-name-is-not-answered](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

even when a fragment of the user's own domain has the same name, reading the user's own fragments answers only their own. This read sees the user scope alone

Given

- their own fragments on 1 of 1 config names opened in the user scope, their domain's fragment of the same name, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user, domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Allow-list entry entry-2: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'slot': 0}
  - app config fragment domain-fragment-1: value {'domains': True}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names: user-1 reads their own fragments for config-1

Then

- for each name, their own fragment if one exists and an empty item otherwise, in request order
  - items = 1
  - items[0].id: same as the fragment of their own made in advance
  - items[0].config = {'slot': 0}

<a id="reading_by_names-three-names-answer-a-fragment-or-an-empty-slot-each-in-request-order"></a>

#### [three-names-answer-a-fragment-or-an-empty-slot-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when two of the three names opened to the user scope hold the user's own fragment and a user granted read permission reads the three names, three items come back in request order and the item without a fragment is empty

Given

- their own fragments on 2 of 3 config names opened in the user scope, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition config-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition config-3: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'slot': 0}
  - app config fragment own-fragment-2: value {'slot': 2}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names: user-1 reads their own fragments for config-1, config-2, config-3

Then

- for each name, their own fragment if one exists and an empty item otherwise, in request order
  - items = 3
  - items[0].id: same as the fragment of their own made in advance
  - items[0].config = {'slot': 0}
  - items[1] = None
  - items[2].id: same as the fragment of their own made in advance
  - items[2].config = {'slot': 2}

<a id="reading_by_names-a-user-granted-nothing-may-not-read-their-own-fragments"></a>

#### [a-user-granted-nothing-may-not-read-their-own-fragments](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

even when the user has their own fragment, a user with no permission reading by name is rejected for lack of permission

Given

- their own fragments on 1 of 1 config names opened in the user scope, and one user with no config fragment permission
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'slot': 0}

When

- AppConfigFragmentAdapter.my_app_config_fragments_by_names: user-1 reads their own fragments for config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_atomic_bulk_upsert

<a id="writing-a-user-granted-write-writes-their-first-own-fragment"></a>

#### [a-user-granted-write-writes-their-first-own-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user granted write permission writes their own fragment for the first time, the node comes back with the owner and scope kind the request left out filled from the caller

Given

- one config name opened in the user scope, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- every config fragment written comes back in request order
  - items = 1
  - items[0].id: skipped: the database generates it
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="writing-several-names-are-written-at-once-in-request-order"></a>

#### [several-names-are-written-at-once-in-request-order](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when two names opened to the user scope are written at once, both are written and come back in request order

Given

- one config name opened in the user scope, and 1 config names opened in the user scope, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition opened-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1, opened-1

Then

- every config fragment written comes back in request order
  - items = 2
  - items[0].id: skipped: the database generates it
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].config_name: same as the requested name
  - items[1].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[1].scope_id: same as the named owner
  - items[1].config = {'editor': {'wrap': True}}
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote

<a id="writing-turning-enforcement-off-lets-a-user-granted-nothing-write"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

turning the permission check off lets a user with no permission write their own fragment

Given

- one config name opened in the user scope, and one user with no config fragment permission
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- every config fragment written comes back in request order
  - items = 1
  - items[0].id: skipped: the database generates it
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="writing-writing-the-same-name-again-replaces-the-value-whole"></a>

#### [writing-the-same-name-again-replaces-the-value-whole](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a name that already holds the user's own fragment is written again with different keys, the id stays the same and the value holds the new value alone. The earlier keys do not remain

Given

- one config name opened in the user scope with an existing fragment of their own, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'light', 'menu': {'home': True}}

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- every config fragment written comes back in request order
  - items = 1
  - items[0].id: same as the fragment that already existed
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.USER: 'user'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'menu': {'docs': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="writing-a-name-nothing-registers-cannot-be-written"></a>

#### [a-name-nothing-registers-cannot-be-written](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user granted write permission writes to an unregistered name, it is rejected as write not allowed

Given

- an unregistered config name, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for unregistered

Then

- the call is rejected
  - rejected: AppConfigFragmentWriteNotAllowed

<a id="writing-a-name-opened-only-to-the-domain-kind-cannot-be-written-by-a-user"></a>

#### [a-name-opened-only-to-the-domain-kind-cannot-be-written-by-a-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user granted write permission writes their own fragment to a name opened only to the domain kind, it is rejected as write not allowed. It is the same check as for an unregistered name

Given

- one config name opened in the domain scope, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- the call is rejected
  - rejected: AppConfigFragmentWriteNotAllowed

<a id="writing-a-user-granted-create-alone-may-not-write"></a>

#### [a-user-granted-create-alone-may-not-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user who holds only create permission on their own scope and no update permission writes, it is rejected for lack of permission. A write requires both create and update permission

Given

- one config name opened in the user scope, and one user granted the CREATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="writing-a-user-granted-nothing-may-not-write-their-own-fragment"></a>

#### [a-user-granted-nothing-may-not-write-their-own-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user with no permission writes to a name opened to the user kind, it is rejected for lack of permission

Given

- one config name opened in the user scope, and one user with no config fragment permission
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="writing-one-name-not-opened-to-the-user-kind-refuses-the-whole-write"></a>

#### [one-name-not-opened-to-the-user-kind-refuses-the-whole-write](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when an opened name and an unopened name are written together, it is rejected as write not allowed. A write is all or nothing

Given

- one config name opened in the user scope, and 1 config names opened in no scope, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a config name opened in no scope
    - Config definition unopened-1: the config of this name is registered

When

- AppConfigFragmentAdapter.my_atomic_bulk_upsert: user-1 writes their own fragments for config-1, unopened-1

Then

- the call is rejected
  - rejected: AppConfigFragmentWriteNotAllowed

### partial_bulk_purge

<a id="purging-mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user"></a>

#### [mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when a user granted delete permission only on their own scope deletes two own fragments, another user's fragment and a missing id at once, the two own fragments come back in the succeeded list and the others come back in the failed list together with the reason

Given

- 2 fragments of their own, one fragment of another user, and one user granted the HARD_DELETE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the HARD_DELETE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: HARD_DELETE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition mine-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment own-fragment-2: value {'mine': 1}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.partial_bulk_purge: user-1 deletes 2 own fragments, another user's fragment and a missing id at once

Then

- the user's own fragments come back in the succeeded list, and another user's fragment and the missing id come back in the failed list
  - successes: same as the user's own fragments made in advance
  - failed = 2
  - failed[0].id: same as another user's fragment made in advance
  - failed[*].message: skipped: the reason comes as a string, and a string is a value that may change

<a id="purging-the-superadmin-purges-both-and-a-missing-id-fails-alone"></a>

#### [the-superadmin-purges-both-and-a-missing-id-fails-alone](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when the superadmin deletes two fragments and one missing id at once, the two come back in the succeeded list and the missing id comes back in the failed list

Given

- 1 fragments of their own, one fragment of another user, and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.partial_bulk_purge: user-1 deletes 1 own fragments, another user's fragment and a missing id at once

Then

- the two existing fragments come back in the succeeded list, and the missing id comes back in the failed list
  - successes: same as the fragments made in advance
  - failed = 1
  - failed[*].message: skipped: the reason comes as a string, and a string is a value that may change

### purge

<a id="purging-a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment"></a>

#### [a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when a user with one own fragment and delete permission on their own scope deletes it, an answer holding the deleted id comes back

Given

- their own fragment and one user granted the HARD_DELETE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the HARD_DELETE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: HARD_DELETE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge: user-1 deletes the fragment of config-1

Then

- it answers with the id of the deleted fragment
  - id: same as the fragment made in advance

<a id="purging-a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment"></a>

#### [a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when a user granted delete permission only on their own scope deletes another user's fragment, it is rejected for lack of permission

Given

- another user's fragment and one user granted the HARD_DELETE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the HARD_DELETE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: HARD_DELETE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - app config fragment anothers-fragment-1: value {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.purge: user-1 deletes the fragment of config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-a-user-granted-read-alone-may-not-purge-their-fragment"></a>

#### [a-user-granted-read-alone-may-not-purge-their-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when a user granted only read permission on their own fragment deletes it, it is rejected for lack of permission. Delete checks a permission other than read

Given

- their own fragment and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge: user-1 deletes the fragment of config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_purging.py): pass

when the superadmin deletes a missing id, it is rejected because no such target exists

Given

- their own fragment and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'mine'}

When

- AppConfigFragmentAdapter.purge: user-1 deletes a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### scoped_app_config_fragments_by_names

<a id="reading_by_names-a-user-granted-read-on-the-domain-reads-its-fragment-by-name"></a>

#### [a-user-granted-read-on-the-domain-reads-its-fragment-by-name](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when a domain fragment exists and a user granted read permission on that domain scope reads by naming the domain, that fragment comes back

Given

- one config name opened in their own domain and one config fragment there, and one user granted the READ permission on config fragments in their own domain
  - Domain home-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - Prepare a user granted the READ permission on config fragment in Domain home-1
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role seated-1: applies only within the scope it is granted in
    - Role seated-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role seated-1
  - app config fragment fragment-1: value {'theme': 'domain'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names: user-1 reads the fragment of config-1 in the domain scope

Then

- the config fragment of the named scope comes back
  - items = 1
  - items[0].id: same as the fragment made in advance
  - items[0].scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'theme': 'domain'}

<a id="reading_by_names-anyone-signed-in-reads-a-public-fragment-by-name"></a>

#### [anyone-signed-in-reads-a-public-fragment-by-name](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when a public fragment exists and a user with no permission reads by naming the public scope, that fragment comes back. A public fragment has no scope to protect

Given

- one config name opened in the public scope and one config fragment there, and one user with no config fragment permission
  - Domain home-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - public app config fragment public-fragment-1: value {'theme': 'public'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names: user-1 reads the fragment of config-1 in the public scope

Then

- the config fragment of the named scope comes back
  - items = 1
  - items[0].id: same as the fragment made in advance
  - items[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - items[0].scope_id: same as no owner
  - items[0].config = {'theme': 'public'}

<a id="reading_by_names-a-domain-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [a-domain-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when the superadmin reads by naming an id that belongs to no domain, it is rejected because no such target exists. Only a user who passes the permission check sees this answer

Given

- one config name opened in their own domain, and one superadmin
  - Domain home-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names: user-1 reads the fragment of config-1 by naming an id that belongs to no domain

Then

- the call is rejected
  - rejected: DomainNotFound

<a id="reading_by_names-a-domain-nothing-answers-to-is-refused-as-permission-for-a-plain-user"></a>

#### [a-domain-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when a user granted read permission on their own domain reads by naming an id that belongs to no domain, it is rejected for lack of permission, not for a missing target

Given

- one config name opened in their own domain, and one user granted the READ permission on config fragments in their own domain
  - Domain home-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - Prepare a user granted the READ permission on config fragment in Domain home-1
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role seated-1: applies only within the scope it is granted in
    - Role seated-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role seated-1

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names: user-1 reads the fragment of config-1 by naming an id that belongs to no domain

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_by_names-a-user-granted-read-on-their-own-scope-may-not-read-another-users"></a>

#### [a-user-granted-read-on-their-own-scope-may-not-read-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_reading_by_names.py): pass

when a user granted read permission only on their own scope reads by naming another user, it is rejected for lack of permission

Given

- one config name opened in another user and one config fragment there, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - app config fragment fragment-1: value {'theme': 'theirs'}

When

- AppConfigFragmentAdapter.scoped_app_config_fragments_by_names: user-1 reads the fragment of config-1 in the user scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_atomic_bulk_upsert

<a id="writing-a-user-granted-write-on-the-domain-writes-a-domain-fragment"></a>

#### [a-user-granted-write-on-the-domain-writes-a-domain-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user granted write permission on their own domain scope writes by naming the domain, the scope kind is domain and the owner is that domain

Given

- one config name opened in their own domain, and one user granted the CREATE, UPDATE permission on config fragments in their own domain
  - Domain home-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in Domain home-1
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role seated-1: applies only within the scope it is granted in
    - Role seated-1: CREATE allowed on every app_config_fragment
    - Role seated-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role seated-1

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the domain scope

Then

- every config fragment written comes back in request order
  - items = 1
  - items[0].id: skipped: the database generates it
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - items[0].scope_id: same as the named owner
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="writing-the-superadmin-writes-a-public-fragment-owned-by-no-one"></a>

#### [the-superadmin-writes-a-public-fragment-owned-by-no-one](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when the superadmin writes by naming the public scope, the scope kind is public and the owner field is empty. A public write checks whether the caller is the superadmin

Given

- one config name opened in the public scope, and one superadmin
  - Domain home-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the public scope

Then

- every config fragment written comes back in request order
  - items = 1
  - items[0].id: skipped: the database generates it
  - items[0].config_name: same as the requested name
  - items[0].scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - items[0].scope_id: same as no owner
  - items[0].config = {'theme': 'light', 'menu': {'home': True}}
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="writing-a-user-granted-write-on-their-own-scope-may-not-write-at-another-users"></a>

#### [a-user-granted-write-on-their-own-scope-may-not-write-at-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user granted write permission only on their own scope writes by naming another user, it is rejected for lack of permission

Given

- one config name opened in another user, and one user granted the CREATE, UPDATE permission on config fragments in their own scope
  - Domain home-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: CREATE allowed on every app_config_fragment
    - Role own-scope-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the user scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="writing-a-user-who-is-not-the-superadmin-may-not-write-a-public-fragment"></a>

#### [a-user-who-is-not-the-superadmin-may-not-write-a-public-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when a user who is not the superadmin, even with write permission on their own domain scope, writes by naming the public scope, it is rejected for lack of role. A public fragment has no corresponding scope

Given

- one config name opened in the public scope, and one user granted the CREATE, UPDATE permission on config fragments in their own domain
  - Domain home-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare a user granted the CREATE, UPDATE permission on config fragment in Domain home-1
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role seated-1: applies only within the scope it is granted in
    - Role seated-1: CREATE allowed on every app_config_fragment
    - Role seated-1: UPDATE allowed on every app_config_fragment
    - regular user user-1: holds Role seated-1

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the public scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="writing-the-superadmin-naming-an-owner-nothing-answers-to-is-refused"></a>

#### [the-superadmin-naming-an-owner-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

when the superadmin writes by naming an id that belongs to no user as the owner, it is rejected as no such owner. Whether an owner exists is checked in the permission graph

Given

- one config name opened in an id that belongs to no user, and one superadmin
  - Domain home-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the user scope

Then

- the call is rejected
  - rejected: VirtualEntityNotFound

<a id="writing-turning-enforcement-off-still-does-not-let-a-user-write-a-public-fragment"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-write-a-public-fragment](/tests/scenario/bai_scenario/manager/app_config_fragment/test_writing.py): pass

turning the permission check off still does not let a user who is not the superadmin write a public fragment

Given

- one config name opened in the public scope, and one user with no config fragment permission
  - Domain home-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_atomic_bulk_upsert: user-1 writes a fragment at config-1 in the public scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### scoped_search

<a id="searching-anyone-signed-in-searches-the-public-scope"></a>

#### [anyone-signed-in-searches-the-public-scope](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when two public fragments exist and a user with no permission searches by naming the public scope, both are counted. A public fragment has no scope to protect

Given

- 2 public fragments, and one user with no config fragment permission
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public scope
    - Config definition publics-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Config definition publics-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'publics': 0}
  - public app config fragment public-fragment-2: value {'publics': 1}

When

- AppConfigFragmentAdapter.scoped_search: user-1 reads without a filter in the public scope

Then

- every config fragment of that scope is counted, and only those
  - items = ['publics-1', 'publics-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-searching-my-own-scope-counts-only-my-fragments"></a>

#### [searching-my-own-scope-counts-only-my-fragments](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when two own fragments and one fragment of another user exist and a user granted read permission on their own scope searches their own scope, only the two own fragments are counted

Given

- 2 fragments of their own, 1 fragments of another user, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition mine-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment own-fragment-2: value {'mine': 1}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.scoped_search: user-1 reads without a filter in the user scope

Then

- every config fragment of that scope is counted, and only those
  - items = ['mine-1', 'mine-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-domain-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [a-domain-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when the superadmin searches by naming an id that belongs to no domain, it is rejected because no such target exists

Given

- no config fragment, and one superadmin
  - Domain home-1
  - Prepare a user with no config fragment permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project

When

- AppConfigFragmentAdapter.scoped_search: user-1 reads without a filter in the domain scope

Then

- the call is rejected
  - rejected: DomainNotFound

<a id="searching-a-user-granted-read-on-their-own-scope-may-not-search-another-users"></a>

#### [a-user-granted-read-on-their-own-scope-may-not-search-another-users](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when a user granted read permission only on their own scope searches by naming another user, it is rejected for lack of permission

Given

- 1 fragments of their own, 1 fragments of another user, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
    - Config definition theirs-1: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}
  - app config fragment anothers-fragment-1: value {'theirs': 0}

When

- AppConfigFragmentAdapter.scoped_search: user-1 reads by naming another user

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="searching-naming-two-scopes-at-once-is-refused-as-bad-input"></a>

#### [naming-two-scopes-at-once-is-refused-as-bad-input](/tests/scenario/bai_scenario/manager/app_config_fragment/test_searching.py): pass

when a user granted read permission searches by naming a domain and a user together, it is rejected as bad input. This search runs in one scope only

Given

- 1 fragments of their own, and one user granted the READ permission on config fragments in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config fragment in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config_fragment
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition mine-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'mine': 0}

When

- AppConfigFragmentAdapter.scoped_search: user-1 reads by naming a domain and a user together

Then

- the call is rejected
  - rejected: InvalidAPIParameters

