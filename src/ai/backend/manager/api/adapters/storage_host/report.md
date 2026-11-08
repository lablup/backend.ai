## storage_host

[adapter](/src/ai/backend/manager/api/adapters/storage_host/adapter.py)

Scenario: complete

- direct implementation (1)
  - my_storage_host_permissions: success present 2 · rejection present 1 (scope)

**my_storage_host_permissions**

| scenario | verdict |
|---|---|
| [when a user granted vfolder read in their own scope lists their storage hosts, a host the domain allows but no storage registers is left out and only the registered host comes back](#storage_host-a-user-granted-vfolder-read-sees-only-the-registered-host) | answered |
| [when every host the user may use is unregistered with the storage, listing the storage hosts comes back empty](#storage_host-a-user-whose-only-allowed-host-is-unregistered-sees-none) | answered |
| [when a user granted nothing tries to list their storage hosts, it is rejected for lack of permission](#storage_host-a-user-granted-nothing-may-not-list-their-storage-hosts) | rejected |

### my_storage_host_permissions

<a id="storage_host-a-user-granted-vfolder-read-sees-only-the-registered-host"></a>

#### [a-user-granted-vfolder-read-sees-only-the-registered-host](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

when a user granted vfolder read in their own scope lists their storage hosts, a host the domain allows but no storage registers is left out and only the registered host comes back

Given

- one user granted vfolder read in their own scope in a place where the domain allows local:volume1, local:volume2 and the keypair policy allows local:volume1
  - Domain home-1: vfolders of this domain can be placed on local:volume1, local:volume2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ permission on vfolders in their own scope
    - Role storage-host-reader-1: applies only within the scope it is granted in
    - Role storage-host-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role storage-host-reader-1

When

- StorageHostAdapter.my_storage_host_permissions: user-1 lists the storage host permissions they hold

Then

- only local:volume1 come back
  - items.length = 1
  - items[0].host = 'local:volume1'
  - items[0].permissions = [<VFolderHostPermission.CREATE: 'create-vfolder'>, <VFolderHostPermission.DELETE: 'delete-vfolder'>, <VFolderHostPermission.DOWNLOAD_FILE: 'download-file'>, <VFolderHostPermission.INVITE_OTHERS: 'invite-others'>, <VFolderHostPermission.MODIFY: 'modify-vfolder'>, <VFolderHostPermission.MOUNT_IN_SESSION: 'mount-in-session'>, <VFolderHostPermission.SET_USER_PERM: 'set-user-specific-permission'>, <VFolderHostPermission.UPLOAD_FILE: 'upload-file'>]

<a id="storage_host-a-user-whose-only-allowed-host-is-unregistered-sees-none"></a>

#### [a-user-whose-only-allowed-host-is-unregistered-sees-none](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

when every host the user may use is unregistered with the storage, listing the storage hosts comes back empty

Given

- one user granted vfolder read in their own scope in a place where the domain allows local:volume2 and the keypair policy allows local:volume2
  - Domain home-1: vfolders of this domain can be placed on local:volume2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume2
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ permission on vfolders in their own scope
    - Role storage-host-reader-1: applies only within the scope it is granted in
    - Role storage-host-reader-1: READ allowed on every vfolder
    - regular user user-1: holds Role storage-host-reader-1

When

- StorageHostAdapter.my_storage_host_permissions: user-1 lists the storage host permissions they hold

Then

- the answer is empty
  - items.length = 0

<a id="storage_host-a-user-granted-nothing-may-not-list-their-storage-hosts"></a>

#### [a-user-granted-nothing-may-not-list-their-storage-hosts](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

when a user granted nothing tries to list their storage hosts, it is rejected for lack of permission

Given

- one user holding no permission in a place where the domain allows local:volume1, local:volume2 and the keypair policy allows local:volume1
  - Domain home-1: vfolders of this domain can be placed on local:volume1, local:volume2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-1: has their own keypair and personal project

When

- StorageHostAdapter.my_storage_host_permissions: user-1 lists the storage host permissions they hold

Then

- the call is rejected
  - rejected: NotEnoughPermission

