---
name: rbac-adapter-scenarios
type: reference
description: what the rbac adapter guarantees for role writes: permission checks by the scope's permission graph, deprecated status handling, and partial bulk results
scope: src/ai/backend/manager/api/adapters/rbac
keywords: [rbac, role, scenario, adapter, restore, partial_bulk, status]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# rbac 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

지금은 역할 쓰기만 적는다. 역할은 한 스코프에 속하고, 역할을 고치는 문은 그 스코프의 권한
그래프가 지킨다. 대상 역할은 부르는 사람이 속하지 않은 도메인에 둔다. 슈퍼관리자가 아닌 사람이
부르는 행은 아무 권한도 받지 않은 사용자다.

## 수정

deprecated `status` 는 수정 뒤에 처리한다. DELETED 는 soft delete 로, 삭제된 역할에 ACTIVE 는
restore 로 보낸다. 이미 그 상태면 아무것도 하지 않고, INACTIVE 는 반영하지 않는다.

## soft delete, restore, purge

## 여럿 수정하기

deprecated `status` 는 역할마다 단건과 같은 기준으로 처리한다. soft delete · restore 에서 실패한
역할은 그 이유로 실패 목록에 온다.

## 여럿 soft delete, restore, purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 역할은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.
