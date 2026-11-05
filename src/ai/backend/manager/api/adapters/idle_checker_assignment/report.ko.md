## idle_checker_assignment

[배경](/src/ai/backend/manager/api/adapters/idle_checker_assignment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/idle_checker_assignment/adapter.py)

시나리오: 미완성 2 / 7

- 직접 구현 (7)
  - admin_create: 성공 있음 1 · 거부 있음 1 (relation)
  - admin_search: 성공 있음 1 · 거부 있음 1 (global_scope)
  - partial_bulk_purge: 성공 있음 3 · 거부 없음 (relation): SCENARIO-GAP
  - partial_bulk_update: 성공 있음 3 · 거부 없음 (relation): SCENARIO-GAP
  - purge: 성공 있음 1 · 거부 있음 1 (relation)
  - scoped_search: 성공 있음 1 · 거부 있음 1 (scope)
  - update: 성공 있음 1 · 거부 있음 1 (relation)

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 검사기를 도메인에 켜면, 요청에서 지정한 검사기와 도메인을 잇는 할당이 활성 상태로 반환됩니다](#creating-the-superadmin-enables-an-idle-checker-on-a-domain) | 성공 |
| [검사기와 도메인이 있고 사용자 컨텍스트 없이 검사기를 도메인에 켜려 하면, 권한 부족으로 거부됩니다](#creating-an-assignment-created-without-a-user-is-refused) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [global 역할로 검사하는 연산이므로 superadmin 이 검색하면, 심은 할당이 모두 한 번씩 집계되어 반환됩니다](#searching-the-superadmin-searches-idle-checker-assignments) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 검색하면, 역할 부족으로 거부됩니다](#searching-an-assignment-search-carrying-no-user-is-refused) | 거부 |

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 삭제한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 한 번에 purge 하면, 답이 와서 모두 호출자를 알 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-an-assignment-purge-carrying-no-user-fails-every-item) | 성공 |
| [superadmin 이 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제하기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 비활성화하려 하면, 비활성화한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 한 번에 끄려 하면, 답이 와서 모두 호출자를 알 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-an-assignment-update-carrying-no-user-fails-every-item) | 성공 |
| [superadmin 이 할당 여럿을 한 번에 비활성화하면, 모두 비활성 할당으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-disables-several-assignments-at-once) | 성공 |

**purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 할당 하나를 purge 하면, 요청에 넣은 할당의 id 로 반환됩니다](#retiring-the-superadmin-purges-an-idle-checker-assignment) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 하나를 purge 하려 하면, 대상을 찾을 수 없다는 이유로 거부됩니다](#retiring-an-assignment-purge-carrying-no-user-is-refused) | 거부 |

**scoped_search**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 도메인 둘을 스코프로 검색하면, 그 도메인들의 할당이 모두 한 번씩 집계되어 반환됩니다](#scoped_searching-the-superadmin-scoped-searches-idle-checker-assignments) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 스코프 검색하면, 권한 부족으로 거부됩니다](#scoped_searching-a-scoped-assignment-search-carrying-no-user-is-refused) | 거부 |

**update**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 할당을 끄면, 요청한 할당이 꺼진 상태로 반환됩니다](#updating-the-superadmin-disables-an-idle-checker-assignment) | 성공 |
| [할당 둘이 있고 사용자 컨텍스트 없이 하나를 끄려 하면, 대상을 찾을 수 없다는 이유로 거부됩니다](#updating-an-assignment-update-carrying-no-user-is-refused) | 거부 |

### admin_create

<a id="creating-the-superadmin-enables-an-idle-checker-on-a-domain"></a>

#### [the-superadmin-enables-an-idle-checker-on-a-domain](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_creating.py): pass

superadmin 이 검사기를 도메인에 켜면, 요청에서 지정한 검사기와 도메인을 잇는 할당이 활성 상태로 반환됩니다

Given

- 유휴 검사기 하나와 도메인 하나, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.admin_create: user-1이 검사기를 도메인 scope-1에 켭니다

Then

- 요청에서 지정한 검사기와 도메인을 잇는 할당이 활성 상태로 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - scope_id: 미리 저장한 도메인와 같다
  - idle_checker_id: 미리 저장한 검사기와 같다
  - enabled = True
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating-an-assignment-created-without-a-user-is-refused"></a>

#### [an-assignment-created-without-a-user-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_creating.py): pass

검사기와 도메인이 있고 사용자 컨텍스트 없이 검사기를 도메인에 켜려 하면, 권한 부족으로 거부됩니다

Given

- 유휴 검사기 하나와 도메인 하나, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.admin_create: user-1이 검사기를 도메인 scope-1에 켭니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### admin_search

<a id="searching-the-superadmin-searches-idle-checker-assignments"></a>

#### [the-superadmin-searches-idle-checker-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_searching.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 검색하면, 심은 할당이 모두 한 번씩 집계되어 반환됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.admin_search: user-1 이 검사기로 필터 기반 조회합니다

Then

- 미리 저장한 할당이 모두 한 번씩 집계되어 전체가 반환됩니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: id 순으로 읽은 미리 저장한 할당와 같다
  - items[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[0].scope_id: 미리 저장한 도메인와 같다
  - items[0].idle_checker_id: 미리 저장한 검사기와 같다
  - items[0].enabled = True
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: id 순으로 읽은 미리 저장한 할당와 같다
  - items[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[1].scope_id: 미리 저장한 도메인와 같다
  - items[1].idle_checker_id: 미리 저장한 검사기와 같다
  - items[1].enabled = True
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각

<a id="searching-an-assignment-search-carrying-no-user-is-refused"></a>

#### [an-assignment-search-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_searching.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 검색하면, 역할 부족으로 거부됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.admin_search: user-2 이 검사기로 필터 기반 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments"></a>

#### [a-user-granted-nothing-purges-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 삭제한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge: user-2이 할당 2개를 한 번에 purge 합니다

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id 와 같다
  - failed[0].message: 'Cannot resolve the given idle_checker key'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id 와 같다
  - failed[1].message: 'Cannot resolve the given idle_checker key'를 담은 이유

<a id="partial_bulk_purging-an-assignment-purge-carrying-no-user-fails-every-item"></a>

#### [an-assignment-purge-carrying-no-user-fails-every-item](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 한 번에 purge 하면, 답이 와서 모두 호출자를 알 수 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge: 사용자 컨텍스트 없이 할당 2개를 한 번에 purge 합니다

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id 와 같다
  - failed[0].message: 'User not found in context'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id 와 같다
  - failed[1].message: 'User not found in context'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

superadmin 이 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제하기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge: user-1이 할당 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 요청한 할당이 모두 활성 상태로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - successes[0].id: 요청에 넣은 1번째 id 와 같다
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: 1번째로 미리 저장한 도메인와 같다
  - successes[0].idle_checker_id: 미리 저장한 검사기와 같다
  - successes[0].enabled = True
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 요청에 넣은 2번째 id 와 같다
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: 2번째로 미리 저장한 도메인와 같다
  - successes[1].idle_checker_id: 미리 저장한 검사기와 같다
  - successes[1].enabled = True
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'No such idle checker assignment'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments"></a>

#### [a-user-granted-nothing-disables-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py): pass

아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 비활성화하려 하면, 비활성화한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_update: user-2이 할당 2개를 한 번에 비활성화합니다

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id 와 같다
  - failed[0].message: 'Cannot resolve the given idle_checker key'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id 와 같다
  - failed[1].message: 'Cannot resolve the given idle_checker key'를 담은 이유

<a id="partial_bulk_editing-an-assignment-update-carrying-no-user-fails-every-item"></a>

#### [an-assignment-update-carrying-no-user-fails-every-item](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 한 번에 끄려 하면, 답이 와서 모두 호출자를 알 수 없다는 이유로 실패 목록에 옵니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_update: 사용자 컨텍스트 없이 할당 2개를 한 번에 비활성화합니다

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id 와 같다
  - failed[0].message: 'User not found in context'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id 와 같다
  - failed[1].message: 'User not found in context'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-disables-several-assignments-at-once"></a>

#### [the-superadmin-disables-several-assignments-at-once](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py): pass

superadmin 이 할당 여럿을 한 번에 비활성화하면, 모두 비활성 할당으로 오고 실패한 것은 없습니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.partial_bulk_update: user-1이 할당 2개를 한 번에 비활성화합니다

Then

- 요청한 할당이 모두 비활성 상태로 오고, 실패한 것은 없습니다
  - successes count = 2
  - successes[0].id: 요청에 넣은 1번째 id 와 같다
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: 1번째로 미리 저장한 도메인와 같다
  - successes[0].idle_checker_id: 미리 저장한 검사기와 같다
  - successes[0].enabled = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 요청에 넣은 2번째 id 와 같다
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: 2번째로 미리 저장한 도메인와 같다
  - successes[1].idle_checker_id: 미리 저장한 검사기와 같다
  - successes[1].enabled = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

### purge

<a id="retiring-the-superadmin-purges-an-idle-checker-assignment"></a>

#### [the-superadmin-purges-an-idle-checker-assignment](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_retiring.py): pass

superadmin 이 할당 하나를 purge 하면, 요청에 넣은 할당의 id 로 반환됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.purge: user-1이 도메인 scope-1의 할당을 purge 합니다

Then

- 요청에 넣은 할당의 id 로 반환됩니다
  - id: 요청에 넣은 할당와 같다

<a id="retiring-an-assignment-purge-carrying-no-user-is-refused"></a>

#### [an-assignment-purge-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_retiring.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 하나를 purge 하려 하면, 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.purge: user-2이 도메인 scope-1의 할당을 purge 합니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

### scoped_search

<a id="scoped_searching-the-superadmin-scoped-searches-idle-checker-assignments"></a>

#### [the-superadmin-scoped-searches-idle-checker-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_scoped_searching.py): pass

superadmin 이 도메인 둘을 스코프로 검색하면, 그 도메인들의 할당이 모두 한 번씩 집계되어 반환됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.scoped_search: user-1 이 도메인 scope-1과 scope-2을 스코프로 조회합니다

Then

- 미리 저장한 할당이 모두 한 번씩 집계되어 전체가 반환됩니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: id 순으로 읽은 미리 저장한 할당와 같다
  - items[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[0].scope_id: 미리 저장한 도메인와 같다
  - items[0].idle_checker_id: 미리 저장한 검사기와 같다
  - items[0].enabled = True
  - items[0].created_at: 이 실행이 쓴 시각
  - items[0].updated_at: 이 실행이 쓴 시각
  - items[1].id: id 순으로 읽은 미리 저장한 할당와 같다
  - items[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[1].scope_id: 미리 저장한 도메인와 같다
  - items[1].idle_checker_id: 미리 저장한 검사기와 같다
  - items[1].enabled = True
  - items[1].created_at: 이 실행이 쓴 시각
  - items[1].updated_at: 이 실행이 쓴 시각

<a id="scoped_searching-a-scoped-assignment-search-carrying-no-user-is-refused"></a>

#### [a-scoped-assignment-search-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_scoped_searching.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 스코프 검색하면, 권한 부족으로 거부됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.scoped_search: user-2 이 도메인 scope-1과 scope-2을 스코프로 조회합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### update

<a id="updating-the-superadmin-disables-an-idle-checker-assignment"></a>

#### [the-superadmin-disables-an-idle-checker-assignment](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_updating.py): pass

superadmin 이 할당을 끄면, 요청한 할당이 꺼진 상태로 반환됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAssignmentAdapter.update: user-1이 도메인 scope-1의 할당을 끕니다

Then

- 요청한 할당 전체가 꺼진 상태로 반환됩니다
  - scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - scope_id: 미리 저장한 도메인와 같다
  - idle_checker_id: 미리 저장한 검사기와 같다
  - enabled = False
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="updating-an-assignment-update-carrying-no-user-is-refused"></a>

#### [an-assignment-update-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_updating.py): pass

할당 둘이 있고 사용자 컨텍스트 없이 하나를 끄려 하면, 대상을 찾을 수 없다는 이유로 거부됩니다

Given

- 도메인 2개에 활성화해 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 scope-2 가 활성화한 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다
    - 사용자 자원 정책 user-policy-2: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키페어와 개인 프로젝트를 갖습니다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.update: user-2이 도메인 scope-1의 할당을 끕니다

Then

- 거부됩니다
  - 거부: GenericBadRequest

