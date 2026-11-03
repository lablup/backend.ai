## deployment_revision_preset

[background](/src/ai/backend/manager/api/adapters/deployment_revision_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/deployment_revision_preset/adapter.py)

Scenario: incomplete 10 / 10

- built from ops (8)
  - available_presets: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_resource_slots: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (2)
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk, single_get_ops): SCENARIO-GAP
  - update: success absent · rejection absent (single_entity, single_get_ops): SCENARIO-GAP

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user who can only read presets tries to purge several presets at once, nothing is purged and every preset comes back in the failed list because the user lacks permission](#partial_bulk-a-preset-reader-purges-none-of-several-presets) | answered |
| [when a superadmin purges two presets and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it](#partial_bulk-purging-several-presets-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user who can only read presets tries to update several presets at once, nothing is updated and every preset comes back in the failed list because the user lacks permission](#partial_bulk-a-preset-reader-edits-none-of-several-presets) | answered |
| [when a superadmin changes the description of several presets at once, every preset comes back with the new description and nothing failed](#partial_bulk-the-superadmin-edits-several-presets-at-once) | answered |

### partial_bulk_purge

<a id="partial_bulk-a-preset-reader-purges-none-of-several-presets"></a>

#### [a-preset-reader-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

when a user who can only read presets tries to purge several presets at once, nothing is purged and every preset comes back in the failed list because the user lacks permission

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted read permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every deployment_preset
    - regular user user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge: user-1 purges 2 presets at once

Then

- no preset is processed and every preset comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the preset seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the preset seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk-purging-several-presets-answers-for-the-missing-one"></a>

#### [purging-several-presets-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

when a superadmin purges two presets and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it

Given

- one runtime variant and 2 deployment revision presets of it, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted read permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every deployment_preset
    - superadmin user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.partial_bulk_purge: user-1 purges 2 presets and one unknown id at once

Then

- every preset comes back with the description 'a preset seeded in advance' and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].description = 'a preset seeded in advance'
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].description = 'a preset seeded in advance'
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk-a-preset-reader-edits-none-of-several-presets"></a>

#### [a-preset-reader-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

when a user who can only read presets tries to update several presets at once, nothing is updated and every preset comes back in the failed list because the user lacks permission

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted read permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every deployment_preset
    - regular user user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.partial_bulk_update: user-1 changes the description of 2 presets at once

Then

- no preset is processed and every preset comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the preset seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the preset seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_partial_bulk.py): pass

when a superadmin changes the description of several presets at once, every preset comes back with the new description and nothing failed

Given

- one runtime variant and 2 deployment revision presets of it, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted read permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every deployment_preset
    - superadmin user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.partial_bulk_update: user-1 changes the description of 2 presets at once

Then

- every preset comes back with the description 'the description edited at once' and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].description = 'the description edited at once'
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].description = 'the description edited at once'
  - failed = []

