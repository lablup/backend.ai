## login_client_type

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/login_client_type/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/login_client_type/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-login-client-type-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 이름과 설명을 함께 지정해 생성하면 지정한 값이 그대로 담긴 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 생성

Then

- 생성한 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'webui'
  - description = '새로 지정한 설명'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-login-client-type-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

같은 이름의 종류가 이미 있을 때 그 이름으로 다시 생성하면, 이름 중복으로 거부된다

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

- LoginClientTypeAdapter.admin_create — user-1이 이미 있는 이름 client-1(으)로 다시 생성

Then

- 거부된다
  - 거부: LoginClientTypeConflict

#### [a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 종류를 생성하면 역할 부족으로 거부된다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-makes-a-login-client-type-with-a-name-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

슈퍼관리자가 이름만 지정해 생성하면 설명이 비어 있는 노드가 반환된다

Given

- 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 생성

Then

- 생성한 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'webui'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-does-not-let-a-user-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py) — pass

권한 검사를 꺼도 슈퍼관리자가 아니면 종류를 생성하지 못한다. 생성은 권한 그래프가 아니라 역할로 보호되므로 스위치와 무관하다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- LoginClientTypeAdapter.admin_create — user-1이 webui 종류를 생성

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-login-client-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다

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

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 아무것도 수정

Then

- 미리 만들어 둔 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = '미리 만들어 둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

아무 권한도 없는 사용자가 존재하지 않는 id를 수정하면 대상 없음이 아니라 권한 부족으로 거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다

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

- LoginClientTypeAdapter.admin_update — user-1이 존재하지 않는 id의 이름 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [a-user-granted-nothing-may-not-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

아무 권한도 없는 사용자가 종류를 수정하면 권한 부족으로 거부된다. 종류는 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없다

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

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [clearing-a-login-client-type-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

설명이 있는 종류에 설명을 비우는 수정을 하면, 설명이 없어진다

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

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 설명 수정

Then

- 미리 만들어 둔 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = None
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [renaming-a-login-client-type-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

슈퍼관리자가 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 유지된다

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

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 수정

Then

- 미리 만들어 둔 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '미리 만들어 둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [renaming-a-login-client-type-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름 중복으로 거부된다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파된다

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

- LoginClientTypeAdapter.admin_update — user-1이 wanted-1의 이름을 other-1(으)로 수정

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다

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

- LoginClientTypeAdapter.admin_update — user-1이 존재하지 않는 id의 이름 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [turning-enforcement-off-lets-a-user-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 종류를 수정할 수 있다. 수정은 역할이 아니라 권한 그래프로 보호되기 때문이다

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

- LoginClientTypeAdapter.admin_update — user-1이 client-1의 이름 수정

Then

- 미리 만들어 둔 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'renamed'
  - description = '미리 만들어 둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

### reading

#### [a-user-granted-nothing-reads-a-login-client-type-by-id](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py) — pass

아무 권한도 없는 사용자가 id로 조회하면 그 종류 전체가 반환된다. 이 조회는 인증만 확인한다

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

- LoginClientTypeAdapter.get — user-1이 client-1(으)로 조회

Then

- 미리 만들어 둔 종류 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - name = 'client-1'
  - description = '미리 만들어 둔 로그인 클라이언트 종류'
  - created_at: 이 실행이 쓴 시각
  - modified_at: 이 실행이 쓴 시각

#### [reading-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py) — pass

존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다

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

- LoginClientTypeAdapter.get — user-1이 존재하지 않는 id(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### retiring

#### [a-user-granted-nothing-may-not-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

아무 권한도 없는 사용자가 종류를 삭제하면 권한 부족으로 거부된다

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

- LoginClientTypeAdapter.admin_delete — user-1이 client-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [deleting-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다

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

- LoginClientTypeAdapter.admin_delete — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-deletes-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

슈퍼관리자가 종류를 삭제하면 삭제한 종류의 id를 담은 응답이 반환된다

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

- LoginClientTypeAdapter.admin_delete — user-1이 client-1 삭제

Then

- 삭제한 종류의 id가 반환된다
  - id: 미리 만들어 둔 종류와 같다

#### [turning-enforcement-off-lets-a-user-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 종류를 삭제할 수 있다. 삭제는 역할이 아니라 권한 그래프로 보호되기 때문이다

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

- LoginClientTypeAdapter.admin_delete — user-1이 client-1 삭제

Then

- 삭제한 종류의 id가 반환된다
  - id: 미리 만들어 둔 종류와 같다

### searching

#### [a-name-filter-narrows-the-answer-to-the-login-client-type-it-names](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 종류만 남는다

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

- LoginClientTypeAdapter.search — user-1이 wanted-1 이름 필터로 조회

Then

- 필터에 맞는 종류 하나만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [a-user-granted-nothing-counts-every-login-client-type-laid](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다

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

- 미리 만들어 둔 종류가 모두 집계된다
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [omitting-the-page-size-answers-fifty-login-client-types-and-a-next-page](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py) — pass

종류 51개가 있을 때 크기 없이 조회하면 50건까지 반환되고 다음 페이지가 있다고 응답한다. 기본 페이지 크기가 다른 카탈로그의 10이 아니라 50이다

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

- 기본 크기의 첫 페이지가 반환된다
  - len(items) = 50
  - total_count = 51
  - has_next_page = True
  - has_previous_page = False

