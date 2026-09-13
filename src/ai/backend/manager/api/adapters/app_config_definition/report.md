## app_config_definition

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_definition/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_definition/adapter.py)

Not exercised by any scenario: batch_load_fields.

### purging

#### [a-definition-holding-an-entry-and-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

허용 목록 항목과 설정 조각이 딸린 설정 정의를 슈퍼관리자가 삭제하면, 딸린 것이 막지 않고 삭제한 id를 담은 응답이 반환된다

Given

- 허용 목록 항목과 설정 조각이 딸린 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있다, 순위는 그 스코프 종류의 기본값
  - 공개 설정 조각 public-fragment-1: 값 {'theme': 'light'}
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 삭제

Then

- 삭제한 설정 정의의 id를 응답한다
  - id: 미리 만들어 둔 설정 정의와 같다

#### [a-user-who-is-not-the-superadmin-may-not-purge-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

같은 설정 정의가 있고 슈퍼관리자가 아닌 사용자가 삭제하면, 권한 부족으로 거부된다

Given

- 설정 정의 하나와, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 존재하지 않는 id 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-purges-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

아무것도 딸리지 않은 설정 정의를 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 삭제

Then

- 삭제한 설정 정의의 id를 응답한다
  - id: 미리 만들어 둔 설정 정의와 같다

### reading

#### [a-user-who-is-not-the-superadmin-may-not-read-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

같은 설정 정의가 있고 슈퍼관리자가 아닌 사용자가 조회하면, 권한 부족으로 거부된다. 설정 정의는 어느 스코프에도 속하지 않아 역할로는 권한을 받을 수 없다

Given

- 설정 정의 하나와, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1(으)로 조회

Then

- 거부된다
  - 거부: NotEnoughPermission

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 권한 검사를 통과하는 사용자만 이 응답을 본다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 존재하지 않는 id(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

#### [the-superadmin-reads-a-definition-by-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

설정 정의 하나가 있고 슈퍼관리자가 id로 조회하면, 그 정의 전체가 반환된다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1(으)로 조회

Then

- 미리 만들어 둔 설정 정의 전체가 반환된다
  - id: 미리 만들어 둔 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

권한 검사를 끄면 아무 권한도 없는 사용자도 설정 정의를 조회할 수 있다. 조회는 역할이 아니라 권한 그래프로 보호되므로 스위치가 영향을 준다

Given

- 설정 정의 하나와, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_get — user-1이 config-1(으)로 조회

Then

- 미리 만들어 둔 설정 정의 전체가 반환된다
  - id: 미리 만들어 둔 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

### reading_many

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 아닌 사용자가 설정 정의 둘과 없는 id 하나를 한 번에 조회하면, 요청 전체가 막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부된다

Given

- 설정 정의 둘과, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 존재하지 않는 id를 한 번에 조회

Then

- 있는 둘도 없는 id도 그 항목만 거부된다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

#### [an-empty-id-list-answers-empty-without-calling-anything](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

빈 id 목록을 주면 빈 응답이 반환된다. 하위 계층을 호출하지 않는다

Given

- 설정 정의 둘과, 아무 권한도 없는 사용자 한 명
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

- 빈 응답이 반환된다
  - items = []

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 설정 정의 둘과 없는 id 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 id 자리는 비어 있다. 권한 검사를 통과하는 사용자만 빈 항목을 본다

Given

- 설정 정의 둘과, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 존재하지 않는 id를 한 번에 조회

Then

- 있는 둘은 노드로, 없는 id 자리는 비어서 반환된다
  - items = 3
  - items[0].id: 미리 만들어 둔 첫째 설정 정의와 같다
  - items[1].id: 미리 만들어 둔 둘째 설정 정의와 같다
  - items[2] = None

### registering

#### [a-name-already-registered-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

이미 등록된 이름으로 슈퍼관리자가 다시 등록하면 거부되지만, 응답이 이름 중복이라고 알려 주지 않고 데이터베이스의 제약 위반이 그대로 전파된다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 설정 이름 config-1 등록

Then

- 거부된다
  - 거부: UniqueConstraintViolationError

#### [a-user-who-is-not-the-superadmin-may-not-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

슈퍼관리자가 아닌 사용자가 설정 정의를 등록하려 하면, 역할 부족으로 거부된다

Given

- 설정 정의 하나와, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 설정 이름 fresh-config 등록

Then

- 거부된다
  - 거부: InsufficientPrivilege

#### [the-superadmin-registers-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

슈퍼관리자가 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 id와 시각은 서버가 채운 노드가 반환된다. 등록은 전역 역할로 보호된다

Given

- 설정 정의 하나와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 설정 이름 fresh-config 등록

Then

- 등록한 설정 정의 전체가 반환된다
  - id: 무시함 — 데이터베이스가 만든다
  - config_name = 'fresh-config'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

#### [turning-enforcement-off-still-does-not-let-a-user-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

권한 검사를 꺼도 설정 정의 등록은 여전히 거부된다. 등록은 권한 그래프가 아니라 역할로 보호되기 때문이다

Given

- 설정 정의 하나와, 아무 권한도 없는 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_create — user-1이 설정 이름 fresh-config 등록

Then

- 거부된다
  - 거부: InsufficientPrivilege

### searching

#### [a-user-who-is-not-the-superadmin-may-not-search-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

슈퍼관리자가 아닌 사용자가 전체를 검색하면, 역할 부족으로 거부된다

Given

- 설정 정의 3개와, 아무 권한도 없는 사용자 한 명
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

이름이 다른 설정 정의 여럿이 있고 슈퍼관리자가 이름 필터로 검색하면, 그 이름의 정의만 반환된다

Given

- 설정 정의 3개와, 슈퍼관리자 한 명
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

- AppConfigDefinitionAdapter.admin_search — user-1이 wanted-1 이름 필터로 조회

Then

- 이름 필터에 맞는 설정 정의만 반환된다
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

#### [leaving-the-page-size-out-answers-ten-with-a-next-page](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

설정 정의 11개가 있고 슈퍼관리자가 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다

Given

- 설정 정의 11개와, 슈퍼관리자 한 명
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

- 10건까지 반환되고 다음 페이지가 있다고 응답한다
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

#### [ordering-by-name-answers-in-name-order](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

설정 정의 셋이 있고 슈퍼관리자가 이름 오름차순으로 검색하면, 이름 순서대로 반환된다

Given

- 설정 정의 3개와, 슈퍼관리자 한 명
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

- 이름 순서대로 반환된다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3

#### [the-superadmin-counts-every-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

설정 정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 셋 다 집계된다. 검색은 전역 역할로 보호된다

Given

- 설정 정의 3개와, 슈퍼관리자 한 명
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

- 미리 만들어 둔 설정 정의가 모두, 그리고 그것만 집계된다
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

