## storage_namespace

[어댑터](/src/ai/backend/manager/api/adapters/storage_namespace/adapter.py)

시나리오: 완성

- ops 구성 (5)
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - get_namespaces: 대표 성공 ✓ · 대표 거부 ✓
  - register: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✓
  - unregister: 대표 성공 ✓ · 대표 거부 ✓

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 네임스페이스 둘과 존재하지 않는 id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다](#reading-the-superadmin-reads-several-namespaces-in-the-requested-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 네임스페이스 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id) | 거부 |

**get_namespaces**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 에 등록된 네임스페이스를 읽으면 등록된 네임스페이스가 모두 반환됩니다](#reading-the-superadmin-reads-every-namespace-of-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 의 네임스페이스를 읽으려 하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage) | 거부 |

**register**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 에 네임스페이스를 등록하면 등록한 네임스페이스 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다](#registering-the-superadmin-registers-a-namespace-on-an-object-storage) | 성공 |
| [superadmin 이 아닌 사용자가 네임스페이스를 등록하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#registering-a-user-who-is-not-the-superadmin-may-not-register-a-namespace) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 네임스페이스를 검색하면 미리 저장한 네임스페이스가 모두 반환됩니다. 이 호출은 전역 역할을 검사합니다](#searching-the-superadmin-searching-namespaces-counts-every-one) | 성공 |
| [superadmin 이 아닌 사용자가 네임스페이스를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-namespaces) | 거부 |

**unregister**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 네임스페이스를 빼면 그 네임스페이스가 있던 object storage 의 id 가 반환됩니다](#unregistering-the-superadmin-unregisters-a-namespace-from-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 네임스페이스를 빼려 하면 거부됩니다. 이 호출은 네임스페이스를 먼저 찾아 읽어야 하므로, 읽을 수 없는 대상은 있는지도 드러나지 않습니다](#unregistering-a-user-granted-nothing-may-not-unregister-a-namespace) | 거부 |
| [superadmin 이 등록되지 않은 네임스페이스를 빼려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#unregistering-unregistering-a-namespace-nothing-answers-to-is-not-found) | 거부 |

### batch_load_by_ids

<a id="reading-the-superadmin-reads-several-namespaces-in-the-requested-order"></a>

#### [the-superadmin-reads-several-namespaces-in-the-requested-order](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

superadmin 이 미리 저장한 네임스페이스 둘과 존재하지 않는 id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.batch_load_by_ids: user-1이 미리 저장한 네임스페이스 둘과 존재하지 않는 id 하나를 한 번에 조회합니다

Then

- 미리 저장한 네임스페이스는 요청한 순서대로 반환되고, 존재하지 않는 id 의 항목은 비어 있습니다
  - length = 3
  - [0].id: 미리 저장한 네임스페이스와 같다
  - [0].entity_id: 미리 저장한 네임스페이스와 같다
  - [0].storage_id: 그 네임스페이스가 등록된 object storage 의 id 와 같다
  - [0].namespace = 'seeded-bucket'
  - [1] = None
  - [2].id: 미리 저장한 네임스페이스와 같다
  - [2].entity_id: 미리 저장한 네임스페이스와 같다
  - [2].storage_id: 그 네임스페이스가 등록된 object storage 의 id 와 같다
  - [2].namespace = 'second-bucket'

<a id="reading-a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-namespace-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

아무 권한도 받지 않은 사용자가 네임스페이스 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.batch_load_by_ids: user-1이 미리 저장한 네임스페이스 둘과 존재하지 않는 id 하나를 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### get_namespaces

<a id="reading-the-superadmin-reads-every-namespace-of-an-object-storage"></a>

#### [the-superadmin-reads-every-namespace-of-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

superadmin 이 object storage 에 등록된 네임스페이스를 읽으면 등록된 네임스페이스가 모두 반환됩니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.get_namespaces: user-1이 object-storage-1에 등록된 네임스페이스를 읽습니다

Then

- 그 object storage 에 등록된 네임스페이스가 모두 반환됩니다
  - items: 미리 저장한 네임스페이스와 같다

<a id="reading-a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-read-the-namespaces-of-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_reading.py): pass

아무 권한도 받지 않은 사용자가 object storage 의 네임스페이스를 읽으려 하면 권한 부족으로 거부됩니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.get_namespaces: user-1이 object-storage-1에 등록된 네임스페이스를 읽습니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### register

<a id="registering-the-superadmin-registers-a-namespace-on-an-object-storage"></a>

#### [the-superadmin-registers-a-namespace-on-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_registering.py): pass

superadmin 이 object storage 에 네임스페이스를 등록하면 등록한 네임스페이스 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 하나와, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.register: user-1이 object-storage-1에 네임스페이스를 등록합니다

Then

- 등록한 네임스페이스 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - storage_id: 미리 저장한 object storage 와 같다
  - namespace = 'registered-bucket'

<a id="registering-a-user-who-is-not-the-superadmin-may-not-register-a-namespace"></a>

#### [a-user-who-is-not-the-superadmin-may-not-register-a-namespace](/tests/scenario/bai_scenario/manager/storage_namespace/test_registering.py): pass

superadmin 이 아닌 사용자가 네임스페이스를 등록하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 하나와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.register: user-1이 object-storage-1에 네임스페이스를 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### search

<a id="searching-the-superadmin-searching-namespaces-counts-every-one"></a>

#### [the-superadmin-searching-namespaces-counts-every-one](/tests/scenario/bai_scenario/manager/storage_namespace/test_searching.py): pass

superadmin 이 네임스페이스를 검색하면 미리 저장한 네임스페이스가 모두 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.search: user-1이 등록된 네임스페이스를 검색합니다

Then

- 미리 저장한 네임스페이스가 모두 반환됩니다
  - items: 미리 저장한 네임스페이스와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-namespaces"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-namespaces](/tests/scenario/bai_scenario/manager/storage_namespace/test_searching.py): pass

superadmin 이 아닌 사용자가 네임스페이스를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 둘, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 네임스페이스 둘을 등록한 object storage 준비
    - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
    - 저장소 네임스페이스 second-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.search: user-1이 등록된 네임스페이스를 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### unregister

<a id="unregistering-the-superadmin-unregisters-a-namespace-from-an-object-storage"></a>

#### [the-superadmin-unregisters-a-namespace-from-an-object-storage](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

superadmin 이 네임스페이스를 빼면 그 네임스페이스가 있던 object storage 의 id 가 반환됩니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 하나, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.unregister: user-1이 object-storage-1에서 네임스페이스 seeded-bucket 를 뺍니다

Then

- 네임스페이스를 빼낸 object storage 의 id 가 반환됩니다
  - id: 미리 저장한 object storage 와 같다

<a id="unregistering-a-user-granted-nothing-may-not-unregister-a-namespace"></a>

#### [a-user-granted-nothing-may-not-unregister-a-namespace](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

아무 권한도 받지 않은 사용자가 네임스페이스를 빼려 하면 거부됩니다. 이 호출은 네임스페이스를 먼저 찾아 읽어야 하므로, 읽을 수 없는 대상은 있는지도 드러나지 않습니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 하나, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.unregister: user-1이 object-storage-1에서 네임스페이스 seeded-bucket 를 뺍니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

<a id="unregistering-unregistering-a-namespace-nothing-answers-to-is-not-found"></a>

#### [unregistering-a-namespace-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/storage_namespace/test_unregistering.py): pass

superadmin 이 등록되지 않은 네임스페이스를 빼려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- object storage 하나와 그 아래 등록된 네임스페이스 하나, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 seeded-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- StorageNamespaceAdapter.unregister: user-1이 object-storage-1에서 네임스페이스 missing-bucket 를 뺍니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

