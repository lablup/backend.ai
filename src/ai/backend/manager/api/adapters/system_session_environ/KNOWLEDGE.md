---
name: system-session-environ-adapter-scenarios
type: reference
description: what the system session environ adapter guarantees, as scenarios; superadmin search of every row at every scope with filters, the default order and pages, the monitor role passing the search, the value source list any user reads, the read by ids checked per row against the public, domain and project member grants
scope: src/ai/backend/manager/api/adapters/system_session_environ
keywords: [system session environ, scenario, adapter, superadmin, monitor, global_search, public_list_value_sources, bulk_get_ids, partial bulk]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
updated:
  by: claude-code/opus-5.5
  at: 2026-10-26
status: draft
---
# 시스템 세션 환경변수 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

시스템 세션 환경변수 행은 public 스코프, 도메인 스코프, 프로젝트 스코프 중 하나에 만들어진다.
이 어댑터는 모든 행을 검색하는 호출, 값 출처 목록을 읽는 호출, id로 여러 행을 읽는 호출을 제공한다.

검색은 전역 superadmin 역할 검사로 보호된다. 세션에 실제로 주입되는 행을 고르지 않고, 스코프와
삭제 여부에 상관없이 조건에 맞는 행을 모두 반환한다.

id로 여러 행을 읽을 때는 행마다 권한을 검사한다. 모든 사용자는 public 스코프의 행을 읽을 수 있고,
도메인과 프로젝트의 구성원은 그 도메인과 프로젝트의 행을 읽을 수 있다.

## 전체 검색

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| superadmin이 모든 행을 검색한다 | public 스코프, 한 도메인, 한 프로젝트에 같은 키의 행을 하나씩 미리 만들어 둠. 프로젝트의 행은 삭제되어 있음. superadmin | 조건 없이 검색 | 세 행이 모두 반환된다. 삭제된 행도 반환된다 |
| 모니터 역할이 검색한다 | "superadmin이 모든 행을 검색한다"와 같은 행, 모니터 역할 | 조건 없이 검색 | superadmin과 같은 응답 |
| superadmin이 아닌 사용자가 검색한다 | "superadmin이 모든 행을 검색한다"와 같은 행, 그 프로젝트의 구성원 | 조건 없이 검색 | 역할 부족으로 거부 |
| 스코프 종류와 스코프 id로 검색한다 | "superadmin이 모든 행을 검색한다"와 같은 행, superadmin | 도메인 스코프와 그 도메인의 id를 지정해 검색 | 그 도메인의 행만 반환된다 |
| 삭제된 행만 검색한다 | "superadmin이 모든 행을 검색한다"와 같은 행, superadmin | 삭제된 행으로 지정해 검색 | 프로젝트의 행만 반환된다 |
| 키의 일부로 검색한다 | 키가 서로 다른 행 여럿, superadmin | 키에 포함된 문자열을 지정해 검색 | 그 문자열을 키에 포함한 행만 반환된다 |
| 값 출처로 검색한다 | 값 출처가 서로 다른 행 여럿, superadmin | 값 출처 하나를 지정해 검색 | 그 값 출처의 행만 반환된다 |
| 없는 값 출처로 검색한다 | superadmin | 매니저가 제공하지 않는 값 출처 이름을 지정해 검색 | 알 수 없는 값 출처로 거부 |
| 정렬을 지정하지 않는다 | 키가 서로 다른 행 여럿, superadmin | 조건 없이 검색 | 키의 오름차순으로 반환된다 |
| 개수를 지정해 나누어 검색한다 | 행 3개, superadmin | 2개씩 검색한 뒤 다음 페이지를 검색 | 첫 페이지에 2개와 다음 페이지가 있다는 표시, 다음 페이지에 나머지 1개. 전체 개수는 두 번 모두 3 |

모니터 역할은 전역 superadmin 역할 검사에서 읽기만 통과한다. REST handler와 GQL resolver는
어댑터를 부르기 전에 superadmin만 통과시키므로, 모니터 역할의 검색은 어댑터를 직접 부를 때만
통과한다.

## 값 출처 목록

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 일반 사용자가 값 출처 목록을 읽는다 | 어느 도메인과 프로젝트의 권한도 받지 않은 사용자 | 값 출처 목록을 조회 | 매니저가 제공하는 값 출처의 이름이 모두 반환된다 |

값 출처는 행이 아니라 매니저가 제공하는 목록이므로 로그인 여부만 확인하고 반환된다. 행의 값 출처는 이 목록의
이름으로 반환되고, 검색 조건에도 이 이름을 쓴다.

## id로 여러 행 읽기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| superadmin이 여러 스코프의 행을 함께 읽는다 | public 스코프, 한 도메인, 한 프로젝트의 행을 하나씩 미리 만들어 둠, superadmin | 세 행의 id 목록으로 조회 | 요청한 순서대로 세 행 |
| 프로젝트 구성원이 자기 프로젝트의 행과 다른 프로젝트의 행을 함께 읽는다 | 두 프로젝트에 행을 하나씩 미리 만들어 둠, 한 프로젝트의 구성원 | 두 행의 id 목록으로 조회 | 자기 프로젝트의 행은 반환되고, 다른 프로젝트 행의 항목은 권한 부족으로 거부 |
| 도메인 구성원이 다른 도메인의 행을 읽는다 | 다른 도메인의 행 하나, 한 도메인의 구성원 | 그 행의 id 목록으로 조회 | 그 항목이 권한 부족으로 거부 |
| 도메인과 프로젝트의 권한이 없는 사용자가 public 스코프의 행을 읽는다 | public 스코프의 행 하나, 어느 도메인과 프로젝트의 읽기 권한도 받지 않은 사용자 | 그 행의 id 목록으로 조회 | 그 행이 반환된다 |
| superadmin이 어느 행의 것도 아닌 id를 읽는다 | superadmin | 그 id 목록으로 조회 | 그 항목이 빈 값 |
| 프로젝트 구성원이 어느 행의 것도 아닌 id를 읽는다 | 한 프로젝트의 구성원 | 그 id 목록으로 조회 | 그 항목이 권한 부족으로 거부 |

여럿 읽기는 호출 전체를 거부하지 않고 항목마다 응답한다.

없는 id는 superadmin과 그 밖의 사용자에게 서로 다르게 응답한다. 권한 검사는 id마다 권한 그래프를
보는데, 그래프에 없는 id는 권한을 확인할 수 없어 superadmin이 아닌 사용자에게는 권한 부족으로
응답한다. 그 검사를 통과하는 superadmin만 빈 값을 받는다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 전체 검색, 값 출처 목록, id로 여러 행 읽기가 모두 위에 있다.

모든 어댑터가 물려받는 공용 도우미는 이 엔티티의 호출이 아니므로 적을 시나리오가 없다.
