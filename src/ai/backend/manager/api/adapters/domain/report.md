## domain

[background](/src/ai/backend/manager/api/adapters/domain/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/domain/adapter.py)

Scenario: complete

- built from ops (12)
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - bulk_lookup_names: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - global_search: representative success ✓ · representative rejection ✓
  - lookup_name: representative success ✓ · representative rejection ✓
  - partial_bulk_delete: representative success ✓ · representative rejection ✓
  - partial_bulk_restore: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - restore: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - create: success present 2 · rejection present 4 (global_scope)
  - purge: success present 1 · rejection present 4 (single_entity)

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when the superadmin reads several domains by id, the domain comes back for that item](#bulk_reading-the-superadmin-reads-domains-by-id) | answered |
| [when a user granted nothing reads several domains by id, that item is rejected for lack of permission](#bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id) | rejected |

**bulk_lookup_names**

| scenario | verdict |
|---|---|
| [a user granted nothing gets the same answer as the superadmin. This call checks authentication only, so whether a name exists is visible to anyone](#looking_up-a-user-granted-nothing-gets-the-same-ids-by-name) | answered |
| [when the superadmin looks up several ids for a name that exists and one that does not, the id of that domain comes back for the name that exists and an empty value for the name that does not](#looking_up-the-superadmin-looks-up-domains-by-name) | answered |
| [looking up several ids by name without a login context is rejected as user not found](#looking_up-looking-up-domains-by-name-without-login-is-refused) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes an already soft-deleted domain again, the answer says it was done and the domain comes back inactive](#deleting-soft-deleting-a-domain-already-soft-deleted) | answered |
| [when the superadmin soft deletes a domain, the answer says it was done and the domain comes back inactive](#deleting-the-superadmin-soft-deletes-a-domain) | answered |
| [a user granted nothing cannot soft delete a domain](#deleting-a-user-granted-nothing-may-not-soft-delete-a-domain) | rejected |
| [soft-deleting a name no domain answers to is rejected as not found](#deleting-soft-deleting-a-name-nothing-answers-to-is-not-found) | rejected |

**get**

| scenario | verdict |
|---|---|
| [with one domain laid, when the superadmin reads it by name, that domain comes back](#reading-the-superadmin-reads-a-domain-by-name) | answered |
| [when the superadmin soft deletes a domain and then reads it by name, that domain comes back carrying the inactive state](#reading-the-superadmin-reads-a-soft-deleted-domain-by-name) | answered |
| [with the same domain laid, when a user granted nothing reads it by name, the call is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-a-domain) | rejected |
| [when the superadmin reads by a name that does not exist, the call is rejected as not found, not for a permission problem](#reading-reading-a-name-nothing-answers-to-is-not-found) | rejected |

**global_search**

| scenario | verdict |
|---|---|
| [when several domains are searched with a filter on the name of one, only the domain of that name is left in the answer](#searching-a-name-filter-narrows-the-answer-to-the-domain-it-names) | answered |
| [when domains are searched with a filter on the name of a project one of them holds, only the domain holding that project is left](#nested_searching-a-project-name-filter-narrows-the-answer-to-the-domain-holding-it) | answered |
| [when domains are searched with a filter on the username of a user living in one of them, only the domain that user lives in is left](#nested_searching-a-username-filter-narrows-the-answer-to-the-domain-the-user-lives-in) | answered |
| [when domains are searched with a filter on the email of a user living in one of them, only the domain that user lives in is left](#nested_searching-an-email-filter-narrows-the-answer-to-the-domain-the-user-lives-in) | answered |
| [when domains are searched with a filter on inactive users, only the domain such a user lives in is left](#nested_searching-an-inactive-user-filter-narrows-the-answer-to-the-domain-they-live-in) | answered |
| [when every domain is searched ordered by the email of its users, the domain whose user's email comes first comes first](#nested_searching-ordering-by-the-email-puts-the-domains-in-that-order) | answered |
| [when every domain is searched ordered by the name of the project it holds, the domain holding the project whose name comes first comes first](#nested_searching-ordering-by-the-project-name-puts-the-domains-in-that-order) | answered |
| [when every domain is searched ordered by the username of its users, the domain whose user's name comes first comes first](#nested_searching-ordering-by-the-username-puts-the-domains-in-that-order) | answered |
| [when this scenario seeded four domains, a search without a filter brings back all four](#searching-the-answer-counts-every-domain-the-scenario-laid) | answered |
| [when one of the domains seeded in advance is soft-deleted and every domain is searched without a filter, that one comes back too](#searching-the-answer-includes-soft-deleted-domains-too) | answered |
| [when a user who is not the superadmin asks to search every domain, the role rejects it](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain) | rejected |

**lookup_name**

| scenario | verdict |
|---|---|
| [a user granted nothing can still look up a domain by name. This call checks authentication only, and the call receiving that id checks the permission](#looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name) | answered |
| [when the superadmin looks up a domain by name, the id of that domain comes back](#looking_up-the-superadmin-looks-up-a-domain-by-name) | answered |
| [looking up an id by a name no domain answers to is rejected as not found](#looking_up-looking-up-a-name-nothing-answers-to-is-not-found) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing soft-deletes several domains at once, none is soft-deleted and every one comes back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-domains) | answered |
| [when two active domains and one missing id are soft-deleted at once, the two come back inactive and the missing id comes back in the failed list because there is no such target](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |
| [soft-deleting several domains at once without a login context is rejected with the error saying no user is in the context](#partial_bulk_deleting-soft-deleting-domains-without-login-is-refused) | rejected |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted domains are restored at once, all of them come back active](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |
| [restoring several domains at once without a login context is rejected with the error saying no user is in the context](#partial_bulk_deleting-restoring-domains-without-login-is-refused) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing edits several domains at once, none is edited and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-domains) | answered |
| [when several domains are edited at once with a mix of active flags and descriptions, the one deactivated is soft-deleted and the one activated is restored, both come back with the new description, and the missing id comes back in the failed list because there is no such target](#partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-domains) | answered |
| [when the superadmin changes the description of several domains at once, all of them come back with the new description and none failed](#partial_bulk_editing-the-superadmin-edits-several-domains-at-once) | answered |
| [editing several domains at once without a login context is rejected with the error saying no user is in the context](#partial_bulk_editing-editing-domains-without-login-is-refused) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when the superadmin restores a domain that is not soft-deleted, the answer says it was restored and the domain comes back active](#deleting-restoring-a-domain-that-is-not-soft-deleted) | answered |
| [when a soft-deleted domain is restored, the answer says it was restored and the domain comes back active](#deleting-restoring-answers-that-it-restored) | answered |
| [a user granted nothing cannot restore a domain](#deleting-a-user-granted-nothing-may-not-restore-a-domain) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted the domain read role in a resource group scope searches in that scope, the same domains as the superadmin sees come back](#scoped_searching-a-user-granted-read-in-the-group-searches-its-domains) | answered |
| [when the superadmin searches in a resource group scope, only the domains that can use the group come back](#scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group) | answered |
| [when a user granted nothing searches in a resource group scope, the call is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group) | rejected |

**update**

| scenario | verdict |
|---|---|
| [an edit that turns the active flag off soft deletes the domain, and the response carries the inactive state](#editing-clearing-the-active-flag-soft-deletes-a-domain) | answered |
| [when the superadmin changes only the description of a domain, the description becomes the new value and the name stays](#editing-editing-a-description-leaves-the-name-alone) | answered |
| [when an edit turns the active flag off of a soft-deleted domain and changes the description, the description becomes the new value and the inactive state stays](#editing-lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest) | answered |
| [an edit that turns the active flag on of a soft-deleted domain restores it, and the response carries the active state](#editing-raising-the-active-flag-restores-a-soft-deleted-domain) | answered |
| [when a user granted nothing tries to edit a domain, the call is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-domain) | rejected |
| [editing a name no domain answers to is rejected as not found](#editing-editing-a-name-nothing-answers-to-is-not-found) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a domain, its model-store project is created too, and searching for the domain holding that project brings back the domain just created](#creating-creating-a-domain-also-creates-its-model-store-project) | answered |
| [when the superadmin creates a domain with only a name and a description, the whole node comes back with the values the request omitted filled from defaults](#creating-creating-a-domain-answers-with-the-whole-node) | answered |
| [a domain cannot be created when the name is only whitespace](#creating-a-blank-name-is-refused) | rejected |
| [when a domain is created with a name another domain already holds, it is rejected because the name is taken even when the caller has the permission](#creating-a-name-another-domain-already-holds-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a domain, the role rejects it regardless of how much permission the user holds](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain) | rejected |
| [turning entity permission enforcement off still rejects creating a domain, because a role checks this operation, not the permission graph](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [a domain nothing else refers to can be purged](#deleting-purging-a-domain-nothing-else-refers-to-succeeds) | answered |
| [a domain holding a project cannot be purged even by the superadmin](#deleting-a-domain-holding-a-project-is-not-purged) | rejected |
| [a domain holding a user cannot be purged even by the superadmin](#deleting-a-domain-holding-a-user-is-not-purged) | rejected |
| [a user granted nothing cannot purge a domain even when nothing else refers to it](#deleting-a-user-granted-nothing-may-not-purge-a-domain) | rejected |
| [purging a name no domain answers to is rejected as not found](#deleting-purging-a-name-nothing-answers-to-is-not-found) | rejected |

### bulk_get_ids

<a id="bulk_reading-the-superadmin-reads-domains-by-id"></a>

#### [the-superadmin-reads-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py): pass

when the superadmin reads several domains by id, the domain comes back for that item

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.bulk_get_ids: user-1 reads several by the id of target-1

Then

- the whole domain seeded in advance comes back for the item asked
  - [0].name = 'target-1'
  - [0].description = 'a domain that already existed'
  - [0].integration_name = None
  - [0].allowed_docker_registries = []
  - [0].is_active = True
  - [0].is_default = False
  - [0].id: skipped: the database generates it
  - [0].entity_id: same as the id of the domain seeded in advance
  - [0].created_at: the time this run wrote
  - [0].modified_at: the time this run wrote

<a id="bulk_reading-a-user-granted-nothing-may-not-read-domains-by-id"></a>

#### [a-user-granted-nothing-may-not-read-domains-by-id](/tests/scenario/bai_scenario/manager/domain/test_bulk_reading.py): pass

when a user granted nothing reads several domains by id, that item is rejected for lack of permission

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.bulk_get_ids: user-1 reads several by the id of target-1

Then

- the item asked is rejected
  - rejected: NotEnoughPermission

### bulk_lookup_names

<a id="looking_up-a-user-granted-nothing-gets-the-same-ids-by-name"></a>

#### [a-user-granted-nothing-gets-the-same-ids-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

a user granted nothing gets the same answer as the superadmin. This call checks authentication only, so whether a name exists is visible to anyone

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.bulk_lookup_names: user-1 looks up several ids for target-1 and no-such-domain

Then

- the id of that domain comes back for the name that exists, and an empty value for the name that does not
  - [0]: same as the id of the domain seeded in advance
  - [1] = None

<a id="looking_up-the-superadmin-looks-up-domains-by-name"></a>

#### [the-superadmin-looks-up-domains-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

when the superadmin looks up several ids for a name that exists and one that does not, the id of that domain comes back for the name that exists and an empty value for the name that does not

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.bulk_lookup_names: user-1 looks up several ids for target-1 and no-such-domain

Then

- the id of that domain comes back for the name that exists, and an empty value for the name that does not
  - [0]: same as the id of the domain seeded in advance
  - [1] = None

<a id="looking_up-looking-up-domains-by-name-without-login-is-refused"></a>

#### [looking-up-domains-by-name-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

looking up several ids by name without a login context is rejected as user not found

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.bulk_lookup_names: without a login context, looks up several ids for target-1

Then

- the call is rejected
  - rejected: UserNotFound

### delete

<a id="deleting-soft-deleting-a-domain-already-soft-deleted"></a>

#### [soft-deleting-a-domain-already-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

when the superadmin soft deletes an already soft-deleted domain again, the answer says it was done and the domain comes back inactive

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain twice-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.delete: user-1 soft deletes twice-1 twice

Then

- the answer says it was done and the domain comes back inactive
  - deleted = True
  - domain.name = 'twice-1'
  - domain.description = 'a domain that already existed'
  - domain.integration_name = None
  - domain.allowed_docker_registries = []
  - domain.is_active = False
  - domain.is_default = False
  - domain.id: skipped: the database generates it
  - domain.entity_id: same as the id of the domain seeded in advance
  - domain.created_at: the time this run wrote
  - domain.modified_at: the time this run wrote

<a id="deleting-the-superadmin-soft-deletes-a-domain"></a>

#### [the-superadmin-soft-deletes-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

when the superadmin soft deletes a domain, the answer says it was done and the domain comes back inactive

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain to-delete-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.delete: user-1 soft deletes to-delete-1

Then

- the answer says it was done and the domain comes back inactive
  - deleted = True
  - domain.name = 'to-delete-1'
  - domain.description = 'a domain that already existed'
  - domain.integration_name = None
  - domain.allowed_docker_registries = []
  - domain.is_active = False
  - domain.is_default = False
  - domain.id: skipped: the database generates it
  - domain.entity_id: same as the id of the domain seeded in advance
  - domain.created_at: the time this run wrote
  - domain.modified_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-domain"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a user granted nothing cannot soft delete a domain

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain untouchable-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.delete: user-1 soft deletes untouchable-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="deleting-soft-deleting-a-name-nothing-answers-to-is-not-found"></a>

#### [soft-deleting-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

soft-deleting a name no domain answers to is rejected as not found

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.delete: user-1 soft deletes no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get

<a id="reading-the-superadmin-reads-a-domain-by-name"></a>

#### [the-superadmin-reads-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

with one domain laid, when the superadmin reads it by name, that domain comes back

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.get: user-1 reads a domain by name host-1

Then

- the whole domain seeded in advance comes back
  - name = 'host-1'
  - description = 'a domain that already existed'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="reading-the-superadmin-reads-a-soft-deleted-domain-by-name"></a>

#### [the-superadmin-reads-a-soft-deleted-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

when the superadmin soft deletes a domain and then reads it by name, that domain comes back carrying the inactive state

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain soft-deleted-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.get: user-1 soft deletes soft-deleted-1 and then reads it by name

Then

- the whole domain seeded in advance comes back
  - name = 'soft-deleted-1'
  - description = 'a domain that already existed'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="reading-a-user-granted-nothing-may-not-read-a-domain"></a>

#### [a-user-granted-nothing-may-not-read-a-domain](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

with the same domain laid, when a user granted nothing reads it by name, the call is rejected for lack of permission

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.get: user-1 reads a domain by name host-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-reading-a-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_reading.py): pass

when the superadmin reads by a name that does not exist, the call is rejected as not found, not for a permission problem

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.get: user-1 reads a domain by name no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### global_search

<a id="searching-a-name-filter-narrows-the-answer-to-the-domain-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-domain-it-names](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

when several domains are searched with a filter on the name of one, only the domain of that name is left in the answer

Given

- 4 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Domain other-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.global_search: user-1 searches with a filter on wanted-1

Then

- only the domain that the filter named is left
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-a-project-name-filter-narrows-the-answer-to-the-domain-holding-it"></a>

#### [a-project-name-filter-narrows-the-answer-to-the-domain-holding-it](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when domains are searched with a filter on the name of a project one of them holds, only the domain holding that project is left

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches for the domain holding the project named alpha-team-1

Then

- only the first domain is left
  - items = ['first-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-a-username-filter-narrows-the-answer-to-the-domain-the-user-lives-in"></a>

#### [a-username-filter-narrows-the-answer-to-the-domain-the-user-lives-in](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when domains are searched with a filter on the username of a user living in one of them, only the domain that user lives in is left

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches for the domain where user-1 lives

Then

- only the first domain is left
  - items = ['first-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-an-email-filter-narrows-the-answer-to-the-domain-the-user-lives-in"></a>

#### [an-email-filter-narrows-the-answer-to-the-domain-the-user-lives-in](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when domains are searched with a filter on the email of a user living in one of them, only the domain that user lives in is left

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches for the domain where the user with the email user-1@scenario.local lives

Then

- only the first domain is left
  - items = ['first-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-an-inactive-user-filter-narrows-the-answer-to-the-domain-they-live-in"></a>

#### [an-inactive-user-filter-narrows-the-answer-to-the-domain-they-live-in](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when domains are searched with a filter on inactive users, only the domain such a user lives in is left

Given

- two domains, each holding one project of a different name and one user, the user of the second is inactive, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Prepare one inactive user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: status inactive, has their own keypair and personal project

When

- DomainAdapter.global_search: user-3 searches for the domain where an inactive user lives

Then

- only the second domain is left
  - items = ['second-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-ordering-by-the-email-puts-the-domains-in-that-order"></a>

#### [ordering-by-the-email-puts-the-domains-in-that-order](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when every domain is searched ordered by the email of its users, the domain whose user's email comes first comes first

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches every domain ordered by the email of its users

Then

- the domains come back in name order
  - items = ['first-1', 'second-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-ordering-by-the-project-name-puts-the-domains-in-that-order"></a>

#### [ordering-by-the-project-name-puts-the-domains-in-that-order](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when every domain is searched ordered by the name of the project it holds, the domain holding the project whose name comes first comes first

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches every domain ordered by project name

Then

- the domains come back in name order
  - items = ['first-1', 'second-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="nested_searching-ordering-by-the-username-puts-the-domains-in-that-order"></a>

#### [ordering-by-the-username-puts-the-domains-in-that-order](/tests/scenario/bai_scenario/manager/domain/test_nested_searching.py): pass

when every domain is searched ordered by the username of its users, the domain whose user's name comes first comes first

Given

- two domains, each holding one project of a different name and one user, and the first holds one more superadmin
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Domain first-1
  - Domain second-1
  - Project alpha-team-1
  - Project beta-team-1
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

When

- DomainAdapter.global_search: user-3 searches every domain ordered by the username of its users

Then

- the domains come back in name order
  - items = ['first-1', 'second-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-counts-every-domain-the-scenario-laid"></a>

#### [the-answer-counts-every-domain-the-scenario-laid](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

when this scenario seeded four domains, a search without a filter brings back all four

Given

- 4 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Domain other-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.global_search: user-1 searches every domain without a filter

Then

- every domain seeded in advance comes back
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-answer-includes-soft-deleted-domains-too"></a>

#### [the-answer-includes-soft-deleted-domains-too](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

when one of the domains seeded in advance is soft-deleted and every domain is searched without a filter, that one comes back too

Given

- 4 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Domain other-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.global_search: user-1 soft deletes wanted-1 and then searches every domain without a filter

Then

- every domain seeded in advance comes back
  - items = ['home-1', 'other-1', 'other-2', 'wanted-1']
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-domain](/tests/scenario/bai_scenario/manager/domain/test_searching.py): pass

when a user who is not the superadmin asks to search every domain, the role rejects it

Given

- 4 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Domain other-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.global_search: user-1 searches every domain without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### lookup_name

<a id="looking_up-a-user-granted-nothing-still-looks-up-a-domain-by-name"></a>

#### [a-user-granted-nothing-still-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

a user granted nothing can still look up a domain by name. This call checks authentication only, and the call receiving that id checks the permission

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.lookup_name: user-1 looks up the id of target-1

Then

- the id of that domain comes back
  - id: same as the id of the domain seeded in advance

<a id="looking_up-the-superadmin-looks-up-a-domain-by-name"></a>

#### [the-superadmin-looks-up-a-domain-by-name](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

when the superadmin looks up a domain by name, the id of that domain comes back

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.lookup_name: user-1 looks up the id of target-1

Then

- the id of that domain comes back
  - id: same as the id of the domain seeded in advance

<a id="looking_up-looking-up-a-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_looking_up.py): pass

looking up an id by a name no domain answers to is rejected as not found

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.lookup_name: user-1 looks up the id of no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-domains"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

when a user granted nothing soft-deletes several domains at once, none is soft-deleted and every one comes back in the failed list for lack of permission

Given

- 3 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_delete: user-1 soft deletes 2 domains at once

Then

- no domain is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target domain
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target domain
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

when two active domains and one missing id are soft-deleted at once, the two come back inactive and the missing id comes back in the failed list because there is no such target

Given

- 3 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_delete: user-1 soft deletes 2 domains and one missing id at once

Then

- every target domain comes back inactive and the missing id comes back in the failed list because there is no such target
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'a domain that already existed'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = False
  - successes[0].is_default = False
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the domain seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'other-1'
  - successes[1].description = 'a domain that already existed'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = False
  - successes[1].is_default = False
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the domain seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_deleting-soft-deleting-domains-without-login-is-refused"></a>

#### [soft-deleting-domains-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

soft-deleting several domains at once without a login context is rejected with the error saying no user is in the context

Given

- 3 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_delete: without a login context, soft deletes 2 domains at once

Then

- the call is rejected
  - rejected: UnreachableError

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

when several soft-deleted domains are restored at once, all of them come back active

Given

- 3 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_restore: user-1 soft deletes 2 domains at once and then restores them at once

Then

- every target domain comes back active and none failed
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'a domain that already existed'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = True
  - successes[0].is_default = False
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the domain seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'other-1'
  - successes[1].description = 'a domain that already existed'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the domain seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed = []

<a id="partial_bulk_deleting-restoring-domains-without-login-is-refused"></a>

#### [restoring-domains-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_deleting.py): pass

restoring several domains at once without a login context is rejected with the error saying no user is in the context

Given

- 3 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_restore: without a login context, restores 2 domains at once

Then

- the call is rejected
  - rejected: UnreachableError

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-domains"></a>

#### [a-user-granted-nothing-edits-none-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

when a user granted nothing edits several domains at once, none is edited and every one comes back in the failed list for lack of permission

Given

- 3 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_update: user-1 edits the description of 2 domains at once

Then

- no domain is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target domain
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target domain
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-active-flag-soft-deletes-or-restores-each-of-several-domains"></a>

#### [the-active-flag-soft-deletes-or-restores-each-of-several-domains](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

when several domains are edited at once with a mix of active flags and descriptions, the one deactivated is soft-deleted and the one activated is restored, both come back with the new description, and the missing id comes back in the failed list because there is no such target

Given

- 3 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_update: user-1 soft deletes the second domain, then deactivates the active flag of the first, activates the second, changes the description of both, and deactivates the active flag of one missing id

Then

- both come back with the new description, the first is inactive and the second is active, and the missing id comes back in the failed list because there is no such target
  - successes count = 2
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'a description edited at once'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = False
  - successes[0].is_default = False
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the domain seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'other-1'
  - successes[1].description = 'a description edited at once'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the domain seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_editing-the-superadmin-edits-several-domains-at-once"></a>

#### [the-superadmin-edits-several-domains-at-once](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several domains at once, all of them come back with the new description and none failed

Given

- 3 domains and one superadmin in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_update: user-1 edits the description of 2 domains at once

Then

- every target domain comes back with the new description and none failed
  - successes count = 2
  - failed = []
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'a description edited at once'
  - successes[0].integration_name = None
  - successes[0].allowed_docker_registries = []
  - successes[0].is_active = True
  - successes[0].is_default = False
  - successes[0].id: skipped: the database generates it
  - successes[0].entity_id: same as the id of the domain seeded in advance
  - successes[0].created_at: the time this run wrote
  - successes[0].modified_at: the time this run wrote
  - successes[1].name = 'other-1'
  - successes[1].description = 'a description edited at once'
  - successes[1].integration_name = None
  - successes[1].allowed_docker_registries = []
  - successes[1].is_active = True
  - successes[1].is_default = False
  - successes[1].id: skipped: the database generates it
  - successes[1].entity_id: same as the id of the domain seeded in advance
  - successes[1].created_at: the time this run wrote
  - successes[1].modified_at: the time this run wrote

<a id="partial_bulk_editing-editing-domains-without-login-is-refused"></a>

#### [editing-domains-without-login-is-refused](/tests/scenario/bai_scenario/manager/domain/test_partial_bulk_editing.py): pass

editing several domains at once without a login context is rejected with the error saying no user is in the context

Given

- 3 domains and one user in one of them
  - Domain home-1
  - Domain wanted-1
  - Domain other-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.partial_bulk_update: without a login context, edits the description of 2 domains at once

Then

- the call is rejected
  - rejected: UnreachableError

### restore

<a id="deleting-restoring-a-domain-that-is-not-soft-deleted"></a>

#### [restoring-a-domain-that-is-not-soft-deleted](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

when the superadmin restores a domain that is not soft-deleted, the answer says it was restored and the domain comes back active

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain active-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.restore: user-1 restores active-1

Then

- the answer says it was done and the domain comes back active
  - restored = True
  - domain.name = 'active-1'
  - domain.description = 'a domain that already existed'
  - domain.integration_name = None
  - domain.allowed_docker_registries = []
  - domain.is_active = True
  - domain.is_default = False
  - domain.id: skipped: the database generates it
  - domain.entity_id: same as the id of the domain seeded in advance
  - domain.created_at: the time this run wrote
  - domain.modified_at: the time this run wrote

<a id="deleting-restoring-answers-that-it-restored"></a>

#### [restoring-answers-that-it-restored](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

when a soft-deleted domain is restored, the answer says it was restored and the domain comes back active

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain to-restore-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.restore: user-1 soft deletes to-restore-1 and then restores it

Then

- the answer says it was done and the domain comes back active
  - restored = True
  - domain.name = 'to-restore-1'
  - domain.description = 'a domain that already existed'
  - domain.integration_name = None
  - domain.allowed_docker_registries = []
  - domain.is_active = True
  - domain.is_default = False
  - domain.id: skipped: the database generates it
  - domain.entity_id: same as the id of the domain seeded in advance
  - domain.created_at: the time this run wrote
  - domain.modified_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-restore-a-domain"></a>

#### [a-user-granted-nothing-may-not-restore-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a user granted nothing cannot restore a domain

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain untouchable-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.restore: user-1 restores untouchable-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="scoped_searching-a-user-granted-read-in-the-group-searches-its-domains"></a>

#### [a-user-granted-read-in-the-group-searches-its-domains](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

when a user granted the domain read role in a resource group scope searches in that scope, the same domains as the superadmin sees come back

Given

- one resource group, two domains that can use it and one that cannot, and the user granted the domain read role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Domain linked-1
  - Domain linked-2
  - Domain linked-1 whose sessions can use Resource group resource-group-1
  - Domain linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the domain read role in the resource group scope
    - Role domain-reader-1: applies only within the scope it is granted in
    - Role domain-reader-1: READ allowed on every domain
    - regular user user-1: holds Role domain-reader-1

When

- DomainAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- only the domains that can use the group are left
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-the-superadmin-searches-the-domains-of-a-resource-group"></a>

#### [the-superadmin-searches-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

when the superadmin searches in a resource group scope, only the domains that can use the group come back

Given

- one resource group, two domains that can use it and one that cannot, and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Domain linked-1
  - Domain linked-2
  - Domain linked-1 whose sessions can use Resource group resource-group-1
  - Domain linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- only the domains that can use the group are left
  - items = ['linked-1', 'linked-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group](/tests/scenario/bai_scenario/manager/domain/test_scoped_searching.py): pass

when a user granted nothing searches in a resource group scope, the call is rejected for lack of permission

Given

- one resource group, two domains that can use it and one that cannot, and one user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Domain linked-1
  - Domain linked-2
  - Domain linked-1 whose sessions can use Resource group resource-group-1
  - Domain linked-2 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.scoped_search: user-1 searches in the resource group resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-clearing-the-active-flag-soft-deletes-a-domain"></a>

#### [clearing-the-active-flag-soft-deletes-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

an edit that turns the active flag off soft deletes the domain, and the response carries the inactive state

Given

- one domain and one superadmin in it
  - Domain to-deactivate-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 edits the active flag of to-deactivate-1

Then

- the whole domain seeded in advance comes back
  - name = 'to-deactivate-1'
  - description = 'a domain that already existed'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-editing-a-description-leaves-the-name-alone"></a>

#### [editing-a-description-leaves-the-name-alone](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

when the superadmin changes only the description of a domain, the description becomes the new value and the name stays

Given

- one domain and one superadmin in it
  - Domain editable-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 edits the description of editable-1

Then

- the whole domain seeded in advance comes back
  - name = 'editable-1'
  - description = 'an edited description'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest"></a>

#### [lowering-the-active-flag-of-a-soft-deleted-domain-edits-only-the-rest](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

when an edit turns the active flag off of a soft-deleted domain and changes the description, the description becomes the new value and the inactive state stays

Given

- one domain and one superadmin in it
  - Domain already-deleted-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 soft deletes already-deleted-1 and then edits the active flag and the description

Then

- the whole domain seeded in advance comes back
  - name = 'already-deleted-1'
  - description = 'an edited description'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = False
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-raising-the-active-flag-restores-a-soft-deleted-domain"></a>

#### [raising-the-active-flag-restores-a-soft-deleted-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

an edit that turns the active flag on of a soft-deleted domain restores it, and the response carries the active state

Given

- one domain and one superadmin in it
  - Domain to-restore-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 soft deletes to-restore-1 and then edits the active flag

Then

- the whole domain seeded in advance comes back
  - name = 'to-restore-1'
  - description = 'a domain that already existed'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: skipped: the database generates it
  - entity_id: same as the id of the domain seeded in advance
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-a-domain"></a>

#### [a-user-granted-nothing-may-not-edit-a-domain](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

when a user granted nothing tries to edit a domain, the call is rejected for lack of permission

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 edits the description of host-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-editing-a-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_editing.py): pass

editing a name no domain answers to is rejected as not found

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.update: user-1 edits the description of no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### create

<a id="creating-creating-a-domain-also-creates-its-model-store-project"></a>

#### [creating-a-domain-also-creates-its-model-store-project](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

when the superadmin creates a domain, its model-store project is created too, and searching for the domain holding that project brings back the domain just created

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as with-model-store, then searches for the domain holding the model-store project

Then

- the whole domain just created comes back
  - name = 'with-model-store'
  - description = 'a freshly created domain'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: skipped: the database generates it
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="creating-creating-a-domain-answers-with-the-whole-node"></a>

#### [creating-a-domain-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

when the superadmin creates a domain with only a name and a description, the whole node comes back with the values the request omitted filled from defaults

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as new-domain

Then

- the whole domain just created comes back
  - name = 'new-domain'
  - description = 'a freshly created domain'
  - integration_name = None
  - allowed_docker_registries = []
  - is_active = True
  - is_default = False
  - id: skipped: the database generates it
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="creating-a-blank-name-is-refused"></a>

#### [a-blank-name-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

a domain cannot be created when the name is only whitespace

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as    

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="creating-a-name-another-domain-already-holds-is-refused"></a>

#### [a-name-another-domain-already-holds-is-refused](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

when a domain is created with a name another domain already holds, it is rejected because the name is taken even when the caller has the permission

Given

- one domain and one superadmin in it
  - Domain taken-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as taken-1

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

when a user who is not the superadmin tries to create a domain, the role rejects it regardless of how much permission the user holds

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as by-a-user

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-domain"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-domain](/tests/scenario/bai_scenario/manager/domain/test_creating.py): pass

turning entity permission enforcement off still rejects creating a domain, because a role checks this operation, not the permission graph

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.create: user-1 creates it as by-a-user-again

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### purge

<a id="deleting-purging-a-domain-nothing-else-refers-to-succeeds"></a>

#### [purging-a-domain-nothing-else-refers-to-succeeds](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a domain nothing else refers to can be purged

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain to-purge-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.purge: user-1 purges to-purge-1

Then

- the answer says it was done
  - purged = True

<a id="deleting-a-domain-holding-a-project-is-not-purged"></a>

#### [a-domain-holding-a-project-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a domain holding a project cannot be purged even by the superadmin

Given

- one target domain holding a project and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.purge: user-1 purges target-1

Then

- the call is rejected
  - rejected: DomainHasGroups

<a id="deleting-a-domain-holding-a-user-is-not-purged"></a>

#### [a-domain-holding-a-user-is-not-purged](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a domain holding a user cannot be purged even by the superadmin

Given

- one target domain holding a user and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project

When

- DomainAdapter.purge: user-2 purges target-1

Then

- the call is rejected
  - rejected: DomainHasUsers

<a id="deleting-a-user-granted-nothing-may-not-purge-a-domain"></a>

#### [a-user-granted-nothing-may-not-purge-a-domain](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

a user granted nothing cannot purge a domain even when nothing else refers to it

Given

- one target domain and one user in another domain
  - Domain home-1
  - Domain untouchable-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DomainAdapter.purge: user-1 purges untouchable-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="deleting-purging-a-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/domain/test_deleting.py): pass

purging a name no domain answers to is rejected as not found

Given

- one target domain and one superadmin in another domain
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- DomainAdapter.purge: user-1 purges no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

