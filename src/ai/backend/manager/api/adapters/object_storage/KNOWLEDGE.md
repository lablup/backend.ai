---
name: object-storage-adapter-scenarios
type: reference
description: what the object storage adapter guarantees; update, purge and their partial bulk forms, which only a superadmin passes because the row lives in global alone
scope: src/ai/backend/manager/api/adapters/object_storage
keywords: [object storage, scenario, adapter, superadmin, purge, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# object_storage 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

object storage 행은 global 에만 소속되어 만들어진다. 하나나 여럿을 지정해 수정·purge 하는 호출은
그 행에 부여된 권한을 검사한다. 그 권한은 global 에서만 나오므로 슈퍼관리자만 통과한다.

## 수정

## purge

옛 이름의 삭제는 같은 purge 를 부른다.

## 여럿 수정하기

## 여럿 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 object storage 는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.
