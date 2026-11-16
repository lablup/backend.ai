# 배포 프리셋 서비스: 배경

> 규칙: `../AGENTS.md`. 스펙 선택: `../../models/specs/KNOWLEDGE.md`.

배포 프리셋은 배포를 생성할 때 사용하는 template 이다. 자원 슬롯량도 함께 선언하므로 이 패키지는 두 테이블을 다룬다.

## processor 필드

`backend.ai mgr ops list --concern deployment --entity deployment_preset` 는 연결 및 호출 경로로 처리되는 목록을 출력한다. 그 출력은 엔티티 유형, shape, 연산, gate, backing 을 반환한다.

## slot row 는 프리셋의 field row 다

- `preset_resource_slots` 는 프리셋 하나가 own 하고 그로부터 함께 삭제되므로 field row 이고, `PresetResourceSlotID` 용 `id` uuid 를 따로 가진다. 기본 키는 `(preset_id, slot_name)` 으로 유지된다.
- 공유 `ResourceSlotEntryData` 대신 자체 `PresetResourceSlotData` 를 가진다. field row 의 data 는 own 하는 엔티티를 함께 반환하고, 공유 타입은 deployment revision 의 slot 에도 사용하도록 작성했다.
- `search_resource_slots` 는 프리셋을 인자로 받으므로 프리셋 소유자 조회를 실행하지 않는다. 이 연산은 프리셋 조회로 결과를 얻고 그 프리셋에 기록한다.

## rank 는 잠금 없이 INSERT 안에서 정한다

- creator 는 `build_row()` 에서 `rank` 에 `max(rank) + RANK_GAP` subquery 를 둔다. 부모 row 를 잠그고 MAX 를 읽던 세 문장이 하나로 줄었다.
- 동시 INSERT 는 같은 rank 에 놓일 수 있다. rank 는 목록의 순서만 정하고 프리셋은 드물게 생성되므로 같은 값은 허용한다. 순서를 결정적으로 정하려면 잠금을 되살려야 하고, 그러려면 스펙이 잠글 대상을 선언해야 한다.
- `RANK_GAP` 은 나중에 기존 프리셋 둘 사이에 새 프리셋을 추가할 여지를 남긴다.

## 변경만 서비스 메서드를 유지한다

- slot 을 다시 선언하면 기존 slot 을 비우고 새 집합을 기록한다. 한 트랜잭션의 두 테이블은 스펙 하나가 감당할 수 있는 범위를 넘는다.
- `slot_creators` 가 `None` 이면 slot 을 그대로 둔다. sequence 는 집합 전체를 교체하고, 빈 sequence 는 비운다.
- 생성에는 서비스가 필요 없다. `create_global_entity_with_fields` 가 프리셋과 slot 을 한 트랜잭션에서 함께 생성한다.

## 내부 이름만 DeploymentPreset 이다

- 테이블은 `deployment_revision_presets` 이고, GraphQL 타입과 DTO 는 그 이름을 유지한다. 이름을 변경하면 schema 호환성이 깨지고 migration 이 필요하다.
- 내부(actions, specs, repository, service)는 `DeploymentPreset` 으로 줄인다. 엔티티 유형과 `DeploymentPresetID` 도 그 이름을 사용한다.
