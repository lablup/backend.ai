## entity

[adapter](/src/ai/backend/manager/api/adapters/entity/adapter.py)

**list_entity_types**

| scenario | verdict |
|---|---|
| [when no processors are wired, an empty list comes back](#listing-nothing-wired-lists-nothing) | answered |
| [the entity type the processor wiring names comes back](#listing-the-wired-entity-type-is-listed) | answered |

### list_entity_types

<a id="listing-nothing-wired-lists-nothing"></a>

#### [nothing-wired-lists-nothing](/tests/scenario/bai_scenario/manager/entity/test_listing.py): pass

when no processors are wired, an empty list comes back

Given

- no processors are wired

When

- EntityAdapter.list_entity_types: lists the entity types

Then

- an empty list comes back
  - items = []

<a id="listing-the-wired-entity-type-is-listed"></a>

#### [the-wired-entity-type-is-listed](/tests/scenario/bai_scenario/manager/entity/test_listing.py): pass

the entity type the processor wiring names comes back

Given

- the domain processors are wired

When

- EntityAdapter.list_entity_types: lists the entity types

Then

- the one wired domain type comes back by its name
  - items = [EntityTypeNode(name='domain')]

