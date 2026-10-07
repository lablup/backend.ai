## session

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session/adapter.py)

시나리오: 미완 21 / 22

- ops + 직접 구현 (10)
  - admin_search — 성공 있음 3 · 실패 있음 1 (global_searcher_ops, partial_bulk)
  - admin_search_kernels — 성공 없음 · 실패 없음 (atomic_bulk_field, global_searcher_ops) — SCENARIO-GAP
  - batch_load_by_ids — 성공 없음 · 실패 없음 (partial_bulk, partial_bulk_get_ops) — SCENARIO-GAP
  - batch_load_kernels_by_ids — 성공 없음 · 실패 없음 (atomic_bulk_field, partial_bulk_get_ops) — SCENARIO-GAP
  - gql_search_by_project — 성공 없음 · 실패 없음 (partial_bulk, scoped_search_ops) — SCENARIO-GAP
  - project_search — 성공 없음 · 실패 없음 (partial_bulk, scoped_search_ops) — SCENARIO-GAP
  - scoped_search — 성공 없음 · 실패 없음 (partial_bulk, scoped_search_ops) — SCENARIO-GAP
  - search_kernels_by_agent — 성공 없음 · 실패 없음 (atomic_bulk_field, global_searcher_ops) — SCENARIO-GAP
  - search_kernels_by_session — 성공 없음 · 실패 없음 (atomic_bulk_field, atomic_bulk_scoped_search_ops) — SCENARIO-GAP
  - search_sessions_by_agent — 성공 없음 · 실패 없음 (global_searcher_ops, partial_bulk) — SCENARIO-GAP
- 직접 구현 (12)
  - batch_resource_allocation_by_kernel — 성공 없음 · 실패 없음 (atomic_bulk_field) — SCENARIO-GAP
  - batch_resource_allocation_by_session — 성공 없음 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - compute_schedule — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - enqueue — 성공 없음 · 실패 없음 (partial_bulk, scope) — SCENARIO-GAP
  - exclude_idle_checks — 성공 없음 · 실패 없음 (legacy_partial_bulk) — SCENARIO-GAP
  - get — 성공 없음 · 실패 없음 (partial_bulk, single_entity) — SCENARIO-GAP
  - get_logs — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - include_idle_checks — 성공 없음 · 실패 없음 (legacy_partial_bulk) — SCENARIO-GAP
  - shutdown_service — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - start_service — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - terminate — 성공 없음 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - update — 성공 없음 · 실패 없음 (partial_bulk, single_entity) — SCENARIO-GAP

**admin_search**

| 시나리오 | 판정 |
|---|---|
| [세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다](#session-a-scenario-that-laid-no-session-finds-none) | 성공 |
| [슈퍼관리자가 지정된 세션 스케줄링 조건을 읽으면 기존 세션 정보와 함께 유지된다](#searching_details-session-placement-is-preserved-when-configured) | 성공 |
| [슈퍼관리자가 미설정인 세션 스케줄링 조건을 읽으면 기존 세션 정보와 함께 유지된다](#searching_details-session-placement-is-preserved-when-unset) | 성공 |
| [필터 없는 전체 조회는 슈퍼관리자 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부된다](#session-a-user-granted-nothing-may-not-search-sessions) | 거부 |

### admin_search

<a id="session-a-scenario-that-laid-no-session-finds-none"></a>

#### [a-scenario-that-laid-no-session-finds-none](/tests/scenario/bai_scenario/manager/session/test_session.py) — pass

세션을 하나도 심지 않은 상태에서 슈퍼관리자가 조회하면, 답은 비어 있다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SessionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-placement-is-preserved-when-configured"></a>

#### [session-placement-is-preserved-when-configured](/tests/scenario/bai_scenario/manager/session/test_searching_details.py) — pass

슈퍼관리자가 지정된 세션 스케줄링 조건을 읽으면 기존 세션 정보와 함께 유지된다

Given

- 세션 그룹, designated_agent_ids, requested_starts_at의 세 값이 지정된 세션과 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 그룹 session-group-1: 가능하면 세션들을 서로 다른 에이전트에 배치한다
  - 에이전트 agent-1: 살아 있고, 아직 보고한 슬롯이 없다
  - 에이전트 agent-2: 살아 있고, 아직 보고한 슬롯이 없다
  - 세션 session-1: 세션 그룹, 에이전트 둘, 요청한 시작 시각을 지정한 대기 세션

When

- SessionAdapter.admin_search — user-2이 필터 없이 전체 조회

Then

- 스케줄링 조건을 포함한 세션 정보 전체가 저장된 그대로 반환된다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-placement-is-preserved-when-unset"></a>

#### [session-placement-is-preserved-when-unset](/tests/scenario/bai_scenario/manager/session/test_searching_details.py) — pass

슈퍼관리자가 미설정인 세션 스케줄링 조건을 읽으면 기존 세션 정보와 함께 유지된다

Given

- 세션 그룹, designated_agent_ids, requested_starts_at의 세 값이 미설정인 세션과 슈퍼관리자
  - 도메인 home-1
  - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
  - 프로젝트 team-1
  - 리소스 그룹 resource-group-1: fifo 스케줄러를 쓴다
  - 도메인에 속한 사용자 한 명 준비
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다
    - 사용자 정책 user-policy-2: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-3: 동시 세션 5개까지
    - 슈퍼관리자 user-2: 자기 키와 개인 프로젝트를 갖는다
  - 키페어 정책 keypair-policy-2: 동시 세션 5개까지
  - 일반 사용자 user-1: 기본이 아닌 활성 키 하나를 더 갖는다
  - 컨테이너 레지스트리 registry-1: 이미지를 가져오는 곳
  - 이미지 image-1: x86_64 이미지
  - 세션 session-1: 스케줄링을 기다리고 있다

When

- SessionAdapter.admin_search — user-2이 필터 없이 전체 조회

Then

- 스케줄링 조건을 포함한 세션 정보 전체가 저장된 그대로 반환된다
  - items: 저장된 세션의 전체 정보와 같다
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="session-a-user-granted-nothing-may-not-search-sessions"></a>

#### [a-user-granted-nothing-may-not-search-sessions](/tests/scenario/bai_scenario/manager/session/test_session.py) — pass

필터 없는 전체 조회는 슈퍼관리자 역할로만 열리므로, 아무 권한도 받지 않은 사용자는 역할 부족으로 거부된다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- SessionAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

