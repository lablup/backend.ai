---
name: system-session-environ-adapter-scenarios
type: reference
description: what the system session environ adapter guarantees; rows are created in a public, domain or project scope, the global search is protected by the superadmin role check and lets the monitor role read, the value source list any logged-in user reads, the update and delete rules, and the per-row permission checks when reading several rows by id with different responses for unknown ids
scope: src/ai/backend/manager/api/adapters/system_session_environ
keywords: [system session environ, scenario, adapter, superadmin, monitor, global_search, scoped_search, public_list_value_sources, create, update, delete, restore, purge, bulk_get_ids, partial bulk]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
updated:
  by: claude-code/opus-5.5
  at: 2026-10-30
status: draft
---
# 시스템 세션 환경변수 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

시스템 세션 환경변수 행은 public 스코프, 도메인 스코프, 프로젝트 스코프 중 하나에 만들어진다.
이 어댑터는 모든 행을 검색하는 호출, 지정한 스코프 안에서 검색하는 호출, 값 출처 목록을 읽는 호출,
행을 만드는 호출, 행의 키를 바꾸는 호출, 행을 삭제하고 복원하는 호출, 행을 영구 삭제하는 호출,
id로 여러 행을 읽는 호출을 제공한다.

검색은 전역 superadmin 역할 검사로 보호된다. 세션에 실제로 주입되는 행을 고르지 않고, 스코프와
삭제 여부에 상관없이 조건에 맞는 행을 모두 반환한다.

id로 여러 행을 읽을 때는 행마다 권한을 검사한다. 모든 사용자는 public 스코프의 행을 읽을 수 있고,
도메인과 프로젝트의 관리자는 그 도메인과 프로젝트의 행을 읽을 수 있다. 관리자가 아닌 구성원은 도메인과
프로젝트의 행을 읽을 수 없다.

## 전체 검색

모니터 역할은 전역 superadmin 역할 검사에서 읽기만 통과한다. REST handler와 GQL resolver는
어댑터를 부르기 전에 superadmin만 통과시키므로, 모니터 역할의 검색은 어댑터를 직접 부를 때만
통과한다.

## 스코프 안에서 검색

## 값 출처 목록

값 출처는 행이 아니라 매니저가 제공하는 목록이므로 로그인 여부만 확인하고 반환된다. 행의 값 출처는 이 목록의
이름으로 반환되고, 검색 조건에도 이 이름을 쓴다.

## 생성

## 수정

스코프와 값 출처는 바꿀 수 없다. 같은 스코프에서는 삭제된 행을 포함해 키가 겹칠 수 없다.

## 삭제

삭제된 행은 그 뒤에 시작하는 세션에 주입되지 않는다.

## 복원

## 영구 삭제

## id로 여러 행 읽기

여럿 읽기는 호출 전체를 거부하지 않고 항목마다 응답한다.

없는 id는 superadmin과 그 밖의 사용자에게 서로 다르게 응답한다. 권한 검사는 id마다 권한 그래프를
보는데, 그래프에 없는 id는 권한을 확인할 수 없어 superadmin이 아닌 사용자에게는 권한 부족으로
응답한다. 그 검사를 통과하는 superadmin만 빈 값을 받는다.
