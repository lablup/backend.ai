## app_config_allow_list

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_allow_list/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_allow_list/adapter.py)

Not exercised by any scenario: batch_load_fields.

### creating

#### [a-name-nothing-registers-cannot-be-opened](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

같은 이름의 정의가 없을 때 슈퍼관리자가 허용 항목을 만들려 하면, 정의 없음으로 거부된다

Given

- 등록되지 않은 이름과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_create — user-1이 unregistered을 공개 종류에 순위 없이 엶

Then

- 거부된다
  - 거부: AppConfigDefinitionNotFound

#### [a-rank-given-in-the-request-is-kept-as-is](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 기본값 사이의 순위를 주고 허용 항목을 만들면, 그 값이 그대로 저장된다

Given

- 허용 항목이 없는 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 도메인 종류에 순위 250로 엶

Then

- 만든 허용 항목 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 250
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [a-user-who-is-not-the-superadmin-may-not-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 아닌 사용자가 허용 항목을 만들려 하면, 역할로 거부된다

Given

- 허용 항목이 없는 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 공개 종류에 순위 없이 엶

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [leaving-the-rank-out-opens-the-domain-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 도메인 종류의 허용 항목을 만들면, 순위 200이 매겨진다. 이 문은 전역 역할이다

Given

- 허용 항목이 없는 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 도메인 종류에 순위 없이 엶

Then

- 만든 허용 항목 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.DOMAIN: 'domain'>
  - rank = 200
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [leaving-the-rank-out-opens-the-public-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 공개 종류의 허용 항목을 만들면, 순위 100이 매겨진다. 이 문은 전역 역할이다

Given

- 허용 항목이 없는 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 공개 종류에 순위 없이 엶

Then

- 만든 허용 항목 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.PUBLIC: 'public'>
  - rank = 100
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [leaving-the-rank-out-opens-the-user-kind-at-its-default-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

슈퍼관리자가 순위를 생략하고 사용자 종류의 허용 항목을 만들면, 순위 300이 매겨진다. 이 문은 전역 역할이다

Given

- 허용 항목이 없는 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 사용자 종류에 순위 없이 엶

Then

- 만든 허용 항목 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [opening-the-same-name-to-the-same-kind-twice-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

이미 그 종류에 열린 이름을 슈퍼관리자가 같은 종류에 다시 열면 거부되지만, 답이 겹친다고 말하지 않고 데이터베이스의 제약 위반이 그대로 올라온다

Given

- 공개 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 공개 종류에 순위 없이 엶

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [turning-enforcement-off-still-does-not-let-a-user-open-a-name](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_creating.py) — pass

엔티티 권한 집행을 꺼도 허용 항목 만들기는 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 허용 항목이 없는 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다

When

- AppConfigAllowListAdapter.admin_create — user-1이 config-1을 공개 종류에 순위 없이 엶

Then

- 거부된다
  - 거부: InsufficientPrivilege

### editing

#### [a-user-who-is-not-the-superadmin-may-not-change-a-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

같은 항목이 있고 슈퍼관리자가 아닌 사용자가 순위를 고치면, 권한 부족으로 거부된다

Given

- 사용자 스코프에 연 허용 항목 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목을 순위를 150으로 수정

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-edit-carrying-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

슈퍼관리자가 아무 값도 주지 않고 고치면, 아무것도 바뀌지 않은 노드가 온다

Given

- 사용자 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목을 아무 값도 주지 않고 수정

Then

- 심은 허용 항목 전체가 온다
  - id: 심은 허용 항목와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id의 순위를 고치면, 대상이 없다는 것으로 거부된다

Given

- 공개 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 아무것도 갖지 않은 id을 순위를 150으로 수정

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-changes-an-entrys-rank](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_editing.py) — pass

항목 하나가 있고 슈퍼관리자가 순위를 바꾸면, 순위는 새 값이고 이름과 종류는 그대로다

Given

- 사용자 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_update — user-1이 config-1의 항목을 순위를 150으로 수정

Then

- 심은 허용 항목 전체가 온다
  - id: 심은 허용 항목와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 150
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### purging

#### [a-user-who-is-not-the-superadmin-may-not-purge-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

같은 항목이 있고 슈퍼관리자가 아닌 사용자가 지우면, 권한 부족으로 거부된다

Given

- 사용자 스코프에 연 허용 항목 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목을 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-entry-holding-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

조각이 딸린 항목을 슈퍼관리자가 지우면, 조각이 막지 않고 지운 id를 실은 답이 온다

Given

- 조각이 딸린 공개 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'theme': 'light'}

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목을 지움

Then

- 지운 허용 항목의 id를 답한다
  - id: 심은 허용 항목와 같다

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 공개 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 아무것도 갖지 않은 id을 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_purging.py) — pass

조각이 딸리지 않은 항목을 슈퍼관리자가 지우면, 지운 id를 실은 답이 온다

Given

- 사용자 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_purge — user-1이 config-1의 항목을 지움

Then

- 지운 허용 항목의 id를 답한다
  - id: 심은 허용 항목와 같다

### reading

#### [a-user-who-is-not-the-superadmin-may-not-read-an-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

같은 항목이 있고 슈퍼관리자가 아닌 사용자가 조회하면, 권한 부족으로 거부된다. 항목은 어느 스코프에도 속하지 않아 역할로 열 수 없다

Given

- 사용자 스코프에 연 허용 항목 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 config-1의 항목으로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 권한 검사를 지나가는 사람만 이 답을 본다

Given

- 공개 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 아무것도 갖지 않은 id으로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-an-entry-by-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading.py) — pass

항목 하나가 있고 슈퍼관리자가 id로 조회하면, 그 항목 전체가 답으로 온다

Given

- 사용자 스코프에 연 허용 항목 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값

When

- AppConfigAllowListAdapter.admin_get — user-1이 config-1의 항목으로 조회

Then

- 심은 허용 항목 전체가 온다
  - id: 심은 허용 항목와 같다
  - config_name = 'config-1'
  - scope_type = <AppConfigScopeType.USER: 'user'>
  - rank = 300
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading_many

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

슈퍼관리자가 아닌 사용자가 항목 둘과 없는 id 하나를 한 번에 읽으면, 요청 전체가 막히는 것이 아니라 세 자리 모두 그 자리만 권한 부족으로 거부된다

Given

- 한 이름을 두 스코프에 연 허용 항목 둘과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 first-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 second-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 항목 둘과 아무것도 갖지 않은 id를 한 번에 조회

Then

- 있는 둘도 없는 id도 그 자리만 거부된다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-id-list-answers-empty-without-calling-anything](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다

Given

- 한 이름을 두 스코프에 연 허용 항목 둘과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 first-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 second-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - items = []

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_reading_many.py) — pass

