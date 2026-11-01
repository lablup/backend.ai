---
name: api-guide
description: Guide for implementing REST and GraphQL APIs (create, get, search, update, delete, purge, scope prefix patterns, admin_ prefix, SearchScope, BaseFilterAdapter, @api_function, Click CLI)
version: 1.0.0
dependencies:
  - service-guide
  - repository-guide
tags:
  - rest-api
  - graphql
  - client-sdk
  - cli
  - api-patterns
---

# API implementation guide

REST and GraphQL APIs share the standard operations and scope patterns below.

## Standard operations

APIs implement 6 standard operations:

1. **create** - create a new entity
2. **get** - get a single entity
3. **search** - query with filters and pagination
4. **update** - update an entity
5. **delete** - delete an entity (soft)
6. **purge** - permanently remove an entity (hard)

`batch_*` runs atomically in one statement. `bulk_*` handles rows individually with partial failures. See `/repository-guide`.

## Scope prefix rules

The prefix applies to the API layer. The service and repository layers do not use it.

### Scoped operations

Operations within a scope use a `{scope}_` prefix.

REST:

```
POST   /domains/{domain}/users        → domain_create_user
GET    /domains/{domain}/users/{id}   → domain_user
GET    /domains/{domain}/users         → domain_search_users
PATCH  /domains/{domain}/users/{id}   → domain_update_user
DELETE /domains/{domain}/users/{id}   → domain_delete_user
```

GraphQL:

```graphql
mutation domainCreateUser(scope: DomainScope, input: ...)
query domainUser(scope: DomainScope, id: ID)
query domainSearchUsers(scope: DomainScope, filter: ...)
```

### Admin operations

Operations without a scope use the `admin_` prefix and require the superadmin.

REST:

```
POST   /admin/domains        → admin_create_domain
GET    /admin/domains/{id}   → admin_domain
GET    /admin/domains         → admin_search_domains
```

GraphQL:

```graphql
mutation adminCreateDomain(input: ...)
query adminDomain(id: ID)
query adminSearchDomains(filter: ...)
```

### When to separate admin_ and non-admin endpoints

**search always has two variants:**

- `admin_search_*` - superadmin, no scope, queries the entire system.
- `{scope}_search_*` - non-admin, scope required, queries within the given scope only.
- There is no "search everything without scope" for non-admin users.

**create, update, get, delete and purge depend on the entity:**

1. **Admin-only entity** (for example Domain or ContainerRegistry): a single `admin_` endpoint.
2. **Both admin and users, but behavior differs** (for example the admin can set more fields on create or update): separate `admin_` and non-admin endpoints with different DTOs.
3. **Both admin and users, with only the permission check differing** - a single endpoint. The admin already has the entity access permissions, so no separate `admin_` variant is needed.

## REST v1 API patterns (legacy)

New endpoints use the REST v2 patterns below. REST v1 holds only existing legacy handlers; do not add new handlers there.

### Architecture

```
REST v1 Handler → Processor → Service → Repository
```

Key files:

- `src/ai/backend/manager/api/rest/{domain}/handler.py` - Handlers
- `src/ai/backend/manager/api/rest/{domain}/adapter.py` - Filters, per domain
- `src/ai/backend/manager/api/rest/adapter.py` - Base adapter

See `api/rest/fair_share/handler.py` for a handler that calls a processor, and `services/processors.py` for the ActionProcessor base class.

## REST v2 API patterns

REST v2 uses the same DTOs as GraphQL (`common/dto/manager/v2/`), so both API surfaces share one schema.

### Architecture

```
REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
```

The difference from v1 is that v2 handlers call shared adapters instead of processors directly. The adapters are shared with the GQL layer.

Key files:

- `src/ai/backend/manager/api/rest/v2/{domain}/handler.py` - Handlers
- `src/ai/backend/manager/api/rest/v2/{domain}/registry.py` - Route registration
- `src/ai/backend/manager/api/adapters/{domain}.py` - Shared adapters, the same as GQL
- `src/ai/backend/common/dto/manager/v2/{domain}/` - Shared DTOs

### Handler pattern

```python
from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.domain.request import AdminSearchDomainsInput
from ai.backend.manager.api.adapters.registry import Adapters


class DomainV2Handler:
    def __init__(self, *, adapters: Adapters) -> None:
        self._adapters = adapters

    async def admin_search(
        self,
        body: BodyParam[AdminSearchDomainsInput],
    ) -> APIResponse:
        payload = await self._adapters.domain.admin_search(body.parsed)
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=payload,
        )
```

### Scope pattern

Scope defines the access boundary.

Repository scope:

- `src/ai/backend/manager/repositories/{domain}/types.py`
- Example: `repositories/fair_share/types.py` with `DomainFairShareSearchScope` and `ProjectFairShareSearchScope`

Pattern:

- A frozen dataclass with scope parameters
- `to_conditions()` converts it to query conditions

See `api/fair_share/handler.py` for the scoped handler implementations.

