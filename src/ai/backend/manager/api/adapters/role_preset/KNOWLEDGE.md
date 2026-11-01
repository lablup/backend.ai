---
name: role-preset-adapter-scenarios
type: reference
description: what the role preset adapter guarantees for its writes; the permission graph guarding each write, bulk operations answering per id, and permission entries added all-or-nothing and removed one by one
scope: src/ai/backend/manager/api/adapters/role_preset
keywords: [role preset, scenario, adapter, partial bulk, soft delete, restore, purge, permission entry]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# role_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

역할 프리셋(이하 프리셋)은 global 스코프에 만들어진다. 수정, soft delete, restore, purge, 권한
항목 넣기·빼기는 프리셋에 대한 권한 그래프가 지킨다. 아무 역할도 받지 않은 사용자는 global 에서
나오는 권한이 없으므로 거부된다. 이 문서는 쓰기 연산만 적는다. 만들기와 읽기는 아직 적지 않았다.

공통 계약(대상 존재, 일괄 구성)은 프레임워크 계약 테스트가 확인한다. 여기에는 연산마다 대표
성공과 대표 실패만 적는다.

## 수정하기

## soft delete, restore, purge

## 여럿 수정하기

## 여럿 soft delete, restore, purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.

## 권한 항목 넣기, 빼기

항목 넣기는 전부 넣거나 하나도 넣지 않는다. 항목 빼기는 항목마다 답한다.
