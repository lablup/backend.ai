## reservoir_registry

[background](/src/ai/backend/manager/api/adapters/reservoir_registry/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/reservoir_registry/adapter.py)

Scenario: complete

- built from ops (1)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
- direct implementation (8)
  - create: success present 1 · rejection present 1 (global_scope)
  - get: success present 1 · rejection present 1 (single_entity)
  - get_many: success present 1 · rejection present 1 (global_scope)
  - partial_bulk_purge: success present 2 · rejection present 1 (partial_bulk)
  - partial_bulk_update: success present 1 · rejection present 1 (partial_bulk)
  - purge: success present 1 · rejection present 1 (single_entity)
  - search: success present 1 · rejection present 1 (global_scope)
  - update: success present 1 · rejection present 1 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted permission to read Reservoir registries loads two registries seeded in advance at once, the two come back in the requested order](#reading-a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order) | answered |
| [when a user granted nothing loads several registry ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a Reservoir registry, the whole created registry comes back. This call is gated by the global role](#creating-the-superadmin-creates-a-reservoir-registry) | answered |
| [when a user who is not the superadmin tries to create a Reservoir registry, it is rejected for lack of permission. This call is gated by the global role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted permission to read Reservoir registries reads one, the whole registry seeded in advance comes back](#reading-a-user-granted-read-gets-a-registry) | answered |
| [when a user granted nothing tries to read a registry, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-get-a-registry) | rejected |

**get_many**

| scenario | verdict |
|---|---|
| [when the superadmin reads two registries by id at once, both come back. This call is gated by the global role](#reading-the-superadmin-reads-several-reservoir-registries-by-id) | answered |
| [when a user who is not the superadmin reads registries by id at once, it is rejected for lack of permission. This call is gated by the global role](#reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted permission to purge Reservoir registries purges several at once, every id comes back in the processed list and none failed](#partial_bulk_purging-a-user-granted-purge-purges-several-registries) | answered |
| [when the superadmin purges two Reservoir registries and one id that does not exist at once, the two ids come back in the processed list and the id that does not exist comes back in the failed list because there is no such target. The superadmin passes every check, so the missing target is revealed as it is](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |
| [when a user granted nothing tries to purge several Reservoir registries at once, nothing is purged and all come back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted permission to edit Reservoir registries changes the endpoints of several at once, all come back with the new endpoint and none failed](#partial_bulk_editing-a-user-granted-update-edits-several-registries) | answered |
| [when a user granted nothing tries to edit several Reservoir registries at once, nothing is edited and all come back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted permission to purge Reservoir registries purges one, the id of the purged Reservoir registry comes back](#purging-a-user-granted-purge-purges-a-registry) | answered |
| [when a user granted nothing tries to purge, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-registry) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin searches Reservoir registries and asks for one page, one of the two registries seeded in advance comes back and the total count is two. This call is gated by the global role](#searching-the-superadmin-searching-reservoir-registries-gets-one-page) | answered |
| [when a user who is not the superadmin tries to search Reservoir registries, it is rejected for lack of permission. This call is gated by the global role](#searching-a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted permission to edit Reservoir registries changes the endpoint, the Reservoir registry comes back with the new endpoint](#editing-a-user-granted-update-edits-a-registry) | answered |
| [when a user granted nothing tries to change the endpoint, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-registry) | rejected |

### batch_load_by_ids

<a id="reading-a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order"></a>

#### [a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when a user granted permission to read Reservoir registries loads two registries seeded in advance at once, the two come back in the requested order

Given

- 2 Reservoir registries and one regular user granted READ on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: READ allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.batch_load_by_ids: user-1 loads two registries seeded in advance by id at once

Then

- the registries seeded in advance come back in the requested order
  - length = 2
  - [0].id: same as the id of the registry seeded in advance
  - [0].entity_id: same as the id of the registry seeded in advance
  - [0].name = 'registry-1'
  - [0].endpoint = 'https://reservoir.example.com'
  - [0].access_key = 'access-key'
  - [0].secret_key = 'secret-key'
  - [0].api_version = 'v1'
  - [1].id: same as the id of the registry seeded in advance
  - [1].entity_id: same as the id of the registry seeded in advance
  - [1].name = 'registry-2'
  - [1].endpoint = 'https://reservoir.example.com'
  - [1].access_key = 'access-key'
  - [1].secret_key = 'secret-key'
  - [1].api_version = 'v1'

<a id="reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when a user granted nothing loads several registry ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

Given

- 2 Reservoir registries and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.batch_load_by_ids: user-1 loads two registries seeded in advance by id at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-reservoir-registry"></a>

#### [the-superadmin-creates-a-reservoir-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_creating.py): pass

when the superadmin creates a Reservoir registry, the whole created registry comes back. This call is gated by the global role

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.create: user-1 creates a Reservoir registry

Then

- the whole created registry comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'made-reservoir'
  - endpoint = 'https://made.reservoir.example.com'
  - access_key = 'made-access-key'
  - secret_key = 'made-secret-key'
  - api_version = 'v1'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-reservoir-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_creating.py): pass

when a user who is not the superadmin tries to create a Reservoir registry, it is rejected for lack of permission. This call is gated by the global role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.create: user-1 creates a Reservoir registry

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-read-gets-a-registry"></a>

#### [a-user-granted-read-gets-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when a user granted permission to read Reservoir registries reads one, the whole registry seeded in advance comes back

Given

- one Reservoir registry and one regular user granted READ on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: READ allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.get: user-1 reads registry-1

Then

- the whole registry seeded in advance comes back
  - id: same as the id of the registry seeded in advance
  - entity_id: same as the id of the registry seeded in advance
  - name = 'registry-1'
  - endpoint = 'https://reservoir.example.com'
  - access_key = 'access-key'
  - secret_key = 'secret-key'
  - api_version = 'v1'

<a id="reading-a-user-granted-nothing-may-not-get-a-registry"></a>

#### [a-user-granted-nothing-may-not-get-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when a user granted nothing tries to read a registry, it is rejected for lack of permission

Given

- one Reservoir registry and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.get: user-1 reads registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_many

<a id="reading-the-superadmin-reads-several-reservoir-registries-by-id"></a>

#### [the-superadmin-reads-several-reservoir-registries-by-id](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when the superadmin reads two registries by id at once, both come back. This call is gated by the global role

Given

- 2 Reservoir registries and one superadmin
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.get_many: user-1 reads two registries seeded in advance by id at once

Then

- every registry seeded in advance comes back
  - items: same as the registries seeded in advance

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_reading.py): pass

when a user who is not the superadmin reads registries by id at once, it is rejected for lack of permission. This call is gated by the global role

Given

- 2 Reservoir registries and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.get_many: user-1 reads two registries seeded in advance by id at once

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-registries"></a>

#### [a-user-granted-purge-purges-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

when a user granted permission to purge Reservoir registries purges several at once, every id comes back in the processed list and none failed

Given

- 2 Reservoir registries and one regular user granted HARD_DELETE on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: HARD_DELETE allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1 purges 2 Reservoir registries at once

Then

- every target registry id comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the registry seeded in advance
  - successes[1].id: same as the id of the registry seeded in advance
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

when the superadmin purges two Reservoir registries and one id that does not exist at once, the two ids come back in the processed list and the id that does not exist comes back in the failed list because there is no such target. The superadmin passes every check, so the missing target is revealed as it is

Given

- 2 Reservoir registries and one superadmin
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1 purges 2 Reservoir registries and one id that does not exist at once

Then

- every target registry id comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the registry seeded in advance
  - successes[1].id: same as the id of the registry seeded in advance
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries"></a>

#### [a-user-granted-nothing-purges-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several Reservoir registries at once, nothing is purged and all come back in the failed list because there is no permission

Given

- 2 Reservoir registries and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.partial_bulk_purge: user-1 purges 2 Reservoir registries at once

Then

- no registry is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target registry
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target registry
  - rejected: failed[1]: Insufficient permission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-update-edits-several-registries"></a>

#### [a-user-granted-update-edits-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py): pass

when a user granted permission to edit Reservoir registries changes the endpoints of several at once, all come back with the new endpoint and none failed

Given

- 2 Reservoir registries and one regular user granted UPDATE on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: UPDATE allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.partial_bulk_update: user-1 changes the endpoints of 2 Reservoir registries at once

Then

- every target registry comes back with the new endpoint and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].id: same as the id of the registry seeded in advance
  - successes[0].entity_id: same as the id of the registry seeded in advance
  - successes[0].name = 'registry-1'
  - successes[0].endpoint = 'https://storage.example.com'
  - successes[0].access_key = 'access-key'
  - successes[0].secret_key = 'secret-key'
  - successes[0].api_version = 'v1'
  - successes[1].id: same as the id of the registry seeded in advance
  - successes[1].entity_id: same as the id of the registry seeded in advance
  - successes[1].name = 'registry-2'
  - successes[1].endpoint = 'https://storage.example.com'
  - successes[1].access_key = 'access-key'
  - successes[1].secret_key = 'secret-key'
  - successes[1].api_version = 'v1'

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries"></a>

#### [a-user-granted-nothing-edits-none-of-several-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several Reservoir registries at once, nothing is edited and all come back in the failed list because there is no permission

Given

- 2 Reservoir registries and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.partial_bulk_update: user-1 changes the endpoints of 2 Reservoir registries at once

Then

- no registry is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target registry
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target registry
  - rejected: failed[1]: Insufficient permission

### purge

<a id="purging-a-user-granted-purge-purges-a-registry"></a>

#### [a-user-granted-purge-purges-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py): pass

when a user granted permission to purge Reservoir registries purges one, the id of the purged Reservoir registry comes back

Given

- one Reservoir registry and one regular user granted HARD_DELETE on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: HARD_DELETE allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.purge: user-1 purges registry-1

Then

- the id of the purged registry comes back
  - id: same as the id of the registry seeded in advance

<a id="purging-a-user-granted-nothing-may-not-purge-a-registry"></a>

#### [a-user-granted-nothing-may-not-purge-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_purging.py): pass

when a user granted nothing tries to purge, it is rejected for lack of permission

Given

- one Reservoir registry and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.purge: user-1 purges registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search

<a id="searching-the-superadmin-searching-reservoir-registries-gets-one-page"></a>

#### [the-superadmin-searching-reservoir-registries-gets-one-page](/tests/scenario/bai_scenario/manager/reservoir_registry/test_searching.py): pass

when the superadmin searches Reservoir registries and asks for one page, one of the two registries seeded in advance comes back and the total count is two. This call is gated by the global role

Given

- 2 Reservoir registries and one superadmin
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.search: user-1 searches Reservoir registries and asks for one page

Then

- only one of the two registries seeded in advance comes on the page and the other is on the next page
  - length = 1
  - items: one of the registries seeded in advance
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-reservoir-registries](/tests/scenario/bai_scenario/manager/reservoir_registry/test_searching.py): pass

when a user who is not the superadmin tries to search Reservoir registries, it is rejected for lack of permission. This call is gated by the global role

Given

- 2 Reservoir registries and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Reservoir registry registry-2: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.search: user-1 searches Reservoir registries and asks for one page

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update

<a id="editing-a-user-granted-update-edits-a-registry"></a>

#### [a-user-granted-update-edits-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py): pass

when a user granted permission to edit Reservoir registries changes the endpoint, the Reservoir registry comes back with the new endpoint

Given

- one Reservoir registry and one regular user granted UPDATE on registries
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare a user granted permission on artifact registries in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: UPDATE allowed on every artifact_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ReservoirRegistryAdapter.update: user-1 changes the endpoint of registry-1

Then

- the registry seeded in advance comes back with the new endpoint
  - id: same as the id of the registry seeded in advance
  - entity_id: same as the id of the registry seeded in advance
  - name = 'registry-1'
  - endpoint = 'https://storage.example.com'
  - access_key = 'access-key'
  - secret_key = 'secret-key'
  - api_version = 'v1'

<a id="editing-a-user-granted-nothing-may-not-edit-a-registry"></a>

#### [a-user-granted-nothing-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/reservoir_registry/test_editing.py): pass

when a user granted nothing tries to change the endpoint, it is rejected for lack of permission

Given

- one Reservoir registry and one regular user with no permission
  - Reservoir registry registry-1: refers to https://reservoir.example.com
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ReservoirRegistryAdapter.update: user-1 changes the endpoint of registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

