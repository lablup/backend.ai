# Manager Services layer: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다. action framework 설계 배경은 `../actions/KNOWLEDGE.md` 에, write spec 설계 배경은 `../models/specs/KNOWLEDGE.md` 에 있다.

## 이 문서가 있는 이유

services 계층은 도메인 검증과 business rule 이 있는 곳이다. 이 문서는 v2 전환에서 계층의 중심 판단, 즉 어떤 entity_type 을 어떤 모양으로 배선하는지와 service 메서드를 언제 남기는지를 담는다. 대량 교체 작업(BA-7295~7302)은 이 표와 다른 것을 모두 맞추는 일이다.

## 판단 기준 셋과 항상 정확히 하나의 parent

- **독립 권한 부여 여부**: 이 대상의 접근을 따로 허용하거나 거부하는 데 실제 가치가 있는지 판단한다.
- **parent 없는 존재 여부**: 다른 row 없이 생성되고 살아남을 수 있는지(독립적인 수명) 판단한다.
- **사용자 직접 처리 여부**: API 가 이 대상을 CRUD 로 지정하는지 판단한다.
- parent(`scope_of`)는 항상 정확히 하나이다. 추가 접근 경로는 membership(`member_of`, 공유와 유사)으로 표현한다.
- 모든 entity 가 scope 를 겸하므로, scope 가 아닌 entity(예: deployment)도 자식을 가질 수 있다.

판단 결과와 배선, spec 대응은 다음과 같다.

| 판단 | 조건 | action 모양 | write spec |
|---|---|---|---|
| scope 제공 | 셋 다 예이고 다른 entity 를 govern 한다 | scope (create) / single 등 | `RoleManagedEntity*` (preset 역할 부여) |
| entity | parent 가 있고 직접 다룬다 | scope (create) / single / bulk | `Entity*` (own virtual entity + member_of) |
| global | RBAC scope 밖이고 직접 다룬다 | global (gate: SA 또는 public read) | `GlobalEntity*` (등록 없음) |
| field | 독립 권한이 없고 수명이 묶인다 | 소유자 위의 single_entity | `FieldEntity*` (`owner_id` 필요) |
| action-only | 대상 row 가 없다 (동작 / non-DB) | 대상 성격에 따르고 spec 없음 | 없음 (service 유지) |

## entity_type 판단: scope 제공과 entity

아직 미결로 표시한 항목은 해당 이관 작업에서 확정한다. 여기 없는 도메인은 기준으로 명백히 나뉜다(대부분 global 또는 entity).

scope 제공 (`RoleManagedEntity*`):

| entity_type | parent | 메모 |
|---|---|---|
| domain | 최상위 (global) | 생성 이관이 가장 늦다 |
| project (group) | domain | |
| user | domain | |
| resource_group (scaling_group) | domain | |

entity (`Entity*`):

| entity_type | parent (scope) | 메모 |
|---|---|---|
| session | project | 소유 user 는 member_of 로 연결한다 (확정) |
| vfolder | 생성 scope (user 또는 project, 정확히 하나) | |
| deployment (endpoint) | project | |
| artifact | artifact_registry | scope 가 아닌 parent |
| artifact_revision | artifact | import/approve 상태 기계는 revision 단위이다 |
| model_card | project | |
| session_template | 생성 scope (domain/project/user) | |
| role | role 이 속한 scope | |

## field 로 내린 entity_type

소유자를 거쳐 권한을 받고 독립 권한이 없다. `FieldEntity*` 이며 membership 그래프에 들어가지 않는다.

| entity_type | 소유자 | 메모 |
|---|---|---|
| kernel | session | entity 등록 금지 (확정) |
| deployment:revision, route, access_token, auto_scaling_rule, replica, replica_group | deployment | (확정) |
| deployment:policy | deployment | deployment 의 단일(1:1, FK CASCADE) rollout 전략 설정 (확정) |
| role:permission, role:assignment | role | |
| keypair | user | credential 로 독립 권한이 없고, 이름을 변경하기보다 해지하고 재발급한다 |
| dotfile | keypair | keypairs row 안에 묶인 column |
| image:alias, tag, resource_limit | image | |
| storage_namespace | object_storage | storage_id+namespace, 수명이 묶인다 |
| fair_share x3, usage_bucket x3 | resource_group | 모든 row 가 `resource_group_id` 를 가진다(fair share 유일성의 key). row 는 scope 별로 분해한 resource group 의 회계이고, domain/project/user 접근은 읽기의 scope 필터이며, 관리 write 는 rg 수준이다 |
| resource_group:domain, resource_group:user_group | resource_group | association row |

## global 로 판단한 entity_type

RBAC scope 밖의 대상이다. `GlobalEntity*` 이며 membership 등록이 없다.

| entity_type | 메모 |
|---|---|
| agent, image, container_registry, artifact_registry, object_storage, vfs_storage | 관리자 도메인 인프라 |
| resource_slot_type, retention_policy, runtime_variant(+preset), prometheus_query_preset(+category), login_client_type, role_preset, idle_checker(+assignment), notification_channel, notification_rule, resource policy 3종, service_catalog, app_config_definition | 시스템 설정/catalog 이고 읽기의 공개 범위만 다르다 (public) |
| audit_log, error_log, scheduling_history 기록 | 시스템 기록이고 `*:scoped_history` 형태만 scoped search 이다 |
| `invitation` (지금은 `vfolder:invitation`) | 방향: 모든 entity 가 사용할 수 있는 global invitation 하나로 나누고 entity_type/entity_id 를 받는다. 권한 부여는 Grant / Invite 두 경로로 흐른다 |

