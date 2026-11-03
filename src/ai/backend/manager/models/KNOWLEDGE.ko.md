# Manager models: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

DB schema 의 선언 계층이다. 도메인별 패키지(`models/{domain}/row.py`)가 테이블 구조를 담고 `models/specs/` 가 write 선언을 담는다. 이 문서는 이 패키지가 "선언만 두고 구현은 두지 않는" 이유를 다룬다.

## Row 는 선언이고 구현을 담지 않는다

- Row 는 테이블 구조의 선언이다. query builder 나 business method 가 붙는 순간 session 과 transaction 경계 밖에서 호출되는 로직이 생기고 계층이 무너진다.
- 도메인별 패키지 분리는 schema 변경의 영향 범위를 그 도메인으로 좁힌다.
- `session/row.py` 의 legacy query method 는 남은 반례일 뿐 본받을 대상이 아니다.

## 객체 조작은 spec 을 거친다

- 생성, 삭제, upsert 는 가능한 한 `models/specs/` 의 spec 선언으로 처리한다. db 객체를 직접 조작하는 것보다 우선한다.
- 이유: RBAC 부수 효과(scope 프로비저닝, 멤버십 등록)는 **spec 의 타입**이 결정한다. Row 를 직접 삽입하면 그 부수 효과를 조용히 건너뛴다([specs/KNOWLEDGE.md](specs/KNOWLEDGE.md)).

## session 으로 model 을 직접 조작하지 않는다

- db session 을 열어 Row 를 직접 조작하는 코드를 피한다. 구현은 repository 에 속한다.
- 첫 번째 이유: transaction 경계는 repository 의 책임이므로 흩어진 직접 session 은 원자성 보장을 깬다.
- 두 번째 이유: 직접 session 은 Row 가 repository 위 계층으로 새는 통로가 된다. Row 가 `repositories/` 위로 올라가지 않는다는 계층 규칙을 우회한다.

## 모든 id 기본값이 v7 인 이유

- UUIDv7 의 앞 60 bit 는 생성 시각이므로 새 row 의 id 가 v4 처럼 primary key index 전체에 흩어지는 대신 그 index 의 오른쪽 끝에 놓인다. 결과가 둘이다. insert 는 항상 이미 cache 된 page 하나만 접근하고, 최근 row 를 읽을 때 hot index page 가 몇 개로 유지된다. heap page 배치는 insert 순서가 결정하므로 이 이득에 포함되지 않는다.
- 이득의 크기는 index 가 cache 를 얼마나 넘는지와 그 테이블에 기록이 얼마나 잦은지의 곱이다. row 가 수천 개인 테이블에서는 index 전체가 memory 에 남아 차이가 측정되지 않고, 수백만 개인 테이블에서는 random disk read 로 바로 드러난다.
- 모든 테이블에 generator 하나를 사용한다. 테이블마다 다르게 두면 다음 사람이 다시 판단해야 한다.
- v7 은 id 를 가진 쪽에 생성 시각을 알린다. 이 schema 에서는 id 를 볼 수 있으면 그 row 의 `created_at` 도 볼 수 있으므로 새로 새는 정보가 없다.
- 62 bit 가 무작위다. 앞 48 bit 는 millisecond timestamp 이고 다음 12 bit 는 sub-millisecond tick 이며 나머지가 남는다. v4 의 122 bit 보다 적으므로 추측할 수 없어야 하는 값은 id 가 아니라 자기 column 에 둔다.
- v4 와 v7 은 모두 `uuid` 타입이므로 한 column 에 섞여 있을 수 있다. 기존 row 를 다시 기록할 필요는 없다.
- 함수는 한 session 안에서 엄격히 증가한다. 마지막으로 반환한 값을 session setting 에 기억하고 시계가 나아가지 않았으면 가장 작은 단위만큼 올린다. PostgreSQL 18 의 내장 `uuidv7()` 과 같으며, 18 이 최소 version 이 되면 본문이 `RETURN uuidv7();` 이 된다.
- session 상태를 변경하므로 parallel safe 로 표시하지 않는다.

## creator column 과 남는 row

BEP-1077 이후 소유권은 `scope -> virtual_entity -> entity` 경로만으로 판정한다. 그래서 어느 row 도 `owner_*` column 을 갖지 않는다. 같은 질문에 응답이 둘로 남고, 그것이 BEP 가 없애려던 상태다.

`creator_id` 는 다른 질문에 응답한다. **이 row 가 어느 사용자를 위해 생겼는지**다. 소유권이 아니라 출처이므로 접근 판정에 참여하지 않는다. 이 구분은 개인 project 때문에 필요하다. 개인 project 는 사용자와 함께 생성되므로 "이 사용자의 project 는 무엇인가"에 응답할 값이 필요하고, 그래프에서 읽으면 소유권 질문에 조회 멤버십으로 응답하게 된다. 그 멤버 목록도 share 로 다시 기록할 예정이라 모양이 바뀌지만 column 은 바뀌지 않는다.

### 사용자가 사라진 뒤

foreign key 는 `ON DELETE SET NULL` 이다. 사용자를 영구 삭제해도 project 는 가져가지 않는다.

