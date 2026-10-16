---
name: rbac-adapter-scenarios
type: reference
description: what the rbac adapter guarantees for role writes, as scenarios; the tests in tests/scenario/bai_scenario/manager/rbac match these one for one
scope: src/ai/backend/manager/api/adapters/rbac
keywords: [rbac, role, scenario, adapter, restore, partial_bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# rbac 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

지금은 역할 쓰기만 적는다. 역할은 한 스코프에 속하고, 역할을 고치는 문은 그 스코프의 권한
그래프가 지킨다. 대상 역할은 부르는 사람이 속하지 않은 도메인에 둔다. 슈퍼관리자가 아닌 사람이
부르는 행은 아무 권한도 받지 않은 사용자다.

## 수정

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 역할의 설명을 바꾼다 | 커스텀 역할 하나 | 설명 수정 | 새 설명을 실은 역할 전체 |
| 아무 권한도 받지 않은 사용자가 역할을 수정한다 | 같은 역할 | 설명 수정 | 권한 부족으로 거부 |

## soft delete, restore, purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 역할을 soft delete 한다 | 활성 역할 하나 | soft delete | 그 역할의 id |
| 아무 권한도 받지 않은 사용자가 역할을 soft delete 한다 | 같은 역할 | soft delete | 권한 부족으로 거부 |
| soft delete 된 역할을 restore 한다 | 역할 하나 | soft delete 뒤 restore | 그 역할의 id |
| 아무 권한도 받지 않은 사용자가 역할을 restore 한다 | 같은 역할 | restore | 권한 부족으로 거부 |
| 슈퍼관리자가 역할을 purge 한다 | 역할 하나 | purge | 그 역할의 id |
| 아무 권한도 받지 않은 사용자가 역할을 purge 한다 | 같은 역할 | purge | 권한 부족으로 거부 |

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 설명을 한 번에 바꾼다 | 역할 둘 | 둘의 설명 수정 | 둘 다 새 설명으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 역할 둘 | 둘의 설명 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 soft delete, restore, purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 soft delete 한다 | 활성 역할 둘 | 셋 soft delete | 둘은 삭제 상태로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 soft delete 한다 | 같은 역할 둘 | 둘 soft delete | soft delete 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| soft delete 된 여럿을 한 번에 restore 한다 | 역할 둘 | 둘 soft delete 뒤 둘 restore | 둘 다 활성으로 옴 |
| 슈퍼관리자가 여럿을 한 번에 purge 한다 | 역할 둘 | 둘 purge | 둘 다 처리된 목록에 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 역할 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 역할은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

역할 만들기와 읽기, 검색, 권한 항목(만들기, 수정, purge, 여럿 추가, 여럿 제거, 교체), 역할
부여와 회수, 부르는 사람이 가진 권한 조회, 권한 표 조회. 이 호출들의 시나리오는 아직 아무도 적지
않았다.
