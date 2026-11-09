# 세션 그룹 service: 배경

> 규칙은 `../AGENTS.md`, 배치 정책은 `proposals/BEP-1064-session-group-placement.md` 에 있다.

세션 그룹은 멤버 세션의 배치 정책을 담는다. 프로젝트와 사용자가 own 한다. deployment 는 모든 replica group 을 포함하는 세션 그룹을 하나 생성하고, 그 그룹은 사용자가 아니라 deployment 가 관리한다.

## processor fields

`backend.ai mgr ops list` 를 실행하면 연결된 목록이 출력된다. 그 출력이 엔티티 종류, shape, operation, gate, backing 을 알려 준다.

## deployment 의 그룹은 모든 사용자 조회에서 제외된다

| Operation | 그룹이 제외되는 곳 |
|---|---|
| `get` | action 의 searcher 는 replica group 이 그 row 를 가지고 있지 않을 때만 row 를 찾는다. 아니면 service 가 찾을 수 없음으로 반환한다 |
| `bulk_get_ids` | 여러 id 에 같은 searcher 를 사용한다. replica group 이 가진 그룹은 빈 값으로 반환한다 |
| `scoped_search` | 모든 `SessionGroupTarget` 이 자기 스코프 조건에 같은 조건을 추가한다 |
| `global_search` | 제외되지 않는다. superadmin 은 모든 그룹을 본다 |
| `update` | `SessionGroupUpdater` 가 그 조건을 `GuardCheck` 로 담는다. replica group 이 가진 그룹은 사용 중으로 거부된다. 상태 코드는 409 다 |
| `purge` | purger 의 guard 가 DELETE 에 함께 적용된다. replica group 이 가진 그룹은 사용 중으로 거부된다. 상태 코드는 409 다 |
| session `enqueue` | `EnqueueSessionAction.to_held_session_group_searcher` 가 조건을 담는다. 소유자의 replica group 이 가진 그룹은 사용 중으로 거부되고, 다른 그룹은 찾을 수 없음으로 반환된다 |

- 조건은 `SessionGroupSearchableFields.linked.replica_groups.not_exists()` 이고, 모든 경로가 이 선언 하나를 읽는다.
- 조회는 replica group 이 가진 그룹을 거부가 아니라 찾을 수 없음으로 반환한다. 호출자가 프로젝트를 통해 그 그룹에 READ 를 가질 수 있으므로 권한이 그 그룹을 제외하는 이유가 아니다.
- update 와 purge 는 replica group 이 가진 그룹을 사용 중으로 거부한다. 그 그룹에 UPDATE 나 PURGE 를 가진 호출자만 guard 에 도달하고, 참조하는 deployment 가 그 그룹을 관리한다.
- enqueue 는 그룹이 사용 중이라는 응답을 소유자에게만 준다. 다른 호출자에게는 그룹이 찾을 수 없음으로 반환된다. enqueue 는 그룹에 대한 권한을 검사하지 않는다.

## id 로 하는 조회는 service 를 둔다

- generic ops 의 get 과 bulk get 은 id 로만 row 를 조회하므로 replica group 이 가진 그룹을 제외할 수 없다.
- `get` 은 `single_entity` 로, `bulk_get_ids` 는 `partial_bulk` 로 연결한다. gate 는 ops shape 이 실행하는 것과 같은 READ 검사다.
- searcher 는 generic `OpsRepository` 로 간다. service 가 찾을 수 없음 응답과 id 별 응답을 맡으므로 domain repository 를 두지 않는다.
- `bulk_get_ids` 는 partial 이다. gate 가 id 마다 판정하고, service 가 통과한 id 마다 그룹이나 빈 값을 응답한다.
- graph 에 node 가 없는 id 는 검사할 수 없으므로 superadmin 이 아닌 호출자에게는 빈 항목이 아니라 거부다.

## update 는 ops 로 실행한다

- `placement_direction` 과 `placement_enforcement` 만 변경할 수 있다. scheduler 가 배치마다 이 값을 읽으므로 이후에 배치되는 멤버는 새 정책을 따른다.
- guard 가 UPDATE 에 함께 적용되므로 generic update 에 service method 가 필요 없다.
- 설정할 것이 없으면 ops 는 guard 없이 row 를 읽는다. 그래서 update 입력은 두 field 어느 쪽도 지정하지 않는 호출을 거부한다.

## search 는 ops 로 실행한다

- search 는 action 에서 스코프를 받으므로 replica group 이 가진 그룹 조건이 searcher 가 아니라 Target 에 적용된다.
- 삭제로 표시된 그룹은 최상위 필터가 `deleted_at` 을 지정하지 않으면 제외된다. `AND`/`OR`/`NOT` 안에서 지정해도 이 제외를 해제하지 못한다. 이 기본값은 adapter 의 것이고 `role_preset` 도 같은 방식이다.

## 생성은 ops 로 실행한다

- `create` 는 service method 없이 `entity_create_ops` 로 연결한다. action 의 스코프 Target 이 프로젝트이므로 gate 는 그 프로젝트의 session_group CREATE 다.
- 호출자가 소유자가 되고, row 가 자기 프로젝트와 소유자에 연결된다. 도메인은 insert 가 결정하는 프로젝트의 도메인이므로 다른 도메인의 호출자는 이 그룹을 자기 도메인에 둘 수 없다.

## purge 는 ops 로 실행한다

- `purge` 는 service method 없이 `entity_purge_ops` 로 연결한다. purger 의 guard 가 replica group 이 가진 그룹 조건을 담으므로 분기할 것이 없다.
- row 와 가상 엔티티는 함께 삭제된다. 멤버 세션은 남고, FK(`ON DELETE SET NULL`)가 그 `session_group_id` 를 비운다.
- 동시 트랜잭션이 추가한 replica group 은 guard 의 snapshot 너머에 있으므로 DELETE 가 FK(`replica_groups.session_group_id`, NO ACTION)에서 실패한다. ops 는 이를 `ForeignKeyViolationError` 로 발생시키고 응답은 409 다.
