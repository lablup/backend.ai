# Manager GraphQL layer — Guardrails

> For background (federation collisions, pagination behavior), see `KNOWLEDGE.md` in the same directory; for implementation patterns, see the `/api-guide` skill (GraphQL Patterns).

## Type naming

- Every Strawberry type appends the `GQL` suffix to its **Python class name**: `DomainGQL`, `DomainFilterGQL`, `DomainScopeGQL`.
- Applies to output, input, and connection types alike.
- The **schema-exposed name** must NOT contain `GQL`. Always pass `name=` (the class name with `GQL` stripped) to the decorator
  (e.g. `CreateDomainInputGQL` → `name="CreateDomainInput"`). Omitting `name=` leaks `GQL` into the SDL.
- If the name collides with a v1 Graphene type, use a `V2`-suffixed schema name (`name="KeyPairV2"`). See `KNOWLEDGE.md` for background.

## Decorators

- Do NOT use `@strawberry.type/input/field/enum/mutation` or `@strawberry.experimental.pydantic.*` directly.
- Use only the custom decorators in `decorators.py`:
  - `@gql_node_type` — Relay Node type (inherits `PydanticNodeMixin[DTO]`)
  - `@gql_pydantic_type(model=DTO)` — output type / payload based on a v2 Pydantic DTO
  - `@gql_pydantic_input` — input type (inherits `PydanticInputMixin[DTO]`)
  - `@gql_pydantic_interface(model=DTO)` — DTO-based interface
  - `@gql_connection_type` — `Connection[T]`/`Edge[T]` subclass
  - `gql_field` / `gql_added_field` — a field introduced together with its parent type / a field added later (with its own version)
  - `@gql_root_field` — a root query field on the Query type (always version-tagged)
  - `gql_enum` / `@gql_enum`, `@gql_mutation`, `@gql_subscription`, `@gql_federation_type`
- Do NOT add new decorators to bypass the Pydantic DTO requirement.

## Version metadata

- Rule: root `AGENTS.md` (Version metadata). A new type, field, enum, or mutation takes it through its decorator:
  ```python
  from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
  @gql_root_field(BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="..."))
  async def my_foo(...): ...
  ```

## import

- Do NOT import Strawberry types inside a `TYPE_CHECKING` block — Strawberry evaluates types at runtime, so it will
  silently fail or error. Always import at module level.

## Cross-entity references

- Use `strawberry.lazy()` for cross-entity node references to avoid circular imports
  (for the `Annotated[T, lazy(...)] | None` syntax, see `/api-guide`).

## Relations

Rules for a table row joining two entities with neither an entity type nor a field type declared for it
(user↔role, scope↔idle checker, session↔idle checker). Background: `KNOWLEDGE.md`, BEP-1075.

- Expose a relation row as a relation type. A relation type implements Node.
- A relation type's `id` is a global ID built from the type name and the end UUIDs. A polymorphic side adds
  its type (`IdleCheckerAssignment`: scope type, scope id, idle checker). Do NOT use a row id.
- Build and decode the global ID in the GQL layer only. Adapters and DTOs carry the end UUIDs only.
- Use the global ID for `node(id:)` and the Relay store key only. Individual queries and mutations take the end
  UUIDs as arguments.
- Reading a relation through `node(id:)` asks read on both end scopes.
- A relation type carries both end entities as Node fields and the relation values as plain fields. One per
  relation, whichever direction it is read from (`SessionIdleCheck`).
- Name a relation type after the relation's Data and DTO names, not its table. Append `V2` when the name is
  taken (`RoleAssignmentV2`).
- Put a connection of the relation type on both end entity Nodes, or on neither. Do NOT add a connection
  joining the two entities directly.
- Add a root scoped query per relation type. Its scope takes lists of both end entities, OR'd together
  (`scopedSessionIdleChecks(scope: {session, checker})`).
- `filter` and `order_by` on relation connections and root queries are the relation type's Filter and OrderBy.
  They carry relation value conditions and end entity conditions (`checker: IdleCheckerFilter`), with
  `AND`/`OR`/`NOT`.
