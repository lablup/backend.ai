---
name: artifact-adapter-scenarios
type: reference
description: what the artifact adapter guarantees for update, soft delete and restore, as scenarios; the tests in tests/scenario/bai_scenario/manager/artifact match these one for one
scope: src/ai/backend/manager/api/adapters/artifact
keywords: [artifact, scenario, adapter, partial_bulk, soft delete, restore]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# artifact 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

아티팩트는 어느 스코프에도 속하지 않게 만들어진다. 개별 아티팩트를 고치고 soft delete,
restore 하는 문은 권한 그래프가 지키고, id 목록으로 여럿을 soft delete, restore 하는 옛 호출은
전역 역할이 지킨다.

공통 계약(대상 존재, 일괄 구성)은 프레임워크 계약 테스트가 확인한다. 여기에는 연산마다 대표
성공과 대표 실패, 그리고 아티팩트 규칙이 만드는 차이만 적는다.

## 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 설명을 바꾼다 | 아티팩트 하나 | 설명 수정 | 새 설명을 실은 아티팩트 |
| 아무 권한도 받지 않은 사용자가 고친다 | 같은 아티팩트 | 설명 수정 | 권한 부족으로 거부 |
| soft delete 된 아티팩트를 고친다 | 같은 아티팩트 | soft delete 뒤 설명 수정 | 대상 없음으로 거부 |

## soft delete, restore

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 soft delete 한다 | 아티팩트 하나 | soft delete | 삭제됨 상태의 아티팩트 |
| 아무 권한도 받지 않은 사용자가 soft delete 한다 | 같은 아티팩트 | soft delete | 권한 부족으로 거부 |
| soft delete 된 것을 restore 한다 | 같은 아티팩트 | soft delete 뒤 restore | 살아 있는 상태의 아티팩트 |
| 아무 권한도 받지 않은 사용자가 restore 한다 | 같은 아티팩트 | restore | 권한 부족으로 거부 |

purge 는 없다.

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 여럿의 설명을 한 번에 바꾼다 | 아티팩트 둘 | 둘의 설명 수정 | 둘 다 새 설명으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 고친다 | 같은 아티팩트 둘 | 둘의 설명 수정 | 고쳐진 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 soft delete, restore

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 soft delete 한다 | 아티팩트 둘 | 셋 soft delete | 둘은 삭제됨 상태로 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴 |
| 아무 권한도 받지 않은 사용자가 여럿을 soft delete 한다 | 같은 아티팩트 둘 | 둘 soft delete | soft delete 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |
| soft delete 된 여럿을 한 번에 restore 한다 | 아티팩트 둘 | 둘 soft delete 뒤 둘 restore | 둘 다 살아 있는 상태로 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 아티팩트는 처리된 목록에, 처리하지 못한 것은
id 와 이유를 실패 목록에 싣는다.

## id 목록으로 여럿 soft delete, restore

여럿 연산이 생기기 전의 호출이다. 옛 REST 경로와 GQL mutation 이 부른다.

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 id 목록으로 soft delete 한다 | 아티팩트 둘 | 둘 soft delete | 둘 다 삭제됨 상태로 옴 |
| 슈퍼관리자가 아닌 사용자가 id 목록으로 soft delete 한다 | 같은 아티팩트 둘 | 둘 soft delete | 역할로 거부 |
| 슈퍼관리자가 id 목록으로 restore 한다 | 아티팩트 둘 | 둘 soft delete 뒤 둘 restore | 둘 다 살아 있는 상태로 옴 |

## 아직 적지 않은 것

어느 시나리오도 부르지 않는 어댑터 호출이다. 실행 결과가 이 목록을 함께 낸다.

`admin_search`, `admin_search_gql`, `search_revisions_gql`, `search_revisions_of_artifact_gql`,
`batch_load_by_ids`, `batch_load_revisions_by_ids`, `get`, `get_revision`, `scan`,
`import_revision`, `delegate_scan`, `delegate_import_batch`, `cleanup_revision`,
`cancel_import`, `approve_revision`, `reject_revision`, `retrieve_models`
