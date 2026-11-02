---
name: project-adapter-scenarios
type: reference
description: what the project adapter guarantees; domain-scope authorization on create, the active flag mapped to soft delete and restore, partial bulk results, and image commit registries
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

## 명부

## 수정하기

수정의 활성 플래그는 deprecated 다. 내리면 soft delete, 올리면 restore 를 부르고, 이미 그 상태면
부르지 않는다. 나머지 필드는 수정으로 반영한다. 상태는 노드에 실리지 않아 시나리오는 활성 플래그로
본다.

## 여럿 수정하기

여럿 수정은 프로젝트마다 단건 수정과 같은 쓰기를 한다. 프로젝트 행을 고친 뒤 그 프로젝트가 따르는
리소스 정책 공유를 다시 적는다.

활성 플래그는 항목마다 단건 수정과 같은 기준으로 soft delete 와 restore 를 부른다. 실패는 항목마다
실패 목록에 싣는다.

## 여럿 soft delete, restore

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프로젝트는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. 여럿 purge 는 없다.

## image commit을 위한 Container Registry 조회

일반 프로젝트 조회에는 image commit을 위한 Container Registry 조회가 포함되지 않는다. GraphQL에서 해당 필드를 요청하면 별도로 일괄 조회한다.