- The cursor encodes the end keys.
- `node(id:)` and `nodes(ids:)` read a list of end keys at once. End entity fields load through that entity's
  bulk data loader.
- A mutation creating or changing a relation takes the end UUIDs. Its payload follows "Mutation payload" below.
- A row declared as an entity type (`EntityShare`) is an entity, not a relation, and is a Node.
- Keep an already published relation Node (`RoleAssignment`) deprecated and add no fields to it.
- Do NOT change connections published before this rule that join two entities directly (`DomainV2.users`,
  `UserV2.projects`, ...).

## Mutation payload

Whether the target (entity, field row, relation) still exists when the response is sent decides the payload.
Background: `KNOWLEDGE.md`.

| Operation | Target at response time | Payload |
|---|---|---|
| create · update · soft delete · restore | exists | the target Node field |
| purge finishing within the request | gone | `purgedId: ID!` + `entityId` for an entity, `fieldId` for a field row, the end UUIDs for a relation |
| purge of an entity with `purge_status` | exists (`purgeStatus: PURGING`) | the target Node field, no `purgedId` |
| force purge | gone | same as a purge finishing within the request |

- `purgedId` is the removed target's global ID; Relay's `@deleteEdge` and `@deleteRecord` take it. The GQL
  layer builds it from the DTO's UUID.
- A purge mutation returns a payload type of its own, `Purge<X>Payload`. Do NOT share a payload type with a
  delete (soft delete) mutation.
- Do NOT put `purgedId` on a payload named `Delete*`. Leave a published `delete*` mutation that removes the row
  as it is, add a `purge*` mutation returning `Purge<X>Payload`, and deprecate the old mutation.
- Do NOT put a global ID in the payload's own `id`.
- Do NOT return the removed target as a Node.
- A purge of an entity with `purge_status` is complete when `node(id:)` answers null. A failure is
  `purgeStatus: PURGE_ERROR` on the same Node.
- Input arguments are UUIDs. Do not change the type of a published field or argument; add the new one and
  deprecate the old.

## N+1 prevention

- Do NOT fetch related entities via individual fetch functions inside a resolver.
- Always use `info.context.data_loaders.*` for cross-entity loading.
- A data loader reads its ids through a bulk action (`partial_bulk_get_ops`, `public_partial_bulk_get_ops` for a
  public entity, `batch_load_fields` for field rows). Do NOT read them through a global search with an id condition.
- A global search is gated on SUPERADMIN, so a regular user following a node they can read has the whole batch refused.
- One batch mixes ids from several resolvers. A bulk action answers per id: only the field awaiting a denied id
  errors, and a missing id stays `None`.

## Calling services

- Resolvers call services only through the Adapter (`info.context.adapters.*`) — no direct Processor/Service calls.
- The Adapter receives and returns Pydantic DTOs (`common/dto/manager/v2/`).

## Pydantic DTO integration

GQL types are thin wrappers over the v2 DTOs (`common/dto/manager/v2/`).

- Node: inherit `PydanticNodeMixin[DTO]` + `@gql_node_type`. Convert via `FooGQL.from_pydantic(dto)`.
- Nested output/payload: `@gql_pydantic_type(model=DTO)`. `from_pydantic()` is auto-generated.
- Input: inherit `PydanticInputMixin[DTO]` + `@gql_pydantic_input`. Convert via `input_gql.to_pydantic()`.
- GQL enum values must exactly match the DTO enum values (converted via `.value`). GQL field names must match the DTO field names.
- GQL's `strawberry.UNSET` is automatically mapped to the DTO's `SENTINEL` default in `to_pydantic()`.

## Error handling & nullable schema

- Any field that runs through a resolver declares a **nullable** return type (`T | None`): root `Query` / `Mutation` fields
  and computed fields on Node / Connection / Payload types.
  See `README.md` "Nullable Return Types".
- Do NOT catch domain exceptions (`NotFound`, etc.) in the fetcher just to return `None` — propagate the exception.
  Per the Relay spec, only `resolve_nodes` may return `Iterable[Self | None]`.

