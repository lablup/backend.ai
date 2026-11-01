# 역할 프리셋 service: 배경

> 규칙은 `../AGENTS.md`, spec 선택은 `../../models/specs/KNOWLEDGE.md` 에 있다.

역할 프리셋은 어떤 엔티티 종류의 엔티티를 생성할 때 그 스코프 종류가 어떤 역할을 프로비저닝하는지, 그 역할마다 어떤 권한을 갖는지 선언한다. 권한 row 는 own 하는 프리셋과 떨어져 생명을 갖지 않으므로 이 패키지가 두 테이블을 다룬다.

## Processor field

`backend.ai mgr ops list --concern rbac` 를 실행하면 연결된 목록이 출력된다. 그 출력이 엔티티 종류, shape, operation, gate, backing 을 알려 준다.

`ProcessorGroup` 하나를 연결한다. 프리셋이 엔티티이고 그 권한 프리셋은 프리셋의 field row 이므로, 그 항목에 대한 operation 은 그 그룹이 내주는 field 하위 그룹에서 온다. 감사에 기록하는 엔티티는 항상 프리셋이다.

## 프리셋은 field row 를 own 하는 global 상태다

- 프리셋은 스코프 종류가 무엇을 받는지 선언하며 다른 곳과 공유하지 않는다. `global` 스코프에서 생성하므로 `RolePresetCreator` 는 `CreatedInGlobal` 을 가진 `EntityCreator` 다.
- 권한 row 는 `FieldCreator` 다. 프리셋을 참조하는 FK 에 `ondelete=CASCADE` 가 붙고, `(preset, entity_type, operation)` 세 값에 unique 제약이 있으며, 다른 곳에서 참조하지 않는다.
- global 소유자여도 모순이 아니다. field 는 row 의 소속을 소유자를 통해서만 알 수 있다는 뜻이고, 소유자가 무언가 아래에 있다는 뜻이 아니다.

## 생성이 action 하나라 두 테이블이 한 트랜잭션을 공유한다

- `global_create_with_fields_ops` 는 프리셋의 creator 와 권한 creator 를 함께 받는다. 권한 row 하나가 실패했는데 프리셋이 남으면 선언한 것보다 적은 권한을 부여하게 된다.
- field creator 는 부모의 id 로 row 를 생성한다. 부모 row 가 생기기 전에는 그 id 가 없고, `FieldCreator.build_row(owner_id)` 가 한 번의 쓰기 안에서 그 순서를 정할 수 있게 한다.

## 권한 프리셋의 operation 은 프리셋이 처리한다

- 권한 프리셋을 추가하거나 제거하는 일은 프리셋에 대한 변경이므로 `UPDATE` 로 기록한다. 권한 프리셋은 자체적인 권한 비트를 갖지 않는다.
- `atomic_bulk_add_permissions` 는 프리셋 id 를 받는다. 아직 지목할 권한 프리셋이 없다. `partial_bulk_remove_permissions` 는 권한 프리셋 id 만 받고, lookup 이 own 하는 프리셋을 찾아낸다.
- `partial_bulk_remove_permissions` 가 받는 권한 프리셋은 서로 다른 프리셋에 속할 수 있다. 그 소유자를 한 번에 조회하고 모두 검사한다. 응답은 권한 프리셋마다, 기록은 프리셋마다 남긴다.

## 삭제와 영구 삭제는 중복이 아니라 서로 다른 operation 이다

- lifecycle column 은 삭제 표시 mixin 의 `role_presets.deleted_at` 이다. 그래서 `delete` 와 `partial_bulk_delete` 는 DB 에서 UPDATE 이고 `DELETE` 로 기록하며, `restore` 와 `partial_bulk_restore` 는 같은 update 를 되돌린 것이다. 둘 다 공유 updater(`models/specs/soft_delete.py`)를 사용한다.
- `purge` 와 `partial_bulk_purge` 는 row 를 삭제하고, 권한 row 는 FK cascade 로 함께 삭제된다.
- lifecycle column 은 일반 updater 에 노출되지 않으므로 보통의 수정으로는 이 전이를 할 수 없다.

## template 을 확정하는 두 쓰기만 service 를 둔다

- 사용 시점의 render 는 자기 실패를 무시하고 생성한 이름으로 대체한다. 엔티티 생성이 역할 이름 때문에 실패해서는 안 되기 때문이다. 그래서 template 이 깨졌다는 것을 호출자가 아는 지점은 쓰기뿐이다.
- template 을 받는 operation 은 create, update, partial bulk update 뿐이므로 이 셋만 분기한다. 나머지는 ops 로 바로 실행한다.
- 검사는 sandbox 로 격리한 Jinja 환경에서 dummy 스코프로 template 을 render 하고, 문법 오류, 정의되지 않은 변수, 빈 결과를 거부한다.
- 길이는 검사하지 않는다. render 가 column 한도로 자르므로 거부할 것이 없다.

## 프리셋 변경은 그 프리셋에서 파생된 역할에 반영된다

- 역할은 자신을 생성한 프리셋을 `roles.role_preset_id` 에 기록한다. update, partial bulk update, 권한 추가, 권한 제거는 `RolePresetRepository` 를 거치고, 이 repository 가 같은 트랜잭션에서 그 프리셋에서 파생된 역할을 프리셋이 지금 선언한 상태로 되돌린다. 연결이 NULL 인 역할은 건드리지 않는다.
- 권한은 역할 자신의 스코프에 프리셋의 권한 집합과 같게 선언한다. 프리셋에서 빠진 엔티티 종류의 권한은 해지한다. row 를 삭제하고 다시 생성하지 않으므로 역할 id 가 유지된다.
- 이름은 생성이 사용한 것과 같은 규칙(`_preset_role_name`)으로 다시 render 한다. template 을 사용하는 프리셋의 스코프 row 가 없으면 그 역할의 이름은 그대로 둔다.
- 역할은 자기를 프로비저닝한 스코프에 있다. 따라서 수정할 역할은 프리셋의 역할을 프리셋의 `scope_type` 인 스코프와 join 해서 찾는다. `scope_type` 이 변경되면 기존 파생 역할은 그 join 에서 빠지고 그대로 남는다. 다른 종류의 스코프에 있는 역할은 새 종류로 다시 파생할 수 없다.
- `auto_assign` 이 False 에서 True 로 변경되어도 기존 사용자에게 아무것도 부여하지 않는다. 부여는 엔티티 생성의 규칙이고, 프리셋 변경은 역할의 flag 만 변경한다.
