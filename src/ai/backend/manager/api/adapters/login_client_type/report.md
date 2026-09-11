## login_client_type

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/login_client_type/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/login_client_type/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-login-client-type-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 이름과 설명을 함께 주고 만들면 준 값이 그대로 실린 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 만듦

Then

- 만든 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'webui'
  - description = '새로 적은 설명'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-login-client-type-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

같은 이름의 종류가 이미 있을 때 그 이름으로 다시 만들면, 이름이 겹친다는 이유로 거부된다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 이미 있는 client-1으로 다시 만듦

Then

- 거부된다
  - 거부: LoginClientTypeConflict

#### [a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 종류를 만들면 역할로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-login-client-type-with-a-name-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 이름만 주고 만들면 설명이 빈 노드가 온다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 만듦

Then

- 만든 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'webui'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

엔티티 권한 집행을 꺼도 슈퍼관리자가 아니면 종류를 만들지 못한다. 이 문은 권한 그래프가 아니라 역할이라 스위치와 무관하다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 만듦

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-login-client-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 아무것도 고침

Then

- 심은 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = '심어둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 없는 id를 고치면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 돌고 없는 행에는 걸린 권한도 없다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 없는 id의 이름 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

아무 권한도 받지 않은 사용자가 종류를 고치면 권한 부족으로 거부된다. 종류는 어느 스코프에도 없어 그 권한을 받을 길이 없다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 고침

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [clearing-a-login-client-type-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

설명이 있는 종류의 설명을 비우는 수정을 하면, 설명이 없어진다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 설명 고침

Then

- 심은 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [renaming-a-login-client-type-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

슈퍼관리자가 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 남는다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 고침

Then

- 심은 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '심어둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [renaming-a-login-client-type-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름이 겹친다는 이유로 거부된다. 만들 때와 달리 저장소의 제약 위반이 그대로 온다

Given

- 로그인 클라이언트 종류 2개와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 wanted-1의 이름을 other-1으로 고침

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

슈퍼관리자가 아무 종류도 갖지 않은 id를 고치면 대상이 없다는 것으로 거부된다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 없는 id의 이름 고침

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-lets-a-user-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 종류를 고친다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 고침

Then

- 심은 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '심어둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### reading

#### [a-user-granted-nothing-reads-a-login-client-type-by-id](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py) — pass

아무 권한도 받지 않은 사용자가 id로 조회하면 그 종류 전체가 온다. 이 읽기는 인증만 본다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.get — user-1이 client-1로 조회

Then

- 심은 종류 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = '심어둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [reading-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py) — pass

아무 종류도 갖지 않은 id로 조회하면 대상이 없다는 것으로 거부된다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.get — user-1이 없는 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### retiring

#### [a-user-granted-nothing-may-not-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

아무 권한도 받지 않은 사용자가 종류를 지우면 권한 부족으로 거부된다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_delete — user-1이 client-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [deleting-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

슈퍼관리자가 아무 종류도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_delete — user-1이 없는 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-deletes-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

슈퍼관리자가 종류를 지우면 지운 종류의 id를 실은 답이 온다

Given

- 로그인 클라이언트 종류 하나와, 슈퍼관리자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_delete — user-1이 client-1를 지움

Then

- 지운 종류의 id가 온다
  - id: 심은 종류와 같다

#### [turning-enforcement-off-lets-a-user-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 종류를 지운다. 이 문은 역할이 아니라 권한 그래프가 지키기 때문이다

Given

- 로그인 클라이언트 종류 하나와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 client-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_delete — user-1이 client-1를 지움

Then

- 지운 종류의 id가 온다
  - id: 심은 종류와 같다

### searching

#### [a-name-filter-narrows-the-answer-to-the-login-client-type-it-names](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 것만 남는다

Given

- 로그인 클라이언트 종류 3개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 로그인 클라이언트 종류 other-2
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.search — user-1이 wanted-1으로 걸러 조회

Then

- 걸러낸 그 종류 하나만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-counts-every-login-client-type-laid](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 둘이 있을 때 아무 권한도 받지 않은 사용자가 필터 없이 조회하면 둘을 모두 센다

Given

- 로그인 클라이언트 종류 2개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.search — user-1이 필터 없이 전체 조회

Then

- 심은 종류가 모두 세어진다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-fifty-login-client-types-and-a-next-page](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 쉰하나가 있을 때 크기 없이 조회하면 쉰 건까지 오고 다음 쪽이 있다고 답한다. 기본 페이지 크기가 다른 카탈로그의 열이 아니라 쉰이다

Given

- 로그인 클라이언트 종류 51개와, 일반 사용자 한 명
  - 로그인 클라이언트 종류 wanted-1
  - 로그인 클라이언트 종류 other-1
  - 로그인 클라이언트 종류 other-2
  - 로그인 클라이언트 종류 other-3
  - 로그인 클라이언트 종류 other-4
  - 로그인 클라이언트 종류 other-5
  - 로그인 클라이언트 종류 other-6
  - 로그인 클라이언트 종류 other-7
  - 로그인 클라이언트 종류 other-8
  - 로그인 클라이언트 종류 other-9
  - 로그인 클라이언트 종류 other-10
  - 로그인 클라이언트 종류 other-11
  - 로그인 클라이언트 종류 other-12
  - 로그인 클라이언트 종류 other-13
  - 로그인 클라이언트 종류 other-14
  - 로그인 클라이언트 종류 other-15
  - 로그인 클라이언트 종류 other-16
  - 로그인 클라이언트 종류 other-17
  - 로그인 클라이언트 종류 other-18
  - 로그인 클라이언트 종류 other-19
  - 로그인 클라이언트 종류 other-20
  - 로그인 클라이언트 종류 other-21
  - 로그인 클라이언트 종류 other-22
  - 로그인 클라이언트 종류 other-23
  - 로그인 클라이언트 종류 other-24
  - 로그인 클라이언트 종류 other-25
  - 로그인 클라이언트 종류 other-26
  - 로그인 클라이언트 종류 other-27
  - 로그인 클라이언트 종류 other-28
  - 로그인 클라이언트 종류 other-29
  - 로그인 클라이언트 종류 other-30
  - 로그인 클라이언트 종류 other-31
  - 로그인 클라이언트 종류 other-32
  - 로그인 클라이언트 종류 other-33
  - 로그인 클라이언트 종류 other-34
  - 로그인 클라이언트 종류 other-35
  - 로그인 클라이언트 종류 other-36
  - 로그인 클라이언트 종류 other-37
  - 로그인 클라이언트 종류 other-38
  - 로그인 클라이언트 종류 other-39
  - 로그인 클라이언트 종류 other-40
  - 로그인 클라이언트 종류 other-41
  - 로그인 클라이언트 종류 other-42
  - 로그인 클라이언트 종류 other-43
  - 로그인 클라이언트 종류 other-44
  - 로그인 클라이언트 종류 other-45
  - 로그인 클라이언트 종류 other-46
  - 로그인 클라이언트 종류 other-47
  - 로그인 클라이언트 종류 other-48
  - 로그인 클라이언트 종류 other-49
  - 로그인 클라이언트 종류 other-50
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.search — user-1이 필터 없이 전체 조회

Then

- 기본 크기의 첫 쪽이 온다
  - len(items) = 50
  - total_count = 51
  - has_next_page = True
  - has_previous_page = False

