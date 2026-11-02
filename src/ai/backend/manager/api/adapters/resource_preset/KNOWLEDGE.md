---
name: resource-preset-adapter-scenarios
type: reference
description: what the resource preset adapter guarantees for update and purge, single and partial bulk
scope: src/ai/backend/manager/api/adapters/resource_preset
keywords: [resource preset, scenario, adapter, rbac, update, purge, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# resource_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

리소스 프리셋은 리소스 그룹에 묶이지 않으면 public 스코프에 속한다. 수정과 purge 는 권한
그래프가 지킨다. public 에서 프리셋 수정 권한을 받은 사용자는 슈퍼관리자가 아니어도 수정할 수
있다.

## 수정

## purge

## 여럿 수정하기

여럿 수정은 리소스 그룹을 바꾸지 않는다. 리소스 그룹은 프리셋을 누구에게 보일지를 바꾸므로
단건 수정으로만 바꾼다.

## 여럿 purge

여럿 연산은 처리하지 못한 항목 때문에 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된
목록에, 처리하지 못한 것은 id 와 이유를 실패 목록에 싣는다.
