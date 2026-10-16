---
name: idle-checker-assignment-adapter-scenarios
type: reference
description: what the idle checker assignment adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/idle_checker_assignment match these one for one
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

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿을 한 번에 끈다 | 도메인 둘에 같은 검사기를 켜 둠 | 둘 끄기 | 둘 다 꺼진 할당으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 끈다 | 같은 할당 둘 | 둘 끄기 | 끈 것 없이 둘 다 찾을 수 없다는 이유로 실패 목록에 옴 |

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 도메인 둘에 같은 검사기를 켜 둠 | 셋 purge | 둘은 지우기 전 할당으로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 할당 둘 | 둘 purge | 지운 것 없이 둘 다 찾을 수 없다는 이유로 실패 목록에 옴 |

권한 없는 사용자에게는 할당 id 를 찾는 단계가 없는 id 와 같은 답을 준다. 할당이 있는지 드러내지
않기 위해서다. 슈퍼관리자에게는 없는 id 가 대상 없음으로 온다.

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 할당은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.

할당 id 는 데이터베이스가 만든다. 시나리오는 슈퍼관리자 한 명으로 할당을 검색해 id 를 얻은 뒤
호출자로 부른다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

`admin_create`, `update`, `purge`, `scoped_search`, `batch_load_fields`. `admin_search` 는
할당 id 를 얻는 데만 쓴다.
