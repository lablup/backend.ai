## app_config_allow_list

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_allow_list/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_allow_list/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-name-nothing-registers-cannot-be-opened](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 등록되지 않은 설정 이름으로 허용 목록 항목을 생성하면, 정의 없음 오류가 반환된다

Given

- 등록되지 않은 설정 이름과 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_create — user-1이 unregistered의 공개 허용 목록 항목 생성 (순위 생략)

Then

- 거부된다
  - 거부: AppConfigDefinitionNotFound

#### [a-rank-given-in-the-request-is-kept-as-is](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 지정해 허용 목록 항목을 생성하면, 지정한 값이 그대로 저장된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 도메인 허용 목록 항목 생성 (순위 250)

Then

- 생성한 허용 목록 항목의 모든 필드가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 250
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

일반 사용자가 허용 목록 항목을 생성하면, 슈퍼관리자 권한이 없어 거부된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 공개 허용 목록 항목 생성 (순위 생략)

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [leaving-the-rank-out-opens-the-domain-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 도메인 스코프 유형의 허용 목록 항목을 생성하면, 순위 200이 적용된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 도메인 허용 목록 항목 생성 (순위 생략)

Then

- 생성한 허용 목록 항목의 모든 필드가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 200
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [leaving-the-rank-out-opens-the-public-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 공개 스코프 유형의 허용 목록 항목을 생성하면, 순위 100이 적용된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 공개 허용 목록 항목 생성 (순위 생략)

Then

- 생성한 허용 목록 항목의 모든 필드가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - rank = 100
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [leaving-the-rank-out-opens-the-user-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 사용자 스코프 유형의 허용 목록 항목을 생성하면, 순위 300이 적용된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 사용자 허용 목록 항목 생성 (순위 생략)

Then

- 생성한 허용 목록 항목의 모든 필드가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 같은 설정 이름과 스코프 유형으로 항목을 다시 생성하면, 데이터베이스의 고유 제약 오류가 반환된다

Given

- 공개 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 공개 허용 목록 항목 생성 (순위 생략)

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [turning-enforcement-off-still-does-not-let-a-user-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

RBAC 강제를 꺼도 일반 사용자의 허용 목록 항목 생성은 거부된다. 생성에는 별도의 슈퍼관리자 검사가 적용된다

Given

- 허용 목록 항목이 없는 설정 정의 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1의 공개 허용 목록 항목 생성 (순위 생략)

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-who-is-not-the-superadmin-may-not-change-a-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

같은 항목을 권한이 없는 일반 사용자가 수정하면, 엔티티 수정 권한이 없어 거부된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목 수정 (순위 150(으)로 변경)

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-edit-carrying-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

슈퍼관리자가 아무 값도 지정하지 않고 수정하면, 아무것도 바뀌지 않은 노드가 반환된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목 수정 (빈 요청)

Then

- 준비한 허용 목록 항목의 모든 필드가 반환된다
  - id: 준비한 ID와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

슈퍼관리자가 존재하지 않는 ID의 순위를 수정하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 공개 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 존재하지 않는 ID 수정 (순위 150(으)로 변경)

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-changes-an-entrys-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

항목 하나가 있고 슈퍼관리자가 순위를 바꾸면, 순위만 변경되고 설정 이름과 스코프 유형은 그대로다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목 수정 (순위 150(으)로 변경)

Then

- 준비한 허용 목록 항목의 모든 필드가 반환된다
  - id: 준비한 ID와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 150
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### purging

#### [a-user-who-is-not-the-superadmin-may-not-purge-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

같은 항목을 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 삭제 권한이 없어 거부된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목 영구 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-entry-holding-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

설정 조각이 있는 항목을 슈퍼관리자가 영구 삭제하면, 설정 조각이 막지 않고 항목의 ID가 반환된다

Given

- 설정 조각이 있는 공개 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light'}

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목 영구 삭제

Then

- 영구 삭제한 허용 목록 항목의 ID가 반환된다
  - id: 준비한 ID와 같다

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 ID를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 공개 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 존재하지 않는 ID 영구 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

설정 조각이 없는 항목을 슈퍼관리자가 영구 삭제하면, 삭제한 항목의 ID가 반환된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목 영구 삭제

Then

- 영구 삭제한 허용 목록 항목의 ID가 반환된다
  - id: 준비한 ID와 같다

### reading

#### [a-user-who-is-not-the-superadmin-may-not-read-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

같은 항목을 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 config-1의 항목 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 ID로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 권한 검사를 통과하는 사용자만 이 응답을 본다

Given

- 공개 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 존재하지 않는 ID 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-an-entry-by-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

항목 하나가 있고 슈퍼관리자가 ID로 조회하면, 그 항목의 모든 필드가 반환된다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 config-1의 항목 조회

Then

- 준비한 허용 목록 항목의 모든 필드가 반환된다
  - id: 준비한 ID와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

RBAC 강제를 끄면 권한이 없는 일반 사용자도 허용 목록 항목을 조회할 수 있다. 개별 조회는 엔티티 권한 검사를 사용한다

Given

- 사용자 스코프 유형의 허용 목록 항목 하나와 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 config-1의 항목 조회

Then

- 준비한 허용 목록 항목의 모든 필드가 반환된다
  - id: 준비한 ID와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading_many

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

권한이 없는 일반 사용자가 항목 둘과 없는 ID 하나를 함께 조회하면, 각 입력 위치에 엔티티 읽기 권한 오류가 반환된다

Given

- 한 설정 이름의 PUBLIC·USER 허용 목록 항목과 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 first-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 second-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 항목 둘과 존재하지 않는 ID를 한 번에 조회

Then

- 있는 ID 둘과 없는 ID 모두 각 위치에 권한 오류가 반환된다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-id-list-answers-empty](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

빈 ID 목록으로 조회하면 빈 목록이 반환된다

Given

- 한 설정 이름의 PUBLIC·USER 허용 목록 항목과 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 first-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 second-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 빈 ID 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

#### [duplicate-ids-keep-their-input-positions](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

슈퍼관리자가 같은 허용 목록 항목의 ID를 두 번 조회하면, 같은 노드가 두 위치에 반환된다

Given

- 한 설정 이름의 PUBLIC·USER 허용 목록 항목과 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 first-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 second-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 첫 번째 허용 목록 항목의 ID를 두 번 조회

Then

- 중복 ID의 두 위치에 같은 허용 목록 항목이 반환된다
  - items = 2
  - items[0].id: 준비한 첫 번째 ID와 같다
  - items[1].id: 준비한 첫 번째 ID와 같다

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

슈퍼관리자가 항목 둘과 없는 ID 하나를 함께 조회하면, 입력 순서대로 노드 둘과 None이 반환된다

Given

- 한 설정 이름의 PUBLIC·USER 허용 목록 항목과 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 first-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 second-1: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 항목 둘과 존재하지 않는 ID를 한 번에 조회

Then

- 있는 ID 둘은 노드로, 없는 ID는 None으로 반환된다
  - items = 3
  - items[0].id: 준비한 첫 번째 ID와 같다
  - items[1].id: 준비한 두 번째 ID와 같다
  - items[2] = None

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

일반 사용자가 허용 목록을 검색하면, 슈퍼관리자 권한이 없어 거부된다

Given

- 설정 이름 2개에 각각 공개 스코프 유형의 허용 목록 항목과 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 정의 definition-2: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-2: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 필터 없이 검색

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-counts-every-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

설정 이름 둘에 항목 넷이 있고 슈퍼관리자가 필터 없이 검색하면, 네 항목이 모두 반환된다

Given

- 설정 이름 2개에 각각 공개·사용자 스코프 유형의 허용 목록 항목과 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 entry-2: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 설정 정의 definition-2: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-3: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 허용 목록 항목 entry-4: 사용자 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 필터 없이 검색

Then

- 준비한 허용 목록 항목만 모두 반환된다
  - items = [('definition-1', <AppConfigScopeType.PUBLIC: 'public'>), ('definition-1', <AppConfigScopeType.USER: 'user'>), ('definition-2', <AppConfigScopeType.PUBLIC: 'public'>), ('definition-2', <AppConfigScopeType.USER: 'user'>)]
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