## Query pagination arguments

Every search/list query provides **all** of the argument groups below — do not omit any:
- `filter: XxxFilterGQL | None`
- `order_by: list[XxxOrderByGQL] | None`
- `before/after: str | None`, `first/last: int | None` (cursor)
- `limit/offset: int | None` (offset)

The client must be free to choose cursor or offset. For per-mode behavior, see `KNOWLEDGE.md`.

## Admin & scope

- superadmin-only resolvers: call `check_admin_only()` on the first line.

**search — three variants:**
- `adminFoosV2`: superadmin only, no scope — the entire system.
- `scopedFoosV2` (e.g. `scopedSessionsV2`): non-admin, scope required — within that scope.
- `myFoosV2`: self-service — fills the current user in as the user scope and calls the same adapter `scoped_search` as `scopedFoosV2`.
- There is no "unscoped system-wide query" for non-admins.

**scoped search convention:**
- Query name `scopedFoosV2` (a single root field per entity).
- The scope is a **required argument** received as a per-entity input (`FooScopeGQL`, `api/gql/{entity}/types/scope.py`) — no bare ID.
- That input carries one list per scope kind, each item a `UUIDScope`, and every item is OR'd:
  `ResourceGroupScope{domain: [UUIDScope], project: [UUIDScope], user: [UUIDScope]}`. An open
  entity type the closed RBAC element enum cannot name takes its own pair instead
  (`EntityShareTargetScope`).
- Which kinds a scope carries is fixed: an entity takes the scopes that may own it
  (`created_in`, plus the scopes it is enrolled in), a field row takes its owner's type alone.
- Every kind in a scope is also reachable the other way, as a connection field on that
  scope's node — `ResourceGroupScope.domain` and `DomainV2.resourceGroups` are the two
  directions of one relation. Add both or neither.
- Put non-empty validation in the DTO's Pydantic `model_validator` — uniformly rejected at the GQL/REST boundary.
- The resolver passes the scope to the adapter together with the search input DTO. Authorization (RBAC) is the responsibility of the adapter/service — not the resolver.
- Legacy `{scope}FoosV2` (e.g. `projectSessionsV2`) predates this convention — do not create new ones.

**`myFoosV2` resolver:**
- The resolver builds the user scope from `current_user()`, puts it in `ScopedSearchFoosInput`, and calls the adapter's `scoped_search`.
- Do not add `my_search` to the adapter.

**create / update / get / delete / purge — criteria for splitting out `admin_`:**
- admin-only entities: a single `admin_` mutation/query.
- both admin and user, with different behavior: split `admin_` and non-admin (different input types).
- differing only in permission checks: a single one — admins already have access.

## Bulk field naming

**Telling atomic from partial** — does a per-item failure path actually exist.
A write where one item can fail while the rest commit is partial; anything else is
atomic. A read is atomic by default.

**The rule that follows**:
- An atomic field carries no `failed` / `errors` channel. A field that carries one is partial.
- This must agree with whether the action subclasses `BasePartialBulkAction` (`actions/v2/bulk/base.py`).

**Naming**: `AtomicBulk` or `PartialBulk` goes after the access prefix, and the rest of
the name is identical to the single form, with no pluralisation —
`myScopePermissions` / `myAtomicBulkScopePermissions`.

**Where the existing surface stands**: 22 payloads carry a `failed` or an `errors` field
and the names say nothing about which behaviour they have. 18 are genuinely partial.
3 are atomic with a channel that is always empty — `BulkAddRolePermissionPresetsPayload`,
`ReplaceRolePermissionsPayload`, `UpsertAppConfigFragmentsPayload`.
The remaining one, `ScanProjectModelCardsV2Payload`, reports a scan summary in `errors`
rather than a per-item channel. Renaming the 22 is breaking, so this states the policy
and the migration is judged separately.

## Legacy

- Do NOT copy `gql_legacy/` (Graphene) patterns — migrating to Strawberry.
