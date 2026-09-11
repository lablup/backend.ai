---
name: resource-group-adapter-scenarios
type: reference
description: what the resource group adapter guarantees, as scenarios; the tests in tests/scenario/bai_scenario/manager/resource_group match these
scope: src/ai/backend/manager/api/adapters/resource_group
keywords: [resource group, scenario, adapter, rbac, scheduling]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# 리소스 그룹 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다.

리소스 그룹 생성은 도메인 생성과 같이 전역 역할이 지킨다. 권한을 얼마나 받았는지와 무관하다.

세션이 리소스 그룹에 닿는 길은 셋이다. 도메인에 걸린 것, 프로젝트에 걸린 것, 사용자의
키페어에 걸린 것. 세션의 스코프가 그 셋 중 하나에서 그룹을 찾는다.

## 만들기와 읽기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 도메인 아래에 만든다 | 도메인이 있음 | 만들기 | 그 이름의 그룹 |
| 슈퍼관리자가 아닌 사용자가 만든다 | 권한 없음 | 만들기 | 역할로 거부 |
| 이미 있는 그룹을 이름으로 읽는다 | 그 그룹이 있음 | 이름으로 조회 | 그 그룹 |

## 아직 적지 않은 것

세 갈래 연결은 시드로는 세울 수 있으나 그것을 확인하는 시나리오는 아직 없다. 세션 스케줄링을
세울 수 있게 되면 거기서 확인한다.

`admin_replace_default_deployment_options`, `admin_replace_default_session_options`,
`batch_load_by_ids`, `batch_load_by_names`, `batch_load_fields`,
`get_allowed_domains_for_resource_group`, `get_allowed_projects_for_resource_group`,
`get_allowed_resource_groups_for_domain`, `get_allowed_resource_groups_for_project`,
`get_fair_share_spec`, `get_resource_info`, `purge`, `scoped_search`, `search`,
`update`, `update_allowed_domains_for_resource_group`,
`update_allowed_projects_for_resource_group`,
`update_allowed_resource_groups_for_domain`,
`update_allowed_resource_groups_for_project`, `update_config`,
`update_fair_share_spec`.
