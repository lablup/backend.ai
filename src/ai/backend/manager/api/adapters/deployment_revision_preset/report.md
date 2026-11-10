## deployment_revision_preset

[background](/src/ai/backend/manager/api/adapters/deployment_revision_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/deployment_revision_preset/adapter.py)

Scenario: incomplete 3 / 10

- built from ops (8)
  - available_presets: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - search_resource_slots: representative success ✓ · representative rejection ✓
- ops + direct implementation (2)
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk, single_get_ops): SCENARIO-GAP
  - update: success present 1 · rejection present 1 (single_entity, single_get_ops)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted preset read loads the presets seeded in advance by id in one call, they come back in input order](#batch_loading-a-preset-reader-loads-the-presets-by-id) | answered |
| [when a user granted nothing loads the presets seeded in advance by id in one call, the call succeeds but a rejection for lack of permission comes back for each entry](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-each-preset) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin makes a preset, an operation gated by the global role, the preset made comes back. The requesting user of this row is the superadmin because the call is gated by the global role](#creating-the-superadmin-makes-a-preset) | answered |
| [when a user granted only preset read tries to make a preset, the create is rejected because the user lacks the global role](#creating-a-preset-reader-makes-no-preset) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted preset read reads one of the presets seeded in advance by id, that preset comes back](#reading-a-preset-reader-reads-a-preset) | answered |
| [when a user granted preset read reads a preset carrying a model definition and runtime preset values by id, that preset comes back](#reading-a-preset-reader-reads-a-preset-with-a-model-definition) | answered |
| [when a user granted nothing tries to read one of the presets seeded in advance by id, the read is rejected because the user lacks permission](#reading-a-user-granted-nothing-reads-no-preset) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user who can only read presets tries to purge several presets at once, nothing is purged and every preset comes back in the failed list because the user lacks permission](#partial_bulk-a-preset-reader-purges-none-of-several-presets) | answered |
| [when a superadmin purges two presets and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it](#partial_bulk-purging-several-presets-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted preset hard delete purges one of the presets seeded in advance, the id of that preset comes back](#retiring-a-user-granted-hard-delete-purges-a-preset) | answered |
| [when a user granted only preset read tries to purge one of the presets seeded in advance, the purge is rejected because the user lacks permission](#retiring-a-preset-reader-purges-no-preset) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when a user granted preset read searches the presets with a filter, every preset seeded in advance comes back](#searching-a-preset-reader-searches-every-preset) | answered |
| [when a user granted nothing tries to search the presets, the search is rejected because the user lacks permission](#searching-a-user-granted-nothing-searches-no-preset) | rejected |

**search_resource_slots**

| scenario | verdict |
|---|---|
| [when a user granted preset read searches the resource slots the preset declares with a filter, that slot comes back](#searching_slots-a-preset-reader-searches-the-slots-of-a-preset) | answered |
| [when a user granted nothing tries to search the resource slots the preset declares, the search is rejected because the user lacks permission](#searching_slots-a-user-granted-nothing-searches-no-slots) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user who can only read presets tries to update several presets at once, nothing is updated and every preset comes back in the failed list because the user lacks permission](#partial_bulk-a-preset-reader-edits-none-of-several-presets) | answered |
| [when a superadmin changes the description of several presets at once, every preset comes back with the new description and nothing failed](#partial_bulk-the-superadmin-edits-several-presets-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [when a user granted preset update changes the description of one of the presets seeded in advance, the preset comes back with the new description](#updating-a-user-granted-update-edits-a-preset) | answered |
| [when a user granted only preset read tries to change the description of one of the presets, the edit is rejected because the user lacks permission](#updating-a-preset-reader-edits-no-preset) | rejected |

### batch_load_by_ids

<a id="batch_loading-a-preset-reader-loads-the-presets-by-id"></a>

#### [a-preset-reader-loads-the-presets-by-id](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_batch_loading.py): pass

when a user granted preset read loads the presets seeded in advance by id in one call, they come back in input order

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

- DeploymentRevisionPresetAdapter.batch_load_by_ids: user-1 loads 2 of the presets seeded in advance by id in one call

Then

- the presets seeded in advance come back whole in input order
  - length = 2
  - [0].id: same as the id of the preset seeded in advance
  - [0].entity_id: same as the id of the preset seeded in advance
  - [0].runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - [0].name = 'preset-1'
  - [0].description = 'a preset created in advance'
  - [0].rank = 100
  - [0].cluster.cluster_mode = 'single-node'
  - [0].cluster.cluster_size = 1
  - [0].resource.resource_opts = []
  - [0].execution.image_id: the image id fixed in advance
  - [0].execution.startup_command = None
  - [0].execution.bootstrap_script = None
  - [0].execution.environ = []
  - [0].deployment_defaults.open_to_public = None
  - [0].deployment_defaults.replica_count = 1
  - [0].deployment_defaults.revision_history_limit = None
  - [0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - [0].deployment_defaults.deployment_strategy_spec = {}
  - [0].model_definition = None
  - [0].preset_values count = 0
  - [0].created_at: same as the time the preset seeded in advance was made
  - [0].updated_at: same as the time the preset seeded in advance was made
  - [1].id: same as the id of the preset seeded in advance
  - [1].entity_id: same as the id of the preset seeded in advance
  - [1].runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - [1].name = 'preset-2'
  - [1].description = 'a preset created in advance'
  - [1].rank = 200
  - [1].cluster.cluster_mode = 'single-node'
  - [1].cluster.cluster_size = 1
  - [1].resource.resource_opts = []
  - [1].execution.image_id: the image id fixed in advance
  - [1].execution.startup_command = None
  - [1].execution.bootstrap_script = None
  - [1].execution.environ = []
  - [1].deployment_defaults.open_to_public = None
  - [1].deployment_defaults.replica_count = 1
  - [1].deployment_defaults.revision_history_limit = None
  - [1].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - [1].deployment_defaults.deployment_strategy_spec = {}
  - [1].model_definition = None
  - [1].preset_values count = 0
  - [1].created_at: same as the time the preset seeded in advance was made
  - [1].updated_at: same as the time the preset seeded in advance was made

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-each-preset"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-each-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_batch_loading.py): pass

when a user granted nothing loads the presets seeded in advance by id in one call, the call succeeds but a rejection for lack of permission comes back for each entry

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user granted nothing on presets
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DeploymentRevisionPresetAdapter.batch_load_by_ids: user-1 loads 2 of the presets seeded in advance by id in one call

Then

- a rejection for lack of permission comes back for each entry
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-makes-a-preset"></a>

#### [the-superadmin-makes-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_creating.py): pass

when the superadmin makes a preset, an operation gated by the global role, the preset made comes back. The requesting user of this row is the superadmin because the call is gated by the global role

Given

- one runtime variant and one superadmin to make a preset of it
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- DeploymentRevisionPresetAdapter.create: user-1 makes one preset of the runtime variant

Then

- the whole preset made comes back
  - preset.id: skipped: the database generates it
  - preset.entity_id: skipped: the database generates it
  - preset.runtime_variant_id: same as the id of the variant laid before
  - preset.name = 'created-preset'
  - preset.description = 'a preset made by this run'
  - preset.rank: a ranked value
  - preset.cluster.cluster_mode = 'single-node'
  - preset.cluster.cluster_size = 1
  - preset.resource.resource_opts = []
  - preset.execution.image_id: the image id fixed in advance
  - preset.execution.startup_command = None
  - preset.execution.bootstrap_script = None
  - preset.execution.environ = []
  - preset.deployment_defaults.open_to_public = None
  - preset.deployment_defaults.replica_count = 1
  - preset.deployment_defaults.revision_history_limit = None
  - preset.deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - preset.deployment_defaults.deployment_strategy_spec = {}
  - preset.model_definition = None
  - preset.preset_values = []
  - preset.created_at: the time this run wrote
  - preset.updated_at: the time this run wrote

<a id="creating-a-preset-reader-makes-no-preset"></a>

#### [a-preset-reader-makes-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_creating.py): pass

when a user granted only preset read tries to make a preset, the create is rejected because the user lacks the global role

Given

- one runtime variant and one regular user to make a preset of it
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- DeploymentRevisionPresetAdapter.create: user-1 makes one preset of the runtime variant

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-preset-reader-reads-a-preset"></a>

#### [a-preset-reader-reads-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

when a user granted preset read reads one of the presets seeded in advance by id, that preset comes back

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

- DeploymentRevisionPresetAdapter.get: user-1 reads one of the presets seeded in advance by id

Then

- the whole preset read comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - name = 'preset-1'
  - description = 'a preset created in advance'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: the image id fixed in advance
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = None
  - preset_values count = 0
  - created_at: same as the time the preset seeded in advance was made
  - updated_at: same as the time the preset seeded in advance was made

<a id="reading-a-preset-reader-reads-a-preset-with-a-model-definition"></a>

#### [a-preset-reader-reads-a-preset-with-a-model-definition](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

when a user granted preset read reads a preset carrying a model definition and runtime preset values by id, that preset comes back

Given

- one deployment revision preset carrying a model definition and runtime preset values, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Deployment revision preset preset-2: single node, one replica, rolling update, carries a model definition, carries runtime preset values
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

- DeploymentRevisionPresetAdapter.get: user-1 reads one of the presets seeded in advance by id

Then

- the whole preset read comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - name = 'preset-2'
  - description = 'a preset created in advance'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: the image id fixed in advance
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = PresetModelDefinitionInfoDTO(models=[PresetModelConfigInfoDTO(name='preset-model', model_path='/models/preset-model', service=None, metadata=None)])
  - preset_values count = 1
  - preset_values[0].preset_id: same as the id of the runtime variant preset the value is bound to
  - preset_values[0].value = 'preset-value'
  - created_at: same as the time the preset seeded in advance was made
  - updated_at: same as the time the preset seeded in advance was made

<a id="reading-a-user-granted-nothing-reads-no-preset"></a>

#### [a-user-granted-nothing-reads-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_reading.py): pass

when a user granted nothing tries to read one of the presets seeded in advance by id, the read is rejected because the user lacks permission

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user granted nothing on presets
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DeploymentRevisionPresetAdapter.get: user-1 reads one of the presets seeded in advance by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

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

### purge

<a id="retiring-a-user-granted-hard-delete-purges-a-preset"></a>

#### [a-user-granted-hard-delete-purges-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_retiring.py): pass

when a user granted preset hard delete purges one of the presets seeded in advance, the id of that preset comes back

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted the HARD_DELETE permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: HARD_DELETE allowed on every deployment_preset
    - regular user user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.purge: user-1 purges one of the presets seeded in advance

Then

- the id of the purged preset comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance

<a id="retiring-a-preset-reader-purges-no-preset"></a>

#### [a-preset-reader-purges-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_retiring.py): pass

when a user granted only preset read tries to purge one of the presets seeded in advance, the purge is rejected because the user lacks permission

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

- DeploymentRevisionPresetAdapter.purge: user-1 purges one of the presets seeded in advance

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search

<a id="searching-a-preset-reader-searches-every-preset"></a>

#### [a-preset-reader-searches-every-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching.py): pass

when a user granted preset read searches the presets with a filter, every preset seeded in advance comes back

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user, one more preset with a different name
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Deployment revision preset other-1: single node, one replica, rolling update
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

- DeploymentRevisionPresetAdapter.search: user-1 searches the presets with one filter, one order and pagination

Then

- the preset the filter excludes does not come back, and the presets seeded in advance come back
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the preset seeded in advance
  - items[0].entity_id: same as the id of the preset seeded in advance
  - items[0].runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - items[0].name = 'preset-1'
  - items[0].description = 'a preset created in advance'
  - items[0].rank = 100
  - items[0].cluster.cluster_mode = 'single-node'
  - items[0].cluster.cluster_size = 1
  - items[0].resource.resource_opts = []
  - items[0].execution.image_id: the image id fixed in advance
  - items[0].execution.startup_command = None
  - items[0].execution.bootstrap_script = None
  - items[0].execution.environ = []
  - items[0].deployment_defaults.open_to_public = None
  - items[0].deployment_defaults.replica_count = 1
  - items[0].deployment_defaults.revision_history_limit = None
  - items[0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[0].deployment_defaults.deployment_strategy_spec = {}
  - items[0].model_definition = None
  - items[0].preset_values count = 0
  - items[0].created_at: same as the time the preset seeded in advance was made
  - items[0].updated_at: same as the time the preset seeded in advance was made
  - items[1].id: same as the id of the preset seeded in advance
  - items[1].entity_id: same as the id of the preset seeded in advance
  - items[1].runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - items[1].name = 'preset-2'
  - items[1].description = 'a preset created in advance'
  - items[1].rank = 200
  - items[1].cluster.cluster_mode = 'single-node'
  - items[1].cluster.cluster_size = 1
  - items[1].resource.resource_opts = []
  - items[1].execution.image_id: the image id fixed in advance
  - items[1].execution.startup_command = None
  - items[1].execution.bootstrap_script = None
  - items[1].execution.environ = []
  - items[1].deployment_defaults.open_to_public = None
  - items[1].deployment_defaults.replica_count = 1
  - items[1].deployment_defaults.revision_history_limit = None
  - items[1].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[1].deployment_defaults.deployment_strategy_spec = {}
  - items[1].model_definition = None
  - items[1].preset_values count = 0
  - items[1].created_at: same as the time the preset seeded in advance was made
  - items[1].updated_at: same as the time the preset seeded in advance was made

<a id="searching-a-user-granted-nothing-searches-no-preset"></a>

#### [a-user-granted-nothing-searches-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching.py): pass

when a user granted nothing tries to search the presets, the search is rejected because the user lacks permission

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user granted nothing on presets
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DeploymentRevisionPresetAdapter.search: user-1 searches the presets with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_resource_slots

<a id="searching_slots-a-preset-reader-searches-the-slots-of-a-preset"></a>

#### [a-preset-reader-searches-the-slots-of-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching_slots.py): pass

when a user granted preset read searches the resource slots the preset declares with a filter, that slot comes back

Given

- two slot types and two presets declaring them (a preset seeded in advance) and one user who can read them, one more slot of a different slot type on the same preset, and one slot on another preset
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-1: declares one cpu slot
  - Deployment revision preset preset-1: declares one mem slot
  - Deployment revision preset other-1: single node, one replica, rolling update
  - Deployment revision preset other-1: declares one cpu slot
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

- DeploymentRevisionPresetAdapter.search_resource_slots: user-1 searches the resource slots the preset declares with one filter, one order and pagination

Then

- the slot the filter excludes and the slot on another preset do not come back, and the slot the preset declares comes back with its quantity
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].slot_name = 'cpu'
  - items[0].quantity = Decimal('4')

<a id="searching_slots-a-user-granted-nothing-searches-no-slots"></a>

#### [a-user-granted-nothing-searches-no-slots](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_searching_slots.py): pass

when a user granted nothing tries to search the resource slots the preset declares, the search is rejected because the user lacks permission

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user granted nothing on presets
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- DeploymentRevisionPresetAdapter.search_resource_slots: user-1 searches the resource slots the preset declares with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

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

### update

<a id="updating-a-user-granted-update-edits-a-preset"></a>

#### [a-user-granted-update-edits-a-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_updating.py): pass

when a user granted preset update changes the description of one of the presets seeded in advance, the preset comes back with the new description

Given

- one runtime variant and 2 deployment revision presets of it, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: single node, one replica, rolling update
  - Deployment revision preset preset-2: single node, one replica, rolling update
  - Domain home-1
  - Prepare a user granted the UPDATE permission on deployment_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: UPDATE allowed on every deployment_preset
    - regular user user-1: holds Role public-reader-1

When

- DeploymentRevisionPresetAdapter.update: user-1 changes the description of one of the presets

Then

- the whole preset edited comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - runtime_variant_id: same as the id of the runtime variant the preset is laid on
  - name = 'preset-1'
  - description = 'the description edited at once'
  - rank = 100
  - cluster.cluster_mode = 'single-node'
  - cluster.cluster_size = 1
  - resource.resource_opts = []
  - execution.image_id: the image id fixed in advance
  - execution.startup_command = None
  - execution.bootstrap_script = None
  - execution.environ = []
  - deployment_defaults.open_to_public = None
  - deployment_defaults.replica_count = 1
  - deployment_defaults.revision_history_limit = None
  - deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - deployment_defaults.deployment_strategy_spec = {}
  - model_definition = None
  - preset_values count = 0
  - created_at: same as the time the preset seeded in advance was made
  - updated_at: the time this run wrote

<a id="updating-a-preset-reader-edits-no-preset"></a>

#### [a-preset-reader-edits-no-preset](/tests/scenario/bai_scenario/manager/deployment_revision_preset/test_updating.py): pass

when a user granted only preset read tries to change the description of one of the presets, the edit is rejected because the user lacks permission

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

- DeploymentRevisionPresetAdapter.update: user-1 changes the description of one of the presets

Then

- the call is rejected
  - rejected: NotEnoughPermission

