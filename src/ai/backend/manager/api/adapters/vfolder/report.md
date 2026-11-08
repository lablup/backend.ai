## vfolder

[background](/src/ai/backend/manager/api/adapters/vfolder/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/vfolder/adapter.py)

Scenario: incomplete 5 / 30

- built from ops (4)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - project_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- direct implementation (26)
  - batch_load_mount_permissions: success present 1 · rejection present 1 (partial_bulk)
  - batch_load_permissions: success present 1 · rejection present 1 (partial_bulk)
  - bulk_delete: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - bulk_purge: success absent · rejection absent (single_entity): SCENARIO-GAP
  - clone: success present 1 · rejection present 2 (single_entity)
  - create: success present 1 · rejection present 1 (scope)
  - create_download_session: success present 1 · rejection present 1 (single_entity)
  - create_in_project: success present 1 · rejection present 1 (scope)
  - create_upload_session: success present 1 · rejection present 1 (single_entity)
  - delete: success present 1 · rejection present 1 (single_entity)
  - delete_files: success present 1 · rejection present 1 (single_entity)
  - deploy: success present 1 · rejection present 2 (scope, single_entity)
  - get: success present 2 · rejection present 2 (single_entity)
  - get_folder_usage: success present 2 · rejection present 1 (single_entity)
  - list_files: success present 1 · rejection present 1 (single_entity)
  - list_mount_policies: success present 1 · rejection present 1 (single_entity)
  - mkdir: success present 1 · rejection present 1 (single_entity)
  - move_file: success present 1 · rejection present 1 (single_entity)
  - partial_bulk_delete: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_restore: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 1 · rejection present 2 (single_entity)
  - restore: success present 1 · rejection present 1 (single_entity)
  - set_mount_policy: success present 1 · rejection present 2 (single_entity)
  - unset_mount_policy: success present 1 · rejection present 1 (single_entity)
  - update: success present 1 · rejection present 2 (single_entity)

**admin_search**

