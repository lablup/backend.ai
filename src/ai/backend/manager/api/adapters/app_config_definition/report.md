## app_config_definition

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_definition/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_definition/adapter.py)

Not exercised by any scenario: batch_load_fields.

### purging

#### [a-definition-holding-an-entry-and-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

허용 항목과 조각이 딸린 정의를 슈퍼관리자가 지우면, 딸린 것이 막지 않고 지운 id를 실은 답이 온다

Given

- 허용 항목과 조각이 딸린 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 항목 entry-1: 공개 스코프가 이 이름을 채울 수 있다, 순위는 그 종류의 기본값
  - 공개 조각 public-fragment-1: 값 {'theme': 'light'}
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1를 지움

Then

- 지운 정의의 id를 답한다
  - id: 심은 정의와 같다

#### [a-user-who-is-not-the-superadmin-may-not-purge-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

같은 정의가 있고 슈퍼관리자가 아닌 사용자가 지우면, 권한 부족으로 거부된다

Given

- 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1를 지움

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 아무것도 갖지 않은 id를 지움

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

아무것도 딸리지 않은 정의를 슈퍼관리자가 지우면, 지운 id를 실은 답이 온다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1를 지움

Then

- 지운 정의의 id를 답한다
  - id: 심은 정의와 같다

### reading

#### [a-user-who-is-not-the-superadmin-may-not-read-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

같은 정의가 있고 슈퍼관리자가 아닌 사용자가 조회하면, 권한 부족으로 거부된다. 정의는 어느 스코프에도 속하지 않아 역할로 열 수 없다

Given

- 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

슈퍼관리자가 아무것도 갖지 않은 id로 조회하면, 대상이 없다는 것으로 거부된다. 권한 검사를 지나가는 사람만 이 답을 본다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 아무것도 갖지 않은 id로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-a-definition-by-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

정의 하나가 있고 슈퍼관리자가 id로 조회하면, 그 정의 전체가 답으로 온다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1로 조회

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 정의를 읽는다. 이 문은 역할이 아니라 권한 그래프가 지키므로 스위치가 통한다

Given

- 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1로 조회

Then

- 심은 정의 전체가 온다
  - id: 심은 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading_many

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 아닌 사용자가 정의 둘과 없는 id 하나를 한 번에 읽으면, 요청 전체가 막히는 것이 아니라 세 자리 모두 그 자리만 권한 부족으로 거부된다

Given

- 정의 둘과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 아무것도 갖지 않은 id를 한 번에 조회

Then

- 있는 둘도 없는 id도 그 자리만 거부된다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-id-list-answers-empty-without-calling-anything](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

빈 id 목록을 주면 빈 답이 온다. 배선을 부르지 않는다

Given

- 정의 둘과, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 빈 id 목록으로 조회

Then

- 빈 답이 온다
  - items = []

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 정의 둘과 없는 id 하나를 한 번에 읽으면, 둘은 노드로 오고 없는 id 자리는 비어서 온다. 권한 검사를 지나가는 사람만 빈 자리를 본다

Given

- 정의 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 아무것도 갖지 않은 id를 한 번에 조회

Then

- 있는 둘은 노드로, 없는 id 자리는 비어서 온다
  - items = 3
  - items[0].id: 심은 첫째 정의와 같다
  - items[1].id: 심은 둘째 정의와 같다
  - items[2] = None

### registering

#### [a-name-already-registered-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

이미 등록된 이름으로 슈퍼관리자가 다시 등록하면 거부되지만, 답이 이름이 겹친다고 말하지 않고 데이터베이스의 제약 위반이 그대로 올라온다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 config-1을 등록

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

슈퍼관리자가 아닌 사용자가 정의를 등록하려 하면, 역할로 거부된다

Given

- 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 fresh-config을 등록

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-registers-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

슈퍼관리자가 이름만 주고 정의를 등록하면, 이름은 준 그대로이고 id와 시각은 서버가 채운 노드가 답으로 온다. 이 문은 전역 역할이다

Given

- 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 fresh-config을 등록

Then

- 등록한 정의 전체가 온다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'fresh-config'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-still-does-not-let-a-user-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

엔티티 권한 집행을 꺼도 정의 등록은 여전히 막힌다. 이 문은 권한 그래프가 아니라 역할이 지키기 때문이다

Given

- 정의 하나와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 fresh-config을 등록

Then

- 거부된다
  - 거부: InsufficientPrivilege

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체를 훑으면, 역할로 거부된다

Given

- 정의 3개와, 아무 권한도 받지 않은 사용자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [filtering-by-name-keeps-only-that-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

이름이 다른 정의 여럿이 있고 슈퍼관리자가 이름으로 걸러 훑으면, 그 이름의 것만 남는다

Given

- 정의 3개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 이름 wanted-1으로 걸러 조회

Then

- 이름으로 고른 정의만 남는다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [leaving-the-page-size-out-answers-ten-with-a-next-page](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

정의 열하나가 있고 슈퍼관리자가 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다

Given

- 정의 11개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-3: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-4: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-5: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-6: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-7: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-8: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-9: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-10: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 열 건까지 오고 다음 쪽이 있다고 답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [ordering-by-name-answers-in-name-order](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

정의 셋이 있고 슈퍼관리자가 이름 오름차순으로 훑으면, 이름 순서대로 온다

Given

- 정의 3개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 이름 오름차순으로 전체 조회

Then

- 이름 순서대로 온다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3

#### [the-superadmin-counts-every-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 훑으면, 셋을 모두 센다. 이 문은 전역 역할이다

Given

- 정의 3개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 wanted-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 other-2: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 심은 정의가 모두, 그리고 그것만 세어진다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

