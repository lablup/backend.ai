# Manager Repositories layer: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 데이터 접근 경로 선택

| 상황 | 경로 |
|---|---|
| 외부 API 를 처리하는 연산 | v2 ops (`V2DBOpsProvider` + `models/specs/` 타입), 우선 |
| 순수 전달 (spec 입력, 데이터 출력, 분기 없음) | ops-generic service 를 거치는 범용 `OpsRepository`, 도메인 repository 를 아예 작성하지 않는다 |
| 복잡한 내부 연산 (다중 테이블, scheduler 내부) | db object(`db_source`) 위의 repository 메서드 |

기본은 첫 번째 row 이다. 연산을 spec 으로 실제로 표현할 수 없을 때만 db object 로 내려가고, 순수 전달만 남으면 repository 를 건너뛴다.

## 연산별로 spec 이 담는 것

| 연산 | spec | 담는 것 |
|---|---|---|
| get | `DataQuerier` | row 클래스, entity id column 과 값, `to_data` |
| | `FieldQuerier` | 위와 같고 field row 자체의 id 로 찾는다 |
| | `OwnedFieldQuerier` | 소유자가 지정한 row 를 소유자로 찾는다 |
| lookup | `DataLookup` | row 클래스, key 조건, `to_data` |
| search | `Searcher` | select, options, `to_data` |
| create | `GlobalEntityCreator` | row 만 |
| | `EntityCreator` | scope 와 membership 도 생성한다 |
| | `RoleManagedEntityCreator` | entity 와 preset 역할 |
| update | `DataUpdater` | row 클래스, pk, 값, `to_data` |
| upsert | `EntityUpserter` | conflict key, scope 는 생성된 상태로 유지한다 |
| purge | `GlobalEntityPurger` | create 와 대칭 |
| | `EntityPurger` | row 와 함께 scope 를 정리한다 |

- create, purge, upsert 메서드는 write 가 무엇을 등록하는지에 따라 나뉜다. 그래서 scoped spec 이 등록이 없는 경로로 흐를 수 없다.
- `delete` 는 없다. 어느 column 이 row 를 삭제로 표시하는지는 도메인 지식이므로, delete action 은 `DataUpdater` 를 가지고 update 경로를 실행한다.
- `OpsRepository` 는 row 가 없으면 `None` 대신 `EntityNotFoundError` / `FieldNotFoundError` 를 반환한다. ops 위에 추가하는 것은 이 경계 하나뿐이다. 에러의 domain 은 spec 이 가진 식별자에서 읽고, key 로 지정한 row 라면 lookup 에서 읽는다.

## ops provider 로의 점진 이관

`ops/v2/provider.py` 의 `V2DBOpsProvider` 가 표준 경로이다. db_source 는 ops 로 점진 이관 중이므로 새 코드와 수정하는 코드에는 ops 를 사용하고, 기존 코드는 손댈 때까지 둔다. raw session 이 호출자에게 노출되지 않도록 engine 을 격리하고, 임의의 SQL 이 계층을 넘지 못하도록 spec 타입만 받는다.

## tx 를 하나의 메서드로 묶는 이유

tx 경계를 명확히 하기 위해 public 메서드에서 session 을 열고 닫는다. 여러 연산을 하나의 service 호출로 묶으면 부분 commit 없이 원자성을 보장한다. 메서드를 작은 조각으로 나누면 호출자가 여러 tx 에 걸쳐 일관성을 잃는다.

## spec 이 테이블 하나만 다루는 이유

spec 안에 다중 테이블 write 를 숨기면 순서와 의존성이 드러나지 않는다. 소유자를 먼저 생성하고 소유된 row 는 소유자의 확정된 id 아래에서 구성된 `FieldCreator` 이므로, parent→child 순서가 명시적이다.

## scope 필터 기본값

`batch_query_with_scopes` 가 RBAC scope 를 강제하기 위한 기본값이다. `batch_query_in_global` 은 필터를 우회하므로 superadmin/internal 경로로 한정하고, 빈 scope 는 `EmptyOperationScopeError` 로 차단한다.
