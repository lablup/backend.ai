## huggingface_registry

[background](/src/ai/backend/manager/api/adapters/huggingface_registry/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/huggingface_registry/adapter.py)

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
| [when the superadmin loads two registries seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty](#reading-the-superadmin-loads-several-registries-in-the-requested-order) | answered |
| [when a user granted nothing loads several registry ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a HuggingFace registry, the whole created registry comes back. This call is gated by the global role](#creating-the-superadmin-creates-a-huggingface-registry) | answered |
| [when a user who is not the superadmin tries to create a HuggingFace registry, it is rejected for lack of permission. This call is gated by the global role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-huggingface-registry) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted permission to read HuggingFace registries reads one, the whole registry seeded in advance comes back](#reading-a-user-granted-read-gets-a-registry) | answered |
| [when a user granted nothing tries to read a registry, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-get-a-registry) | rejected |

**get_many**

| scenario | verdict |
|---|---|
| [when the superadmin reads two registries by id at once, both come back. This call is gated by the global role](#reading-the-superadmin-reads-several-huggingface-registries-by-id) | answered |
| [when a user who is not the superadmin reads registries by id at once, it is rejected for lack of permission. This call is gated by the global role](#reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted permission to purge HuggingFace registries purges several at once, every id comes back in the processed list and none failed](#partial_bulk_purging-a-user-granted-purge-purges-several-registries) | answered |
| [when the superadmin purges two HuggingFace registries and one id that does not exist at once, the two ids come back in the processed list and the id that does not exist comes back in the failed list because there is no such target. The superadmin passes every check, so the missing target is revealed as it is](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |
| [when a user granted nothing tries to purge several HuggingFace registries at once, nothing is purged and all come back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted permission to edit HuggingFace registries changes the addresses of several at once, all come back with the new address and none failed](#partial_bulk_editing-a-user-granted-update-edits-several-registries) | answered |
| [when a user granted nothing tries to edit several HuggingFace registries at once, nothing is edited and all come back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted permission to purge HuggingFace registries purges one, the id of the purged HuggingFace registry comes back](#purging-a-user-granted-purge-purges-a-registry) | answered |
| [when a user granted nothing tries to purge, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-registry) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin searches HuggingFace registries, every registry seeded in advance comes back. This call is gated by the global role](#searching-the-superadmin-searching-huggingface-registries-counts-every-one) | answered |
| [when a user who is not the superadmin tries to search HuggingFace registries, it is rejected for lack of permission. This call is gated by the global role](#searching-a-user-who-is-not-the-superadmin-may-not-search-huggingface-registries) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted permission to edit a HuggingFace registry changes the address, the HuggingFace registry comes back with the new address](#editing-a-user-granted-update-edits-a-registry) | answered |
| [when a user granted nothing tries to change the address, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-registry) | rejected |

### batch_load_by_ids

<a id="reading-the-superadmin-loads-several-registries-in-the-requested-order"></a>

#### [the-superadmin-loads-several-registries-in-the-requested-order](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when the superadmin loads two registries seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty

Given

- 2 HuggingFace registries and one superadmin
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.batch_load_by_ids: user-1 loads two registries seeded in advance and one id that does not exist at once

Then

- the registries seeded in advance come back in the requested order, and the entry for the id that does not exist is empty
  - length = 3
  - [0].name = 'registry-1'
  - [1] = None
  - [2].name = 'registry-2'

<a id="reading-a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when a user granted nothing loads several registry ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

Given

- 2 HuggingFace registries and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.batch_load_by_ids: user-1 loads two registries seeded in advance and one id that does not exist at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-huggingface-registry"></a>

#### [the-superadmin-creates-a-huggingface-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_creating.py): pass

when the superadmin creates a HuggingFace registry, the whole created registry comes back. This call is gated by the global role

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.create: user-1 creates a HuggingFace registry

Then

- the whole created registry comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'made-huggingface'
  - url = 'https://made.huggingface.example.com'
  - token = None

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-huggingface-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-huggingface-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_creating.py): pass

when a user who is not the superadmin tries to create a HuggingFace registry, it is rejected for lack of permission. This call is gated by the global role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.create: user-1 creates a HuggingFace registry

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-read-gets-a-registry"></a>

#### [a-user-granted-read-gets-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when a user granted permission to read HuggingFace registries reads one, the whole registry seeded in advance comes back

Given

- one HuggingFace registry and one regular user granted READ on registries
  - HuggingFace registry registry-1: refers to https://huggingface.co
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

- HuggingFaceRegistryAdapter.get: user-1 reads registry-1

Then

- the whole registry seeded in advance comes back
  - id: same as the id of the registry created in advance
  - entity_id: same as the id of the registry created in advance
  - name = 'registry-1'
  - url = 'https://huggingface.co'
  - token = None

<a id="reading-a-user-granted-nothing-may-not-get-a-registry"></a>

#### [a-user-granted-nothing-may-not-get-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when a user granted nothing tries to read a registry, it is rejected for lack of permission

Given

- one HuggingFace registry and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.get: user-1 reads registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_many

<a id="reading-the-superadmin-reads-several-huggingface-registries-by-id"></a>

#### [the-superadmin-reads-several-huggingface-registries-by-id](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when the superadmin reads two registries by id at once, both come back. This call is gated by the global role

Given

- 2 HuggingFace registries and one superadmin
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.get_many: user-1 reads two registries seeded in advance by id at once

Then

- every registry seeded in advance comes back
  - items: same as the registries seeded in advance

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-several-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-several-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_reading.py): pass

when a user who is not the superadmin reads registries by id at once, it is rejected for lack of permission. This call is gated by the global role

Given

- 2 HuggingFace registries and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.get_many: user-1 reads two registries seeded in advance by id at once

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-registries"></a>

#### [a-user-granted-purge-purges-several-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_partial_bulk_purging.py): pass

when a user granted permission to purge HuggingFace registries purges several at once, every id comes back in the processed list and none failed

Given

- 2 HuggingFace registries and one regular user granted HARD_DELETE on registries
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
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

- HuggingFaceRegistryAdapter.partial_bulk_purge: user-1 purges 2 HuggingFace registries at once

Then

- every target registry id comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the registry created in advance
  - successes[1].id: same as the id of the registry created in advance
  - failed = []

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/huggingface_registry/test_partial_bulk_purging.py): pass

when the superadmin purges two HuggingFace registries and one id that does not exist at once, the two ids come back in the processed list and the id that does not exist comes back in the failed list because there is no such target. The superadmin passes every check, so the missing target is revealed as it is

Given

- 2 HuggingFace registries and one superadmin
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.partial_bulk_purge: user-1 purges 2 HuggingFace registries and one id that does not exist at once

Then

- every target registry id comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the registry created in advance
  - successes[1].id: same as the id of the registry created in advance
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries"></a>

#### [a-user-granted-nothing-purges-none-of-several-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several HuggingFace registries at once, nothing is purged and all come back in the failed list because there is no permission

Given

- 2 HuggingFace registries and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.partial_bulk_purge: user-1 purges 2 HuggingFace registries at once

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

#### [a-user-granted-update-edits-several-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_partial_bulk_editing.py): pass

when a user granted permission to edit HuggingFace registries changes the addresses of several at once, all come back with the new address and none failed

Given

- 2 HuggingFace registries and one regular user granted UPDATE on registries
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
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

- HuggingFaceRegistryAdapter.partial_bulk_update: user-1 changes the addresses of 2 HuggingFace registries at once

Then

- every target registry comes back with the new URL and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].id: same as the id of the registry created in advance
  - successes[0].entity_id: same as the id of the registry created in advance
  - successes[0].name = 'registry-1'
  - successes[0].url = 'https://hub.example.com'
  - successes[0].token = None
  - successes[1].id: same as the id of the registry created in advance
  - successes[1].entity_id: same as the id of the registry created in advance
  - successes[1].name = 'registry-2'
  - successes[1].url = 'https://hub.example.com'
  - successes[1].token = None

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries"></a>

#### [a-user-granted-nothing-edits-none-of-several-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several HuggingFace registries at once, nothing is edited and all come back in the failed list because there is no permission

Given

- 2 HuggingFace registries and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.partial_bulk_update: user-1 changes the addresses of 2 HuggingFace registries at once

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

#### [a-user-granted-purge-purges-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_purging.py): pass

when a user granted permission to purge HuggingFace registries purges one, the id of the purged HuggingFace registry comes back

Given

- one HuggingFace registry and one regular user granted HARD_DELETE on registries
  - HuggingFace registry registry-1: refers to https://huggingface.co
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

- HuggingFaceRegistryAdapter.purge: user-1 purges registry-1

Then

- the id of the purged registry comes back
  - id: same as the id of the registry created in advance

<a id="purging-a-user-granted-nothing-may-not-purge-a-registry"></a>

#### [a-user-granted-nothing-may-not-purge-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_purging.py): pass

when a user granted nothing tries to purge, it is rejected for lack of permission

Given

- one HuggingFace registry and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.purge: user-1 purges registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search

<a id="searching-the-superadmin-searching-huggingface-registries-counts-every-one"></a>

#### [the-superadmin-searching-huggingface-registries-counts-every-one](/tests/scenario/bai_scenario/manager/huggingface_registry/test_searching.py): pass

when the superadmin searches HuggingFace registries, every registry seeded in advance comes back. This call is gated by the global role

Given

- 2 HuggingFace registries and one superadmin
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.search: user-1 searches HuggingFace registries

Then

- every registry seeded in advance comes back
  - items: same as the registries seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-huggingface-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-huggingface-registries](/tests/scenario/bai_scenario/manager/huggingface_registry/test_searching.py): pass

when a user who is not the superadmin tries to search HuggingFace registries, it is rejected for lack of permission. This call is gated by the global role

Given

- 2 HuggingFace registries and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.search: user-1 searches HuggingFace registries

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update

<a id="editing-a-user-granted-update-edits-a-registry"></a>

#### [a-user-granted-update-edits-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_editing.py): pass

when a user granted permission to edit a HuggingFace registry changes the address, the HuggingFace registry comes back with the new address

Given

- one HuggingFace registry and one regular user granted UPDATE on registries
  - HuggingFace registry registry-1: refers to https://huggingface.co
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

- HuggingFaceRegistryAdapter.update: user-1 changes the address of registry-1

Then

- the registry created in advance comes back with the new URL
  - id: same as the id of the registry created in advance
  - entity_id: same as the id of the registry created in advance
  - name = 'registry-1'
  - url = 'https://hub.example.com'
  - token = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-registry"></a>

#### [a-user-granted-nothing-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/huggingface_registry/test_editing.py): pass

when a user granted nothing tries to change the address, it is rejected for lack of permission

Given

- one HuggingFace registry and one regular user with no permission
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- HuggingFaceRegistryAdapter.update: user-1 changes the address of registry-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

