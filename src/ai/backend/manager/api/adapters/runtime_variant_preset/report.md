## runtime_variant_preset

[background](/src/ai/backend/manager/api/adapters/runtime_variant_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/runtime_variant_preset/adapter.py)

Scenario: incomplete 2 / 8

- built from ops (6)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - update: success present 5 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when an empty id list is read, an empty response comes back and the lower layer is not called](#reading-an-empty-preset-id-list-answers-empty-without-a-call) | answered |
| [when two existing ids and one unknown id are read together, the items come back in the order asked and the place of the unknown id is empty](#reading-presets-read-by-many-ids-come-back-in-the-order-asked) | answered |
| [when a user without read permission on presets in public reads several by id, the whole read is refused](#reading-a-user-without-read-permission-is-refused-on-batch-read) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates one more preset on a runtime variant that already has one, the new preset's rank is 100 higher](#creating-a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher) | answered |
| [when a preset is created with a slider option added, the UI type is read from the option and carried on the response node](#creating-a-ui-option-given-on-create-carries-its-type-into-the-node) | answered |
| [when target, value type, default and key are all given on creation, the four values come back bound into one spec](#creating-target-value-type-default-and-key-come-back-as-one-spec) | answered |
| [when the superadmin creates a preset on a runtime variant that has none, giving only the required values, the rank is 100, it is not marked required, and the remaining optional values are empty](#creating-the-first-preset-of-a-variant-is-ranked-a-hundred) | answered |
| [because the uniqueness constraint applies to the pair of runtime variant and name, a preset with the same name can be created under another runtime variant](#creating-the-same-preset-name-is-free-in-another-variant) | answered |
| [when a preset with the same name is created again under the same runtime variant, the request is rejected as a duplicate name](#creating-a-preset-name-taken-in-the-same-variant-is-refused) | rejected |
| [when a user who is not the superadmin creates a preset, the request is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset) | rejected |
| [turning the permission check off still does not let a user who is not the superadmin create a preset](#creating-turning-enforcement-off-does-not-let-a-user-create-a-preset) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted nothing reads a preset by id, the whole preset comes back. This read checks authentication only](#reading-a-user-granted-nothing-reads-a-preset-by-id) | answered |
| [when a read names an id that nothing answers to, it is rejected. There is no target to ask for permission on, so the response does not show whether it does not exist or cannot be reached](#reading-reading-a-preset-id-nothing-answers-to-is-refused) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several presets in one call, nothing is purged and every one comes back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets) | answered |
| [when the superadmin purges two presets and one unknown id in one call, the two come back in the processed list as they were before the purge, and the unknown id comes back in the failed list](#partial_bulk_purging-purging-several-presets-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a preset, a response carrying the id of the deleted preset comes back](#retiring-the-superadmin-deletes-a-preset) | answered |
| [turning the permission check off lets even a user granted nothing delete a preset](#retiring-turning-enforcement-off-lets-a-user-delete-a-preset) | answered |
| [when a user granted nothing deletes a preset, the request is rejected for lack of permission](#retiring-a-user-granted-nothing-may-not-delete-a-preset) | rejected |
| [when the superadmin deletes an unknown id, the request is rejected because the target cannot be found](#retiring-deleting-a-preset-id-nothing-answers-to-is-not-found) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when two presets exist and a user granted nothing reads with no filter, both presets come back](#searching-a-user-granted-nothing-counts-every-preset-laid) | answered |
| [when presets are split across two runtime variants and one runtime variant is named in the filter, only the presets of that runtime variant come back](#searching-a-variant-filter-narrows-the-answer-to-that-variants-presets) | answered |
| [when presets with different added and deprecated versions are read with a version filter, only the presets at or above the added version and below the deprecated version come back. An empty side places no limit](#searching-a-version-filter-keeps-only-the-presets-valid-at-that-version) | answered |
| [when eleven presets exist and the page size is omitted, ten come back and the response marks that there is a next page](#searching-omitting-the-page-size-answers-ten-presets-and-a-next-page) | answered |
| [when a user without read permission on presets in public searches, the whole search is refused](#searching-a-user-without-read-permission-is-refused-on-search) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several presets in one call, nothing is updated and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | answered |
| [when the superadmin changes the description of several presets in one call, they all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [when an update gives no value to change, the node comes back with nothing changed](#editing-a-preset-edit-giving-no-value-changes-nothing) | answered |
| [when the description of a preset that has one is cleared, the description is gone](#editing-clearing-a-preset-description-leaves-it-empty) | answered |
| [when the superadmin changes the preset's rank, the node comes back with the changed rank](#editing-editing-a-preset-rank-sets-the-new-rank) | answered |
| [when the superadmin changes only the preset's name, the name takes the new value and the rest stays](#editing-renaming-a-preset-leaves-the-rest-alone) | answered |
| [turning the permission check off lets even a user granted nothing update a preset](#editing-turning-enforcement-off-lets-a-user-edit-a-preset) | answered |
| [when a user granted nothing updates a preset, the request is rejected for lack of permission. A preset belongs to no scope, so at present there is no way to grant that permission](#editing-a-user-granted-nothing-may-not-edit-a-preset) | rejected |
| [when the superadmin updates an unknown id, the request is rejected because the target cannot be found](#editing-the-superadmin-editing-a-preset-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-an-empty-preset-id-list-answers-empty-without-a-call"></a>

#### [an-empty-preset-id-list-answers-empty-without-a-call](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py): pass

when an empty id list is read, an empty response comes back and the lower layer is not called

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty response comes back
  - items = []

<a id="reading-presets-read-by-many-ids-come-back-in-the-order-asked"></a>

#### [presets-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py): pass

when two existing ids and one unknown id are read together, the items come back in the order asked and the place of the unknown id is empty

Given

- 2 presets of one variant and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.batch_load_by_ids: user-1 reads 2 presets seeded in advance together with one unknown id

Then

- items come back in the order asked, and an empty item comes back where the id does not exist
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].runtime_variant_id: same as the identifier of the variant seeded in advance
  - items[0].name = 'preset-1'
  - items[0].description = 'a preset seeded in advance'
  - items[0].rank = 100
  - items[0].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - items[0].required = False
  - items[0].added_version = None
  - items[0].deprecated_version = None
  - items[0].category = None
  - items[0].ui_type = None
  - items[0].display_name = None
  - items[0].ui_option = None
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].runtime_variant_id: same as the identifier of the variant seeded in advance
  - items[1].name = 'preset-2'
  - items[1].description = 'a preset seeded in advance'
  - items[1].rank = 200
  - items[1].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - items[1].required = False
  - items[1].added_version = None
  - items[1].deprecated_version = None
  - items[1].category = None
  - items[1].ui_type = None
  - items[1].display_name = None
  - items[1].ui_option = None
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[2] = None

<a id="reading-a-user-without-read-permission-is-refused-on-batch-read"></a>

#### [a-user-without-read-permission-is-refused-on-batch-read](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py): pass

when a user without read permission on presets in public reads several by id, the whole read is refused

Given

- 2 presets of one variant and one regular user with no permission
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RuntimeVariantPresetAdapter.batch_load_by_ids: user-1 reads 2 presets seeded in advance together with one unknown id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create

<a id="creating-a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher"></a>

#### [a-second-preset-in-the-same-variant-is-ranked-a-hundred-higher](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when the superadmin creates one more preset on a runtime variant that already has one, the new preset's rank is 100 higher

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates one more runtime variant preset named max-tokens under the runtime variant runtime-1

Then

- the whole preset comes back with a rank larger than the existing preset by the set gap
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'max-tokens'
  - description = None
  - rank = 200
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-ui-option-given-on-create-carries-its-type-into-the-node"></a>

#### [a-ui-option-given-on-create-carries-its-type-into-the-node](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when a preset is created with a slider option added, the UI type is read from the option and carried on the response node

Given

- one runtime variant and one superadmin
  - Runtime variant variant-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset max-tokens under the runtime variant variant-1

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = 'slider'
  - display_name = None
  - ui_option = UIOption(ui_type=<UIType.SLIDER: 'slider'>, slider=SliderOption(min=1.0, max=8.0, step=1.0), number=None, choices=None, text=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-target-value-type-default-and-key-come-back-as-one-spec"></a>

#### [target-value-type-default-and-key-come-back-as-one-spec](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when target, value type, default and key are all given on creation, the four values come back bound into one spec

Given

- one runtime variant and one superadmin
  - Runtime variant variant-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset max-tokens under the runtime variant variant-1

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ARGS: 'args'>, value_type=<PresetValueType.INT: 'int'>, default_value='4', key='--workers')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-the-first-preset-of-a-variant-is-ranked-a-hundred"></a>

#### [the-first-preset-of-a-variant-is-ranked-a-hundred](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when the superadmin creates a preset on a runtime variant that has none, giving only the required values, the rank is 100, it is not marked required, and the remaining optional values are empty

Given

- one runtime variant and one superadmin
  - Runtime variant variant-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset max-tokens under the runtime variant variant-1

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'max-tokens'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-the-same-preset-name-is-free-in-another-variant"></a>

#### [the-same-preset-name-is-free-in-another-variant](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

because the uniqueness constraint applies to the pair of runtime variant and name, a preset with the same name can be created under another runtime variant

Given

- two variants, one preset that only one of them holds, and one superadmin
  - Runtime variant taken-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant free-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset preset-1 under the runtime variant free-1

Then

- the whole preset created under the other variant comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'preset-1'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='MAX_TOKENS')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-preset-name-taken-in-the-same-variant-is-refused"></a>

#### [a-preset-name-taken-in-the-same-variant-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when a preset with the same name is created again under the same runtime variant, the request is rejected as a duplicate name

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates one more runtime variant preset named preset-1 under the runtime variant runtime-1

Then

- the call is rejected
  - rejected: RuntimeVariantPresetConflict

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

when a user who is not the superadmin creates a preset, the request is rejected for lack of role

Given

- one runtime variant and one regular user
  - Runtime variant variant-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset max-tokens under the runtime variant variant-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-preset"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_creating.py): pass

turning the permission check off still does not let a user who is not the superadmin create a preset

Given

- one runtime variant and one regular user
  - Runtime variant variant-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.create: user-1 creates the runtime variant preset max-tokens under the runtime variant variant-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-nothing-reads-a-preset-by-id"></a>

#### [a-user-granted-nothing-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py): pass

when a user granted nothing reads a preset by id, the whole preset comes back. This read checks authentication only

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.get: read request from user-1: target: preset-1

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'preset-1'
  - description = 'a preset seeded in advance'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-reading-a-preset-id-nothing-answers-to-is-refused"></a>

#### [reading-a-preset-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_reading.py): pass

when a read names an id that nothing answers to, it is rejected. There is no target to ask for permission on, so the response does not show whether it does not exist or cannot be reached

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.get: read request from user-1: target: an unknown id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several presets in one call, nothing is purged and every one comes back in the failed list for lack of permission

Given

- 2 presets of one variant and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.partial_bulk_purge: user-1 purges 2 presets in one call

Then

- no preset is processed and every preset seeded in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the preset seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the preset seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-presets-answers-for-the-missing-one"></a>

#### [purging-several-presets-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_partial_bulk_purging.py): pass

when the superadmin purges two presets and one unknown id in one call, the two come back in the processed list as they were before the purge, and the unknown id comes back in the failed list

Given

- 2 presets of one variant and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.partial_bulk_purge: user-1 purges 2 presets and one unknown id in one call

Then

- every preset seeded in advance comes back in the processed list, and an unknown id comes back in the failed list
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].runtime_variant_id: same as the identifier of the variant seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].description = 'a preset seeded in advance'
  - successes[0].rank = 100
  - successes[0].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - successes[0].required = False
  - successes[0].added_version = None
  - successes[0].deprecated_version = None
  - successes[0].category = None
  - successes[0].ui_type = None
  - successes[0].display_name = None
  - successes[0].ui_option = None
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].runtime_variant_id: same as the identifier of the variant seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].description = 'a preset seeded in advance'
  - successes[1].rank = 200
  - successes[1].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - successes[1].required = False
  - successes[1].added_version = None
  - successes[1].deprecated_version = None
  - successes[1].category = None
  - successes[1].ui_type = None
  - successes[1].display_name = None
  - successes[1].ui_option = None
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: skipped: the reason comes as a string, and the string is a value that may change

### purge

<a id="retiring-the-superadmin-deletes-a-preset"></a>

#### [the-superadmin-deletes-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py): pass

when the superadmin deletes a preset, a response carrying the id of the deleted preset comes back

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.purge: delete request from user-1: target: preset-1

Then

- the id of the preset deleted comes back
  - id: same as the identifier of the preset seeded in advance

<a id="retiring-turning-enforcement-off-lets-a-user-delete-a-preset"></a>

#### [turning-enforcement-off-lets-a-user-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py): pass

turning the permission check off lets even a user granted nothing delete a preset

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.purge: delete request from user-1: target: preset-1

Then

- the id of the preset deleted comes back
  - id: same as the identifier of the preset seeded in advance

<a id="retiring-a-user-granted-nothing-may-not-delete-a-preset"></a>

#### [a-user-granted-nothing-may-not-delete-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py): pass

when a user granted nothing deletes a preset, the request is rejected for lack of permission

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.purge: delete request from user-1: target: preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-deleting-a-preset-id-nothing-answers-to-is-not-found"></a>

#### [deleting-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_retiring.py): pass

when the superadmin deletes an unknown id, the request is rejected because the target cannot be found

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.purge: delete request from user-1: target: an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-a-user-granted-nothing-counts-every-preset-laid"></a>

#### [a-user-granted-nothing-counts-every-preset-laid](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py): pass

when two presets exist and a user granted nothing reads with no filter, both presets come back

Given

- 2 presets of one variant and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.search: user-1 reads everything with no filter

Then

- only the presets that belong in the response come back
  - items = ['preset-1', 'preset-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-variant-filter-narrows-the-answer-to-that-variants-presets"></a>

#### [a-variant-filter-narrows-the-answer-to-that-variants-presets](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py): pass

when presets are split across two runtime variants and one runtime variant is named in the filter, only the presets of that runtime variant come back

Given

- three presets split across two variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset mine-1: target env, value type str
  - Runtime variant preset mine-2: target env, value type str
  - Runtime variant preset elsewhere-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.search: user-1 reads with the runtime variant filter: target: wanted-1

Then

- only the presets that belong in the response come back
  - items = ['mine-1', 'mine-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-version-filter-keeps-only-the-presets-valid-at-that-version"></a>

#### [a-version-filter-keeps-only-the-presets-valid-at-that-version](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py): pass

when presets with different added and deprecated versions are read with a version filter, only the presets at or above the added version and below the deprecated version come back. An empty side places no limit

Given

- five presets with different added and deprecated versions and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset open-1: target env, value type str, version from 1.0.0 to the last
  - Runtime variant preset unbounded-1: target env, value type str
  - Runtime variant preset closed-1: target env, value type str, version from 1.0.0 to 2.0.0
  - Runtime variant preset retired-1: target env, value type str, version from the first to 2.0.0
  - Runtime variant preset upcoming-1: target env, value type str, version from 3.0.0 to the last
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.search: user-1 reads only the presets valid at version 2.5.0

Then

- only the presets that belong in the response come back
  - items = ['open-1', 'unbounded-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-presets-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-presets-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py): pass

when eleven presets exist and the page size is omitted, ten come back and the response marks that there is a next page

Given

- 11 presets of one variant and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Runtime variant preset preset-3: target env, value type str
  - Runtime variant preset preset-4: target env, value type str
  - Runtime variant preset preset-5: target env, value type str
  - Runtime variant preset preset-6: target env, value type str
  - Runtime variant preset preset-7: target env, value type str
  - Runtime variant preset preset-8: target env, value type str
  - Runtime variant preset preset-9: target env, value type str
  - Runtime variant preset preset-10: target env, value type str
  - Runtime variant preset preset-11: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.search: user-1 reads everything with no filter

Then

- the first page of the default size comes back
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-without-read-permission-is-refused-on-search"></a>

#### [a-user-without-read-permission-is-refused-on-search](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_searching.py): pass

when a user without read permission on presets in public searches, the whole search is refused

Given

- 2 presets of one variant and one regular user with no permission
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RuntimeVariantPresetAdapter.search: user-1 reads everything with no filter

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several presets in one call, nothing is updated and every one comes back in the failed list for lack of permission

Given

- 2 presets of one variant and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.partial_bulk_update: user-1 updates the description of 2 presets in one call

Then

- no preset is processed and every preset seeded in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the preset seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the preset seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several presets in one call, they all come back with the new description and nothing failed

Given

- 2 presets of one variant and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Runtime variant preset preset-2: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.partial_bulk_update: user-1 updates the description of 2 presets in one call

Then

- every preset seeded in advance comes back in the processed list, and nothing failed
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].runtime_variant_id: same as the identifier of the variant seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].description = 'the description updated in one call'
  - successes[0].rank = 100
  - successes[0].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - successes[0].required = False
  - successes[0].added_version = None
  - successes[0].deprecated_version = None
  - successes[0].category = None
  - successes[0].ui_type = None
  - successes[0].display_name = None
  - successes[0].ui_option = None
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].runtime_variant_id: same as the identifier of the variant seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].description = 'the description updated in one call'
  - successes[1].rank = 200
  - successes[1].target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - successes[1].required = False
  - successes[1].added_version = None
  - successes[1].deprecated_version = None
  - successes[1].category = None
  - successes[1].ui_type = None
  - successes[1].display_name = None
  - successes[1].ui_option = None
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### update

<a id="editing-a-preset-edit-giving-no-value-changes-nothing"></a>

#### [a-preset-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when an update gives no value to change, the node comes back with nothing changed

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: no field changed

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'preset-1'
  - description = 'a preset seeded in advance'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-clearing-a-preset-description-leaves-it-empty"></a>

#### [clearing-a-preset-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when the description of a preset that has one is cleared, the description is gone

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: description

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'preset-1'
  - description = None
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-editing-a-preset-rank-sets-the-new-rank"></a>

#### [editing-a-preset-rank-sets-the-new-rank](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when the superadmin changes the preset's rank, the node comes back with the changed rank

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: rank

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'preset-1'
  - description = 'a preset seeded in advance'
  - rank = 7
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-renaming-a-preset-leaves-the-rest-alone"></a>

#### [renaming-a-preset-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when the superadmin changes only the preset's name, the name takes the new value and the rest stays

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: name

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'renamed'
  - description = 'a preset seeded in advance'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-preset"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

turning the permission check off lets even a user granted nothing update a preset

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: name

Then

- the whole preset seeded in advance comes back
  - id: skipped: the database generates it
  - runtime_variant_id: same as the identifier of the variant seeded in advance
  - name = 'renamed'
  - description = 'a preset seeded in advance'
  - rank = 100
  - target_spec = PresetTargetSpec(preset_target=<PresetTarget.ENV: 'env'>, value_type=<PresetValueType.STR: 'str'>, default_value=None, key='PRESET_KEY')
  - required = False
  - added_version = None
  - deprecated_version = None
  - category = None
  - ui_type = None
  - display_name = None
  - ui_option = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-a-preset"></a>

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when a user granted nothing updates a preset, the request is rejected for lack of permission. A preset belongs to no scope, so at present there is no way to grant that permission

Given

- one variant, one preset of that variant, and one regular user
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - regular user user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: preset-1, fields changed: name

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-the-superadmin-editing-a-preset-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-preset-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant_preset/test_editing.py): pass

when the superadmin updates an unknown id, the request is rejected because the target cannot be found

Given

- one variant, one preset of that variant, and one superadmin
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant preset preset-1: target env, value type str
  - Domain home-1
  - Prepare a user granted read permission on runtime_variant_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every runtime_variant_preset
    - superadmin user-1: holds Role public-reader-1

When

- RuntimeVariantPresetAdapter.update: update request from user-1: target: an unknown id, fields changed: name

Then

- the call is rejected
  - rejected: RuntimeVariantPresetNotFound

