## vfolder_auto_mount

[adapter](/src/ai/backend/manager/api/adapters/vfolder_auto_mount/adapter.py)

Scenario: complete

- built from ops (4)
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (1)
  - create: success present 1 · rejection present 1 (scope)

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user granted auto-mount read loads it by id, that auto-mount comes back](#batch_loading-a-user-granted-auto-mount-read-loads-it-by-id) | answered |
| [when a user granted nothing loads an auto-mount by id, the call succeeds but that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-an-auto-mount) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when a user granted auto-mount delete soft deletes it, the deleted auto-mount comes back](#deleting-a-user-granted-auto-mount-delete-soft-deletes-it) | answered |
| [when a user granted nothing tries to soft delete an auto-mount, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-delete-an-auto-mount) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user lists the auto-mounts of a project that has none, the answer is empty](#searching-a-project-with-no-auto-mount-answers-an-empty-page) | answered |
| [when a user granted auto-mount read in a project searches by a destination fragment, ordered by destination and limited to one page, one page holding only the two matching auto-mounts in destination order comes back](#searching-a-user-granted-auto-mount-read-lists-the-project-auto-mounts) | answered |
| [when a user granted nothing tries to list the auto-mounts of a project, it is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-list-project-auto-mounts) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted auto-mount update changes its destination and permission, the changed auto-mount comes back](#editing-a-user-granted-auto-mount-update-changes-its-destination) | answered |
| [when a user granted nothing tries to change an auto-mount, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-change-an-auto-mount) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted auto-mount create in a project registers one of its folders, the auto-mount naming that folder comes back](#creating-a-user-granted-auto-mount-create-registers-a-project-folder) | answered |
| [when a user granted nothing tries to register an auto-mount, it is rejected for lack of permission](#creating-a-user-granted-nothing-may-not-register-an-auto-mount) | rejected |

### bulk_get_ids

<a id="batch_loading-a-user-granted-auto-mount-read-loads-it-by-id"></a>

#### [a-user-granted-auto-mount-read-loads-it-by-id](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_batch_loading.py): pass

when a user granted auto-mount read loads it by id, that auto-mount comes back

Given

- a project with one vfolder and one user granted the READ permission on auto-mounts, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare a user granted the READ permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: READ allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.bulk_get_ids: user-1 loads the auto-mount by id in one call

Then

- the one auto-mount comes back
  - length = 1
  - id: same as the entity_id
  - scope_type = 'project'
  - scope_id: same as the project the folder is in
  - vfolder_id: same as the auto-mounted vfolder
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-an-auto-mount"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_batch_loading.py): pass

when a user granted nothing loads an auto-mount by id, the call succeeds but that entry is rejected for lack of permission

Given

- a project with one vfolder and one user holding no permission, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.bulk_get_ids: user-1 loads the auto-mount by id in one call

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### delete

<a id="deleting-a-user-granted-auto-mount-delete-soft-deletes-it"></a>

#### [a-user-granted-auto-mount-delete-soft-deletes-it](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_deleting.py): pass

when a user granted auto-mount delete soft deletes it, the deleted auto-mount comes back

Given

- a project with one vfolder and one user granted the SOFT_DELETE permission on auto-mounts, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare a user granted the SOFT_DELETE permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: SOFT_DELETE allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.delete: user-1 soft deletes the auto-mount

Then

- the whole deleted auto-mount comes back
  - id: same as the entity_id
  - scope_type = 'project'
  - scope_id: same as the project the folder is in
  - vfolder_id: same as the auto-mounted vfolder
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-delete-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-delete-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_deleting.py): pass

when a user granted nothing tries to soft delete an auto-mount, it is rejected for lack of permission

Given

- a project with one vfolder and one user holding no permission, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.delete: user-1 soft deletes the auto-mount

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-a-project-with-no-auto-mount-answers-an-empty-page"></a>

#### [a-project-with-no-auto-mount-answers-an-empty-page](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

when a user lists the auto-mounts of a project that has none, the answer is empty

Given

- a project with one vfolder and one user granted the READ permission on auto-mounts
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare a user granted the READ permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: READ allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1

When

- VFolderAutoMountAdapter.scoped_search: user-1 lists the auto-mounts of the project-1 project

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-auto-mount-read-lists-the-project-auto-mounts"></a>

#### [a-user-granted-auto-mount-read-lists-the-project-auto-mounts](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

when a user granted auto-mount read in a project searches by a destination fragment, ordered by destination and limited to one page, one page holding only the two matching auto-mounts in destination order comes back

Given

- a project with two auto-mounts whose destination holds match and one whose does not, one auto-mount outside that project whose destination holds match, and one user granted the READ permission on auto-mounts in that project
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/match-one with ro
  - Project vfolder folder-2: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-2: is mounted at /home/work/match-two with ro
  - Project vfolder folder-3: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-3: is mounted at /home/work/other with ro
  - Personal vfolder folder-4: is placed in that person's personal project and is ready to use
  - Vfolder auto-mount auto-mount-4: is mounted at /home/work/match-three with ro
  - Prepare a user granted the READ permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: READ allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1

When

- VFolderAutoMountAdapter.scoped_search: user-1 lists up to 2 auto-mounts of the project-1 project whose destination holds match, ordered by destination

Then

- one page holding only the two matching auto-mounts in destination order comes back
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the entity_id
  - items[0].scope_type = 'project'
  - items[0].scope_id: same as the project the folder is in
  - items[0].vfolder_id: same as the auto-mounted vfolder
  - items[0].mount_destination = '/home/work/match-one'
  - items[0].subpath = '.'
  - items[0].mount_permission = 'ro'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].deleted_at = None
  - items[1].id: same as the entity_id
  - items[1].scope_type = 'project'
  - items[1].scope_id: same as the project the folder is in
  - items[1].vfolder_id: same as the auto-mounted vfolder
  - items[1].mount_destination = '/home/work/match-two'
  - items[1].subpath = '.'
  - items[1].mount_permission = 'ro'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].deleted_at = None
  - items ids: the two matching auto-mounts

