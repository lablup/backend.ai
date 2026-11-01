# search 필드 선언: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

엔티티마다 손으로 작성하던 조건 함수와 order 메서드를 field 마다 선언 하나로 대체한다. filter, order,
field cap 이 모두 같은 field 목록을 읽는다.

## field 별 선언은 누락을 검사할 수 있게 한다

- 함수 방식에서는 "field" 가 이름 규칙에만 존재해서 빠진 연산이나 order 를 알아채지 못했다. 선언은 filter slot 과 order slot 을 함께 가지므로 field 가 무엇을 지원하는지 선언에 드러난다. mypy 는 `match` + `assert_never` 로 order 를 검사하고, sweep test 는 filter DTO 와 선언이 짝을 이루는지 검사한다.
- `RowDataConverter.to_data` 는 data 생성자를 호출하고 모든 값을 선언의 `read(row)` 로 읽는다. 따라서 선언 없는 data field 는 mypy 에서 실패하고, type 이 어긋나도 실패한다. `row.x` 를 직접 읽는 것은 type 으로 차단할 수 없고 review 가 차단한다.

## 민감한 값은 응답에 없어도 새어 나간다

- filter 는 조건을 만족하는 row 가 있는지를 반환하므로 `starts_with` 를 글자 하나씩 반복하면 값을 복원할 수 있고, order 도 같은 정보를 준다. filter 와 order 가 열려 있는 한 field cap 으로 가려도 의미가 없으므로 cap 은 order 도 검사한다.
- 동등 비교만 남기는 타협은 사용하지 않는다. token 은 후보 집합이 좁아 동등 비교를 반복하면 확인된다. access key 는 응답이 이미 전달하는 식별자이고, 그 자격 증명은 `keypairs.secret_key` 다.
- `endpoint_tokens.token` 은 `SecretColumn` 이 아니라 `sa.String` 이라 type 축이 잡지 못한다. `huggingface_registries.token`, `reservoir_registries.secret_key`, `object_storages.secret_key` 도 같다. `sessions.bootstrap_script` 와 `startup_command` 는 자격 증명을 담을 수 있다. `users.allowed_client_ip` 는 array 라 type 축에도 잡히지만, array 가 아니게 되어도 닫힌 상태를 유지하도록 여기에 둔다.

## type 이 불가능한 것을 정한다

- JSON/JSONB 와 array 는 문서 구조라 크기 비교가 의미 없다. `SecretColumn` 은 암호문을 비교하므로 평문 순서와 무관하고, 동등 비교는 값을 암시한다. 파생 field 는 연산을 걸 column 이 없다.
- `DecimalType` 은 VARCHAR 로 저장되어 `"10" < "9"` 다. cast 를 하면 성립한다. enum 은 성립하지만 알파벳 순서이지 의미 있는 순서가 아니다.

## 비용은 column 종류와 인덱스가 정한다

- 큰 text column 의 부분 일치는 인덱스를 사용하지 못해 전체를 스캔한다. 짧은 문자열은 전체를 스캔해도 행당 비교가 싸다.
- 경계는 1024 하나다. 선언된 길이는 16, 20, 32, 64, 128, 255, 256, 500, 512, 1024 에 몰려 있고 다음은 `16 * 1024` 다. 1024 이하는 이름, 경로, URL, 설명 같은 한 줄 값이며 사용자가 부분 일치로 찾는 대상이다. 그보다 크면 `sa.Text` 나 script 다.
- 256 을 경계로 하면 512 인 `endpoints.name` 과 `model_cards.name` 의 부분 일치가 닫힌다. 구간을 둘로 나누면 257부터 1023까지 규칙이 없어지는데 `groups.description` 도 512 다.
- to-many 집계는 outer row 마다 subquery 를 다시 수행하므로 `ToManyCorrelation` 에 `order` 가 없다. to-one 은 outer row 당 한 row 이므로 열려 있다. 인덱스는 선언과 같은 변경에 함께 넣는다.

## 조건 class 는 filter DTO 를 모른다

