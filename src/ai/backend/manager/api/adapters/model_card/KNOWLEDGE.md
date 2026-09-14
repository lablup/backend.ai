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

## 아직 적지 않은 것

`create`가 아직 없다. 모델 카드는 폴더 위에 얹히므로 폴더를 먼저 세워야 한다.

`admin_bulk_delete`, `available_presets`, `batch_load_fields`, `create`, `delete`,
`deploy`, `get`, `min_resources`, `project_search`, `scan_project`, `scoped_search`,
`search_by_vfolder`, `update`.
