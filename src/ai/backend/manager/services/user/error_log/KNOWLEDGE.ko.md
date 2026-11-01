# 에러 로그 service: 배경

> 규칙은 `../AGENTS.md`, spec 선택은 `../../models/specs/KNOWLEDGE.md` 에 있다.

이 패키지는 사용자와 컴포넌트가 겪은 에러를 기록하고 누가 다시 조회할 수 있는지 판정한다. 테이블에 사용자가 own 하는 row 와 아무도 own 하지 않는 row 두 종류가 있고 첫 번째만 action 계층을 거치기 때문에 별도 domain 으로 존재한다.

## Processor field

`backend.ai mgr ops list --field error_log` 를 실행하면 연결 및 호출 경로로 처리되는 목록이 출력된다. 그 출력이 엔티티 종류, shape, operation, gate, backing 을 알려 준다.

## 기록은 global 이 아니라 사용자 스코프다

- 에러는 그 에러를 겪은 주체에게 속한다. row 가 사용자 FK 와, 소유자가 읽음 처리하는 `is_cleared` flag 를 갖는다.
- global gate 를 두면 설치 관리자만 자기에게 생긴 문제를 보고할 수 있게 되는데, route 가 선언한 것과 다르다.
- 그래서 `ErrorLogCreator` 는 own 하는 사용자의 스코프를 `member_of` 로 조인하는 `EntityCreator` 이고, 소유자가 없는 row 에서는 비어 있다.

## 조회는 스스로 넓어지는 action 하나가 아니라 action 둘이다

- superadmin 은 테이블 전체를 조회하고 나머지는 자기 스코프 안에서 조회한다. REST handler 가 둘 중 하나를 고른다.
- 둘을 분리해야 각자 자기 gate 를 가질 수 있다. 스스로 넓어지는 action 하나는 좁은 경우로 인가받은 뒤 넓은 결과를 반환해야 한다.

## 읽음 처리는 이 domain 의 소프트 삭제다

- `is_cleared` 가 lifecycle column 이다. row 소유자의 조회는 읽음 처리한 row 를 제외하고 admin 조회는 여전히 반환한다.
- 그래서 `ErrorLogSoftDeleteUpdater` 를 사용하는 `DELETE` 이고, 이 updater 의 `build_values()` 는 상수다. 전이를 인자로 받으면 반대 방향으로 전달될 수 있다.
- 그 시점에는 지정할 row 가 있으므로 action 은 single-entity 다. scope shape 이면 읽음 처리하는 row 가 아니라 호출자 자신의 스코프로 인가하게 된다.

## 인가는 권한 계층으로 옮겼고 row 는 아직 미리 저장하지 않는다

- 소유 여부는 예전에 repository 의 WHERE 절로 강제했고, 지금은 RBAC validator 에 달려 있다.
- `migrate_error_log_data_to_rbac` 이 없으므로 권한 row 가 들어오기 전까지 superadmin 이 아닌 호출자는 거부된다.
- component suite 는 두 상태 모두 볼 수 없다. virtual entity validator 를 mock 으로 대체하므로 그 fixture 가 모든 호출자를 허용한다.
