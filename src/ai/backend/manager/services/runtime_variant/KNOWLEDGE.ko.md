# runtime variant service: 배경

> 규칙은 `../AGENTS.md`, spec 선택은 `../../models/specs/KNOWLEDGE.md` 에 있다.

runtime variant 는 배포 리비전이 실행되는 serving runtime 을 지정하는 시스템 전역 catalog 항목이다. 이 패키지는 두 purge 를 위해 있다. 나머지는 모두 ops 에 전달하는 spec 이다.

## Processor field

`backend.ai mgr ops list` 를 실행하면 연결된 목록이 출력된다. 그 출력이 엔티티 종류, shape, operation, gate, backing 을 알려 준다.

## variant 는 global 이고 누구나 조회한다

- `runtime_variants` row 는 어느 스코프에도 속하지 않으므로 row 별로 부여하는 권한이 없고, update 와 purge 의 엔티티 gate 는 superadmin 만 통과한다.
- get, bulk get, search, 이름으로 lookup 하는 모든 조회는 public 으로 연결한다. runtime 을 지정하는 데 권한이 들지 않는다.

## purge 는 service 를 둔다

- variant 는 preset 을 own 하고, 그 preset 이 먼저 삭제된 뒤에야 row 를 삭제한다. `RuntimeVariantPresetsOfVariantPurger` 를 먼저 호출하고 `RuntimeVariantPurger` 를 호출한다.
- 한 트랜잭션에 spec 두 개를 쓰는 것은 여러 테이블에 걸친 쓰기이고 generic ops purge 는 하지 않는다. repository 가 이 쓰기를 하고 service 가 action 의 purger 를 전달한다.

## bulk purge 는 custom backing 을 사용하고 partial 이다

- `bulk_purge` 는 `ProcessorGroup.partial_bulk` 로 실행한다. 항목별 함수가 generic ops purge 가 아니라 앞의 service purge 이기 때문이다.
- shape 는 partial 이다. gate 가 id 마다 판정하고, 거부된 id 나 어떤 row 와도 맞지 않는 id 는 실패 항목 하나가 되며, 실행 자체는 성공한다.
- variant 마다 자기 savepoint 안에서 preset 과 함께 purge 하므로, 하나가 실패해도 나머지는 purge 된 상태로 남는다.
- adapter 는 응답을 그대로 보고한다. purge 된 id 와, purge 되지 않은 id 마다 그 이유다.
