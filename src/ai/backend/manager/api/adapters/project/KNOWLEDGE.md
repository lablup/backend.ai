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

## 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 활성 플래그를 내린다 | 활성 프로젝트가 있음 | 활성 플래그를 내리는 수정 | soft delete 와 같이 비활성 상태를 실은 답 |
| 슈퍼관리자가 soft delete 된 프로젝트의 활성 플래그를 올린다 | 그 프로젝트가 있음 | soft delete 뒤 활성 플래그를 올리는 수정 | restore 와 같이 활성 상태를 실은 답 |

수정의 활성 플래그는 deprecated 다. 내리면 soft delete, 올리면 restore 를 부르고, 이미 그 상태면
부르지 않는다. 나머지 필드는 수정으로 반영한다. 상태는 노드에 실리지 않아 시나리오는 활성 플래그로
본다.

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 설명을 한 번에 바꾼다 | 프로젝트 둘이 있음 | 둘의 설명 수정 | 둘 다 새 설명으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 프로젝트 둘 | 둘의 설명 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| 슈퍼관리자가 활성 플래그와 설명을 섞어 여럿을 한 번에 고친다 | 프로젝트 둘이 있음 | 둘째를 soft delete 한 뒤, 첫째는 플래그 내리기와 설명, 둘째는 플래그 올리기와 설명, 없는 id 하나는 플래그 내리기 | 둘 다 새 설명으로 오고 첫째는 비활성, 둘째는 활성, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |

여럿 수정은 프로젝트마다 단건 수정과 같은 쓰기를 한다. 프로젝트 행을 고친 뒤 그 프로젝트가 따르는
리소스 정책 공유를 다시 적는다.

활성 플래그는 항목마다 단건 수정과 같은 기준으로 soft delete 와 restore 를 부른다. 실패는 항목마다
실패 목록에 싣는다.

## 여럿 soft delete, restore

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 soft delete 한다 | 활성 프로젝트 둘이 있음 | 셋 soft delete | 둘은 비활성으로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 soft delete 한다 | 같은 프로젝트 둘 | 둘 soft delete | soft delete 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| soft delete 된 여럿을 한 번에 restore 한다 | 프로젝트 둘이 있음 | 둘 soft delete 뒤 둘 restore | 둘 다 활성으로 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프로젝트는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. 여럿 purge 는 없다.

## 아직 적지 않은 것

`admin_purge`, `admin_search`, `batch_load_by_ids`, `batch_load_fields`, `delete`, `get`,
`restore`, `scoped_search`, `search_by_domain_name`, `search_by_user`, `unassign_users`.

## image commit을 위한 Container Registry 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 설정된 Container Registry를 읽는다 | 프로젝트 읽기 권한과 image commit을 위한 Container Registry 설정이 있음 | 여러 프로젝트의 image commit을 위한 Container Registry 조회 | 요청 순서대로 Container Registry를 반환 |
| Container Registry가 설정되지 않은 프로젝트를 읽는다 | 프로젝트 읽기 권한은 있으나 image commit을 위한 Container Registry 설정이 없음 | image commit을 위한 Container Registry 조회 | 빈 값 반환 |
| 권한 없는 프로젝트의 조회를 거부한다 | 프로젝트 읽기 권한이 없음 | image commit을 위한 Container Registry 조회 | 해당 프로젝트만 권한 부족으로 거부 |

일반 프로젝트 조회에는 image commit을 위한 Container Registry 조회가 포함되지 않는다. GraphQL에서 해당 필드를 요청하면 별도로 일괄 조회한다.
