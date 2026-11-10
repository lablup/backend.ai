## model_card

[background](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

Scenario: complete

- built from ops (8)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - min_resources: representative success ✓ · representative rejection ✓
  - ownership_search: representative success ✓ · representative rejection ✓
  - project_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- ops + direct implementation (3)
  - deploy: success present 1 · rejection present 1 (scope, single_get_ops)
  - partial_bulk_update: success present 1 · rejection present 1 (atomic_bulk_scoped_search_ops, partial_bulk)
  - update: success present 1 · rejection present 1 (atomic_bulk_scoped_search_ops, single_entity)
- direct implementation (4)
  - admin_bulk_delete: success present 1 · rejection present 1 (partial_bulk)
  - partial_bulk_purge: success present 1 · rejection present 1 (partial_bulk)
  - purge: success present 1 · rejection present 1 (single_entity)
  - scan_project: success present 1 · rejection present 2 (global_scope)
- no Action (1)
  - available_presets: success present 1 · rejection absent

**admin_search**

| scenario | verdict |
|---|---|
| [with no model card seeded, a superadmin reading every card gets an empty answer](#model_card-a-scenario-that-laid-no-model-card-finds-none) | answered |
| [when a user who is not the superadmin asks to read every model card, the role blocks it](#model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the project loads two cards of that project by id, both cards come back in input order](#batch_loading-a-user-granted-model-card-read-loads-cards-by-id-in-order) | answered |
| [when a user granted model card read in only one project loads a card of that project and a card of another project together, the call succeeds but the entry of the other project's card is rejected for lack of permission](#batch_loading-a-card-of-a-project-without-read-gets-a-rejection-in-the-batch) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted create and read permission on model cards in the project creates a card, a card placed in that project and created by that user comes back with the requested values and minimum resources](#creating-a-user-granted-create-in-the-project-makes-a-model-card) | answered |
| [when a user granted create and read permission on model cards in the project creates a card under the name of a card already in that project, the call is rejected as a name conflict](#creating-a-name-taken-in-the-project-is-refused) | rejected |
| [when a user granted only read permission on model cards in the project tries to create a card, the call is rejected for lack of permission](#creating-a-user-granted-only-read-may-not-make-a-model-card) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the project reads a card by id, the whole card comes back](#getting-a-user-granted-model-card-read-gets-a-card-by-id) | answered |
| [when a user granted only model card update and not read in the project reads a card by id, the call is rejected for lack of permission](#getting-a-user-without-model-card-read-may-not-get-a-card) | rejected |

**min_resources**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the project reads the minimum resource requirements of two cards of that project, the requirement seeded for each card comes back](#min_resources-a-user-granted-model-card-read-reads-the-minimum-resources) | answered |
| [when a user granted model card read in only one project reads the minimum resource requirements of a card of that project and a card of another project together, the whole call is rejected for lack of permission](#min_resources-a-card-of-a-project-without-read-refuses-the-whole-call) | rejected |

**ownership_search**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page](#searching-a-user-granted-model-card-read-finds-cards-by-vfolder-ownership) | answered |
| [when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission](#searching-a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership) | rejected |

**project_search**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page](#searching-a-user-granted-model-card-read-finds-cards-by-project) | answered |
| [when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission](#searching-a-user-without-model-card-read-may-not-find-cards-by-project) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page](#searching-a-user-granted-model-card-read-finds-cards-by-scope) | answered |
| [when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission](#searching-a-user-without-model-card-read-may-not-find-cards-by-scope) | rejected |

**deploy**

| scenario | verdict |
|---|---|
| [when a user who can read the card and its vfolder and is granted deployment create in the project deploys the card with a preset, a deployment named after the card is created](#deploying-a-user-granted-deployment-create-deploys-a-model-card) | answered |
| [when a user who can read the card and its vfolder in the project but is not granted deployment create tries to deploy the card, the call is rejected for lack of permission](#deploying-a-user-without-deployment-create-may-not-deploy-a-model-card) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted read and update permission on model cards in the project changes the titles of several cards at once, they all come back with the new title and nothing failed](#partial_bulk_editing-a-user-granted-update-edits-several-model-cards) | answered |
| [when a user granted read and update permission on model cards in the project edits a card of that project and a card of another project at once, only the card of that project comes back with the new title and the other one comes back in the failed list for lack of permission](#partial_bulk_editing-a-card-outside-the-granted-project-is-not-edited) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted read and update permission on model cards in the project changes the title of a card, the title takes the new value and the rest stays unchanged](#editing-a-user-granted-update-in-the-project-edits-a-model-card) | answered |
| [when a user granted nothing tries to update a model card, the call is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-model-card) | rejected |

**admin_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted purge permission on model cards in the project deletes two cards at once, the ids of both come back in the processed list and nothing failed](#bulk_deleting-a-user-granted-purge-deletes-several-model-cards) | answered |
| [when a user granted purge permission on model cards in the project deletes a card of that project and a card of another project at once, only the card of that project comes back in the processed list and the other one comes back in the failed list for lack of permission](#bulk_deleting-a-card-outside-the-granted-project-is-not-deleted) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted purge permission on model cards in the project purges two cards at once, both come back in the processed list and nothing failed](#partial_bulk_purging-a-user-granted-purge-purges-several-model-cards) | answered |
| [when a user granted purge permission on model cards in the project purges a card of that project and a card of another project at once, only the card of that project comes back in the processed list and the other one comes back in the failed list for lack of permission](#partial_bulk_purging-a-card-outside-the-granted-project-is-not-purged) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted purge permission on model cards in the project purges a card, the id of that card comes back](#purging-a-user-granted-purge-in-the-project-purges-a-model-card) | answered |
| [when a user granted nothing tries to purge a model card, the call is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-model-card) | rejected |

**scan_project**

| scenario | verdict |
|---|---|
| [when the superadmin scans a model-store project holding one vfolder with a model definition file, one card is created. The global role gates this call, so the superadmin calls it](#scanning-the-superadmin-scans-a-model-store-into-a-card) | answered |
| [when the superadmin tries to scan a project that is not a model-store, the call is rejected for the wrong project type](#scanning-a-project-that-is-not-a-model-store-is-refused) | rejected |
| [when a regular user tries to scan a model-store project, the global role rejects the call](#scanning-a-regular-user-may-not-scan-a-model-store) | rejected |

**available_presets**

| scenario | verdict |
|---|---|
| [when a user who can read presets and the card looks for the presets the card can be deployed on, filtered and ordered by name, one page at a time, only the presets meeting the minimum resources the card requires are counted, and neither the preset falling short nor the one the filter excludes comes back](#available_presets-a-reader-finds-the-presets-meeting-the-card) | answered |

### admin_search

<a id="model_card-a-scenario-that-laid-no-model-card-finds-none"></a>

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py): pass

with no model card seeded, a superadmin reading every card gets an empty answer

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ModelCardAdapter.admin_search: user-1 reads every card without a filter

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py): pass

when a user who is not the superadmin asks to read every model card, the role blocks it

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ModelCardAdapter.admin_search: user-1 reads every card without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-model-card-read-loads-cards-by-id-in-order"></a>

#### [a-user-granted-model-card-read-loads-cards-by-id-in-order](/tests/scenario/bai_scenario/manager/model_card/test_batch_loading.py): pass

when a user granted model card read in the project loads two cards of that project by id, both cards come back in input order

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.batch_load_by_ids: user-2 loads the cards card-1 and card-2 by id in one call

Then

- both cards come back in input order with their optional fields and minimum resource requirement filled
  - length = 2
  - [0].id: same as the card created in advance
  - [0].entity_id: same as the card created in advance
  - [0].name = 'card-1'
  - [0].vfolder_id: same as the vfolder the card is placed on
  - [0].domain_name = 'home-1'
  - [0].project_id: same as the project the card is placed in
  - [0].creator_id: same as the user who created the card
  - [0].metadata.author = 'the-author'
  - [0].metadata.title = 'a card the search finds'
  - [0].metadata.model_version = '1.0'
  - [0].metadata.description = 'the description'
  - [0].metadata.task = 'text-generation'
  - [0].metadata.category = 'llm'
  - [0].metadata.architecture = 'llama'
  - [0].metadata.framework = ['pytorch']
  - [0].metadata.label = ['chat']
  - [0].metadata.license = 'apache-2.0'
  - [0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - [0].readme = 'the readme'
  - [0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1].id: same as the card created in advance
  - [1].entity_id: same as the card created in advance
  - [1].name = 'card-2'
  - [1].vfolder_id: same as the vfolder the card is placed on
  - [1].domain_name = 'home-1'
  - [1].project_id: same as the project the card is placed in
  - [1].creator_id: same as the user who created the card
  - [1].metadata.author = 'the-author'
  - [1].metadata.title = 'a card the search finds'
  - [1].metadata.model_version = '1.0'
  - [1].metadata.description = 'the description'
  - [1].metadata.task = 'text-generation'
  - [1].metadata.category = 'llm'
  - [1].metadata.architecture = 'llama'
  - [1].metadata.framework = ['pytorch']
  - [1].metadata.label = ['chat']
  - [1].metadata.license = 'apache-2.0'
  - [1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - [1].readme = 'the readme'
  - [1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [1].created_at: the time this run wrote
  - [1].updated_at: the time this run wrote

<a id="batch_loading-a-card-of-a-project-without-read-gets-a-rejection-in-the-batch"></a>

#### [a-card-of-a-project-without-read-gets-a-rejection-in-the-batch](/tests/scenario/bai_scenario/manager/model_card/test_batch_loading.py): pass

when a user granted model card read in only one project loads a card of that project and a card of another project together, the call succeeds but the entry of the other project's card is rejected for lack of permission

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.batch_load_by_ids: user-2 loads the card card-1 and the card card-5 of the other project by id in one call

Then

- the readable card comes back as a node and the entry of the card without permission as a rejection for lack of permission
  - length = 2
  - [0].id: same as the card created in advance
  - [0].entity_id: same as the card created in advance
  - [0].name = 'card-1'
  - [0].vfolder_id: same as the vfolder the card is placed on
  - [0].domain_name = 'home-1'
  - [0].project_id: same as the project the card is placed in
  - [0].creator_id: same as the user who created the card
  - [0].metadata.author = 'the-author'
  - [0].metadata.title = 'a card the search finds'
  - [0].metadata.model_version = '1.0'
  - [0].metadata.description = 'the description'
  - [0].metadata.task = 'text-generation'
  - [0].metadata.category = 'llm'
  - [0].metadata.architecture = 'llama'
  - [0].metadata.framework = ['pytorch']
  - [0].metadata.label = ['chat']
  - [0].metadata.license = 'apache-2.0'
  - [0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - [0].readme = 'the readme'
  - [0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - rejected: NotEnoughPermission

### create

<a id="creating-a-user-granted-create-in-the-project-makes-a-model-card"></a>

#### [a-user-granted-create-in-the-project-makes-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

when a user granted create and read permission on model cards in the project creates a card, a card placed in that project and created by that user comes back with the requested values and minimum resources

Given

- a project holding a vfolder and one user granted CREATE, READ on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Resource slot type cpu: a revision may leave it unfilled
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: CREATE allowed on every model_card
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-1: holds Role card-handler-1

When

- ModelCardAdapter.create: user-1 creates a card with every optional field filled

Then

- a card placed in the project, created by the requesting user, comes back with every value the request filled
  - id: skipped: the database generates it
  - entity_id: same as the id of the answer
  - name = 'llama-card'
  - vfolder_id: same as the requested vfolder
  - domain_name = 'home-1'
  - project_id: same as the requested project
  - creator_id: same as the requesting user
  - metadata.author = 'the model author'
  - metadata.title = 'a new card'
  - metadata.model_version = '1.0'
  - metadata.description = 'a newly registered card'
  - metadata.task = 'text-generation'
  - metadata.category = 'llm'
  - metadata.architecture = 'transformer'
  - metadata.framework = ['pytorch']
  - metadata.label = ['chat']
  - metadata.license = 'apache-2.0'
  - min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - readme = 'the card readme'
  - access_level = <ModelCardAccessLevel.PUBLIC: 'public'>
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-name-taken-in-the-project-is-refused"></a>

#### [a-name-taken-in-the-project-is-refused](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

when a user granted create and read permission on model cards in the project creates a card under the name of a card already in that project, the call is rejected as a name conflict

Given

- a project holding a vfolder and one user granted CREATE, READ on model cards in that project, and one card already placed in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: CREATE allowed on every model_card
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-1: holds Role card-handler-1

When

- ModelCardAdapter.create: user-1 creates a card under the name of the card already there

Then

- the call is rejected
  - rejected: ModelCardConflict

<a id="creating-a-user-granted-only-read-may-not-make-a-model-card"></a>

#### [a-user-granted-only-read-may-not-make-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_creating.py): pass

when a user granted only read permission on model cards in the project tries to create a card, the call is rejected for lack of permission

Given

- a project holding a vfolder and one user granted READ on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Resource slot type cpu: a revision may leave it unfilled
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-1: holds Role card-handler-1

When

- ModelCardAdapter.create: user-1 creates a card with every optional field filled

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get

<a id="getting-a-user-granted-model-card-read-gets-a-card-by-id"></a>

#### [a-user-granted-model-card-read-gets-a-card-by-id](/tests/scenario/bai_scenario/manager/model_card/test_getting.py): pass

when a user granted model card read in the project reads a card by id, the whole card comes back

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.get: user-2 reads the card card-1 by id

Then

- the whole card comes back with its optional fields and minimum resource requirement filled
  - id: same as the card created in advance
  - entity_id: same as the card created in advance
  - name = 'card-1'
  - vfolder_id: same as the vfolder the card is placed on
  - domain_name = 'home-1'
  - project_id: same as the project the card is placed in
  - creator_id: same as the user who created the card
  - metadata.author = 'the-author'
  - metadata.title = 'a card the search finds'
  - metadata.model_version = '1.0'
  - metadata.description = 'the description'
  - metadata.task = 'text-generation'
  - metadata.category = 'llm'
  - metadata.architecture = 'llama'
  - metadata.framework = ['pytorch']
  - metadata.label = ['chat']
  - metadata.license = 'apache-2.0'
  - min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - readme = 'the readme'
  - access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="getting-a-user-without-model-card-read-may-not-get-a-card"></a>

#### [a-user-without-model-card-read-may-not-get-a-card](/tests/scenario/bai_scenario/manager/model_card/test_getting.py): pass

when a user granted only model card update and not read in the project reads a card by id, the call is rejected for lack of permission

Given

- two projects holding model cards and one user granted UPDATE on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.get: user-2 reads the card card-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### min_resources

<a id="min_resources-a-user-granted-model-card-read-reads-the-minimum-resources"></a>

#### [a-user-granted-model-card-read-reads-the-minimum-resources](/tests/scenario/bai_scenario/manager/model_card/test_min_resources.py): pass

when a user granted model card read in the project reads the minimum resource requirements of two cards of that project, the requirement seeded for each card comes back

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.min_resources: user-2 reads the minimum resource requirements of the cards card-1 and card-2

Then

- each requested card comes with the minimum resource requirement seeded
  - length = 2
  - card-1 = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - card-2 = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]

<a id="min_resources-a-card-of-a-project-without-read-refuses-the-whole-call"></a>

#### [a-card-of-a-project-without-read-refuses-the-whole-call](/tests/scenario/bai_scenario/manager/model_card/test_min_resources.py): pass

when a user granted model card read in only one project reads the minimum resource requirements of a card of that project and a card of another project together, the whole call is rejected for lack of permission

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.min_resources: user-2 reads the minimum resource requirements of the card card-1 and the card card-5 of the other project together

Then

- the call is rejected
  - rejected: NotEnoughPermission

### ownership_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-vfolder-ownership"></a>

#### [a-user-granted-model-card-read-finds-cards-by-vfolder-ownership](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page

Given

- two projects holding model cards and one user granted READ on model cards in the first project and vfolder read in it
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1
  - Grant vfolder read permission
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- ModelCardAdapter.ownership_search: user-2 searches the cards using one vfolder owned by the project model-store-1 with a title filter, name descending and a page of two

Then

- only the cards inside the scope that the filter matches come back in the requested order in one page, and the card outside the scope and the card the filter skips are in neither the page nor the count
  - items count = 1
  - items[0].id: same as the card created in advance
  - items[0].entity_id: same as the card created in advance
  - items[0].name = 'card-1'
  - items[0].vfolder_id: same as the vfolder the card is placed on
  - items[0].domain_name = 'home-1'
  - items[0].project_id: same as the project the card is placed in
  - items[0].creator_id: same as the user who created the card
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = 'a card the search finds'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='1')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-vfolder-ownership](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission

Given

- two projects holding model cards and one user granted UPDATE on model cards in the first project and vfolder read in it
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1
  - Grant vfolder read permission
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- ModelCardAdapter.ownership_search: user-2 searches the cards using one vfolder owned by the project model-store-1 with a title filter, name descending and a page of two

Then

- the call is rejected
  - rejected: NotEnoughPermission

### project_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-project"></a>

#### [a-user-granted-model-card-read-finds-cards-by-project](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.project_search: user-2 searches the project model-store-1 with a title filter, name descending and a page of two

Then

- only the cards inside the scope that the filter matches come back in the requested order in one page, and the card outside the scope and the card the filter skips are in neither the page nor the count
  - items count = 2
  - items[0].id: same as the card created in advance
  - items[0].entity_id: same as the card created in advance
  - items[0].name = 'card-3'
  - items[0].vfolder_id: same as the vfolder the card is placed on
  - items[0].domain_name = 'home-1'
  - items[0].project_id: same as the project the card is placed in
  - items[0].creator_id: same as the user who created the card
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = 'a card the search finds'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='3')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the card created in advance
  - items[1].entity_id: same as the card created in advance
  - items[1].name = 'card-2'
  - items[1].vfolder_id: same as the vfolder the card is placed on
  - items[1].domain_name = 'home-1'
  - items[1].project_id: same as the project the card is placed in
  - items[1].creator_id: same as the user who created the card
  - items[1].metadata.author = 'the-author'
  - items[1].metadata.title = 'a card the search finds'
  - items[1].metadata.model_version = '1.0'
  - items[1].metadata.description = 'the description'
  - items[1].metadata.task = 'text-generation'
  - items[1].metadata.category = 'llm'
  - items[1].metadata.architecture = 'llama'
  - items[1].metadata.framework = ['pytorch']
  - items[1].metadata.label = ['chat']
  - items[1].metadata.license = 'apache-2.0'
  - items[1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - items[1].readme = 'the readme'
  - items[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-project"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-project](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission

Given

- two projects holding model cards and one user granted UPDATE on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.project_search: user-2 searches the project model-store-1 with a title filter, name descending and a page of two

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-a-user-granted-model-card-read-finds-cards-by-scope"></a>

#### [a-user-granted-model-card-read-finds-cards-by-scope](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted model card read in the first project searches, only the cards in the scope that the filter matches come back in the requested order and page

Given

- two projects holding model cards and one user granted READ on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.scoped_search: user-2 searches the scope of the project model-store-1 with a title filter, name descending and a page of two

Then

- only the cards inside the scope that the filter matches come back in the requested order in one page, and the card outside the scope and the card the filter skips are in neither the page nor the count
  - items count = 2
  - items[0].id: same as the card created in advance
  - items[0].entity_id: same as the card created in advance
  - items[0].name = 'card-3'
  - items[0].vfolder_id: same as the vfolder the card is placed on
  - items[0].domain_name = 'home-1'
  - items[0].project_id: same as the project the card is placed in
  - items[0].creator_id: same as the user who created the card
  - items[0].metadata.author = 'the-author'
  - items[0].metadata.title = 'a card the search finds'
  - items[0].metadata.model_version = '1.0'
  - items[0].metadata.description = 'the description'
  - items[0].metadata.task = 'text-generation'
  - items[0].metadata.category = 'llm'
  - items[0].metadata.architecture = 'llama'
  - items[0].metadata.framework = ['pytorch']
  - items[0].metadata.label = ['chat']
  - items[0].metadata.license = 'apache-2.0'
  - items[0].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='3')]
  - items[0].readme = 'the readme'
  - items[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the card created in advance
  - items[1].entity_id: same as the card created in advance
  - items[1].name = 'card-2'
  - items[1].vfolder_id: same as the vfolder the card is placed on
  - items[1].domain_name = 'home-1'
  - items[1].project_id: same as the project the card is placed in
  - items[1].creator_id: same as the user who created the card
  - items[1].metadata.author = 'the-author'
  - items[1].metadata.title = 'a card the search finds'
  - items[1].metadata.model_version = '1.0'
  - items[1].metadata.description = 'the description'
  - items[1].metadata.task = 'text-generation'
  - items[1].metadata.category = 'llm'
  - items[1].metadata.architecture = 'llama'
  - items[1].metadata.framework = ['pytorch']
  - items[1].metadata.label = ['chat']
  - items[1].metadata.license = 'apache-2.0'
  - items[1].min_resource = [ResourceSlotEntryInfo(resource_type='cpu', quantity='2')]
  - items[1].readme = 'the readme'
  - items[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-without-model-card-read-may-not-find-cards-by-scope"></a>

#### [a-user-without-model-card-read-may-not-find-cards-by-scope](/tests/scenario/bai_scenario/manager/model_card/test_searching.py): pass

when a user granted only model card update and not read in the first project searches, the call is rejected for lack of permission

Given

- two projects holding model cards and one user granted UPDATE on model cards in the first project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project other-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Model card card-3: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Project vfolder folder-4: is placed in the project and is ready to use
  - Model card card-4: placed in the project and added on top of a vfolder, titled 'a card the search skips', with every optional field filled
  - Project vfolder folder-5: is placed in the project and is ready to use
  - Model card card-5: placed in the project and added on top of a vfolder, titled 'a card the search finds', with every optional field filled
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: requires at least 1 of cpu
  - Model card card-2: requires at least 2 of cpu
  - Model card card-3: requires at least 3 of cpu
  - Model card card-4: requires at least 4 of cpu
  - Model card card-5: requires at least 5 of cpu
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.scoped_search: user-2 searches the scope of the project model-store-1 with a title filter, name descending and a page of two

Then

- the call is rejected
  - rejected: NotEnoughPermission

### deploy

<a id="deploying-a-user-granted-deployment-create-deploys-a-model-card"></a>

#### [a-user-granted-deployment-create-deploys-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_deploying.py): pass

when a user who can read the card and its vfolder and is granted deployment create in the project deploys the card with a preset, a deployment named after the card is created

Given

- a project holding one model card and a preset to deploy it on, and one user who can read the card and its vfolder in that project and is granted CREATE on deployments
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Resource group resource-group-1: uses the fifo scheduler
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: names the image, serves one model 'served', single node, one replica, rolling update
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1
  - Grant deployment permissions
    - Role deployer-1: applies only within the scope it is granted in
    - Role deployer-1: CREATE allowed on every deployment
    - regular user user-2: holds Role deployer-1

When

- ModelCardAdapter.deploy: user-2 deploys card card-1 with preset preset-1 in resource group resource-group-1

Then

- a deployment named after the card is created
  - deployment_id: skipped: the database generates it
  - deployment_name: 'card-1-' followed by eight hex digits

<a id="deploying-a-user-without-deployment-create-may-not-deploy-a-model-card"></a>

#### [a-user-without-deployment-create-may-not-deploy-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_deploying.py): pass

when a user who can read the card and its vfolder in the project but is not granted deployment create tries to deploy the card, the call is rejected for lack of permission

Given

- a project holding one model card and a preset to deploy it on, and one user who can read the card and its vfolder in that project and is granted no deployment permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Resource group resource-group-1: uses the fifo scheduler
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset preset-1: names the image, serves one model 'served', single node, one replica, rolling update
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- ModelCardAdapter.deploy: user-2 deploys card card-1 with preset preset-1 in resource group resource-group-1

Then

- the call is rejected for lack of permission
  - rejected: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-update-edits-several-model-cards"></a>

#### [a-user-granted-update-edits-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py): pass

when a user granted read and update permission on model cards in the project changes the titles of several cards at once, they all come back with the new title and nothing failed

Given

- a project holding 2 model cards and one user granted READ, UPDATE on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.partial_bulk_update: user-2 edits the titles of 2 cards at once

Then

- every target card comes back with the new title and nothing failed
  - successes count = 2
  - successes[0].id: same as the card created in advance
  - successes[0].entity_id: same as the card created in advance
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: same as the vfolder the card is placed on
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: same as the project the card is placed in
  - successes[0].creator_id: same as the user who created the card
  - successes[0].metadata.author = None
  - successes[0].metadata.title = 'the edited title'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the card created in advance
  - successes[1].entity_id: same as the card created in advance
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: same as the vfolder the card is placed on
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: same as the project the card is placed in
  - successes[1].creator_id: same as the user who created the card
  - successes[1].metadata.author = None
  - successes[1].metadata.title = 'the edited title'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

<a id="partial_bulk_editing-a-card-outside-the-granted-project-is-not-edited"></a>

#### [a-card-outside-the-granted-project-is-not-edited](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py): pass

when a user granted read and update permission on model cards in the project edits a card of that project and a card of another project at once, only the card of that project comes back with the new title and the other one comes back in the failed list for lack of permission

Given

- a project holding 1 model cards and one user granted READ, UPDATE on model cards in that project, and 1 card in another project where that user was granted nothing
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project model-store-2
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.partial_bulk_update: user-2 edits the titles of 2 cards at once

Then

- every card the caller may touch comes back in the processed list, and only the card in the other project comes back in the failed list for lack of permission
  - successes count = 1
  - successes[0].id: same as the card created in advance
  - successes[0].entity_id: same as the card created in advance
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: same as the vfolder the card is placed on
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: same as the project the card is placed in
  - successes[0].creator_id: same as the user who created the card
  - successes[0].metadata.author = None
  - successes[0].metadata.title = 'the edited title'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the card in the other project
  - rejected: failed[0].message: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-in-the-project-edits-a-model-card"></a>

#### [a-user-granted-update-in-the-project-edits-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py): pass

when a user granted read and update permission on model cards in the project changes the title of a card, the title takes the new value and the rest stays unchanged

Given

- a project holding 1 model cards and one user granted READ, UPDATE on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - Role card-handler-1: UPDATE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.update: user-2 edits the title of card-1

Then

- the whole card comes back with the title taking the new value and the rest unchanged
  - id: same as the card created in advance
  - entity_id: same as the card created in advance
  - name = 'card-1'
  - vfolder_id: same as the vfolder the card is placed on
  - domain_name = 'home-1'
  - project_id: same as the project the card is placed in
  - creator_id: same as the user who created the card
  - metadata.author = None
  - metadata.title = 'the edited title'
  - metadata.model_version = None
  - metadata.description = None
  - metadata.task = None
  - metadata.category = None
  - metadata.architecture = None
  - metadata.framework = []
  - metadata.label = []
  - metadata.license = None
  - min_resource = None
  - readme = None
  - access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-a-model-card"></a>

#### [a-user-granted-nothing-may-not-edit-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_editing.py): pass

when a user granted nothing tries to update a model card, the call is rejected for lack of permission

Given

- a project holding 1 model cards and one user granted no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'

When

- ModelCardAdapter.update: user-2 edits the title of card-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_bulk_delete

<a id="bulk_deleting-a-user-granted-purge-deletes-several-model-cards"></a>

#### [a-user-granted-purge-deletes-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_bulk_deleting.py): pass

when a user granted purge permission on model cards in the project deletes two cards at once, the ids of both come back in the processed list and nothing failed

Given

- a project holding 2 model cards and one user granted HARD_DELETE on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: HARD_DELETE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.admin_bulk_delete: user-2 deletes 2 cards at once, keeping their vfolders

Then

- the id of every target card comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0]: same as the target card
  - successes[1]: same as the target card
  - failed = []

<a id="bulk_deleting-a-card-outside-the-granted-project-is-not-deleted"></a>

#### [a-card-outside-the-granted-project-is-not-deleted](/tests/scenario/bai_scenario/manager/model_card/test_bulk_deleting.py): pass

when a user granted purge permission on model cards in the project deletes a card of that project and a card of another project at once, only the card of that project comes back in the processed list and the other one comes back in the failed list for lack of permission

Given

- a project holding 1 model cards and one user granted HARD_DELETE on model cards in that project, and 1 card in another project where that user was granted nothing
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project model-store-2
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: HARD_DELETE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.admin_bulk_delete: user-2 deletes 2 cards at once, keeping their vfolders

Then

- the id of the card of that project comes back in the processed list, and only the card in the other project comes back in the failed list for lack of permission
  - successes count = 1
  - successes[0]: same as the target card
  - failed count = 1
  - failed[0].card_id: same as the card in the other project
  - rejected: failed[0].message: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-purge-purges-several-model-cards"></a>

#### [a-user-granted-purge-purges-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

when a user granted purge permission on model cards in the project purges two cards at once, both come back in the processed list and nothing failed

Given

- a project holding 2 model cards and one user granted HARD_DELETE on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: HARD_DELETE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.partial_bulk_purge: user-2 purges 2 cards at once

Then

- every target card comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: same as the card created in advance
  - successes[0].entity_id: same as the card created in advance
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: same as the vfolder the card is placed on
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: same as the project the card is placed in
  - successes[0].creator_id: same as the user who created the card
  - successes[0].metadata.author = None
  - successes[0].metadata.title = 'a card that already existed'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the card created in advance
  - successes[1].entity_id: same as the card created in advance
  - successes[1].name = 'card-2'
  - successes[1].vfolder_id: same as the vfolder the card is placed on
  - successes[1].domain_name = 'home-1'
  - successes[1].project_id: same as the project the card is placed in
  - successes[1].creator_id: same as the user who created the card
  - successes[1].metadata.author = None
  - successes[1].metadata.title = 'a card that already existed'
  - successes[1].metadata.model_version = None
  - successes[1].metadata.description = None
  - successes[1].metadata.task = None
  - successes[1].metadata.category = None
  - successes[1].metadata.architecture = None
  - successes[1].metadata.framework = []
  - successes[1].metadata.label = []
  - successes[1].metadata.license = None
  - successes[1].min_resource = None
  - successes[1].readme = None
  - successes[1].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

<a id="partial_bulk_purging-a-card-outside-the-granted-project-is-not-purged"></a>

#### [a-card-outside-the-granted-project-is-not-purged](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

when a user granted purge permission on model cards in the project purges a card of that project and a card of another project at once, only the card of that project comes back in the processed list and the other one comes back in the failed list for lack of permission

Given

- a project holding 1 model cards and one user granted HARD_DELETE on model cards in that project, and 1 card in another project where that user was granted nothing
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project model-store-2
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: HARD_DELETE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.partial_bulk_purge: user-2 purges 2 cards at once

Then

- every card the caller may touch comes back in the processed list, and only the card in the other project comes back in the failed list for lack of permission
  - successes count = 1
  - successes[0].id: same as the card created in advance
  - successes[0].entity_id: same as the card created in advance
  - successes[0].name = 'card-1'
  - successes[0].vfolder_id: same as the vfolder the card is placed on
  - successes[0].domain_name = 'home-1'
  - successes[0].project_id: same as the project the card is placed in
  - successes[0].creator_id: same as the user who created the card
  - successes[0].metadata.author = None
  - successes[0].metadata.title = 'a card that already existed'
  - successes[0].metadata.model_version = None
  - successes[0].metadata.description = None
  - successes[0].metadata.task = None
  - successes[0].metadata.category = None
  - successes[0].metadata.architecture = None
  - successes[0].metadata.framework = []
  - successes[0].metadata.label = []
  - successes[0].metadata.license = None
  - successes[0].min_resource = None
  - successes[0].readme = None
  - successes[0].access_level = <ModelCardAccessLevel.INTERNAL: 'internal'>
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the card in the other project
  - rejected: failed[0].message: NotEnoughPermission

### purge

<a id="purging-a-user-granted-purge-in-the-project-purges-a-model-card"></a>

#### [a-user-granted-purge-in-the-project-purges-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py): pass

when a user granted purge permission on model cards in the project purges a card, the id of that card comes back

Given

- a project holding 1 model cards and one user granted HARD_DELETE on model cards in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: HARD_DELETE allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.purge: user-2 purges card-1 and leaves the vfolder alone

Then

- the id of the purged card comes back
  - id: same as the card created in advance

<a id="purging-a-user-granted-nothing-may-not-purge-a-model-card"></a>

#### [a-user-granted-nothing-may-not-purge-a-model-card](/tests/scenario/bai_scenario/manager/model_card/test_purging.py): pass

when a user granted nothing tries to purge a model card, the call is rejected for lack of permission

Given

- a project holding 1 model cards and one user granted no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'

When

- ModelCardAdapter.purge: user-2 purges card-1 and leaves the vfolder alone

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scan_project

<a id="scanning-the-superadmin-scans-a-model-store-into-a-card"></a>

#### [the-superadmin-scans-a-model-store-into-a-card](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

when the superadmin scans a model-store project holding one vfolder with a model definition file, one card is created. The global role gates this call, so the superadmin calls it

Given

- a model-store project holding one vfolder whose model definition file names one model, and one superadmin
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1: of type model-store
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - superadmin user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project, is ready to use, and is for model

When

- ModelCardAdapter.scan_project: user-1 scans the vfolders of project model-store-1

Then

- one card is created, none is updated and nothing went wrong
  - created_count = 1
  - updated_count = 0
  - errors = []

<a id="scanning-a-project-that-is-not-a-model-store-is-refused"></a>

#### [a-project-that-is-not-a-model-store-is-refused](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

when the superadmin tries to scan a project that is not a model-store, the call is rejected for the wrong project type

Given

- a general project holding one vfolder whose model definition file names one model, and one superadmin
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1: of type general
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - superadmin user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project and is ready to use

When

- ModelCardAdapter.scan_project: user-1 scans the vfolders of project model-store-1

Then

- the call is rejected
  - rejected: InvalidProjectTypeForModelCard

<a id="scanning-a-regular-user-may-not-scan-a-model-store"></a>

#### [a-regular-user-may-not-scan-a-model-store](/tests/scenario/bai_scenario/manager/model_card/test_scanning.py): pass

when a regular user tries to scan a model-store project, the global role rejects the call

Given

- a model-store project holding one vfolder whose model definition file names one model, and one user
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project model-store-1: of type model-store
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project vfolder folder-1: is placed in the project, is ready to use, and is for model

When

- ModelCardAdapter.scan_project: user-1 scans the vfolders of project model-store-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### available_presets

<a id="available_presets-a-reader-finds-the-presets-meeting-the-card"></a>

#### [a-reader-finds-the-presets-meeting-the-card](/tests/scenario/bai_scenario/manager/model_card/test_available_presets.py): pass

when a user who can read presets and the card looks for the presets the card can be deployed on, filtered and ordered by name, one page at a time, only the presets meeting the minimum resources the card requires are counted, and neither the preset falling short nor the one the filter excludes comes back

Given

- one model card requiring at least 2 cpu, three presets named starting with 'fits' (cpu 4, cpu 2, cpu 1), one cpu 4 preset under another name, and one user who reads presets in public and the card in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Resource slot type cpu: a revision may leave it unfilled
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Model card card-1: requires at least 2 of cpu
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Deployment revision preset fits-1: single node, one replica, rolling update
  - Deployment revision preset fits-1: declares one cpu slot
  - Deployment revision preset fits-2: single node, one replica, rolling update
  - Deployment revision preset fits-2: declares one cpu slot
  - Deployment revision preset fits-3: single node, one replica, rolling update
  - Deployment revision preset fits-3: declares one cpu slot
  - Deployment revision preset other-1: single node, one replica, rolling update
  - Deployment revision preset other-1: declares one cpu slot
  - Prepare a user granted read permission on deployment_preset in public
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-2: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every deployment_preset
    - regular user user-2: holds Role public-reader-1
  - Grant model card permissions
    - Role card-handler-1: applies only within the scope it is granted in
    - Role card-handler-1: READ allowed on every model_card
    - regular user user-2: holds Role card-handler-1

When

- ModelCardAdapter.available_presets: user-2 looks for presets card card-1 can be deployed on, named starting with 'fits', in reverse name order, first one only

Then

- the two presets meeting the requirement under the filtered name are counted, and the first page in reverse name order holds the later-named cpu 2 preset. The preset falling short and the one under another name do not come back
  - items count = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - items[0].id: same as the preset created in advance
  - items[0].entity_id: same as the preset created in advance
  - items[0].runtime_variant_id: same as the runtime variant of the preset
  - items[0].name = 'fits-2'
  - items[0].description = 'a preset created in advance'
  - items[0].rank = 200
  - items[0].cluster.cluster_mode = 'single-node'
  - items[0].cluster.cluster_size = 1
  - items[0].resource.resource_opts = []
  - items[0].execution.image_id: same as the image the preset points at
  - items[0].execution.startup_command = None
  - items[0].execution.bootstrap_script = None
  - items[0].execution.environ = []
  - items[0].deployment_defaults.open_to_public = None
  - items[0].deployment_defaults.replica_count = 1
  - items[0].deployment_defaults.revision_history_limit = None
  - items[0].deployment_defaults.deployment_strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - items[0].deployment_defaults.deployment_strategy_spec = {}
  - items[0].model_definition = None
  - items[0].preset_values = []
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