- models(`conditions/`, `orders/`, `search/`)는 column 과 SQL 연산을 가진다. adapter base(`BaseFilterAdapter.apply_*_filter`)는 DTO field 를 연산 호출로 변경하는 분기를 가진다. common DTO 는 field 만 가지며 `EnumFilter[E]` 와 `ToManyFilter[F]` 도 logic 을 갖지 않는다.

- 분기는 adapter 에 두어 models 가 API DTO 를 import 하지 않게 한다. 예전에는 DTO, adapter, GQL type 세 곳에 있었고 지금은 adapter 한 곳에 있다. `apply_*_filter` 가 설정되지 않은 field 를 건너뛰고, 연산은 `None` 을 받지 않는다. `None` 을 받으면 값을 반드시 가진 호출자(guard, handler)가 `QueryCondition | None` 과 실행되지 않는 분기를 갖게 된다. `@overload` 로 좁히면 연산마다 선언이 늘어난다.

## own / nested / linked 는 권한이 적용되는 방식으로 나뉜다

- own 은 엔티티 자신의 column 이고 field cap 아래에 있다. nested 는 엔티티가 소유하는 다른 테이블의 row 이고 역시 field cap 아래에 있다(경로 `labels.key`). linked 는 다른 엔티티로의 연결이며 스코프와 상대 엔티티의 권한 아래에 있다.

- 구분은 테이블이 아니라 소유를 따른다. label 은 다른 테이블에 있지만 vfolder 의 데이터다. 진입점이 하나이므로 sweep test 와 권한 검사가 한 곳에서 시작한다. 그 뒤의 class 는 private 이다.

## 다른 테이블의 field 는 펼치지 않고 중첩한다

- 펼친 방식(`label_key`, `label_value`)은 field 마다 EXISTS 하나가 필요해서 key 와 value 가 다른 label 과 일치해도 통과한다. some / every / none 을 표현할 수 없고 경로에 새 이름이 필요하다.
- 중첩 방식(`labels.key`)은 모든 조건에 EXISTS 하나를 써서 같은 label 과 일치해야 한다. `ToManyCorrelation` 이 some / every / none 을 제공하고, 경로는 field cap 및 읽기 경로와 같은 모양이다.

- every 는 `NOT EXISTS(NOT P)` 이므로 child 가 없을 때 참이다(BEP-1060). dangling field(label)는 외래 키 대신 `(entity_type, entity_id)` 로 연결한다는 점만 다르다.

## to-many 는 filter 를 열고 order 는 선언하지 않는다

- some 은 `EXISTS(P)`, every 와 none 은 `NOT EXISTS(NOT P)` 와 `NOT EXISTS(P)` 다. 셋 다 filter 를 열고 order 는 열지 않는다. 집계는 상관 subquery 이며 둘 다 열지 않는다.

- filter 가 열리고 order 가 닫힌 이유는 다르다. some / every / none 은 조건을 만족하는(또는 깨는) 첫 child 에서 멈출 수 있고 planner 가 child 인덱스로 구동되는 semi-join 으로 다시 쓴다. 집계는 child 를 끝까지 읽어야 값이 생기고 그것이 outer row 마다 반복된다.
- 같은 EXISTS 를 order 로 쓰면 결과의 모든 row 에 값을 만들어야 하므로 semi-join 으로 접히지 않는다. filter 는 filter 일 때만 싸다.

## child 조건은 order key 가 되지 않는다

- 요청하는 것은 boolean 이 아니다. "실행 중인 child 가 있는 것부터" 가 아니라 "정상인 것부터, 그다음 문제가 있는 것" 이다. `Endpoint.status`(`api/gql_legacy/endpoint.py`)가 그 요청을 네 술어에서 나온 다섯 값으로 표현하며, boolean order 는 그 순서를 만들지 못한다.
- 지금은 Python 에서 값을 접는다. 답은 부모 column 이다. 그러면 `own` field 가 되어 filter 와 order 가 함께 열리고 인덱스가 접근한다. 이는 schema 변경이라 별도 작업이다. `endpoints.replicas` 는 원하는 개수이지 살아 있는 child 수가 아니다.
- MIN scalar subquery 로 이미 노출된 order 세 개가 금지 대상이다: `UserV2OrderField.PROJECT_NAME`, `ProjectV2OrderField.USER_USERNAME`, `ProjectV2OrderField.USER_EMAIL`(26.2.0). deprecate 로 표시하고 다음 릴리스에서 제거하되 그때까지 동작하게 둔다.

