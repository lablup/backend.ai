# search field 선언: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

이 패키지는 엔티티마다 손으로 작성하던 condition 함수와 order 메서드(field 와 operation 마다 하나)를
field 마다 하나의 선언으로 대체한다. filter, order, 권한(field cap)이 모두 같은 field 목록을 읽는다.

## field 마다 선언하면 누락을 검사할 수 있다

- 함수로는 "field" 가 이름 규칙에만 존재했으므로 빠진 operation 이나 order 가 드러나지 않았다.
- 선언은 filter slot 과 order slot 을 함께 가지므로 field 를 filter 하거나 order 할 수 있는지가 선언에
  드러난다.
- mypy 가 `match` + `assert_never` 로 order 를 검사하고, sweep test 가 filter DTO 와 선언이 짝을 이루는지
  검사한다.

## 선언을 통해 row 에서 data 를 만들면 누락이 type 오류가 된다

- test 에서 선언과 data 를 비교하면 test 나 그 test 가 의존하는 등록이 빠질 때 누락을 놓친다.
- `RowDataConverter.to_data` 가 data 생성자를 직접 호출하고 모든 값을 선언의 `read(row)` 로 읽는다.
  선언 없이 data field 를 추가하면 mypy 가 실패한다.
- `read` 는 column 의 값 type 을 반환하므로 선언과 data field 의 type 이 맞는지도 mypy 가 검사한다.
- 선언을 거치지 않고 `row.x` 를 직접 읽는 것은 type 으로 차단할 수 없다. review 가 차단한다.

## 빈 slot 의 이유를 세 축으로 나누는 이유

- 이전 규칙은 type 이 금지하는 것만 나열했다. 동작하지만 의도적으로 제외한 값에는 규칙이 없어 엔티티마다
  작성자가 다시 판단했다.
- 축을 나누면 그 판단이 사라진다. 불가능한 것은 type 이 정하고, 민감함과 비용은 표의 row 와 대조해 정한다.
- 개수를 셋으로 고정하는 것도 규칙이다. 네 번째 이유로 비운 slot 은 그 이유를 어디에도 남기지 않는다.

## 불가능한 것은 type 이 정한다

| column 종류 | 값을 담지 못하는 이유 |
|---|---|
| JSON/JSONB, array | 문서 구조이므로 크기 비교에 의미가 없다 |
| `SecretColumn` | 암호문 비교는 평문 순서와 무관하고, 동등 비교가 값을 암시한다 |
| 파생 field | operation 을 걸 column 이 없다 |
| `DecimalType` | VARCHAR 로 저장되므로 `"10" < "9"` 다. cast 를 하면 담긴다 |
| enum | 담긴다. 알파벳 순서이며 의미 있는 순서는 아니다 |

## 민감한 값은 응답에 없어도 새어 나간다

- filter 는 조건을 만족하는 row 가 있는지 알려 준다. `starts_with` 를 한 글자씩 반복하면 값을 전부
  복원할 수 있다. order 도 같은 정보를 준다.
- 그래서 field cap 뒤에 값을 가려도 filter 와 order 가 열려 있으면 의미가 없다. cap 이 order 도 검사하는
  이유다.
- 절충으로 동등 비교만 여는 방식은 쓰지 않는다. token 은 후보 집합이 좁아 동등 비교를 반복하면 확인된다.
- access key 는 응답이 이미 나르는 식별자이고, 자격 증명은 그 짝인 `keypairs.secret_key`(`SecretColumn`)다.
  응답이 보내는 값은 반복 filter 로 복원할 것이 없으므로 이 축에 속하지 않는다.
- 표의 row 는 조사에서 찾은 사례다. `endpoint_tokens.token` 은 `SecretColumn` 이 아니라 `sa.String` 이라
  type 축이 잡지 못한다. `huggingface_registries.token`, `reservoir_registries.secret_key`,
  `object_storages.secret_key` 도 같은 사례다. `sessions.bootstrap_script` 와 `startup_command` 는
  사용자가 작성한 script 이며 자격 증명을 그대로 담을 수 있다.
- `users.allowed_client_ip` 는 array 라 type 축도 잡는다. array 가 아니게 되어도 닫힌 채로 남도록 민감한
  값으로도 적는다.

## 비용은 column 종류와 인덱스가 정한다

- 큰 text column 의 부분 일치는 인덱스에 접근하지 못하고 full scan 이 되며, search 한 번이 테이블 전체를
  읽는다. 짧은 문자열에는 같은 기준을 적용하지 않는다. full scan 이어도 row 마다 비교가 저렴하다.
- 경계를 1024 하나로 둔 것은 schema 를 세어 나온 값이다. 선언된 길이는 16, 20, 32, 64, 128, 255, 256,
  500, 512, 1024 에 모여 있고 그다음은 `16 * 1024` 다. 1024 이하는 한 줄 값(이름, path, URL, 설명)이며
  사용자가 실제로 부분 일치로 찾는 대상이다. 그보다 큰 것은 `sa.Text` 이거나 script 다.
- 256 에 경계를 두면 512 인 `endpoints.name` 과 `model_cards.name` 의 부분 일치가 닫힌다. 이름 search 를
  닫는 규칙은 비용을 아끼는 것이 아니라 기능을 없앤다.
