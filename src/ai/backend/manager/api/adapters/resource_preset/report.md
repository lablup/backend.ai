## resource_preset

[background](/src/ai/backend/manager/api/adapters/resource_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/resource_preset/adapter.py)

Scenario: incomplete 1 / 9

- built from ops (5)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
- direct implementation (4)
  - apply_resource_group: success present 1 · rejection present 1 (membership)
  - create: success present 1 · rejection present 2 (global_scope)
  - purge: success present 1 · rejection present 2 (single_entity)
  - update: success present 2 · rejection present 2 (membership, single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user who can read presets in public batch loads several presets by id, every preset comes back in the order requested](#reading-a-user-reading-presets-reads-several-presets-by-id) | answered |
| [a user granted nothing batch loading presets by id is not rejected as a call, and every item asked carries a denial for not enough permission](#reading-a-user-granted-nothing-batch-loading-presets-is-refused-per-item) | rejected |

**get**

| scenario | verdict |
|---|---|
| [a user granted read in public reading one preset by id gets the whole preset](#reading-a-user-granted-read-in-public-reads-a-preset) | answered |
| [a user granted nothing reading a preset by id is rejected for not enough permission](#reading-a-user-granted-nothing-may-not-read-a-preset) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to purge several presets at once gets none purged and every one in the failed list for not enough permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets) | answered |
| [purging two presets and one unknown id at once answers the two as deleted nodes and the unknown id in the failed list because no target answers to it](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to edit several presets at once gets none edited and every one in the failed list for not enough permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | answered |
| [when the superadmin changes the shared memory of several presets at once, they all come back with the new shared memory and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | answered |
| [editing several presets with the resources of one changed without the intrinsic slots rejects the whole request as invalid input](#partial_bulk_editing-editing-several-with-slots-missing-intrinsic-ones-is-refused) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin narrows presets by their shared name prefix and asks for the first page in descending name order, only the first of the presets holding that prefix comes back, and the preset without it does not. the superadmin role gates this call](#searching-filtering-and-ordering-preset-search-gives-its-first-page) | answered |
| [a user who is not the superadmin searching every preset is rejected for lacking the role](#searching-a-user-who-is-not-the-superadmin-may-not-search-presets) | rejected |

**apply_resource_group**

| scenario | verdict |
|---|---|
| [when a user who can update presets and the public scope itself in public binds a preset to a resource group, the preset comes back naming that group and the rest stays as it was](#applying_resource_group-a-user-granted-update-binds-a-preset-to-a-resource-group) | answered |
| [a user granted nothing binding a preset to a resource group is rejected for not enough permission](#applying_resource_group-a-user-granted-nothing-may-not-bind-a-preset-to-a-resource-group) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a preset bound to a resource group, the whole preset comes back naming that group. the superadmin role gates this call](#creating-the-superadmin-creates-a-preset-bound-to-a-resource-group) | answered |
| [a user who is not the superadmin creating a preset is rejected for lacking the role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset) | rejected |
| [when the superadmin creates a preset with the name another preset already holds, the call is rejected as a duplicate name](#creating-creating-a-preset-name-another-preset-holds-is-refused) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a preset, the id of the deleted preset comes back](#purging-the-superadmin-purges-a-preset) | answered |
| [a user granted nothing trying to purge a preset is rejected for not enough permission](#purging-a-user-granted-nothing-may-not-purge-a-preset) | rejected |
| [when the superadmin tries to purge the preset of an unknown id, the call is rejected as no such target](#purging-purging-an-id-nothing-answers-to-is-not-found) | rejected |

**update**

| scenario | verdict |
|---|---|
| [a user granted update in public renaming a preset gets the preset under the new name](#editing-a-user-granted-update-in-public-renames-a-preset) | answered |
| [when the superadmin renames a preset, the name takes the new value and the rest stays as it was](#editing-the-superadmin-renames-a-preset) | answered |
| [a user granted nothing trying to edit a preset is rejected for not enough permission](#editing-a-user-granted-nothing-may-not-edit-a-preset) | rejected |
| [when the superadmin tries to edit the preset of an unknown id, the call is rejected as no such target](#editing-editing-an-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-a-user-reading-presets-reads-several-presets-by-id"></a>

#### [a-user-reading-presets-reads-several-presets-by-id](/tests/scenario/bai_scenario/manager/resource_preset/test_reading.py): pass

when a user who can read presets in public batch loads several presets by id, every preset comes back in the order requested

Given

- 2 presets and one regular user granted READ in public
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare a user granted the READ permission on resource presets in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-writer-1: applies only within the scope it is granted in
    - Role preset-writer-1: READ allowed on every resource_preset
    - regular user user-1: holds Role preset-writer-1

When

- ResourcePresetAdapter.batch_load_by_ids: user-1 reads several presets by the ids of 2

Then

- every preset comes back in the order requested
  - len(items) = 2
  - items[0].id: same as the id of the preset seeded in advance
  - items[0].entity_id: same as the id of the preset seeded in advance
  - items[0].name = 'preset-1'
  - items[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - items[0].shared_memory = None
  - items[0].resource_group_name = None
  - items[1].id: same as the id of the preset seeded in advance
  - items[1].entity_id: same as the id of the preset seeded in advance
  - items[1].name = 'preset-2'
  - items[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - items[1].shared_memory = None
  - items[1].resource_group_name = None

<a id="reading-a-user-granted-nothing-batch-loading-presets-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-presets-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_preset/test_reading.py): pass

a user granted nothing batch loading presets by id is not rejected as a call, and every item asked carries a denial for not enough permission

Given

- 2 presets and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.batch_load_by_ids: user-1 reads several presets by the ids of 2

Then

- every item asked comes back carrying a denial for not enough permission
  - len(items) = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-in-public-reads-a-preset"></a>

#### [a-user-granted-read-in-public-reads-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_reading.py): pass

a user granted read in public reading one preset by id gets the whole preset

Given

- one preset and one regular user granted READ in public
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare a user granted the READ permission on resource presets in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-writer-1: applies only within the scope it is granted in
    - Role preset-writer-1: READ allowed on every resource_preset
    - regular user user-1: holds Role preset-writer-1

When

- ResourcePresetAdapter.get: user-1 reads the preset of preset-1

Then

- the whole preset seeded in advance comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = None
  - resource_group_name = None

<a id="reading-a-user-granted-nothing-may-not-read-a-preset"></a>

#### [a-user-granted-nothing-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_reading.py): pass

a user granted nothing reading a preset by id is rejected for not enough permission

Given

- one preset and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.get: user-1 reads the preset of preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_purging.py): pass

a user granted nothing trying to purge several presets at once gets none purged and every one in the failed list for not enough permission

Given

- 2 presets and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.partial_bulk_purge: user-1 purges 2 presets at once

Then

- no preset is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target preset
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target preset
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_purging.py): pass

purging two presets and one unknown id at once answers the two as deleted nodes and the unknown id in the failed list because no target answers to it

Given

- 2 presets and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.partial_bulk_purge: user-1 purges 2 presets and one unknown id at once

Then

- every target preset comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[0].shared_memory = None
  - successes[0].resource_group_name = None
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[1].shared_memory = None
  - successes[1].resource_group_name = None
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py): pass

a user granted nothing trying to edit several presets at once gets none edited and every one in the failed list for not enough permission

Given

- 2 presets and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.partial_bulk_update: user-1 changes the shared memory of 2 presets at once

Then

- no preset is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target preset
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target preset
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py): pass

when the superadmin changes the shared memory of several presets at once, they all come back with the new shared memory and nothing failed

Given

- 2 presets and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.partial_bulk_update: user-1 changes the shared memory of 2 presets at once

Then

- every target preset comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[0].shared_memory = BinarySizeInfo(expr='1073741824', display='1g')
  - successes[0].resource_group_name = None
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - successes[1].shared_memory = BinarySizeInfo(expr='1073741824', display='1g')
  - successes[1].resource_group_name = None
  - failed = []

<a id="partial_bulk_editing-editing-several-with-slots-missing-intrinsic-ones-is-refused"></a>

#### [editing-several-with-slots-missing-intrinsic-ones-is-refused](/tests/scenario/bai_scenario/manager/resource_preset/test_partial_bulk_editing.py): pass

editing several presets with the resources of one changed without the intrinsic slots rejects the whole request as invalid input

Given

- 2 presets and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.partial_bulk_update: user-1 edits 2 presets at once, changing the resources of the first without the intrinsic slots

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### search

<a id="searching-filtering-and-ordering-preset-search-gives-its-first-page"></a>

#### [filtering-and-ordering-preset-search-gives-its-first-page](/tests/scenario/bai_scenario/manager/resource_preset/test_searching.py): pass

when the superadmin narrows presets by their shared name prefix and asks for the first page in descending name order, only the first of the presets holding that prefix comes back, and the preset without it does not. the superadmin role gates this call

Given

- 2 presets sharing a name and one preset not sharing it, and one superadmin
  - Resource preset unrelated-1: belongs to public because it is bound to no resource group
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.search: user-1 searches the first page of presets whose name starts with preset, in descending name order

Then

- the presets that pass the filter come back as the first page in descending name order, and the preset the filter excludes does not
  - total_count = 2
  - len(items) = 1
  - has_next_page = True
  - has_previous_page = False
  - items[0].id: same as the id of the preset seeded in advance
  - items[0].entity_id: same as the id of the preset seeded in advance
  - items[0].name = 'preset-2'
  - items[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - items[0].shared_memory = None
  - items[0].resource_group_name = None

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-presets"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-presets](/tests/scenario/bai_scenario/manager/resource_preset/test_searching.py): pass

a user who is not the superadmin searching every preset is rejected for lacking the role

Given

- 2 presets and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.search: user-1 searches every preset without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### apply_resource_group

<a id="applying_resource_group-a-user-granted-update-binds-a-preset-to-a-resource-group"></a>

#### [a-user-granted-update-binds-a-preset-to-a-resource-group](/tests/scenario/bai_scenario/manager/resource_preset/test_applying_resource_group.py): pass

when a user who can update presets and the public scope itself in public binds a preset to a resource group, the preset comes back naming that group and the rest stays as it was

Given

- one preset, one resource group and one regular user granted the UPDATE permission in public and the UPDATE permission on the public scope itself
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource group group-1: uses the fifo scheduler
  - Domain home-1
  - Prepare a user granted the UPDATE permission on resource presets in public and the UPDATE permission on the public scope itself
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-writer-1: applies only within the scope it is granted in
    - Role preset-writer-1: UPDATE allowed on every resource_preset
    - Role preset-writer-1: UPDATE allowed on every global
    - regular user user-1: holds Role preset-writer-1

When

- ResourcePresetAdapter.apply_resource_group: user-1 binds the preset preset-1 to the resource group group-1

Then

- the preset comes back naming that resource group, and the rest stays as it was
  - id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - resource_slots = {'cpu': Decimal('1'), 'mem': Decimal('1073741824')}
  - shared_memory = None
  - resource_group_name = 'group-1'

<a id="applying_resource_group-a-user-granted-nothing-may-not-bind-a-preset-to-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-bind-a-preset-to-a-resource-group](/tests/scenario/bai_scenario/manager/resource_preset/test_applying_resource_group.py): pass

a user granted nothing binding a preset to a resource group is rejected for not enough permission

Given

- one preset, one resource group and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource group group-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.apply_resource_group: user-1 binds the preset preset-1 to the resource group group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-preset-bound-to-a-resource-group"></a>

#### [the-superadmin-creates-a-preset-bound-to-a-resource-group](/tests/scenario/bai_scenario/manager/resource_preset/test_creating.py): pass

when the superadmin creates a preset bound to a resource group, the whole preset comes back naming that group. the superadmin role gates this call

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.create: user-1 creates the preset fresh-preset bound to the resource group group-1

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'fresh-preset'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = BinarySizeInfo(expr='1073741824', display='1g')
  - resource_group_name = 'group-1'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_creating.py): pass

a user who is not the superadmin creating a preset is rejected for lacking the role

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.create: user-1 creates the preset fresh-preset bound to no resource group

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-creating-a-preset-name-another-preset-holds-is-refused"></a>

#### [creating-a-preset-name-another-preset-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_preset/test_creating.py): pass

when the superadmin creates a preset with the name another preset already holds, the call is rejected as a duplicate name

Given

- one preset and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.create: user-1 creates a preset with the name preset-1 that another preset already holds

Then

- the call is rejected
  - rejected: ResourcePresetConflict

### purge

<a id="purging-the-superadmin-purges-a-preset"></a>

#### [the-superadmin-purges-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py): pass

when the superadmin purges a preset, the id of the deleted preset comes back

Given

- one preset and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.purge: user-1 purges preset-1

Then

- the id of the deleted preset comes back
  - id: same as the id of the preset seeded in advance

<a id="purging-a-user-granted-nothing-may-not-purge-a-preset"></a>

#### [a-user-granted-nothing-may-not-purge-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py): pass

a user granted nothing trying to purge a preset is rejected for not enough permission

Given

- one preset and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.purge: user-1 purges preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-purging-an-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_preset/test_purging.py): pass

when the superadmin tries to purge the preset of an unknown id, the call is rejected as no such target

Given

- one preset and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.purge: user-1 purges an unknown id

Then

- the call is rejected
  - rejected: ResourcePresetNotFound

### update

<a id="editing-a-user-granted-update-in-public-renames-a-preset"></a>

#### [a-user-granted-update-in-public-renames-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py): pass

a user granted update in public renaming a preset gets the preset under the new name

Given

- one preset and one regular user granted UPDATE in public
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare a user granted the UPDATE permission on resource presets in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-writer-1: applies only within the scope it is granted in
    - Role preset-writer-1: UPDATE allowed on every resource_preset
    - regular user user-1: holds Role preset-writer-1

When

- ResourcePresetAdapter.update: user-1 renames preset-1

Then

- the whole preset seeded in advance comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'renamed-preset'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = None
  - resource_group_name = None

<a id="editing-the-superadmin-renames-a-preset"></a>

#### [the-superadmin-renames-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py): pass

when the superadmin renames a preset, the name takes the new value and the rest stays as it was

Given

- one preset and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.update: user-1 renames preset-1

Then

- the whole preset seeded in advance comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'renamed-preset'
  - resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - shared_memory = None
  - resource_group_name = None

<a id="editing-a-user-granted-nothing-may-not-edit-a-preset"></a>

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py): pass

a user granted nothing trying to edit a preset is rejected for not enough permission

Given

- one preset and one regular user
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.update: user-1 renames preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-editing-an-id-nothing-answers-to-is-not-found"></a>

#### [editing-an-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_preset/test_editing.py): pass

when the superadmin tries to edit the preset of an unknown id, the call is rejected as no such target

Given

- one preset and one superadmin
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePresetAdapter.update: user-1 renames an unknown id

Then

- the call is rejected
  - rejected: ResourcePresetNotFound

