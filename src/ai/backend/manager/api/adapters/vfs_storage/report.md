## vfs_storage

[background](/src/ai/backend/manager/api/adapters/vfs_storage/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/vfs_storage/adapter.py)

Scenario: incomplete 7 / 9

- built from ops (9)
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - list_all: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - update: representative success ✓ · representative rejection ✓

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several VFS storages in one call, none is purged and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages) | answered |
| [when the superadmin purges two VFS storages and a missing id in one call, the two come back in the purged list and the missing id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several VFS storages in one call, none is edited and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages) | answered |
| [when the superadmin changes the base path of several VFS storages in one call, all come back with the new base path and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a VFS storage, the id of the purged one is returned](#purging-the-superadmin-purges-a-vfs-storage) | answered |
| [when a user granted nothing purges a VFS storage, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-vfs-storage) | rejected |
| [when the superadmin purges an id that does not exist, it is rejected because the target is not found](#purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes only the base path, the base path takes the new value and the rest stays as it is](#editing-the-superadmin-changes-the-base-path-of-a-vfs-storage) | answered |
| [when a user granted nothing edits a VFS storage, it is rejected for lack of permission. A VFS storage belongs only to global, so there is no way to grant that permission](#editing-a-user-granted-nothing-may-not-edit-a-vfs-storage) | rejected |
| [when the superadmin edits an id that does not exist, it is rejected because the target is not found](#editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found) | rejected |

### partial_bulk_purge

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
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target VFS storage
  - failed[1].message: a reason containing 'Insufficient permission'

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

### partial_bulk_update

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
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target VFS storage
  - failed[1].message: a reason containing 'Insufficient permission'

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