- 구간을 둘로 나누면 257~1023 에 규칙이 없게 되고, 그 구간에 column 이 실제로 있다(`endpoints.name`,
  `model_cards.name`, `groups.description` 이 모두 512). 그래서 경계는 하나여야 한다.
- to-many 집계는 outer row 마다 subquery 를 다시 실행한다. `ToManyCorrelation` 에 `order` 가 없는 것은
  표현할 수 없어서가 아니라 집계를 열지 않기로 한 결정이다. to-one 은 outer row 마다 row 하나이므로 연다.
- 인덱스는 선언과 같은 변경에 포함한다. 인덱스 없이 연 부분 일치는 부하가 드러날 때까지 남는다.

## condition class 는 filter DTO 를 알지 못한다

| 계층 | 담는 것 |
|---|---|
| models (`conditions/`, `orders/`, `search/`) | column 과 SQL operation |
| adapter base (`BaseFilterAdapter.apply_*_filter`) | DTO field 를 operation 호출로 변경하는 분기 |
| common DTO | field 만. `EnumFilter[E]`, `ToManyFilter[F]` 같은 generic base 도 로직을 담지 않는다 |

- 분기는 adapter 에 있다. models 가 API DTO 를 import 하지 않도록 분기를 adapter 에 둔다.
- 분기는 예전에 세 곳(DTO, adapter, GQL type)에 있었고 지금은 adapter 한 곳에 있다.

## operation 은 None 을 받지 않는다

- `None` 을 받으면 값을 확실히 가진 호출자(guard, handler)까지 `QueryCondition | None` 을 받게 되고,
  실행되지 않는 분기가 늘어난다.
- `@overload` 로 좁히는 방식은 쓰지 않는다. operation 마다 선언이 늘어난다.
- 설정되지 않은 field 를 건너뛰는 일은 `apply_*_filter` 한 곳에서 한다.

## own / nested / linked 는 권한 적용 방식으로 나뉜다

| 구분 | 기준 | 권한 |
|---|---|---|
| own | 엔티티 자신의 column | 엔티티의 field cap |
| nested | 엔티티가 소유하는 다른 테이블의 row | 엔티티의 field cap(path `labels.key`) |
| linked | 다른 엔티티와의 연결 | 스코프, 다른 엔티티의 권한 |

- 나누는 기준은 소유이지 테이블이 아니다. label 은 다른 테이블에 있지만 vfolder 의 data 다.
- 진입점이 하나이므로 sweep test 와 권한 검사가 한 곳에서 시작한다. 뒤의 class 는 이름으로 참조하지
  않으므로 private 이다.

## 다른 테이블의 field 는 펼치지 않고 nested 로 둔다

| | 펼친 경우(`label_key`, `label_value`) | nested(`labels.key`) |
|---|---|---|
| 묶음 | field 마다 EXISTS 하나이므로 key 와 value 가 서로 다른 label 에 맞아도 통과한다 | 조건 전체에 EXISTS 하나이므로 같은 label 에 맞아야 한다 |
| some / every / none | 표현할 수 없다 | `ToManyCorrelation` 이 제공한다 |
| path | 새 이름이 필요하다 | field cap 및 read path 와 같은 모양이다 |

- every 는 `NOT EXISTS(NOT P)` 이므로 child 가 없을 때 참이다(BEP-1060).
- dangling field(label)는 외래 키 대신 `(entity_type, entity_id)` 로 잇는 것만 다르고 같은 to-many 다.

## to-many 는 filter 를 열고 order 를 선언하지 않는다

| 모양 | SQL | filter | order |
|---|---|---|---|
| some | `EXISTS(P)` | 열림 | 열지 않음 |
| every / none | `NOT EXISTS(NOT P)` / `NOT EXISTS(P)` | 열림 | 열지 않음 |
| aggregate | 상관 집계 subquery | 열지 않음 | 열지 않음 |

filter 를 여는 이유와 order 를 열지 않는 이유는 다르다.

- some / every / none 은 조건을 만족하는(또는 깨는) 첫 child 에서 멈출 수 있고, planner 가 child 인덱스로
  구동되는 semi-join 으로 다시 쓸 수 있다. outer row 를 모두 읽지 않는다.
- 집계는 child 를 끝까지 읽어야 값이 생기고, 그것이 outer row 마다 반복된다.
- 같은 EXISTS 를 order 로 쓰면 결과의 모든 row 에 값을 만들어야 하므로 semi-join 으로 접히지 않는다.
  filter 는 filter 일 때만 저렴하다.

## child 조건이 order key 가 되지 않는 이유

- 비용보다 앞서는 것은 실제로 요청받은 값이 boolean 이 아니라는 점이다. 요청은 "실행 중인 child 가 있는
  것을 먼저"가 아니라 "정상인 것을 먼저, 그다음 문제가 있는 것을"이다.
- `Endpoint.status`(`api/gql_legacy/endpoint.py`)가 그 요청을 코드로 옮긴 것이다. child 가 없으면
  DEGRADED, 실행 중인 child 가 없으면 UNHEALTHY, 모두 HEALTHY 면 HEALTHY, 모두 UNHEALTHY 면
  UNHEALTHY, 나머지는 DEGRADED 다. 네 조건으로 다섯 값을 엮는다.
