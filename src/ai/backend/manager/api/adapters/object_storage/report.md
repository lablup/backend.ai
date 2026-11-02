## object_storage

[background](/src/ai/backend/manager/api/adapters/object_storage/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/object_storage/adapter.py)

Scenario: incomplete 8 / 10

- built from ops (8)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - get_presigned_download_url: success absent · rejection absent (single_field): SCENARIO-GAP
  - get_presigned_upload_url: success absent · rejection absent (single_field): SCENARIO-GAP

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several object storages at once, nothing is purged and every one comes back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages) | answered |
| [when the superadmin purges two object storages and an unknown id at once, the two come back in the purged list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several object storages at once, nothing is updated and every one comes back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages) | answered |
| [when the superadmin changes the hosts of several object storages at once, they all come back with the new host and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges an object storage, the id of the purged one comes back](#purging-the-superadmin-purges-an-object-storage) | answered |
| [when a user granted nothing purges an object storage, it is rejected for a lack of permission](#purging-a-user-granted-nothing-may-not-purge-an-object-storage) | rejected |
| [when the superadmin purges an id nothing answers to, it is rejected because the target cannot be found](#purging-purging-an-object-storage-id-nothing-answers-to-is-not-found) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes only the host, the host becomes the new value and the rest stays as it was](#editing-the-superadmin-changes-the-host-of-an-object-storage) | answered |
| [when a user granted nothing updates an object storage, it is rejected for a lack of permission. An object storage belongs to global alone, so there is no way to receive that permission](#editing-a-user-granted-nothing-may-not-edit-an-object-storage) | rejected |
| [when the superadmin updates an id nothing answers to, it is rejected because the target cannot be found](#editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found) | rejected |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several object storages at once, nothing is purged and every one comes back in the failed list because there is no permission

Given

- 2 object storages and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Object storage object-storage-2: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.partial_bulk_purge: user-1 purges 2 object storages at once

Then

- no object storage is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target object storage
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target object storage
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-object-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py): pass

when the superadmin purges two object storages and an unknown id at once, the two come back in the purged list and the unknown id comes back in the failed list because no target answers to it

Given

- 2 object storages and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Object storage object-storage-2: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.partial_bulk_purge: user-1 purges 2 object storages and one unknown id at once

Then

- every target object storage comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the object storage created in advance
  - successes[0].entity_id: same as the object storage created in advance
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'seeded.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: same as the object storage created in advance
  - successes[1].entity_id: same as the object storage created in advance
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'seeded.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several object storages at once, nothing is updated and every one comes back in the failed list because there is no permission

Given

- 2 object storages and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Object storage object-storage-2: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.partial_bulk_update: user-1 updates the host of 2 object storages at once

Then

- no object storage is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target object storage
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target object storage
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once"></a>

#### [the-superadmin-edits-several-object-storages-at-once](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py): pass

when the superadmin changes the hosts of several object storages at once, they all come back with the new host and nothing failed

Given

- 2 object storages and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Object storage object-storage-2: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.partial_bulk_update: user-1 updates the host of 2 object storages at once

Then

- every target object storage comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: same as the object storage created in advance
  - successes[0].entity_id: same as the object storage created in advance
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'moved.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: same as the object storage created in advance
  - successes[1].entity_id: same as the object storage created in advance
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'moved.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed = []

### purge

<a id="purging-the-superadmin-purges-an-object-storage"></a>

#### [the-superadmin-purges-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

when the superadmin purges an object storage, the id of the purged one comes back

Given

- one object storage and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.purge: user-1 purges object-storage-1

Then

- the id of the purged object storage comes back
  - id: same as the object storage created in advance

<a id="purging-a-user-granted-nothing-may-not-purge-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-purge-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

when a user granted nothing purges an object storage, it is rejected for a lack of permission

Given

- one object storage and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.purge: user-1 purges object-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-purging-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

when the superadmin purges an id nothing answers to, it is rejected because the target cannot be found

Given

- one object storage and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.purge: user-1 purges an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update

<a id="editing-the-superadmin-changes-the-host-of-an-object-storage"></a>

#### [the-superadmin-changes-the-host-of-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

when the superadmin changes only the host, the host becomes the new value and the rest stays as it was

Given

- one object storage and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.update: user-1 updates the host of object-storage-1

Then

- the whole object storage created in advance comes back
  - id: same as the object storage created in advance
  - entity_id: same as the object storage created in advance
  - name = 'object-storage-1'
  - host = 'moved.object-storage.test'
  - access_key = 'seeded-access-key'
  - secret_key = 'seeded-secret-key'
  - endpoint = 'http://seeded.object-storage.test'
  - region = 'seeded-region'

<a id="editing-a-user-granted-nothing-may-not-edit-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-edit-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

when a user granted nothing updates an object storage, it is rejected for a lack of permission. An object storage belongs to global alone, so there is no way to receive that permission

Given

- one object storage and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.update: user-1 updates the host of object-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

when the superadmin updates an id nothing answers to, it is rejected because the target cannot be found

Given

- one object storage and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.update: user-1 updates the host of an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

