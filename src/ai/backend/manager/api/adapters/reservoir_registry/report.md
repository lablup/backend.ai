## reservoir_registry

[background](/src/ai/backend/manager/api/adapters/reservoir_registry/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/reservoir_registry/adapter.py)

Scenario: incomplete 7 / 9

- built from ops (1)
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (8)
  - create: success absent · rejection absent (global_scope): SCENARIO-GAP
  - get: success absent · rejection absent (single_entity): SCENARIO-GAP
  - get_many: success absent · rejection absent (global_scope): SCENARIO-GAP
  - partial_bulk_purge: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 1 · rejection present 1 (single_entity)
  - search: success absent · rejection absent (global_scope): SCENARIO-GAP
  - update: success present 1 · rejection present 1 (single_entity)

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several Reservoir registries at once, nothing is purged and all come back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | answered |
| [when a user granted permission to purge Reservoir registries purges several at once, every id comes back in the processed list and none failed](#partial_bulk_purging-a-user-granted-purge-purges-several-registries) | answered |
| [when the superadmin purges two Reservoir registries and one id that does not exist at once, the two ids come back in the processed list and the id that does not exist comes back in the failed list because there is no such target. The superadmin passes every check, so the missing target is revealed as it is](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several Reservoir registries at once, nothing is edited and all come back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-registries) | answered |
| [when a user granted permission to edit Reservoir registries changes the endpoints of several at once, all come back with the new endpoint and none failed](#partial_bulk_editing-a-user-granted-update-edits-several-registries) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted permission to purge Reservoir registries purges one, the id of the purged Reservoir registry comes back](#purging-a-user-granted-purge-purges-a-registry) | answered |
| [when a user granted nothing tries to purge, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-registry) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted permission to edit Reservoir registries changes the endpoint, the Reservoir registry comes back with the new endpoint](#editing-a-user-granted-update-edits-a-registry) | answered |
| [when a user granted nothing tries to change the endpoint, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-registry) | rejected |

### partial_bulk_purge

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
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target registry
  - failed[1].message: a reason containing 'Insufficient permission'

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

### partial_bulk_update

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
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target registry
  - failed[1].message: a reason containing 'Insufficient permission'

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

