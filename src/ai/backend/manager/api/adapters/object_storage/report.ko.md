## object_storage

[배경](/src/ai/backend/manager/api/adapters/object_storage/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/object_storage/adapter.py)

시나리오: 완성

- ops 구성 (8)
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
  - create: 대표 성공 ✓ · 대표 거부 ✓
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (2)
  - get_presigned_download_url: 성공 있음 1 · 거부 있음 3 (single_field)
  - get_presigned_upload_url: 성공 있음 1 · 거부 있음 1 (single_field)

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 이름으로 거르고 이름 오름차순으로 정렬해 한 쪽을 요청하면 그 이름의 object storage 하나만 반환됩니다. 이 호출은 전역 역할을 검사합니다](#searching-filtering-by-name-leaves-only-the-matching-object-storage) | 성공 |
| [superadmin 이 아닌 사용자가 object storage 를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-object-storages) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [object storage 조회 권한을 받은 사용자가 미리 저장한 object storage 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 저장된 secret key 는 반환되지 않습니다](#reading-a-user-granted-read-reads-several-object-storages-in-the-requested-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 를 만들면 만든 object storage 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다](#creating-the-superadmin-creates-an-object-storage) | 성공 |
| [superadmin 이 아닌 사용자가 object storage 를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-an-object-storage) | 거부 |

**get**

| 시나리오 | 판정 |
|---|---|
| [object storage 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 object storage 가 반환되고, 저장된 secret key 는 반환되지 않습니다](#reading-a-user-granted-read-gets-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 하나를 조회하면 권한 부족으로 거부됩니다](#reading-a-user-granted-nothing-may-not-get-an-object-storage) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 둘과 없는 id 하나를 한 번에 purge 하면 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages) | 거부 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 여럿의 호스트를 한 번에 변경하면 모두 새 호스트로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 수정하려 하면 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 object storage 를 purge 하면 purge 한 것의 id 가 반환됩니다](#purging-the-superadmin-purges-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 를 purge 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-an-object-storage) | 거부 |
| [superadmin 이 존재하지 않는 id 를 purge 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#purging-purging-an-object-storage-id-nothing-answers-to-is-not-found) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 호스트만 변경하면 호스트는 새 값이 되고 나머지는 그대로 남습니다](#editing-the-superadmin-changes-the-host-of-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 를 수정하면 권한 부족으로 거부됩니다. object storage 는 global 에만 속해 그 권한을 받을 방법이 없습니다](#editing-a-user-granted-nothing-may-not-edit-an-object-storage) | 거부 |
| [superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다](#editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found) | 거부 |

**get_presigned_download_url**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 사용 가능한 리비전의 객체를 내려받을 URL 을 요청하면 그 객체의 저장 경로로 만든 URL 이 반환됩니다](#presigned_urls-the-superadmin-gets-a-download-url-for-an-available-revision) | 성공 |
| [사용 가능 상태가 아닌 리비전의 객체를 내려받을 URL 을 요청하면 승인되지 않았다는 이유로 거부됩니다](#presigned_urls-downloading-an-unavailable-revision-is-refused) | 거부 |
| [전역 설정의 reservoir 가 오브젝트 스토리지가 아니면 내려받기 URL 을 요청해도 발급되지 않고 지원하지 않는 저장소라는 이유로 거부됩니다](#presigned_urls-downloading-from-a-vfs-reservoir-is-refused) | 거부 |
| [전역 설정에 reservoir 가 없으면 내려받기 URL 을 요청해도 발급되지 않고 서버 설정이 잘못됐다는 이유로 거부됩니다](#presigned_urls-downloading-with-no-reservoir-config-is-refused) | 거부 |

**get_presigned_upload_url**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 쓸 수 있는 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 그 객체의 저장 경로로 만든 URL 과 올릴 때 붙일 값이 반환됩니다](#presigned_urls-the-superadmin-gets-an-upload-url-for-a-writable-artifact) | 성공 |
| [읽기 전용 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 쓸 수 없다는 이유로 거부됩니다](#presigned_urls-uploading-to-a-readonly-artifact-is-refused) | 거부 |

### admin_search

<a id="searching-filtering-by-name-leaves-only-the-matching-object-storage"></a>

#### [filtering-by-name-leaves-only-the-matching-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_searching.py): pass

superadmin 이 이름으로 거르고 이름 오름차순으로 정렬해 한 쪽을 요청하면 그 이름의 object storage 하나만 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 2개와, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.admin_search: user-1이 이름으로 object storage 를 거르고 이름 오름차순으로 정렬해 한 쪽을 요청합니다

Then

- 이름이 일치하는 object storage 만 반환됩니다
  - items: 미리 저장한 object storage 와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-object-storages"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_searching.py): pass

superadmin 이 아닌 사용자가 object storage 를 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.admin_search: user-1이 이름으로 object storage 를 거르고 이름 오름차순으로 정렬해 한 쪽을 요청합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-a-user-granted-read-reads-several-object-storages-in-the-requested-order"></a>

#### [a-user-granted-read-reads-several-object-storages-in-the-requested-order](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

object storage 조회 권한을 받은 사용자가 미리 저장한 object storage 둘을 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 저장된 secret key 는 반환되지 않습니다

Given

- object storage 2개와, object storage 에 READ 권한을 받은 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - global 에서 object storage 에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 storage-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-keeper-1: object_storage 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-keeper-1 보유

When

- ObjectStorageAdapter.batch_load_by_ids: user-1이 미리 저장한 object storage 둘을 한 번에 조회합니다

Then

- 미리 저장한 object storage 는 요청한 순서대로 반환되고, secret key 는 '*****' 로 반환됩니다
  - length = 2
  - [0].id: 미리 저장한 object storage 와 같다
  - [0].entity_id: 미리 저장한 object storage 와 같다
  - [0].name = 'object-storage-1'
  - [0].host = 'seeded.object-storage.test'
  - [0].access_key = 'seeded-access-key'
  - [0].secret_key = '*****'
  - [0].endpoint = 'http://seeded.object-storage.test'
  - [0].region = 'seeded-region'
  - [1].id: 미리 저장한 object storage 와 같다
  - [1].entity_id: 미리 저장한 object storage 와 같다
  - [1].name = 'object-storage-2'
  - [1].host = 'seeded.object-storage.test'
  - [1].access_key = 'seeded-access-key'
  - [1].secret_key = '*****'
  - [1].endpoint = 'http://seeded.object-storage.test'
  - [1].region = 'seeded-region'

<a id="reading-a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

아무 권한도 받지 않은 사용자가 object storage id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.batch_load_by_ids: user-1이 미리 저장한 object storage 둘을 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 2
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### create

<a id="creating-the-superadmin-creates-an-object-storage"></a>

#### [the-superadmin-creates-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_creating.py): pass

superadmin 이 object storage 를 만들면 만든 object storage 전체가 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.create: user-1이 object storage 를 만듭니다

Then

- 만든 object storage 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'made-object-storage'
  - host = 'made.object-storage.test'
  - access_key = 'made-access-key'
  - secret_key = 'made-secret-key'
  - endpoint = 'https://made.object-storage.test'
  - region = 'made-region'

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-an-object-storage"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_creating.py): pass

superadmin 이 아닌 사용자가 object storage 를 만들려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.create: user-1이 object storage 를 만듭니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### get

<a id="reading-a-user-granted-read-gets-an-object-storage"></a>

#### [a-user-granted-read-gets-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

object storage 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 object storage 가 반환되고, 저장된 secret key 는 반환되지 않습니다

Given

- object storage 하나와, object storage 에 READ 권한을 받은 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - global 에서 object storage 에 READ 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 storage-keeper-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 storage-keeper-1: object_storage 전체에 READ 허용
    - 일반 사용자 user-1: 역할 storage-keeper-1 보유

When

- ObjectStorageAdapter.get: user-1이 object-storage-1을 조회합니다

Then

- 미리 저장한 object storage 가 반환되고, secret key 는 '*****' 로 반환됩니다
  - id: 미리 저장한 object storage 와 같다
  - entity_id: 미리 저장한 object storage 와 같다
  - name = 'object-storage-1'
  - host = 'seeded.object-storage.test'
  - access_key = 'seeded-access-key'
  - secret_key = '*****'
  - endpoint = 'http://seeded.object-storage.test'
  - region = 'seeded-region'

<a id="reading-a-user-granted-nothing-may-not-get-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-get-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_reading.py): pass

아무 권한도 받지 않은 사용자가 object storage 하나를 조회하면 권한 부족으로 거부됩니다

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

- ObjectStorageAdapter.get: user-1이 object-storage-1을 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-object-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py): pass

superadmin 이 object storage 둘과 없는 id 하나를 한 번에 purge 하면 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- object storage 2개와, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.partial_bulk_purge: user-1 이 object storage 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 대상 object storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 미리 저장한 object storage 와 같다
  - successes[0].entity_id: 미리 저장한 object storage 와 같다
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'seeded.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: 미리 저장한 object storage 와 같다
  - successes[1].entity_id: 미리 저장한 object storage 와 같다
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'seeded.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.partial_bulk_purge: user-1 이 object storage 2개를 한 번에 purge 합니다

Then

- 처리된 object storage 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 object storage 의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 object storage 의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### partial_bulk_update

<a id="partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once"></a>

#### [the-superadmin-edits-several-object-storages-at-once](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py): pass

superadmin 이 object storage 여럿의 호스트를 한 번에 변경하면 모두 새 호스트로 오고 실패한 것은 없습니다

Given

- object storage 2개와, superadmin 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.partial_bulk_update: user-1 이 object storage 2개의 호스트를 한 번에 수정합니다

Then

- 대상 object storage 가 모두 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 미리 저장한 object storage 와 같다
  - successes[0].entity_id: 미리 저장한 object storage 와 같다
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'moved.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: 미리 저장한 object storage 와 같다
  - successes[1].entity_id: 미리 저장한 object storage 와 같다
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'moved.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed = []

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 수정하려 하면 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트는 seeded.object-storage.test 입니다
  - object storage object-storage-2: 호스트는 seeded.object-storage.test 입니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.partial_bulk_update: user-1 이 object storage 2개의 호스트를 한 번에 수정합니다

Then

- 처리된 object storage 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 object storage 의 id 와 같다
  - 거부: failed[0]: Insufficient permission
  - failed[1].id: 대상 object storage 의 id 와 같다
  - 거부: failed[1]: Insufficient permission

### purge

<a id="purging-the-superadmin-purges-an-object-storage"></a>

#### [the-superadmin-purges-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

superadmin 이 object storage 를 purge 하면 purge 한 것의 id 가 반환됩니다

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

- ObjectStorageAdapter.purge: user-1 이 object-storage-1를 purge 합니다

Then

- purge 한 object storage 의 id 가 반환됩니다
  - id: 미리 저장한 object storage 와 같다
  - entity_id: 미리 저장한 object storage 와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-purge-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

아무 권한도 받지 않은 사용자가 object storage 를 purge 하면 권한 부족으로 거부됩니다

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

- ObjectStorageAdapter.purge: user-1 이 object-storage-1를 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-purging-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py): pass

superadmin 이 존재하지 않는 id 를 purge 하면 대상을 찾을 수 없다는 이유로 거부됩니다

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

- ObjectStorageAdapter.purge: user-1 이 존재하지 않는 id 를 purge 합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### update

<a id="editing-the-superadmin-changes-the-host-of-an-object-storage"></a>

#### [the-superadmin-changes-the-host-of-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

superadmin 이 호스트만 변경하면 호스트는 새 값이 되고 나머지는 그대로 남습니다

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

- ObjectStorageAdapter.update: user-1 이 object-storage-1의 호스트를 수정합니다

Then

- 미리 저장한 object storage 전체가 반환됩니다
  - id: 미리 저장한 object storage 와 같다
  - entity_id: 미리 저장한 object storage 와 같다
  - name = 'object-storage-1'
  - host = 'moved.object-storage.test'
  - access_key = 'seeded-access-key'
  - secret_key = 'seeded-secret-key'
  - endpoint = 'http://seeded.object-storage.test'
  - region = 'seeded-region'

<a id="editing-a-user-granted-nothing-may-not-edit-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-edit-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

아무 권한도 받지 않은 사용자가 object storage 를 수정하면 권한 부족으로 거부됩니다. object storage 는 global 에만 속해 그 권한을 받을 방법이 없습니다

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

- ObjectStorageAdapter.update: user-1 이 object-storage-1의 호스트를 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py): pass

superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다

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

- ObjectStorageAdapter.update: user-1 이 존재하지 않는 id 의 호스트를 수정합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### get_presigned_download_url

<a id="presigned_urls-the-superadmin-gets-a-download-url-for-an-available-revision"></a>

#### [the-superadmin-gets-a-download-url-for-an-available-revision](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

superadmin 이 사용 가능한 리비전의 객체를 내려받을 URL 을 요청하면 그 객체의 저장 경로로 만든 URL 이 반환됩니다

Given

- 쓸 수 있는 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_download_url: user-1이 리비전의 model.bin 객체를 내려받을 URL 을 요청합니다

Then

- 그 객체의 저장 경로로 만든 내려받기 URL 이 반환됩니다
  - presigned_url = 'https://presigned.scenario.local/download/artifact-1/1.0/model.bin'

<a id="presigned_urls-downloading-an-unavailable-revision-is-refused"></a>

#### [downloading-an-unavailable-revision-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

사용 가능 상태가 아닌 리비전의 객체를 내려받을 URL 을 요청하면 승인되지 않았다는 이유로 거부됩니다

Given

- 쓸 수 있는 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_download_url: user-1이 리비전의 model.bin 객체를 내려받을 URL 을 요청합니다

Then

- 거부됩니다
  - 거부: ArtifactRevisionNotApproved

<a id="presigned_urls-downloading-from-a-vfs-reservoir-is-refused"></a>

#### [downloading-from-a-vfs-reservoir-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

전역 설정의 reservoir 가 오브젝트 스토리지가 아니면 내려받기 URL 을 요청해도 발급되지 않고 지원하지 않는 저장소라는 이유로 거부됩니다

Given

- 쓸 수 있는 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_download_url: user-1이 리비전의 model.bin 객체를 내려받을 URL 을 요청합니다

Then

- 거부됩니다
  - 거부: ObjectStorageOperationNotSupported

<a id="presigned_urls-downloading-with-no-reservoir-config-is-refused"></a>

#### [downloading-with-no-reservoir-config-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

전역 설정에 reservoir 가 없으면 내려받기 URL 을 요청해도 발급되지 않고 서버 설정이 잘못됐다는 이유로 거부됩니다

Given

- 쓸 수 있는 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_download_url: user-1이 리비전의 model.bin 객체를 내려받을 URL 을 요청합니다

Then

- 거부됩니다
  - 거부: ServerMisconfiguredError

### get_presigned_upload_url

<a id="presigned_urls-the-superadmin-gets-an-upload-url-for-a-writable-artifact"></a>

#### [the-superadmin-gets-an-upload-url-for-a-writable-artifact](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

superadmin 이 쓸 수 있는 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 그 객체의 저장 경로로 만든 URL 과 올릴 때 붙일 값이 반환됩니다

Given

- 쓸 수 있는 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_upload_url: user-1이 리비전에 model.bin 객체를 올릴 URL 을 요청합니다

Then

- 그 객체의 저장 경로로 만든 올리기 URL 과 함께 올릴 때 붙일 값이 반환됩니다
  - presigned_url = 'https://presigned.scenario.local/upload/artifact-1/1.0/model.bin'
  - fields = {'policy': 'seeded-policy'}

<a id="presigned_urls-uploading-to-a-readonly-artifact-is-refused"></a>

#### [uploading-to-a-readonly-artifact-is-refused](/tests/scenario/bai_scenario/manager/object_storage/test_presigned_urls.py): pass

읽기 전용 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 쓸 수 없다는 이유로 거부됩니다

Given

- 읽기 전용 artifact 하나와 그 리비전 하나, superadmin 한 명
  - object storage archive-storage: 호스트는 seeded.object-storage.test 입니다
  - 저장소 네임스페이스 archive-bucket: 오브젝트 스토리지에 등록된 버킷 이름입니다
  - 아티팩트 artifact-1: 허깅 페이스 레지스트리에서 스캔한 모델
  - 아티팩트 artifact-1: 아티팩트 리비전
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- ObjectStorageAdapter.get_presigned_upload_url: user-1이 리비전에 model.bin 객체를 올릴 URL 을 요청합니다

Then

- 거부됩니다
  - 거부: ArtifactReadonly

