## vfs_storage

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/vfs_storage/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/vfs_storage/adapter.py)

시나리오: 미완 7 / 9

- ops 로 구성 (9)
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - create — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - list_all — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - partial_bulk_update — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - purge — 대표 성공 ✓ · 대표 실패 ✓
  - search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - update — 대표 성공 ✓ · 대표 실패 ✓

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages) | 성공 |
| [슈퍼관리자가 VFS storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages) | 성공 |
| [슈퍼관리자가 VFS storage 여럿의 기본 경로를 한 번에 바꾸면, 모두 새 기본 경로로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 VFS storage 를 purge 하면 purge 한 것의 id 가 반환된다](#purging-the-superadmin-purges-a-vfs-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 를 purge 하면 권한 부족으로 거부된다](#purging-a-user-granted-nothing-may-not-purge-a-vfs-storage) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 purge 하면 대상을 찾을 수 없다는 이유로 거부된다](#purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 기본 경로만 바꾸면, 기본 경로는 새 값이 되고 나머지는 그대로 남는다](#editing-the-superadmin-changes-the-base-path-of-a-vfs-storage) | 성공 |
| [아무 권한도 받지 않은 사용자가 VFS storage 를 수정하면 권한 부족으로 거부된다. VFS storage 는 global 에만 속해 그 권한을 받을 방법이 없다](#editing-a-user-granted-nothing-may-not-edit-a-vfs-storage) | 거부 |
| [슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다](#editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found) | 거부 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-purges-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 purge 하려 하면, purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.partial_bulk_purge — user-1이 VFS storage 2개를 한 번에 purge

Then

- 처리된 VFS storage 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 VFS storage 의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 VFS storage 의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-vfs-storages-and-a-missing-id"></a>

#### [the-superadmin-purges-several-vfs-storages-and-a-missing-id](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_purging.py) — pass

슈퍼관리자가 VFS storage 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- VFS storage 2개와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.partial_bulk_purge — user-1이 VFS storage 2개 와 없는 id 하나를 한 번에 purge

Then

- 대상 VFS storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 VFS storage와 같다
  - successes[0].entity_id: 미리 만들어 둔 VFS storage와 같다
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/seeded/vfs-storage'
  - successes[1].id: 미리 만들어 둔 VFS storage와 같다
  - successes[1].entity_id: 미리 만들어 둔 VFS storage와 같다
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/seeded/vfs-storage'
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-vfs-storages"></a>

#### [a-user-granted-nothing-edits-none-of-several-vfs-storages](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 VFS storage 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- VFS storage 2개와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.partial_bulk_update — user-1이 VFS storage 2개의 기본 경로를 한 번에 수정

Then

- 처리된 VFS storage 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 VFS storage 의 id와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 VFS storage 의 id와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-vfs-storages-at-once"></a>

#### [the-superadmin-edits-several-vfs-storages-at-once](/tests/scenario/bai_scenario/manager/vfs_storage/test_partial_bulk_editing.py) — pass

슈퍼관리자가 VFS storage 여럿의 기본 경로를 한 번에 바꾸면, 모두 새 기본 경로로 오고 실패한 것은 없다

Given

- VFS storage 2개와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - VFS storage vfs-storage-2: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.partial_bulk_update — user-1이 VFS storage 2개의 기본 경로를 한 번에 수정

Then

- 대상 VFS storage 가 모두 처리된 목록에 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 미리 만들어 둔 VFS storage와 같다
  - successes[0].entity_id: 미리 만들어 둔 VFS storage와 같다
  - successes[0].name = 'vfs-storage-1'
  - successes[0].host = 'seeded-host'
  - successes[0].base_path = '/moved/vfs-storage'
  - successes[1].id: 미리 만들어 둔 VFS storage와 같다
  - successes[1].entity_id: 미리 만들어 둔 VFS storage와 같다
  - successes[1].name = 'vfs-storage-2'
  - successes[1].host = 'seeded-host'
  - successes[1].base_path = '/moved/vfs-storage'
  - failed = []

### purge

<a id="purging-the-superadmin-purges-a-vfs-storage"></a>

#### [the-superadmin-purges-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py) — pass

슈퍼관리자가 VFS storage 를 purge 하면 purge 한 것의 id 가 반환된다

Given

- VFS storage 하나와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.purge — user-1이 vfs-storage-1 purge

Then

- purge 한 VFS storage 의 id 가 반환된다
  - id: 미리 만들어 둔 VFS storage와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-purge-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py) — pass

아무 권한도 받지 않은 사용자가 VFS storage 를 purge 하면 권한 부족으로 거부된다

Given

- VFS storage 하나와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.purge — user-1이 vfs-storage-1 purge

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="purging-purging-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 id를 purge 하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- VFS storage 하나와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.purge — user-1이 존재하지 않는 id purge

Then

- 거부된다
  - 거부: EntityNotFoundError

### update

<a id="editing-the-superadmin-changes-the-base-path-of-a-vfs-storage"></a>

#### [the-superadmin-changes-the-base-path-of-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py) — pass

슈퍼관리자가 기본 경로만 바꾸면, 기본 경로는 새 값이 되고 나머지는 그대로 남는다

Given

- VFS storage 하나와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.update — user-1이 vfs-storage-1의 기본 경로 수정

Then

- 미리 만들어 둔 VFS storage 전체가 반환된다
  - id: 미리 만들어 둔 VFS storage와 같다
  - entity_id: 미리 만들어 둔 VFS storage와 같다
  - name = 'vfs-storage-1'
  - host = 'seeded-host'
  - base_path = '/moved/vfs-storage'

<a id="editing-a-user-granted-nothing-may-not-edit-a-vfs-storage"></a>

#### [a-user-granted-nothing-may-not-edit-a-vfs-storage](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 VFS storage 를 수정하면 권한 부족으로 거부된다. VFS storage 는 global 에만 속해 그 권한을 받을 방법이 없다

Given

- VFS storage 하나와, 일반 사용자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.update — user-1이 vfs-storage-1의 기본 경로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="editing-the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-vfs-storage-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/vfs_storage/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

Given

- VFS storage 하나와, 슈퍼관리자 한 명
  - VFS storage vfs-storage-1: 기본 경로가 /seeded/vfs-storage 이다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- VFSStorageAdapter.update — user-1이 존재하지 않는 id의 기본 경로 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

