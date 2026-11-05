## system_session_environ

[배경](/src/ai/backend/manager/api/adapters/system_session_environ/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/system_session_environ/adapter.py)

시나리오: 완성

- ops 구성 (7)
  - bulk_get_ids: 대표 성공 ✓ · 대표 거부 ✓
  - delete: 대표 성공 ✓ · 대표 거부 ✓
  - global_search: 대표 성공 ✓ · 대표 거부 ✓
  - purge: 대표 성공 ✓ · 대표 거부 ✓
  - restore: 대표 성공 ✓ · 대표 거부 ✓
  - scoped_search: 대표 성공 ✓ · 대표 거부 ✓
  - update: 대표 성공 ✓ · 대표 거부 ✓
- 직접 구현 (2)
  - create: 성공 있음 1 · 거부 있음 4 (scope)
  - public_list_value_sources: 성공 있음 1 · 거부 있음 1 (public)

**bulk_get_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다](#reading-the-superadmin-reads-several-environs-in-the-requested-order) | 성공 |
| [아무 권한도 받지 않은 사용자가 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다](#reading-a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id) | 거부 |

**delete**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 시스템 세션 환경변수를 지우면 지운 시각을 실은 행 전체가 반환됩니다](#deleting-the-superadmin-deletes-an-environ) | 성공 |
| [아무 권한도 받지 않은 사용자가 지우려 하면 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-delete-an-environ) | 거부 |
| [superadmin 이 존재하지 않는 id 를 지우려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#deleting-deleting-an-environ-id-nothing-answers-to-is-not-found) | 거부 |

**global_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 범위를 가리지 않고 검색하면 미리 저장한 행이 모두 반환됩니다. 이 호출은 전역 역할을 검사합니다](#searching-the-superadmin-searching-every-scope-counts-every-row) | 성공 |
| [superadmin 이 아닌 사용자가 범위를 가리지 않고 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-scope) | 거부 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 시스템 세션 환경변수를 완전히 지우면 지운 행의 id 가 반환됩니다](#purging-the-superadmin-purges-an-environ) | 성공 |
| [아무 권한도 받지 않은 사용자가 완전히 지우려 하면 권한 부족으로 거부됩니다](#purging-a-user-granted-nothing-may-not-purge-an-environ) | 거부 |
| [superadmin 이 존재하지 않는 id 를 완전히 지우려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#purging-purging-an-environ-id-nothing-answers-to-is-not-found) | 거부 |

**restore**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 지운 시스템 세션 환경변수를 되살리면 지운 시각이 비워진 행 전체가 반환됩니다](#deleting-the-superadmin-restores-a-deleted-environ) | 성공 |
| [아무 권한도 받지 않은 사용자가 되살리려 하면 권한 부족으로 거부됩니다](#deleting-a-user-granted-nothing-may-not-restore-an-environ) | 거부 |
| [superadmin 이 존재하지 않는 id 를 되살리려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#deleting-restoring-an-environ-id-nothing-answers-to-is-not-found) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 public 범위를 검색하면 그 범위의 미리 저장한 행이 모두 반환됩니다](#searching-the-superadmin-searching-public-counts-the-public-rows) | 성공 |
| [아무 권한도 받지 않은 사용자가 public 범위를 검색하려 하면 권한 부족으로 거부됩니다](#searching-a-user-granted-nothing-may-not-search-the-public-scope) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 시스템 세션 환경변수의 이름을 바꾸면 새 이름과 이번 실행의 수정 시각을 실은 행 전체가 반환됩니다](#editing-the-superadmin-changes-the-key-of-an-environ) | 성공 |
| [아무 권한도 받지 않은 사용자가 이름을 바꾸려 하면 권한 부족으로 거부됩니다](#editing-a-user-granted-nothing-may-not-edit-an-environ) | 거부 |
| [지운 행의 이름을 바꾸려 하면 먼저 복원하라는 이유로 거부됩니다](#editing-editing-a-deleted-environ-is-refused) | 거부 |
| [superadmin 이 존재하지 않는 id 의 이름을 바꾸려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#editing-editing-an-environ-id-nothing-answers-to-is-not-found) | 거부 |
| [같은 범위에서 다른 행이 쓰는 이름으로 바꾸려 하면 거부됩니다](#editing-editing-an-environ-to-a-key-another-row-holds-is-refused) | 거부 |

**create**

| 시나리오 | 판정 |
|---|---|
| [public 에서 등록 권한을 받은 사용자가 시스템 세션 환경변수를 등록하면 등록한 행 전체가 반환됩니다](#creating-a-user-granted-create-registers-an-environ-in-public) | 성공 |
| [아무 권한도 받지 않은 사용자가 시스템 세션 환경변수를 등록하려 하면 권한 부족으로 거부됩니다](#creating-a-user-granted-nothing-may-not-create-an-environ) | 거부 |
| [없는 도메인에 등록하려 하면 대상을 찾을 수 없다는 이유로 거부됩니다](#creating-registering-an-environ-at-a-missing-domain-is-refused) | 거부 |
| [같은 범위에서 이미 쓰이는 이름으로 등록하려 하면 거부됩니다](#creating-registering-an-environ-under-a-key-already-held-is-refused) | 거부 |
| [매니저가 모르는 값 출처로 등록하려 하면 거부됩니다](#creating-registering-an-environ-with-an-unknown-value-source-is-refused) | 거부 |

**public_list_value_sources**

| 시나리오 | 판정 |
|---|---|
| [인증된 사용자면 누구나 매니저가 제공하는 값 출처 목록을 읽을 수 있습니다](#reading-any-authenticated-user-reads-the-value-sources) | 성공 |
| [호출자 없이 값 출처 목록을 읽으려 하면 거부됩니다. 이 호출은 인증만 검사합니다](#reading-a-call-with-no-caller-is-refused-the-value-sources) | 거부 |

### bulk_get_ids

<a id="reading-the-superadmin-reads-several-environs-in-the-requested-order"></a>

#### [the-superadmin-reads-several-environs-in-the-requested-order](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

superadmin 이 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.bulk_get_ids: user-1이 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 번에 조회합니다

Then

- 미리 저장한 행은 요청한 순서대로 반환되고, 존재하지 않는 id 의 항목은 비어 있습니다
  - length = 3
  - [0].key = 'SCENARIO_SEEDED_KEY'
  - [1] = None
  - [2].key = 'SCENARIO_OTHER_KEY'

<a id="reading-a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

아무 권한도 받지 않은 사용자가 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.bulk_get_ids: user-1이 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 번에 조회합니다

Then

- 항목마다 권한 부족 거부가 담겨 반환됩니다
  - length = 3
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission
  - 거부: NotEnoughPermission

### delete

<a id="deleting-the-superadmin-deletes-an-environ"></a>

#### [the-superadmin-deletes-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

superadmin 이 시스템 세션 환경변수를 지우면 지운 시각을 실은 행 전체가 반환됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.delete: user-1이 SCENARIO_SEEDED_KEY 를 지웁니다

Then

- 미리 저장한 행 전체가 반환되고, 지운 시각과 수정 시각이 이번 실행의 시각입니다
  - entity_id: 미리 저장한 행와 같다
  - key = 'SCENARIO_SEEDED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: 그 행이 묶인 범위의 id 와 같다
  - created_at: 미리 저장한 행의 생성 시각와 같다
  - updated_at: 이 실행이 쓴 시각
  - deleted_at: 이 실행이 쓴 시각

<a id="deleting-a-user-granted-nothing-may-not-delete-an-environ"></a>

#### [a-user-granted-nothing-may-not-delete-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 지우려 하면 권한 부족으로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.delete: user-1이 SCENARIO_SEEDED_KEY 를 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-deleting-an-environ-id-nothing-answers-to-is-not-found"></a>

#### [deleting-an-environ-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

superadmin 이 존재하지 않는 id 를 지우려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.delete: user-1이 존재하지 않는 id 를 지웁니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### global_search

<a id="searching-the-superadmin-searching-every-scope-counts-every-row"></a>

#### [the-superadmin-searching-every-scope-counts-every-row](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

superadmin 이 범위를 가리지 않고 검색하면 미리 저장한 행이 모두 반환됩니다. 이 호출은 전역 역할을 검사합니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.global_search: user-1이 범위를 가리지 않고 시스템 세션 환경변수를 검색합니다

Then

- 미리 저장한 행이 모두 반환됩니다
  - items: 미리 저장한 행와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-scope"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-scope](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

superadmin 이 아닌 사용자가 범위를 가리지 않고 검색하려 하면 권한 부족으로 거부됩니다. 이 호출은 전역 역할을 검사합니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.global_search: user-1이 범위를 가리지 않고 시스템 세션 환경변수를 검색합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### purge

<a id="purging-the-superadmin-purges-an-environ"></a>

#### [the-superadmin-purges-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_purging.py): pass

superadmin 이 시스템 세션 환경변수를 완전히 지우면 지운 행의 id 가 반환됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.purge: user-1이 SCENARIO_SEEDED_KEY 를 완전히 지웁니다

Then

- 완전히 지운 행의 id 가 반환됩니다
  - entity_id: 미리 저장한 행와 같다

<a id="purging-a-user-granted-nothing-may-not-purge-an-environ"></a>

#### [a-user-granted-nothing-may-not-purge-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_purging.py): pass

아무 권한도 받지 않은 사용자가 완전히 지우려 하면 권한 부족으로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.purge: user-1이 SCENARIO_SEEDED_KEY 를 완전히 지웁니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="purging-purging-an-environ-id-nothing-answers-to-is-not-found"></a>

#### [purging-an-environ-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/system_session_environ/test_purging.py): pass

superadmin 이 존재하지 않는 id 를 완전히 지우려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.purge: user-1이 존재하지 않는 id 를 완전히 지웁니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### restore

<a id="deleting-the-superadmin-restores-a-deleted-environ"></a>

#### [the-superadmin-restores-a-deleted-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

superadmin 이 지운 시스템 세션 환경변수를 되살리면 지운 시각이 비워진 행 전체가 반환됩니다

Given

- public 범위에서 지운 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 삭제된 시스템 세션 환경변수 deleted-environ-1: 지운 시각이 기록돼 있습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.restore: user-1이 SCENARIO_SEEDED_KEY 를 되살립니다

Then

- 미리 저장한 행 전체가 반환되고, 지운 시각은 비어 있으며 수정 시각은 이번 실행의 시각입니다
  - entity_id: 미리 저장한 행와 같다
  - key = 'SCENARIO_SEEDED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: 그 행이 묶인 범위의 id 와 같다
  - created_at: 미리 저장한 행의 생성 시각와 같다
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="deleting-a-user-granted-nothing-may-not-restore-an-environ"></a>

#### [a-user-granted-nothing-may-not-restore-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

아무 권한도 받지 않은 사용자가 되살리려 하면 권한 부족으로 거부됩니다

Given

- public 범위에서 지운 시스템 세션 환경변수 하나와, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 삭제된 시스템 세션 환경변수 deleted-environ-1: 지운 시각이 기록돼 있습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.restore: user-1이 SCENARIO_SEEDED_KEY 를 되살립니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="deleting-restoring-an-environ-id-nothing-answers-to-is-not-found"></a>

#### [restoring-an-environ-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

superadmin 이 존재하지 않는 id 를 되살리려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.restore: user-1이 존재하지 않는 id 를 되살립니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

### scoped_search

<a id="searching-the-superadmin-searching-public-counts-the-public-rows"></a>

#### [the-superadmin-searching-public-counts-the-public-rows](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

superadmin 이 public 범위를 검색하면 그 범위의 미리 저장한 행이 모두 반환됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.scoped_search: user-1이 public 범위의 시스템 세션 환경변수를 검색합니다

Then

- 미리 저장한 행이 모두 반환됩니다
  - items: 미리 저장한 행와 같다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-the-public-scope"></a>

#### [a-user-granted-nothing-may-not-search-the-public-scope](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

아무 권한도 받지 않은 사용자가 public 범위를 검색하려 하면 권한 부족으로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.scoped_search: user-1이 public 범위의 시스템 세션 환경변수를 검색합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="editing-the-superadmin-changes-the-key-of-an-environ"></a>

#### [the-superadmin-changes-the-key-of-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

superadmin 이 시스템 세션 환경변수의 이름을 바꾸면 새 이름과 이번 실행의 수정 시각을 실은 행 전체가 반환됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.update: user-1이 SCENARIO_SEEDED_KEY 의 이름을 SCENARIO_EDITED_KEY 로 바꿉니다

Then

- 미리 저장한 행 전체가 반환됩니다
  - entity_id: 미리 저장한 행와 같다
  - key = 'SCENARIO_EDITED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: 그 행이 묶인 범위의 id 와 같다
  - created_at: 미리 저장한 행의 생성 시각와 같다
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-edit-an-environ"></a>

#### [a-user-granted-nothing-may-not-edit-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

아무 권한도 받지 않은 사용자가 이름을 바꾸려 하면 권한 부족으로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, 일반 사용자 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.update: user-1이 SCENARIO_SEEDED_KEY 의 이름을 SCENARIO_EDITED_KEY 로 바꿉니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="editing-editing-a-deleted-environ-is-refused"></a>

#### [editing-a-deleted-environ-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

지운 행의 이름을 바꾸려 하면 먼저 복원하라는 이유로 거부됩니다

Given

- public 범위에서 지운 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 삭제된 시스템 세션 환경변수 deleted-environ-1: 지운 시각이 기록돼 있습니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.update: user-1이 SCENARIO_SEEDED_KEY 의 이름을 SCENARIO_EDITED_KEY 로 바꿉니다

Then

- 거부됩니다
  - 거부: SystemSessionEnvironDeleted

<a id="editing-editing-an-environ-id-nothing-answers-to-is-not-found"></a>

#### [editing-an-environ-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

superadmin 이 존재하지 않는 id 의 이름을 바꾸려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 하나와, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.update: user-1이 존재하지 않는 id 의 이름을 SCENARIO_EDITED_KEY 로 바꿉니다

Then

- 거부됩니다
  - 거부: EntityNotFoundError

<a id="editing-editing-an-environ-to-a-key-another-row-holds-is-refused"></a>

#### [editing-an-environ-to-a-key-another-row-holds-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

같은 범위에서 다른 행이 쓰는 이름으로 바꾸려 하면 거부됩니다

Given

- public 범위에 등록된 시스템 세션 환경변수 둘과, superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 시스템 세션 환경변수 SCENARIO_OTHER_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.update: user-1이 SCENARIO_SEEDED_KEY 의 이름을 SCENARIO_OTHER_KEY 로 바꿉니다

Then

- 거부됩니다
  - 거부: SystemSessionEnvironKeyConflict

### create

<a id="creating-a-user-granted-create-registers-an-environ-in-public"></a>

#### [a-user-granted-create-registers-an-environ-in-public](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

public 에서 등록 권한을 받은 사용자가 시스템 세션 환경변수를 등록하면 등록한 행 전체가 반환됩니다

Given

- public 에서 시스템 세션 환경변수에 CREATE 권한을 받은 사용자 한 명
  - 도메인 home-1
  - public 에서 시스템 세션 환경변수에 CREATE 권한을 받은 사용자 준비
    - 도메인에 속한 사용자 한 명 준비
      - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
      - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
      - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
      - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 역할 environ-writer-1: 부여된 스코프 안에서만 적용됩니다
    - 역할 environ-writer-1: system_session_environ 전체에 CREATE 허용
    - 일반 사용자 user-1: 역할 environ-writer-1 보유

When

- SystemSessionEnvironAdapter.create: user-1이 시스템 세션 환경변수를 등록합니다

Then

- 등록한 행 전체가 반환됩니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - key = 'SCENARIO_CREATED_KEY'
  - value_source = 'user_email'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: public 범위의 id 와 같다
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-create-an-environ"></a>

#### [a-user-granted-nothing-may-not-create-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

아무 권한도 받지 않은 사용자가 시스템 세션 환경변수를 등록하려 하면 권한 부족으로 거부됩니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.create: user-1이 시스템 세션 환경변수를 등록합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

<a id="creating-registering-an-environ-at-a-missing-domain-is-refused"></a>

#### [registering-an-environ-at-a-missing-domain-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

없는 도메인에 등록하려 하면 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.create: user-1이 시스템 세션 환경변수를 등록합니다

Then

- 거부됩니다
  - 거부: DomainNotFound

<a id="creating-registering-an-environ-under-a-key-already-held-is-refused"></a>

#### [registering-an-environ-under-a-key-already-held-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

같은 범위에서 이미 쓰이는 이름으로 등록하려 하면 거부됩니다

Given

- 이미 등록된 행 하나와 superadmin 한 명
  - 시스템 세션 환경변수 SCENARIO_SEEDED_KEY: public 범위에서 session_id 값을 주입합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.create: user-1이 시스템 세션 환경변수를 등록합니다

Then

- 거부됩니다
  - 거부: SystemSessionEnvironKeyConflict

<a id="creating-registering-an-environ-with-an-unknown-value-source-is-refused"></a>

#### [registering-an-environ-with-an-unknown-value-source-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

매니저가 모르는 값 출처로 등록하려 하면 거부됩니다

Given

- superadmin 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.create: user-1이 시스템 세션 환경변수를 등록합니다

Then

- 거부됩니다
  - 거부: UnknownSystemSessionEnvironValueSource

### public_list_value_sources

<a id="reading-any-authenticated-user-reads-the-value-sources"></a>

#### [any-authenticated-user-reads-the-value-sources](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

인증된 사용자면 누구나 매니저가 제공하는 값 출처 목록을 읽을 수 있습니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.public_list_value_sources: user-1이 매니저가 제공하는 값 출처를 읽습니다

Then

- 매니저가 제공하는 값 출처가 모두 반환됩니다
  - items = ['session_id', 'session_name', 'cluster_size', 'cluster_replicas', 'cluster_hosts', 'preopen_ports', 'user_uuid', 'user_email', 'user_name', 'access_key']

<a id="reading-a-call-with-no-caller-is-refused-the-value-sources"></a>

#### [a-call-with-no-caller-is-refused-the-value-sources](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

호출자 없이 값 출처 목록을 읽으려 하면 거부됩니다. 이 호출은 인증만 검사합니다

Given

- 일반 사용자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- SystemSessionEnvironAdapter.public_list_value_sources: user-1이 매니저가 제공하는 값 출처를 읽습니다

Then

- 거부됩니다
  - 거부: UserNotFound