- boolean order 를 열어도 그 순서가 나오지 않는다. 열리는 것이 요청받은 것이 아니므로 열어도 요청은 그대로
  남는다.
- 지금은 child row 를 모두 읽은 뒤 Python 에서 값을 접는다. 답은 order 를 여는 것이 아니라 server 가 값을
  column 으로 두게 한다. 그러면 `own` field 가 되어 filter 와 order 가 함께 열리고 인덱스로 접근할 수 있다.
  그것은 schema 변경이며 별도 작업이다.
- `endpoints.replicas` 는 실행 중인 child 수가 아니라 원하는 수다. 접은 값을 column 으로 올리면 그 이름이
  무엇을 세었는지 말한다.

## 이미 노출된 to-many order 는 deprecation 으로 나간다

| 노출 값 | 구현 | 노출 버전 |
|---|---|---|
| `UserV2OrderField.PROJECT_NAME` | `UserOrders.by_project_name`: `MIN(projects.name)` scalar subquery | 26.2.0 |
| `ProjectV2OrderField.USER_USERNAME` | `ProjectOrders.by_user_username`: `MIN(users.username)` | 26.2.0 |
| `ProjectV2OrderField.USER_EMAIL` | `ProjectOrders.by_user_email`: `MIN(users.email)` | 26.2.0 |

- 셋 다 M:N child 를 `MIN` 으로 접어 order 한다. 금지하는 모양이 정확히 그것이다.
- 규칙을 이들에 맞추어 느슨하게 하지 않는다. 이미 나간 것은 규칙의 반례가 아니라 이전 대상이다.
- 노출된 order field 를 바로 삭제하면 이미 쓰는 client 의 질의가 깨진다. deprecated 로 표시하고 다음
  release 에서 제거하며 그때까지 동작하게 둔다.
- 규칙을 먼저 적는 이유가 이것이다. 규칙이 없으면 네 번째와 다섯 번째가 같은 방식으로 들어온다.

## 다른 service 도 to-many order 를 집계 이상으로 열지 않는다

엔티티가 소유하는 child row 에 대한 내용이다. 다른 엔티티로 들어가는 filter 는 `다른 service 가 관계
filter 를 여는 방식` 에 있다.

| service | to-many order 로 여는 것 | 조건 순서 |
|---|---|---|
| Hasura | 집계만: "array relationships only supporting aggregates for sorting" | 없음 |
| Prisma | `_count` 만 | 없음 |
| Hasura ndc-spec | `OrderByTarget: aggregate`, `relationships.order_by_aggregate` capability 뒤로 분리 | 없음 |
| OData | `$orderby` 는 field path 나 정렬 가능한 함수를 받는다. `any` / `all` lambda 는 `$filter` 용이다 | 없음 |
| Elasticsearch | child column order 를 열지만 `mode`(min/max/avg/sum)와 다시 선언한 `nested_filter` 를 요구한다 | 없음 |
| GitHub | 이름 붙은 enum 값(`STARGAZERS`, `COMMENTS`) 뒤의 미리 센 counter | 없음 |

- to-many order 를 주기로 한 service 도 결국 집계로 접는다. child column 으로 order 하는 사례는
  Elasticsearch 하나이며, 여러 child 를 하나로 접으려고 `mode` 를 요구한다.
- 조건을 order key 로 받는 service 는 어디에도 없다. Prisma 의 tracker 에 child column order 와 filter 된
  count 로 order 하는 요청은 있지만 조건으로 order 하는 요청은 없다.
- 이 패키지는 집계도 닫고 parent column 으로 보낸다. GitHub 가 counter 를 여는 방식이다.

## 다른 엔티티로 들어가는 nested filter 는 열지 않는다. 권한을 검사하는 곳이 없기 때문이다

- validator 는 스코프에 대한 호출자 권한을 미리 검사하지만, nested filter 는 EXISTS 안에서 다른 row 의
  값을 row 마다 평가할 뿐 그 row 를 호출자가 읽을 수 있는지 묻지 않는다.
- 그러면 filter 결과가 호출자가 읽을 수 없는 row 의 값(다른 사용자의 email 등)을 드러낼 수 있다.
- 필요한 경우(관계 엔티티의 상태, 표시 값으로 search, 관계 속성으로 order)에는 두 단계 조회를 쓰거나
  식별자를 엔티티 자신의 column 으로 복사한다.
- 열려면 EXISTS 안에 "호출자가 읽을 수 있는 row" 조건을 더하는 공유 부분이 먼저 필요하다.
- 같은 이유로 entity share 처럼 자체 권한 type 을 가진 row 는 `nested` 가 아니다.

## Relation 이 아니라 Correlation 이다

- BEP-1075 에서 `Relation` 은 "두 엔티티가 함께 소유하는 연결 row" 를 의미한다.
- 여기의 type 은 상관 subquery 로 outer row 와 연결된 다른 테이블의 row 를 찾을 뿐이므로 SQL 용어를
  쓴다.
- `.correlate()` 는 outer SELECT 에 그 테이블이 있을 때만 subquery 의 FROM 에서 제거한다. outer 질의 없이
  쓰면 cross join 이 된다.

