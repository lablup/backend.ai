---
name: project-adapter-scenarios
type: reference
description: what the project adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/project match these
scope: src/ai/backend/manager/api/adapters/project
keywords: [project, scenario, adapter, rbac, roster]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 프로젝트 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

프로젝트는 도메인 아래에 생긴다. 생성을 지키는 것은 전역 역할이 아니라 그 도메인 스코프의
권한이다. 도메인 생성과 여기가 다르므로 짝을 따로 적는다.

## 만들기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 도메인 아래에 만든다 | 도메인과 프로젝트 정책이 있음 | 만들기 | 그 이름의 프로젝트가 그 도메인 아래에 |
| 아무 권한도 받지 않은 사용자가 만든다 | 권한 없음 | 만들기 | 권한 부족으로 거부 |

## 명부

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 사용자를 배정한다 | 프로젝트와 그 스코프의 역할이 있음 | 사용자 배정 | 그 사용자가 명부에 오름 |

## 아직 적지 않은 것

`admin_delete`, `admin_purge`, `admin_restore`, `admin_search`, `admin_update`,
`batch_load_by_ids`, `batch_load_fields`, `get`, `scoped_search`,
`search_by_domain_name`, `search_by_user`, `unassign_users`.
