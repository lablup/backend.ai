---
name: model-card-adapter-scenarios
type: reference
description: what the model card adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/model_card match these
scope: src/ai/backend/manager/api/adapters/model_card
keywords: [model card, scenario, adapter, rbac, purge, partial_bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# 모델 카드 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 모델 카드가 없을 때 슈퍼관리자가 훑는다 | 모델 카드 없음 | 전체 조회 | 비어 있음 |
| 슈퍼관리자가 아닌 사용자가 훑는다 | 권한 없음 | 전체 조회 | 역할로 거부 |

## 수정

카드는 프로젝트에 놓인 폴더 위에 얹는다. 카드를 만든 사람과 부르는 사람은 다르다. 권한은 카드가
놓인 프로젝트에서 받는다. 수정은 고친 카드를 최소 자원 요구와 함께 읽어 답하므로 읽기 권한도
필요하다.

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 읽기와 수정 권한을 받은 사용자가 제목을 바꾼다 | 카드 하나 | 제목 수정 | 제목만 새 값이고 나머지는 그대로인 카드 전체 |
| 아무 권한도 받지 않은 사용자가 수정한다 | 같은 카드 | 제목 수정 | 권한 부족으로 거부 |

## purge

purge 는 카드 행을 지운다. 옵션을 주면 카드가 얹힌 폴더를 휴지통으로 옮긴다.

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| purge 권한을 받은 사용자가 카드를 purge 한다 | 카드 하나 | 폴더는 두고 purge | 그 카드의 id |
| 아무 권한도 받지 않은 사용자가 purge 한다 | 같은 카드 | 폴더는 두고 purge | 권한 부족으로 거부 |

## 여럿 수정하기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 읽기와 수정 권한을 받은 사용자가 여럿의 제목을 한 번에 바꾼다 | 카드 둘 | 둘의 제목 수정 | 둘 다 새 제목으로 오고 실패한 것은 없음 |
| 아무 권한도 받지 않은 사용자가 여럿을 수정한다 | 같은 카드 둘 | 둘의 제목 수정 | 수정된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

## 여럿 purge

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| purge 권한을 받은 사용자가 여럿을 한 번에 purge 한다 | 카드 둘 | 둘 purge | 둘 다 purge 전 모습으로 처리된 목록에 오고 실패한 것은 없음 |
| 슈퍼관리자가 둘과 없는 id 하나를 한 번에 purge 한다 | 카드 둘 | 셋 purge | 둘은 처리된 목록에 오고, 없는 id 는 대상 없음 이유로 실패 목록에 옴. 권한 검사가 슈퍼관리자를 먼저 통과시켜 없는 id 가 purge 까지 간다 |
| 아무 권한도 받지 않은 사용자가 여럿을 purge 한다 | 같은 카드 둘 | 둘 purge | purge 된 것 없이 둘 다 권한 부족 이유로 실패 목록에 옴 |

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 카드는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. purge 된 카드의 최소 자원 요구는 카드와 함께 지워져 처리된 목록에
싣지 않는다.

## 아직 적지 않은 것

`admin_bulk_delete`, `available_presets`, `batch_load_by_ids`, `create`, `deploy`, `get`,
`min_resources`, `ownership_search`, `project_search`, `scan_project`, `scoped_search`.