## 사용 관계는 graph 밖에 둔다

- govern 은 "스코프의 역할이 target 이 own 하는 모든 것에 접근한다" 이므로 session 을 govern 하는
  프로젝트 역할이 그 session 이 마운트한 vfolder 에 접근하게 된다.
- own + cap(share)은 엔티티별 권한으로 퍼지지 않지만, scoped search 의 접근 범위는 cap 을 무시하므로
  목록이 새어 나간다.
- 그래서 사용은 좁히기만 하고 아무것도 부여하지 않는다. 진실의 원천은 외래 키 column 하나다.
- column 이 어느 테이블에 있는지는 사용인지 결정하지 않는다. `roles.role_preset_id` 는 search 대상 row 에
  있고 사용이다.
- JSON 값 안의 id(`extra_mounts`, `vfolder_mounts`)는 외래 키가 아니고 사용도 아니다. 외래 키를 가진
  row 로 정규화된 뒤에 사용이 된다.

## 호출자가 읽을 수 없는 엔티티를 지정한 조건은 search 를 거부한다

| 입력 | 검사 | 결과에 미치는 영향 |
|---|---|---|
| scope | 스코프 안에서 결과 엔티티를 읽을 권한(govern) | 넓힘(OR) |
| 사용(`used_by`, `uses`) | 조건이 지정한 엔티티를 읽을 권한(own READ) | 좁힘(AND) |
| filter | 없음 | 좁힘 |

- 결과는 스코프가 허용한 row 에서만 나오므로, 사용을 통해 접근한 row 도 호출자가 읽을 수 없으면 제외된다.
- 권한 모델을 가진 search API(GitHub search `repo:`, GCP Cloud Asset scope)는 호출자가 읽을 수 없는
  조건 target 을 거부하고 결과를 호출자가 읽을 수 있는 것으로 제한한다. 이 패키지도 그 방식을 따른다.
- 지정한 엔티티의 권한은 질의 전에 검사하므로 SQL 은 사용 조건만 나른다.
- used_by 는 search 에만 있고 create 같은 다른 scope action 에는 의미가 없어 별도 validator 로
  시작했다. BA-8024 가 이를 scope validator 로 합쳤고, 이제 둘을 한 번의 database 왕복으로 읽는다.
- global search 는 지정한 엔티티를 검사하지 않는다. 스코프 없는 읽기는 SUPERADMIN gate 가 판정한다.
- 두 방향이 하나의 묶음에 있는 것은 검사와 좁힘이 같기 때문이다. 어느 방향이든 지정한 엔티티의 READ 를
  검사하고 결과를 AND 로 좁힌다. 방향이 정하는 것은 조건이 어느 column 에 걸리는지다.
- 일반 column filter 로 이를 대신할 수 없다. 지정한 엔티티의 권한을 검사하지 않으므로 결과가 돌아오는지가
  호출자에게 읽을 수 없는 row 의 존재를 알려 준다.
- "내 resource 를 누가 사용하는가" 는 `uses` 로 답한다. 사용하는 쪽을 search 하고 사용되는 엔티티의 id 로
  좁힌다.
- 방향에 이름을 붙이는 이유는 search 대상 쪽 이름만으로는 어느 쪽이 어느 쪽을 사용하는지 알 수 없기
  때문이다. session 과 agent 를 잇는 조건을 `used_by` 만으로 보내면 agent 를 사용하는 session 을 찾는지
  session 이 사용하는 agent 를 찾는지 알 수 없다. 묶음을 `used_by` 와 `uses` 로 나누면 입력의 path 가
  주어진 id 가 어느 쪽에 속하는지 말한다.
- 검사와 좁힘은 양방향이 같으므로 규칙은 묶음에 한 번 적는다. 실행 경로도 하나다.
  `ScopedSearcher.used_by` 와 `GlobalSearcher.used_by` 가 두 방향의 조건을 받는다.

## scope 와 사용은 searcher 로 전달된다

- `ScopedSearcher(scopes, used_by, searcher)` 와 `GlobalSearcher(used_by, searcher)` 가 ops 입력이다.
  action 은 그 객체 하나를 field 로 받고, 검사는 그로부터 target 을 읽는다.
- `ScopeTarget` 은 검사할 스코프 id 와 row 제한을 갖고, `UsedBy` 는 검사할 엔티티와 그 조건을 갖는다.
  검사하는 것과 질의하는 것이 어긋날 수 없다.
- 이전에는 `ScopeItem` 이 `OperationScope` 를 일대일로 감싸 그 짝을 만들었다. `OperationScope` class
  72개 중 31개에 item 이 없어 권한 target 이 선언되지 않았다. BA-8022 가 모든 wrapper 를 그 scope 에
  합치고 나머지를 옮겨 짝이 하나의 class 가 되었다.
- `RouteHistoryTarget` 은 아직 `OperationScope` 를 쓰는 예외다. `FieldIdentifier` 인 `ReplicaID` 로
  key 를 잡고, replica 는 이를 소유하는 deployment 를 통해 권한을 판정한다. 그 스코프를 지정하려면 소유
  deployment id 가 필요한데 target 은 이를 갖지 않는다.

## field cap 이 선언에 요구하는 것