- project 가 보유한 것은 계정보다 오래 남는다. 사용자 row 를 삭제하는 같은 transaction 에서 개인 vfolder 를 삭제하면 데이터를 전달할 방법이 없다.
- project 삭제는 그 안의 자원을 정리하는 일이고 비동기 작업이다. 동기 purge transaction 에 속하지 않는다.
- 그래서 creator 가 NULL 인 개인 project 는 **dangling** 이고 retention sweep 이 수집한다. project 도 함께 없애려는 삭제 요청은 API option 으로 이를 알리고, 삭제 자체는 비동기로 남는다.

일반 project 에서 `creator_id` 는 단순한 audit 정보이고 비어 있어도 의미가 없다. 그래서 이 key 가 `RESTRICT` 가 아니다. 오래전 누군가가 생성한 팀 project 가 그 사용자의 purge 를 방해해서는 안 된다.

### 개수

사용자는 개인 project 를 최대 하나 가지며 partial unique index 가 이를 보장한다. dangling project 는 NULL 을 가지며 unique index 에서 NULL 은 충돌하지 않으므로 여러 개가 공존한다.

## scope 가 조건을 읽는 곳

`OperationScope` 가 경계를 정하는 row 는 세 가지 모양 중 하나다. 어느 모양인지가 조건이 무엇을 읽을 수 있는지 결정한다.

| 모양 | 구분 방법 | 조건 |
|---|---|---|
| 엔티티 | row 의 id class 가 `EntityIdentifier` 이고 자기 `EntityType` 을 반환한다 | govern edge 와 own edge 에 대한 상관 EXISTS |
| 필드 | `FieldType.owner_type()` 이 엔티티 종류를 반환한다 | owner column 에 대한 동등 비교, 또는 그 owner 에 대한 edge EXISTS |
| Dangling field | `FieldType.owner_type()` 이 `None` 이다 | row 에 적힌 `(entity_type, entity_id)` 짝에 대한 동등 비교 |

### scope 는 권한을 부여하지 않는다

action 의 scope 검사나 bulk 검사가 먼저 실행된다. scope 는 그 검사가 이미 허용한 범위를 좁힌다. 따라서 scope 조건 안의 role 분기나 권한 판정은 한 질문에 판정을 둘로 남긴다.

아무것도 경계로 두지 않는 읽기는 빈 scope 목록으로 기록하지 않는다. global 읽기에는 선언된 위치가 있고 빈 목록은 거부된다. 여러 scope 가 함께 오면 그 조건을 OR 로 잇는다.

### 소유자는 값에서, 멤버십은 edge 에서 읽는다

field row 와 dangling field row 는 그래프에 node 를 갖지 않으므로 누가 소유자인지는 row 의 값에서 읽는다. 그 소유자가 호출자가 지정한 scope 에 속하는지는 edge 에서 읽는다. 두 hop 이 이렇게 나뉜다.

field scope 는 소유자 자체와 그 위의 scope 를 함께 받는다. 지정한 scope 가 소유 엔티티이면 조건은 owner column 의 동등 비교이고, 그 소유자 위이면 같은 column 에 대한 edge EXISTS 다. 어떤 종류가 어떤 축을 받는지는 종류마다 선언하며 아무 scope 에나 열려 있지 않다.

### scope 가 도달하는 경로는 edge 둘이다

`entity_memberships` 는 어느 virtual entity 가 row 를 보유하는지 알리고, `scope_bindings` 는 어느 scope 가 virtual entity 를 govern 하는지 알린다. 권한 검사는 둘을 모두 거치므로 첫째만 거치는 scope predicate 는 호출자가 볼 수 있는 것보다 적게 찾는다. domain 은 자기 project 가 보유한 row 를 모두 놓친다. 모든 node 는 자기 자신을 govern 하는 edge 를 가지므로 row 자체를 보유한 scope 도 같은 범위로 응답한다.

membership edge 는 소속과 share 를 구분하지 않고 응답한다. share 를 거쳐 도달한 대상으로 무엇을 할 수 있는지는 그 edge 의 cap 이 제한하므로 scope 가 둘을 구분할 이유가 없다. 반대로 scope 에서 share 를 제외하면 공유된 row 가 조회에서 제외되고, 이는 scope 가 내릴 판단이 아니다.

### 권한을 요구하지 않는 축

대부분의 축은 호출자를 먼저 검사할 scope 를 지정한다. 모두에게 보이는 것을 읽는 축은 검사할 대상이 없다. 그런 축은 `scope_targets()` 에서 제외되고 `operation_scopes()` 에만 추가된다. gate 가 적용되는 것은 `scope_targets()` 뿐이므로 gate 없는 축을 표현할 수 있다.

`image` 의 `global` 축이 그렇다. image 가 global 인지는 image row 가 아니라 그 image 가 붙은 container registry 의 `is_global` 이 결정한다. 그 column 은 nullable 이고 값을 두지 않은 registry 는 global 이 아니다.

### `existence_checks`

scope 가 지정한 엔티티의 존재를 검증한다. 모든 scope 의 모든 검사는 본 질의 앞에서 하나의 질의로 합쳐진다.

권한 검사가 이미 존재를 판정한 곳에서는 비워 둔다. 인증된 요청자 자신을 지정하는 scope 와, bulk 검사가 이미 도달 가능성을 판정한 dangling field 가 그렇다. 빈 값은 무엇이 대신 응답했는지 한 문장으로 알린다.
