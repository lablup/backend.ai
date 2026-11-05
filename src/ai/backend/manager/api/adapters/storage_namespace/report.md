## storage_namespace

[adapter](/src/ai/backend/manager/api/adapters/storage_namespace/adapter.py)

Scenario: complete

- built from ops (5)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - get_namespaces: representative success ✓ · representative rejection ✓
  - register: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - unregister: representative success ✓ · representative rejection ✓

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin loads two namespaces seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty](#reading-the-superadmin-reads-several-namespaces-in-the-requested-order) | answered |
| [when a user granted nothing loads several namespace ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id) | rejected |

**get_namespaces**

| scenario | verdict |
|---|---|
| [when the superadmin reads the namespaces of an object storage, every registered namespace comes back](#reading-the-superadmin-reads-every-namespace-of-an-object-storage) | answered |
| [when a user granted nothing reads the namespaces of an object storage, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage) | rejected |

**register**

| scenario | verdict |
|---|---|
| [when the superadmin registers a namespace on an object storage, the whole registered namespace comes back. This call is gated by the global role](#registering-the-superadmin-registers-a-namespace-on-an-object-storage) | answered |
| [when a user who is not the superadmin tries to register a namespace, it is rejected for lack of permission. This call is gated by the global role](#registering-a-user-who-is-not-the-superadmin-may-not-register-a-namespace) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin searches namespaces, every namespace seeded in advance comes back. This call is gated by the global role](#searching-the-superadmin-searching-namespaces-counts-every-one) | answered |
| [when a user who is not the superadmin tries to search namespaces, it is rejected for lack of permission. This call is gated by the global role](#searching-a-user-who-is-not-the-superadmin-may-not-search-namespaces) | rejected |

**unregister**

| scenario | verdict |
|---|---|
| [when the superadmin unregisters a namespace, the id of the object storage it was on comes back](#unregistering-the-superadmin-unregisters-a-namespace-from-an-object-storage) | answered |
| [when a user granted nothing tries to unregister a namespace, it is rejected. This call reads the namespace first, so a target the caller cannot read does not reveal whether it exists](#unregistering-a-user-granted-nothing-may-not-unregister-a-namespace) | rejected |
| [when the superadmin unregisters a namespace that was never registered, it is rejected because the target cannot be found](#unregistering-unregistering-a-namespace-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-the-superadmin-reads-several-namespaces-in-the-requested-order"></a>

#### [the-superadmin-reads-several-namespaces-in-the-requested-order](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

when the superadmin loads two namespaces seeded in advance and one id that does not exist at once, the two come back in the requested order and the entry for the id that does not exist is empty

Given

- one object storage with two namespaces registered on it and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.batch_load_by_ids: user-1 loads two namespaces seeded in advance and one id that does not exist at once

Then

- the namespaces seeded in advance come back in the requested order, and the entry for the id that does not exist is empty
  - length = 3
  - [0].id: same as the namespace seeded in advance
  - [0].entity_id: same as the namespace seeded in advance
  - [0].storage_id: same as the id of the object storage it is registered on
  - [0].namespace = 'seeded-bucket'
  - [1] = None
  - [2].id: same as the namespace seeded in advance
  - [2].entity_id: same as the namespace seeded in advance
  - [2].storage_id: same as the id of the object storage it is registered on
  - [2].namespace = 'second-bucket'

<a id="reading-a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

when a user granted nothing loads several namespace ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

Given

- one object storage with two namespaces registered on it and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.batch_load_by_ids: user-1 loads two namespaces seeded in advance and one id that does not exist at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### get_namespaces

<a id="reading-the-superadmin-reads-every-namespace-of-an-object-storage"></a>

#### [the-superadmin-reads-every-namespace-of-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

when the superadmin reads the namespaces of an object storage, every registered namespace comes back

Given

- one object storage with two namespaces registered on it and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.get_namespaces: user-1 reads the namespaces registered on object-storage-1

Then

- every namespace registered on the object storage comes back
  - items: same as the namespaces seeded in advance

<a id="reading-a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

when a user granted nothing reads the namespaces of an object storage, it is rejected for lack of permission

Given

- one object storage with two namespaces registered on it and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.get_namespaces: user-1 reads the namespaces registered on object-storage-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### register

<a id="registering-the-superadmin-registers-a-namespace-on-an-object-storage"></a>

#### [the-superadmin-registers-a-namespace-on-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_registering.py): pass

when the superadmin registers a namespace on an object storage, the whole registered namespace comes back. This call is gated by the global role

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

- StorageNamespaceAdapter.register: user-1 registers a namespace on object-storage-1

Then

- the whole registered namespace comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - storage_id: same as the object storage seeded in advance
  - namespace = 'registered-bucket'

<a id="registering-a-user-who-is-not-the-superadmin-may-not-register-a-namespace"></a>

#### [a-user-who-is-not-the-superadmin-may-not-register-a-namespace](/tests/scenario/bai_scenario/manager/storage_namespace/test_registering.py): pass

when a user who is not the superadmin tries to register a namespace, it is rejected for lack of permission. This call is gated by the global role

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

- StorageNamespaceAdapter.register: user-1 registers a namespace on object-storage-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search

<a id="searching-the-superadmin-searching-namespaces-counts-every-one"></a>

#### [the-superadmin-searching-namespaces-counts-every-one](/tests/scenario/bai_scenario/manager/storage_namespace/test_searching.py): pass

when the superadmin searches namespaces, every namespace seeded in advance comes back. This call is gated by the global role

Given

- one object storage with two namespaces registered on it and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.search: user-1 searches registered namespaces

Then

- every namespace seeded in advance comes back
  - items: same as the namespaces seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-namespaces"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-namespaces](/tests/scenario/bai_scenario/manager/storage_namespace/test_searching.py): pass

when a user who is not the superadmin tries to search namespaces, it is rejected for lack of permission. This call is gated by the global role

Given

- one object storage with two namespaces registered on it and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - Prepare an object storage with two namespaces registered
    - storage namespace seeded-bucket: a bucket name registered on the object storage
    - storage namespace second-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.search: user-1 searches registered namespaces

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### unregister

<a id="unregistering-the-superadmin-unregisters-a-namespace-from-an-object-storage"></a>

#### [the-superadmin-unregisters-a-namespace-from-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

when the superadmin unregisters a namespace, the id of the object storage it was on comes back

Given

- one object storage with one namespace registered on it and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - storage namespace seeded-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.unregister: user-1 unregisters the namespace seeded-bucket from object-storage-1

Then

- the id of the object storage the namespace left comes back
  - id: same as the object storage seeded in advance

<a id="unregistering-a-user-granted-nothing-may-not-unregister-a-namespace"></a>

#### [a-user-granted-nothing-may-not-unregister-a-namespace](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

when a user granted nothing tries to unregister a namespace, it is rejected. This call reads the namespace first, so a target the caller cannot read does not reveal whether it exists

Given

- one object storage with one namespace registered on it and one regular user
  - Object storage object-storage-1: host is seeded.object-storage.test
  - storage namespace seeded-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.unregister: user-1 unregisters the namespace seeded-bucket from object-storage-1

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="unregistering-unregistering-a-namespace-nothing-answers-to-is-not-found"></a>

#### [unregistering-a-namespace-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

when the superadmin unregisters a namespace that was never registered, it is rejected because the target cannot be found

Given

- one object storage with one namespace registered on it and one superadmin
  - Object storage object-storage-1: host is seeded.object-storage.test
  - storage namespace seeded-bucket: a bucket name registered on the object storage
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- StorageNamespaceAdapter.unregister: user-1 unregisters the namespace missing-bucket from object-storage-1

Then

- the call is rejected
  - rejected: EntityNotFoundError