| 요구 | 이유 |
|---|---|
| 선언 이름 = filter DTO field = data field = cap path | 요청 path 를 변환 없이 cap path 로 쓴다 |
| row 별 masking | share 는 field path 단위이므로 같은 field 도 row 마다 cap 이 다르다. filter 는 `cap AND condition`, order 는 `CASE WHEN cap THEN column END` 가 된다 |
| order 도 검사 | 응답에 없어도 order 와 반복 filter 로 값이 새어 나간다 |

## 다른 service 가 관계 filter 를 여는 방식

| service | 여는 것 | 깊이 |
|---|---|---|
| Stripe, GitHub, Jira | FK id, 이름 같은 식별자 | 0~1 |
| Kubernetes | 자신의 label | 0 |
| Linear, Prisma, Hasura | 관계 엔티티의 전체 filter | 무제한 |
| Hasura 깊이 제한 | selection set 만 세고 filter 조건은 세지 않는다 | 해당 없음 |

- API 가 공개적일수록 식별자와 소유 부분에서 멈춘다.
- 이 패키지는 소유한 모든 것을 열고 field cap 으로 좁히며, 다른 엔티티와의 관계는 스코프로 표현한다.

## search 가 받는 스코프

아래 표는 `models/` 아래 엔티티 package 마다 그 search 가 받는 스코프를 적는다. 각 package 의 migration
이 자기 row 가 적은 것을 구현하고 review 가 그에 맞춰 검사한다.

### 소유 스코프를 모두 받는 이유

- 소유 스코프 하나가 빠지면 그 스코프의 역할은 권한을 가졌는데도 목록을 볼 방법이 없다. 남는 것은
  superadmin 의 global search 뿐이다.
- READ 를 부여하는 relation 도 같다. relation 은 스코프가 대상 READ cap 아래 target 을 govern 하게
  하므로(BEP-1075) 그 스코프의 역할이 target 과 target 이 own 하는 것을 읽는다. 프로젝트가 container
  registry 의 image 를 읽는 방식이다.
- field row 는 graph 에 아무것도 보유하지 않는다. 소유 엔티티가 읽을 수 있는지 판정하므로 그 스코프는
  소유 엔티티다.

### public 이 스코프인 이유

| | public processor | public scope |
|---|---|---|
| 검사 | 호출자가 로그인했는지 | public singleton 의 엔티티 type 에 대한 READ |
| row 조건 | 없음 | Target 이 선언한다(public 에 등록된 row) |
| 다른 스코프와 함께 받기 | 불가 | Target 목록에 섞인다 |

- public processor 는 권한을 요청하지 않으므로 public 역할에서 READ 를 빼도 읽기가 통과한다. row 조건도
  없다. `image` 의 public 읽기 네 개는 public 에 등록되지 않은 registry 의 image 를 반환한다.
- 스코프로 두면 검사하는 것과 row 조건이 한 class 에 있다. 이유는 `scope 와 사용은 searcher 로
  전달된다` 에 있다.

### public 의 두 가지 membership

| 종류 | 적용 대상 | 기록하는 주체 | row 조건 |
|---|---|---|---|
| 전체 type | type 전체가 public 인 엔티티 | `CreatedInPublic` | 없음 |
| row 별 | row 마다 전환되는 엔티티: container registry, image, resource preset | creator 의 `created_in`, 전환 action | column(`container_registries.is_global`, `resource_presets.scaling_group_name`) |

- 어느 쪽이든 public 이 row 를 own 하고 govern 한다. 다른 것은 row 조건이 적용되는지다.
- row 조건의 원천은 column 이다. 복구와 질의 조건이 이를 읽는다(BEP-1077 5.8).
- image 의 row 조건은 자기 column 이 아니라 속한 registry 의 `is_global` 이다.
- `is_global` 은 이름을 유지한다. 이름을 변경하면 API 와 migration 이 함께 움직인다. global singleton 을
  의미하지 않으므로 코드에서는 public 이라고 한다.

### global 읽기가 action 모양을 유지하는 이유

- global 의 모든 엔티티는 global singleton 하나에 속한다. 스코프 조건이 걸러 낼 row 가 없다.
- 권한은 type 단위다. global singleton 의 그 type 에 대한 READ 가 있으면 전부 읽고 없으면 하나도 읽지
  못한다.

### 스코프 표를 읽는 방법

| column | 의미 | 읽는 곳 |
|---|---|---|
| 소유 스코프 | 생성될 때 row 를 own 하고 govern 하는 스코프 | `creators.py` 와 `upserters.py` 의 `created_in` |
| READ relation | 소유는 아니지만 READ 를 부여하는 연결 | `RelationCreator` 선언, share write |
| public | membership: 전체 type / row 별(등록된 row 만) / 해당 없음 | BEP-1077 5.8 의 분류 표, column |
| 기존 Target | `scopes.py` 에 선언된 class | `scopes.py` |
| 빠진 Target | 규칙이 요구하는데 없는 것 | 위 세 column 과의 차이 |

- `global` row 는 `CreatedInGlobal` 로 생성된 row 다. global 읽기는 action 모양을 유지하므로 global 용
  Target 은 빠진 것으로 세지 않는다.
