---
name: model-card-adapter-scenarios
type: reference
description: what the model card adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/model_card match these
scope: src/ai/backend/manager/api/adapters/model_card
keywords: [model card, scenario, adapter, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 모델 카드 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

## 조회

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 모델 카드가 없을 때 슈퍼관리자가 훑는다 | 모델 카드 없음 | 전체 조회 | 비어 있음 |
| 슈퍼관리자가 아닌 사용자가 훑는다 | 권한 없음 | 전체 조회 | 역할로 거부 |

## 쓸 수 있는 프리셋

카드의 요구 자원을 모두 채우는 프리셋을 묻는다. 프리셋은 공개 스코프에 있으므로, 물을 수
있는지는 그 카드를 읽을 수 있는지가 정한다.

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 카드를 읽을 수 있는 사용자가 묻는다 | 요구 자원이 있는 카드 하나, 그것을 채우는 프리셋 하나와 못 채우는 프리셋 하나, 그 프로젝트에서 카드 읽기 권한을 받은 사용자 | 그 카드에 쓸 수 있는 프리셋 조회 | 채우는 프리셋만 |
| 아무 권한도 없는 사용자가 묻는다 | 같은 카드와 프리셋, 권한 없음 | 같은 조회 | 권한으로 거부 |
| 카드를 읽을 수 있는 사용자가 없는 카드를 묻는다 | 카드 읽기 권한을 받은 사용자 | 존재하지 않는 id로 조회 | 권한으로 거부 — 없는 행에는 부여된 권한도 없다 |
| 슈퍼관리자가 없는 카드를 묻는다 | 슈퍼관리자 | 존재하지 않는 id로 조회 | 없다고 거부 |

## 아직 적지 않은 것

`create`가 아직 없다. 모델 카드는 폴더 위에 얹히므로 폴더를 먼저 세워야 한다.

`admin_bulk_delete`, `batch_load_fields`, `create`, `delete`, `deploy`, `get`,
`min_resources`, `project_search`, `scan_project`, `scoped_search`, `search_by_vfolder`,
`update`.
