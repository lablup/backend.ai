---
name: idle-checker-adapter-scenarios
type: reference
description: what the idle checker adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/idle_checker match these one for one
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

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 검사기 둘이 있음 | 셋 purge | 둘은 지운 검사기로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 검사기 둘 | 둘 purge | 지운 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 purge 는 호출 전체를 거부하지 않는다. 지운 검사기는 처리된 목록에, 지우지 못한 것은 id 와
이유를 실패 목록에 싣는다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

`admin_create`, `admin_update`, `admin_purge`, `admin_search`, `batch_load_by_ids`,
`batch_load_fields`.