- domain 은 자기 project 와 user 를 govern 한다. project 나 user 가 소유한 엔티티도 pilot(vfolder,
  session, deployment, model card)처럼 Domain Target 을 받는다.
- search 가 아직 없는 package 는 빠진 Target 아래에 "search 없음" 이라고 적고, search 가 추가되면 받을
  스코프를 이어 적는다.

### domain, project, user 또는 다른 엔티티가 소유하는 엔티티

| package | 소유 스코프 | READ relation | public | 기존 Target | 빠진 Target |
|---|---|---|---|---|---|
| `session` | user, project | 없음 | 해당 없음 | `DomainSessionTarget`, `UserSessionTarget`, `ProjectSessionTarget` | 없음 |
| `endpoint`(deployment) | project, user | 없음 | 해당 없음 | `DomainDeploymentTarget`, `ProjectDeploymentTarget`, `UserDeploymentTarget` | 없음 |
| `vfolder` | project(개인 폴더는 개인 project 에 있다) | 공유받은 user 와 project | 해당 없음 | `DomainVFolderTarget`, `ProjectVFolderTarget`, `UserVFolderTarget` | 공유 ABC `VFolderTarget` |
| `model_card` | project, user | 없음 | 해당 없음 | `DomainModelCardTarget`, `UserModelCardTarget`, `ProjectModelCardTarget` | 없음 |
| `image` | container registry, project(선택) | registry 에 연결된 project | membership(row 별, registry 의 `is_global`) | `DomainImageTarget`, `ProjectImageTarget`, `UserImageTarget`, `ContainerRegistryImageTarget`, `PublicImageTarget` | 없음 |
| `project` | domain, global | roster 의 user, 연결된 resource group | 해당 없음 | `DomainProjectTarget`, `UserProjectTarget`, `ResourceGroupProjectTarget` | 없음 |
| `user` | domain, global | 자신이 roster 에 있는 project, role | 해당 없음 | `DomainUserTarget`, `ProjectUserTarget`, `RoleUserTarget` | 없음 |
| `agent` | resource group | resource group 에 연결된 domain, project, user | 해당 없음 | 없음(global search 만) | `ResourceGroupAgentTarget`, `DomainAgentTarget`, `ProjectAgentTarget`, `UserAgentTarget` |
| `app_config_fragment` | row 의 소유자(domain, user) 또는 global 과 public | 없음 | membership(row 별, `scope_type='public'` 인 row) | `AppConfigFragmentTarget`, `VisibleAppConfigFragmentTarget`, `PublicAppConfigFragmentTarget` | 없음 |
| `entity_share` | 제안이 붙은 엔티티 | 받는 user 나 project | 해당 없음 | `RecipientUserEntityShareTarget`, `RecipientProjectEntityShareTarget`, `OwningEntityShareTarget` | 없음 |
| `rbac_models/role` | role 이 놓인 스코프 | role 을 가진 user | 해당 없음 | `ScopedRoleTarget`, `HeldRoleTarget` | 없음 |
| `network` | project | 없음 | 해당 없음 | 없음 | search 없음. `ProjectNetworkTarget`, `DomainNetworkTarget` |
| `session_group` | project, user | 없음 | 해당 없음 | `DomainSessionGroupTarget`, `ProjectSessionGroupTarget`, `UserSessionGroupTarget` | 없음. 모든 Target 이 replica group 이 가진 group 을 제외한다 |
| `session_template` | user, project(선택) | 없음 | 해당 없음 | 없음 | search 없음. `UserSessionTemplateTarget`, `ProjectSessionTemplateTarget`, `DomainSessionTemplateTarget` |

### global 이 소유하는 엔티티

| package | READ relation | public | 기존 Target | 빠진 Target |
|---|---|---|---|---|
| `domain` | 연결된 resource group | 해당 없음 | `ResourceGroupDomainTarget` | 없음 |
| `resource_group` | 연결된 domain, project, user(keypair 를 통해) | 해당 없음. `is_public` 은 숨김 filter column 이며 public membership 과 무관하다 | `DomainResourceGroupTarget`, `ProjectResourceGroupTarget`, `UserResourceGroupTarget` | 없음 |
| `container_registry` | 연결된 project | membership(row 별, `is_global`) | 없음 | `ProjectContainerRegistryTarget`, `PublicContainerRegistryTarget` |
| `resource_preset` | 없음 | membership(row 별, `scaling_group_name` 이 NULL 인 row) | 없음 | `PublicResourcePresetTarget`, 그리고 묶인 row 를 받는 `ResourceGroupResourcePresetTarget`(계획) |
| `idle_checker` | binding 으로 연결된 domain, project, resource group, user, session | 해당 없음 | `IdleCheckerAssignmentTarget`(binding row) | 없음. binding Target 이 스코프에서 checker 에 접근하는 경로다 |
| `resource_policy` | 없음. policy row 는 user row 나 project row 에서 이를 지정하는 column 으로 고른다 | 해당 없음 | `UserKeypairResourcePolicyTarget`, `UserResourcePolicyTarget`, `ProjectResourcePolicyTarget` | 없음 |
| `runtime_variant` | 없음 | membership(전체 type) | 없음 | `PublicRuntimeVariantTarget` |
| `runtime_variant_preset` | 없음 | membership(전체 type) | 없음 | `PublicRuntimeVariantPresetTarget` |
| `prometheus_query_preset` | 없음 | membership(전체 type) | 없음 | `PublicPrometheusQueryPresetTarget` |
| `prometheus_query_preset_category` | 없음 | membership(전체 type) | 없음 | `PublicPrometheusQueryPresetCategoryTarget` |
| `resource_slot`(slot type) | 없음 | membership(전체 type) | 없음 | `PublicResourceSlotTypeTarget` |
| `login_client_type` | 없음 | membership(전체 type) | 없음 | `PublicLoginClientTypeTarget` |
| `deployment_revision_preset` | 없음 | membership(전체 type) | 없음 | `PublicDeploymentPresetTarget` |
| `app_config_allow_list`, `app_config_definition` | 없음 | 해당 없음 | 없음 | 없음 |
| `artifact`, `artifact_registries`, `huggingface_registry`, `reservoir_registry` | 없음 | 해당 없음 | 없음 | 없음 |
| `object_storage`, `vfs_storage`, `storage_namespace` | 없음 | 해당 없음 | 없음 | 없음 |
| `notification`(channel, rule) | 없음 | 해당 없음 | 없음 | 없음 |
| `retention`, `client_ip_masking`, `service_catalog` | 없음 | 해당 없음 | 없음 | 없음 |
| `rbac_models/role_preset` | 없음 | 해당 없음 | 없음 | 없음 |

