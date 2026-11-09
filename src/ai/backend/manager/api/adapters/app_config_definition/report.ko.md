## app_config_definition

[배경](/src/ai/backend/manager/api/adapters/app_config_definition/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/app_config_definition/adapter.py)

시나리오: 미완성 1 / 6

- ops 구성 (4)
  - admin_create: 대표 성공 ✓ · 대표 거부 ✓
  - admin_get: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (2)
  - partial_bulk_purge: 성공 있음 3 · 거부 없음 (partial_bulk): SCENARIO-GAP
  - purge: 성공 있음 2 · 거부 있음 2 (single_entity)

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 ID 와 시각은 서버가 채운 노드가 반환됩니다](#registering-the-superadmin-registers-a-name) | 성공 |
| [이미 등록된 이름으로 superadmin 이 다시 등록하면 거부되지만, 응답이 이름 중복이라고 알려 주지 않고 데이터베이스의 제약 위반이 그대로 전파됩니다](#registering-a-name-already-registered-is-refused-as-a-constraint-violation) | 거부 |
| [일반 사용자가 설정 정의를 등록하려 하면, superadmin 권한이 없어 거부됩니다](#registering-a-user-who-is-not-the-superadmin-may-not-register-a-name) | 거부 |
| [RBAC 강제를 꺼도 일반 사용자의 설정 정의 등록은 거부됩니다](#registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name) | 거부 |

**admin_get**

| 시나리오 | 판정 |
|---|---|
| [설정 정의 하나가 있고 superadmin 이 ID 로 조회하면, 그 정의의 모든 필드가 반환됩니다](#reading-the-superadmin-reads-a-definition-by-id) | 성공 |
| [RBAC 강제를 끄면 권한이 없는 일반 사용자도 설정 정의를 조회할 수 있습니다](#reading-turning-enforcement-off-lets-a-plain-user-read) | 성공 |
| [같은 설정 정의가 있고 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부됩니다](#reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition) | 거부 |
| [superadmin 이 존재하지 않는 ID 로 조회하면, 대상을 찾을 수 없다는 이유로 거부됩니다. 권한 검사를 통과하는 사용자만 이 응답을 봅니다](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [설정 정의 셋이 있고 superadmin 이 필터 없이 전체를 검색하면, 셋 다 집계됩니다](#searching-the-superadmin-counts-every-definition) | 성공 |
| [일반 사용자가 전체를 검색하면, superadmin 권한이 없어 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-definitions) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [빈 ID 목록을 주면 빈 응답이 반환됩니다](#reading_many-an-empty-id-list-answers-empty) | 성공 |
| [superadmin 이 같은 설정 정의 ID 를 두 번 조회하면, 입력 순서를 보존해 같은 노드가 두 번 반환됩니다](#reading_many-duplicate-ids-keep-their-input-positions) | 성공 |
| [superadmin 이 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 ID 에 해당하는 항목은 비어 있습니다. 권한 검사를 통과하는 사용자만 빈 항목을 봅니다](#reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty) | 성공 |
| [superadmin 이 아닌 사용자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 요청 전체가 막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부됩니다](#reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [권한이 없는 일반 사용자가 설정 정의 둘을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-definitions) | 성공 |
| [global 스코프에서 설정 정의에 대한 영구 삭제 권한을 받은 일반 사용자가 설정 정의 둘을 한 번에 영구 삭제하면, 둘 다 처리된 목록에 오고 실패한 것은 없습니다](#partial_bulk_purging-a-user-granted-purge-in-global-purges-both-definitions-at-once) | 성공 |
| [superadmin 이 설정 정의 둘과 존재하지 않는 ID 를 한 번에 영구 삭제하면, 둘은 처리된 목록에 오고 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [허용 목록 항목과 설정 조각이 딸린 설정 정의를 superadmin 이 영구 삭제하면, 종속 행이 삭제를 막지 않고 정의의 ID 가 반환됩니다](#purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged) | 성공 |
| [종속 행이 없는 설정 정의를 superadmin 이 영구 삭제하면, 삭제한 ID 가 반환됩니다](#purging-the-superadmin-purges-a-definition) | 성공 |
| [같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 영구 삭제 권한이 없어 거부됩니다](#purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition) | 거부 |
| [superadmin 이 존재하지 않는 ID 를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부됩니다](#purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | 거부 |

### admin_create

<a id="registering-the-superadmin-registers-a-name"></a>

#### [the-superadmin-registers-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

superadmin 이 이름만 지정해 설정 정의를 등록하면, 이름은 지정한 그대로이고 ID 와 시각은 서버가 채운 노드가 반환됩니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_create: user-1 이 설정 이름 fresh-config 을 등록합니다

Then

- 등록한 설정 정의의 모든 필드가 반환됩니다
  - ID: 건너뜀: 데이터베이스가 생성합니다
  - config_name = 'fresh-config'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="registering-a-name-already-registered-is-refused-as-a-constraint-violation"></a>

#### [a-name-already-registered-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

이미 등록된 이름으로 superadmin 이 다시 등록하면 거부되지만, 응답이 이름 중복이라고 알려 주지 않고 데이터베이스의 제약 위반이 그대로 전파됩니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_create: user-1 이 설정 이름 config-1 을 등록합니다

Then

- 거부됩니다
  - 거부: UniqueConstraintViolationError

<a id="registering-a-user-who-is-not-the-superadmin-may-not-register-a-name"></a>

#### [a-user-who-is-not-the-superadmin-may-not-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

일반 사용자가 설정 정의를 등록하려 하면, superadmin 권한이 없어 거부됩니다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_create: user-1 이 설정 이름 fresh-config 을 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

<a id="registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

RBAC 강제를 꺼도 일반 사용자의 설정 정의 등록은 거부됩니다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_create: user-1 이 설정 이름 fresh-config 을 등록합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_get

<a id="reading-the-superadmin-reads-a-definition-by-id"></a>

#### [the-superadmin-reads-a-definition-by-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

설정 정의 하나가 있고 superadmin 이 ID 로 조회하면, 그 정의의 모든 필드가 반환됩니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_get: user-1 이 config-1 로 조회합니다

Then

- 미리 저장한 설정 정의의 모든 필드가 반환됩니다
  - ID: 미리 저장한 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading-turning-enforcement-off-lets-a-plain-user-read"></a>

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

RBAC 강제를 끄면 권한이 없는 일반 사용자도 설정 정의를 조회할 수 있습니다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_get: user-1 이 config-1 로 조회합니다

Then

- 미리 저장한 설정 정의의 모든 필드가 반환됩니다
  - ID: 미리 저장한 설정 정의와 같다
  - config_name = 'config-1'
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

같은 설정 정의가 있고 권한이 없는 일반 사용자가 조회하면, 엔티티 읽기 권한이 없어 거부됩니다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_get: user-1 이 config-1 로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

superadmin 이 존재하지 않는 ID 로 조회하면, 대상을 찾을 수 없다는 이유로 거부됩니다. 권한 검사를 통과하는 사용자만 이 응답을 봅니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_get: user-1 이 존재하지 않는 ID 로 조회합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### admin_search

<a id="searching-the-superadmin-counts-every-definition"></a>

#### [the-superadmin-counts-every-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py): pass

설정 정의 셋이 있고 superadmin 이 필터 없이 전체를 검색하면, 셋 다 집계됩니다

Given

- 설정 정의 3개와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 definition-2: 이 이름의 설정을 등록했습니다
  - 설정 정의 definition-3: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 설정 정의가 모두, 그리고 그것만 집계됩니다
  - items = ['definition-1', 'definition-2', 'definition-3']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-definitions"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py): pass

일반 사용자가 전체를 검색하면, superadmin 권한이 없어 거부됩니다

Given

- 설정 정의 3개와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 definition-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 definition-2: 이 이름의 설정을 등록했습니다
  - 설정 정의 definition-3: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading_many-an-empty-id-list-answers-empty"></a>

#### [an-empty-id-list-answers-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

빈 ID 목록을 주면 빈 응답이 반환됩니다

Given

- 설정 정의 둘과, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 이 빈 ID 목록으로 조회합니다

Then

- 빈 응답이 반환됩니다
  - items = []

<a id="reading_many-duplicate-ids-keep-their-input-positions"></a>

#### [duplicate-ids-keep-their-input-positions](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

superadmin 이 같은 설정 정의 ID 를 두 번 조회하면, 입력 순서를 보존해 같은 노드가 두 번 반환됩니다

Given

- 설정 정의 둘과, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 이 첫 번째 설정 정의의 ID 를 두 번 조회합니다

Then

- 중복 ID 의 두 항목에 같은 설정 정의가 반환됩니다
  - items = 2
  - items[0].ID: 미리 저장한 첫 번째 설정 정의와 같다
  - items[1].ID: 미리 저장한 첫 번째 설정 정의와 같다

<a id="reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty"></a>

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

superadmin 이 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 둘은 노드로 반환되고 없는 ID 에 해당하는 항목은 비어 있습니다. 권한 검사를 통과하는 사용자만 빈 항목을 봅니다

Given

- 설정 정의 둘과, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 이 first-1, second-1, 존재하지 않는 ID 를 한 번에 조회합니다

Then

- 있는 둘은 노드로 반환되고, 없는 ID 에 해당하는 항목은 비어 있습니다
  - items = 3
  - items[0].ID: 미리 저장한 첫째 설정 정의와 같다
  - items[1].ID: 미리 저장한 둘째 설정 정의와 같다
  - items[2] = None

<a id="reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id"></a>

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

superadmin 이 아닌 사용자가 설정 정의 둘과 없는 ID 하나를 한 번에 조회하면, 요청 전체가 막히는 것이 아니라 세 항목 모두 그 항목만 권한 부족으로 거부됩니다

Given

- 설정 정의 둘과, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 이 first-1, second-1, 존재하지 않는 ID 를 한 번에 조회합니다

Then

- 있는 둘도 없는 ID 도 그 항목만 거부됩니다
  - items = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-definitions"></a>

#### [a-user-granted-nothing-purges-none-of-several-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_partial_bulk_purging.py): pass

권한이 없는 일반 사용자가 설정 정의 둘을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 설정 정의 둘과, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.partial_bulk_purge: user-1 이 설정 정의 둘을 한 번에 영구 삭제합니다

Then

- 처리된 설정 정의 없이 둘 다 권한이 없다는 이유로 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 준비한 ID 와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 준비한 ID 와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-a-user-granted-purge-in-global-purges-both-definitions-at-once"></a>

#### [a-user-granted-purge-in-global-purges-both-definitions-at-once](/tests/scenario/bai_scenario/manager/app_config_definition/test_partial_bulk_purging.py): pass

global 스코프에서 설정 정의에 대한 영구 삭제 권한을 받은 일반 사용자가 설정 정의 둘을 한 번에 영구 삭제하면, 둘 다 처리된 목록에 오고 실패한 것은 없습니다

Given

- 설정 정의 둘과, global 스코프에서 설정 정의에 대한 HARD_DELETE 권한을 받은 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - global 스코프에서 설정 정의에 대한 HARD_DELETE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 global-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 global-1: app_config_definition 전체에 HARD_DELETE 허용
    - 일반 사용자 user-1: 역할 global-1 보유

When

- AppConfigDefinitionAdapter.partial_bulk_purge: user-1 이 설정 정의 둘을 한 번에 영구 삭제합니다

Then

- 설정 정의 둘은 처리된 목록에 오고, 실패한 것은 없습니다
  - successes count = 2
  - failed = []
  - successes[0].id: 준비한 ID 와 같다
  - successes[0].entity_id: 준비한 ID 와 같다
  - successes[0].config_name = 'first-1'
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 준비한 ID 와 같다
  - successes[1].entity_id: 준비한 ID 와 같다
  - successes[1].config_name = 'second-1'
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/app_config_definition/test_partial_bulk_purging.py): pass

superadmin 이 설정 정의 둘과 존재하지 않는 ID 를 한 번에 영구 삭제하면, 둘은 처리된 목록에 오고 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 설정 정의 둘과, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 first-1: 이 이름의 설정을 등록했습니다
  - 설정 정의 second-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.partial_bulk_purge: user-1 이 설정 정의 둘과 존재하지 않는 ID 를 한 번에 영구 삭제합니다

Then

- 설정 정의 둘은 처리된 목록에 오고, 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes: 준비한 ID 둘와 같다
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 ID 와 같다
  - failed[0].message: 'not found'를 담은 이유

### purge

<a id="purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged"></a>

#### [a-definition-holding-an-entry-and-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

허용 목록 항목과 설정 조각이 딸린 설정 정의를 superadmin 이 영구 삭제하면, 종속 행이 삭제를 막지 않고 정의의 ID 가 반환됩니다

Given

- 허용 목록 항목과 설정 조각이 딸린 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 허용 목록 항목 entry-1: 공개 스코프에서 이 이름의 설정을 지정할 수 있습니다, 순위는 그 스코프 종류의 기본값
  - 공개 스코프별 앱 설정 public-fragment-1: 값 {'theme': 'light'}
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.purge: user-1 이 config-1 을 영구 삭제합니다

Then

- 영구 삭제한 설정 정의의 ID 를 응답합니다
  - ID: 미리 저장한 설정 정의와 같다

<a id="purging-the-superadmin-purges-a-definition"></a>

#### [the-superadmin-purges-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

종속 행이 없는 설정 정의를 superadmin 이 영구 삭제하면, 삭제한 ID 가 반환됩니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.purge: user-1 이 config-1 을 영구 삭제합니다

Then

- 영구 삭제한 설정 정의의 ID 를 응답합니다
  - ID: 미리 저장한 설정 정의와 같다

<a id="purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

같은 설정 정의가 있고 권한이 없는 일반 사용자가 영구 삭제하면, 엔티티 영구 삭제 권한이 없어 거부됩니다

Given

- 설정 정의 하나와, 권한이 없는 일반 사용자 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.purge: user-1 이 config-1 을 영구 삭제합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

superadmin 이 존재하지 않는 ID 를 영구 삭제하면, 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 설정 정의 하나와, superadmin 한 명
  - 도메인 home-1
  - 설정 정의 config-1: 이 이름의 설정을 등록했습니다
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- AppConfigDefinitionAdapter.purge: user-1 이 존재하지 않는 ID 를 영구 삭제합니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

