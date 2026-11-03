## resource_preset

[background](/src/ai/backend/manager/api/adapters/resource_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/resource_preset/adapter.py)

Scenario: incomplete 6 / 9

- built from ops (5)
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (4)
  - apply_resource_group: success absent · rejection absent (membership): SCENARIO-GAP
  - create: success absent · rejection absent (global_scope): SCENARIO-GAP
  - purge: success present 1 · rejection present 2 (single_entity)
  - update: success present 2 · rejection present 2 (membership, single_entity)

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

