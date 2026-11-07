## entity

[어댑터](/src/ai/backend/manager/api/adapters/entity/adapter.py)

**list_entity_types**

| 시나리오 | 판정 |
|---|---|
| [배선된 처리기가 없으면 빈 목록이 반환됩니다](#listing-nothing-wired-lists-nothing) | 성공 |
| [처리기 배선이 이름 붙인 엔티티 유형이 반환됩니다](#listing-the-wired-entity-type-is-listed) | 성공 |

### list_entity_types

<a id="listing-nothing-wired-lists-nothing"></a>

#### [nothing-wired-lists-nothing](/tests/scenario/bai_scenario/manager/entity/test_listing.py): pass

배선된 처리기가 없으면 빈 목록이 반환됩니다

Given

- 배선된 처리기가 없습니다

When

- EntityAdapter.list_entity_types: 엔티티 유형 목록을 조회합니다

Then

- 빈 목록이 반환됩니다
  - items = []

<a id="listing-the-wired-entity-type-is-listed"></a>

#### [the-wired-entity-type-is-listed](/tests/scenario/bai_scenario/manager/entity/test_listing.py): pass

처리기 배선이 이름 붙인 엔티티 유형이 반환됩니다

Given

- 도메인 처리기가 배선되어 있습니다

When

- EntityAdapter.list_entity_types: 엔티티 유형 목록을 조회합니다

Then

- 배선된 도메인 유형 하나가 그 이름으로 반환됩니다
  - items = [EntityTypeNode(name='domain')]

