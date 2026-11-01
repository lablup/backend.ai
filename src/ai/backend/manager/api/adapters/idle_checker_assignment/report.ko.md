## idle_checker_assignment

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/idle_checker_assignment/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/idle_checker_assignment/adapter.py)

시나리오: 미완 7 / 7

- 직접 구현 (7)
  - admin_create — 성공 없음 · 실패 없음 (relation) — SCENARIO-GAP
  - admin_search — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - partial_bulk_purge — 성공 있음 2 · 실패 없음 (relation) — SCENARIO-GAP
  - partial_bulk_update — 성공 있음 2 · 실패 없음 (relation) — SCENARIO-GAP
  - purge — 성공 없음 · 실패 없음 (relation) — SCENARIO-GAP
  - scoped_search — 성공 없음 · 실패 없음 (scope) — SCENARIO-GAP
  - update — 성공 없음 · 실패 없음 (relation) — SCENARIO-GAP

**partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 지운 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments) | 성공 |
| [슈퍼관리자가 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one) | 성공 |

**partial_bulk_update**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 끄려 하면, 끈 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 온다](#partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments) | 성공 |
| [슈퍼관리자가 할당 여럿을 한 번에 끄면, 모두 꺼진 할당으로 오고 실패한 것은 없다](#partial_bulk_editing-the-superadmin-disables-several-assignments-at-once) | 성공 |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments"></a>

#### [a-user-granted-nothing-purges-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 지운 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 온다

Given

- 도메인 2개에 켜 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 scope-2 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge — user-2이 할당 2개를 한 번에 purge 함

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id와 같다
  - failed[0].message: 'Cannot resolve the given idle_checker key'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id와 같다
  - failed[1].message: 'Cannot resolve the given idle_checker key'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py) — pass

슈퍼관리자가 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 할당으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 도메인 2개에 켜 둔 유휴 검사기 하나와, 슈퍼관리자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 scope-2 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge — user-1이 할당 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 요청한 할당이 모두 켜진 상태로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 온다
  - successes count = 2
  - successes[0].id: 요청에 넣은 1번째 id와 같다
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: 1번째로 심은 도메인와 같다
  - successes[0].idle_checker_id: 심은 검사기와 같다
  - successes[0].enabled = True
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 요청에 넣은 2번째 id와 같다
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: 2번째로 심은 도메인와 같다
  - successes[1].idle_checker_id: 심은 검사기와 같다
  - successes[1].enabled = True
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed count = 1
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'No such idle checker assignment'를 담은 이유

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments"></a>

#### [a-user-granted-nothing-disables-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py) — pass

아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 끄려 하면, 끈 것 없이 모두 찾을 수 없다는 이유로 실패 목록에 온다

Given

- 도메인 2개에 켜 둔 유휴 검사기 하나와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 scope-2 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
    - 일반 사용자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 도메인 home-2

When

- IdleCheckerAssignmentAdapter.partial_bulk_update — user-2이 할당 2개를 한 번에 끔

Then

- 처리된 할당 없이 요청한 할당이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 요청에 넣은 1번째 id와 같다
  - failed[0].message: 'Cannot resolve the given idle_checker key'를 담은 이유
  - failed[1].id: 요청에 넣은 2번째 id와 같다
  - failed[1].message: 'Cannot resolve the given idle_checker key'를 담은 이유

<a id="partial_bulk_editing-the-superadmin-disables-several-assignments-at-once"></a>

#### [the-superadmin-disables-several-assignments-at-once](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py) — pass

슈퍼관리자가 할당 여럿을 한 번에 끄면, 모두 꺼진 할당으로 오고 실패한 것은 없다

Given

- 도메인 2개에 켜 둔 유휴 검사기 하나와, 슈퍼관리자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 scope-1
  - 도메인 scope-2
  - 도메인 scope-1 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 scope-2 에 켜 둔 유휴 검사기 idle-checker-1
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- IdleCheckerAssignmentAdapter.partial_bulk_update — user-1이 할당 2개를 한 번에 끔

Then

- 요청한 할당이 모두 꺼진 상태로 오고, 실패한 것은 없다
  - successes count = 2
  - successes[0].id: 요청에 넣은 1번째 id와 같다
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: 1번째로 심은 도메인와 같다
  - successes[0].idle_checker_id: 심은 검사기와 같다
  - successes[0].enabled = False
  - successes[0].created_at: 이 실행이 쓴 시각
  - successes[0].updated_at: 이 실행이 쓴 시각
  - successes[1].id: 요청에 넣은 2번째 id와 같다
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: 2번째로 심은 도메인와 같다
  - successes[1].idle_checker_id: 심은 검사기와 같다
  - successes[1].enabled = False
  - successes[1].created_at: 이 실행이 쓴 시각
  - successes[1].updated_at: 이 실행이 쓴 시각
  - failed = []

