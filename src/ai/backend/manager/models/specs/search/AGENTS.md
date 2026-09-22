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
- Fill every filter and order slot unless `Slots left empty` says otherwise.
- The filter DTO and the order-field enum decide what the API exposes. A declaration states only what is possible.
- Attribute names match the filter DTO field, the data field and the field cap path.
- Declarations are class attributes. Do not create module-level instances.
- A declaration due for removal lives in `models/{entity}/deprecated_search.py`. A migrated entity keeps no `conditions.py` or `orders.py`.

## Slots left empty

A slot is emptied for one of three reasons. Do not empty one for a reason that is not here.

### Impossible — the type does not support the operation

| Column kind | Filter | Order |
|---|---|---|
| JSON/JSONB | None | None |
| Array | None | None |
| `SecretColumn` | None | None |
| Derived field (no column behind it) | None | None |
| `DecimalType` (stored as VARCHAR) | Numeric cast | Numeric cast |
| To-many child (order) | Filter with some / every / none | None |

- Leave the filter empty when no shared condition class takes the column's type. Today that is interval (`retention_policies.retention_period`, `audit_logs.duration`).
- Adding a shared condition class adds that type's scenarios to the shared declaration DB test in the same change.

### Sensitive — it works, but the value leaks

Repeating a partial-match filter recovers the value one character at a time even when it is not in the response. An order does the same.
Empty both slots for the values below. Do not leave equality either.

| Column | Kind |
|---|---|
| `endpoint_tokens.token` | Plaintext token. `sa.String`, not `SecretColumn`, so the type alone does not catch it |
| `users.allowed_client_ip` | Access control setting. An array, so it is impossible as well |
| `sessions.callback_url`, `deployment_revisions.callback_url` | External callback address |
| `sessions.bootstrap_script`, `sessions.startup_command` | User-written script |
| `deployment_revisions.bootstrap_script`, `deployment_revisions.startup_command` | User-written script |
| `huggingface_registries.token` | Plaintext token. `sa.String`, so the type axis does not catch it |
| `reservoir_registries.secret_key`, `object_storages.secret_key` | Plaintext credential. `sa.String` for the same reason |
| `audit_logs.client_ip` | The address a call came from |

- To narrow by ownership, use the owner identifier (`user_id`, `creator_id`) instead of the value.
- A new column of the same kind as a row here gets a row of its own and empty slots.
- What this says is to leave the slot out of the declaration. Where an internal query already uses such a condition, finding another route belongs to that entity's migration issue.

### Cost — it works, but the query cannot carry it

| Column kind | Index | Operations allowed |
|---|---|---|
| `sa.String(length=N)`, N of 1024 or less | Either way | All |
| `sa.Text`, or N above 1024 | None | `equals`, `in_` |
| `sa.Text`, or N above 1024 | One that serves partial matches | All |
| Order by the entity's own column | Either way | Order allowed |
| Order by a to-one correlated column | Either way | `ToOneCorrelation.order` |
| To-many aggregate (count, min, max) | Either way | None — filter and order alike |

- There is one boundary, 1024, and the schema divides there: 1024 and below holds single-line values such as names, paths, URLs and descriptions, and anything larger is `sa.Text` or a `16 * 1024` script.
- A to-many aggregate runs its subquery again for every outer row. Promote a folded value to a parent column (`Rows of other tables`).
- **A value already exposed is not an exception but a migration target.** `UserV2OrderField.PROJECT_NAME`, `ProjectV2OrderField.USER_USERNAME` and `ProjectV2OrderField.USER_EMAIL` are MIN scalar subqueries and fall under this ban (exposed in 26.2.0). Mark them deprecated, remove them in the next release, and keep them working until then.
- Opening a partial match by adding an index puts that index in the same change.

## What the API exposes

A filled slot is not an API surface by itself.

- Expose a filter or an order only for a value a response carries. Nothing can populate
  a filter for a value no read returns, so it is surface nobody can use.
- Read that off the published schema (`docs/manager/graphql-reference/`), not off the
  row: a column can be accepted by a create input and absent from the node.
- A concept held back from the API stays unexposed although it is declared. The
  declaration serves the internal callers and the day it is opened — `replica_groups` is
  declared on the deployment and reaches no DTO.
- A value the API reports through another shape is exposed under that shape or not at
  all. One deployment status covers several lifecycle stages, so `lifecycle_stage`
  carries a filter and no order.
- An order enum value with no column behind it is not deleted. Mark it deprecated, ignore
  the value, and remove it in the next release.

## Conditions and orders

- A per-value-type condition class (`conditions/`) holds one column and its operation methods. It does not import filter DTOs.
- Operations do not take `None`. Skipping an unset filter field is `apply_*_filter`'s job.
- A field the shared implementation cannot serve gets a subclass in the entity module that overrides only that operation.
- Convert an order-field enum with `match` and end with `case _: assert_never(...)`.

## Rows of other tables

- Declare fields of other tables as `nested`, not flattened. Conditions gathered into one EXISTS apply to the same row.
- Use `ToManyCorrelation` (exists / not_exists / some / every / none) for to-many and
  `ToOneCorrelation` (exists, has, order) for to-one.
- A matching mode takes the conditions one related row must meet and refuses an empty list.
  Whether a related row is there at all is `exists` / `not_exists`, which take no condition.
- **A to-many opens filters and declares no order.** `ToManyCorrelation` building conditions only, with no `order`, is that rule.