<a id="searching-a-user-granted-nothing-may-not-list-project-auto-mounts"></a>

#### [a-user-granted-nothing-may-not-list-project-auto-mounts](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_searching.py): pass

when a user granted nothing tries to list the auto-mounts of a project, it is rejected for lack of permission

Given

- a project with one vfolder and one user holding no permission, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.scoped_search: user-1 lists the auto-mounts of the project-1 project

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-a-user-granted-auto-mount-update-changes-its-destination"></a>

#### [a-user-granted-auto-mount-update-changes-its-destination](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_editing.py): pass

when a user granted auto-mount update changes its destination and permission, the changed auto-mount comes back

Given

- a project with one vfolder and one user granted the UPDATE permission on auto-mounts, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare a user granted the UPDATE permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: UPDATE allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.update: user-1 moves the auto-mount to /home/work/edited and changes its permission to read-write

Then

- the whole live auto-mount comes back
  - id: same as the entity_id
  - scope_type = 'project'
  - scope_id: same as the project the folder is in
  - vfolder_id: same as the auto-mounted vfolder
  - mount_destination = '/home/work/edited'
  - subpath = '.'
  - mount_permission = 'rw'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-change-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-change-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_editing.py): pass

when a user granted nothing tries to change an auto-mount, it is rejected for lack of permission

Given

- a project with one vfolder and one user holding no permission, and the folder already auto-mounted
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Vfolder auto-mount auto-mount-1: is mounted at /home/work/extra with ro

When

- VFolderAutoMountAdapter.update: user-1 moves the auto-mount to /home/work/edited and changes its permission to read-write

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create

<a id="creating-a-user-granted-auto-mount-create-registers-a-project-folder"></a>

#### [a-user-granted-auto-mount-create-registers-a-project-folder](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_creating.py): pass

when a user granted auto-mount create in a project registers one of its folders, the auto-mount naming that folder comes back

Given

- a project with one vfolder and one user granted the CREATE permission on auto-mounts
  - Domain home-1: vfolders of this domain can be placed on local:volume1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Project project-1
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare a user granted the CREATE permission on vfolder auto-mounts in the project
    - Role auto-mount-user-1: applies only within the scope it is granted in
    - Role auto-mount-user-1: CREATE allowed on every vfolder_auto_mount
    - regular user user-1: holds Role auto-mount-user-1

When

- VFolderAutoMountAdapter.create: user-1 auto-mounts the folder-1 vfolder of the project-1 project at /home/work/extra

Then

- the whole live auto-mount comes back
  - id: same as the entity_id
  - scope_type = 'project'
  - scope_id: same as the project the folder is in
  - vfolder_id: same as the auto-mounted vfolder
  - mount_destination = '/home/work/extra'
  - subpath = '.'
  - mount_permission = 'ro'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-register-an-auto-mount"></a>

#### [a-user-granted-nothing-may-not-register-an-auto-mount](/tests/scenario/bai_scenario/manager/vfolder_auto_mount/test_creating.py): pass

when a user granted nothing tries to register an auto-mount, it is rejected for lack of permission

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

- VFolderAutoMountAdapter.create: user-1 auto-mounts the folder-1 vfolder of the project-1 project at /home/work/extra

Then

- the call is rejected
  - rejected: NotEnoughPermission

