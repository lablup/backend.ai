---
name: system-session-environ-adapter-scenarios
type: reference
description: what the system session environ adapter guarantees, as scenarios; the value source list any logged-in user reads and a call without login is refused
scope: src/ai/backend/manager/api/adapters/system_session_environ
keywords: [system session environ, scenario, adapter, value source, public_list_value_sources]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-27
status: draft
---
# 시스템 세션 환경변수 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

시스템 세션 환경변수 행은 public 스코프, 도메인 스코프, 프로젝트 스코프 중 하나에 만들어진다.
이 어댑터는 행이 가질 수 있는 값 출처 목록을 읽는 호출을 제공한다.

## 값 출처 목록

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 일반 사용자가 값 출처 목록을 읽는다 | 어느 도메인과 프로젝트의 권한도 받지 않은 사용자 | 값 출처 목록을 조회 | 매니저가 제공하는 값 출처의 이름이 모두 반환된다 |
| 로그인하지 않은 호출이 값 출처 목록을 읽는다 | 로그인한 사용자 없음 | 값 출처 목록을 조회 | 로그인하지 않은 호출로 거부 |

값 출처는 행이 아니라 매니저가 제공하는 목록이므로 로그인 여부만 확인하고 반환된다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 값 출처 목록이 위에 있다.

모든 어댑터가 물려받는 공용 도우미는 이 엔티티의 호출이 아니므로 적을 시나리오가 없다.
