## vfolder

[background](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Scenario: incomplete 25 / 30

- built from ops (4)
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - project_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✗: SCENARIO-GAP
- direct implementation (26)
  - batch_load_mount_permissions: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - batch_load_permissions: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - bulk_delete: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - bulk_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - clone: success absent · rejection absent (single_entity): SCENARIO-GAP
  - create: success present 1 · rejection present 1 (scope)
  - create_download_session: success absent · rejection absent (single_entity): SCENARIO-GAP
  - create_in_project: success absent · rejection absent (scope): SCENARIO-GAP
  - create_upload_session: success absent · rejection absent (single_entity): SCENARIO-GAP
  - delete: success absent · rejection absent (single_entity): SCENARIO-GAP
  - delete_files: success absent · rejection absent (single_entity): SCENARIO-GAP
  - deploy: success absent · rejection absent (scope, single_entity): SCENARIO-GAP
  - get: success present 2 · rejection present 2 (single_entity)
  - get_folder_usage: success absent · rejection absent (single_entity): SCENARIO-GAP
  - list_files: success absent · rejection absent (single_entity): SCENARIO-GAP
  - list_mount_policies: success absent · rejection absent (single_entity): SCENARIO-GAP
  - mkdir: success absent · rejection absent (single_entity): SCENARIO-GAP
  - move_file: success absent · rejection absent (single_entity): SCENARIO-GAP
  - partial_bulk_delete: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_restore: success present 1 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - restore: success absent · rejection absent (single_entity): SCENARIO-GAP
  - set_mount_policy: success absent · rejection absent (single_entity): SCENARIO-GAP
  - unset_mount_policy: success absent · rejection absent (single_entity): SCENARIO-GAP
  - update: success present 1 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted nothing gives an empty id list, an empty list comes back without a permission check](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | answered |
| [when a user granted vfolder read in their personal project loads their own vfolder by id, that vfolder comes back](#batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id) | answered |
| [when a user who accepted a read share of someone else's vfolder loads it by id, that vfolder comes back](#batch_loading-an-accepted-share-loads-someone-elses-folder-by-id) | answered |
| [when the superadmin asks for someone else's vfolder and a missing id together, the vfolder comes back as a node and the missing id entry as an empty value](#batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |
| [when a user who can read only their own vfolder asks for their vfolder, someone else's unshared vfolder and a missing id in one call, their vfolder, a rejection and a rejection come back in input order](#batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order) | rejected |
| [when a user granted nothing loads their own vfolder by id, the call succeeds but that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder) | rejected |
| [when a user who was offered someone else's vfolder but did not accept loads it by id, the call succeeds but that entry is rejected for lack of permission](#batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder) | rejected |

**project_search**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read in a project lists the vfolders of that project, the vfolders of that project come back](#reaching-a-user-granted-folder-read-in-a-project-lists-its-folder) | answered |
| [when a user granted nothing tries to list the vfolders of a project, it is rejected for lack of permission](#reaching-a-user-granted-nothing-may-not-list-a-projects-folders) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user who has created no vfolder lists their own vfolders, the answer is empty](#vfolder-a-user-who-has-made-no-folder-lists-none) | answered |

**create**

| scenario | verdict |
|---|---|
| [when a user granted vfolder create in their own scope creates a vfolder, its ownership belongs to that user](#vfolder-a-user-granted-folder-create-makes-one-of-their-own) | answered |
| [when a user granted nothing tries to create a vfolder, it is rejected for lack of permission](#vfolder-a-user-granted-nothing-may-not-make-a-folder) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read in their personal project reads their own vfolder, that vfolder comes back](#reaching-a-user-granted-folder-read-reads-their-own-folder) | answered |
| [when a user who accepted a read share of someone else's vfolder reads it, that vfolder comes back](#reaching-an-accepted-share-reads-someone-elses-folder) | answered |
| [when a user granted nothing tries to read their own vfolder, it is rejected for lack of permission](#reaching-a-user-granted-nothing-may-not-read-their-own-folder) | rejected |
| [when a user who was offered someone else's vfolder but did not accept tries to read it, it is rejected for lack of permission](#reaching-an-unanswered-offer-may-not-read-someone-elses-folder) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete in their personal project soft deletes their two vfolders and someone else's vfolder in one call, their two vfolders come back delete-pending and the other user's vfolder comes back in the failed list for lack of permission](#partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several) | answered |
| [when a user granted nothing tries to soft delete several vfolders in one call, none is soft deleted and all come back in the failed list for lack of permission](#partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete restores their two soft-deleted vfolders in one call, both come back ready for use](#partial_bulk-restoring-several-folders-brings-them-back) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update in their personal project updates their two vfolders and someone else's vfolder in one call, their two vfolders come back updated and the other user's vfolder comes back in the failed list for lack of permission](#partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several) | answered |
| [when a user granted nothing tries to update several vfolders in one call, none is updated and all come back in the failed list for lack of permission](#partial_bulk-a-user-granted-nothing-updates-none-of-several-folders) | answered |

**update**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update in their personal project changes the name and options of their own vfolder, the changed vfolder comes back](#editing-a-user-granted-folder-update-renames-their-folder) | answered |
| [when a user granted nothing tries to change their own vfolder, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-update-their-folder) | rejected |
| [when the user tries to rename it to a name their other vfolder already uses, it is rejected as an invalid value](#editing-renaming-to-a-name-the-owner-already-uses-is-refused) | rejected |

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user granted nothing gives an empty id list, an empty list comes back without a permission check

Given

- a domain that can hold vfolders and one user holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project

When

- VFolderAdapter.batch_load_by_ids: user-1 loads with an empty list

Then

- an empty list comes back
  - loaded = []

<a id="batch_loading-a-user-granted-folder-read-loads-their-own-folder-by-id"></a>

#### [a-user-granted-folder-read-loads-their-own-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user granted vfolder read in their personal project loads their own vfolder by id, that vfolder comes back

Given

- one user with one personal vfolder of their own, who can read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-reader-1

When

- VFolderAdapter.batch_load_by_ids: user-1 loads the folder-1 vfolder by id in one call

Then

- the whole vfolder seeded in advance comes back
  - length = 1
  - [0].id: same as the vfolder seeded in advance
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: same as the vfolder owner
  - [0].ownership.project_id: same as the project the vfolder is placed in
  - [0].ownership.creator_id: same as the user who created the vfolder
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: skipped: the type already fixes the value
  - [0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - [0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - [0].quota: skipped: the storage answers it, so it cannot be stated here
  - [0].metadata.created_at: the time this run wrote

<a id="batch_loading-an-accepted-share-loads-someone-elses-folder-by-id"></a>

#### [an-accepted-share-loads-someone-elses-folder-by-id](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user who accepted a read share of someone else's vfolder loads it by id, that vfolder comes back

Given

- one user offered another user's personal vfolder to read, accepted, and able to read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - vfolder share offer share-1: offered under the READ permission, not answered yet
  - vfolder share offer share-1: the recipient accepts it
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- VFolderAdapter.batch_load_by_ids: user-2 loads the folder-1 vfolder by id in one call

Then

- the whole vfolder seeded in advance comes back
  - length = 1
  - [0].id: same as the vfolder seeded in advance
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: same as the vfolder owner
  - [0].ownership.project_id: same as the project the vfolder is placed in
  - [0].ownership.creator_id: same as the user who created the vfolder
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: skipped: the type already fixes the value
  - [0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - [0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - [0].quota: skipped: the storage answers it, so it cannot be stated here
  - [0].metadata.created_at: the time this run wrote

<a id="batch_loading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when the superadmin asks for someone else's vfolder and a missing id together, the vfolder comes back as a node and the missing id entry as an empty value

Given

- one personal vfolder of another user and one superadmin holding no role
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.batch_load_by_ids: user-2 loads the folder-1 vfolder and a missing id in one call

Then

- the existing vfolder comes back as a node and the missing id entry as an empty value
  - length = 2
  - [0].id: same as the vfolder seeded in advance
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: same as the vfolder owner
  - [0].ownership.project_id: same as the project the vfolder is placed in
  - [0].ownership.creator_id: same as the user who created the vfolder
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: skipped: the type already fixes the value
  - [0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - [0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - [0].quota: skipped: the storage answers it, so it cannot be stated here
  - [0].metadata.created_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"></a>

#### [a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user who can read only their own vfolder asks for their vfolder, someone else's unshared vfolder and a missing id in one call, their vfolder, a rejection and a rejection come back in input order

Given

- one user with one personal vfolder of their own who can read vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-2: is placed in that person's personal project and is ready to use
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-reader-1

When

- VFolderAdapter.batch_load_by_ids: user-1 loads a readable vfolder, an unreadable vfolder and a missing id in that order in one call

Then

- a vfolder or a rejection comes back for each id in input order
  - length = 3
  - [0].id: same as the vfolder seeded in advance
  - [0].host = 'local:volume1'
  - [0].status = 'ready'
  - [0].metadata.name = 'folder-1'
  - [0].metadata.cloneable = False
  - [0].metadata.last_used = None
  - [0].access_control.ownership_type = 'user'
  - [0].ownership.user_id: same as the vfolder owner
  - [0].ownership.project_id: same as the project the vfolder is placed in
  - [0].ownership.creator_id: same as the user who created the vfolder
  - [0].ownership.creator_email = 'user-1@scenario.local'
  - [0].unmanaged_path = None
  - [0].metadata.usage_mode: skipped: the type already fixes the value
  - [0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - [0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - [0].quota: skipped: the storage answers it, so it cannot be stated here
  - [0].metadata.created_at: the time this run wrote
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user granted nothing loads their own vfolder by id, the call succeeds but that entry is rejected for lack of permission

Given

- one user with one personal vfolder of their own, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.batch_load_by_ids: user-1 loads the folder-1 vfolder by id in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

<a id="batch_loading-an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder"></a>

#### [an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_batch_loading.py): pass

when a user who was offered someone else's vfolder but did not accept loads it by id, the call succeeds but that entry is rejected for lack of permission

Given

- one user offered another user's personal vfolder to read, not yet answered, and able to read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - vfolder share offer share-1: offered under the READ permission, not answered yet
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- VFolderAdapter.batch_load_by_ids: user-2 loads the folder-1 vfolder by id in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### project_search

<a id="reaching-a-user-granted-folder-read-in-a-project-lists-its-folder"></a>

#### [a-user-granted-folder-read-in-a-project-lists-its-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user granted vfolder read in a project lists the vfolders of that project, the vfolders of that project come back

Given

- a project with one vfolder and one user who can read vfolders in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-reader-1

When

- VFolderAdapter.project_search: user-1 lists the vfolders of the project the folder-1 vfolder is placed in

Then

- the whole vfolder seeded in advance comes back
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the vfolder seeded in advance
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'group'
  - items[0].ownership.user_id: same as the vfolder owner
  - items[0].ownership.project_id: same as the project the vfolder is placed in
  - items[0].ownership.creator_id: same as the user who created the vfolder
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode: skipped: the type already fixes the value
  - items[0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - items[0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - items[0].quota: skipped: the storage answers it, so it cannot be stated here
  - items[0].metadata.created_at: the time this run wrote

<a id="reaching-a-user-granted-nothing-may-not-list-a-projects-folders"></a>

#### [a-user-granted-nothing-may-not-list-a-projects-folders](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user granted nothing tries to list the vfolders of a project, it is rejected for lack of permission

Given

- a project with one vfolder and one user holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use

When

- VFolderAdapter.project_search: user-1 lists the vfolders of the project the folder-1 vfolder is placed in

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="vfolder-a-user-who-has-made-no-folder-lists-none"></a>

#### [a-user-who-has-made-no-folder-lists-none](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

when a user who has created no vfolder lists their own vfolders, the answer is empty

Given

- a domain that can hold vfolders and one user who can create a vfolder there
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare a user who can create vfolders
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
      - regular user user-1: has their own keypair and personal project
    - Role folder-owner-1: applies only within the scope it is granted in
    - Role folder-owner-1: CREATE allowed on every vfolder
    - Role folder-owner-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-owner-1

When

- VFolderAdapter.scoped_search: user-1 lists their own vfolders

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

### create

<a id="vfolder-a-user-granted-folder-create-makes-one-of-their-own"></a>

#### [a-user-granted-folder-create-makes-one-of-their-own](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

when a user granted vfolder create in their own scope creates a vfolder, its ownership belongs to that user

Given

- a domain that can hold vfolders and one user who can create a vfolder there
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare a user who can create vfolders
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
      - regular user user-1: has their own keypair and personal project
    - Role folder-owner-1: applies only within the scope it is granted in
    - Role folder-owner-1: CREATE allowed on every vfolder
    - Role folder-owner-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-owner-1

When

- VFolderAdapter.create: user-1 creates a vfolder named work

Then

- the whole vfolder just created comes back and its ownership belongs to the creator
  - host = 'local:volume1'
  - metadata.name = 'work'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: same as the creator
  - ownership.project_id: skipped: a personal vfolder belongs to the user's personal project. That id is made when the user is created
  - ownership.creator_id: same as the creator
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - id: skipped: the database generates it
  - status: skipped: a value that moves while the vfolder is being created
  - metadata.usage_mode: skipped: the type already fixes the value
  - metadata.quota_scope_id: skipped: the storage decides it
  - access_control.permission: skipped: there is nothing to check for the creator
  - quota: skipped: the storage answers it, so it cannot be stated here
  - metadata.created_at: the time this run wrote

<a id="vfolder-a-user-granted-nothing-may-not-make-a-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-folder](/tests/scenario/bai_scenario/manager/vfolder/test_vfolder.py): pass

when a user granted nothing tries to create a vfolder, it is rejected for lack of permission

Given

- a domain that can hold vfolders and one user holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project

When

- VFolderAdapter.create: user-1 creates a vfolder named denied

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get

<a id="reaching-a-user-granted-folder-read-reads-their-own-folder"></a>

#### [a-user-granted-folder-read-reads-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user granted vfolder read in their personal project reads their own vfolder, that vfolder comes back

Given

- one user with one personal vfolder of their own, who can read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-reader-1

When

- VFolderAdapter.get: user-1 reads the folder-1 vfolder

Then

- the whole vfolder seeded in advance comes back
  - id: same as the vfolder seeded in advance
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: same as the vfolder owner
  - ownership.project_id: same as the project the vfolder is placed in
  - ownership.creator_id: same as the user who created the vfolder
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: skipped: the type already fixes the value
  - metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - access_control.permission: skipped: it is a mount permission, which this table does not check
  - quota: skipped: the storage answers it, so it cannot be stated here
  - metadata.created_at: the time this run wrote

<a id="reaching-an-accepted-share-reads-someone-elses-folder"></a>

#### [an-accepted-share-reads-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user who accepted a read share of someone else's vfolder reads it, that vfolder comes back

Given

- one user offered another user's personal vfolder to read, accepted, and able to read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - vfolder share offer share-1: offered under the READ permission, not answered yet
  - vfolder share offer share-1: the recipient accepts it
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- VFolderAdapter.get: user-2 reads the folder-1 vfolder

Then

- the whole vfolder seeded in advance comes back
  - id: same as the vfolder seeded in advance
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'folder-1'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'user'
  - ownership.user_id: same as the vfolder owner
  - ownership.project_id: same as the project the vfolder is placed in
  - ownership.creator_id: same as the user who created the vfolder
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode: skipped: the type already fixes the value
  - metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - access_control.permission: skipped: it is a mount permission, which this table does not check
  - quota: skipped: the storage answers it, so it cannot be stated here
  - metadata.created_at: the time this run wrote

<a id="reaching-a-user-granted-nothing-may-not-read-their-own-folder"></a>

#### [a-user-granted-nothing-may-not-read-their-own-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user granted nothing tries to read their own vfolder, it is rejected for lack of permission

Given

- one user with one personal vfolder of their own, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.get: user-1 reads the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reaching-an-unanswered-offer-may-not-read-someone-elses-folder"></a>

#### [an-unanswered-offer-may-not-read-someone-elses-folder](/tests/scenario/bai_scenario/manager/vfolder/test_reaching.py): pass

when a user who was offered someone else's vfolder but did not accept tries to read it, it is rejected for lack of permission

Given

- one user offered another user's personal vfolder to read, not yet answered, and able to read vfolders in their personal project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - vfolder share offer share-1: offered under the READ permission, not answered yet
  - Grant permission to read vfolders
    - Role folder-reader-1: applies only within the scope it is granted in
    - Role folder-reader-1: READ allowed on every vfolder
    - regular user user-2: holds Role folder-reader-1

When

- VFolderAdapter.get: user-2 reads the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several"></a>

#### [a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted vfolder soft delete in their personal project soft deletes their two vfolders and someone else's vfolder in one call, their two vfolders come back delete-pending and the other user's vfolder comes back in the failed list for lack of permission

Given

- one user with two personal vfolders of their own, granted the SOFT_DELETE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.partial_bulk_delete: user-1 soft deletes their two vfolders and someone else's vfolder in one call

Then

- both of their vfolders come back in the delete-pending state and the other user's vfolder comes back in the failed list for lack of permission
  - successes count = 2
  - successes[0].id: same as the vfolder seeded in advance
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'delete-pending'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: same as the vfolder owner
  - successes[0].ownership.project_id: same as the project the vfolder is placed in
  - successes[0].ownership.creator_id: same as the user who created the vfolder
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: skipped: the type already fixes the value
  - successes[0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[0].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'delete-pending'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: same as the vfolder owner
  - successes[1].ownership.project_id: same as the project the vfolder is placed in
  - successes[1].ownership.creator_id: same as the user who created the vfolder
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: skipped: the type already fixes the value
  - successes[1].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[1].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[1].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[1].metadata.created_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the id of the target vfolder
  - failed[0].message: a reason containing 'Insufficient permission'

<a id="partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted nothing tries to soft delete several vfolders in one call, none is soft deleted and all come back in the failed list for lack of permission

Given

- one user with two personal vfolders of their own, holding no permission, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.partial_bulk_delete: user-1 soft deletes their two vfolders and someone else's vfolder in one call

Then

- no vfolder is processed and all three come back in the failed list for lack of permission
  - successes = []
  - failed count = 3
  - failed[0].id: same as the id of the target vfolder
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target vfolder
  - failed[1].message: a reason containing 'Insufficient permission'
  - failed[2].id: same as the id of the target vfolder
  - failed[2].message: a reason containing 'Insufficient permission'

### partial_bulk_restore

<a id="partial_bulk-restoring-several-folders-brings-them-back"></a>

#### [restoring-several-folders-brings-them-back](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted vfolder soft delete restores their two soft-deleted vfolders in one call, both come back ready for use

Given

- one user with two personal vfolders of their own, granted the SOFT_DELETE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.partial_bulk_restore: user-1 soft deletes their two vfolders in one call and then restores them in one call. It answers the restore

Then

- both of their vfolders come back in the ready state and nothing failed
  - successes count = 2
  - successes[0].id: same as the vfolder seeded in advance
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = False
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: same as the vfolder owner
  - successes[0].ownership.project_id: same as the project the vfolder is placed in
  - successes[0].ownership.creator_id: same as the user who created the vfolder
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: skipped: the type already fixes the value
  - successes[0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[0].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = False
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: same as the vfolder owner
  - successes[1].ownership.project_id: same as the project the vfolder is placed in
  - successes[1].ownership.creator_id: same as the user who created the vfolder
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: skipped: the type already fixes the value
  - successes[1].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[1].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[1].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[1].metadata.created_at: the time this run wrote
  - failed = []

### partial_bulk_update

<a id="partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several"></a>

#### [a-user-granted-folder-update-updates-their-folders-of-several](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted vfolder update in their personal project updates their two vfolders and someone else's vfolder in one call, their two vfolders come back updated and the other user's vfolder comes back in the failed list for lack of permission

Given

- one user with two personal vfolders of their own, granted the UPDATE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.partial_bulk_update: user-1 makes their two vfolders and someone else's vfolder cloneable in one call

Then

- both of their vfolders come back cloneable and the other user's vfolder comes back in the failed list for lack of permission
  - successes count = 2
  - successes[0].id: same as the vfolder seeded in advance
  - successes[0].host = 'local:volume1'
  - successes[0].status = 'ready'
  - successes[0].metadata.name = 'first-1'
  - successes[0].metadata.cloneable = True
  - successes[0].metadata.last_used = None
  - successes[0].access_control.ownership_type = 'user'
  - successes[0].ownership.user_id: same as the vfolder owner
  - successes[0].ownership.project_id: same as the project the vfolder is placed in
  - successes[0].ownership.creator_id: same as the user who created the vfolder
  - successes[0].ownership.creator_email = 'user-1@scenario.local'
  - successes[0].unmanaged_path = None
  - successes[0].metadata.usage_mode: skipped: the type already fixes the value
  - successes[0].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[0].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[0].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].host = 'local:volume1'
  - successes[1].status = 'ready'
  - successes[1].metadata.name = 'second-1'
  - successes[1].metadata.cloneable = True
  - successes[1].metadata.last_used = None
  - successes[1].access_control.ownership_type = 'user'
  - successes[1].ownership.user_id: same as the vfolder owner
  - successes[1].ownership.project_id: same as the project the vfolder is placed in
  - successes[1].ownership.creator_id: same as the user who created the vfolder
  - successes[1].ownership.creator_email = 'user-1@scenario.local'
  - successes[1].unmanaged_path = None
  - successes[1].metadata.usage_mode: skipped: the type already fixes the value
  - successes[1].metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - successes[1].access_control.permission: skipped: it is a mount permission, which this table does not check
  - successes[1].quota: skipped: the storage answers it, so it cannot be stated here
  - successes[1].metadata.created_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the id of the target vfolder
  - failed[0].message: a reason containing 'Insufficient permission'

<a id="partial_bulk-a-user-granted-nothing-updates-none-of-several-folders"></a>

#### [a-user-granted-nothing-updates-none-of-several-folders](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted nothing tries to update several vfolders in one call, none is updated and all come back in the failed list for lack of permission

Given

- one user with two personal vfolders of their own, holding no permission, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.partial_bulk_update: user-1 makes their two vfolders and someone else's vfolder cloneable in one call

Then

- no vfolder is processed and all three come back in the failed list for lack of permission
  - successes = []
  - failed count = 3
  - failed[0].id: same as the id of the target vfolder
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target vfolder
  - failed[1].message: a reason containing 'Insufficient permission'
  - failed[2].id: same as the id of the target vfolder
  - failed[2].message: a reason containing 'Insufficient permission'

### update

<a id="editing-a-user-granted-folder-update-renames-their-folder"></a>

#### [a-user-granted-folder-update-renames-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

when a user granted vfolder update in their personal project changes the name and options of their own vfolder, the changed vfolder comes back

Given

- one user with two personal vfolders of their own, granted the UPDATE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.update: user-1 renames their first vfolder to renamed and makes it cloneable

Then

- the first vfolder comes back named renamed and cloneable
  - vfolder.id: same as the vfolder seeded in advance
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'renamed'
  - vfolder.metadata.cloneable = True
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: same as the vfolder owner
  - vfolder.ownership.project_id: same as the project the vfolder is placed in
  - vfolder.ownership.creator_id: same as the user who created the vfolder
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode: skipped: the type already fixes the value
  - vfolder.metadata.quota_scope_id: skipped: it is made from the owner's id, so it differs per run
  - vfolder.access_control.permission: skipped: it is a mount permission, which this table does not check
  - vfolder.quota: skipped: the storage answers it, so it cannot be stated here
  - vfolder.metadata.created_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-update-their-folder"></a>

#### [a-user-granted-nothing-may-not-update-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

when a user granted nothing tries to change their own vfolder, it is rejected for lack of permission

Given

- one user with two personal vfolders of their own, holding no permission, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.update: user-1 renames their first vfolder to renamed and makes it cloneable

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-renaming-to-a-name-the-owner-already-uses-is-refused"></a>

#### [renaming-to-a-name-the-owner-already-uses-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_editing.py): pass

when the user tries to rename it to a name their other vfolder already uses, it is rejected as an invalid value

Given

- one user with two personal vfolders of their own, granted the UPDATE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project and is ready to use
  - Personal vfolder second-1: is placed in that person's personal project and is ready to use
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.update: user-1 renames their first vfolder to the second vfolder's name and makes it cloneable

Then

- the call is rejected
  - rejected: VFolderInvalidParameter

