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
| 아무 권한도 받지 않은 사용자가 훑는다 | 권한 없음 | 전체 조회 | 역할 부족으로 거부 |
| 슈퍼관리자가 세션에 지정한 배치 정보를 읽는다 | 세션 그룹, 지정 에이전트 목록, 요청한 시작 시각이 있는 세션 | 전체 조회 | 세 값이 저장된 그대로 반환되고 기존 세션 정보도 유지됨 |
| 슈퍼관리자가 배치 정보를 지정하지 않은 세션을 읽는다 | 세션 그룹, 지정 에이전트, 요청한 시작 시각이 없는 세션 | 전체 조회 | 세 값이 미설정으로 반환되고 기존 세션 정보도 유지됨 |

필터 없는 전체 조회는 슈퍼관리자 역할로 막힌다. 스코프 권한으로 막히는 조회는 스코프를
받는 검색이다.

## 아직 적지 않은 것

지정 에이전트의 빈 목록은 기존 저장값 그대로 반환해야 한다. 현재 세션 생성 spec은 빈
목록을 미설정으로 저장하므로, 빈 목록을 저장한 기존 행의 조회는 시나리오로 심을 수 없다.

조회 시나리오는 세션 생성 spec으로 저장한 세션을 읽는다. `enqueue`를 거치는 생성 요청과
스케줄러의 리소스 검증은 아직 시나리오로 옮기지 않았다.

`admin_search_kernels`, `batch_load_by_ids`,
`batch_load_kernels_by_ids`, `batch_resource_allocation_by_kernel`,
`batch_resource_allocation_by_session`, `compute_schedule`, `enqueue`,
`exclude_idle_checks`, `get`, `get_logs`, `gql_search_by_project`,
`include_idle_checks`, `project_search`, `scoped_search`, `search_kernels_by_agent`,
`search_kernels_by_session`, `search_sessions_by_agent`, `shutdown_service`,
`start_service`, `terminate`, `update`.
