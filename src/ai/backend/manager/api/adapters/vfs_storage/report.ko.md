## vfs_storage

[배경](/src/ai/backend/manager/api/adapters/vfs_storage/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfs_storage/adapter.py)

시나리오: 완성

- ops 구성 (9)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - list_all: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [VFS storage 조회 권한을 받은 사용자가 미리 저장한 VFS storage 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환됩니다](#reading-a-user-granted-read-reads-several-vfs-storages-in-the-requested-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 를 만들면 만든 VFS storage 전체가 반환됩니다](#creating-the-superadmin-creates-a-vfs-storage) | 성공 |
| [superadmin 이 아닌 사용자가 VFS storage 를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [VFS storage 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 VFS storage 전체가 반환됩니다](#reading-a-user-granted-read-gets-a-vfs-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 하나를 조회하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-get-a-vfs-storage) | 거부 |

**list_all**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 전체 목록을 읽으면 미리 저장한 VFS storage 가 모두 반환됩니다](#searching-the-superadmin-listing-vfs-storages-gets-every-one) | 성공 |
| [superadmin 이 아닌 사용자가 VFS storage 전체 목록을 읽으려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다](#searching-a-user-who-is-not-the-superadmin-may-not-list-vfs-storages) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 여럿의 기본 경로를 한 번에 변경하면, 모두 새 기본 경로로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 를 purge 하면 purge 한 것의 id 가 반환됩니다](#purging-the-superadmin-purges-a-vfs-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 를 purge 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-a-vfs-storage) | 거부 |
| [superadmin 이 존재하지 않는 id 를 purge 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 VFS storage 를 검색해 한 쪽을 요청하면 미리 저장한 VFS storage 둘 가운데 하나만 오고, 전체 개수는 둘입니다](#searching-the-superadmin-searching-vfs-storages-gets-one-page) | 성공 |
| [superadmin 이 아닌 사용자가 VFS storage 를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-vfs-storages) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 기본 경로만 변경하면, 기본 경로는 새 값이 되고 나머지는 그대로 남습니다](#editing-the-superadmin-changes-the-base-path-of-a-vfs-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 를 수정하면 권한 부족으로 거부됩니다. VFS storage 는 global 에만 속해 그 권한을 받을 방법이 없습니다](#editing-a-user-granted-nothing-may-not-edit-a-vfs-storage) | 거부 |
| [superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다](#editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found) | 거부 |

### batch_load_by_ids

<a id="reading-a-user-granted-read-reads-several-vfs-storages-in-the-requested-order"></a>

#### [a-user-granted-read-reads-several-vfs-storages-in-the-requested-order](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

VFS storage 조회 권한을 받은 사용자가 미리 저장한 VFS storage 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환됩니다

Given

- VFS storage 2개와, VFS storage 에 READ 권한을 받은 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - global 에서 VFS storage 에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 storage-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-keeper-1: vfs_storage 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-keeper-1 보유

When

- VFSStorageAdapter.batch_load_by_ids: user-1이 미리 저장한 VFS storage 둘을 한 번에 조회합니다

Then

- 미리 저장한 VFS storage 는 요청한 순서대로 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 VFS storage 와 같다
  - [0].entity_id: 미리 저장한 VFS storage 와 같다
  - [0].name = 'vfs-storage-1'
  - [0].host = 'seeded-host'
  - [0].base_path = '/seeded/vfs-storage'
  - [1].id: 미리 저장한 VFS storage 와 같다
  - [1].entity_id: 미리 저장한 VFS storage 와 같다
  - [1].name = 'vfs-storage-2'
  - [1].host = 'seeded-host'
  - [1].base_path = '/seeded/vfs-storage'

<a id="reading-a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

아무 권한도 받지 않은 사용자가 VFS storage id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.batch_load_by_ids: user-1이 미리 저장한 VFS storage 둘을 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-a-vfs-storage"></a>

#### [the-superadmin-creates-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_creating.py): pass

superadmin 이 VFS storage 를 만들면 만든 VFS storage 전체가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.create: user-1이 VFS storage 를 만듭니다

Then

- 만든 VFS storage 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'made-vfs-storage'
  - host = 'made-host'
  - base_path = '/made/vfs-storage'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_creating.py): pass

superadmin 이 아닌 사용자가 VFS storage 를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.create: user-1이 VFS storage 를 만듭니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### get

<a id="reading-a-user-granted-read-gets-a-vfs-storage"></a>

#### [a-user-granted-read-gets-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

VFS storage 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 VFS storage 전체가 반환됩니다

Given

- VFS storage 하나와, VFS storage 에 READ 권한을 받은 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - global 에서 VFS storage 에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 storage-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-keeper-1: vfs_storage 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-keeper-1 보유

When

- VFSStorageAdapter.get: user-1이 vfs-storage-1을 조회합니다

Then

- 미리 저장한 VFS storage 전체가 반환됩니다
  - id: 미리 저장한 VFS storage 와 같다
  - entity_id: 미리 저장한 VFS storage 와 같다
  - name = 'vfs-storage-1'
  - host = 'seeded-host'
  - base_path = '/seeded/vfs-storage'

<a id="reading-a-user-granted-nothing-may-not-get-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-get-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_reading.py): pass

아무 권한도 받지 않은 사용자가 VFS storage 하나를 조회하면 권한 부족으로 거부됩니다

Given

- VFS storage 하나와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.get: user-1이 vfs-storage-1을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### list_all

<a id="searching-the-superadmin-listing-vfs-storages-gets-every-one"></a>

#### [the-superadmin-listing-vfs-storages-gets-every-one](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

superadmin 이 VFS storage 전체 목록을 읽으면 미리 저장한 VFS storage 가 모두 반환됩니다

Given

- VFS storage 2개와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.list_all: user-1이 VFS storage 전체 목록을 읽습니다

Then

- 미리 저장한 VFS storage 가 모두 순서 없이 반환됩니다
  - items: 미리 저장한 VFS storage 와 같다

<a id="searching-a-user-who-is-not-the-superadmin-may-not-list-vfs-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-list-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

superadmin 이 아닌 사용자가 VFS storage 전체 목록을 읽으려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.list_all: user-1이 VFS storage 전체 목록을 읽습니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-vfs-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py): pass

superadmin 이 VFS storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- VFS storage 2개와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.partial_bulk_purge: user-1이 VFS storage 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 대상 VFS storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 VFS storage 와 같다
  - successes[0].entity_id: 미리 저장한 VFS storage 와 같다
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/seeded/vfs-storage'
  - successes[1].id: 미리 저장한 VFS storage 와 같다
  - successes[1].entity_id: 미리 저장한 VFS storage 와 같다
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/seeded/vfs-storage'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.partial_bulk_purge: user-1이 VFS storage 2개를 한 번에 purge 합니다

Then

- 처리된 VFS storage 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 VFS storage 의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 VFS storage 의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### partial_bulk_update

<a id="partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once"></a>

#### [the-superadmin-edits-several-vfs-storages-at-once](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py): pass

superadmin 이 VFS storage 여럿의 기본 경로를 한 번에 변경하면, 모두 새 기본 경로로 오고 실패한 것은 없습니다

Given

- VFS storage 2개와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.partial_bulk_update: user-1이 VFS storage 2개의 기본 경로를 한 번에 수정합니다

Then

- 대상 VFS storage 가 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 VFS storage 와 같다
  - successes[0].entity_id: 미리 저장한 VFS storage 와 같다
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/moved/vfs-storage'
  - successes[1].id: 미리 저장한 VFS storage 와 같다
  - successes[1].entity_id: 미리 저장한 VFS storage 와 같다
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/moved/vfs-storage'
  - failed = []

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 수정하려 하면, 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.partial_bulk_update: user-1이 VFS storage 2개의 기본 경로를 한 번에 수정합니다

Then

- 처리된 VFS storage 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 VFS storage 의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 VFS storage 의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### purge

<a id="purging-the-superadmin-purges-a-vfs-storage"></a>

#### [the-superadmin-purges-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

superadmin 이 VFS storage 를 purge 하면 purge 한 것의 id 가 반환됩니다

Given

- VFS storage 하나와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.purge: user-1이 vfs-storage-1 를 purge 합니다

Then

- purge 한 VFS storage 의 id 가 반환됩니다
  - id: 미리 저장한 VFS storage 와 같다
  - entity_id: 미리 저장한 VFS storage 와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-purge-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

아무 권한도 받지 않은 사용자가 VFS storage 를 purge 하면 권한 부족으로 거부됩니다

Given

- VFS storage 하나와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.purge: user-1이 vfs-storage-1 를 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py): pass

superadmin 이 존재하지 않는 id 를 purge 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- VFS storage 하나와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.purge: user-1이 존재하지 않는 id 를 purge 합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search

<a id="searching-the-superadmin-searching-vfs-storages-gets-one-page"></a>

#### [the-superadmin-searching-vfs-storages-gets-one-page](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

superadmin 이 VFS storage 를 검색해 한 쪽을 요청하면 미리 저장한 VFS storage 둘 가운데 하나만 오고, 전체 개수는 둘입니다

Given

- VFS storage 2개와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.search: user-1이 VFS storage 를 검색해 한 쪽을 요청합니다

Then

- 미리 저장한 VFS storage 둘 가운데 하나만 한 쪽에 오고, 남은 하나는 다음 쪽에 있습니다
  - length = 1
  - items: 미리 저장한 VFS storage 가운데 하나
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-vfs-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_searching.py): pass

superadmin 이 아닌 사용자가 VFS storage 를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.search: user-1이 VFS storage 를 검색해 한 쪽을 요청합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### update

<a id="editing-the-superadmin-changes-the-base-path-of-a-vfs-storage"></a>

#### [the-superadmin-changes-the-base-path-of-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

superadmin 이 기본 경로만 변경하면, 기본 경로는 새 값이 되고 나머지는 그대로 남습니다

Given

- VFS storage 하나와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.update: user-1이 vfs-storage-1 의 기본 경로를 수정합니다

Then

- 미리 저장한 VFS storage 전체가 반환됩니다
  - id: 미리 저장한 VFS storage 와 같다
  - entity_id: 미리 저장한 VFS storage 와 같다
  - name = 'vfs-storage-1'
  - host = 'seeded-host'
  - base_path = '/moved/vfs-storage'

<a id="editing-a-user-granted-nothing-may-not-edit-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-edit-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

아무 권한도 받지 않은 사용자가 VFS storage 를 수정하면 권한 부족으로 거부됩니다. VFS storage 는 global 에만 속해 그 권한을 받을 방법이 없습니다

Given

- VFS storage 하나와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.update: user-1이 vfs-storage-1 의 기본 경로를 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py): pass

superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- VFS storage 하나와, superadmin 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- VFSStorageAdapter.update: user-1이 존재하지 않는 id 의 기본 경로를 수정합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