## 다른 서비스는 to-many order 와 relation filter 를 어디까지 여는가

- Hasura 는 집계만, Prisma 는 `_count` 만, Hasura ndc-spec 은 `relationships.order_by_aggregate` 뒤의 `OrderByTarget: aggregate` 를 연다. OData 는 field 경로나 정렬 가능한 함수를 받고 `any` / `all` 은 `$filter` 용으로 둔다. Elasticsearch 는 `mode` 와 다시 선언한 `nested_filter` 를 통해서만 child column 으로 order 한다. GitHub 는 이름 붙은 enum 값 뒤의 미리 계산한 counter 를 연다. 술어로 order 하는 서비스는 없다.

- to-many order 를 연 서비스도 결국 집계로 접는다. 조건을 order key 로 받는 곳은 없으며, Prisma 의 tracker 에도 child column 정렬과 filter 된 개수 정렬 요청만 있고 술어 정렬 요청은 없다. 이 패키지는 집계도 닫고 부모 column 으로 보내며, GitHub 이 counter 를 여는 방식과 같다.
- 다른 엔티티로의 relation 은 식별자까지만 여는 쪽(Stripe, GitHub, Jira: FK id 와 이름, depth 0–1; Kubernetes: 자체 label, depth 0)과 전혀 열지 않는 쪽으로 갈린다. Linear, Prisma, Hasura 는 관련 엔티티의 전체 filter 를 제한 없이 연다. Hasura 의 depth 제한은 selection set 만 센다. API 가 공개적일수록 식별자와 소유 부분에서 멈춘다. 이 패키지는 소유한 것을 모두 열고 field cap 으로 좁히며, 다른 엔티티로의 relation 은 스코프로 표현한다.

## 다른 엔티티로의 중첩 filter 는 열지 않는다

- 중첩 filter 는 EXISTS 안에서 상대 row 의 값을 평가할 뿐 호출자가 그 row 를 읽을 수 있는지 묻지 않는다. 그래서 결과가 호출자가 읽을 수 없는 row 의 값(다른 사용자의 email 등)을 드러낼 수 있다.
- 두 단계 lookup 이나 엔티티 자신의 column 에 복사한 식별자를 사용한다. 열려면 EXISTS 안에 "호출자가 읽을 수 있는 row" 를 더하는 공유 부분이 먼저 필요하다. 같은 이유로 entity share 처럼 자체 권한 type 을 가진 row 는 `nested` 에 두지 않는다.

## Relation 이 아니라 Correlation 이다

- BEP-1075 에서 `Relation` 은 "두 엔티티가 함께 소유하는 link row" 다. 여기의 type 은 상관 subquery 로 다른 테이블의 row 를 찾을 뿐이므로 SQL 용어를 쓴다. `.correlate()` 는 outer SELECT 가 그 테이블을 가질 때만 subquery 의 FROM 에서 제거한다. outer 질의 없이 사용하면 cross join 이 된다.

## usage relation 은 graph 밖에 둔다

- govern 은 "스코프의 역할이 target 이 own 하는 모든 것에 접근한다" 는 뜻이므로, session 을 govern 하는 project 역할은 session 이 마운트한 vfolder 에도 접근한다. own + cap(share)은 엔티티별 권한으로 퍼지지 않지만, 스코프 검색의 도달 범위는 cap 을 무시하므로 목록이 새어 나간다.
- 그래서 usage 는 좁히기만 하고 아무것도 부여하지 않는다. 기준 값은 외래 키 column 하나다.
- column 이 어느 테이블에 있는지는 usage 인지 정하지 않는다. `roles.role_preset_id` 는 검색 대상 row 에 있고 usage 다. JSON 값 안의 id(`extra_mounts`, `vfolder_mounts`)는 외래 키가 아니며 usage 도 아니다. 외래 키를 가진 row 로 정규화한 뒤에 usage 가 된다.

