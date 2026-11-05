## vfs_storage

[background](/src/ai/backend/manager/api/adapters/vfs_storage/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/vfs_storage/adapter.py)

Scenario: complete

- built from ops (9)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - list_all: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin loads two VFS storages seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty](#reading-the-superadmin-reads-several-vfs-storages-in-the-requested-order) | answered |
| [when a user granted nothing loads several VFS storage ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a VFS storage, the whole created one comes back](#creating-the-superadmin-creates-a-vfs-storage) | answered |
| [when a user who is not the superadmin tries to create a VFS storage, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when the superadmin reads one VFS storage, the whole seeded VFS storage comes back](#reading-the-superadmin-gets-a-vfs-storage) | answered |
| [when a user granted nothing reads one VFS storage, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-get-a-vfs-storage) | rejected |

**list_all**

| scenario | verdict |
|---|---|
| [when the superadmin lists VFS storages, every VFS storage seeded in advance comes back](#searching-the-superadmin-listing-vfs-storages-gets-every-one) | answered |
| [when a user who is not the superadmin tries to list VFS storages, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#searching-a-user-who-is-not-the-superadmin-may-not-list-vfs-storages) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges two VFS storages and a missing id in one call, the two come back in the purged list and the missing id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id) | answered |
| [when a user granted nothing tries to purge several VFS storages in one call, none is purged and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the base path of several VFS storages in one call, all come back with the new base path and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once) | answered |
| [when a user granted nothing tries to edit several VFS storages in one call, none is edited and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a VFS storage, the id of the purged one is returned](#purging-the-superadmin-purges-a-vfs-storage) | answered |
| [when a user granted nothing purges a VFS storage, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-vfs-storage) | rejected |
| [when the superadmin purges an id that does not exist, it is rejected because the target is not found](#purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin searches VFS storages, every VFS storage seeded in advance comes back](#searching-the-superadmin-searching-vfs-storages-counts-every-one) | answered |
| [when a user who is not the superadmin tries to search VFS storages, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#searching-a-user-who-is-not-the-superadmin-may-not-search-vfs-storages) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes only the base path, the base path takes the new value and the rest stays as it is](#editing-the-superadmin-changes-the-base-path-of-a-vfs-storage) | answered |
| [when a user granted nothing edits a VFS storage, it is rejected for lack of permission. A VFS storage belongs only to global, so there is no way to grant that permission](#editing-a-user-granted-nothing-may-not-edit-a-vfs-storage) | rejected |
| [when the superadmin edits an id that does not exist, it is rejected because the target is not found](#editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-the-superadmin-reads-several-vfs-storages-in-the-requested-order"></a>

#### [the-superadmin-reads-several-vfs-storages-in-the-requested-order](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

when the superadmin loads two VFS storages seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty

Given

- 2 VFS storages and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.batch_load_by_ids: user-1 loads two VFS storages seeded in advance and one id that does not exist at once

Then

- the VFS storages seeded in advance come back in the requested order, and the entry for the id that does not exist is empty
  - length = 3
  - [0].name = 'vfs-storage-1'
  - [1] = None
  - [2].name = 'vfs-storage-2'

<a id="reading-a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

when a user granted nothing loads several VFS storage ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

Given

- 2 VFS storages and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.batch_load_by_ids: user-1 loads two VFS storages seeded in advance and one id that does not exist at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-vfs-storage"></a>

#### [the-superadmin-creates-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_creating.py): pass

when the superadmin creates a VFS storage, the whole created one comes back

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.create: user-1 creates a VFS storage

Then

- the whole created VFS storage comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'made-vfs-storage'
  - host = 'made-host'
  - base_path = '/made/vfs-storage'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_creating.py): pass

when a user who is not the superadmin tries to create a VFS storage, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.create: user-1 creates a VFS storage

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-the-superadmin-gets-a-vfs-storage"></a>

#### [the-superadmin-gets-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

when the superadmin reads one VFS storage, the whole seeded VFS storage comes back

Given

- one VFS storage and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.get: user-1 reads vfs-storage-1

Then

- the whole VFS storage seeded in advance comes back
  - id: same as the VFS storage seeded in advance
  - entity_id: same as the VFS storage seeded in advance
  - name = 'vfs-storage-1'
  - host = 'seeded-host'
  - base_path = '/seeded/vfs-storage'

<a id="reading-a-user-granted-nothing-may-not-get-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-get-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

when a user granted nothing reads one VFS storage, it is rejected for lack of permission

Given

- one VFS storage and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.get: user-1 reads vfs-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### list_all

<a id="searching-the-superadmin-listing-vfs-storages-gets-every-one"></a>

#### [the-superadmin-listing-vfs-storages-gets-every-one](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

when the superadmin lists VFS storages, every VFS storage seeded in advance comes back

Given

- 2 VFS storages and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.list_all: user-1 lists every VFS storage

Then

- every VFS storage seeded in advance comes back
  - items: same as the VFS storages seeded in advance

<a id="searching-a-user-who-is-not-the-superadmin-may-not-list-vfs-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-list-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

when a user who is not the superadmin tries to list VFS storages, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- 2 VFS storages and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.list_all: user-1 lists every VFS storage

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-vfs-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py): pass

when the superadmin purges two VFS storages and a missing id in one call, the two come back in the purged list and the missing id comes back in the failed list because no target answers to it

Given

- 2 VFS storages and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.partial_bulk_purge: user-1 purges 2 VFS storages and a missing id in one call

Then

- every target VFS storage comes back in the processed list, and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the VFS storage seeded in advance
  - successes[0].entity_id: same as the VFS storage seeded in advance
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/seeded/vfs-storage'
  - successes[1].id: same as the VFS storage seeded in advance
  - successes[1].entity_id: same as the VFS storage seeded in advance
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/seeded/vfs-storage'
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several VFS storages in one call, none is purged and all come back in the failed list for lack of permission

Given

- 2 VFS storages and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.partial_bulk_purge: user-1 purges 2 VFS storages in one call

Then

- no VFS storage is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target VFS storage
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target VFS storage
  - rejected: failed[1]: Insufficient permission

### partial_bulk_update

<a id="partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once"></a>

#### [the-superadmin-edits-several-vfs-storages-at-once](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py): pass

when the superadmin changes the base path of several VFS storages in one call, all come back with the new base path and nothing failed

Given

- 2 VFS storages and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.partial_bulk_update: user-1 changes the base path of 2 VFS storages in one call

Then

- every target VFS storage comes back in the processed list, and nothing failed
  - successes count = 2
  - successes[0].id: same as the VFS storage seeded in advance
  - successes[0].entity_id: same as the VFS storage seeded in advance
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/moved/vfs-storage'
  - successes[1].id: same as the VFS storage seeded in advance
  - successes[1].entity_id: same as the VFS storage seeded in advance
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/moved/vfs-storage'
  - failed = []

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several VFS storages in one call, none is edited and all come back in the failed list for lack of permission

Given

- 2 VFS storages and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.partial_bulk_update: user-1 changes the base path of 2 VFS storages in one call

Then

- no VFS storage is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target VFS storage
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target VFS storage
  - rejected: failed[1]: Insufficient permission

### purge

<a id="purging-the-superadmin-purges-a-vfs-storage"></a>

#### [the-superadmin-purges-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

when the superadmin purges a VFS storage, the id of the purged one is returned

Given

- one VFS storage and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.purge: user-1 purges vfs-storage-1

Then

- the id of the purged VFS storage comes back
  - id: same as the VFS storage seeded in advance

<a id="purging-a-user-granted-nothing-may-not-purge-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-purge-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

when a user granted nothing purges a VFS storage, it is rejected for lack of permission

Given

- one VFS storage and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.purge: user-1 purges vfs-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

when the superadmin purges an id that does not exist, it is rejected because the target is not found

Given

- one VFS storage and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.purge: user-1 purges a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-the-superadmin-searching-vfs-storages-counts-every-one"></a>

#### [the-superadmin-searching-vfs-storages-counts-every-one](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

when the superadmin searches VFS storages, every VFS storage seeded in advance comes back

Given

- 2 VFS storages and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.search: user-1 searches VFS storages

Then

- every VFS storage seeded in advance comes back
  - items: same as the VFS storages seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-vfs-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

when a user who is not the superadmin tries to search VFS storages, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- 2 VFS storages and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - VFS storage vfs-storage-2: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.search: user-1 searches VFS storages

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update

<a id="editing-the-superadmin-changes-the-base-path-of-a-vfs-storage"></a>

#### [the-superadmin-changes-the-base-path-of-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

when the superadmin changes only the base path, the base path takes the new value and the rest stays as it is

Given

- one VFS storage and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.update: user-1 changes the base path of vfs-storage-1

Then

- the whole VFS storage seeded in advance comes back
  - id: same as the VFS storage seeded in advance
  - entity_id: same as the VFS storage seeded in advance
  - name = 'vfs-storage-1'
  - host = 'seeded-host'
  - base_path = '/moved/vfs-storage'

<a id="editing-a-user-granted-nothing-may-not-edit-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-edit-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

when a user granted nothing edits a VFS storage, it is rejected for lack of permission. A VFS storage belongs only to global, so there is no way to grant that permission

Given

- one VFS storage and one regular user
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- VFSStorageAdapter.update: user-1 changes the base path of vfs-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

when the superadmin edits an id that does not exist, it is rejected because the target is not found

Given

- one VFS storage and one superadmin
  - VFS storage vfs-storage-1: its base path is /seeded/vfs-storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- VFSStorageAdapter.update: user-1 changes the base path of a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