### Scope parameter usage

The scope parameter is needed for:

1. **search**, to filter multiple items within the scope
   ```python
   domain_search_users(scope: DomainScope, filter: ...)
   ```

2. **batch operations**, to process multiple items within the scope
   ```python
   domain_batch_update_users(scope: DomainScope, ids: list[ID], ...)
   ```

The scope parameter is not needed for:

1. **get**, because the id uniquely identifies the item
   ```python
   user(id: ID)  # ✅ No scope needed
   # domain_user(scope: DomainScope, id: ID)  # ❌ Unnecessary
   ```

2. **update, delete and purge**, because the id uniquely identifies the item
   ```python
   update_user(id: ID, data: ...)  # ✅ No scope
   delete_user(id: ID)  # ✅ No scope
   ```

3. **create**, because the scope information is in the data
   ```python
   create_user(data: CreateUserData)  # data contains domain_name
   ```

The scope prefix in the API name (`domain_search_users`) differs from the scope parameter (`scope: DomainScope`).

### Filter pattern

Filters convert API parameters to a QueryCondition.

Adapter:

- `api/adapter.py` - BaseFilterAdapter
- `api/fair_share/adapter.py` - Domain adapters

Pattern:

- `to_conditions(filters)` → `list[QueryCondition]`
- `to_orders(order_by)` → `list[QueryOrder]`
- Adapter → `BatchQuerier` → repository

See `api/fair_share/adapter.py` for the filter adapters and `api/fair_share/handler.py` for handler implementations with BatchQuerier.

### admin_ prefix pattern

Admin operations require a superadmin check before processing.

- `_check_superadmin(request)` at the start of the handler
- Raise `InsufficientPermission` when the caller is not the superadmin

See `api/rbac/handler.py` for the admin handler implementations.

### Pagination

REST uses offset-based pagination.

```python
class PaginationQuery(BaseModel):
    offset: int = 0
    limit: int = 20

# Response
class SearchResult(BaseModel):
    items: list[Item]
    total_count: int
    offset: int
    limit: int
```

The client calculates `has_next = offset + limit < total_count`.

## GraphQL patterns

### Architecture

```
GraphQL Resolver → check_admin_only (if admin) → Adapter (info.context.adapters.*) → Processor → Service → Repository
```

Key files:

- `src/ai/backend/manager/api/gql/{domain}/resolver/` - Resolvers
- `src/ai/backend/manager/api/gql/decorators.py` - Custom decorators (required)
- `src/ai/backend/manager/api/gql/pydantic_compat.py` - PydanticNodeMixin, PydanticInputMixin
- `src/ai/backend/manager/api/gql/utils.py` - Utilities

### Decorator rules

All GQL types use the custom decorators from `decorators.py`. Do not use `@strawberry.type`, `@strawberry.input` or `@strawberry.experimental.pydantic.*` directly:

- `@gql_node_type(meta)` - Relay Node types, which inherit `PydanticNodeMixin[DTO]`
- `@gql_pydantic_type(meta, model=DTO)` - output types and payloads backed by a v2 Pydantic DTO
- `@gql_pydantic_input(meta)` - input types, which inherit `PydanticInputMixin[DTO]`
- `@gql_pydantic_interface(meta, model=DTO)` - interface types
- `@gql_connection_type(meta)` - `Connection[T]` and `Edge[T]` subclasses

`@strawberry.enum`, `@strawberry.field`, `@strawberry.mutation` and `@strawberry.subscription` may be used directly.

### Type system rules

Strawberry runtime evaluation:

- Strawberry types are evaluated at runtime
- Do not use `TYPE_CHECKING` for Strawberry types (Connection, Filter, OrderBy, Input, Type)
- Import Strawberry types directly at module level
- Use `TYPE_CHECKING` only for data layer types that Strawberry does not use
- When a lazy import is needed, use `strawberry.lazy()` or string-based forward references

Naming convention:

- All GraphQL types have the `GQL` suffix (`DomainGQL`, `DomainScopeGQL`, `DomainFilterGQL`)
- The suffix distinguishes GraphQL types from data layer types

Scope and filter:

- Scope: required context parameters (`resource_group`, `domain_name`, `project_id`)
- Filter: optional filtering conditions (name contains, status equals, created after)
- Do not put optional fields in Scope. Use Filter instead
- Scope fields are all required, with no default values and no Optional types

### Cross-entity reference resolvers

When a GQL node references another entity node, use `strawberry.lazy()` to avoid circular imports. Strawberry resolves types at runtime, so `TYPE_CHECKING` imports alone are not sufficient.

```python
# 1. TYPE_CHECKING: for static analysis (mypy)
if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL

# 2. Return type: Annotated with strawberry.lazy() for runtime resolution
# 3. Function body: runtime import + DataLoader
async def domain(self, info: Info[StrawberryGQLContext]) -> Annotated[
    DomainV2GQL,
    strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
]:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    data = await info.context.data_loaders.domain_loader.load(self.domain_name)
    return DomainV2GQL.from_data(data)
```

