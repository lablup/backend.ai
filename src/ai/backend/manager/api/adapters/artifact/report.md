## artifact

[background](/src/ai/backend/manager/api/adapters/artifact/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/artifact/adapter.py)

Scenario: incomplete 21 / 25

- built from ops (9)
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_revisions_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✓ · representative rejection ✓
  - get_revision: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✓ · representative rejection ✓
  - search_revisions_of_artifact_gql: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (16)
  - admin_search: success absent · rejection absent (global_scope): SCENARIO-GAP
  - admin_search_gql: success absent · rejection absent (global_scope): SCENARIO-GAP
  - approve_revision: success absent · rejection absent (single_field): SCENARIO-GAP
  - cancel_import: success absent · rejection absent (single_field): SCENARIO-GAP
  - cleanup_revision: success absent · rejection absent (single_field): SCENARIO-GAP
  - delegate_import_batch: success absent · rejection absent (global_scope): SCENARIO-GAP
  - delegate_scan: success absent · rejection absent (global_scope): SCENARIO-GAP
  - delete_artifacts: success present 1 · rejection present 1 (global_scope)
  - get: success absent · rejection absent (single_entity): SCENARIO-GAP
  - import_revision: success absent · rejection absent (single_field): SCENARIO-GAP
  - reject_revision: success absent · rejection absent (single_field): SCENARIO-GAP
  - restore_artifacts: success present 1 · rejection absent (global_scope): SCENARIO-GAP
  - retrieve_models: success absent · rejection absent (global_scope): SCENARIO-GAP
  - scan: success absent · rejection absent (global_scope): SCENARIO-GAP
  - search_revisions_gql: success absent · rejection absent (global_scope): SCENARIO-GAP
  - update: success present 1 · rejection present 2 (single_entity)

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes an artifact, the artifact comes back in the deleted state](#deleting-the-superadmin-soft-deletes-an-artifact) | answered |
| [a user granted nothing cannot soft delete an artifact](#deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several artifacts at once, nothing is soft deleted and all come back in the failed list because there is no permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts) | answered |
| [when two artifacts and one id that does not exist are soft deleted at once, the two come back in the deleted state and the id that does not exist comes back in the failed list because there is no such target](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted artifacts are restored at once, all come back in the live state](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several artifacts at once, nothing is edited and all come back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-artifacts) | answered |
| [when the superadmin changes the description of several artifacts at once, all come back with the new description and none failed](#partial_bulk_editing-the-superadmin-edits-several-artifacts-at-once) | answered |

**restore**

| scenario | verdict |
|---|---|
| [when a soft-deleted artifact is restored, the artifact comes back in the live state](#deleting-restoring-brings-an-artifact-back) | answered |
| [a user granted nothing cannot restore an artifact](#deleting-a-user-granted-nothing-may-not-restore-an-artifact) | rejected |

**delete_artifacts**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes several artifacts by an id list, all come back in the deleted state](#bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids) | answered |
| [a user who is not the superadmin cannot soft delete several artifacts by an id list, and the role rejects it](#bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids) | rejected |

**restore_artifacts**

| scenario | verdict |
|---|---|
| [when the superadmin restores several soft-deleted artifacts by an id list, all come back in the live state](#bulk_deleting-the-superadmin-restores-artifacts-by-ids) | answered |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the description of an artifact, the artifact comes back holding the new description](#editing-the-superadmin-edits-an-artifact) | answered |
| [a soft-deleted artifact cannot be edited even by the superadmin, and it is rejected as having no target](#editing-a-soft-deleted-artifact-is-not-edited) | rejected |
| [a user granted nothing cannot edit an artifact](#editing-a-user-granted-nothing-may-not-edit-an-artifact) | rejected |

### delete

<a id="deleting-the-superadmin-soft-deletes-an-artifact"></a>

#### [the-superadmin-soft-deletes-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

when the superadmin soft deletes an artifact, the artifact comes back in the deleted state

Given

- one artifact and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.delete: user-1 soft deletes artifact-1

Then

- the whole artifact made in advance comes back
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = 'an artifact that already existed'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: same as the id of the artifact made in advance
  - entity_id: same as the id of the artifact made in advance
  - registry_id: same as the registry id of the artifact made in advance
  - source_registry_id: same as the registry id of the artifact made in advance
  - scanned_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact"></a>

#### [a-user-granted-nothing-may-not-soft-delete-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

a user granted nothing cannot soft delete an artifact

Given

- one artifact and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.delete: user-1 soft deletes artifact-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to soft delete several artifacts at once, nothing is soft deleted and all come back in the failed list because there is no permission

Given

- 2 artifacts and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.partial_bulk_delete: user-1 soft deletes 2 artifacts at once

Then

- no artifact is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target artifact
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target artifact
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

when two artifacts and one id that does not exist are soft deleted at once, the two come back in the deleted state and the id that does not exist comes back in the failed list because there is no such target

Given

- 2 artifacts and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.partial_bulk_delete: user-1 soft deletes 2 artifacts and one id that does not exist at once

Then

- every target artifact comes back processed, and the missing id comes back in the failed list with a reason that it does not exist
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = 'an artifact that already existed'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: same as the id of the artifact made in advance
  - successes[0].entity_id: same as the id of the artifact made in advance
  - successes[0].registry_id: same as the registry id of the artifact made in advance
  - successes[0].source_registry_id: same as the registry id of the artifact made in advance
  - successes[0].scanned_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = 'an artifact that already existed'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: same as the id of the artifact made in advance
  - successes[1].entity_id: same as the id of the artifact made in advance
  - successes[1].registry_id: same as the registry id of the artifact made in advance
  - successes[1].source_registry_id: same as the registry id of the artifact made in advance
  - successes[1].scanned_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the nonexistent id sent in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

when several soft-deleted artifacts are restored at once, all come back in the live state

Given

- 2 artifacts and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.partial_bulk_restore: user-1 soft deletes 2 artifacts at once and then restores them at once

Then

- every target artifact comes back processed, and none failed
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = 'an artifact that already existed'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: same as the id of the artifact made in advance
  - successes[0].entity_id: same as the id of the artifact made in advance
  - successes[0].registry_id: same as the registry id of the artifact made in advance
  - successes[0].source_registry_id: same as the registry id of the artifact made in advance
  - successes[0].scanned_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = 'an artifact that already existed'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: same as the id of the artifact made in advance
  - successes[1].entity_id: same as the id of the artifact made in advance
  - successes[1].registry_id: same as the registry id of the artifact made in advance
  - successes[1].source_registry_id: same as the registry id of the artifact made in advance
  - successes[1].scanned_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-edits-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several artifacts at once, nothing is edited and all come back in the failed list because there is no permission

Given

- 2 artifacts and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.partial_bulk_update: user-1 changes the description of 2 artifacts at once

Then

- no artifact is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target artifact
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target artifact
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-artifacts-at-once"></a>

#### [the-superadmin-edits-several-artifacts-at-once](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several artifacts at once, all come back with the new description and none failed

Given

- 2 artifacts and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.partial_bulk_update: user-1 changes the description of 2 artifacts at once

Then

- every target artifact comes back processed, and none failed
  - successes count = 2
  - successes[0].name = 'artifact-1'
  - successes[0].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[0].description = 'the description edited at once'
  - successes[0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[0].readonly = False
  - successes[0].extra = None
  - successes[0].revisions = []
  - successes[0].id: same as the id of the artifact made in advance
  - successes[0].entity_id: same as the id of the artifact made in advance
  - successes[0].registry_id: same as the registry id of the artifact made in advance
  - successes[0].source_registry_id: same as the registry id of the artifact made in advance
  - successes[0].scanned_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].name = 'artifact-2'
  - successes[1].type = <ArtifactType.MODEL: 'MODEL'>
  - successes[1].description = 'the description edited at once'
  - successes[1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - successes[1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - successes[1].readonly = False
  - successes[1].extra = None
  - successes[1].revisions = []
  - successes[1].id: same as the id of the artifact made in advance
  - successes[1].entity_id: same as the id of the artifact made in advance
  - successes[1].registry_id: same as the registry id of the artifact made in advance
  - successes[1].source_registry_id: same as the registry id of the artifact made in advance
  - successes[1].scanned_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### restore

<a id="deleting-restoring-brings-an-artifact-back"></a>

#### [restoring-brings-an-artifact-back](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

when a soft-deleted artifact is restored, the artifact comes back in the live state

Given

- one artifact and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.restore: user-1 soft deletes artifact-1 and then restores it

Then

- the whole artifact made in advance comes back
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = 'an artifact that already existed'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: same as the id of the artifact made in advance
  - entity_id: same as the id of the artifact made in advance
  - registry_id: same as the registry id of the artifact made in advance
  - source_registry_id: same as the registry id of the artifact made in advance
  - scanned_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-restore-an-artifact"></a>

#### [a-user-granted-nothing-may-not-restore-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_deleting.py): pass

a user granted nothing cannot restore an artifact

Given

- one artifact and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.restore: user-1 restores artifact-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### delete_artifacts

<a id="bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids"></a>

#### [the-superadmin-soft-deletes-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

when the superadmin soft deletes several artifacts by an id list, all come back in the deleted state

Given

- 2 artifacts and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.delete_artifacts: user-1 soft deletes 2 artifacts by an id list

Then

- every target artifact comes back in the processed state
  - count = 2
  - [0].name = 'artifact-1'
  - [0].type = <ArtifactType.MODEL: 'MODEL'>
  - [0].description = 'an artifact that already existed'
  - [0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - [0].readonly = False
  - [0].extra = None
  - [0].revisions = []
  - [0].id: same as the id of the artifact made in advance
  - [0].entity_id: same as the id of the artifact made in advance
  - [0].registry_id: same as the registry id of the artifact made in advance
  - [0].source_registry_id: same as the registry id of the artifact made in advance
  - [0].scanned_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1].name = 'artifact-2'
  - [1].type = <ArtifactType.MODEL: 'MODEL'>
  - [1].description = 'an artifact that already existed'
  - [1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].availability = <ArtifactAvailability.DELETED: 'DELETED'>
  - [1].readonly = False
  - [1].extra = None
  - [1].revisions = []
  - [1].id: same as the id of the artifact made in advance
  - [1].entity_id: same as the id of the artifact made in advance
  - [1].registry_id: same as the registry id of the artifact made in advance
  - [1].source_registry_id: same as the registry id of the artifact made in advance
  - [1].scanned_at: the time this run wrote
  - [1].updated_at: the time this run wrote

<a id="bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids"></a>

#### [a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

a user who is not the superadmin cannot soft delete several artifacts by an id list, and the role rejects it

Given

- 2 artifacts and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.delete_artifacts: user-1 soft deletes 2 artifacts by an id list

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### restore_artifacts

<a id="bulk_deleting-the-superadmin-restores-artifacts-by-ids"></a>

#### [the-superadmin-restores-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

when the superadmin restores several soft-deleted artifacts by an id list, all come back in the live state

Given

- 2 artifacts and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.restore_artifacts: user-1 soft deletes 2 artifacts by an id list and then restores them

Then

- every target artifact comes back in the processed state
  - count = 2
  - [0].name = 'artifact-1'
  - [0].type = <ArtifactType.MODEL: 'MODEL'>
  - [0].description = 'an artifact that already existed'
  - [0].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [0].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [0].readonly = False
  - [0].extra = None
  - [0].revisions = []
  - [0].id: same as the id of the artifact made in advance
  - [0].entity_id: same as the id of the artifact made in advance
  - [0].registry_id: same as the registry id of the artifact made in advance
  - [0].source_registry_id: same as the registry id of the artifact made in advance
  - [0].scanned_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1].name = 'artifact-2'
  - [1].type = <ArtifactType.MODEL: 'MODEL'>
  - [1].description = 'an artifact that already existed'
  - [1].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [1].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [1].readonly = False
  - [1].extra = None
  - [1].revisions = []
  - [1].id: same as the id of the artifact made in advance
  - [1].entity_id: same as the id of the artifact made in advance
  - [1].registry_id: same as the registry id of the artifact made in advance
  - [1].source_registry_id: same as the registry id of the artifact made in advance
  - [1].scanned_at: the time this run wrote
  - [1].updated_at: the time this run wrote

### update

<a id="editing-the-superadmin-edits-an-artifact"></a>

#### [the-superadmin-edits-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

when the superadmin changes the description of an artifact, the artifact comes back holding the new description

Given

- one artifact and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.update: user-1 changes the description of artifact-1

Then

- the whole artifact made in advance comes back
  - name = 'artifact-1'
  - type = <ArtifactType.MODEL: 'MODEL'>
  - description = 'the edited description'
  - registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - readonly = False
  - extra = None
  - revisions = []
  - id: same as the id of the artifact made in advance
  - entity_id: same as the id of the artifact made in advance
  - registry_id: same as the registry id of the artifact made in advance
  - source_registry_id: same as the registry id of the artifact made in advance
  - scanned_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-soft-deleted-artifact-is-not-edited"></a>

#### [a-soft-deleted-artifact-is-not-edited](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

a soft-deleted artifact cannot be edited even by the superadmin, and it is rejected as having no target

Given

- one artifact and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.update: user-1 soft deletes artifact-1 and then changes its description

Then

- the call is rejected
  - rejected: ArtifactNotFoundError

<a id="editing-a-user-granted-nothing-may-not-edit-an-artifact"></a>

#### [a-user-granted-nothing-may-not-edit-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_editing.py): pass

a user granted nothing cannot edit an artifact

Given

- one artifact and one user
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.update: user-1 changes the description of artifact-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