## 호출자가 읽을 수 없는 엔티티를 지정한 조건은 검색을 거부한다

- 스코프는 그 안에서 결과 엔티티를 읽을 권한(govern)으로 검사하고 결과를 OR 로 넓힌다. usage(`used_by`, `uses`)는 지정한 엔티티의 own READ 로 검사하고 AND 로 좁힌다. filter 는 권한을 검사하지 않고 좁힌다.

- 결과는 스코프가 허용한 row 에서만 나오므로 usage 로 접근한 row 도 호출자가 읽을 수 없으면 빠진다. 권한 모델을 가진 검색 API(GitHub `repo:`, GCP Cloud Asset scope)는 호출자가 읽을 수 없는 target 을 거부하며, 이 패키지도 이를 따른다.
- 지정한 엔티티의 권한은 질의 전에 검사하므로 SQL 에는 usage 조건만 들어간다. BA-8024 가 `used_by` 를 스코프 validator 에 병합해 둘을 한 번의 왕복으로 읽는다. global 검색은 지정한 엔티티를 검사하지 않는다. SUPERADMIN gate 가 답한다.
- 두 방향을 한 묶음에 두는 이유는 검사와 좁히기가 같기 때문이고, 방향은 조건이 어느 column 에 걸리는지를 정한다. 일반 column filter 는 권한을 검사하지 않고 읽을 수 없는 row 가 있음을 드러내므로 이를 대신하지 못한다.
- "누가 내 자원을 쓰는가" 는 `uses` 다. session 과 agent 를 잇는 조건을 `used_by` 만으로 보내면 어느 쪽을 원하는지 알 수 없다.

## 스코프와 uses 는 searcher 로 전달된다

- `ScopedSearcher(scopes, used_by, searcher)` 와 `GlobalSearcher(used_by, searcher)` 가 ops 입력이다. `ScopeTarget` 은 검사할 스코프 id 와 row 제한을 가지고, `UsedBy` 는 검사할 엔티티와 그 조건을 가진다. 그래서 검사하는 것과 질의하는 것이 어긋나지 않는다.
- BA-8022 가 `ScopeItem` 을 `OperationScope` 에 병합했다. `RouteHistoryTarget` 은 `ReplicaID`(`FieldIdentifier`)를 key 로 쓰고 소유 deployment 를 지정하려면 target 이 갖지 않은 id 가 필요하므로 `OperationScope` 에 남는다.

## field cap 이 선언에 요구하는 것

- 선언 이름, filter DTO field, data field, cap 경로가 하나의 문자열이라 요청 경로를 변환 없이 cap 경로로 쓴다.
- share 가 field 경로 단위라 가리기는 row 단위다. 그래서 filter 는 `cap AND condition`, order 는 `CASE WHEN cap THEN column END` 가 된다.
- order 도 검사한다. 값은 응답에 없어도 정렬과 반복 filter 로 새어 나간다.

## 검색이 받는 스코프

표는 `models/` 아래 엔티티 패키지마다 검색이 받는 스코프를 적는다. 각 패키지의 이관이 그 row 대로 구현하고
review 가 이를 검사한다.

- 소유 스코프는 모두 받는다. 하나라도 빠지면 그 스코프의 역할은 권한을 가졌는데도 목록을 볼 방법이 없고 superadmin 의 global 검색만 남는다.
- READ 를 부여하는 relation 도 같다. READ cap 아래에서 스코프가 target 을 govern 하게 한다(BEP-1075). field row 는 graph 에 아무것도 보유하지 않으므로 그 스코프는 소유 엔티티다.
- 소유 스코프는 `creators.py` 와 `upserters.py` 의 `created_in` 에서, READ relation 은 `RelationCreator` 선언과 share write 에서, public membership 은 BEP-1077 5.8 에서, 기존 Target 은 `scopes.py` 에서 읽는다. Missing Target 은 그 차이다.
- `global` row 는 `CreatedInGlobal` 로 생성되고 global 읽기는 action 모양을 유지하므로 missing 으로 세지 않는다. domain 은 project 와 user 를 govern 하므로 project 나 user 가 소유한 엔티티도 Domain Target 을 얻는다. 검색이 없는 패키지는 "no search" 라고 적고 검색이 추가되면 받을 스코프를 덧붙인다.

