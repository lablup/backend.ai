# Template service: 배경

> 규칙: `../AGENTS.md`. Action 모양과 gate: `../../actions/AGENTS.md`.

이 service 는 REST v1 의 세션 템플릿과 cluster template 경로를 처리한다. 두 종류 모두
`session_templates` 의 row 이고 `type` 으로 구분하며, 각 template 은 소유자의 user scope 와
프로젝트의 scope 에 생성된다(`SessionTemplateCreator.created_in`).

## processor 마다 모양이 하나다

| Processor field | 모양 | 권한 판정 대상 |
|---|---|---|
| `create_task`, `create_cluster` | scope | 요청한 프로젝트 |
| `list_task`, `list_cluster` | scope | 요청자의 user scope |
| `global_list_task`, `global_list_cluster` | global | global gate. superadmin 이 통과한다 |
| `get_*`, `update_*`, `delete_*` | single_entity | 해당 template |

- 생성은 아직 이름 붙일 template 이 없으므로, 생성하는 프로젝트를 대상으로 권한을 판정한다.
- 목록은 두 읽기의 권한 판정 대상이 달라 action 두 개로 나뉜다. scope 읽기는 사용자 한 명을,
  모든 template 읽기는 global gate 를 대상으로 한다.

## 목록 action 은 REST handler 가 고른다

- superadmin 이 `all=true` 를 주면 global action 을 실행하고, 이 action 은
  `list_templates_in_global` 로 모든 template 을 읽는다.
- superadmin 이 아닌 호출자가 `all=true` 를 주면 scope 읽기로 대신하지 않고 `InsufficientPrivilege`
  으로 거부한다. 그래서 호출자가 일부 목록을 전체로 오해하지 않는다.
- `all` 이 없는 요청은 scope action 을 실행한다.
- handler 가 고르기 전에 role 을 확인하고, action 을 실행할 때 global gate 가 다시 확인한다.

## scope 읽기는 사용자와 사용자가 속한 프로젝트를 포함한다

- service 가 요청자의 `UserSessionTemplateTarget` 하나와 `joined_project_ids` 의 프로젝트마다
  `ProjectSessionTemplateTarget` 하나를 만들고, `list_templates_in_scopes` 가 그 조건을 OR 로 묶는다.
- action 의 권한은 user scope 하나로만 판정한다. 프로젝트 목록은 사용자 자신의 소속에서 오므로
  gate 가 프로젝트를 하나씩 검사하지 않는다.
- 도메인 관리자를 위한 분기는 없다. 관리자도 프로젝트 멤버와 같은 목록을 받는다.

## 두 읽기 모두 Searcher 를 실행하고 같은 읽기 안에서 이름을 채운다

- `list_templates_in_scopes` 는 `SessionTemplateSearcher` 를 `search_with_scopes` 로,
  `list_templates_in_global` 은 `search_in_global` 로 실행한다.
- `Searcher` 는 테이블 하나만 select 하므로, 소유자의 이메일과 프로젝트 이름은 같은 `read_ops()` 안에서
  `BulkUserQuerier` 와 `BulkProjectQuerier` 로 읽어 `SessionTemplateWithOwnerEmailAndProjectName` 으로 묶는다.

## 프로젝트 필터는 좁히기만 하고, is_owner 는 REST handler 가 계산한다

- `group_id` 는 scope 들이 읽은 row 중 프로젝트 하나의 row 만 남긴다. scope 밖의 프로젝트를 주면
  아무것도 반환되지 않는다.
- `is_owner` 는 row 의 `user_uuid` 가 요청자일 때 true 다. handler 가 비교하므로 두 읽기 모두
  요청자를 받지 않는다.
