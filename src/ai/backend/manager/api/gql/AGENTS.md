# Manager GraphQL layer — Guardrails

> For background (federation collisions, pagination behavior), see `CONTEXTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill (GraphQL Patterns).

## Type naming

- Every Strawberry type appends the `GQL` suffix to its **Python class name**: `DomainGQL`, `DomainFilterGQL`, `DomainScopeGQL`.
- Applies to output, input, and connection types alike.
- The **schema-exposed name** must NOT contain `GQL`. Always pass `name=` (the class name with `GQL` stripped) to the decorator
  (e.g. `CreateDomainInputGQL` → `name="CreateDomainInput"`). Omitting `name=` leaks `GQL` into the SDL.
- If the name collides with a v1 Graphene type, use a `V2`-suffixed schema name (`name="KeyPairV2"`). See `CONTEXTS.md` for background.

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

- When adding a new type, field, enum, or mutation, use the `NEXT_RELEASE_VERSION` constant for `added_version` — do NOT
  hardcode the version string (`scripts/release.sh` freezes it at release time). Do not change literal versions that are already released.
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

## N+1 prevention

- Do NOT fetch related entities via individual fetch functions inside a resolver.
- Always use `info.context.data_loaders.*` for cross-entity loading.

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

- For queries/resolvers that may not find an object, declare the return type as **nullable** (`T | None`).
- Do NOT catch domain exceptions (`NotFound`, etc.) in the fetcher just to return `None` — propagate the exception.
  Per the Relay spec, only `resolve_nodes` may return `Iterable[Self | None]`.

## Query pagination arguments

Every search/list query provides **all** of the argument groups below — do not omit any:
- `filter: XxxFilterGQL | None`
- `order_by: list[XxxOrderByGQL] | None`
- `before/after: str | None`, `first/last: int | None` (cursor)
- `limit/offset: int | None` (offset)

The client must be free to choose cursor or offset. For per-mode behavior, see `CONTEXTS.md`.

## Admin & scope

- superadmin-only resolvers: call `check_admin_only()` on the first line.

**search — three variants:**
- `adminFoosV2`: superadmin only, no scope — the entire system.
- `scopedFoosV2` (e.g. `scopedSessionsV2`): non-admin, scope required — within that scope.
- `myFoosV2`: self-service, the adapter resolves the current user as the scope internally.
- There is no "unscoped system-wide query" for non-admins.

**scoped search convention:**
- Query name `scopedFoosV2` (a single root field per entity).
- The scope is a **required argument** received as a per-entity input (`FooScopeGQL`, `api/gql/{entity}/types/scope.py`) — no bare ID.
  The shape is per-entity (single ID / list of entity-tag refs / per-category list).
- Put non-empty validation in the DTO's Pydantic `model_validator` — uniformly rejected at the GQL/REST boundary.
- The resolver passes the scope to the adapter together with the search input DTO. Authorization (RBAC) is the responsibility of the adapter/service — not the resolver.
- Legacy `{scope}FoosV2` (e.g. `projectSessionsV2`) predates this convention — do not create new ones.

**`myFoosV2` resolver:**
- The resolver does NOT call `current_user()` or build a scope — it passes only the search input DTO to the adapter.
- The adapter builds the scope internally via `current_user()`.

**create / update / get / delete / purge — criteria for splitting out `admin_`:**
- admin-only entities: a single `admin_` mutation/query.
- both admin and user, with different behavior: split `admin_` and non-admin (different input types).
- differing only in permission checks: a single one — admins already have access.

## Legacy

- Do NOT copy `gql_legacy/` (Graphene) patterns — migrating to Strawberry.
