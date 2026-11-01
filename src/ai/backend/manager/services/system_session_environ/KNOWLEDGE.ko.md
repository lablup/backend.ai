# 시스템 세션 environ service: 배경

> 규칙은 `../AGENTS.md`, 연결은 `backend.ai mgr ops list` 로 확인한다.

system session environ row 는 시작하는 세션의 값을 public 스코프, 도메인, 프로젝트에서 환경 변수 이름에 묶는다. launcher 는 domain repository 를 통해 row 를 읽고, 이 패키지는 호출자가 API 로 도달하는 operation 을 담는다.

## Processor field

| 필드 | 실패 모드 | 인가 기준 |
|---|---|---|
| `global_search` | 한 번 실행 | 엔티티 종류별 `global` singleton |
| `public_list_value_sources` | 한 번 실행 | 인증만 |
| `scoped_search` | 한 번 실행 | 지목한 모든 스코프: public, 도메인, 프로젝트 |
| `create` | 한 번 실행 | row 를 생성하는 스코프 |
| `update` | row 하나 | 지목한 row |
| `delete` | row 하나 | 지목한 row |
| `restore` | row 하나 | 지목한 row |
| `purge` | row 하나 | 지목한 row |
| `bulk_get_ids` | partial bulk | 지목한 row 각각 |

## value source 목록과 create 만 service method 를 둔다

- 다른 row operation 은 generic ops service 에 spec 을 전달하고 row 를 변환하므로 `service.py` method 를 갖지 않는다.
- value source 목록은 row 를 조회하지 않으므로 ops 가 backing 이 될 수 없다. `SystemSessionEnvironService` 가 이 operation 을 처리한다.
- create 의 spec 은 전제 조건을 담는데 generic create 는 이를 받지 않는다. service 가 이를 domain repository 에 전달한다.
- 세션이 받는 row, 즉 key 마다 가장 구체적인 스코프의 row 를 정하는 일은 여러 row 에 걸친 분기다. 그 조회는 ops 가 아니라 launcher 가 호출하는 domain repository 에 남는다.

## admin 조회는 global 이다

- 모든 스코프의 모든 row 를 삭제로 표시된 것까지 조회하므로 검사할 스코프를 지목하지 않는다.
- global gate 는 superadmin 과, 조회에 한해 monitor 를 통과시킨다.

## scoped search 는 스코프별이다

- 호출자는 public, 도메인, 프로젝트를 지목하고, 그중 어느 것의 row 든 삭제로 표시된 것까지 조회한다. 조회 전에 지목한 모든 스코프를 검사하므로 호출자가 조회할 수 없는 스코프가 하나라도 있으면 search 전체를 거부한다.
- 도메인 스코프는 도메인 자체에 묶인 row 를 조회한다. graph 는 프로젝트의 node 를 그 도메인 아래에 묶으므로, target 이 프로젝트의 row 를 빼기 위해 scope type column 도 함께 맞춘다.

## value source 목록은 public 이다

- value source 는 manager 자체의 목록이고 row 가 아니므로 row 권한이 적용되지 않는다. `public` 으로 연결하고, 이 shape 은 호출자가 로그인했는지만 검사한다.
- API 는 value source 를 enum 이 아니라 이름으로 전달하므로 value source 가 늘어도 schema 가 바뀌지 않는다. adapter 는 manager 가 제공하지 않는 이름을 거부한다.

## create 는 그 스코프를 기준으로 인가한다

- row 를 생성하는 스코프를 받는다. public 엔티티, 도메인, 프로젝트다. 그곳의 CREATE 부여가 판정한다. 프로젝트 관리자는 그 프로젝트, 도메인 관리자는 그 도메인과 프로젝트, superadmin 은 public 을 포함한 모든 스코프다.
- `scope_id` 에는 foreign key 가 없으므로, 없는 도메인이나 프로젝트는 쓰기가 graph 에 node 를 요청하기 전에 거부한다.
- public row 는 `global` 과 `public` 스코프에서, 도메인이나 프로젝트의 row 는 그 소유자에서 생성한다. seed 로 미리 저장한 row 와 같다.
- database 는 같은 스코프의 다른 row 가 가진 key 를, 삭제로 표시된 row 가 가진 key 까지 포함해 거부하고, 환경 변수 이름이 아닌 key 도 거부한다.

## purge 는 row 별이다

- 삭제 표시 여부와 관계없이 row 를 가상 엔티티, 그 row 를 지목하는 모든 edge 와 함께 삭제한다. 그 row 의 HARD_DELETE 부여가 판정하고, UPDATE 와 같은 관리자가 가진다.
- purge 한 row 의 key 는 그 스코프에서 다시 비어 있다.

## update 는 row 별이다

- key 만 변경한다. 스코프와 value source 는 고정이다. row 를 다른 스코프로 옮기면 graph 에서의 소속도 옮겨지기 때문이다.
- 그 row 의 UPDATE 부여가 판정한다. 프로젝트 관리자는 그 프로젝트의 row, 도메인 관리자는 그 도메인의 row 와, graph 가 프로젝트를 그 도메인 아래에 묶으므로 그 프로젝트의 row, superadmin 은 모든 row 다. public row 에 UPDATE 를 가진 다른 이는 없다.
- database 는 같은 스코프의 다른 row 가 가진 key 와 환경 변수 이름이 아닌 key 를 거부한다. updater 가 둘 다를 domain 에러로 매핑한다.
- 삭제로 표시된 row 는 거부한다. 먼저 복원한다.

## 삭제와 복원은 row 별이다

- 공유 삭제 표시 updater 로 `deleted_at` 을 기록한다. launcher 가 삭제로 표시된 row 를 제외하므로 삭제 후 시작한 세션은 그 row 를 받지 않는다.
- 그 row 의 SOFT_DELETE 부여가 둘 다를 판정하고, UPDATE 와 같은 관리자가 가진다.
- 삭제로 표시된 row 는 key 를 유지한다. 삭제된 row 를 purge 할 때까지 같은 스코프의 다른 row 가 그 key 를 가져가지 않으므로 key 때문에 restore 가 거부되는 일은 없다.
- seed 는 같은 key 로 upsert 하고 삭제로 표시된 row 도 포함한다. 삭제 후에는 그 key 를 건너뛴다. overwrite 는 삭제된 row 의 value source 를 다시 쓰고 삭제 상태로 둔다.

## id 로 하는 조회는 partial 이다

- `node(id:)` 뒤의 GQL DataLoader 에 값을 제공하고, 한 batch 에 여러 resolver 의 id 가 섞인다. 호출자가 조회할 수 없는 row 만 실패한다.
- row 마다 graph 에서 검사한다. 모든 사용자는 public row 를, 도메인이나 프로젝트의 관리자는 그 row 를, 도메인 관리자는 그 프로젝트의 row 도 조회한다.
- 도메인 멤버와 프로젝트 멤버 프리셋은 READ 를 갖지 않는다. graph 가 프로젝트를 그 도메인 아래에 묶으므로 도메인 멤버의 READ 는 도메인의 모든 프로젝트에 통과하게 된다.
