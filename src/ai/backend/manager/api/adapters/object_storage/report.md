## object_storage

[background](/src/ai/backend/manager/api/adapters/object_storage/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/object_storage/adapter.py)

Scenario: complete

- built from ops (8)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - get_presigned_download_url: success present 1 · rejection present 3 (single_field)
  - get_presigned_upload_url: success present 1 · rejection present 1 (single_field)

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin filters by name, only the object storage with that name comes back](#searching-filtering-by-name-leaves-only-the-matching-object-storage) | answered |
| [when the superadmin searches object storages with no condition, every object storage seeded in advance comes back. This call is gated by the global role](#searching-searching-without-a-condition-counts-every-object-storage) | answered |
| [when a user who is not the superadmin tries to search object storages, it is rejected for lack of permission. This call is gated by the global role](#searching-a-user-who-is-not-the-superadmin-may-not-search-object-storages) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin loads two object storages seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty](#reading-the-superadmin-reads-several-object-storages-in-the-requested-order) | answered |
| [when a user granted nothing loads several object storage ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates an object storage, the whole created one comes back. This call is gated by the global role](#creating-the-superadmin-creates-an-object-storage) | answered |
| [when a user who is not the superadmin tries to create an object storage, it is rejected for lack of permission. This call is gated by the global role](#creating-a-user-who-is-not-the-superadmin-may-not-create-an-object-storage) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when the superadmin reads one object storage, the whole seeded object storage comes back](#reading-the-superadmin-gets-an-object-storage) | answered |
| [when a user granted nothing reads one object storage, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-get-an-object-storage) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges two object storages and an unknown id at once, the two come back in the purged list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id) | answered |
| [when a user granted nothing tries to purge several object storages at once, nothing is purged and every one comes back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the hosts of several object storages at once, they all come back with the new host and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once) | answered |
| [when a user granted nothing tries to update several object storages at once, nothing is updated and every one comes back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages) | rejected |

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

**get_presigned_download_url**

| scenario | verdict |
|---|---|
| [when the superadmin asks for a URL to download an object of an available revision, a URL made from the object's stored path comes back](#presigned_urls-the-superadmin-gets-a-download-url-for-an-available-revision) | answered |
| [when a download URL is asked for a revision that is not available, it is rejected because the revision is not approved](#presigned_urls-downloading-an-unavailable-revision-is-refused) | rejected |
| [when the reservoir in the global config is not an object storage, a download URL request is rejected because the storage is not supported](#presigned_urls-downloading-from-a-vfs-reservoir-is-refused) | rejected |
| [when the global config has no reservoir, a download URL request is rejected because the server is misconfigured](#presigned_urls-downloading-with-no-reservoir-config-is-refused) | rejected |

**get_presigned_upload_url**

| scenario | verdict |
|---|---|
| [when the superadmin asks for a URL to upload an object to a writable artifact's revision, a URL made from the object's stored path comes back with the fields to send along](#presigned_urls-the-superadmin-gets-an-upload-url-for-a-writable-artifact) | answered |
| [when an upload URL is asked for a readonly artifact's revision, it is rejected because the artifact cannot be written](#presigned_urls-uploading-to-a-readonly-artifact-is-refused) | rejected |

### admin_search

<a id="searching-filtering-by-name-leaves-only-the-matching-object-storage"></a>

#### [filtering-by-name-leaves-only-the-matching-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_searching.py): pass

when the superadmin filters by name, only the object storage with that name comes back

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

- ObjectStorageAdapter.admin_search: user-1 searches object storages named object-storage-1

Then

- only the object storage with the matching name comes back
  - items: same as the object storages seeded in advance
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-searching-without-a-condition-counts-every-object-storage"></a>

#### [searching-without-a-condition-counts-every-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_searching.py): pass

when the superadmin searches object storages with no condition, every object storage seeded in advance comes back. This call is gated by the global role

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

- ObjectStorageAdapter.admin_search: user-1 searches object storages with no condition

Then

- every object storage seeded in advance comes back
  - items: same as the object storages seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-object-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_searching.py): pass

when a user who is not the superadmin tries to search object storages, it is rejected for lack of permission. This call is gated by the global role

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

- ObjectStorageAdapter.admin_search: user-1 searches object storages with no condition

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-reads-several-object-storages-in-the-requested-order"></a>

#### [the-superadmin-reads-several-object-storages-in-the-requested-order](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

when the superadmin loads two object storages seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty

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

- ObjectStorageAdapter.batch_load_by_ids: user-1 loads two object storages seeded in advance and one id that does not exist at once

Then

- the object storages seeded in advance come back in the requested order, and the entry for the id that does not exist is empty
  - length = 3
  - [0].name = 'object-storage-1'
  - [1] = None
  - [2].name = 'object-storage-2'

<a id="reading-a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

when a user granted nothing loads several object storage ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

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

- ObjectStorageAdapter.batch_load_by_ids: user-1 loads two object storages seeded in advance and one id that does not exist at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-an-object-storage"></a>

#### [the-superadmin-creates-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_creating.py): pass

when the superadmin creates an object storage, the whole created one comes back. This call is gated by the global role

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.create: user-1 creates an object storage

Then

- the whole created object storage comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'made-object-storage'
  - host = 'made.object-storage.test'
  - access_key = 'made-access-key'
  - secret_key = 'made-secret-key'
  - endpoint = 'https://made.object-storage.test'
  - region = 'made-region'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-an-object-storage"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_creating.py): pass

when a user who is not the superadmin tries to create an object storage, it is rejected for lack of permission. This call is gated by the global role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.create: user-1 creates an object storage

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-the-superadmin-gets-an-object-storage"></a>

#### [the-superadmin-gets-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

when the superadmin reads one object storage, the whole seeded object storage comes back

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

- ObjectStorageAdapter.get: user-1 reads object-storage-1

Then

- the whole object storage created in advance comes back
  - id: same as the object storage created in advance
  - entity_id: same as the object storage created in advance
  - name = 'object-storage-1'
  - host = 'seeded.object-storage.test'
  - access_key = 'seeded-access-key'
  - secret_key = 'seeded-secret-key'
  - endpoint = 'http://seeded.object-storage.test'
  - region = 'seeded-region'

<a id="reading-a-user-granted-nothing-may-not-get-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-get-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

when a user granted nothing reads one object storage, it is rejected for lack of permission

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

- ObjectStorageAdapter.get: user-1 reads object-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

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
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target object storage
  - rejected: failed[1]: Insufficient permission

### partial_bulk_update

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
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the target object storage
  - rejected: failed[1]: Insufficient permission

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

### get_presigned_download_url

<a id="presigned_urls-the-superadmin-gets-a-download-url-for-an-available-revision"></a>

#### [the-superadmin-gets-a-download-url-for-an-available-revision](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when the superadmin asks for a URL to download an object of an available revision, a URL made from the object's stored path comes back

Given

- one writable artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_download_url: user-1 asks for a URL to download model.bin of the revision

Then

- a download URL made from the object's stored path comes back
  - presigned_url = 'https://presigned.scenario.local/download/artifact-1/1.0/model.bin'

<a id="presigned_urls-downloading-an-unavailable-revision-is-refused"></a>

#### [downloading-an-unavailable-revision-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when a download URL is asked for a revision that is not available, it is rejected because the revision is not approved

Given

- one writable artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_download_url: user-1 asks for a URL to download model.bin of the revision

Then

- the call is rejected
  - rejected: ArtifactRevisionNotApproved

<a id="presigned_urls-downloading-from-a-vfs-reservoir-is-refused"></a>

#### [downloading-from-a-vfs-reservoir-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when the reservoir in the global config is not an object storage, a download URL request is rejected because the storage is not supported

Given

- one writable artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_download_url: user-1 asks for a URL to download model.bin of the revision

Then

- the call is rejected
  - rejected: ObjectStorageOperationNotSupported

<a id="presigned_urls-downloading-with-no-reservoir-config-is-refused"></a>

#### [downloading-with-no-reservoir-config-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when the global config has no reservoir, a download URL request is rejected because the server is misconfigured

Given

- one writable artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_download_url: user-1 asks for a URL to download model.bin of the revision

Then

- the call is rejected
  - rejected: ServerMisconfiguredError

### get_presigned_upload_url

<a id="presigned_urls-the-superadmin-gets-an-upload-url-for-a-writable-artifact"></a>

#### [the-superadmin-gets-an-upload-url-for-a-writable-artifact](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when the superadmin asks for a URL to upload an object to a writable artifact's revision, a URL made from the object's stored path comes back with the fields to send along

Given

- one writable artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_upload_url: user-1 asks for a URL to upload model.bin to the revision

Then

- an upload URL made from the object's stored path comes back with the fields to send along
  - presigned_url = 'https://presigned.scenario.local/upload/artifact-1/1.0/model.bin'
  - fields = {'policy': 'seeded-policy'}

<a id="presigned_urls-uploading-to-a-readonly-artifact-is-refused"></a>

#### [uploading-to-a-readonly-artifact-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

when an upload URL is asked for a readonly artifact's revision, it is rejected because the artifact cannot be written

Given

- one readonly artifact and one of its revisions, and one superadmin
  - Object storage archive-storage: host is seeded.object-storage.test
  - storage namespace archive-bucket: a bucket name registered on the object storage
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: artifact revision
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ObjectStorageAdapter.get_presigned_upload_url: user-1 asks for a URL to upload model.bin to the revision

Then

- the call is rejected
  - rejected: ArtifactReadonly