### 소유 엔티티별 field

| package(row) | 소유 엔티티 | 기존 Target | 빠진 Target |
|---|---|---|---|
| `kernel` | session | `SessionKernelTarget` | 없음 |
| `session`(dependency) | session | 없음 | search 없음. `SessionDependencyTarget` |
| `scheduling_history`(session) | session | `SessionSchedulingHistoryTarget` | 없음 |
| `scheduling_history`(kernel) | session | `SessionKernelHistoryTarget`, `KernelKernelHistoryTarget` | 없음 |
| `scheduling_history`(deployment) | deployment | `DeploymentHistoryTarget` | 없음 |
| `scheduling_history`(route) | deployment | `RouteHistoryTarget`(`OperationScope`) | replica 를 통해 소유 deployment 를 찾아 그에 대해 검사하는 Target(계획) |
| `replica_group_history` | deployment | `DeploymentReplicaGroupHistoryTarget` | 없음 |
| `deployment_revision` | deployment | `DeploymentRevisionTarget` | 없음 |
| `endpoint`(access token) | deployment | `DeploymentAccessTokenTarget` | 없음 |
| `routing`(replica) | deployment | `DeploymentReplicaTarget` | 없음 |
| `replica_group` | deployment | 없음(deployment 선언에서 `nested` 로 읽는다) | 없음 |
| `deployment_policy` | deployment | `DeploymentPolicyTarget` | 없음 |
| `deployment_auto_scaling_policy` | deployment | 없음 | search 없음 |
| `keypair` | user | `UserKeypairTarget` | 없음 |
| `login_session`(session, history) | user | `MyLoginSessionTarget`, `MyLoginHistoryTarget` | 없음 |
| `error_log` | user | `UserErrorLogTarget` | 없음 |
| `image`(alias) | image | 없음 | search 없음. `ImageAliasTarget` |
| `model_card`(resource requirement) | model card | `ModelCardResourceRequirementTarget` | 없음 |
| `vfolder`(user mount policy) | vfolder | 없음(vfolder 선언에서 `nested` 로 읽는다) | 없음 |
| `artifact_revision` | artifact | `ArtifactRevisionTarget` | 없음 |
| `deployment_revision_preset`(slot) | deployment preset | `DeploymentPresetSlotTarget` | 없음 |
| `service_catalog`(endpoint) | service catalog | 없음 | search 없음 |
| `resource_slot`(agent resource) | agent | `AgentResourceTarget` | 없음 |
| `resource_slot`(allocation) | kernel 을 통해 session | 없음 | search 없음 |
| `resource_usage_history`(kernel usage record) | kernel 을 통해 session | 없음 | search 없음 |
| `resource_usage_history`(usage bucket) | resource group | `DomainUsageBucketTarget`, `ProjectUsageBucketTarget`, `UserUsageBucketTarget`(resource group 에 대해 검사) | 없음 |
| `fair_share` | resource group | `DomainFairShareTarget`, `ProjectFairShareTarget`, `UserFairShareTarget`(resource group 에 대해 검사) | 없음 |
| `entity_label` | label 이 붙은 엔티티 | `EntityLabelTarget` | 없음 |
| `audit_log` | 기록이 지정한 엔티티. 아무것도 지정하지 않은 기록은 global 에 있다 | `EntityAuditLogTarget`, `ScopeAuditLogTarget`, `TriggeredByAuditLogTarget` | 없음 |
| `rbac_models/permission` | role | `RolePermissionTarget` | 없음 |
| `rbac_models/role_permission_preset` | role preset | `RolePresetPermissionTarget` | 없음 |

### relation row 와 나머지

