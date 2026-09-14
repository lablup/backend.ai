---
name: session-adapter-scenarios
type: reference
description: what the session adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/session match these
scope: src/ai/backend/manager/api/adapters/session
keywords: [session, scenario, adapter, rbac, enqueue]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 세션 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

세션은 자기가 속한 프로젝트를 이름으로 댄다. 그래서 세션 권한은 프로젝트 스코프에 앉고, 그
역할을 주는 일이 곧 그 사람을 프로젝트 명부에 올리는 일이 된다.

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 세션이 하나도 없을 때 슈퍼관리자가 훑는다 | 세션 없음 | 전체 조회 | 비어 있음 |
| 아무 권한도 받지 않은 사용자가 훑는다 | 권한 없음 | 전체 조회 | 권한 부족으로 거부 |

세션 조회가 역할이 아니라 스코프 권한으로 막힌다는 것이 이 짝의 요지다. 도메인이나 리소스
그룹과 다르다.

## 아직 적지 않은 것

`enqueue`가 가장 크다. 스케줄러가 "리소스 슬롯을 제공하는 에이전트가 그 리소스 그룹에
없다"로 막는데, 에이전트 행은 write spec이 없다. 하트비트로 등록되기 때문이다. 시나리오로
세우려면 그 경로를 먼저 열어야 한다.

`admin_search_kernels`, `batch_load_by_ids`, `batch_load_fields`,
`batch_load_kernels_by_ids`, `batch_resource_allocation_by_kernel`,
`batch_resource_allocation_by_session`, `compute_schedule`, `enqueue`,
`exclude_idle_checks`, `get`, `get_logs`, `gql_search_by_project`,
`include_idle_checks`, `my_search`, `project_search`, `search_kernels_by_agent`,
`search_kernels_by_session`, `search_sessions_by_agent`, `shutdown_service`,
`start_service`, `terminate`, `update`.
