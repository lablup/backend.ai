---
name: project-service-composition
type: decision-table
description: 프로젝트 처리기의 모양 선택, dotfile이 프로젝트 컬럼인 이유, 멤버십이 별도 경로인 이유
scope: src/ai/backend/manager/services/project
keywords:
  - GroupProcessors
  - GroupCreator
  - GroupUpdater
  - GroupDotfilesUpdater
  - assign_users_to_project
  - RoleManagedEntityCreator
sources:
  - src/ai/backend/manager/services/project/processors.py
  - src/ai/backend/manager/models/project
generated:
  by: claude-code/opus-5
  at: 2026-08-22
status: draft
---

# 프로젝트 서비스

도메인 아래에 놓이므로 생성은 도메인을 scope로 하는 scope 모양이고, 이미 만들어진
프로젝트를 지목하는 연산은 single_entity다.

## 처리기 구성

| 필드 | 모양 | 연산 |
|---|---|---|
| `lookup` | lookup (public) | (도메인, 이름) → 프로젝트 |
| `get_project` | single_entity | GET |
| `global_search` | global | 전체 프로젝트 페이지 |
| `search_projects_by_domain` | scope (도메인) | SEARCH |
| `search_projects_by_user` | scope (사용자) | SEARCH |
| `create_project` | scope (도메인) | CREATE |
| `delete_project` / `restore_project` | single_entity | DELETE / RESTORE |
| `update_project` | single_entity | UPDATE |
| `purge_project` | single_entity | PURGE |
| `usage_per_month` / `usage_per_period` | global | SEARCH |
| `assign_users_to_project` / `unassign_users_from_project` | single_entity | UPDATE |
| `create_dotfile` / `update_dotfile` / `delete_dotfile` | single_entity | UPDATE |

## 멤버십은 프로젝트에 대한 변경이다

사용자를 프로젝트에 넣고 빼는 연산은 사용자가 아니라 프로젝트를 지목한다. 답하는 쪽이
프로젝트이고 감사 행도 프로젝트를 가리킨다.

멤버십 행 자체는 어느 쪽에도 속하지 않는 연관 행이라 v2 ops에 쓰는 원시 연산이 없다.
`update_project`이 멤버십을 함께 바꿀 때 멤버십 쓰기와 행 갱신은 서로 다른 트랜잭션이다.

## dotfile은 프로젝트 행의 컬럼이다

`dotfiles` 컬럼에 msgpack으로 묶여 저장된다. 판정은 `data/dotfile/types.py`의
`DotfileEntries`가 답하며, 도메인·키페어와 같은 판정을 쓴다.

## 서비스가 남은 연산

| 연산 | 남은 이유 |
|---|---|
| `update_project` | 멤버십 변경을 함께 받는다 |
| `purge_project` | vfolder와 세션을 함께 정리한다 |
| `assign_users_to_project` / `unassign_users_from_project` | 연관 행을 쓴다 |
| `usage_per_month` / `usage_per_period` | 커널 통계를 집계한다 |
| dotfile 쓰기 셋 | 읽고 병합한 뒤 쓴다 |