### public 이 스코프인 이유

- public processor 는 호출자의 로그인 여부만 검사하고 row 조건을 더하지 않으며 다른 스코프와 함께 받지 않는다. public 스코프는 public singleton 에서 엔티티 type 에 대한 READ 를 검사하고, row 조건(public 에 등재된 row)을 선언하며 Target 목록에 섞인다.

- public processor 는 권한을 요구하지 않으므로 public 역할에서 READ 를 빼도 읽기가 통과한다. row 조건도 없다. `image` 의 public 읽기 네 개는 public 에 등재되지 않은 registry 의 image 를 반환한다. 스코프로서는 검사와 row 조건이 한 class 에 있다.

### public membership 은 두 종류다

- whole type: type 전체가 public 인 엔티티는 `CreatedInPublic` 이 쓰고 row 조건이 없다. per row: container registry, image, resource preset 은 생성자의 `created_in` 과 스위치 action 이 쓰고 column(`container_registries.is_global`, `resource_presets.scaling_group_name`)을 읽는다.

- 어느 쪽이든 public 이 row 를 own 하고 govern 한다. 차이는 row 조건의 적용 여부다. image 의 row 조건은 속한 registry 의 `is_global` 이다. `is_global` 은 이름을 유지한다. 이름을 변경하면 API 와 migration 이 함께 움직이고, global singleton 을 의미하지 않으므로 code 는 이를 public 이라 한다.
- global 의 모든 엔티티는 하나의 global singleton 에 속하므로 스코프 조건이 걸러 낼 row 가 없다. global 읽기는 action 모양을 유지한다. 권한은 global singleton 에서 type 단위이고, global 용 Target 은 missing 으로 세지 않는다.

### 엔티티, field, relation 스코프 표

Target 이 완전한 패키지는 `scopes.py` 에 선언하고 여기에 row 를 두지 않는다. 아래는 gap 이 있거나 스코프가
자명하지 않은 패키지다.

| 패키지 | 스코프 또는 gap |
|---|---|
| `vfolder` | 개인 폴더는 개인 project 에 있다. share 는 user 와 project 에 접근한다. 공유 ABC `VFolderTarget` 이 missing 이다 |
| `image` | container registry 와 선택적 project. registry 의 `is_global` 로 per row public. `PublicImageTarget` 이 있다 |
| `agent` | resource group. global 검색만 있다. `ResourceGroupAgentTarget`, `DomainAgentTarget`, `ProjectAgentTarget`, `UserAgentTarget` 이 missing 이다 |
| `app_config_fragment` | row 의 소유자(domain, user) 또는 global 과 public. `scope_type='public'` 으로 per row public |
| `entity_share` | offer 가 붙은 엔티티. 받는 쪽은 user 또는 project |
| `rbac_models/role` | 역할이 놓인 스코프. 역할을 가진 user |
| `network`, `session_template` | 검색 없음. `ProjectNetworkTarget`, `DomainNetworkTarget`, `UserSessionTemplateTarget`, `ProjectSessionTemplateTarget`, `DomainSessionTemplateTarget` |
| `session_group` | 모든 Target 이 replica group 이 보유한 group 을 뺀다 |
| `container_registry` | `is_global` 로 per row public. `ProjectContainerRegistryTarget` 과 `PublicContainerRegistryTarget` 이 missing 이다 |
| `resource_preset` | `scaling_group_name` 이 NULL 인 row 로 per row public. `PublicResourcePresetTarget` 이 missing 이고, bound row 를 받는 `ResourceGroupResourcePresetTarget` 이 계획 중이다 |
| `idle_checker`, `resource_policy` | `IdleCheckerAssignmentTarget` binding row 로 접근한다. policy row 는 user 또는 project row 에서 이를 지정하는 column 으로 고른다 |
| `runtime_variant`, `runtime_variant_preset`, `prometheus_query_preset`, `prometheus_query_preset_category`, `resource_slot`(slot type), `login_client_type`, `deployment_revision_preset` | type 전체가 public 이다. 각각의 `Public*Target` 이 missing 이다 |
| `scheduling_history`(route) | deployment. `RouteHistoryTarget` 은 `OperationScope` 에 남는다. replica 를 거쳐 소유 deployment 를 찾는 Target 이 계획 중이다 |
| `session`(dependency), `resource_slot`(allocation), `resource_usage_history`(kernel usage record), `image`(alias), `service_catalog`(endpoint), `deployment_auto_scaling_policy` | 검색 없음. `SessionDependencyTarget` 과 `ImageAliasTarget` 이 계획 중이다 |
| `replica_group`, `vfolder`(user mount policy) | 소유 엔티티의 선언에서 `nested` 로 읽는다 |
| `association_container_registries_groups`, `resource_group` 의 relation row, `agent_installed_image`, `event_log`, `association_artifacts_storages`, `global_entity`, `virtual_entity`, `rbac_models/entity_field` | 두 엔티티의 Target 으로 읽는 관계. creator 가 없음. singleton 과 graph row 는 검색하지 않는다 |

