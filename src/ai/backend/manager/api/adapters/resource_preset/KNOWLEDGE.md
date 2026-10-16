---
name: resource-preset-adapter-scenarios
type: reference
description: what the resource preset adapter guarantees for update and purge, single and partial bulk, as scenarios; the tests in tests/scenario/bai_scenario/manager/resource_preset match these one for one
scope: src/ai/backend/manager/api/adapters/resource_preset
keywords: [resource preset, scenario, adapter, rbac, update, purge, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# resource_preset 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

리소스 프리셋은 리소스 그룹에 묶이지 않으면 public 스코프에 속한다. 수정과 purge 는 권한
그래프가 지킨다. public 에서 프리셋 수정 권한을 받은 사용자는 슈퍼관리자가 아니어도 수정할 수
있다.

## 수정

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 이름만 바꾼다 | 프리셋 하나 | 이름 수정 | 새 이름의 노드 전체, 나머지는 그대로 |
| public 에서 수정 권한을 받은 사용자가 이름을 바꾼다 | 같은 프리셋 | 이름 수정 | 새 이름의 노드 전체 |
| 아무 권한도 받지 않은 사용자가 수정한다 | 같은 프리셋 | 이름 수정 | 권한 부족으로 거부 |
| 없는 id 를 수정한다 | 슈퍼관리자 | 이름 수정 | 대상 없음으로 거부 |

## purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 purge 한다 | 프리셋 하나 | purge | 지운 프리셋의 id |
| 아무 권한도 받지 않은 사용자가 purge 한다 | 같은 프리셋 | purge | 권한 부족으로 거부 |
| 없는 id 를 purge 한다 | 슈퍼관리자 | purge | 대상 없음으로 거부 |

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 공유 메모리를 한 번에 바꾼다 | 프리셋 둘 | 둘의 공유 메모리 수정 | 둘 다 새 공유 메모리로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 프리셋 둘 | 둘의 공유 메모리 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| 필수 자원 슬롯이 빠진 자원으로 바꾼다 | 프리셋 둘, 슈퍼관리자 | 하나의 자원을 필수 슬롯 없이 수정 | 요청 전체가 입력 오류로 거부됨 |

여럿 수정은 리소스 그룹을 바꾸지 않는다. 리소스 그룹은 프리셋을 누구에게 보일지를 바꾸므로
단건 수정으로만 바꾼다.

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 프리셋 둘 | 셋 purge | 둘은 지워진 노드로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 프리셋 둘 | 둘 purge | 지워진 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 처리하지 못한 항목 때문에 호출 전체를 거부하지 않는다. 처리한 프리셋은 처리된
목록에, 처리하지 못한 것은 id 와 이유를 실패 목록에 싣는다.

## 아직 적지 않은 것

어댑터가 제공하는 `search`, `get`, `batch_load_by_ids`, `create`, `apply_resource_group` 은 아직
시나리오가 없다.