## action-only 로 남는 entity_type: 대상 row 없음

동작이거나 DB 가 아닌 대상이다. spec 없이 service 를 유지한다.

| entity_type | 메모 |
|---|---|
| vfolder:file | vfolder 동작이고 subtype 을 유지한다 |
| auth | user/keypair 위의 동작 |
| session:file, commit, log 및 그 밖의 subtype | session 동작이고 subtype 을 분리하지 않는다 |
| stream | 대상은 session 이고 배선 축은 이관 중 확인한다 |
| etcd_config, manager_admin, metric | DB 가 아니며 아래 예외 목록을 참조한다 |
| export, events, resource_overview | scoped data 위의 조회/보고 동작 |

## pass-through 는 결합 base 하나만 상속한다

ops-direct action 은 `<Operation><Shape>OpsAction` 결합 base 하나를 상속하고, 여기서 `operation_type()` 이 따라온다. 선언하는 것은 entity_type / action_name / spec getter (+ 모양의 대상 메서드)뿐이다. 실제 코드 `services/resource_slot/actions/create.py`:

```python
@dataclass(frozen=True)
class CreateResourceSlotTypeAction(CreateGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]):
    creator: ResourceSlotTypeCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType: ...
    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_resource_slot_type"
    @override
    def to_creator(self) -> ResourceSlotTypeCreator:
        return self.creator
```

## 배선은 factory 호출뿐이다

- 전부 pass-through 인 도메인에는 service 가 없다. 실제 코드 `services/app_config_allow_list/processors.py`:

```python
class AppConfigAllowListProcessors:
    def __init__(self, group: ProcessorGroup[AppConfigAllowListData]) -> None:
        self.create = group.global_create_ops(CreateAppConfigAllowListAction)
        self.get = group.single_get_ops(GetAppConfigAllowListAction)
        self.update = group.single_update_ops(UpdateAppConfigAllowListAction)
        self.purge = group.global_purge_ops(PurgeAppConfigAllowListAction)
        self.admin_search = group.global_search_ops(AdminSearchAppConfigAllowListAction)
```

- public global read 는 gate 가 SUPERADMIN 을 인증으로 변경하는 형태이다: `group.public_get_ops(...)` / `group.public_search_ops(...)`.
- service 기반 action 은 service 메서드를 모양 factory 에 전달한다: `group.single_entity(CloneVFolderAction, service.clone)`. 이름으로 ops-direct(`*_ops`)와 구분한다. factory 는 있지만 아직 호출자가 없고, 교체 이슈가 첫 소비자이다.
- 두 search scope: `operation_scopes()` 는 models 계층 statement 에 주입하는 조회 scope 이고, `scope_targets()` 는 RBAC 대상이다. 빈 `operation_scopes()` 는 거부되며 global 로 넓히지 않는다.

## 복잡한 action 도 pass-through 로 내릴 수 있다

service 메서드를 유지하기로 결정하기 전에 이 표를 본다.

| 기존 패턴 | 내리는 도구 | 상태 |
|---|---|---|
| id/name 이중 lookup 분기 | adapter 가 실제 action 전에 lookup action 을 실행한다 | 사용 중 |
| 1~2 줄 검증 (상태 검사, 이름 규칙) | factory 의 `validators=` 추가 인자 | 사용 가능 |
| lifecycle 값을 status 로 접는 것 (순수 함수) | spec 의 `to_data()` / Searcher 의 data 변환 | 사용 가능 |
| 삭제 | `DataUpdater` (status 전이로 취급하고 deleter spec 은 없다) | 사용 가능 |
| 순위 할당 | creator 가 `build_row()` 에서 그 column 에 SQL 식을 넣는다 | 사용 중 |
| parent 와 자식을 함께 생성 | `create_*_with_fields` 가 `FieldCreator` 를 한 transaction 에 넣는다 | 사용 중 |
| 소유자 하나의 field row 읽기 | `FieldProcessorGroup.search_ops` | 사용 중 |

- 순위는 lock 없이 INSERT 안에서 계산한다. 동시 insert 가 같은 값에 놓일 수 있고, 순위가 목록 정렬에만 사용되는 곳에서는 이를 허용한다. 결정적인 순서가 필요하면 lock 을 되돌려야 하는데, 이 표의 어떤 도구도 lock 을 제공하지 않는다. spec 이 무엇을 잠글지 선언해야 한다.
- SQL 식으로 채운 column 은 insert 후 한 번 다시 읽는다. `_insert_rows` 가 row 에서 이를 판단하므로 spec 은 아무것도 선언하지 않는다.

## DB 가 아닌 대상은 ops-direct 후보가 아니다

- DB row 가 없는 대상은 spec 없이 이관한다. service 를 유지하고 action base 만 v2 로 옮긴다.
- v2 이관의 가치는 감사, 지표, gate 가 action 계층에서 한결같이 적용된다는 데 있다.

| 묶음 | 대상 시스템 | 배선 |
|---|---|---|
| etcd_config (6) | etcd | global (SA), 인증된 조회 3개는 public |
| manager_admin (6) | etcd, valkey, socket | global (SA), 이관 중 확인한 익명 상태 조회 3개 |
| stream (7) | agent RPC, valkey | session 대상 action: single_entity(session), 내부 GC 만 global |
| metric (3) | Prometheus | global + public 조회 |
| prometheus_query_preset preview/execute | Prometheus 실행 | service 유지 |
| vfolder file/quota/usage 연산 | storage proxy | service 유지 (vfolder 권한 축) |
| agent watcher (4) | watcher HTTP | service 유지 |
| container_registry quota 등 | Harbor API | service 유지 |
