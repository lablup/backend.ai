## idle_checker_assignment

[배경](/src/ai/backend/manager/api/adapters/idle_checker_assignment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/idle_checker_assignment/adapter.py)

시나리오: 미완성 7 / 7

- 직접 구현 (7)
  - admin_create: 성공 없음 · 거부 없음 (relation): SCENARIO-GAP
  - admin_search: 성공 없음 · 거부 없음 (global_scope): SCENARIO-GAP
  - partial_bulk_purge: 성공 있음 2 · 거부 없음 (relation): SCENARIO-GAP
  - partial_bulk_update: 성공 있음 2 · 거부 없음 (relation): SCENARIO-GAP
  - purge: 성공 없음 · 거부 없음 (relation): SCENARIO-GAP
  - scoped_search: 성공 없음 · 거부 없음 (scope): SCENARIO-GAP
  - update: 성공 없음 · 거부 없음 (relation): SCENARIO-GAP

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 삭제한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments) | 성공 |
| [superadmin 이 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다](#partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 비활성화하려 하면, 비활성화한 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 옵니다](#partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments) | 성공 |
| [superadmin 이 할당 여럿을 한 번에 비활성화하면, 모두 비활성 할당으로 오고 실패한 것은 없습니다](#partial_bulk_editing-the-superadmin-disables-several-assignments-at-once) | 성공 |

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

<a id="partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

superadmin 이 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다

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