| package | 무엇인가 | search |
|---|---|---|
| `association_container_registries_groups` | project 와 container registry 의 relation | 두 엔티티의 Target 으로 읽는다 |
| `resource_group`(for-domain, for-project, for-keypair row) | 스코프와 resource group 의 relation | 두 엔티티의 Target 으로 읽는다 |
| `idle_checker`(binding, session idle check) | 스코프와 idle checker, session 과 idle checker 의 relation | `IdleCheckerAssignmentTarget` |
| `rbac_models/user_role` | role 과 user 의 relation | `UserRoleAssignmentTarget`, `RoleRoleAssignmentTarget` |
| `association_artifacts_storages` | artifact 와 storage 를 잇는 row. graph relation 으로 쓰지 않는다 | 없음 |
| `agent_installed_image`, `event_log` | creator 가 없다 | 없음 |
| `global_entity`, `virtual_entity`, `rbac_models/entity_field` | singleton row 와 graph row | search 하지 않는다 |
| `alembic`, `hasher`, `minilang`, `mixins`, `rbac`, `specs` | 엔티티 package 가 아니다 | 없음 |

### public processor 로 처리하는 읽기

`services/*/processors.py` 가 public processor 로 처리하는 모든 읽기다. public processor 는 호출자가
로그인했는지만 검사하고 public singleton 의 권한은 검사하지 않는다(`actions/registry/group.py`).

"login 만" 은 public 에 등록된 엔티티를 읽지 않는 읽기다.

#### public 에 등록된 엔티티를 읽는 경우

| service | 연결 | 읽는 것 | 옮길 스코프 | 이유 |
|---|---|---|---|---|
| `login_client_type` | `public_get`, `public_search` | `login_client_types` 전체 | public | type 전체가 public 에 있다 |
| `prometheus_query_preset` | `public_get_preset`, `public_search_presets` | `prometheus_query_presets` 전체 | public | 같다 |
| `prometheus_query_preset_category` | `public_get_category`, `public_bulk_get_categories`, `public_search_categories` | `prometheus_query_preset_categories` 전체 | public | 같다 |
| `resource_slot` | `public_get_resource_slot_type`, `public_search_resource_slot_types`, `public_lookup_resource_slot_type` | `resource_slot_types` 전체, 이름에서 id 로 | public | 같다 |
| `runtime_variant` | `public_get`, `public_bulk_get`, `public_search`, `public_lookup` | `runtime_variants` 전체, 이름에서 id 로 | public | 같다 |
| `runtime_variant_preset` | `public_get`, `public_search` | `runtime_variant_presets` 전체 | public | 같다 |
| `image` | `public_get_all_images`, `public_get_image_by_id`, `public_get_image_by_identifier`, `public_get_images_by_canonicals` | `images` 전체. status 조건만 보고 registry 의 `is_global` 이나 소유는 보지 않는다 | public 과 소유 스코프(`ImageTarget` 목록) | public 에 등록되지 않은 registry 의 image 를 login 만으로 읽는다. legacy GQL 과 REST v1 이 호출한다 |
| `resource_preset` | `list_presets`, `check_presets`, `lookup` | `resource_presets`. resource group 이 없으면 `scaling_group_name` 이 NULL 인 row, 있으면 그 row 도 함께. `list_presets` 와 `lookup` 은 주어진 resource group 의 권한을 검사하지 않는다 | public, 묶인 row 는 그 resource group 의 스코프(계획) | NULL row 는 public 에, 묶인 row 는 그 resource group 에 있다 |

#### 소유 스코프에 속하는 읽기

남은 것이 없다. `resource_group.get_wsproxy_version` 은 `ResourceGroupTarget` 목록을 받는 scope action 이
되었고, `domain.bulk_get` 은 domain 마다 READ 를 검사하는 읽기로 옮겼다.

#### login 만 하는 경우

| service | 연결 | 읽는 것 | 옮길 스코프 | 이유 |
|---|---|---|---|---|
| `agent` | `lookup`, `bulk_lookup` | `agents` 의 이름에서 id 로 | 옮기지 않음 | id 만 반환한다. 뒤따르는 get 이 값에 대한 권한을 검사한다 |
| `artifact_registry` | `lookup` | `artifact_registries` 의 이름에서 id 로 | 옮기지 않음 | 같다 |
| `domain` | `lookup`, `bulk_lookup` | `domains` 의 이름에서 id 로 | 옮기지 않음 | 같다 |
| `project` | `lookup` | `groups` 의 (domain 이름, 이름) 짝에서 id 로 | 옮기지 않음 | 같다 |
| `resource_group` | `lookup`, `bulk_lookup` | `scaling_groups` 의 이름에서 id 로 | 옮기지 않음 | 같다 |
| `session` | `lookup` | `sessions` 의 (user, 이름, 종료되지 않은 status)에서 id 로 | 옮기지 않음 | 같다. handler 가 user 를 정한다 |
| `etcd_config` | `get_resource_slots`, `get_resource_metadata`, `get_vfolder_types` | etcd 설정, valkey 의 device metadata | 옮기지 않음 | 엔티티가 아니다 |
| `metric` | `metadata_public_search` | Prometheus 의 container metric 이름 | 옮기지 않음 | 엔티티가 아니다 |
| `export` | `public_get_report` | 코드에 등록된 report 정의. export 질의는 따로 권한을 검사한다 | 옮기지 않음 | 엔티티가 아니다 |
