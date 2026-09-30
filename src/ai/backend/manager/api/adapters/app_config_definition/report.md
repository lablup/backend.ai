## app_config_definition

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/app_config_definition/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_definition/adapter.py)

시나리오: 완성

- ops 로 구성 (4)
  - admin_create — 대표 성공 ✓ · 대표 실패 ✓
  - admin_get — 대표 성공 ✓ · 대표 실패 ✓
  - admin_search — 대표 성공 ✓ · 대표 실패 ✓
  - batch_load_by_ids — 대표 성공 ✓ · 대표 실패 ✓
- 직접 구현 (1)
  - admin_purge — 성공 있음 2 · 실패 있음 2 (single_entity)

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [슈퍼관리자가 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 ID와 시각은 서버가 채운 노드가 반환된다](#registering-the-superadmin-registers-a-name) | 성공 |
| [이미 등록된 이름으로 슈퍼관리자가 다시 등록하면 거부되지만, 응답이 이름 중복이라고 알려 주지 않고 데이터베이스의 제약 위반이 그대로 전파된다](#registering-a-name-already-registered-is-refused-as-a-constraint-violation) | 거부 |
| [일반 사용자가 설정 정의를 등록하려 하면, 슈퍼관리자 권한이 없어 거부된다](#registering-a-user-who-is-not-the-superadmin-may-not-register-a-name) | 거부 |
| [RBAC 강제를 꺼도 일반 사용자의 설정 정의 등록은 거부된다](#registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name) | 거부 |

**admin_get**

| 시나리오 | 판정 |
|---|---|
| [설정 정의 하나가 있고 슈퍼관리자가 ID로 조회하면, 그 정의의 모든 필드가 반환된다](#reading-the-superadmin-reads-a-definition-by-id) | 성공 |
| [RBAC 강제를 끄면 권한이 없는 일반 사용자도 설정 정의를 조회할 수 있다](#reading-turning-enforcement-off-lets-a-plain-user-read) | 성공 |
| [같은 설정 정의가 있고 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부된다](#reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition) | 거부 |
| [슈퍼관리자가 존재하지 않는 ID로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 권한 검사를 통과하는 사용자만 이 응답을 본다](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [설정 정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 셋 다 집계된다](#searching-the-superadmin-counts-every-definition) | 성공 |
| [일반 사용자가 전체를 검색하면, 슈퍼관리자 권한이 없어 거부된다](#searching-a-user-who-is-not-the-superadmin-may-not-search-definitions) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 ID 목록을 주면 빈 응답이 반환된다](#reading_many-an-empty-id-list-answers-empty) | 성공 |
| [슈퍼관리자가 같은 설정 정의 ID를 두 번 조회하면, 입력 순서를 보존해 같은 노드가 두 번 반환된다](#reading_many-duplicate-ids-keep-their-input-positions) | 성공 |
| [슈퍼관리자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 ID에 해당하는 항목은 비어 있다. 권한 검사를 통과하는 사용자만 빈 항목을 본다](#reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty) | 성공 |
| [슈퍼관리자가 아닌 사용자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 요청 전체가 막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부된다](#reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id) | 거부 |

**admin_purge**

| 시나리오 | 판정 |
|---|---|
| [허용 목록 항목과 설정 조각이 딸린 설정 정의를 슈퍼관리자가 영구 삭제하면, 종속 행이 삭제를 막지 않고 정의의 ID가 반환된다](#purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged) | 성공 |
| [종속 행이 없는 설정 정의를 슈퍼관리자가 영구 삭제하면, 삭제한 ID가 반환된다](#purging-the-superadmin-purges-a-definition) | 성공 |
| [같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 영구 삭제 권한이 없어 거부된다](#purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition) | 거부 |
| [슈퍼관리자가 존재하지 않는 ID를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다](#purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

### admin_create

<a id="registering-the-superadmin-registers-a-name"></a>

#### [the-superadmin-registers-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

슈퍼관리자가 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 ID와 시각은 서버가 채운 노드가 반환된다

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

- 등록한 설정 정의의 모든 필드가 반환된다
  - ID: 무시함 — 데이터베이스가 만든다
  - config_name = 'fresh-config'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="registering-a-name-already-registered-is-refused-as-a-constraint-violation"></a>

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

<a id="registering-a-user-who-is-not-the-superadmin-may-not-register-a-name"></a>

#### [a-user-who-is-not-the-superadmin-may-not-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

일반 사용자가 설정 정의를 등록하려 하면, 슈퍼관리자 권한이 없어 거부된다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
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

<a id="registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py) — pass

RBAC 강제를 꺼도 일반 사용자의 설정 정의 등록은 거부된다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
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

### admin_get

<a id="reading-the-superadmin-reads-a-definition-by-id"></a>

#### [the-superadmin-reads-a-definition-by-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

설정 정의 하나가 있고 슈퍼관리자가 ID로 조회하면, 그 정의의 모든 필드가 반환된다

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

- 미리 만들어 둔 설정 정의의 모든 필드가 반환된다
  - ID: 미리 만들어 둔 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading-turning-enforcement-off-lets-a-plain-user-read"></a>

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

RBAC 강제를 끄면 권한이 없는 일반 사용자도 설정 정의를 조회할 수 있다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
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

- 미리 만들어 둔 설정 정의의 모든 필드가 반환된다
  - ID: 미리 만들어 둔 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

같은 설정 정의가 있고 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부된다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
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

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py) — pass

슈퍼관리자가 존재하지 않는 ID로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. 권한 검사를 통과하는 사용자만 이 응답을 본다

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

- AppConfigDefinitionAdapter.admin_get — user-1이 존재하지 않는 ID(으)로 조회

Then

- 거부된다
  - 거부: EntityNotFoundError

### admin_search

<a id="searching-the-superadmin-counts-every-definition"></a>

#### [the-superadmin-counts-every-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

설정 정의 셋이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, 셋 다 집계된다

Given

- 설정 정의 3개와, 슈퍼관리자 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 definition-2: 이 이름의 설정이 등록돼 있다
  - 설정 정의 definition-3: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 미리 만들어 둔 설정 정의가 모두, 그리고 그것만 집계된다
  - items = ['definition-1', 'definition-2', 'definition-3']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-definitions"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py) — pass

일반 사용자가 전체를 검색하면, 슈퍼관리자 권한이 없어 거부된다

Given

- 설정 정의 3개와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 definition-2: 이 이름의 설정이 등록돼 있다
  - 설정 정의 definition-3: 이 이름의 설정이 등록돼 있다
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

### batch_load_by_ids

<a id="reading_many-an-empty-id-list-answers-empty"></a>

#### [an-empty-id-list-answers-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

빈 ID 목록을 주면 빈 응답이 반환된다

Given

- 설정 정의 둘과, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 빈 ID 목록으로 조회

Then

- 빈 응답이 반환된다
  - items = []

<a id="reading_many-duplicate-ids-keep-their-input-positions"></a>

#### [duplicate-ids-keep-their-input-positions](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 같은 설정 정의 ID를 두 번 조회하면, 입력 순서를 보존해 같은 노드가 두 번 반환된다

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

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 첫 번째 설정 정의의 ID를 두 번 조회

Then

- 중복 ID의 두 항목에 같은 설정 정의가 반환된다
  - items = 2
  - items[0].ID: 미리 만들어 둔 첫 번째 설정 정의와 같다
  - items[1].ID: 미리 만들어 둔 첫 번째 설정 정의와 같다

<a id="reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty"></a>

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 ID에 해당하는 항목은 비어 있다. 권한 검사를 통과하는 사용자만 빈 항목을 본다

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

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 존재하지 않는 ID를 한 번에 조회

Then

- 있는 둘은 노드로 반환되고, 없는 ID에 해당하는 항목은 비어 있다
  - items = 3
  - items[0].ID: 미리 만들어 둔 첫째 설정 정의와 같다
  - items[1].ID: 미리 만들어 둔 둘째 설정 정의와 같다
  - items[2] = None

<a id="reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id"></a>

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py) — pass

슈퍼관리자가 아닌 사용자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 요청 전체가 막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부된다

Given

- 설정 정의 둘과, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정이 등록돼 있다
  - 설정 정의 second-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.batch_load_by_ids — user-1이 first-1, second-1, 존재하지 않는 ID를 한 번에 조회

Then

- 있는 둘도 없는 ID도 그 항목만 거부된다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### admin_purge

<a id="purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged"></a>

#### [a-definition-holding-an-entry-and-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

허용 목록 항목과 설정 조각이 딸린 설정 정의를 슈퍼관리자가 영구 삭제하면, 종속 행이 삭제를 막지 않고 정의의 ID가 반환된다

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

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 영구 삭제

Then

- 영구 삭제한 설정 정의의 ID를 응답한다
  - ID: 미리 만들어 둔 설정 정의와 같다

<a id="purging-the-superadmin-purges-a-definition"></a>

#### [the-superadmin-purges-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

종속 행이 없는 설정 정의를 슈퍼관리자가 영구 삭제하면, 삭제한 ID가 반환된다

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

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 영구 삭제

Then

- 영구 삭제한 설정 정의의 ID를 응답한다
  - ID: 미리 만들어 둔 설정 정의와 같다

<a id="purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 영구 삭제 권한이 없어 거부된다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정이 등록돼 있다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- AppConfigDefinitionAdapter.admin_purge — user-1이 config-1 영구 삭제

Then

- 거부된다
  - 거부: NotEnoughPermission

<a id="purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py) — pass

슈퍼관리자가 존재하지 않는 ID를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다

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

- AppConfigDefinitionAdapter.admin_purge — user-1이 존재하지 않는 ID 영구 삭제

Then

- 거부된다
  - 거부: EntityNotFoundError