| scenario | verdict |
|---|---|
| [when a superadmin holding no role searches every vfolder, the vfolder seeded in advance comes back](#searching-a-superadmin-searches-every-folder) | answered |
| [when a regular user tries to search every vfolder, it is rejected for lack of permission](#searching-a-regular-user-may-not-search-every-folder) | rejected |

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
| [when a user granted vfolder read in their own scope searches by a name fragment, ordered by name ascending and limited to one page, one page holding only their two matching vfolders in name order comes back](#searching-a-search-narrows-to-the-matching-folder-in-order-and-page) | answered |
| [when a user who has created no vfolder lists their own vfolders, the answer is empty](#vfolder-a-user-who-has-made-no-folder-lists-none) | answered |
| [when a user granted nothing tries to search the vfolders of their own scope, it is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-search-their-own-scope) | rejected |

**batch_load_mount_permissions**

| scenario | verdict |
|---|---|
| [when the user who can read their own personal vfolder loads the mount level they get, an answer holding the read-write level comes back](#batch_permissions-the-owner-of-a-personal-folder-loads-the-read-write-mount-level) | answered |
| [when a user granted nothing loads the mount level they get, the call succeeds but that entry is rejected for lack of permission](#batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level) | rejected |

**batch_load_permissions**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read loads the permissions they hold, an answer holding only the read permission comes back](#batch_permissions-a-user-granted-folder-read-loads-their-permissions) | answered |
| [when a user granted nothing loads the permissions they hold, the call succeeds but that entry is rejected for lack of permission](#batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-permissions) | rejected |

**clone**

| scenario | verdict |
|---|---|
| [when a user granted clone on a cloneable vfolder of their own clones it under a new name, the cloned vfolder comes back](#cloning-a-user-granted-clone-copies-a-cloneable-folder) | answered |
| [when a user granted nothing tries to clone their own vfolder, it is rejected for lack of permission](#cloning-a-user-granted-nothing-may-not-clone-their-folder) | rejected |
| [when a user tries to clone a vfolder not marked cloneable, it is rejected](#cloning-cloning-a-folder-not-marked-cloneable-is-refused) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted vfolder create in their own scope creates a vfolder, its ownership belongs to that user](#vfolder-a-user-granted-folder-create-makes-one-of-their-own) | answered |
| [when a user granted nothing tries to create a vfolder, it is rejected for lack of permission](#vfolder-a-user-granted-nothing-may-not-make-a-folder) | rejected |

**create_download_session**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read opens a download session for the folder, the token and address to download from come back](#files-a-user-granted-folder-read-opens-a-download-session) | answered |
| [when a user granted nothing tries to open a download session for a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-open-a-download-session) | rejected |

**create_in_project**

| scenario | verdict |
|---|---|
| [when a user granted vfolder create in a project creates a folder owned by that project, the folder belongs to the project](#creating-a-user-granted-folder-create-in-a-project-makes-a-project-folder) | answered |
| [when a user granted nothing tries to create a project-owned vfolder, it is rejected for lack of permission](#creating-a-user-granted-nothing-may-not-make-a-project-folder) | rejected |

**create_upload_session**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update opens an upload session for the folder, the token and address to upload to come back](#files-a-user-granted-folder-update-opens-an-upload-session) | answered |
| [when a user granted nothing tries to open an upload session for a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-open-an-upload-session) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete in their personal project soft deletes their own vfolder, that vfolder comes back delete-pending](#deleting-a-user-granted-soft-delete-soft-deletes-their-folder) | answered |
| [when a user granted nothing tries to soft delete their own vfolder, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-soft-delete-their-folder) | rejected |

**delete_files**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update deletes files inside the folder, the id of the background task doing it comes back](#files-a-user-granted-folder-update-deletes-files) | answered |
| [when a user granted nothing tries to delete files inside a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-delete-files) | rejected |

**deploy**

| scenario | verdict |
|---|---|
| [when a user granted deployment create in a project deploys a model vfolder they can read, the id and name of the deployment made come back](#deploying-a-user-granted-deployment-create-deploys-a-model-folder) | answered |
| [when a user granted folder read but not deployment create tries to deploy a model vfolder, it is rejected for lack of permission](#deploying-a-user-without-deployment-create-may-not-deploy-a-model-folder) | rejected |
| [when a user tries to deploy a vfolder not used as a model, it is rejected as not a model folder](#deploying-deploying-a-folder-not-used-as-a-model-is-refused) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read in their personal project reads their own vfolder, that vfolder comes back](#reaching-a-user-granted-folder-read-reads-their-own-folder) | answered |
| [when a user who accepted a read share of someone else's vfolder reads it, that vfolder comes back](#reaching-an-accepted-share-reads-someone-elses-folder) | answered |
| [when a user granted nothing tries to read their own vfolder, it is rejected for lack of permission](#reaching-a-user-granted-nothing-may-not-read-their-own-folder) | rejected |
| [when a user who was offered someone else's vfolder but did not accept tries to read it, it is rejected for lack of permission](#reaching-an-unanswered-offer-may-not-read-someone-elses-folder) | rejected |

**get_folder_usage**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read reads the usage of a folder pointing at a path the manager does not own, the call answers no usage](#usage-a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder) | answered |
| [when a user granted vfolder read in their personal project reads their folder's usage, the usage the storage answered comes back](#usage-a-user-granted-folder-read-reads-the-folder-usage) | answered |
| [when a user granted nothing tries to read a folder's usage, it is rejected for lack of permission](#usage-a-user-granted-nothing-may-not-read-the-folder-usage) | rejected |

**list_files**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read lists the files of the folder, the list the storage answered comes back](#files-a-user-granted-folder-read-lists-the-files) | answered |
| [when a user granted nothing tries to list the files of a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-list-the-files) | rejected |

**list_mount_policies**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read lists the mount levels set on the folder, the list holding them comes back](#mount_policies-a-user-granted-folder-read-lists-the-mount-levels) | answered |
| [when a user granted vfolder update sets another user's mount level and then a user holding no permission tries to list the levels set on the folder, it is rejected for lack of permission](#mount_policies-a-user-granted-nothing-may-not-list-the-mount-levels) | rejected |

**mkdir**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update makes directories inside the folder, the paths made come back](#files-a-user-granted-folder-update-makes-directories) | answered |
| [when a user granted nothing tries to make directories inside a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-make-directories) | rejected |

**move_file**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update moves a file inside the folder, where it came from and went to comes back](#files-a-user-granted-folder-update-moves-a-file) | answered |
| [when a user granted nothing tries to move a file inside a folder, it is rejected for lack of permission](#files-a-user-granted-nothing-may-not-move-a-file) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete in their personal project soft deletes their two vfolders and someone else's vfolder in one call, their two vfolders come back delete-pending and the other user's vfolder comes back in the failed list for lack of permission](#partial_bulk-a-user-granted-folder-soft-delete-soft-deletes-their-folders-of-several) | answered |
| [when a user granted nothing tries to soft delete several vfolders in one call, none is soft deleted and all come back in the failed list for lack of permission](#partial_bulk-a-user-granted-nothing-soft-deletes-none-of-several-folders) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete restores their two soft-deleted vfolders in one call, both come back ready for use](#partial_bulk-restoring-several-folders-brings-them-back) | answered |
| [when a user granted vfolder soft delete restores their trashed folder and another user's folder in one call, only their folder comes back and the other user's folder comes back in the failed list for lack of permission](#partial_bulk-restoring-several-folders-leaves-anothers-out) | answered |
| [when a user granted vfolder soft delete restores a trashed vfolder and a folder whose deletion is in progress in one call, only the trashed folder comes back and the other comes back in the failed list](#partial_bulk-restoring-several-folders-leaves-the-purging-one-out) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update in their personal project updates their two vfolders and someone else's vfolder in one call, their two vfolders come back updated and the other user's vfolder comes back in the failed list for lack of permission](#partial_bulk-a-user-granted-folder-update-updates-their-folders-of-several) | answered |
| [when a user granted nothing tries to update several vfolders in one call, none is updated and all come back in the failed list for lack of permission](#partial_bulk-a-user-granted-nothing-updates-none-of-several-folders) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted vfolder hard delete purges their trashed vfolder, that vfolder comes back delete-ongoing](#purging-a-user-granted-hard-delete-purges-a-trashed-folder) | answered |
| [when a user granted nothing tries to purge their trashed vfolder, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-their-folder) | rejected |
| [when a user tries to purge a vfolder that is not in the trash, it is rejected as the status does not allow it](#purging-purging-a-folder-outside-the-trash-is-refused) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when a user granted vfolder soft delete restores their trashed vfolder, the id of that vfolder comes back](#restoring-a-user-granted-soft-delete-restores-their-trashed-folder) | answered |
| [when a user granted nothing tries to restore their trashed vfolder, it is rejected for lack of permission](#restoring-a-user-granted-nothing-may-not-restore-their-folder) | rejected |

**set_mount_policy**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update sets another user's mount level to read-only, the level now set comes back](#mount_policies-a-user-granted-folder-update-sets-another-users-mount-level) | answered |
| [when a user granted nothing tries to set a mount level, it is rejected for lack of permission](#mount_policies-a-user-granted-nothing-may-not-set-a-mount-level) | rejected |
| [when a user tries to set the folder owner's mount level, it is rejected](#mount_policies-setting-the-owners-own-mount-level-is-refused) | rejected |

**unset_mount_policy**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update takes back another user's mount level, its place and that the row is gone come back](#mount_policies-a-user-granted-folder-update-takes-another-users-level-back) | answered |
| [when a user granted vfolder update sets another user's mount level and then a user holding no permission tries to take it back, it is rejected for lack of permission](#mount_policies-a-user-granted-nothing-may-not-take-a-mount-level-back) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted vfolder update in their personal project changes the name and options of their own vfolder, the changed vfolder comes back](#editing-a-user-granted-folder-update-renames-their-folder) | answered |
| [when a user granted nothing tries to change their own vfolder, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-update-their-folder) | rejected |
| [when the user tries to rename it to a name their other vfolder already uses, it is rejected as an invalid value](#editing-renaming-to-a-name-the-owner-already-uses-is-refused) | rejected |

### admin_search

<a id="searching-a-superadmin-searches-every-folder"></a>

#### [a-superadmin-searches-every-folder](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

when a superadmin holding no role searches every vfolder, the vfolder seeded in advance comes back

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

- VFolderAdapter.admin_search: user-2 searches every vfolder without a filter

Then

- the page holding only the vfolder seeded in advance comes back
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items.length = 1
  - items[0].id: same as the vfolder seeded in advance
  - items[0].entity_id: same as the id in the answer
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'folder-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'user'
  - items[0].ownership.user_id: same as the vfolder owner
  - items[0].ownership.project_id: same as the project the vfolder is placed in
  - items[0].ownership.creator_id: same as the user who created the vfolder
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - items[0].access_control.permission = 'none'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
  - items[0].metadata.created_at: the time this run wrote

<a id="searching-a-regular-user-may-not-search-every-folder"></a>

#### [a-regular-user-may-not-search-every-folder](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

when a regular user tries to search every vfolder, it is rejected for lack of permission

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

- VFolderAdapter.admin_search: user-1 searches every vfolder without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

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
  - [0].entity_id: same as the id in the answer
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
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
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
  - [0].entity_id: same as the id in the answer
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
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
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
  - [0].entity_id: same as the id in the answer
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
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
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
  - [0].entity_id: same as the id in the answer
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
  - [0].metadata.usage_mode = 'general'
  - [0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - [0].access_control.permission = 'none'
  - [0].quota.max_size = None
  - [0].quota.max_files = 1000
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
  - items[0].entity_id: same as the id in the answer
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
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - items[0].access_control.permission = 'rw'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
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

<a id="searching-a-search-narrows-to-the-matching-folder-in-order-and-page"></a>

#### [a-search-narrows-to-the-matching-folder-in-order-and-page](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

when a user granted vfolder read in their own scope searches by a name fragment, ordered by name ascending and limited to one page, one page holding only their two matching vfolders in name order comes back

Given

- one user granted the READ permission on vfolders in their own scope, with two personal vfolders whose names hold match, one personal vfolder whose name does not, and one other user's personal vfolder whose name holds match
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder match-1: is placed in that person's personal project and is ready to use
  - Personal vfolder match-2: is placed in that person's personal project and is ready to use
  - Personal vfolder other-1: is placed in that person's personal project and is ready to use
  - Personal vfolder match-3: is placed in that person's personal project and is ready to use
  - Prepare a user granted the READ permission on vfolders in their own scope
    - Role folder-holder-1: applies only within the scope it is granted in
    - Role folder-holder-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-holder-1

When

- VFolderAdapter.scoped_search: user-1 searches their own scope for vfolders whose name holds match, ordered by name ascending, up to 2

Then

- one page holding only their two matching vfolders in name order comes back
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the vfolder seeded in advance
  - items[0].entity_id: same as the id in the answer
  - items[0].host = 'local:volume1'
  - items[0].status = 'ready'
  - items[0].metadata.name = 'match-1'
  - items[0].metadata.cloneable = False
  - items[0].metadata.last_used = None
  - items[0].access_control.ownership_type = 'user'
  - items[0].ownership.user_id: same as the vfolder owner
  - items[0].ownership.project_id: same as the project the vfolder is placed in
  - items[0].ownership.creator_id: same as the user who created the vfolder
  - items[0].ownership.creator_email = 'user-1@scenario.local'
  - items[0].unmanaged_path = None
  - items[0].metadata.usage_mode = 'general'
  - items[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - items[0].access_control.permission = 'none'
  - items[0].quota.max_size = None
  - items[0].quota.max_files = 1000
  - items[0].metadata.created_at: the time this run wrote
  - items[1].id: same as the vfolder seeded in advance
  - items[1].entity_id: same as the id in the answer
  - items[1].host = 'local:volume1'
  - items[1].status = 'ready'
  - items[1].metadata.name = 'match-2'
  - items[1].metadata.cloneable = False
  - items[1].metadata.last_used = None
  - items[1].access_control.ownership_type = 'user'
  - items[1].ownership.user_id: same as the vfolder owner
  - items[1].ownership.project_id: same as the project the vfolder is placed in
  - items[1].ownership.creator_id: same as the user who created the vfolder
  - items[1].ownership.creator_email = 'user-1@scenario.local'
  - items[1].unmanaged_path = None
  - items[1].metadata.usage_mode = 'general'
  - items[1].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - items[1].access_control.permission = 'none'
  - items[1].quota.max_size = None
  - items[1].quota.max_files = 1000
  - items[1].metadata.created_at: the time this run wrote
  - items ids: their two matching vfolders

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

<a id="searching-a-user-granted-nothing-may-not-search-their-own-scope"></a>

#### [a-user-granted-nothing-may-not-search-their-own-scope](/tests/scenario/bai_scenario/manager/vfolder/test_searching.py): pass

when a user granted nothing tries to search the vfolders of their own scope, it is rejected for lack of permission

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

- VFolderAdapter.scoped_search: user-1 searches the vfolders of their own scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### batch_load_mount_permissions

<a id="batch_permissions-the-owner-of-a-personal-folder-loads-the-read-write-mount-level"></a>

#### [the-owner-of-a-personal-folder-loads-the-read-write-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

when the user who can read their own personal vfolder loads the mount level they get, an answer holding the read-write level comes back

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

- VFolderAdapter.batch_load_mount_permissions: user-1 loads the mount level they get on the folder-1 vfolder in one call

Then

- an answer holding the one read-write mount level comes back
  - length = 1
  - [0] = <VFolderPermissionField.READ_WRITE: 'rw'>

<a id="batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-a-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

when a user granted nothing loads the mount level they get, the call succeeds but that entry is rejected for lack of permission

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

- VFolderAdapter.batch_load_mount_permissions: user-1 loads the mount level they get on the folder-1 vfolder in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_permissions

<a id="batch_permissions-a-user-granted-folder-read-loads-their-permissions"></a>

#### [a-user-granted-folder-read-loads-their-permissions](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

when a user granted vfolder read loads the permissions they hold, an answer holding only the read permission comes back

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

- VFolderAdapter.batch_load_permissions: user-1 loads the permissions they hold on the folder-1 vfolder in one call

Then

- an answer holding only the read permission comes back
  - length = 1
  - [0] = [<PermissionBitDTO.READ: 'read'>]

<a id="batch_permissions-a-user-granted-nothing-gets-a-rejection-in-place-of-permissions"></a>

#### [a-user-granted-nothing-gets-a-rejection-in-place-of-permissions](/tests/scenario/bai_scenario/manager/vfolder/test_batch_permissions.py): pass

when a user granted nothing loads the permissions they hold, the call succeeds but that entry is rejected for lack of permission

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

- VFolderAdapter.batch_load_permissions: user-1 loads the permissions they hold on the folder-1 vfolder in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### clone

<a id="cloning-a-user-granted-clone-copies-a-cloneable-folder"></a>

#### [a-user-granted-clone-copies-a-cloneable-folder](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

when a user granted clone on a cloneable vfolder of their own clones it under a new name, the cloned vfolder comes back

Given

- one user with one ready personal vfolder, granted the CREATE, READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is ready, may be cloned
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: CREATE allowed on every vfolder
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.clone: user-1 clones the folder-1 vfolder under the name copy

Then

- the whole cloned vfolder comes back
  - bgtask_id = '00000000-0000-0000-0000-000000000001'
  - vfolder.id: same as the entity_id
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'ready'
  - vfolder.metadata.name = 'copy'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: same as the cloner
  - vfolder.ownership.project_id: same as the cloner's personal project the source vfolder is placed in
  - vfolder.ownership.creator_id: same as the cloner
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: same as the quota scope of the cloner
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: the time this run wrote

<a id="cloning-a-user-granted-nothing-may-not-clone-their-folder"></a>

#### [a-user-granted-nothing-may-not-clone-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

when a user granted nothing tries to clone their own vfolder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is ready, may be cloned

When

- VFolderAdapter.clone: user-1 clones the folder-1 vfolder under the name copy

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="cloning-cloning-a-folder-not-marked-cloneable-is-refused"></a>

#### [cloning-a-folder-not-marked-cloneable-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_cloning.py): pass

when a user tries to clone a vfolder not marked cloneable, it is rejected

Given

- one user with one ready personal vfolder, granted the CREATE, READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: CREATE allowed on every vfolder
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.clone: user-1 clones the folder-1 vfolder under the name copy

Then

- the call is rejected
  - rejected: Forbidden

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

### create_download_session

<a id="files-a-user-granted-folder-read-opens-a-download-session"></a>

#### [a-user-granted-folder-read-opens-a-download-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder read opens a download session for the folder, the token and address to download from come back

Given

- one user with one ready personal vfolder, granted the READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.create_download_session: user-1 opens a download session for the folder-1 vfolder

Then

- the token and address to download from come back
  - token = 'download-token'
  - url = 'http://127.0.0.1:6021/download'

<a id="files-a-user-granted-nothing-may-not-open-a-download-session"></a>

#### [a-user-granted-nothing-may-not-open-a-download-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to open a download session for a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.create_download_session: user-1 opens a download session for the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create_in_project

<a id="creating-a-user-granted-folder-create-in-a-project-makes-a-project-folder"></a>

#### [a-user-granted-folder-create-in-a-project-makes-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py): pass

when a user granted vfolder create in a project creates a folder owned by that project, the folder belongs to the project

Given

- a project that can hold vfolders and one user granted vfolder create in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1: vfolders of this project can be placed on local:volume1
  - Role folder-maker-1: applies only within the scope it is granted in
  - Role folder-maker-1: CREATE allowed on every vfolder
  - regular user user-1: holds Role folder-maker-1

When

- VFolderAdapter.create_in_project: user-1 creates the shared vfolder owned by the project-1 project

Then

- the whole vfolder just created comes back
  - id: same as the entity_id
  - host = 'local:volume1'
  - status = 'ready'
  - metadata.name = 'shared'
  - metadata.cloneable = False
  - metadata.last_used = None
  - access_control.ownership_type = 'group'
  - ownership.user_id: same as the folder owner
  - ownership.project_id: same as the project the folder landed in
  - ownership.creator_id: same as the creator
  - ownership.creator_email = 'user-1@scenario.local'
  - unmanaged_path = None
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: same as the quota scope of the folder owner
  - access_control.permission = 'rw'
  - quota.max_size = None
  - quota.max_files = 1000
  - metadata.created_at: the time this run wrote

<a id="creating-a-user-granted-nothing-may-not-make-a-project-folder"></a>

#### [a-user-granted-nothing-may-not-make-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder/test_creating.py): pass

when a user granted nothing tries to create a project-owned vfolder, it is rejected for lack of permission

Given

- a project that can hold vfolders and one user holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1: vfolders of this project can be placed on local:volume1

When

- VFolderAdapter.create_in_project: user-1 creates the shared vfolder owned by the project-1 project

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create_upload_session

<a id="files-a-user-granted-folder-update-opens-an-upload-session"></a>

#### [a-user-granted-folder-update-opens-an-upload-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder update opens an upload session for the folder, the token and address to upload to come back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.create_upload_session: user-1 opens an upload session for the folder-1 vfolder

Then

- the token and address to upload to come back
  - token = 'upload-token'
  - url = 'http://127.0.0.1:6021/upload'

<a id="files-a-user-granted-nothing-may-not-open-an-upload-session"></a>

#### [a-user-granted-nothing-may-not-open-an-upload-session](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to open an upload session for a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.create_upload_session: user-1 opens an upload session for the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### delete

<a id="deleting-a-user-granted-soft-delete-soft-deletes-their-folder"></a>

#### [a-user-granted-soft-delete-soft-deletes-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deleting.py): pass

when a user granted vfolder soft delete in their personal project soft deletes their own vfolder, that vfolder comes back delete-pending

Given

- one user with one ready personal vfolder, granted the SOFT_DELETE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.delete: user-1 soft deletes the folder-1 vfolder

Then

- the whole vfolder in the delete-pending state comes back
  - id: same as the id of the vfolder called
  - vfolder.id: same as the vfolder seeded in advance
  - vfolder.entity_id: same as the id in the answer
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'delete-pending'
  - vfolder.metadata.name = 'folder-1'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: same as the vfolder owner
  - vfolder.ownership.project_id: same as the project the vfolder is placed in
  - vfolder.ownership.creator_id: same as the user who created the vfolder
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-their-folder"></a>

#### [a-user-granted-nothing-may-not-soft-delete-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deleting.py): pass

when a user granted nothing tries to soft delete their own vfolder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.delete: user-1 soft deletes the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### delete_files

<a id="files-a-user-granted-folder-update-deletes-files"></a>

#### [a-user-granted-folder-update-deletes-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder update deletes files inside the folder, the id of the background task doing it comes back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.delete_files: user-1 deletes one file inside the folder-1 vfolder

Then

- the id of the background task doing the deletion comes back
  - bgtask_id = '00000000-0000-0000-0000-000000000002'

<a id="files-a-user-granted-nothing-may-not-delete-files"></a>

#### [a-user-granted-nothing-may-not-delete-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to delete files inside a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.delete_files: user-1 deletes one file inside the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### deploy

<a id="deploying-a-user-granted-deployment-create-deploys-a-model-folder"></a>

#### [a-user-granted-deployment-create-deploys-a-model-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

when a user granted deployment create in a project deploys a model vfolder they can read, the id and name of the deployment made come back

Given

- a project and a resource group to hold deployments, one model vfolder, a runtime variant and a revision preset, and one user granted folder read and deployment create in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project vfolder folder-1: is placed in the project, is ready, is used as model
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1
  - Role deployer-1: applies only within the scope it is granted in
  - Role deployer-1: CREATE allowed on every deployment
  - regular user user-1: holds Role deployer-1
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Deployment revision preset preset-1: single node, one replica, rolling update, carries a model definition

When

- VFolderAdapter.deploy: user-1 creates a deployment in the project-1 from the folder-1 vfolder

Then

- the id of the deployment made and its name derived from the folder come back
  - deployment_id: skipped: the database generates it
  - deployment_name: a name starting with 'folder-1'

<a id="deploying-a-user-without-deployment-create-may-not-deploy-a-model-folder"></a>

#### [a-user-without-deployment-create-may-not-deploy-a-model-folder](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

when a user granted folder read but not deployment create tries to deploy a model vfolder, it is rejected for lack of permission

Given

- a project and a resource group to hold deployments, one model vfolder, a runtime variant and a revision preset, and one user granted folder read but not deployment create in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project vfolder folder-1: is placed in the project, is ready, is used as model
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Deployment revision preset preset-1: single node, one replica, rolling update, carries a model definition

When

- VFolderAdapter.deploy: user-1 creates a deployment in the project-1 from the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="deploying-deploying-a-folder-not-used-as-a-model-is-refused"></a>

#### [deploying-a-folder-not-used-as-a-model-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_deploying.py): pass

when a user tries to deploy a vfolder not used as a model, it is rejected as not a model folder

Given

- a project and a resource group to hold deployments, one general vfolder, a runtime variant and a revision preset, and one user granted folder read and deployment create in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1
  - Role deployer-1: applies only within the scope it is granted in
  - Role deployer-1: CREATE allowed on every deployment
  - regular user user-1: holds Role deployer-1
  - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Deployment revision preset preset-1: single node, one replica, rolling update, carries a model definition

When

- VFolderAdapter.deploy: user-1 creates a deployment in the project-1 from the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotAModelVFolder

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
  - entity_id: same as the id in the answer
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
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - access_control.permission = 'none'
  - quota.max_size = None
  - quota.max_files = 1000
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
  - entity_id: same as the id in the answer
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
  - metadata.usage_mode = 'general'
  - metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - access_control.permission = 'none'
  - quota.max_size = None
  - quota.max_files = 1000
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

### get_folder_usage

<a id="usage-a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder"></a>

#### [a-user-granted-folder-read-reads-no-usage-for-an-unmanaged-folder](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

when a user granted vfolder read reads the usage of a folder pointing at a path the manager does not own, the call answers no usage

Given

- one user with one personal vfolder pointing at a path the manager does not own, granted the READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder unmanaged-1: is placed in that person's personal project and points at a path the manager does not own
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.get_folder_usage: user-1 reads the usage of the unmanaged-1 vfolder

Then

- the call answers no usage, as the folder is not managed
  - the call answers nothing

<a id="usage-a-user-granted-folder-read-reads-the-folder-usage"></a>

#### [a-user-granted-folder-read-reads-the-folder-usage](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

when a user granted vfolder read in their personal project reads their folder's usage, the usage the storage answered comes back

Given

- one user with one ready personal vfolder, granted the READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.get_folder_usage: user-1 reads the usage of the folder-1 vfolder

Then

- the whole usage the storage answered comes back
  - num_files = 0
  - used_bytes.expr = '0'
  - used_bytes.display = '0'

<a id="usage-a-user-granted-nothing-may-not-read-the-folder-usage"></a>

#### [a-user-granted-nothing-may-not-read-the-folder-usage](/tests/scenario/bai_scenario/manager/vfolder/test_usage.py): pass

when a user granted nothing tries to read a folder's usage, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.get_folder_usage: user-1 reads the usage of the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### list_files

<a id="files-a-user-granted-folder-read-lists-the-files"></a>

#### [a-user-granted-folder-read-lists-the-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder read lists the files of the folder, the list the storage answered comes back

Given

- one user with one ready personal vfolder, granted the READ permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.list_files: user-1 lists the files of the folder-1 vfolder

Then

- the whole file list the storage answered comes back
  - items.length = 2
  - items[0].name = 'hello.txt'
  - items[0].type = 'FILE'
  - items[0].size = 5
  - items[0].mode = 33188
  - items[0].created_at = '2026-01-01 00:00:00'
  - items[0].updated_at = '2026-01-02 00:00:00'
  - items[1].name = 'data'
  - items[1].type = 'DIRECTORY'
  - items[1].size = 0
  - items[1].mode = 16877
  - items[1].created_at = '2026-01-01 00:00:00'
  - items[1].updated_at = '2026-01-01 00:00:00'

<a id="files-a-user-granted-nothing-may-not-list-the-files"></a>

#### [a-user-granted-nothing-may-not-list-the-files](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to list the files of a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.list_files: user-1 lists the files of the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### list_mount_policies

<a id="mount_policies-a-user-granted-folder-read-lists-the-mount-levels"></a>

#### [a-user-granted-folder-read-lists-the-mount-levels](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted vfolder read lists the mount levels set on the folder, the list holding them comes back

Given

- one user with one ready personal vfolder, granted the READ, UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: READ allowed on every vfolder
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.list_mount_policies: user-1 lists the mount levels set on the folder-1 vfolder

Then

- the list holding the one mount level comes back
  - items.length = 1
  - items[0].id: skipped: the database generates it
  - items[0].field_id: same as the id in the answer
  - items[0].vfolder_id: same as the vfolder called
  - items[0].user_id: same as the user given the level
  - items[0].permission = 'ro'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="mount_policies-a-user-granted-nothing-may-not-list-the-mount-levels"></a>

#### [a-user-granted-nothing-may-not-list-the-mount-levels](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted vfolder update sets another user's mount level and then a user holding no permission tries to list the levels set on the folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.list_mount_policies: user-1 sets another user's mount level on the folder-1 vfolder, and then user-2, holding no permission, lists the levels set on it

Then

- the call is rejected
  - rejected: NotEnoughPermission

### mkdir

<a id="files-a-user-granted-folder-update-makes-directories"></a>

#### [a-user-granted-folder-update-makes-directories](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder update makes directories inside the folder, the paths made come back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.mkdir: user-1 makes two directories inside the folder-1 vfolder

Then

- the paths of the directories made come back
  - results = ['new', 'other']

<a id="files-a-user-granted-nothing-may-not-make-directories"></a>

#### [a-user-granted-nothing-may-not-make-directories](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to make directories inside a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.mkdir: user-1 makes two directories inside the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

### move_file

<a id="files-a-user-granted-folder-update-moves-a-file"></a>

#### [a-user-granted-folder-update-moves-a-file](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted vfolder update moves a file inside the folder, where it came from and went to comes back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.move_file: user-1 moves one file inside the folder-1 vfolder

Then

- where the file was moved from and to comes back
  - src = 'hello.txt'
  - dst = 'data/hello.txt'

<a id="files-a-user-granted-nothing-may-not-move-a-file"></a>

#### [a-user-granted-nothing-may-not-move-a-file](/tests/scenario/bai_scenario/manager/vfolder/test_files.py): pass

when a user granted nothing tries to move a file inside a folder, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use

When

- VFolderAdapter.move_file: user-1 moves one file inside the folder-1 vfolder

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
  - successes[0].entity_id: same as the id in the answer
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
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].entity_id: same as the id in the answer
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
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
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
  - successes[0].entity_id: same as the id in the answer
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
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].entity_id: same as the id in the answer
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
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
  - successes[1].metadata.created_at: the time this run wrote
  - failed = []

<a id="partial_bulk-restoring-several-folders-leaves-anothers-out"></a>

#### [restoring-several-folders-leaves-anothers-out](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted vfolder soft delete restores their trashed folder and another user's folder in one call, only their folder comes back and the other user's folder comes back in the failed list for lack of permission

Given

- one user with one delete-pending personal vfolder of their own and one delete-pending personal vfolder of their own, granted the SOFT_DELETE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project, is delete-pending
  - Personal vfolder second-1: is placed in that person's personal project, is delete-pending
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.partial_bulk_restore: user-1 restores their trashed vfolder and another user's vfolder in one call

Then

- only their trashed folder comes back ready for use, and the other user's folder comes back in the failed list for lack of permission
  - successes count = 1
  - successes[0].id: same as the vfolder seeded in advance
  - successes[0].entity_id: same as the id in the answer
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
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the id of the target vfolder
  - failed[0].message: a reason containing 'Insufficient permission'

<a id="partial_bulk-restoring-several-folders-leaves-the-purging-one-out"></a>

#### [restoring-several-folders-leaves-the-purging-one-out](/tests/scenario/bai_scenario/manager/vfolder/test_partial_bulk.py): pass

when a user granted vfolder soft delete restores a trashed vfolder and a folder whose deletion is in progress in one call, only the trashed folder comes back and the other comes back in the failed list

Given

- one user with one delete-pending personal vfolder of their own and one delete-ongoing personal vfolder of their own, granted the SOFT_DELETE permission on vfolders in their personal project, and one other user's personal vfolder not shared with them
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Personal vfolder first-1: is placed in that person's personal project, is delete-pending
  - Personal vfolder second-1: is placed in that person's personal project, is delete-ongoing
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.partial_bulk_restore: user-1 restores their trashed vfolder and their vfolder whose deletion is still in progress in one call

Then

- only the trashed folder comes back ready for use, and the folder whose deletion is in progress comes back in the failed list
  - successes count = 1
  - successes[0].id: same as the vfolder seeded in advance
  - successes[0].entity_id: same as the id in the answer
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
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the vfolder whose deletion is in progress
  - failed[0].message: a reason containing 'being purged'

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
  - successes[0].entity_id: same as the id in the answer
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
  - successes[0].metadata.usage_mode = 'general'
  - successes[0].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[0].access_control.permission = 'none'
  - successes[0].quota.max_size = None
  - successes[0].quota.max_files = 1000
  - successes[0].metadata.created_at: the time this run wrote
  - successes[1].id: same as the vfolder seeded in advance
  - successes[1].entity_id: same as the id in the answer
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
  - successes[1].metadata.usage_mode = 'general'
  - successes[1].metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - successes[1].access_control.permission = 'none'
  - successes[1].quota.max_size = None
  - successes[1].quota.max_files = 1000
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

### purge

<a id="purging-a-user-granted-hard-delete-purges-a-trashed-folder"></a>

#### [a-user-granted-hard-delete-purges-a-trashed-folder](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

when a user granted vfolder hard delete purges their trashed vfolder, that vfolder comes back delete-ongoing

Given

- one user with one delete-pending personal vfolder, granted the HARD_DELETE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is delete-pending
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: HARD_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.purge: user-1 purges the folder-1 vfolder

Then

- the whole vfolder in the delete-ongoing state comes back
  - id: same as the id of the vfolder called
  - vfolder.id: same as the vfolder seeded in advance
  - vfolder.entity_id: same as the id in the answer
  - vfolder.host = 'local:volume1'
  - vfolder.status = 'delete-ongoing'
  - vfolder.metadata.name = 'folder-1'
  - vfolder.metadata.cloneable = False
  - vfolder.metadata.last_used = None
  - vfolder.access_control.ownership_type = 'user'
  - vfolder.ownership.user_id: same as the vfolder owner
  - vfolder.ownership.project_id: same as the project the vfolder is placed in
  - vfolder.ownership.creator_id: same as the user who created the vfolder
  - vfolder.ownership.creator_email = 'user-1@scenario.local'
  - vfolder.unmanaged_path = None
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
  - vfolder.metadata.created_at: the time this run wrote

<a id="purging-a-user-granted-nothing-may-not-purge-their-folder"></a>

#### [a-user-granted-nothing-may-not-purge-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

when a user granted nothing tries to purge their trashed vfolder, it is rejected for lack of permission

Given

- one user with one delete-pending personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is delete-pending

When

- VFolderAdapter.purge: user-1 purges the folder-1 vfolder

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-purging-a-folder-outside-the-trash-is-refused"></a>

#### [purging-a-folder-outside-the-trash-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_purging.py): pass

when a user tries to purge a vfolder that is not in the trash, it is rejected as the status does not allow it

Given

- one user with one ready personal vfolder, granted the HARD_DELETE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: HARD_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.purge: user-1 purges the folder-1 vfolder

Then

- the call is rejected
  - rejected: VFolderFilterStatusFailed

### restore

<a id="restoring-a-user-granted-soft-delete-restores-their-trashed-folder"></a>

#### [a-user-granted-soft-delete-restores-their-trashed-folder](/tests/scenario/bai_scenario/manager/vfolder/test_restoring.py): pass

when a user granted vfolder soft delete restores their trashed vfolder, the id of that vfolder comes back

Given

- one user with one delete-pending personal vfolder, granted the SOFT_DELETE permission on their personal folder
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is delete-pending
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: SOFT_DELETE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.restore: user-1 restores the folder-1 vfolder from trash

Then

- the id of the restored vfolder comes back
  - id: same as the id of the restored vfolder

<a id="restoring-a-user-granted-nothing-may-not-restore-their-folder"></a>

#### [a-user-granted-nothing-may-not-restore-their-folder](/tests/scenario/bai_scenario/manager/vfolder/test_restoring.py): pass

when a user granted nothing tries to restore their trashed vfolder, it is rejected for lack of permission

Given

- one user with one delete-pending personal vfolder, holding no permission
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Personal vfolder folder-1: is placed in that person's personal project, is delete-pending

When

- VFolderAdapter.restore: user-1 restores the folder-1 vfolder from trash

Then

- the call is rejected
  - rejected: NotEnoughPermission

### set_mount_policy

<a id="mount_policies-a-user-granted-folder-update-sets-another-users-mount-level"></a>

#### [a-user-granted-folder-update-sets-another-users-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted vfolder update sets another user's mount level to read-only, the level now set comes back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.set_mount_policy: user-1 sets the mount level of another user on the folder-1 vfolder to read-only

Then

- the whole mount level just set comes back
  - policy.id: skipped: the database generates it
  - policy.field_id: same as the id in the answer
  - policy.vfolder_id: same as the vfolder called
  - policy.user_id: same as the user given the level
  - policy.permission = 'ro'
  - policy.created_at: the time this run wrote
  - policy.updated_at: the time this run wrote

<a id="mount_policies-a-user-granted-nothing-may-not-set-a-mount-level"></a>

#### [a-user-granted-nothing-may-not-set-a-mount-level](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted nothing tries to set a mount level, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, holding no permission, and one other user who does not use that folder
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

When

- VFolderAdapter.set_mount_policy: user-1 sets the mount level of another user on the folder-1 vfolder to read-only

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="mount_policies-setting-the-owners-own-mount-level-is-refused"></a>

#### [setting-the-owners-own-mount-level-is-refused](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user tries to set the folder owner's mount level, it is rejected

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.set_mount_policy: user-1 sets the mount level of the owner themselves on the folder-1 vfolder to read-only

Then

- the call is rejected
  - rejected: VFolderMountPolicyNotApplicable

### unset_mount_policy

<a id="mount_policies-a-user-granted-folder-update-takes-another-users-level-back"></a>

#### [a-user-granted-folder-update-takes-another-users-level-back](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted vfolder update takes back another user's mount level, its place and that the row is gone come back

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.unset_mount_policy: user-1 sets and then takes back another user's mount level on the folder-1 vfolder

Then

- the place of the mount level taken back comes, and the row is gone
  - vfolder_id: same as the vfolder called
  - user_id: same as the user who lost the level
  - removed = True

<a id="mount_policies-a-user-granted-nothing-may-not-take-a-mount-level-back"></a>

#### [a-user-granted-nothing-may-not-take-a-mount-level-back](/tests/scenario/bai_scenario/manager/vfolder/test_mount_policies.py): pass

when a user granted vfolder update sets another user's mount level and then a user holding no permission tries to take it back, it is rejected for lack of permission

Given

- one user with one ready personal vfolder, granted the UPDATE permission on their personal folder, and one other user who does not use that folder
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
  - Grant vfolder permissions
    - Role folder-writer-1: applies only within the scope it is granted in
    - Role folder-writer-1: UPDATE allowed on every vfolder
    - regular user user-1: holds Role folder-writer-1

When

- VFolderAdapter.unset_mount_policy: user-1 sets another user's mount level on the folder-1 vfolder, and then user-2, holding no permission, takes it back

Then

- the call is rejected
  - rejected: NotEnoughPermission

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
  - vfolder.entity_id: same as the id in the answer
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
  - vfolder.metadata.usage_mode = 'general'
  - vfolder.metadata.quota_scope_id: same as the quota scope of the vfolder seeded in advance
  - vfolder.access_control.permission = 'none'
  - vfolder.quota.max_size = None
  - vfolder.quota.max_files = 1000
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