슈퍼관리자가 항목 둘과 없는 id 하나를 한 번에 읽으면, 둘은 노드로 오고 없는 id 자리는 비어서 온다. 권한 검사를 지나가는 사람만 빈 자리를 본다

Given

- 한 이름을 두 스코프에 연 허용 항목 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 first-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 second-1: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.batch_load_by_ids — user-1이 항목 둘과 아무것도 갖지 않은 id를 한 번에 조회

Then

- 있는 둘은 노드로, 없는 id 자리는 비어서 온다
  - items = 3
  - items[0].id: 심은 첫째 항목와 같다
  - items[1].id: 심은 둘째 항목와 같다
  - items[2] = None

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 거부된다

Given

- 이름 2개에 각각 공개 스코프로 연 허용 항목들과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-2: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-by-name-keeps-only-that-names-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

이름 둘에 항목 넷이 있고 슈퍼관리자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 이름 2개에 각각 공개·사용자 스코프로 연 허용 항목들과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-3: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-4: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 이름 wanted-1으로 걸러 조회

Then

- 이름으로 고른 항목만 남는다
  - items = [('wanted-1', <AppConfigScopeType.PUBLIC: 'public'>), ('wanted-1', <AppConfigScopeType.USER: 'user'>)]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

#### [filtering-by-scope-kind-keeps-only-that-kinds-entries](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

세 종류에 항목이 하나씩 있고 슈퍼관리자가 사용자 종류로 걸러 훑으면, 사용자 항목만 남는다

Given

- 이름 1개에 각각 공개·도메인·사용자 스코프로 연 허용 항목들과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-2: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 사용자 종류로 걸러 조회

Then

- 사용자 종류의 항목만 남는다
  - items = [('wanted-1', <AppConfigScopeType.USER: 'user'>)]
  - total_count = 1

#### [leaving-the-page-size-out-answers-ten-with-a-next-page](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

항목 열하나가 있고 슈퍼관리자가 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 이름 11개에 각각 공개 스코프로 연 허용 항목들과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-2: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-3: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-3: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-4: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-4: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-5: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-5: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-6: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-6: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-7: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-7: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-8: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-8: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-9: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-9: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-10: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-10: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-11: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 열 건까지 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [ordering-by-rank-answers-in-rank-order](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

순위가 다른 항목 셋이 있고 슈퍼관리자가 순위 오름차순으로 훑으면, 순위 순서대로 온다

Given

- 이름 1개에 각각 공개·도메인·사용자 스코프로 연 허용 항목들과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-2: 도메인 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-3: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 순위 오름차순으로 전체 조회

Then

- 순위 순서대로 온다
  - items = [100, 200, 300]
  - total_count = 3

#### [the-superadmin-counts-every-entry](/tests/scenario/bai_scenario/manager/app_config_allow_list/test_searching.py) — pass

이름 둘에 항목 넷이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 넷을 모두 센다. 이 문은 전역 역할이다

Given

- 이름 2개에 각각 공개·사용자 스코프로 연 허용 항목들과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-2: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-3: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 허용 항목 entry-4: 사용자 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigAllowListAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 허용 항목이 모두, 그리고 그것만 세어진다
  - items = [('other-1', <AppConfigScopeType.PUBLIC: 'public'>), ('other-1', <AppConfigScopeType.USER: 'user'>), ('wanted-1', <AppConfigScopeType.PUBLIC: 'public'>), ('wanted-1', <AppConfigScopeType.USER: 'user'>)]
  - total_count = 4
  - has_next_page = False
  - has_previous_page = False

