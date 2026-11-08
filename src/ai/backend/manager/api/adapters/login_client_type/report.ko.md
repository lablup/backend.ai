## login_client_type

[배경](/src/ai/backend/manager/api/adapters/login_client_type/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/login_client_type/adapter.py)

시나리오: 미완성 4 / 8

- ops 구성 (8)
  - admin_create: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - get: 대표 성공 ✓ · 대표 거부 ✓
  - partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - partial_bulk_update: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - search: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - update: 대표 성공 ✓ · 대표 거부 ✓

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 이름과 설명을 함께 지정해 로그인 클라이언트 유형을 생성하면 지정한 값이 그대로 담긴 노드가 반환됩니다](#creating-a-login-client-type-made-with-a-description-carries-it-back) | 성공 |
| [superadmin 이 이름만 지정해 로그인 클라이언트 유형을 생성하면 설명이 비어 있는 노드가 반환됩니다](#creating-the-superadmin-makes-a-login-client-type-with-a-name-alone) | 성공 |
| [같은 이름의 로그인 클라이언트 유형이 이미 있을 때 그 이름으로 다시 생성하면 이름 중복으로 거부됩니다](#creating-a-login-client-type-name-already-taken-is-refused) | 거부 |
| [superadmin 이 아닌 사용자가 로그인 클라이언트 유형을 생성하면 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type) | 거부 |
| [권한 검사를 꺼도 superadmin 이 아니면 로그인 클라이언트 유형을 생성하지 못합니다](#creating-turning-enforcement-off-does-not-let-a-user-create-a-login-client-type) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 종류 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |

**get**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 id 로 조회하면 그 로그인 클라이언트 유형 전체가 반환됩니다. 이 조회는 인증만 확인합니다](#reading-a-user-granted-nothing-reads-a-login-client-type-by-id) | 성공 |
| [존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다](#reading-reading-a-login-client-type-id-nothing-answers-to-is-refused) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 로그인 클라이언트 유형 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-login-client-types) | 성공 |
| [superadmin 이 로그인 클라이언트 유형 둘과 없는 id 하나를 한 번에 purge 하면 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-login-client-types-answers-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 없는 사용자가 로그인 클라이언트 유형 여럿을 한 번에 수정하려 하면 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-login-client-types) | 성공 |
| [superadmin 이 로그인 클라이언트 유형 여럿의 설명을 한 번에 변경하면 모두 새 설명으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-edits-several-login-client-types-at-once) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 로그인 클라이언트 유형을 삭제하면 삭제한 유형의 id 를 담은 응답이 반환됩니다](#retiring-the-superadmin-deletes-a-login-client-type) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 로그인 클라이언트 유형을 삭제할 수 있습니다](#retiring-turning-enforcement-off-lets-a-user-delete-a-login-client-type) | 성공 |
| [아무 권한도 없는 사용자가 로그인 클라이언트 유형을 삭제하면 권한 부족으로 거부됩니다](#retiring-a-user-granted-nothing-may-not-delete-a-login-client-type) | 거부 |
| [superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다](#retiring-deleting-a-login-client-type-id-nothing-answers-to-is-not-found) | 거부 |

**search**

| 시나리오 | 판정 |
|---|---|
| [로그인 클라이언트 유형 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계됩니다](#searching-a-user-granted-nothing-counts-every-login-client-type-laid) | 성공 |

**update**

| 시나리오 | 판정 |
|---|---|
| [값을 하나도 지정하지 않고 수정하면 아무것도 변경되지 않은 노드가 반환됩니다](#editing-a-login-client-type-edit-giving-no-value-changes-nothing) | 성공 |
| [설명이 있는 로그인 클라이언트 유형에 설명을 비우는 수정을 하면 설명이 없어집니다](#editing-clearing-a-login-client-type-description-leaves-it-empty) | 성공 |
| [superadmin 이 로그인 클라이언트 유형의 이름만 변경하면 이름은 새 값이 되고 설명은 그대로 유지됩니다](#editing-renaming-a-login-client-type-leaves-its-description-alone) | 성공 |
| [권한 검사를 끄면 아무 권한도 없는 사용자도 로그인 클라이언트 유형을 수정할 수 있습니다](#editing-turning-enforcement-off-lets-a-user-edit-a-login-client-type) | 성공 |
| [아무 권한도 없는 사용자가 존재하지 않는 id 를 수정하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 row 에는 부여된 권한도 없기 때문입니다](#editing-a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission) | 거부 |
| [아무 권한도 없는 사용자가 로그인 클라이언트 유형을 수정하면 권한 부족으로 거부됩니다. 유형은 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없습니다](#editing-a-user-granted-nothing-may-not-edit-a-login-client-type) | 거부 |
| [로그인 클라이언트 유형 둘 중 한쪽의 이름을 다른 쪽 이름으로 변경하면 이름 중복으로 거부됩니다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다](#editing-renaming-a-login-client-type-to-a-name-already-taken-is-refused) | 거부 |
| [superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다](#editing-the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found) | 거부 |

### admin_create

<a id="creating-a-login-client-type-made-with-a-description-carries-it-back"></a>

#### [a-login-client-type-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

superadmin 이 이름과 설명을 함께 지정해 로그인 클라이언트 유형을 생성하면 지정한 값이 그대로 담긴 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- LoginClientTypeAdapter.admin_create: user-1 이 webui 로그인 클라이언트 유형을 생성합니다

Then

- 생성한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'webui'
  - description = '새로 지정한 설명'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-the-superadmin-makes-a-login-client-type-with-a-name-alone"></a>

#### [the-superadmin-makes-a-login-client-type-with-a-name-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

superadmin 이 이름만 지정해 로그인 클라이언트 유형을 생성하면 설명이 비어 있는 노드가 반환됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- LoginClientTypeAdapter.admin_create: user-1 이 webui 로그인 클라이언트 유형을 생성합니다

Then

- 생성한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'webui'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="creating-a-login-client-type-name-already-taken-is-refused"></a>

#### [a-login-client-type-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

같은 이름의 로그인 클라이언트 유형이 이미 있을 때 그 이름으로 다시 생성하면 이름 중복으로 거부됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.admin_create: user-1 이 이미 있는 이름 client-1 (으)로 로그인 클라이언트 유형을 다시 생성합니다

Then

- 거부됩니다
  - 거부: LoginClientTypeConflict

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

superadmin 이 아닌 사용자가 로그인 클라이언트 유형을 생성하면 역할 부족으로 거부됩니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- LoginClientTypeAdapter.admin_create: user-1 이 webui 로그인 클라이언트 유형을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-login-client-type"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

권한 검사를 꺼도 superadmin 이 아니면 로그인 클라이언트 유형을 생성하지 못합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- LoginClientTypeAdapter.admin_create: user-1 이 webui 로그인 클라이언트 유형을 생성합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py): pass

superadmin 이 미리 저장한 종류 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다

Given

- 로그인 클라이언트 종류 2개와, superadmin 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.batch_load_by_ids: user-1이 미리 저장한 종류 2개와 없는 id 하나를 한 번에 조회합니다

Then

- 요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다
  - len(items) = 3
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'wanted-1'
  - description = '미리 생성한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'other-1'
  - description = '미리 생성한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - items[2] = None

### get

<a id="reading-a-user-granted-nothing-reads-a-login-client-type-by-id"></a>

#### [a-user-granted-nothing-reads-a-login-client-type-by-id](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py): pass

아무 권한도 없는 사용자가 id 로 조회하면 그 로그인 클라이언트 유형 전체가 반환됩니다. 이 조회는 인증만 확인합니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.get: user-1 이 client-1 (으)로 조회합니다

Then

- 미리 저장한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'client-1'
  - description = '미리 저장한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="reading-reading-a-login-client-type-id-nothing-answers-to-is-refused"></a>

#### [reading-a-login-client-type-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py): pass

존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.get: user-1 이 존재하지 않는 id (으)로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-login-client-types"></a>

#### [a-user-granted-nothing-purges-none-of-several-login-client-types](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_purging.py): pass

아무 권한도 없는 사용자가 로그인 클라이언트 유형 여럿을 한 번에 purge 하려 하면 purge 된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 로그인 클라이언트 종류 2개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.partial_bulk_purge: user-1 이 로그인 클라이언트 유형 2개를 한 번에 purge 합니다

Then

- 처리된 종류 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 종류의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 종류의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-purging-several-login-client-types-answers-for-the-missing-one"></a>

#### [purging-several-login-client-types-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_purging.py): pass

superadmin 이 로그인 클라이언트 유형 둘과 없는 id 하나를 한 번에 purge 하면 둘은 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 로그인 클라이언트 종류 2개와, superadmin 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.partial_bulk_purge: user-1 이 로그인 클라이언트 유형 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 로그인 클라이언트 유형이 모두 처리된 목록에 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'wanted-1'
  - description = '미리 생성한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'other-1'
  - description = '미리 생성한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-login-client-types"></a>

#### [a-user-granted-nothing-edits-none-of-several-login-client-types](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_editing.py): pass

아무 권한도 없는 사용자가 로그인 클라이언트 유형 여럿을 한 번에 수정하려 하면 수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 로그인 클라이언트 종류 2개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.partial_bulk_update: user-1 이 로그인 클라이언트 유형 2개의 설명을 한 번에 수정합니다

Then

- 처리된 종류 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 대상 종류의 id 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 대상 종류의 id 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-edits-several-login-client-types-at-once"></a>

#### [the-superadmin-edits-several-login-client-types-at-once](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_editing.py): pass

superadmin 이 로그인 클라이언트 유형 여럿의 설명을 한 번에 변경하면 모두 새 설명으로 오고 실패한 것은 없습니다

Given

- 로그인 클라이언트 종류 2개와, superadmin 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.partial_bulk_update: user-1 이 로그인 클라이언트 유형 2개의 설명을 한 번에 수정합니다

Then

- 로그인 클라이언트 유형이 모두 새 설명으로 오고 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'wanted-1'
  - description = '한 번에 수정한 설명'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'other-1'
  - description = '한 번에 수정한 설명'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### purge

<a id="retiring-the-superadmin-deletes-a-login-client-type"></a>

#### [the-superadmin-deletes-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

superadmin 이 로그인 클라이언트 유형을 삭제하면 삭제한 유형의 id 를 담은 응답이 반환됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.purge: user-1 이 client-1를 삭제합니다

Then

- 삭제한 종류의 id 가 반환됩니다
  - id: 미리 저장한 종류와 같다

<a id="retiring-turning-enforcement-off-lets-a-user-delete-a-login-client-type"></a>

#### [turning-enforcement-off-lets-a-user-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 로그인 클라이언트 유형을 삭제할 수 있습니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.purge: user-1 이 client-1를 삭제합니다

Then

- 삭제한 종류의 id 가 반환됩니다
  - id: 미리 저장한 종류와 같다

<a id="retiring-a-user-granted-nothing-may-not-delete-a-login-client-type"></a>

#### [a-user-granted-nothing-may-not-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

아무 권한도 없는 사용자가 로그인 클라이언트 유형을 삭제하면 권한 부족으로 거부됩니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.purge: user-1 이 client-1를 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="retiring-deleting-a-login-client-type-id-nothing-answers-to-is-not-found"></a>

#### [deleting-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

superadmin 이 존재하지 않는 id 를 삭제하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.purge: user-1 이 존재하지 않는 id 를 삭제합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### search

<a id="searching-a-user-granted-nothing-counts-every-login-client-type-laid"></a>

#### [a-user-granted-nothing-counts-every-login-client-type-laid](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py): pass

로그인 클라이언트 유형 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계됩니다

Given

- 로그인 클라이언트 종류 2개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 종류가 모두 집계됩니다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

### update

<a id="editing-a-login-client-type-edit-giving-no-value-changes-nothing"></a>

#### [a-login-client-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

값을 하나도 지정하지 않고 수정하면 아무것도 변경되지 않은 노드가 반환됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 client-1의 아무것도 수정하지 않습니다

Then

- 미리 저장한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'client-1'
  - description = '미리 저장한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-clearing-a-login-client-type-description-leaves-it-empty"></a>

#### [clearing-a-login-client-type-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

설명이 있는 로그인 클라이언트 유형에 설명을 비우는 수정을 하면 설명이 없어집니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 client-1의 설명을 수정합니다

Then

- 미리 저장한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'client-1'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-renaming-a-login-client-type-leaves-its-description-alone"></a>

#### [renaming-a-login-client-type-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

superadmin 이 로그인 클라이언트 유형의 이름만 변경하면 이름은 새 값이 되고 설명은 그대로 유지됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 client-1의 이름을 수정합니다

Then

- 미리 저장한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'renamed'
  - description = '미리 저장한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-login-client-type"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

권한 검사를 끄면 아무 권한도 없는 사용자도 로그인 클라이언트 유형을 수정할 수 있습니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 client-1의 이름을 수정합니다

Then

- 미리 저장한 종류 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'renamed'
  - description = '미리 저장한 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

<a id="editing-a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

아무 권한도 없는 사용자가 존재하지 않는 id 를 수정하면 대상 없음이 아니라 권한 부족으로 거부됩니다. 권한 검사가 먼저 실행되고 없는 row 에는 부여된 권한도 없기 때문입니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 존재하지 않는 id 의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-a-user-granted-nothing-may-not-edit-a-login-client-type"></a>

#### [a-user-granted-nothing-may-not-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

아무 권한도 없는 사용자가 로그인 클라이언트 유형을 수정하면 권한 부족으로 거부됩니다. 유형은 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없습니다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - 일반 사용자 user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 client-1의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-renaming-a-login-client-type-to-a-name-already-taken-is-refused"></a>

#### [renaming-a-login-client-type-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

로그인 클라이언트 유형 둘 중 한쪽의 이름을 다른 쪽 이름으로 변경하면 이름 중복으로 거부됩니다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다

Given

- 로그인 클라이언트 종류 2개와, superadmin 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 wanted-1의 이름을 other-1 (으)로 수정합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="editing-the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 로그인 클라이언트 종류 하나와, superadmin 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - public 에서 login_client_type 조회 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 public-reader-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 public-reader-1: login_client_type 전체에 READ 허용
    - superadmin user-1: 역할 public-reader-1 보유

When

- LoginClientTypeAdapter.update: user-1 이 존재하지 않는 id 의 이름을 수정합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

