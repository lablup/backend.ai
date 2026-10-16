## object_storage

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/object_storage/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/object_storage/adapter.py)

시나리오: 미완 8 / 10

- ops 로 구성 (8)
  - admin_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - create — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_update — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - purge — 대표 성공 ✓ · 대표 실패 ✓
  - update — 대표 성공 ✓ · 대표 실패 ✓
- 직접 구현 (2)
  - get_presigned_download_url — 성공 없음 · 실패 없음 (single_field) — SCENARIO-GAP
  - get_presigned_upload_url — 성공 없음 · 실패 없음 (single_field) — SCENARIO-GAP

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages) | 성공 |
| [슈퍼관리자가 object storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages) | 성공 |
| [슈퍼관리자가 object storage 여럿의 호스트를 한 번에 바꾸면, 모두 새 호스트로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 object storage 를 purge 하면 purge 한 것의 id 가 반환된다](#purging-the-superadmin-purges-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 를 purge 하면 권한 부족으로 거부된다](#purging-a-user-granted-nothing-may-not-purge-an-object-storage) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 purge 하면 대상을 찾을 수 없다는 이유로 거부된다](#purging-purging-an-object-storage-id-nothing-answers-to-is-not-found) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 호스트만 바꾸면, 호스트는 새 값이 되고 나머지는 그대로 남는다](#editing-the-superadmin-changes-the-host-of-an-object-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 object storage 를 수정하면 권한 부족으로 거부된다. object storage 는 global 에만 속해 그 권한을 받을 방법이 없다](#editing-a-user-granted-nothing-may-not-edit-an-object-storage) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다](#editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found) | 거부 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - object storage object-storage-2: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.partial_bulk_purge — user-1이 object storage 2개를 한 번에 purge

Then

- 처리된 object storage 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 object storage 의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 object storage 의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-object-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-object-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_purging.py) — pass

슈퍼관리자가 object storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- object storage 2개와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - object storage object-storage-2: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.partial_bulk_purge — user-1이 object storage 2개 와 없는 id 하나를 한 번에 purge

Then

- 대상 object storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 object storage와 같다
  - successes[0].entity_id: 미리 만들어 둔 object storage와 같다
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'seeded.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: 미리 만들어 둔 object storage와 같다
  - successes[1].entity_id: 미리 만들어 둔 object storage와 같다
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'seeded.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-object-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-object-storages](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 object storage 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- object storage 2개와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - object storage object-storage-2: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.partial_bulk_update — user-1이 object storage 2개의 호스트를 한 번에 수정

Then

- 처리된 object storage 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 object storage 의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 object storage 의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-object-storages-at-once"></a>

#### [the-superadmin-edits-several-object-storages-at-once](/tests/scenario/bai_scenario/manager/object_storage/test_partial_bulk_editing.py) — pass

슈퍼관리자가 object storage 여럿의 호스트를 한 번에 바꾸면, 모두 새 호스트로 오고 실패한 것은 없다

Given

- object storage 2개와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - object storage object-storage-2: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.partial_bulk_update — user-1이 object storage 2개의 호스트를 한 번에 수정

Then

- 대상 object storage 가 모두 처리된 목록에 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 object storage와 같다
  - successes[0].entity_id: 미리 만들어 둔 object storage와 같다
  - successes[0].name = 'object-storage-1'
  - successes[0].host = 'moved.object-storage.test'
  - successes[0].access_key = 'seeded-access-key'
  - successes[0].secret_key = 'seeded-secret-key'
  - successes[0].endpoint = 'http://seeded.object-storage.test'
  - successes[0].region = 'seeded-region'
  - successes[1].id: 미리 만들어 둔 object storage와 같다
  - successes[1].entity_id: 미리 만들어 둔 object storage와 같다
  - successes[1].name = 'object-storage-2'
  - successes[1].host = 'moved.object-storage.test'
  - successes[1].access_key = 'seeded-access-key'
  - successes[1].secret_key = 'seeded-secret-key'
  - successes[1].endpoint = 'http://seeded.object-storage.test'
  - successes[1].region = 'seeded-region'
  - failed = []

### purge

<a id="purging-the-superadmin-purges-an-object-storage"></a>

#### [the-superadmin-purges-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py) — pass

슈퍼관리자가 object storage 를 purge 하면 purge 한 것의 id 가 반환된다

Given

- object storage 하나와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.purge — user-1이 object-storage-1 purge

Then

- purge 한 object storage 의 id 가 반환된다
  - id: 미리 만들어 둔 object storage와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-purge-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 object storage 를 purge 하면 권한 부족으로 거부된다

Given

- object storage 하나와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.purge — user-1이 object-storage-1 purge

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="purging-purging-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 id를 purge 하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- object storage 하나와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.purge — user-1이 존재하지 않는 id purge

Then

- 거부된다
  - 거부: EntityNotFoundError

### update

<a id="editing-the-superadmin-changes-the-host-of-an-object-storage"></a>

#### [the-superadmin-changes-the-host-of-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py) — pass

슈퍼관리자가 호스트만 바꾸면, 호스트는 새 값이 되고 나머지는 그대로 남는다

Given

- object storage 하나와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.update — user-1이 object-storage-1의 호스트 수정

Then

- 미리 만들어 둔 object storage 전체가 반환된다
  - id: 미리 만들어 둔 object storage와 같다
  - entity_id: 미리 만들어 둔 object storage와 같다
  - name = 'object-storage-1'
  - host = 'moved.object-storage.test'
  - access_key = 'seeded-access-key'
  - secret_key = 'seeded-secret-key'
  - endpoint = 'http://seeded.object-storage.test'
  - region = 'seeded-region'

<a id="editing-a-user-granted-nothing-may-not-edit-an-object-storage"></a>

#### [a-user-granted-nothing-may-not-edit-an-object-storage](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 object storage 를 수정하면 권한 부족으로 거부된다. object storage 는 global 에만 속해 그 권한을 받을 방법이 없다

Given

- object storage 하나와, 일반 사용자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.update — user-1이 object-storage-1의 호스트 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing-the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-an-object-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/object_storage/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- object storage 하나와, 슈퍼관리자 한 명
  - object storage object-storage-1: 호스트가 seeded.object-storage.test 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ObjectStorageAdapter.update — user-1이 존재하지 않는 id의 호스트 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

