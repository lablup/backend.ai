---
name: system-session-environ-adapter-scenarios
type: reference
description: what the system session environ adapter guarantees, as scenarios; superadmin read of the effective rows of a domain and project
scope: src/ai/backend/manager/api/adapters/system_session_environ
keywords: [system session environ, scenario, adapter, superadmin, global_resolve, effective rows]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
status: draft
---
# 시스템 세션 환경변수 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

이 어댑터는 domain과 project를 지정하면, 그곳에서 시작하는 세션이 받는 시스템 세션 환경변수의
유효한 행을 반환한다. 같은 키의 행이 여럿이면 project 행, domain 행, public 행 순으로 하나만
반환되고, 그 행이 꺼져 있으면 그 키는 반환되지 않는다. launcher가 세션을 시작할 때 고르는 행과
같다.

조회는 superadmin만 할 수 있다. 값(세션 id, 사용자 이메일 등)은 세션마다 달라서 반환하지 않고,
키마다 어떤 값을 넣는지와 어느 scope의 행인지를 반환한다.

## 유효한 행 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| superadmin이 domain과 project의 유효한 행을 조회한다 | public에 키 A, 그 domain에 키 A와 B, 그 project에 키 B 행을 미리 만들어 둠 | 그 domain과 project를 지정해 조회 | A는 domain 행, B는 project 행이 반환된다 |
| 꺼진 행이 이긴 키는 반환되지 않는다 | public에 켜진 키 A, 그 project에 꺼진 키 A 행을 미리 만들어 둠 | 그 domain과 project를 지정해 조회 | A가 반환되지 않는다 |
| 다른 domain과 project의 행은 반환되지 않는다 | 다른 domain에 키 C, 다른 project에 키 D 행을 미리 만들어 둠 | 그 domain과 project를 지정해 조회 | C와 D가 반환되지 않는다 |
| domain과 project에 행이 없으면 public 행만 반환된다 | public에 키 A 행만 미리 만들어 둠 | 행이 없는 domain과 project를 지정해 조회 | public의 A 행만 반환된다 |
| superadmin이 아닌 사용자가 조회한다 | 첫 시나리오와 같은 행을 미리 만들어 둠 | 그 domain과 project를 지정해 조회 | 역할 부족으로 거부 |

## 아직 적지 않은 것

없음.