An optional return type puts `| None` **outside** `Annotated[]`:

```python
) -> Annotated[DomainV2GQL, strawberry.lazy("...")] | None:  # ✅
) -> Annotated[DomainV2GQL | None, strawberry.lazy("...")]:   # ❌ lazy cannot resolve union
```

DataLoaders (`info.context.data_loaders`) prevent N+1 queries. Use them instead of individual fetch functions. See `api/gql/data_loader/data_loaders.py` for the available loaders.

Examples:

- `api/gql/fair_share/types/domain.py` - Cross-entity reference with DataLoader
- `api/gql/domain_v2/types/node.py` - DomainV2GQL with fair_shares and usage_buckets
- `api/gql/fair_share/types/*.py` - Scope and filter patterns

### Scope pattern

Input types:

- `api/gql/types.py` with `ResourceGroupDomainScope`, `ResourceGroupProjectScope` and `ResourceGroupUserScope`

Pattern:

- A Strawberry `@input` maps to the repository SearchScope
- GraphQL input converts to the repository scope type

See `api/gql/types.py` for the scope input types and `api/gql/fair_share/resolver/domain.py` for the resolver implementations.

### Admin check

- `check_admin_only(info)` at the start of the resolver
- Raise `InsufficientPermission` when the caller is not the superadmin

See `api/gql/utils.py` for the `check_admin_only()` utility and `api/gql/*/resolver/*.py` for the admin resolvers.

### Pagination

GraphQL supports cursor-based pagination, per the Relay spec.

```python
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None

@strawberry.type
class UserConnection:
    edges: list[UserEdge]
    page_info: PageInfo
    total_count: int
```

See `api/gql/` for cursor pagination examples.

## REST v1, REST v2 and GraphQL

- **REST v1 (legacy)** - handler → processor. DTOs come from `common/dto/manager/`. Per-domain adapters live in `api/rest/{domain}/adapter.py`.
- **REST v2** - handler → adapter. DTOs come from `common/dto/manager/v2/`. Shared adapters live in `api/adapters/{domain}.py`.
- **GraphQL** - resolver → adapter, the same adapters as REST v2. DTOs come from `common/dto/manager/v2/`. Strawberry types wrap DTOs through the custom decorators.
- Admin check: REST uses the `superadmin_required` middleware; GQL uses `check_admin_only(info)`.
- Naming: REST uses `domain_create_user`; GQL uses `domainCreateUser`.

## Client SDK and CLI integration

When implementing a REST API, also implement:

1. **SDK function** (`client/func/{domain}.py`), with the `@api_function` decorator, mapped to the REST endpoint
2. **CLI command** (`client/cli/admin/{domain}.py`), a Click command that calls the SDK function

Integration flow:

```
CLI → SDK → REST API → Processor → Service → Repository
```

See `src/ai/backend/client/func/admin.py` for the SDK and `src/ai/backend/client/cli/admin/user.py` for the CLI.

## Testing

See `/test-guide` and `tests/CLAUDE.md` for the full testing strategies.

Test hierarchy:

```
Repository Tests → Real DB (with_tables)
Service Tests → Mock repositories
API Handler Tests → Mock processors
CLI Tests → Mock HTTP
```

## Implementation checklist

When implementing a new API:

1. **Repository** (`/repository-guide`)
   - Implement the standard operations
   - Define the SearchScope

2. **Service** (`/service-guide`)
   - Define the Actions and ActionResults
   - Implement the service methods
   - Create the processors

3. **REST API v2** (all new endpoints)
   - The handler calls the adapter and uses the DTOs from `common/dto/manager/v2/`
   - `BodyParam[DTO]` input and `APIResponse.build(response_model=payload)` output
   - Admin check and scope prefix

4. **GraphQL** (optional)
   - `@gql_pydantic_type` and `@gql_pydantic_input` with the DTO, without `@strawberry.type` directly
   - The resolver calls the adapter (`info.context.adapters.*`)
   - Admin check when needed

5. **Client SDK**
   - Add the SDK function
   - Add the `@api_function` decorator

6. **CLI**
   - Add the Click command
   - Integrate it with the SDK

7. **Tests**
   - Repository (real DB)
   - Service (mock repository)
   - Handler (mock processors)
   - CLI (mock HTTP)

## Related documents

- `/service-guide` - Actions and Processors
- `/repository-guide` - Data access
- `/test-guide` - Scenario-first testing
- `src/ai/backend/manager/api/README.md` - API layer reference

## Examples

REST API:

- `src/ai/backend/manager/api/fair_share/handler.py`
- `src/ai/backend/manager/api/rbac/handler.py`

GraphQL:

- `src/ai/backend/manager/api/gql/fair_share/resolver/domain.py`
- `src/ai/backend/manager/api/gql/types.py`

Client SDK and CLI:

- `src/ai/backend/client/func/admin.py`
- `src/ai/backend/client/cli/admin/user.py`
