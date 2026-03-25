# Manager GraphQL Layer — Guardrails

> For full implementation patterns, see the `/api-guide` skill (GraphQL Patterns section).

## Type Naming

- Every Strawberry type MUST carry a `GQL` suffix: `DomainGQL`, `DomainFilterGQL`, `DomainScopeGQL`.
- Applies to all GQL output types, input types, and connection types.

## Decorators

- NEVER use `@strawberry.type`, `@strawberry.input`, `@strawberry.field`, `@strawberry.enum`,
  `@strawberry.mutation`, or `@strawberry.experimental.pydantic.*` directly.
- Use only the custom decorators defined in `decorators.py`:
  - `@gql_node_type` — Relay Node types (inherit `PydanticNodeMixin[DTO]`)
  - `@gql_pydantic_type(model=DTO)` — output types and payloads backed by a v2 Pydantic DTO
  - `@gql_pydantic_input` — input types (inherit `PydanticInputMixin[DTO]`)
  - `@gql_pydantic_interface(model=DTO)` — interface types backed by a v2 Pydantic DTO
  - `@gql_connection_type` — Connection[T] and Edge[T] subclasses
  - `gql_field` — fields introduced with the parent type (no separate version)
  - `gql_added_field` — fields added after the parent type (own version via `BackendAIGQLMeta`)
  - `@gql_root_field` — root query fields on the Query type (always versioned via `BackendAIGQLMeta`)
  - `gql_enum` / `@gql_enum` — enum types with version metadata
  - `@gql_mutation` — mutation resolvers with version metadata
  - `@gql_subscription` — subscription resolvers with version metadata
  - `@gql_federation_type` — federation types with keys and version metadata
- Do NOT add new decorators to bypass the Pydantic DTO requirement.

## Version Metadata

- When adding **new** types, fields, enums, or mutations, use `NEXT_RELEASE_VERSION` constant for `added_version`.
  Do NOT hardcode the version string — it is frozen to a literal at release time by `scripts/release.sh`.
  ```python
  from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

  @gql_root_field(BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="..."))
  async def my_foo(...): ...
  ```
- Existing types already released with a literal version (e.g., `"24.09.0"`) should NOT be changed.

## Imports

- NEVER import Strawberry types inside `TYPE_CHECKING` blocks — Strawberry evaluates types at
  runtime and will fail silently or raise errors.
- Always import Strawberry types at module level.

## Cross-Entity References

- Use `strawberry.lazy()` for cross-entity node references to avoid circular imports —
  see `/api-guide` skill for the correct `Annotated[T, lazy(...)] | None` syntax.

## N+1 Prevention

- Never call individual fetch functions inside resolvers for related entities.
- Always use `info.context.data_loaders.*` for cross-entity data loading.

## Admin Check

- Superadmin-only resolvers: call `check_admin_only(info)` as the first statement.

## Calling Services

- Resolvers MUST invoke services through Adapters (`info.context.adapters.*`), never
  Processors or Services directly.
- Adapters accept Pydantic DTOs (from `common/dto/manager/v2/`) and return Pydantic DTOs.

## Pydantic DTO Integration

GQL types are thin wrappers over the v2 DTOs in `common/dto/manager/v2/`.

- Node types: inherit `PydanticNodeMixin[DTO]`, decorate with `@gql_node_type`. Convert via `FooGQL.from_pydantic(dto)`.
- Nested output / payload types: use `@gql_pydantic_type(model=DTO)`. Strawberry auto-generates `from_pydantic()`.
- Input types: inherit `PydanticInputMixin[DTO]`, decorate with `@gql_pydantic_input`. Convert via `input_gql.to_pydantic()`.
- GQL enum values MUST match DTO enum values exactly (conversion is by `.value`).
- GQL field names MUST match DTO field names.
- `strawberry.UNSET` in GQL maps to `SENTINEL` default in DTO automatically via `to_pydantic()`.

## Error Handling & Nullable Schema

- When a query/resolver may fail to find an object, declare the return type as **nullable**
  (`T | None`) in the GraphQL schema.
- Do **NOT** catch domain exceptions (e.g., `NotFound`) in fetcher functions just to return `None`.
  Let the exception propagate — only `resolve_nodes` may return `Iterable[Self | None]` per Relay spec.

## Query Pagination Arguments

All search/list queries MUST provide ALL of the following argument groups — do NOT omit any:
- `filter: XxxFilterGQL | None` — entity-specific filter
- `order_by: list[XxxOrderByGQL] | None` — ordering specification
- `before: str | None`, `after: str | None` — cursor-based pagination cursors
- `first: int | None`, `last: int | None` — cursor-based pagination limits
- `limit: int | None`, `offset: int | None` — offset-based pagination

Clients must be able to choose between cursor and offset pagination freely.

## `my_` Resolver Pattern

For self-service queries (`my_keypairs`, `my_roles`, etc.):
- The resolver does NOT call `current_user()` or construct a scope.
- The resolver passes only the search input DTO to the adapter.
- The adapter is responsible for calling `current_user()` internally and constructing the scope.

## Legacy Code

- Do NOT copy patterns from `gql_legacy/` (Graphene) — it is being migrated to Strawberry.
