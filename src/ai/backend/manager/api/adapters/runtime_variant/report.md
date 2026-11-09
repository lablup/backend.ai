## runtime_variant

[background](/src/ai/backend/manager/api/adapters/runtime_variant/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/runtime_variant/adapter.py)

Scenario: incomplete 3 / 10

- built from ops (7)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - resolve_by_name: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (3)
  - bulk_delete: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_purge: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 2 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when an empty id list is given, an empty response comes back. The lower layer is not called](#reading-an-empty-id-list-answers-empty-without-a-call) | answered |
| [when two existing ids and one unknown id are read in one call, the items come back in the order asked and the item for the unknown id is empty](#reading-variants-read-by-many-ids-come-back-in-the-order-asked) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a runtime variant with a name and a description, the node comes back carrying the given values](#creating-a-variant-made-with-a-description-carries-it-back) | answered |
| [when the superadmin creates a runtime variant with only a name, the description is empty, no vfolder config file is read, and the model definition is the default the code sets](#creating-the-superadmin-makes-a-variant-with-a-name-alone) | answered |
| [when a user who is not the superadmin creates a runtime variant, it is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-variant) | rejected |
| [when a runtime variant with the same name already exists and one is created again under that name, it is rejected as a duplicate name](#creating-a-variant-name-already-taken-is-refused) | rejected |
| [turning the permission check off still does not let a user who is not the superadmin create a runtime variant](#creating-turning-enforcement-off-does-not-let-a-user-create-a-variant) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted nothing reads a runtime variant by id, the whole runtime variant comes back. This read checks authentication only](#reading-a-user-granted-nothing-reads-a-variant-by-id) | answered |
| [when a read names an id that nothing answers to, it is rejected. There is no target to ask for permission on, so the response does not show whether it does not exist or cannot be reached](#reading-reading-a-variant-id-nothing-answers-to-is-refused) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several runtime variants in one call, nothing is updated and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-variants) | answered |
| [when the superadmin changes the description of several runtime variants in one call, they all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-variants-at-once) | answered |

**resolve_by_name**

| scenario | verdict |
|---|---|
| [when a user granted nothing resolves a name to an id, the id of that runtime variant comes back](#reading-a-variant-name-resolves-to-its-id-for-any-user) | answered |
| [when a name that nothing answers to is resolved to an id, it is rejected. A permission check follows on the resolved target, so a name that does not exist and a name that cannot be reached are rejected the same way](#reading-resolving-a-variant-name-nothing-answers-to-is-refused) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when one of several runtime variants is named in a filter, only the runtime variant of that name is left in the response](#searching-a-name-filter-narrows-the-answer-to-the-variant-it-names) | answered |
| [when two runtime variants exist and a user granted nothing reads with no filter, both are counted](#searching-a-user-granted-nothing-counts-every-variant-laid) | answered |
| [when eleven runtime variants exist and the read gives no size, ten come back and the response says there is a next page](#searching-omitting-the-page-size-answers-ten-variants-and-a-next-page) | answered |
| [when a user who can read runtime variants reads with a deployment they cannot read as the use filter, it is rejected for lack of permission](#searching-naming-a-deployment-the-caller-cannot-read-is-refused) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when an update gives no value, the node comes back with nothing changed](#editing-an-edit-giving-no-value-changes-nothing) | answered |
| [when a runtime variant that has a description is updated to clear it, the description is gone](#editing-clearing-a-variant-description-leaves-it-empty) | answered |
| [when the superadmin changes only the name of a runtime variant, the name takes the new value and the description stays](#editing-renaming-a-variant-leaves-its-description-alone) | answered |
| [turning the permission check off lets even a user granted nothing update a runtime variant](#editing-turning-enforcement-off-lets-a-user-edit-a-variant) | answered |
| [when a user granted nothing updates an unknown id, it is rejected for lack of permission, not as a missing target. The permission check runs first, and no permission is granted on a row that does not exist](#editing-a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission) | rejected |
| [when a user granted nothing updates a runtime variant, it is rejected for lack of permission. A runtime variant belongs to no scope, so there is no way to grant that permission](#editing-a-user-granted-nothing-may-not-edit-a-variant) | rejected |
| [when one of two runtime variants is renamed to the other's name, it is rejected as a duplicate name. Unlike on creation, the repository's constraint violation propagates as is](#editing-renaming-a-variant-to-a-name-already-taken-is-refused) | rejected |
| [when the superadmin updates an id that nothing answers to, it is rejected because the target cannot be found](#editing-the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found) | rejected |

**bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing deletes two runtime variants in one call, both come back in the failed list and nothing is deleted](#retiring-a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete) | answered |
| [when an unknown id is added behind an existing id in one delete call, the existing one comes back in the deleted list and the unknown id in the failed list](#retiring-an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted) | answered |
| [when the superadmin deletes two runtime variants in one call, both come back in the deleted list and the failed list is empty](#retiring-the-superadmin-deletes-many-variants-at-once) | answered |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several runtime variants in one call, nothing is purged and every one comes back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-variants) | answered |
| [when the superadmin purges two runtime variants and one unknown id in one call, the two come back in the processed list as they were before the purge, and the unknown id comes back in the failed list](#partial_bulk_purging-purging-several-variants-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a runtime variant, a response carrying the id of the deleted runtime variant comes back](#retiring-the-superadmin-deletes-a-variant) | answered |
| [turning the permission check off lets even a user granted nothing delete a runtime variant](#retiring-turning-enforcement-off-lets-a-user-delete-a-variant) | answered |
| [when a user granted nothing deletes a runtime variant, it is rejected for lack of permission](#retiring-a-user-granted-nothing-may-not-delete-a-variant) | rejected |
| [when the superadmin deletes an id that nothing answers to, it is rejected because the target cannot be found](#retiring-deleting-a-variant-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-an-empty-id-list-answers-empty-without-a-call"></a>

#### [an-empty-id-list-answers-empty-without-a-call](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when an empty id list is given, an empty response comes back. The lower layer is not called

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

- RuntimeVariantAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty response comes back
  - items = []

<a id="reading-variants-read-by-many-ids-come-back-in-the-order-asked"></a>

#### [variants-read-by-many-ids-come-back-in-the-order-asked](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when two existing ids and one unknown id are read in one call, the items come back in the order asked and the item for the unknown id is empty

Given

- 2 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.batch_load_by_ids: user-1 reads 2 runtime variants seeded in advance and one unknown id in one call

Then

- items come back in the order asked, and the item for an unknown id carries a rejection
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].name = 'wanted-1'
  - items[0].description = 'a runtime variant seeded in advance'
  - items[0].reads_vfolder_config_files = False
  - items[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].name = 'other-1'
  - items[1].description = 'a runtime variant seeded in advance'
  - items[1].reads_vfolder_config_files = False
  - items[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - rejected: NotEnoughPermission

### create

<a id="creating-a-variant-made-with-a-description-carries-it-back"></a>

#### [a-variant-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

when the superadmin creates a runtime variant with a name and a description, the node comes back carrying the given values

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RuntimeVariantAdapter.create: user-1 creates the runtime variant vllm

Then

- the whole variant just created comes back
  - id: skipped: the database generates it
  - name = 'vllm'
  - description = 'a newly given description'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-the-superadmin-makes-a-variant-with-a-name-alone"></a>

#### [the-superadmin-makes-a-variant-with-a-name-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

when the superadmin creates a runtime variant with only a name, the description is empty, no vfolder config file is read, and the model definition is the default the code sets

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RuntimeVariantAdapter.create: user-1 creates the runtime variant vllm

Then

- the whole variant just created comes back
  - id: skipped: the database generates it
  - name = 'vllm'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-variant"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

when a user who is not the superadmin creates a runtime variant, it is rejected for lack of role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RuntimeVariantAdapter.create: user-1 creates the runtime variant vllm

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-a-variant-name-already-taken-is-refused"></a>

#### [a-variant-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

when a runtime variant with the same name already exists and one is created again under that name, it is rejected as a duplicate name

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

- RuntimeVariantAdapter.create: user-1 creates another runtime variant under the name variant-1 that already exists

Then

- the call is rejected
  - rejected: RuntimeVariantConflict

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-variant"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_creating.py): pass

turning the permission check off still does not let a user who is not the superadmin create a runtime variant

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RuntimeVariantAdapter.create: user-1 creates the runtime variant vllm

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-nothing-reads-a-variant-by-id"></a>

#### [a-user-granted-nothing-reads-a-variant-by-id](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when a user granted nothing reads a runtime variant by id, the whole runtime variant comes back. This read checks authentication only

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

- RuntimeVariantAdapter.get: user-1 reads the runtime variant variant-1

Then

- the whole variant seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'variant-1'
  - description = 'a runtime variant seeded in advance'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-reading-a-variant-id-nothing-answers-to-is-refused"></a>

#### [reading-a-variant-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when a read names an id that nothing answers to, it is rejected. There is no target to ask for permission on, so the response does not show whether it does not exist or cannot be reached

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

- RuntimeVariantAdapter.get: user-1 reads a runtime variant by an unknown id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-variants"></a>

#### [a-user-granted-nothing-edits-none-of-several-variants](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several runtime variants in one call, nothing is updated and every one comes back in the failed list for lack of permission

Given

- 2 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.partial_bulk_update: user-1 updates the description of 2 runtime variants in one call

Then

- no variant is processed and every variant seeded in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the variant seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the variant seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-variants-at-once"></a>

#### [the-superadmin-edits-several-variants-at-once](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several runtime variants in one call, they all come back with the new description and nothing failed

Given

- 2 runtime variants and one superadmin
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.partial_bulk_update: user-1 updates the description of 2 runtime variants in one call

Then

- every variant seeded in advance comes back in the processed list, and nothing failed
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'the description updated in one call'
  - successes[0].reads_vfolder_config_files = False
  - successes[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = 'the description updated in one call'
  - successes[1].reads_vfolder_config_files = False
  - successes[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### resolve_by_name

<a id="reading-a-variant-name-resolves-to-its-id-for-any-user"></a>

#### [a-variant-name-resolves-to-its-id-for-any-user](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when a user granted nothing resolves a name to an id, the id of that runtime variant comes back

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

- RuntimeVariantAdapter.resolve_by_name: user-1 resolves the name variant-1 to an id

Then

- the id of the runtime variant seeded in advance comes back
  - id: same as the runtime variant seeded in advance

<a id="reading-resolving-a-variant-name-nothing-answers-to-is-refused"></a>

#### [resolving-a-variant-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_reading.py): pass

when a name that nothing answers to is resolved to an id, it is rejected. A permission check follows on the resolved target, so a name that does not exist and a name that cannot be reached are rejected the same way

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

- RuntimeVariantAdapter.resolve_by_name: user-1 resolves the name no-such-variant to an id

Then

- the call is rejected
  - rejected: GenericBadRequest

### search

<a id="searching-a-name-filter-narrows-the-answer-to-the-variant-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-variant-it-names](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

when one of several runtime variants is named in a filter, only the runtime variant of that name is left in the response

Given

- 3 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-2: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.search: user-1 reads with the name filter wanted-1

Then

- only the one variant matching the filter comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-counts-every-variant-laid"></a>

#### [a-user-granted-nothing-counts-every-variant-laid](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

when two runtime variants exist and a user granted nothing reads with no filter, both are counted

Given

- 2 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.search: user-1 reads everything with no filter

Then

- every variant seeded in advance is counted
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-variants-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-variants-and-a-next-page](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

when eleven runtime variants exist and the read gives no size, ten come back and the response says there is a next page

Given

- 11 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-2: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-3: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-4: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-5: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-6: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-7: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-8: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-9: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-10: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.search: user-1 reads everything with no filter

Then

- the first page of the default size comes back
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-naming-a-deployment-the-caller-cannot-read-is-refused"></a>

#### [naming-a-deployment-the-caller-cannot-read-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_searching.py): pass

when a user who can read runtime variants reads with a deployment they cannot read as the use filter, it is rejected for lack of permission

Given

- two runtime variants, one deployment of another project, and one user who cannot read that deployment
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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
  - Domain home-2
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-2: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
  - Deployment theirs-1: replica count 1, has no revision yet

When

- RuntimeVariantAdapter.search: user-1 reads with a deployment they cannot read as the use filter

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-an-edit-giving-no-value-changes-nothing"></a>

#### [an-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when an update gives no value, the node comes back with nothing changed

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

- RuntimeVariantAdapter.update: user-1 updates variant-1 without giving a value

Then

- the whole variant seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'variant-1'
  - description = 'a runtime variant seeded in advance'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-clearing-a-variant-description-leaves-it-empty"></a>

#### [clearing-a-variant-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when a runtime variant that has a description is updated to clear it, the description is gone

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

- RuntimeVariantAdapter.update: user-1 updates the description of variant-1

Then

- the whole variant seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'variant-1'
  - description = None
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-renaming-a-variant-leaves-its-description-alone"></a>

#### [renaming-a-variant-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when the superadmin changes only the name of a runtime variant, the name takes the new value and the description stays

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

- RuntimeVariantAdapter.update: user-1 updates the name of variant-1

Then

- the whole variant seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = 'a runtime variant seeded in advance'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-variant"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

turning the permission check off lets even a user granted nothing update a runtime variant

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

- RuntimeVariantAdapter.update: user-1 updates the name of variant-1

Then

- the whole variant seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = 'a runtime variant seeded in advance'
  - reads_vfolder_config_files = False
  - default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when a user granted nothing updates an unknown id, it is rejected for lack of permission, not as a missing target. The permission check runs first, and no permission is granted on a row that does not exist

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

- RuntimeVariantAdapter.update: user-1 updates the name of an unknown id

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-a-user-granted-nothing-may-not-edit-a-variant"></a>

#### [a-user-granted-nothing-may-not-edit-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when a user granted nothing updates a runtime variant, it is rejected for lack of permission. A runtime variant belongs to no scope, so there is no way to grant that permission

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

- RuntimeVariantAdapter.update: user-1 updates the name of variant-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-renaming-a-variant-to-a-name-already-taken-is-refused"></a>

#### [renaming-a-variant-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when one of two runtime variants is renamed to the other's name, it is rejected as a duplicate name. Unlike on creation, the repository's constraint violation propagates as is

Given

- 2 runtime variants and one superadmin
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.update: user-1 renames wanted-1 to other-1

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="editing-the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_editing.py): pass

when the superadmin updates an id that nothing answers to, it is rejected because the target cannot be found

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

- RuntimeVariantAdapter.update: user-1 updates the name of an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### bulk_delete

<a id="retiring-a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete"></a>

#### [a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when a user granted nothing deletes two runtime variants in one call, both come back in the failed list and nothing is deleted

Given

- 2 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.bulk_delete: user-1 deletes 2 runtime variants in one call

Then

- every variant seeded in advance comes back in the failed list, and the deleted list is empty
  - items = []
  - failed[*].id: same as the variants seeded in advance
  - failed[*].message: skipped: the reason comes as a string, and the string is a value that may change
  - deleted_count = 0

<a id="retiring-an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted"></a>

#### [an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when an unknown id is added behind an existing id in one delete call, the existing one comes back in the deleted list and the unknown id in the failed list

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

- RuntimeVariantAdapter.bulk_delete: user-1 deletes variant-1 and one unknown id in one call

Then

- the variant seeded in advance comes back in the deleted list, and an unknown id comes back in the failed list
  - items: same as the variant seeded in advance
  - len(failed) = 1
  - failed[0].id: skipped: the call made an unknown id, so it cannot be known in advance
  - failed[0].message: skipped: the reason comes as a string, and the string is a value that may change
  - deleted_count = 1

<a id="retiring-the-superadmin-deletes-many-variants-at-once"></a>

#### [the-superadmin-deletes-many-variants-at-once](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when the superadmin deletes two runtime variants in one call, both come back in the deleted list and the failed list is empty

Given

- 2 runtime variants and one superadmin
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.bulk_delete: user-1 deletes 2 runtime variants in one call

Then

- every variant seeded in advance comes back in the deleted list, and the failed list is empty
  - items: same as the variants seeded in advance
  - failed = []
  - deleted_count = 2

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-variants"></a>

#### [a-user-granted-nothing-purges-none-of-several-variants](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several runtime variants in one call, nothing is purged and every one comes back in the failed list for lack of permission

Given

- 2 runtime variants and one regular user
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.partial_bulk_purge: user-1 purges 2 runtime variants in one call

Then

- no variant is processed and every variant seeded in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the variant seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the variant seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-variants-answers-for-the-missing-one"></a>

#### [purging-several-variants-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/runtime_variant/test_partial_bulk_purging.py): pass

when the superadmin purges two runtime variants and one unknown id in one call, the two come back in the processed list as they were before the purge, and the unknown id comes back in the failed list

Given

- 2 runtime variants and one superadmin
  - Runtime variant wanted-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Runtime variant other-1: the baseline model definition is empty, and it reads no config file from the model vfolder
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

- RuntimeVariantAdapter.partial_bulk_purge: user-1 purges 2 runtime variants and one unknown id in one call

Then

- every variant seeded in advance comes back in the processed list, and an unknown id comes back in the failed list
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'a runtime variant seeded in advance'
  - successes[0].reads_vfolder_config_files = False
  - successes[0].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = 'a runtime variant seeded in advance'
  - successes[1].reads_vfolder_config_files = False
  - successes[1].default_model_definition = RuntimeVariantModelDefinitionInfo(models=None)
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: skipped: the reason comes as a string, and the string is a value that may change

### purge

<a id="retiring-the-superadmin-deletes-a-variant"></a>

#### [the-superadmin-deletes-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when the superadmin deletes a runtime variant, a response carrying the id of the deleted runtime variant comes back

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

- RuntimeVariantAdapter.purge: user-1 deletes variant-1

Then

- the id of the variant deleted comes back
  - id: same as the variant seeded in advance

<a id="retiring-turning-enforcement-off-lets-a-user-delete-a-variant"></a>

#### [turning-enforcement-off-lets-a-user-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

turning the permission check off lets even a user granted nothing delete a runtime variant

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

- RuntimeVariantAdapter.purge: user-1 deletes variant-1

Then

- the id of the variant deleted comes back
  - id: same as the variant seeded in advance

<a id="retiring-a-user-granted-nothing-may-not-delete-a-variant"></a>

#### [a-user-granted-nothing-may-not-delete-a-variant](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when a user granted nothing deletes a runtime variant, it is rejected for lack of permission

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

- RuntimeVariantAdapter.purge: user-1 deletes variant-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-deleting-a-variant-id-nothing-answers-to-is-not-found"></a>

#### [deleting-a-variant-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/runtime_variant/test_retiring.py): pass

when the superadmin deletes an id that nothing answers to, it is rejected because the target cannot be found

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

- RuntimeVariantAdapter.purge: user-1 deletes an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

