# 권한 controller service: 배경

> 규칙: `../AGENTS.md`. Spec 선택: `../../models/specs/KNOWLEDGE.md`.

역할과 역할이 가진 권한 프리셋을 다룬다. 역할이 엔티티이고 권한 프리셋은 역할의 field
row 이다. 역할 그룹 하나가 연결되며, 권한 프리셋에 대한 연산은 그 그룹이 제공하는 field
하위 그룹에서 온다.

## processor fields

`backend.ai mgr ops list --concern rbac` 는 연결된 목록을 출력한다. 그 출력이 엔티티
타입, 모양, 연산, gate, backing 을 나타낸다.

## 역할은 두 모양으로 생성한다

- 스코프에서 생성하는 역할은 `CreateRoleAction` 이다. scope 모양이므로 역할에 대한 CREATE
  를 모든 스코프에서 검사하고, 각 스코프가 새 역할을 own 하고 govern 한다.
- 스코프 없이 생성하는 역할은 `CreateGlobalRoleAction` 이다. global 모양이므로 gate 는
  SUPERADMIN 이다.
- 모양이 둘인 이유는 `scope_targets()` 가 비어 있으면 scope validator 가 아무것도 검사하지
  않기 때문이다. 스코프 없는 요청을 scope action 으로 처리하면 gate 가 열린 채로 남는다.
- 역할은 가상 엔티티 그래프에 등록된다. 스코프의 역할이 기록되는 곳은 여기뿐이다(BA-7796, 역할 등록을 그래프로 옮긴 작업).
- 사용자에게 역할을 부여하고 회수하는 일은 여기에 없다. 둘 다 역할 row 옆에 roster 항목을
  기록하므로, 그래프에 기록하는 다른 연산과 함께 `../rbac` 에 있다.

## 역할 변경은 guard 가 붙은 단일 엔티티 연산이다

- 변경, 소프트 삭제, 복원은 `single_*_ops` 이고 purge 는 `entity_purge_ops` 이다.
- 각각 역할별로 처리하는 partial bulk 대응 연산(`partial_bulk_{update,delete,restore}_ops`,
  `entity_partial_bulk_purge_ops`)이 있다.
- SYSTEM 역할은 변경, 소프트 삭제, purge 에서 spec 의 guard 가 거부한다. SYSTEM 역할은 역할
  프리셋을 통해 변경한다.

## 권한 프리셋은 역할의 field row 이다

- 권한 프리셋은 `ondelete=CASCADE` 인 역할 외래 키(FK)를 가지며 스스로 권한을 부여하지는 않는다.
- 권한 프리셋을 추가하거나 제거하는 것은 역할의 변경이므로 `UPDATE` 로 기록되고 역할의
  UPDATE 권한이 이를 판정한다. 이전 연결에는 gate 가 없었다.
- `AddRolePermissionAction` 은 역할 id 와 권한 프리셋 하나를 받는다. 아직 지정할 row 가
  없다.
- `BulkRemoveRolePermissionsAction` 은 권한 프리셋 id 만 받는다. lookup 이 각각 어느
  역할에 속하는지 판정하고, 여러 역할에 걸친 권한 프리셋은 역할별로 검사한다. 응답은 권한
  프리셋 단위이고 기록은 역할 단위다.
- API 계약은 알 수 없는 id 를 오류를 내지 않고 무시한다. 소유 역할을 확인하지 못하면 processor
  가 not-found 로 거부하고, 없는 권한 프리셋에는 에러를 반환하므로, adapter 는 빈 입력을
  즉시 반환하고 `failed` 에서 not-found 를 제외한다.

## bulk 추가는 권한 프리셋 하나씩 실행한다

- API 계약은 권한 프리셋 단위로 partial 이다. 중복은 `failed` 로 반환되고 나머지는
  반영된다. 한 요청이 여러 역할의 권한 프리셋을 담을 수 있다.
- field create factory 는 소유자 하나(`atomic_create_ops`)나 row 하나(`create_ops`) 아래에서
  atomic 이다. 여러 소유자에 걸친 partial create 모양은 없다.
- 그래서 adapter 는 권한 프리셋마다 `create_ops` action 을 실행하고
  `PermissionAlreadyGranted` 와 무결성 에러만 `failed` 에 모은다. 권한 거부는 요청 전체에
  대해 발생한다.

## service 메서드를 유지하는 연산

| 연산 | 유지 이유 |
|---|---|
| assign / revoke / bulk assign / bulk revoke | 프로젝트 멤버십까지 정리하는 분기 |
| replace_role_permissions | 한 역할의 권한 프리셋을 비우고 다시 채우는 두 단계 쓰기 |
| create_permission / update_permission / delete_permission | legacy 단일 권한 프리셋 경로로, 아직 field 연산으로 옮기지 않았다 |
| get / search 연산 | legacy 읽기 경로 |