| Shape | Asks | Filter | Order |
|---|---|---|---|
| exists / not_exists | Is there any child at all | Open | Not open |
| some | Is there any child satisfying the condition | Open | Not open |
| every / none | Do all children satisfy it / does none | Open | Not open |
| aggregate | What is the children's count, min or max | Not open | Not open |
| Child column value | — | Used as a condition inside the three shapes above | No such shape |

- With several children it is undefined which row's value an order would take. A to-one is one row, so `ToOneCorrelation.order` is open.
- To order by a value folded from the children, promote that value to a parent column and declare it as `own`. Do not turn a child condition into an order key.
- Use conditions and orders built by a `Correlation` only inside a query whose FROM has `correlate_row`.
- Do not name anything `Relation`. It collides with the link rows on the permission side (`specs/relation.py`, BEP-1075).

### How deep a declaration nests

Depth follows the permission axis, not the foreign keys.

| Target | Depth | Why |
|---|---|---|
| The same owner's field rows | 2 | One permission answers for the whole chain |
| Another entity | 0 | Its rows carry their own permission |
| An entity wired `public_*_ops`, for a to-one order | 1 | Nothing is denied, so the correlation adds no permission axis |

- A deployment reaches its revisions, replica groups, replicas, access tokens and
  auto-scaling rules, and a replica group reaches the revision it points at. That chain,
  `deployment -> replica_group -> revision`, is the deepest allowed. Do not add a third step.
- The second step needs no foreign key. A replica group's `current_revision_id` has none,
  and it is still the same deployment's field row.
- A column naming another entity stays an identifier filter on the owning row:
  `routings.session`, `routings.session_owner`, `routings.domain`, `routings.project`,
  `endpoint_auto_scaling_rules.prometheus_query_preset_id`. A relation between two entities
  is answered by `used_by`, which is where the second permission check belongs.
- The public exception is read off the wiring, not asserted: `runtime_variants` is wired
  `public_get_ops` / `public_search_ops`, so a revision may order by the variant's name.

## Other entities

- Do not add nested filters on another entity's fields (`How deep a declaration nests`). Express a relation to another entity as a scope.
- Filter by another entity only through the identifier stored in the entity's own column (`creator_id`, `domain_name`, ...). To filter by its name or status, look the other entity up first and use its id.
- Rows that carry their own permission type (entity share, ...) do not go in `nested`. They are handled as a scope in that entity's search.

## Usage between entities

- A usage that is not ownership, such as session → vfolder, stays out of the ownership graph. It is decided from a table column.
- Only a foreign key column counts as a usage. An id inside a JSON value does not. A key sitting on the searched row (`roles.role_preset_id`) is a usage too.
- There is one bundle, usage, and two directions inside it.

| Direction | Side searched | Narrowed by | Example |
|---|---|---|---|
| `used_by` | The used side | The using entity's id | The images this deployment uses |
| `uses` | The using side | The used entity's id | The sessions using this agent, the roles using this role preset |

- Declare them under `linked.usage.<entities>`, named after the other entity in the plural
  (`deployments`, `model_cards`). The declaration's type states the direction —
  `UsedByConditions` or `UsesConditions`. Do not put the direction on the path as well.
- That type's one method builds the condition, and its name is the direction.

| Declared as | Call | Reads as |
|---|---|---|
| `UsedByConditions` | `linked.usage.sessions.used_by(session_id)` | The images this session uses |
| `UsesConditions` | `linked.usage.agents.uses(agent_id)` | The sessions using this agent |

- One declaration answers one direction, because the correlation is built around the searched
  row. The other direction is declared on the other entity. Do not leave a usage declared from
  one side only.
- Do not declare `UsageConditions` itself. Only the two subtypes that name a direction.
- The API input carries one `usage` per search, holding `usedBy` and `uses`.
- The rules are the same both ways: narrow with AND, require the caller to be able to read the
  entity the condition names, grant no permission, and pull in no row the scopes disallow.
- A scoped search passes them through `ScopedSearcher`; one named entity the caller cannot read
  refuses the whole search. A global search passes them through `GlobalSearcher`, where the
  SUPERADMIN gate answers, so the named entities are not checked.
- What the search carries is one list either way: `ScopedSearcher.used_by` and
  `GlobalSearcher.used_by` take both directions' conditions, and one condition is a `UsedBy`.
- The agent has no `searchable_fields.py` yet, so `used_by.sessions` cannot be declared on it.
  Fill it in when the agent moves onto the v2 declarations.

## Scopes a search accepts

The per-entity tables are under `Scopes a search accepts` in `KNOWLEDGE.md`. Adding or removing a Target updates them in the same change.

| Searched | Scopes accepted |
|---|---|
| Entity | Every scope entity that can own it, and the scope of every relation that grants READ |
| Field | The entity that owns the field |

- A field search is the bulk shape that checks permission per owning entity. Its execution path is to move onto the new search path.
- Read the owning scopes off `created_in` on the creator and the upserter. Read the READ-granting relations off the `RelationCreator` declarations and the share writes.
- public is a scope like any other. A public read is a scope action, and one Target declares both what is authorized against (the public singleton) and the row condition (rows registered in public). Precedent: `PublicImageTarget` (`models/image/scopes.py`).
- The `is_global` column keeps its name. It means "registered in public". Names in code say public.
- Registration in public is membership. An entity whose whole type is public and an entity switched per row by a column (container registry, image, resource preset) both name public in `created_in`. For the per-row kind, its Target puts that column on as the row condition.
- A global read keeps the action shape. It checks the entity type and operation at the global singleton and adds no scope condition to the query. Permission is per type.
- The superadmin and monitor bypass stays as it is.
