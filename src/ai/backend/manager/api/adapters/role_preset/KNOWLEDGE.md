---
name: role-preset-adapter-scenarios
type: reference
description: what the role preset adapter guarantees for its writes, as scenarios; single and partial bulk update, soft delete, restore and purge, and adding and removing permission entries; the tests in tests/scenario/bai_scenario/manager/role_preset match these one for one
scope: src/ai/backend/manager/api/adapters/role_preset
keywords: [role preset, scenario, adapter, partial bulk, soft delete, restore, purge, permission entry]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# role_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

역할 프리셋(이하 프리셋)은 global 스코프에 만들어진다. 수정, soft delete, restore, purge, 권한
항목 넣기·빼기는 프리셋에 대한 권한 그래프가 지킨다. 아무 역할도 받지 않은 사용자는 global 에서
나오는 권한이 없으므로 거부된다. 이 문서는 쓰기 연산만 적는다. 만들기와 읽기는 아직 적지 않았다.

공통 계약(대상 존재, 일괄 구성)은 프레임워크 계약 테스트가 확인한다. 여기에는 연산마다 대표
성공과 대표 실패만 적는다.

## 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 이름을 바꾼다 | 프리셋 하나 | 이름 수정 | 새 이름을 실은 노드 전체 |
| 아무 권한도 받지 않은 사용자가 수정한다 | 같은 프리셋 | 이름 수정 | 권한 부족으로 거부 |

## soft delete, restore, purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 soft delete 한다 | 프리셋 하나 | soft delete | 삭제 표시가 켜진 노드 |
| 아무 권한도 받지 않은 사용자가 soft delete 한다 | 같은 프리셋 | soft delete | 권한 부족으로 거부 |
| soft delete 된 프리셋을 restore 한다 | 프리셋 하나 | soft delete 뒤 restore | 삭제 표시가 꺼진 노드 |
| 아무 권한도 받지 않은 사용자가 restore 한다 | 같은 프리셋 | restore | 권한 부족으로 거부 |
| 슈퍼관리자가 purge 한다 | 프리셋 하나 | purge | purge 하기 전의 노드 |
| 아무 권한도 받지 않은 사용자가 purge 한다 | 같은 프리셋 | purge | 권한 부족으로 거부 |

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 자동 부여를 한 번에 켠다 | 프리셋 둘 | 둘의 자동 부여 수정 | 둘 다 바뀐 값으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 프리셋 둘 | 둘의 자동 부여 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 soft delete, restore, purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 soft delete 한다 | 프리셋 둘 | 셋 soft delete | 둘은 삭제 표시가 켜진 채 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 soft delete 한다 | 같은 프리셋 둘 | 둘 soft delete | soft delete 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| soft delete 된 여럿을 한 번에 restore 한다 | 프리셋 둘 | 둘 soft delete 뒤 둘 restore | 둘 다 삭제 표시가 꺼진 채 옴 |
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 프리셋 둘 | 셋 purge | 둘은 purge 하기 전의 노드로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 프리셋 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.

## 권한 항목 넣기, 빼기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 항목 둘을 한 번에 넣는다 | 항목 없는 프리셋 하나 | 항목 둘 넣기 | 넣은 두 항목 |
| 아무 권한도 받지 않은 사용자가 항목을 넣는다 | 같은 프리셋 | 항목 둘 넣기 | 권한 부족으로 거부 |
| 슈퍼관리자가 항목 둘과 없는 id 하나를 한 번에 뺀다 | 항목 둘이 있는 프리셋 하나 | 셋 빼기 | 둘은 처리된 목록에 오고, 없는 id 는 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 항목을 뺀다 | 같은 프리셋 | 둘 빼기 | 뺀 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

항목 넣기는 전부 넣거나 하나도 넣지 않는다. 항목 빼기는 항목마다 답한다.

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

| 호출 | 이유 |
|---|---|
| 만들기, 읽기, 여럿 읽기, search, 권한 항목 search | 쓰기 연산 이름을 맞추는 작업에서 쓰기만 적었다 |
| 옛 일괄 soft delete, restore, purge, 항목 넣기·빼기 | 같은 연산을 옛 응답 모양으로 바꿔 답하는 호출이다. 연산은 위 표가 확인한다 |
