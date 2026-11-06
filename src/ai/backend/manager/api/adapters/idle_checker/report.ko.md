## idle_checker

[배경](/src/ai/backend/manager/api/adapters/idle_checker/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/idle_checker/adapter.py)

시나리오: 미완성 2 / 6

- ops 구성 (4)
  - admin_partial_bulk_purge: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
  - admin_purge: 대표 성공 ✓ · 대표 거부 ✓
  - admin_search: 대표 성공 ✓ · 대표 거부 ✓
  - batch_load_by_ids: 대표 성공 ✓ · 대표 거부 ✗: SCENARIO-GAP
- 직접 구현 (2)
  - admin_create: 성공 있음 1 · 거부 있음 1 (global_scope)
  - admin_update: 성공 있음 1 · 거부 있음 1 (global_scope)

**admin_partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 유휴 검사기 여럿을 한 번에 purge 하려 하면, 삭제한 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers) | 성공 |
| [superadmin 이 유휴 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제한 유휴 검사기로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one) | 성공 |

**admin_purge**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 검사기 하나를 purge 하면, 요청에 넣은 검사기의 id 로 반환됩니다](#retiring-the-superadmin-purges-an-idle-checker) | 성공 |
| [아무 권한도 받지 않은 사용자가 검사기 하나를 purge 하려 하면 권한이 없다는 이유로 거부됩니다](#retiring-a-user-granted-nothing-may-not-purge-an-idle-checker) | 거부 |

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [심은 검사기가 쓰지 않는 종류를 필터로 조회하면 아무 검사기도 반환되지 않습니다](#searching-a-checker-type-no-checker-uses-leaves-nothing) | 성공 |
| [검사기가 지어진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다](#searching-a-created-at-filter-after-the-written-time-leaves-nothing) | 성공 |
| [검사기 여럿 중 하나의 이름을 필터로 조회하면 그 이름의 검사기 하나만 반환됩니다](#searching-a-name-filter-narrows-the-answer-to-that-checker) | 성공 |
| [검사기 하나의 id 를 필터로 조회하면 그 검사기 하나만 반환됩니다](#searching-an-entity-id-filter-narrows-the-answer-to-that-checker) | 성공 |
| [이름의 역순으로 정렬해 조회하면 검사기가 이름의 역순으로 반환됩니다](#searching-an-order-by-name-brings-the-checkers-back-in-name-order) | 성공 |
| [검사기가 고쳐진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다](#searching-an-updated-at-filter-after-the-written-time-leaves-nothing) | 성공 |
| [global 역할로 검사하는 연산이므로 superadmin 이 필터 없이 검색하면, 심은 검사기가 모두 한 번씩 집계되어 반환됩니다](#searching-the-superadmin-searches-idle-checkers-without-a-filter) | 성공 |
| [global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검색하면 역할 부족으로 거부됩니다](#searching-a-user-who-is-not-the-superadmin-may-not-search-idle-checkers) | 거부 |

**batch_load_by_ids**

| 시나리오 | 판정 |
|---|---|
| [superadmin 이 미리 저장한 검사기 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | 성공 |

**admin_create**

| 시나리오 | 판정 |
|---|---|
| [global 역할로 검사하는 연산이므로 superadmin 이 세션 수명 검사기를 만들면, 요청에서 지정한 값 그대로 반환됩니다](#creating-the-superadmin-makes-an-idle-checker) | 성공 |
| [global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 만들면 역할 부족으로 거부됩니다](#creating-a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker) | 거부 |

**admin_update**

| 시나리오 | 판정 |
|---|---|
| [global 역할로 검사하는 연산이므로 superadmin 이 검사기의 규격을 바꾸면, 바뀐 규격 그대로 반환됩니다](#editing-the-superadmin-edits-an-idle-checker) | 성공 |
| [global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 바꾸면 역할 부족으로 거부됩니다](#editing-a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker) | 거부 |

### admin_partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers"></a>

#### [a-user-granted-nothing-purges-none-of-several-checkers](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py): pass

아무 권한도 받지 않은 사용자가 유휴 검사기 여럿을 한 번에 purge 하려 하면, 삭제한 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다

Given

- 유휴 검사기 2개와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_partial_bulk_purge: user-1이 유휴 검사기 2개를 한 번에 purge 합니다

Then

- 삭제한 검사기 없이 대상이 모두 실패 목록에 옵니다
  - successes = []
  - failed count = 2
  - failed[0].id: 1번째로 미리 저장한 검사기와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 2번째로 미리 저장한 검사기와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py): pass

superadmin 이 유휴 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제한 유휴 검사기로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_partial_bulk_purge: user-1이 유휴 검사기 2개 와 없는 id 하나를 한 번에 purge 합니다

Then

- 미리 저장한 검사기가 모두 삭제된 모습으로 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다
  - successes count = 2
  - failed count = 1
  - successes[0]: 1번째로 미리 저장한 검사기 전체와 같다
  - successes[1]: 2번째로 미리 저장한 검사기 전체와 같다
  - failed[0].id: 요청에 넣은 없는 id 와 같다
  - failed[0].message: 'not found'를 담은 이유

### admin_purge

<a id="retiring-the-superadmin-purges-an-idle-checker"></a>

#### [the-superadmin-purges-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_retiring.py): pass

superadmin 이 검사기 하나를 purge 하면, 요청에 넣은 검사기의 id 로 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_purge: user-1이 검사기 idle-checker-1을 purge 합니다

Then

- 요청에 넣은 검사기의 id 로 반환됩니다
  - id: 요청에 넣은 검사기와 같다
  - entity_id: 요청에 넣은 검사기와 같다

<a id="retiring-a-user-granted-nothing-may-not-purge-an-idle-checker"></a>

#### [a-user-granted-nothing-may-not-purge-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_retiring.py): pass

아무 권한도 받지 않은 사용자가 검사기 하나를 purge 하려 하면 권한이 없다는 이유로 거부됩니다

Given

- 유휴 검사기 2개와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_purge: user-1이 검사기 idle-checker-1을 purge 합니다

Then

- 거부됩니다
  - 거부: NotEnoughPermission

### admin_search

<a id="searching-a-checker-type-no-checker-uses-leaves-nothing"></a>

#### [a-checker-type-no-checker-uses-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

심은 검사기가 쓰지 않는 종류를 필터로 조회하면 아무 검사기도 반환되지 않습니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 심은 검사기가 쓰지 않는 종류로 조회합니다

Then

- 아무 검사기도 집계되지 않습니다
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-created-at-filter-after-the-written-time-leaves-nothing"></a>

#### [a-created-at-filter-after-the-written-time-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

검사기가 지어진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 검사기가 지어진 시각보다 1초 뒤를 조회합니다

Then

- 아무 검사기도 집계되지 않습니다
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-name-filter-narrows-the-answer-to-that-checker"></a>

#### [a-name-filter-narrows-the-answer-to-that-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

검사기 여럿 중 하나의 이름을 필터로 조회하면 그 이름의 검사기 하나만 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 이름이 idle-checker-1인 검사기만 조회합니다

Then

- 미리 저장한 검사기 하나만 한 번씩 집계되어 전체가 반환됩니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0]: 미리 저장한 검사기 전체와 같다

<a id="searching-an-entity-id-filter-narrows-the-answer-to-that-checker"></a>

#### [an-entity-id-filter-narrows-the-answer-to-that-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

검사기 하나의 id 를 필터로 조회하면 그 검사기 하나만 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 미리 저장한 검사기 하나의 id 로 조회합니다

Then

- 미리 저장한 검사기 하나만 한 번씩 집계되어 전체가 반환됩니다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0]: 미리 저장한 검사기 전체와 같다

<a id="searching-an-order-by-name-brings-the-checkers-back-in-name-order"></a>

#### [an-order-by-name-brings-the-checkers-back-in-name-order](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

이름의 역순으로 정렬해 조회하면 검사기가 이름의 역순으로 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 이름의 역순으로 정렬해 조회합니다

Then

- 미리 저장한 검사기가 이름의 역순으로 모두 한 번씩 집계되어 반환됩니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0]: 이름이 1번째로 느린 미리 저장한 검사기 전체와 같다
  - items[1]: 이름이 2번째로 느린 미리 저장한 검사기 전체와 같다

<a id="searching-an-updated-at-filter-after-the-written-time-leaves-nothing"></a>

#### [an-updated-at-filter-after-the-written-time-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

검사기가 고쳐진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 검사기가 고쳐진 시각보다 1초 뒤를 조회합니다

Then

- 아무 검사기도 집계되지 않습니다
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-searches-idle-checkers-without-a-filter"></a>

#### [the-superadmin-searches-idle-checkers-without-a-filter](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 필터 없이 검색하면, 심은 검사기가 모두 한 번씩 집계되어 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 미리 저장한 검사기가 모두 한 번씩 집계되어 전체가 반환됩니다
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0]: 1번째로 미리 저장한 검사기 전체와 같다
  - items[1]: 2번째로 미리 저장한 검사기 전체와 같다

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-idle-checkers"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-idle-checkers](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검색하면 역할 부족으로 거부됩니다

Given

- 유휴 검사기 2개와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_search: user-1 이 필터 없이 전체를 조회합니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/idle_checker/test_reading.py): pass

superadmin 이 미리 저장한 검사기 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.batch_load_by_ids: user-1이 미리 저장한 검사기 2개와 없는 id 하나를 한 번에 조회합니다

Then

- 요청한 순서대로 반환되고, 없는 id 에 해당하는 항목은 비어 있습니다
  - len(items) = 3
  - items[0]: 1번째로 미리 저장한 검사기 전체와 같다
  - items[1]: 2번째로 미리 저장한 검사기 전체와 같다
  - items[2] = None

### admin_create

<a id="creating-the-superadmin-makes-an-idle-checker"></a>

#### [the-superadmin-makes-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_creating.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 세션 수명 검사기를 만들면, 요청에서 지정한 값 그대로 반환됩니다

Given

- 유휴 검사기 없이 호출자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_create: user-1이 세션 수명 7200초짜리 검사기를 만듭니다

Then

- 생성한 검사기 전체가 반환됩니다
  - id: 건너뜀: 데이터베이스가 생성합니다
  - entity_id: 건너뜀: 데이터베이스가 생성합니다
  - name = 'created-checker'
  - description = None
  - checker_type = 'session_lifetime'
  - target_session_types = [<SessionTypes.INTERACTIVE: 'interactive'>]
  - initial_grace_period_seconds = 0
  - spec.type = 'session_lifetime'
  - spec.session_lifetime.max_lifetime_seconds = 7200
  - created_at: 이 실행이 쓴 시각
  - updated_at: 이 실행이 쓴 시각

<a id="creating-a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_creating.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 만들면 역할 부족으로 거부됩니다

Given

- 유휴 검사기 없이 호출자 한 명
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_create: user-1이 세션 수명 7200초짜리 검사기를 만듭니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

### admin_update

<a id="editing-the-superadmin-edits-an-idle-checker"></a>

#### [the-superadmin-edits-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_editing.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 검사기의 규격을 바꾸면, 바뀐 규격 그대로 반환됩니다

Given

- 유휴 검사기 2개와, superadmin 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - superadmin user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_update: user-1이 검사기 idle-checker-1의 규격을 네트워크 비활성 5400초로 바꿉니다

Then

- 수정한 검사기 전체가 반환됩니다
  - id: 준비한 검사기와 같다
  - entity_id: 준비한 검사기와 같다
  - name = 'idle-checker-1'
  - description = None
  - checker_type = 'network_timeout'
  - target_session_types = [<SessionTypes.INTERACTIVE: 'interactive'>]
  - initial_grace_period_seconds = 0
  - spec.type = 'network_timeout'
  - spec.network.max_network_inactivity_seconds = 5400
  - created_at: 건너뜀: 수정 전에 기록된 시각
  - updated_at: 이 실행이 쓴 시각

<a id="editing-a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker"></a>

#### [a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_editing.py): pass

global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 바꾸면 역할 부족으로 거부됩니다

Given

- 유휴 검사기 2개와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 종료합니다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 종료합니다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 자원 정책 default: 사용자를 생성할 때 함께 생성되는 개인 프로젝트가 이 이름으로 조회합니다
    - 사용자 자원 정책 user-policy-1: 사용자 한 명당 vfolder 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키페어와 개인 프로젝트를 갖습니다

When

- IdleCheckerAdapter.admin_update: user-1이 검사기 idle-checker-1의 규격을 네트워크 비활성 5400초로 바꿉니다

Then

- 거부됩니다
  - 거부: InsufficientPrivilege

