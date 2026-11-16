## storage_host

[어댑터](/src/ai/backend/manager/api/adapters/storage_host/adapter.py)

시나리오: 완성

- 직접 구현 (1)
  - my_storage_host_permissions: 성공 있음 2 · 거부 있음 1 (scope)

**my_storage_host_permissions**

| 시나리오 | 판정 |
|---|---|
| [자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 저장소 호스트 권한을 조회하면, 도메인이 허용하지만 저장소에 등록되지 않은 호스트는 빠지고 등록된 호스트만 응답으로 옵니다](#storage_host-a-user-granted-vfolder-read-sees-only-the-registered-host) | 성공 |
| [허용된 호스트가 저장소에 하나도 등록되어 있지 않은 사용자가 저장소 호스트 권한을 조회하면, 응답은 비어 있습니다](#storage_host-a-user-whose-only-allowed-host-is-unregistered-sees-none) | 성공 |
| [아무 권한도 받지 않은 사용자가 저장소 호스트 권한을 조회하려 하면 권한 부족으로 거부됩니다](#storage_host-a-user-granted-nothing-may-not-list-their-storage-hosts) | 거부 |

### my_storage_host_permissions

<a id="storage_host-a-user-granted-vfolder-read-sees-only-the-registered-host"></a>

#### [a-user-granted-vfolder-read-sees-only-the-registered-host](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

자기 스코프에서 vfolder 읽기 권한을 받은 사용자가 저장소 호스트 권한을 조회하면, 도메인이 허용하지만 저장소에 등록되지 않은 호스트는 빠지고 등록된 호스트만 응답으로 옵니다

Given

- 도메인이 local:volume1, local:volume2 를 허용하고 키페어 정책이 local:volume1 를 허용하는 자리의, vfolder 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1, local:volume2에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 스코프에서 vfolder READ 권한을 받은 사용자 준비
    - 역할 storage-host-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-host-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-host-reader-1 보유

When

- StorageHostAdapter.my_storage_host_permissions: user-1이 자기 저장소 호스트 권한을 조회합니다

Then

- local:volume1 만 응답으로 옵니다
  - items.length = 1
  - items[0].host = 'local:volume1'
  - items[0].permissions = [<VFolderHostPermission.CREATE: 'create-vfolder'>, <VFolderHostPermission.DELETE: 'delete-vfolder'>, <VFolderHostPermission.DOWNLOAD_FILE: 'download-file'>, <VFolderHostPermission.INVITE_OTHERS: 'invite-others'>, <VFolderHostPermission.MODIFY: 'modify-vfolder'>, <VFolderHostPermission.MOUNT_IN_SESSION: 'mount-in-session'>, <VFolderHostPermission.SET_USER_PERM: 'set-user-specific-permission'>, <VFolderHostPermission.UPLOAD_FILE: 'upload-file'>]

<a id="storage_host-a-user-whose-only-allowed-host-is-unregistered-sees-none"></a>

#### [a-user-whose-only-allowed-host-is-unregistered-sees-none](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

허용된 호스트가 저장소에 하나도 등록되어 있지 않은 사용자가 저장소 호스트 권한을 조회하면, 응답은 비어 있습니다

Given

- 도메인이 local:volume2 를 허용하고 키페어 정책이 local:volume2 를 허용하는 자리의, vfolder 읽기 권한을 받은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume2에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume2에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
  - 자기 스코프에서 vfolder READ 권한을 받은 사용자 준비
    - 역할 storage-host-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-host-reader-1: vfolder 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-host-reader-1 보유

When

- StorageHostAdapter.my_storage_host_permissions: user-1이 자기 저장소 호스트 권한을 조회합니다

Then

- 응답은 비어 있습니다
  - items.length = 0

<a id="storage_host-a-user-granted-nothing-may-not-list-their-storage-hosts"></a>

#### [a-user-granted-nothing-may-not-list-their-storage-hosts](/tests/scenario/bai_scenario/manager/storage_host/test_storage_host.py): pass

아무 권한도 받지 않은 사용자가 저장소 호스트 권한을 조회하려 하면 권한 부족으로 거부됩니다

Given

- 도메인이 local:volume1, local:volume2 를 허용하고 키페어 정책이 local:volume1 를 허용하는 자리의, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1: 이 도메인의 vfolder 는 local:volume1, local:volume2에 놓을 수 있습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지, vfolder 는 local:volume1에 놓을 수 있습니다
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageHostAdapter.my_storage_host_permissions: user-1이 자기 저장소 호스트 권한을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

