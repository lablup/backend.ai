## idle_checker

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/idle_checker/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/idle_checker/adapter.py)

시나리오: 미완 6 / 6

- ops 로 구성 (4)
  - admin_partial_bulk_purge — 대표 성공 ✓ · 대표 실패 ✗ — SCENARIO-GAP
  - admin_purge — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - admin_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - batch_load_by_ids — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- 직접 구현 (2)
  - admin_create — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
  - admin_update — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP

**admin_partial_bulk_purge**

| 시나리오 | 판정 |
|---|---|
| [아무 권한도 받지 않은 사용자가 검사기 여럿을 한 번에 purge 하려 하면, 지운 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers) | 성공 |
| [슈퍼관리자가 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지운 검사기로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다](#partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one) | 성공 |

### admin_partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers"></a>

#### [a-user-granted-nothing-purges-none-of-several-checkers](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py) — pass

아무 권한도 받지 않은 사용자가 검사기 여럿을 한 번에 purge 하려 하면, 지운 것 없이 모두 권한이 없다는 이유로 실패 목록에 온다

Given

- 유휴 검사기 2개와, 일반 사용자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- IdleCheckerAdapter.admin_partial_bulk_purge — user-1이 검사기 2개를 한 번에 purge 함

Then

- 지운 검사기 없이 대상이 모두 실패 목록에 온다
  - successes = []
  - failed count = 2
  - failed[0].id: 1번째로 심은 검사기와 같다
  - failed[0].message: 'Insufficient permission'를 담은 이유
  - failed[1].id: 2번째로 심은 검사기와 같다
  - failed[1].message: 'Insufficient permission'를 담은 이유

<a id="partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py) — pass

슈퍼관리자가 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지운 검사기로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다

Given

- 유휴 검사기 2개와, 슈퍼관리자 한 명
  - 유휴 검사기 idle-checker-1: 대화형 세션을 3600초 뒤에 끝낸다
  - 유휴 검사기 idle-checker-2: 대화형 세션을 3600초 뒤에 끝낸다
  - 도메인 home-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- IdleCheckerAdapter.admin_partial_bulk_purge — user-1이 검사기 2개 와 없는 id 하나를 한 번에 purge 함

Then

- 심은 검사기가 모두 지운 모습으로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 온다
  - successes count = 2
  - failed count = 1
  - successes[0]: 1번째로 심은 검사기 전체와 같다
  - successes[1]: 2번째로 심은 검사기 전체와 같다
  - failed[0].id: 요청에 넣은 없는 id와 같다
  - failed[0].message: 'not found'를 담은 이유

