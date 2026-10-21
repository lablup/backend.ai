---
name: session-lifecycle-handler-adapter-scenarios
type: reference
description: what the session lifecycle handler adapter guarantees, as scenarios; lists every lifecycle handler registered on the schedule coordinator with its name and the first line of its class docstring, no permission check of its own
scope: src/ai/backend/manager/api/adapters/session_lifecycle_handler
keywords: [session lifecycle handler, scenario, adapter, handler options, schedule coordinator]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-12
status: draft
---
# session_lifecycle_handler 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 이 문서 쪽을 먼저
의심한다.

어댑터가 제공하는 호출은 `list_session_lifecycle_handlers` 하나다.

이 호출은 스케줄 코디네이터에 등록된 세션 처리기 목록을 그대로 반환한다. 리소스 그룹의 기본 세션 옵션을
교체할 때 처리기별 설정의 이름을 검사하는 목록도 같은 코디네이터에서 읽는다. 그래서 이 호출이 반환한 이름은
그 검사를 통과한다.

어댑터는 권한을 검사하지 않는다. 슈퍼관리자 검사는 GQL resolver가 한다.
그래서 권한이 있는 경우와 없는 경우의 짝을 이 문서에 두지 않는다.

## 목록 조회 (`list_session_lifecycle_handlers`)

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 등록된 처리기를 반환한다 | 코디네이터에 세션 종료 처리기가 등록되어 있다 | 목록 조회 | 세션 종료 처리기 하나가 반환된다. 이름은 그 처리기가 정한 이름이고, 설명은 처리기 클래스 설명의 첫 줄이다 |
| 등록된 처리기가 없으면 빈 목록을 반환한다 | 코디네이터에 등록된 처리기가 없다 | 목록 조회 | 빈 목록이 반환된다 |

## 아직 적지 않은 것

- 클래스 설명이 없는 처리기의 설명이 null로 반환되는 경우. 설명이 없는 세션 처리기가 src에 없어서,
  시나리오로 두려면 테스트 전용 처리기 클래스를 따로 만들어야 한다.
