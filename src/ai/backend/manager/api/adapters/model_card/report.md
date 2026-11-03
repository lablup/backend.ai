## model_card

[background](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

Scenario: incomplete 13 / 16

- built from ops (8)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - create: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - min_resources: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - ownership_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - project_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (3)
  - deploy: success absent · rejection absent (scope, single_get_ops): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (atomic_bulk_scoped_search_ops, partial_bulk): SCENARIO-GAP
  - update: success present 1 · rejection present 1 (atomic_bulk_scoped_search_ops, single_entity)
- direct implementation (4)
  - admin_bulk_delete: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_purge: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 1 · rejection present 1 (single_entity)
  - scan_project: success absent · rejection absent (global_scope): SCENARIO-GAP
- no Action (1)
  - available_presets: success absent · rejection absent: SCENARIO-GAP

**admin_search**

| scenario | verdict |
|---|---|
| [with no model card seeded, a superadmin reading every card gets an empty answer](#model_card-a-scenario-that-laid-no-model-card-finds-none) | answered |
| [when a user who is not the superadmin asks to read every model card, the role blocks it](#model_card-a-user-who-is-not-the-superadmin-may-not-search-every-model-card) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several cards at once, nothing is updated and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-model-cards) | answered |
| [when a user granted read and update permission on model cards in the project changes the titles of several cards at once, they all come back with the new title and nothing failed](#partial_bulk_editing-a-user-granted-update-edits-several-model-cards) | answered |

**update**

| scenario | verdict |
|---|---|
| [when a user granted read and update permission on model cards in the project changes the title of a card, the title takes the new value and the rest stays unchanged](#editing-a-user-granted-update-in-the-project-edits-a-model-card) | answered |
| [when a user granted nothing tries to update a model card, the call is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-model-card) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several cards at once, nothing is purged and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-model-cards) | answered |
| [when a user granted purge permission on model cards in the project purges two cards at once, both come back in the processed list and nothing failed](#partial_bulk_purging-a-user-granted-purge-purges-several-model-cards) | answered |
| [when the superadmin purges two cards and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list as not found. The permission check passes the superadmin first, so the unknown id reaches the purge](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted purge permission on model cards in the project purges a card, the id of that card comes back](#purging-a-user-granted-purge-in-the-project-purges-a-model-card) | answered |
| [when a user granted nothing tries to purge a model card, the call is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-a-model-card) | rejected |

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

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-model-cards"></a>

#### [a-user-granted-nothing-edits-none-of-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several cards at once, nothing is updated and all come back in the failed list for lack of permission

Given

- a project holding 2 model cards and one user granted no permission
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

When

- ModelCardAdapter.partial_bulk_update: user-2 edits the titles of 2 cards at once

Then

- no card is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target card
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target card
  - failed[1].message: a reason containing 'Insufficient permission'

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

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-model-cards"></a>

#### [a-user-granted-nothing-purges-none-of-several-model-cards](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several cards at once, nothing is purged and all come back in the failed list for lack of permission

Given

- a project holding 2 model cards and one user granted no permission
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

When

- ModelCardAdapter.partial_bulk_purge: user-2 purges 2 cards at once

Then

- no card is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target card
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target card
  - failed[1].message: a reason containing 'Insufficient permission'

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

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/model_card/test_partial_bulk_purging.py): pass

when the superadmin purges two cards and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list as not found. The permission check passes the superadmin first, so the unknown id reaches the purge

Given

- a project holding 2 model cards and one superadmin granted no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Project model-store-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Model card card-1: placed in the project and added on top of a vfolder, titled 'a card that already existed'
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Model card card-2: placed in the project and added on top of a vfolder, titled 'a card that already existed'

When

- ModelCardAdapter.partial_bulk_purge: user-2 purges 2 cards and one missing id at once

Then

- every target card comes back in the processed list, and the unknown id comes back in the failed list as not found
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
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'No such model card'

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

