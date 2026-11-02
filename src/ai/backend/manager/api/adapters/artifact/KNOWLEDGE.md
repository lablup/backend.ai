---
name: artifact-adapter-scenarios
type: reference
description: what the artifact adapter guarantees for update, soft delete and restore, and for the bulk and legacy id-list calls; artifacts in no scope, the permission graph on single calls, the global role on the id-list calls, no purge
scope: src/ai/backend/manager/api/adapters/artifact
keywords: [artifact, scenario, adapter, partial_bulk, soft delete, restore]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# artifact 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

아티팩트는 어느 스코프에도 속하지 않게 만들어진다. 개별 아티팩트를 고치고 soft delete,
restore 하는 문은 권한 그래프가 지키고, id 목록으로 여럿을 soft delete, restore 하는 옛 호출은
전역 역할이 지킨다.

공통 계약(대상 존재, 일괄 구성)은 프레임워크 계약 테스트가 확인한다. 여기에는 연산마다 대표
성공과 대표 실패, 그리고 아티팩트 규칙이 만드는 차이만 적는다.

## 수정하기

## soft delete, restore

purge 는 없다.

## 여럿 수정하기

## 여럿 soft delete, restore

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 아티팩트는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.

## id 목록으로 여럿 soft delete, restore

여럿 연산이 생기기 전의 호출이다. 옛 REST 경로와 GQL mutation 이 부른다.
