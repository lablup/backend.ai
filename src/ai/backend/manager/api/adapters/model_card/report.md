## model_card

[무엇을 보장하는가](/src/ai/backend/manager/api/adapters/model_card/KNOWLEDGE.md) · [어댑터](/src/ai/backend/manager/api/adapters/model_card/adapter.py)

시나리오: 미완 12 / 13

- ops 로 구성 (7)
  - admin_search — 대표 성공 ✓ · 대표 실패 ✓
  - create — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - get — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - min_resources — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - ownership_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - project_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
  - scoped_search — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP
- ops + 직접 구현 (2)
  - deploy — 성공 없음 · 실패 없음 (scope, single_get_ops) — SCENARIO-GAP
  - update — 성공 없음 · 실패 없음 (atomic_bulk_scoped_search_ops, single_entity) — SCENARIO-GAP
- 직접 구현 (3)
  - admin_bulk_delete — 성공 없음 · 실패 없음 (partial_bulk) — SCENARIO-GAP
  - delete — 성공 없음 · 실패 없음 (single_entity) — SCENARIO-GAP
  - scan_project — 성공 없음 · 실패 없음 (global_scope) — SCENARIO-GAP
- Action 없음 (1)
  - available_presets — 성공 없음 · 실패 없음 — SCENARIO-GAP

### model_card

#### [a-scenario-that-laid-no-model-card-finds-none](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

모델 카드를 하나도 심지 않은 상태에서 슈퍼관리자가 전체 조회를 하면, 답은 비어 있다

Given

- 도메인 하나와, 그 도메인에 속한 superadmin 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 슈퍼관리자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 답이 비어 있다
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

#### [a-user-who-is-not-the-superadmin-may-not-search-every-model-card](/tests/scenario/bai_scenario/manager/model_card/test_model_card.py) — pass

슈퍼관리자가 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 막힌다

Given

- 도메인 하나와, 그 도메인에 속한 user 한 명
  - 도메인 host-1
  - 도메인에 속한 사용자 한 명 준비
    - 프로젝트 정책 default: 사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다
    - 사용자 정책 user-policy-1: 사용자 한 명당 폴더 10개까지
    - 키페어 정책 keypair-policy-1: 동시 세션 5개까지
    - 일반 사용자 user-1: 자기 키와 개인 프로젝트를 갖는다

When

- ModelCardAdapter.admin_search — user-1이 필터 없이 전체 조회

Then

- 거부된다
  - 거부: InsufficientPrivilege

