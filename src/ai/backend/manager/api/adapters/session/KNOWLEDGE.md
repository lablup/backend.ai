---
name: session-adapter-scenarios
type: reference
description: what the session adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/session match these; the terminate and the allocation load that answer per session
scope: src/ai/backend/manager/api/adapters/session
keywords: [session, scenario, adapter, rbac, enqueue, terminate, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5
  at: 2026-09-18
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
| 아무 권한도 받지 않은 사용자가 훑는다 | 권한 없음 | 전체 조회 | 역할 부족으로 거부 |

필터 없는 전체 조회는 슈퍼관리자 역할로 막힌다. 스코프 권한으로 막히는 조회는 스코프를
받는 검색이다.

## 종료

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 종료 권한을 받은 사용자가 기다리던 세션을 종료한다 | 기다리는 세션 하나, 그 프로젝트에 세션 삭제 권한 | 그 세션 종료 | 취소된 목록에 그 세션, 실패 목록은 비어 있음 |
| 아무 권한도 없는 사용자가 종료한다 | 기다리는 세션 하나, 권한 없음 | 그 세션 종료 | 실패 목록에 그 세션, 네 결과 목록은 비어 있음 |
| 두 프로젝트의 세션을 한 번에 종료한다 | 서로 다른 프로젝트의 세션 둘, 첫 프로젝트에만 세션 삭제 권한 | 두 세션을 한 번에 | 취소된 목록에 자기 프로젝트의 세션, 실패 목록에 다른 프로젝트의 세션 |
| 없는 id를 섞어 종료한다 | 기다리는 세션 하나, 슈퍼관리자 | 그 세션과 없는 id를 한 번에 | 취소된 목록에 그 세션, 건너뛴 목록에 없는 id |

종료는 세션마다 따로 답한다. 권한 검사도 세션마다이고, 거부된 세션은 실패 목록에 들어가며
호출 자체는 거부되지 않는다. 기다리던 세션은 취소된 목록에, 없는 id와 이미 끝난 세션은
건너뛴 목록에 들어간다. 실행 중인 세션을 종료하는 행은 없다. 세션이 실행 중이 되려면
에이전트가 있어야 하고, 에이전트는 심을 수 없다.

## 할당 읽기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 두 프로젝트의 세션 할당을 한 번에 읽는다 | 서로 다른 프로젝트의 세션 둘, 첫 프로젝트 범위에만 세션 읽기 권한 | 두 세션의 할당을 한 번에 | 자기 프로젝트의 세션은 빈 할당, 다른 프로젝트의 세션은 권한 부족으로 거부 |

세션마다 따로 답하고, 거부는 그 세션을 기다리는 필드에서만 난다. 할당 행이 없는 세션은
빈 할당으로 답한다.

## 아직 적지 않은 것

`enqueue`가 가장 크다. 스케줄러가 "리소스 슬롯을 제공하는 에이전트가 그 리소스 그룹에
없다"로 막는데, 에이전트 행은 write spec이 없다. 하트비트로 등록되기 때문이다. 시나리오로
세우려면 그 경로를 먼저 열어야 한다.

`admin_search_kernels`, `batch_load_by_ids`, `batch_load_fields`,
`batch_load_kernels_by_ids`, `batch_resource_allocation_by_kernel`, `compute_schedule`,
`enqueue`, `exclude_idle_checks`, `get`, `get_logs`, `gql_search_by_project`,
`include_idle_checks`, `my_search`, `project_search`, `search_kernels_by_agent`,
`search_kernels_by_session`, `search_sessions_by_agent`, `shutdown_service`,
`start_service`, `update`.
