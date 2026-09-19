# Search field declarations — Guardrails

> For background and rationale, see `KNOWLEDGE.md` in the same directory.

Declares what an entity search can filter and order by. A declaration holds SQL operations only; reading a filter DTO is the job of the adapter's `apply_*_filter` (`repositories/base/filter_adapter.py`).

## Shape of an entity declaration

- Each entity has one entry class `{Entity}SearchableFields` in `models/{entity}/searchable_fields.py`.
- The entry has three attributes. The classes behind them are private (`_{Entity}OwnFields`, ...) and are reached only through the entry.

| Attribute | Holds | Permission |
|---|---|---|
| `own` | The entity's own columns as `SearchableField(column, filter, order)`. Implements `RowDataConverter` to build data from a row | The entity's field cap |
| `nested` | Rows of other tables the entity owns (labels, mount policies, dangling fields), readable under the entity's own permission. `NestedSearchableField(<other entry>.own, correlation)` | The entity's field cap (`labels.key`) |
| `linked` | Connections to other entities (`MembershipConditions`, `UsageConditions`) | Scopes, the other entity's permission |

- Every data field has a `SearchableField` of the same name, and `to_data` reads every value through `self.<name>.read(row)`. The data constructor requires every field, so a missing declaration fails mypy.
- Row classes carry no `to_data` or similar method. Callers use `{Entity}SearchableFields.own.to_data(row)`.
- Fill every filter and order slot. Use `None` only where it cannot work: JSON/JSONB, arrays, `SecretColumn`, derived fields. Order a `DecimalType` (VARCHAR) column by a numeric cast.
- The filter DTO and the order-field enum decide what the API exposes. A declaration states only what is possible.
- Attribute names match the filter DTO field, the data field and the field cap path.
- Declarations are class attributes. Do not create module-level instances.

## Conditions and orders

- A per-value-type condition class (`conditions/`) holds one column and its operation methods. It does not import filter DTOs.
- Operations do not take `None`. Skipping an unset filter field is `apply_*_filter`'s job.
- A field the shared implementation cannot serve gets a subclass in the entity module that overrides only that operation.
- Convert an order-field enum with `match` and end with `case _: assert_never(...)`.

## Rows of other tables

- Declare fields of other tables as `nested`, not flattened. Conditions gathered into one EXISTS apply to the same row.
- Use `ToManyCorrelation` (some / every / none) for to-many and `ToOneCorrelation` (has, order) for to-one.
- Use conditions and orders built by a `Correlation` only inside a query whose FROM has `correlate_row`.
- Do not name anything `Relation`. It collides with the link rows on the permission side (`specs/relation.py`, BEP-1075).

## Other entities

- Do not add nested filters on another entity's fields. Express a relation to another entity as a scope.
- Filter by another entity only through the identifier stored in the entity's own column (`creator_id`, `domain_name`, ...). To filter by its name or status, look the other entity up first and use its id.
- Rows that carry their own permission type (entity share, ...) do not go in `nested`. They are handled as a scope in that entity's search.

## Usage between entities

- A usage that is not ownership, such as session → vfolder, stays out of the ownership graph. It is decided from the using side's table columns.
- Only a foreign key column counts as a usage. An id inside a JSON value does not.
- Declare it in `linked` as `UsageConditions[{using entity}ID]`, named after the using entity in the plural (`deployments`, `model_cards`). `used_by(id)` returns a `UsedBy`.
- A scoped search passes `UsedBy` through `ScopedSearcher`. The caller must be able to read each using entity, or the whole search is refused. Results stay within the rows the scopes allow; a usage grants nothing.
- A global search passes `UsedBy` through `GlobalSearcher`. The SUPERADMIN gate answers for the unscoped read, so using entities are not checked.
