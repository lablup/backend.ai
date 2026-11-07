## artifact

[background](/src/ai/backend/manager/api/adapters/artifact/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/artifact/adapter.py)

Scenario: incomplete 9 / 25

- built from ops (9)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_revisions_by_ids: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - get_revision: representative success ✓ · representative rejection ✓
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✓ · representative rejection ✓
  - search_revisions_of_artifact_gql: representative success ✓ · representative rejection ✓
- direct implementation (16)
  - admin_search: success present 1 · rejection present 1 (global_scope)
  - admin_search_gql: success present 1 · rejection present 1 (global_scope)
  - approve_revision: success present 1 · rejection present 2 (single_field)
  - cancel_import: success present 1 · rejection present 1 (single_field)
  - cleanup_revision: success absent · rejection present 2 (single_field): SCENARIO-GAP
  - delegate_import_batch: success absent · rejection present 2 (global_scope): SCENARIO-GAP
  - delegate_scan: success absent · rejection present 1 (global_scope): SCENARIO-GAP
  - delete_artifacts: success present 1 · rejection present 1 (global_scope)
  - get: success present 1 · rejection present 1 (single_entity)
  - import_revision: success absent · rejection present 2 (single_field): SCENARIO-GAP
  - reject_revision: success present 1 · rejection present 1 (single_field)
  - restore_artifacts: success present 1 · rejection present 1 (global_scope)
  - retrieve_models: success absent · rejection present 1 (global_scope): SCENARIO-GAP
  - scan: success absent · rejection present 1 (global_scope): SCENARIO-GAP
  - search_revisions_gql: success present 1 · rejection present 1 (global_scope)
  - update: success present 1 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [loading artifacts with an empty id list calls no lower layer and an empty answer comes back](#reading-an-empty-artifact-id-list-answers-empty) | answered |
| [when the superadmin loads two artifacts made in advance and one id that does not exist at once, every position holds a whole artifact made in advance and the position of the id that does not exist is empty](#reading-loading-many-artifact-ids-keeps-the-positions) | answered |
| [when a user granted nothing loads several artifact ids at once, every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection so whether it exists is not revealed](#reading-a-user-granted-nothing-loading-artifacts-is-refused-on-every-position) | rejected |

**batch_load_revisions_by_ids**

| scenario | verdict |
|---|---|
| [loading revisions with an empty id list calls no lower layer and an empty answer comes back](#reading-an-empty-revision-id-list-answers-empty) | answered |
| [when the superadmin loads two revisions made in advance and one id that does not exist at once, every position holds a whole revision made in advance and the position of the id that does not exist is empty](#reading-loading-many-revision-ids-keeps-the-positions) | answered |
| [when a user granted nothing loads several revision ids at once, every revision the caller may not read comes back with a rejection for lack of permission](#reading-a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes an artifact, the artifact comes back in the deleted state](#deleting-the-superadmin-soft-deletes-an-artifact) | answered |
| [a user granted nothing cannot soft delete an artifact](#deleting-a-user-granted-nothing-may-not-soft-delete-an-artifact) | rejected |

**get_revision**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifacts in global reads a revision by id, the whole revision made in advance comes back](#reading-a-user-granted-read-gets-a-revision) | answered |
| [when a user granted nothing tries to read a revision by id, it is rejected as the artifact holding it not being resolvable](#reading-a-user-granted-nothing-may-not-read-a-revision) | rejected |

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

**search_revisions_of_artifact_gql**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifacts in global searches only the revisions of one artifact, narrowed to the needs-approval status, ordered by version and limited to the first one, one needs-approval revision of that artifact comes back](#revision_searching-searching-one-artifacts-revisions-returns-only-the-ones-it-holds) | answered |
| [when a user granted nothing tries to search the revisions of one artifact, the whole request is rejected because they hold no permission on that artifact](#revision_searching-a-user-granted-nothing-may-not-search-one-artifacts-revisions) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifacts in global searches narrowed to the model type, ordered by name and limited to two, two model artifacts come back in name order](#searching-narrowing-to-the-model-type-leaves-only-model-artifacts) | answered |
| [when a user granted nothing tries to search artifacts, it is rejected for lack of permission because they hold no global role](#searching-a-user-granted-nothing-may-not-search-artifacts) | rejected |

**admin_search_gql**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifacts in global searches narrowed by the GQL type filter, ordered by name and limited to two, two model artifacts come back in name order](#searching_gql-gql-narrowing-to-the-model-type-leaves-only-model-artifacts) | answered |
| [when a user granted nothing tries to search artifacts with GQL filters, it is rejected for lack of permission because they hold no global role](#searching_gql-a-user-granted-nothing-may-not-search-artifacts-with-gql-filters) | rejected |

**approve_revision**

| scenario | verdict |
|---|---|
| [when a revision waiting for approval is approved, the revision comes back in the available state](#revision_transitions-approving-a-revision-waiting-for-approval-makes-it-available) | answered |
| [a revision that is not waiting for approval cannot be approved, and it is rejected as not verified](#revision_transitions-a-revision-not-waiting-for-approval-is-not-approved) | rejected |
| [when a user granted only read permission tries to approve a revision, it is rejected for lack of permission](#revision_transitions-a-user-granted-read-but-not-update-may-not-approve-a-revision) | rejected |

**cancel_import**

| scenario | verdict |
|---|---|
| [when the import of a revision that is being pulled is cancelled, the revision comes back in the scanned state](#revision_transitions-cancelling-a-running-import-puts-the-revision-back-to-scanned) | answered |
| [when a user granted only read permission tries to cancel the import of a revision, it is rejected for lack of permission](#revision_transitions-a-user-granted-read-but-not-update-may-not-cancel-an-import) | rejected |

**cleanup_revision**

| scenario | verdict |
|---|---|
| [when a user granted only read permission tries to clean up a revision, it is rejected for lack of permission](#revision_transitions-a-user-granted-read-but-not-soft-delete-may-not-clean-up-a-revision) | rejected |
| [a revision that has only been scanned cannot be cleaned up, and it is rejected as not ready to be cleaned up](#revision_transitions-cleaning-up-a-scanned-revision-is-refused) | rejected |

**delegate_import_batch**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to delegate an import, it is rejected for lack of permission because they hold no global role](#revision_transitions-a-user-granted-nothing-may-not-delegate-an-import) | rejected |
| [when an import is delegated without reservoir configuration, it is rejected as the server being misconfigured](#revision_transitions-delegating-an-import-without-reservoir-configuration-is-refused) | rejected |

**delegate_scan**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to delegate a scan of the external registries, it is rejected for lack of permission because they hold no global role](#scanning-a-user-granted-nothing-may-not-delegate-a-scan) | rejected |

**delete_artifacts**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes several artifacts by an id list, all come back in the deleted state](#bulk_deleting-the-superadmin-soft-deletes-artifacts-by-ids) | answered |
| [a user who is not the superadmin cannot soft delete several artifacts by an id list, and the role rejects it](#bulk_deleting-a-user-who-is-not-superadmin-may-not-soft-delete-artifacts-by-ids) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted read permission on artifacts in global reads an artifact by id, the whole artifact made in advance comes back](#reading-a-user-granted-read-gets-an-artifact) | answered |
| [when a user granted nothing tries to read an artifact by id, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-get-an-artifact) | rejected |

**import_revision**

| scenario | verdict |
|---|---|
| [when a user granted only read permission tries to import a revision, it is rejected for lack of permission](#revision_transitions-a-user-granted-read-but-not-create-may-not-import-a-revision) | rejected |
| [when a revision is imported without reservoir configuration, it is rejected as the server being misconfigured](#revision_transitions-importing-without-reservoir-configuration-is-refused) | rejected |

**reject_revision**

| scenario | verdict |
|---|---|
| [when an available revision is rejected, the revision comes back in the rejected state. Rejecting does not check the status it starts from](#revision_transitions-rejecting-an-available-revision-makes-it-rejected) | answered |
| [when a user granted only read permission tries to reject a revision, it is rejected for lack of permission](#revision_transitions-a-user-granted-read-but-not-update-may-not-reject-a-revision) | rejected |

**restore_artifacts**

| scenario | verdict |
|---|---|
| [when the superadmin restores several soft-deleted artifacts by an id list, all come back in the live state](#bulk_deleting-the-superadmin-restores-artifacts-by-ids) | answered |
| [a user who is not the superadmin cannot restore artifacts by an id list](#bulk_deleting-a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids) | rejected |

**retrieve_models**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to read model details from the external registry, it is rejected for lack of permission because they hold no global role](#scanning-a-user-granted-nothing-may-not-retrieve-models) | rejected |

**scan**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to scan the external registries, it is rejected for lack of permission because they hold no global role](#scanning-a-user-granted-nothing-may-not-scan-external-registries) | rejected |

**search_revisions_gql**

| scenario | verdict |
|---|---|
| [when the read-only monitor searches narrowed to the needs-approval status, ordered by version and limited to the first one, one needs-approval revision comes back](#revision_searching-filtering-revisions-by-status-leaves-only-that-status) | answered |
| [when a user granted nothing tries to search revisions, it is rejected for lack of permission because they hold no global role](#revision_searching-a-user-granted-nothing-may-not-search-revisions) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin changes the description of an artifact, the artifact comes back holding the new description](#editing-the-superadmin-edits-an-artifact) | answered |
| [a soft-deleted artifact cannot be edited even by the superadmin, and it is rejected as having no target](#editing-a-soft-deleted-artifact-is-not-edited) | rejected |
| [a user granted nothing cannot edit an artifact](#editing-a-user-granted-nothing-may-not-edit-an-artifact) | rejected |

### batch_load_by_ids

<a id="reading-an-empty-artifact-id-list-answers-empty"></a>

#### [an-empty-artifact-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

loading artifacts with an empty id list calls no lower layer and an empty answer comes back

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

- ArtifactAdapter.batch_load_by_ids: user-1 loads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading-loading-many-artifact-ids-keeps-the-positions"></a>

#### [loading-many-artifact-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when the superadmin loads two artifacts made in advance and one id that does not exist at once, every position holds a whole artifact made in advance and the position of the id that does not exist is empty

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

- ArtifactAdapter.batch_load_by_ids: user-1 loads 2 artifacts made in advance and one id that does not exist at once

Then

- every position holds a whole artifact made in advance, and the position of the id that does not exist is empty
  - length = 3
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
  - [1] = None
  - [2].name = 'artifact-2'
  - [2].type = <ArtifactType.MODEL: 'MODEL'>
  - [2].description = 'an artifact that already existed'
  - [2].registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].source_registry_type = <ArtifactRegistryType.HUGGINGFACE: 'huggingface'>
  - [2].availability = <ArtifactAvailability.ALIVE: 'ALIVE'>
  - [2].readonly = False
  - [2].extra = None
  - [2].revisions = []
  - [2].id: same as the id of the artifact made in advance
  - [2].entity_id: same as the id of the artifact made in advance
  - [2].registry_id: same as the registry id of the artifact made in advance
  - [2].source_registry_id: same as the registry id of the artifact made in advance
  - [2].scanned_at: the time this run wrote
  - [2].updated_at: the time this run wrote

<a id="reading-a-user-granted-nothing-loading-artifacts-is-refused-on-every-position"></a>

#### [a-user-granted-nothing-loading-artifacts-is-refused-on-every-position](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted nothing loads several artifact ids at once, every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection so whether it exists is not revealed

Given

- 2 artifacts and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.batch_load_by_ids: user-1 loads 2 artifacts made in advance and one id that does not exist at once

Then

- every position holds a rejection for lack of permission, and the id that does not exist comes back with the same rejection, so whether it exists is not revealed
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_revisions_by_ids

<a id="reading-an-empty-revision-id-list-answers-empty"></a>

#### [an-empty-revision-id-list-answers-empty](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

loading revisions with an empty id list calls no lower layer and an empty answer comes back

Given

- 2 artifacts with 1 revisions each and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1 loads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading-loading-many-revision-ids-keeps-the-positions"></a>

#### [loading-many-revision-ids-keeps-the-positions](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when the superadmin loads two revisions made in advance and one id that does not exist at once, every position holds a whole revision made in advance and the position of the id that does not exist is empty

Given

- 2 artifacts with 1 revisions each and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1 loads two revisions made in advance and one id that does not exist at once

Then

- every position holds a whole revision made in advance, and the position of the id that does not exist is empty
  - length = 3
  - [0].id: same as the id of the revision created in advance
  - [0].field_id: same as the id of the revision created in advance
  - [0].artifact_id: same as the id of the artifact created in advance
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - [0].verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - [0].readme = 'the revision readme'
  - [1] = None
  - [2].id: same as the id of the revision created in advance
  - [2].field_id: same as the id of the revision created in advance
  - [2].artifact_id: same as the id of the artifact created in advance
  - [2].version = '1.0'
  - [2].size = '1024'
  - [2].status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - [2].remote_status = None
  - [2].created_at = None
  - [2].updated_at = None
  - [2].digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - [2].verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - [2].readme = 'the revision readme'

<a id="reading-a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one"></a>

#### [a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted nothing loads several revision ids at once, every revision the caller may not read comes back with a rejection for lack of permission

Given

- 2 artifacts with 1 revisions each and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.batch_load_revisions_by_ids: user-1 loads two revisions made in advance and one id that does not exist at once

Then

- every revision the caller may not read comes back with a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - [1]: skipped: an id naming no revision comes back empty while a revision the caller may not read comes back as a denial, so this position reveals whether the revision exists. It is recorded as a defect candidate rather than pinned as the expected behavior
  - rejected: NotEnoughPermission

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

- one artifact and one user with no permission
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

### get_revision

<a id="reading-a-user-granted-read-gets-a-revision"></a>

#### [a-user-granted-read-gets-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted read permission on artifacts in global reads a revision by id, the whole revision made in advance comes back

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.get_revision: user-1 reads revision 1.0 of artifact-1 by id

Then

- the whole revision created in advance comes back
  - id: same as the id of the revision created in advance
  - field_id: same as the id of the revision created in advance
  - artifact_id: same as the id of the artifact created in advance
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - readme = 'the revision readme'

<a id="reading-a-user-granted-nothing-may-not-read-a-revision"></a>

#### [a-user-granted-nothing-may-not-read-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted nothing tries to read a revision by id, it is rejected as the artifact holding it not being resolvable

Given

- one artifact with 1 revisions and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.get_revision: user-1 reads revision 1.0 of artifact-1 by id

Then

- the call is rejected
  - rejected: GenericBadRequest

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-artifacts"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to soft delete several artifacts at once, nothing is soft deleted and all come back in the failed list because there is no permission

Given

- 2 artifacts and one user with no permission
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

- 2 artifacts and one user with no permission
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

- one artifact and one user with no permission
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

### search_revisions_of_artifact_gql

<a id="revision_searching-searching-one-artifacts-revisions-returns-only-the-ones-it-holds"></a>

#### [searching-one-artifacts-revisions-returns-only-the-ones-it-holds](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

when a user granted read permission on artifacts in global searches only the revisions of one artifact, narrowed to the needs-approval status, ordered by version and limited to the first one, one needs-approval revision of that artifact comes back

Given

- 2 artifacts with 3 revisions each and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-1: revision 2.0
  - Artifact artifact-1: revision 3.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Artifact artifact-2: revision 2.0
  - Artifact artifact-2: revision 3.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.search_revisions_of_artifact_gql: user-1 searches only the revisions artifact-1 holds, narrowed to the needs-approval status, ordered by version and limited to the first one

Then

- only revisions in that status come back, in version order on one page
  - count = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False
  - [0].id: same as the id of the revision created in advance
  - [0].field_id: same as the id of the revision created in advance
  - [0].artifact_id: same as the id of the artifact created in advance
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - [0].verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - [0].readme = 'the revision readme'

<a id="revision_searching-a-user-granted-nothing-may-not-search-one-artifacts-revisions"></a>

#### [a-user-granted-nothing-may-not-search-one-artifacts-revisions](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

when a user granted nothing tries to search the revisions of one artifact, the whole request is rejected because they hold no permission on that artifact

Given

- 2 artifacts with 2 revisions each and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-1: revision 2.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Artifact artifact-2: revision 2.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.search_revisions_of_artifact_gql: user-1 searches only the revisions artifact-1 holds, narrowed to the needs-approval status, ordered by version and limited to the first one

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_search

<a id="searching-narrowing-to-the-model-type-leaves-only-model-artifacts"></a>

#### [narrowing-to-the-model-type-leaves-only-model-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching.py): pass

when a user granted read permission on artifacts in global searches narrowed to the model type, ordered by name and limited to two, two model artifacts come back in name order

Given

- 3 model artifacts and 1 package artifacts, and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-3: a model scanned from a HuggingFace registry
  - Artifact artifact-4: a model scanned from a HuggingFace registry
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.admin_search: user-1 searches narrowed to the model type, ordered by name and limited to two

Then

- only model artifacts come back, in name order on one page
  - count = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
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

<a id="searching-a-user-granted-nothing-may-not-search-artifacts"></a>

#### [a-user-granted-nothing-may-not-search-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching.py): pass

when a user granted nothing tries to search artifacts, it is rejected for lack of permission because they hold no global role

Given

- 2 model artifacts and 1 package artifacts, and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-3: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.admin_search: user-1 searches narrowed to the model type, ordered by name and limited to two

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_gql

<a id="searching_gql-gql-narrowing-to-the-model-type-leaves-only-model-artifacts"></a>

#### [gql-narrowing-to-the-model-type-leaves-only-model-artifacts](/tests/scenario/bai_scenario/manager/artifact/test_searching_gql.py): pass

when a user granted read permission on artifacts in global searches narrowed by the GQL type filter, ordered by name and limited to two, two model artifacts come back in name order

Given

- 3 model artifacts and 1 package artifacts, and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-3: a model scanned from a HuggingFace registry
  - Artifact artifact-4: a model scanned from a HuggingFace registry
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.admin_search_gql: user-1 searches with a GQL filter narrowed to the model type, ordered by name and limited to two

Then

- only model artifacts come back, in name order on one page
  - count = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
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

<a id="searching_gql-a-user-granted-nothing-may-not-search-artifacts-with-gql-filters"></a>

#### [a-user-granted-nothing-may-not-search-artifacts-with-gql-filters](/tests/scenario/bai_scenario/manager/artifact/test_searching_gql.py): pass

when a user granted nothing tries to search artifacts with GQL filters, it is rejected for lack of permission because they hold no global role

Given

- 2 model artifacts and 1 package artifacts, and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-3: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.admin_search_gql: user-1 searches with a GQL filter narrowed to the model type, ordered by name and limited to two

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### approve_revision

<a id="revision_transitions-approving-a-revision-waiting-for-approval-makes-it-available"></a>

#### [approving-a-revision-waiting-for-approval-makes-it-available](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a revision waiting for approval is approved, the revision comes back in the available state

Given

- one artifact with 1 revisions and one user granted READ, UPDATE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: UPDATE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.approve_revision: user-1 approves revision 1.0

Then

- the whole revision created in advance comes back
  - id: same as the id of the revision created in advance
  - field_id: same as the id of the revision created in advance
  - artifact_id: same as the id of the artifact created in advance
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.AVAILABLE: 'AVAILABLE'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - readme = 'the revision readme'

<a id="revision_transitions-a-revision-not-waiting-for-approval-is-not-approved"></a>

#### [a-revision-not-waiting-for-approval-is-not-approved](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

a revision that is not waiting for approval cannot be approved, and it is rejected as not verified

Given

- one artifact with 1 revisions and one user granted READ, UPDATE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: UPDATE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.approve_revision: user-1 approves revision 1.0

Then

- the call is rejected
  - rejected: ArtifactRevisionNotVerified

<a id="revision_transitions-a-user-granted-read-but-not-update-may-not-approve-a-revision"></a>

#### [a-user-granted-read-but-not-update-may-not-approve-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted only read permission tries to approve a revision, it is rejected for lack of permission

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.approve_revision: user-1 approves revision 1.0

Then

- the call is rejected
  - rejected: NotEnoughPermission

### cancel_import

<a id="revision_transitions-cancelling-a-running-import-puts-the-revision-back-to-scanned"></a>

#### [cancelling-a-running-import-puts-the-revision-back-to-scanned](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when the import of a revision that is being pulled is cancelled, the revision comes back in the scanned state

Given

- one artifact with 1 revisions and one user granted READ, UPDATE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: UPDATE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.cancel_import: user-1 cancels the import of revision 1.0

Then

- the whole revision created in advance comes back
  - id: same as the id of the revision created in advance
  - field_id: same as the id of the revision created in advance
  - artifact_id: same as the id of the artifact created in advance
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.SCANNED: 'SCANNED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - readme = 'the revision readme'

<a id="revision_transitions-a-user-granted-read-but-not-update-may-not-cancel-an-import"></a>

#### [a-user-granted-read-but-not-update-may-not-cancel-an-import](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted only read permission tries to cancel the import of a revision, it is rejected for lack of permission

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.cancel_import: user-1 cancels the import of revision 1.0

Then

- the call is rejected
  - rejected: NotEnoughPermission

### cleanup_revision

<a id="revision_transitions-a-user-granted-read-but-not-soft-delete-may-not-clean-up-a-revision"></a>

#### [a-user-granted-read-but-not-soft-delete-may-not-clean-up-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted only read permission tries to clean up a revision, it is rejected for lack of permission

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.cleanup_revision: user-1 cleans up revision 1.0

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="revision_transitions-cleaning-up-a-scanned-revision-is-refused"></a>

#### [cleaning-up-a-scanned-revision-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

a revision that has only been scanned cannot be cleaned up, and it is rejected as not ready to be cleaned up

Given

- one artifact with 1 revisions and one user granted READ, SOFT_DELETE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: SOFT_DELETE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.cleanup_revision: user-1 cleans up revision 1.0

Then

- the call is rejected
  - rejected: ArtifactRevisionDeletionBadRequestError

### delegate_import_batch

<a id="revision_transitions-a-user-granted-nothing-may-not-delegate-an-import"></a>

#### [a-user-granted-nothing-may-not-delegate-an-import](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted nothing tries to delegate an import, it is rejected for lack of permission because they hold no global role

Given

- 2 artifacts with 1 revisions each and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.delegate_import_batch: user-1 delegates the import of two revisions to another registry

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="revision_transitions-delegating-an-import-without-reservoir-configuration-is-refused"></a>

#### [delegating-an-import-without-reservoir-configuration-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when an import is delegated without reservoir configuration, it is rejected as the server being misconfigured

Given

- 2 artifacts with 1 revisions each and one superadmin
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ArtifactAdapter.delegate_import_batch: user-1 delegates the import of two revisions to another registry

Then

- the call is rejected
  - rejected: ServerMisconfiguredError

### delegate_scan

<a id="scanning-a-user-granted-nothing-may-not-delegate-a-scan"></a>

#### [a-user-granted-nothing-may-not-delegate-a-scan](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

when a user granted nothing tries to delegate a scan of the external registries, it is rejected for lack of permission because they hold no global role

Given

- one artifact and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.delegate_scan: user-1 delegates a scan of the external registries with no condition

Then

- the call is rejected
  - rejected: InsufficientPrivilege

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

- 2 artifacts and one user with no permission
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

### get

<a id="reading-a-user-granted-read-gets-an-artifact"></a>

#### [a-user-granted-read-gets-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted read permission on artifacts in global reads an artifact by id, the whole artifact made in advance comes back

Given

- one artifact and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.get: user-1 reads artifact-1 by id

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

<a id="reading-a-user-granted-nothing-may-not-get-an-artifact"></a>

#### [a-user-granted-nothing-may-not-get-an-artifact](/tests/scenario/bai_scenario/manager/artifact/test_reading.py): pass

when a user granted nothing tries to read an artifact by id, it is rejected for lack of permission

Given

- one artifact and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.get: user-1 reads artifact-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### import_revision

<a id="revision_transitions-a-user-granted-read-but-not-create-may-not-import-a-revision"></a>

#### [a-user-granted-read-but-not-create-may-not-import-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted only read permission tries to import a revision, it is rejected for lack of permission

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.import_revision: user-1 imports revision 1.0

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="revision_transitions-importing-without-reservoir-configuration-is-refused"></a>

#### [importing-without-reservoir-configuration-is-refused](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a revision is imported without reservoir configuration, it is rejected as the server being misconfigured

Given

- one artifact with 1 revisions and one user granted READ, CREATE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: CREATE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.import_revision: user-1 imports revision 1.0

Then

- the call is rejected
  - rejected: ServerMisconfiguredError

### reject_revision

<a id="revision_transitions-rejecting-an-available-revision-makes-it-rejected"></a>

#### [rejecting-an-available-revision-makes-it-rejected](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when an available revision is rejected, the revision comes back in the rejected state. Rejecting does not check the status it starts from

Given

- one artifact with 1 revisions and one user granted READ, UPDATE on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - Role artifact-keeper-1: UPDATE allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.reject_revision: user-1 rejects revision 1.0

Then

- the whole revision created in advance comes back
  - id: same as the id of the revision created in advance
  - field_id: same as the id of the revision created in advance
  - artifact_id: same as the id of the artifact created in advance
  - version = '1.0'
  - size = '1024'
  - status = <ArtifactStatus.REJECTED: 'REJECTED'>
  - remote_status = None
  - created_at = None
  - updated_at = None
  - digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - readme = 'the revision readme'

<a id="revision_transitions-a-user-granted-read-but-not-update-may-not-reject-a-revision"></a>

#### [a-user-granted-read-but-not-update-may-not-reject-a-revision](/tests/scenario/bai_scenario/manager/artifact/test_revision_transitions.py): pass

when a user granted only read permission tries to reject a revision, it is rejected for lack of permission

Given

- one artifact with 1 revisions and one user granted READ on artifacts
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Prepare a user granted permission on artifacts in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role artifact-keeper-1: applies only within the scope it is granted in
    - Role artifact-keeper-1: READ allowed on every artifact
    - regular user user-1: holds Role artifact-keeper-1

When

- ArtifactAdapter.reject_revision: user-1 rejects revision 1.0

Then

- the call is rejected
  - rejected: NotEnoughPermission

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

<a id="bulk_deleting-a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids"></a>

#### [a-user-who-is-not-superadmin-may-not-restore-artifacts-by-ids](/tests/scenario/bai_scenario/manager/artifact/test_bulk_deleting.py): pass

a user who is not the superadmin cannot restore artifacts by an id list

Given

- 2 artifacts and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.restore_artifacts: user-1 restores 2 artifacts by an id list

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### retrieve_models

<a id="scanning-a-user-granted-nothing-may-not-retrieve-models"></a>

#### [a-user-granted-nothing-may-not-retrieve-models](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

when a user granted nothing tries to read model details from the external registry, it is rejected for lack of permission because they hold no global role

Given

- one artifact and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.retrieve_models: user-1 reads model details again from the external registry

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### scan

<a id="scanning-a-user-granted-nothing-may-not-scan-external-registries"></a>

#### [a-user-granted-nothing-may-not-scan-external-registries](/tests/scenario/bai_scenario/manager/artifact/test_scanning.py): pass

when a user granted nothing tries to scan the external registries, it is rejected for lack of permission because they hold no global role

Given

- one artifact and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.scan: user-1 scans the external registries with no condition

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_revisions_gql

<a id="revision_searching-filtering-revisions-by-status-leaves-only-that-status"></a>

#### [filtering-revisions-by-status-leaves-only-that-status](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

when the read-only monitor searches narrowed to the needs-approval status, ordered by version and limited to the first one, one needs-approval revision comes back

Given

- 2 artifacts with 3 revisions each and one monitor with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-1: revision 2.0
  - Artifact artifact-1: revision 3.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Artifact artifact-2: revision 2.0
  - Artifact artifact-2: revision 3.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ArtifactAdapter.search_revisions_gql: user-1 searches narrowed to the needs-approval status, ordered by version and limited to the first one

Then

- only revisions in that status come back, in version order on one page
  - count = 1
  - total_count = 4
  - has_next_page = True
  - has_previous_page = False
  - [0].id: same as the id of the revision created in advance
  - [0].field_id: same as the id of the revision created in advance
  - [0].artifact_id: same as the id of the artifact created in advance
  - [0].version = '1.0'
  - [0].size = '1024'
  - [0].status = <ArtifactStatus.NEEDS_APPROVAL: 'NEEDS_APPROVAL'>
  - [0].remote_status = None
  - [0].created_at = None
  - [0].updated_at = None
  - [0].digest: skipped: the adapter does not put the digest on the revision node, so it cannot be stated from the response
  - [0].verification_result: skipped: the adapter does not put the verification result on the revision node, so it cannot be stated from the response
  - [0].readme = 'the revision readme'

<a id="revision_searching-a-user-granted-nothing-may-not-search-revisions"></a>

#### [a-user-granted-nothing-may-not-search-revisions](/tests/scenario/bai_scenario/manager/artifact/test_revision_searching.py): pass

when a user granted nothing tries to search revisions, it is rejected for lack of permission because they hold no global role

Given

- 2 artifacts with 2 revisions each and one user with no permission
  - Domain home-1
  - Artifact artifact-1: a model scanned from a HuggingFace registry
  - Artifact artifact-1: revision 1.0
  - Artifact artifact-1: revision 2.0
  - Artifact artifact-2: a model scanned from a HuggingFace registry
  - Artifact artifact-2: revision 1.0
  - Artifact artifact-2: revision 2.0
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ArtifactAdapter.search_revisions_gql: user-1 searches narrowed to the needs-approval status, ordered by version and limited to the first one

Then

- the call is rejected
  - rejected: InsufficientPrivilege

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

- one artifact and one user with no permission
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

