## artifact_registry

[adapter](/src/ai/backend/manager/api/adapters/artifact_registry/adapter.py)

Scenario: incomplete 1 / 3

- built from ops (2)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - get_registry_metas: representative success ✓ · representative rejection ✗: SCENARIO-GAP
- direct implementation (1)
  - get_registry_meta: success present 1 · rejection present 4 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [loading registries with an empty id list calls no lower layer and an empty answer comes back](#reading_many-an-empty-registry-id-list-answers-empty) | answered |
| [when the superadmin loads two registries made in advance and one id that does not exist at once, every position holds a whole registry made in advance and the position of the id that does not exist is empty](#reading_many-loading-many-registry-ids-keeps-the-positions) | answered |
| [when a user granted nothing loads several registry ids at once, every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection so whether it exists is not revealed](#reading_many-a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position) | rejected |

**get_registry_metas**

| scenario | verdict |
|---|---|
| [when a user granted nothing reads several registries at once, instead of the whole request being rejected no registry is readable and an empty list comes back](#reading_many-a-user-granted-nothing-reading-many-registries-gets-none) | answered |
| [when a user granted read permission on artifact registries in global reads two registries made in advance and one id that does not exist at once, only the two readable registries come back in the requested order](#reading_many-reading-many-registries-leaves-out-the-id-that-names-none) | answered |

**get_registry_meta**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifact registries in global reads a registry by id, the whole registry made in advance comes back](#reading-a-user-granted-read-reads-a-registry-by-id) | answered |
| [reading by a name that names no registry is rejected as the name not being resolvable](#reading-a-name-naming-no-registry-is-refused) | rejected |
| [when a user granted nothing tries to read a registry by id, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-a-registry) | rejected |
| [when the superadmin reads by an id that names no registry, it is rejected as no such registry](#reading-an-id-naming-no-registry-is-refused) | rejected |
| [reading a registry with neither an id nor a name is rejected as invalid request parameters](#reading-reading-a-registry-with-neither-an-id-nor-a-name-is-refused) | rejected |

### batch_load_by_ids

<a id="reading_many-an-empty-registry-id-list-answers-empty"></a>

#### [an-empty-registry-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

loading registries with an empty id list calls no lower layer and an empty answer comes back

Given

- 2 HuggingFace registries and one superadmin
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.batch_load_by_ids: user-1 loads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading_many-loading-many-registry-ids-keeps-the-positions"></a>

#### [loading-many-registry-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

when the superadmin loads two registries made in advance and one id that does not exist at once, every position holds a whole registry made in advance and the position of the id that does not exist is empty

Given

- 2 HuggingFace registries and one superadmin
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.batch_load_by_ids: user-1 loads two registries made in advance and one id that does not exist at once

Then

- every position holds a whole registry made in advance, and the position of the id that does not exist is empty
  - length = 3
  - [0].id: same as the entity id in the same answer
  - [0].entity_id: same as the id in the same answer
  - [0].registry_id: same as the id of the registry made in advance
  - [0].name = 'registry-1'
  - [0].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1] = None
  - [2].id: same as the entity id in the same answer
  - [2].entity_id: same as the id in the same answer
  - [2].registry_id: same as the id of the registry made in advance
  - [2].name = 'registry-2'
  - [2].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

<a id="reading_many-a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position"></a>

#### [a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

when a user granted nothing loads several registry ids at once, every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection so whether it exists is not revealed

Given

- 2 HuggingFace registries and one user with no permission
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.batch_load_by_ids: user-1 loads two registries made in advance and one id that does not exist at once

Then

- every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection, so whether it exists is not revealed
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### get_registry_metas

<a id="reading_many-a-user-granted-nothing-reading-many-registries-gets-none"></a>

#### [a-user-granted-nothing-reading-many-registries-gets-none](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

when a user granted nothing reads several registries at once, instead of the whole request being rejected no registry is readable and an empty list comes back

Given

- 2 HuggingFace registries and one user with no permission
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.get_registry_metas: user-1 reads 2 registries made in advance at once

Then

- no registry is readable and an empty list comes back
  - items = []

<a id="reading_many-reading-many-registries-leaves-out-the-id-that-names-none"></a>

#### [reading-many-registries-leaves-out-the-id-that-names-none](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading_many.py): pass

when a user granted read permission on artifact registries in global reads two registries made in advance and one id that does not exist at once, only the two readable registries come back in the requested order

Given

- 2 HuggingFace registries and one user granted READ on artifact registries in global
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - HuggingFace registry registry-2: refers to https://huggingface.co
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

- ArtifactRegistryAdapter.get_registry_metas: user-1 reads 2 registries made in advance and one id that does not exist at once

Then

- only the registries the caller may read come back in the requested order, and an id that is unreadable or names no registry is left out
  - count = 2
  - [0].id: same as the entity id in the same answer
  - [0].entity_id: same as the id in the same answer
  - [0].registry_id: same as the id of the registry made in advance
  - [0].name = 'registry-1'
  - [0].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].id: same as the entity id in the same answer
  - [1].entity_id: same as the id in the same answer
  - [1].registry_id: same as the id of the registry made in advance
  - [1].name = 'registry-2'
  - [1].type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

### get_registry_meta

<a id="reading-a-user-granted-read-reads-a-registry-by-id"></a>

#### [a-user-granted-read-reads-a-registry-by-id](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

when a user granted read permission on artifact registries in global reads a registry by id, the whole registry made in advance comes back

Given

- one HuggingFace registry and one user granted READ on artifact registries in global
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
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

- ArtifactRegistryAdapter.get_registry_meta: user-1 reads registry-1 by id

Then

- the whole registry made in advance comes back
  - id: same as the entity id in the same answer
  - entity_id: same as the id in the same answer
  - registry_id: same as the id of the registry made in advance
  - name = 'registry-1'
  - type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>

<a id="reading-a-name-naming-no-registry-is-refused"></a>

#### [a-name-naming-no-registry-is-refused](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

reading by a name that names no registry is rejected as the name not being resolvable

Given

- one HuggingFace registry and one user with no permission
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.get_registry_meta: user-1 reads by a name that names no registry

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="reading-a-user-granted-nothing-may-not-read-a-registry"></a>

#### [a-user-granted-nothing-may-not-read-a-registry](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

when a user granted nothing tries to read a registry by id, it is rejected for lack of permission

Given

- one HuggingFace registry and one user with no permission
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.get_registry_meta: user-1 reads registry-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-an-id-naming-no-registry-is-refused"></a>

#### [an-id-naming-no-registry-is-refused](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

when the superadmin reads by an id that names no registry, it is rejected as no such registry

Given

- one HuggingFace registry and one superadmin
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.get_registry_meta: user-1 reads by an id that names no registry

Then

- the call is rejected
  - rejected: ArtifactRegistryNotFoundError

<a id="reading-reading-a-registry-with-neither-an-id-nor-a-name-is-refused"></a>

#### [reading-a-registry-with-neither-an-id-nor-a-name-is-refused](/tests/scenario/bai_scenario/manager/artifact_registry/test_reading.py): pass

reading a registry with neither an id nor a name is rejected as invalid request parameters

Given

- one HuggingFace registry and one user with no permission
  - Domain home-1
  - HuggingFace registry registry-1: refers to https://huggingface.co
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactRegistryAdapter.get_registry_meta: user-1 reads with neither an id nor a name

Then

- the call is rejected
  - rejected: InvalidAPIParameters

