---
name: idle-checker-adapter-scenarios
type: reference
description: what the idle checker adapter guarantees
scope: src/ai/backend/manager/api/adapters/idle_checker
keywords: [idle checker, scenario, adapter, superadmin, partial bulk, purge]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# idle_checker 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

유휴 검사기는 전역 카탈로그에 있고 어느 스코프에도 속하지 않는다. 쓰기는 전역 superadmin 역할이
지킨다.

## 여럿 purge

여럿 purge 는 호출 전체를 거부하지 않는다. 지운 검사기는 처리된 목록에, 지우지 못한 것은 id 와
이유를 실패 목록에 싣는다.