나머지 패키지는 완전한 Target 집합을 `scopes.py` 에 선언한다. `domain` 과 `resource_group` 은 global 이고
linked 스코프로 접근한다. `alembic`, `hasher`, `minilang`, `mixins`, `rbac`, `specs` 는 엔티티 패키지가
아니다.

### public processor 로 연결된 읽기

`services/*/processors.py` 가 public processor 로 연결한 모든 읽기다. public processor 는 호출자의
로그인만 검사하고 권한은 검사하지 않는다. "login only" 는 public 에 등재된 엔티티를 읽지 않는 읽기다.

| 서비스 | 연결 | 읽는 대상 | 옮길 스코프 |
|---|---|---|---|
| `login_client_type`, `prometheus_query_preset`, `prometheus_query_preset_category`, `resource_slot`, `runtime_variant`, `runtime_variant_preset` | `public_*` | type 의 모든 row. 이름에서 id 로 | public(type 전체가 public 에 있다) |
| `image` | `public_get_all_images`, `public_get_image_by_id`, `public_get_image_by_identifier`, `public_get_images_by_canonicals` | `images` 전체. 상태 조건만 | public 과 소유 스코프(`ImageTarget` 목록). public 에 등재되지 않은 registry 의 image 는 legacy GQL 과 REST v1 이 로그인만으로 읽는다 |
| `resource_preset` | `list_presets`, `check_presets`, `lookup` | `resource_presets`. resource group 이 없으면 `scaling_group_name` 이 NULL 인 row | public 과 bound row 의 resource group 스코프(계획) |
| 남은 것 없음 | 없음 | 없음 | `resource_group.get_wsproxy_version` 은 스코프 action 이 되었고 `domain.bulk_get` 은 domain 마다 READ 를 검사하는 읽기로 옮겼다 |
| `agent`, `artifact_registry`, `domain`, `project`, `resource_group`, `session` | `lookup`, `bulk_lookup` | 이름 또는 pair 에서 id 로 | 옮기지 않음. id 만 반환하고 뒤따르는 get 이 값에 대한 권한을 검사한다 |
| `etcd_config`, `metric`, `export`, `permission_contoller` | `public_*` | etcd 설정, valkey metadata, Prometheus metric 이름, code 상수와 연결된 action 목록 | 옮기지 않음. 엔티티가 아니다 |
| `auth` | `public_resolve_access_key_scope` | access key 를 소유한 user 와 그 domain, role | 옮기지 않음. 서비스가 그 user 를 대신해 행동할 수 있는지 직접 정한다 |
