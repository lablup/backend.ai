---
name: idle-checker-assignment-adapter-scenarios
type: reference
description: what the idle checker assignment adapter guarantees
scope: src/ai/backend/manager/api/adapters/idle_checker_assignment
keywords: [idle checker assignment, scenario, adapter, rbac, partial bulk, relation]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# idle_checker_assignment 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

할당은 스코프와 유휴 검사기를 잇는 relation 이다. 쓰기는 양쪽 엔티티의 권한을 모두 본다.
여럿 연산은 항목마다 단건 쓰기를 따로 돌린다.

## 여럿 수정하기

## 여럿 purge

권한 없는 사용자에게는 할당 id 를 찾는 단계가 없는 id 와 같은 답을 준다. 할당이 있는지 드러내지
않기 위해서다. 슈퍼관리자에게는 없는 id 가 대상 없음으로 온다.

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 할당은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.

할당 id 는 데이터베이스가 만든다. 시나리오는 슈퍼관리자 한 명으로 할당을 검색해 id 를 얻은 뒤
호출자로 부른다.
