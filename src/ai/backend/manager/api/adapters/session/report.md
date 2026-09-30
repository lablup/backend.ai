## session

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/session/adapter.py)

시나리오: 미완 21 / 22

- ops + 직접 구현 (10)
  - admin_search — 성공 있음 1 · 실패 있음 1 (global_searcher_ops, partial_bulk)
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

