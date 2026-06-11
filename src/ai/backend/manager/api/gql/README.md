# Manager GraphQL API (Strawberry)

← [Back to Manager API](../README.md)

## Overview

Manager GraphQL API is a GraphQL interface built using the Strawberry framework,
with all types backed by Pydantic v2 DTOs from `common/dto/manager/v2/`.

## Architecture

```
Client (Web UI/SDK)
    ↓ GraphQL Request
GraphQL Schema (Strawberry)
    ↓
Resolver Layer
    ↓ info.context.adapters.*  (DTO in, DTO out)
Adapter Layer
    ↓ Action/ActionResult
Action Processor Layer
    ↓
Services Layer
```

## Module Organization Pattern

The GraphQL module follows a consistent pattern for organizing code. Choose between file-based or package-based structure based on complexity.

### Decision Tree

```
Is it a simple module (1-2 entities, < 500 lines total)?
├── Yes → Use file-based: fetcher.py, resolver.py, types.py
└── No → Use package-based: fetcher/, resolver/, types/ directories
```

### Package-Based Structure (Complex Modules)

```
domain_v2/
├── __init__.py
├── resolver/
│   ├── __init__.py
│   └── query.py
└── types/
    ├── __init__.py
    ├── node.py        # DomainV2GQL(PydanticNodeMixin[DomainNode])
    ├── nested.py      # DomainBasicInfoGQL (@gql_pydantic_type)
    ├── filters.py     # DomainV2Filter(PydanticInputMixin[DomainFilter])
    └── payloads.py    # SearchDomainsPayloadGQL (@gql_pydantic_type)
```

### Layer Responsibilities

- **types/**: GQL type definitions — Node, Connection, Filter, Input, Payload, Enum
- **fetcher/**: Data loading — pagination, DataLoader usage, Adapter calls, DTO conversion
- **resolver/**: GraphQL operations — thin wrappers calling fetchers

## Type Definition Conventions

### Decorator Rules

All GQL types MUST use custom decorators from `decorators.py`.
Never use `@strawberry.type`, `@strawberry.input`, `@strawberry.field`, `@strawberry.enum`,
`@strawberry.mutation`, `@strawberry.subscription`, or `@strawberry.federation.type` directly.

```python
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_type,
    gql_pydantic_input,
    gql_connection_type,
    gql_field,
    gql_added_field,
    gql_root_field,
    gql_enum,
    gql_mutation,
    gql_subscription,
    gql_federation_type,
)
```

### Node Types (Relay)

Node types represent GraphQL entities with unique IDs. Inherit `PydanticNodeMixin[DTO]`.

```python
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

@gql_node_type(
    BackendAIGQLMeta(added_version="25.1.0", description="Domain entity.")
)
class DomainV2GQL(PydanticNodeMixin[DomainNode]):
    basic_info: DomainBasicInfoGQL
    # ...

    @gql_field(description="Projects belonging to this domain.")
    async def projects(self, info: Info[StrawberryGQLContext]) -> ...:
        return await info.context.data_loaders.project_loader.load(self.domain_name)
```

Conversion from DTO: `DomainV2GQL.from_pydantic(dto)`.

### Nested Output Types

Nested sub-models use `@gql_pydantic_type(model=DTO)`. Strawberry auto-generates `from_pydantic()`.

```python
from ai.backend.common.dto.manager.v2.domain.response import DomainBasicInfo

@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.1.0", description="Domain basic info."),
    model=DomainBasicInfo,
    all_fields=True,
)
class DomainBasicInfoGQL:
    pass  # all fields auto-generated from DTO
```

### Filter / OrderBy Types (Input)

Filter and OrderBy types inherit `PydanticInputMixin[DTO]`. `to_pydantic()` converts to DTO.

```python
from ai.backend.common.dto.manager.v2.domain.request import DomainFilter
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

@gql_pydantic_input(
    BackendAIGQLMeta(added_version="25.1.0", description="Domain filter.")
)
class DomainV2FilterGQL(PydanticInputMixin[DomainFilter]):
    name: strawberry.UNSET | StringFilterGQL = strawberry.UNSET
    AND: strawberry.UNSET | list[DomainV2FilterGQL] = strawberry.UNSET
    OR: strawberry.UNSET | list[DomainV2FilterGQL] = strawberry.UNSET
    NOT: strawberry.UNSET | DomainV2FilterGQL = strawberry.UNSET
```

Conversion to DTO: `filter_gql.to_pydantic()`.

### Payload Types

Mutation payloads use `@gql_pydantic_type(model=DTO)`.

```python
from ai.backend.common.dto.manager.v2.domain.response import AdminSearchDomainsPayload

@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.1.0", description="Admin search domains result."),
    model=AdminSearchDomainsPayload,
)
class AdminSearchDomainsPayloadGQL:
    items: list[DomainV2GQL]
    total_count: int
```

### Enum Values

- Use `gql_enum` (decorator or function call) — never `@strawberry.enum` directly.
- GQL enum values MUST match DTO enum values exactly (conversion is by `.value`).

```python
# As decorator
@gql_enum(BackendAIGQLMeta(added_version="25.1.0", description="Domain status."))
class DomainStatusGQL(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# As function (DTO wrapping)
DomainStatusGQL = gql_enum(
    BackendAIGQLMeta(added_version="25.1.0", description="Domain status."),
    DomainStatusDTO,
    name="DomainStatus",
)
```

### Nullable Return Types

Any field that runs through a **resolver** MUST be declared nullable (`T | None`). This
covers root `Query` / `Mutation` fields and any computed nested field on a Node /
Connection / Payload type — anything decorated with `@gql_root_field`, `@gql_mutation`,
`@gql_field`, or `@gql_added_field`. This follows GraphQL's nullable-by-default best
practice.

**Why**

- **Partial failure isolation.** When a resolver raises, GraphQL propagates `null` up to
  the nearest nullable ancestor. A non-null computed field turns a single nested
  resolver failure into a whole-parent failure, wiping sibling fields the client could
  otherwise have used.
- **Permission / scope denial.** Fields that are visible only to some users naturally
  express "denied" as `null` instead of an error that aborts the query.
- **Forward compatibility.** `nullable → non-null` is a breaking change; `non-null →
  nullable` is not. Starting nullable is the safe default.

**The rule (in Python resolvers)**

```python
# Root Query — single object
@gql_root_field(BackendAIGQLMeta(...))
async def admin_search_domains(...) -> AdminSearchDomainsPayloadGQL | None: ...

# Root Mutation — payload
@gql_mutation(BackendAIGQLMeta(...))
async def admin_create_domain(...) -> CreateDomainPayloadGQL | None: ...

# Root Connection
@gql_root_field(BackendAIGQLMeta(...))
async def admin_audit_logs_v2(...) -> AuditLogV2ConnectionGQL | None: ...

# Computed nested field — cross-entity DataLoader resolver
class DomainV2GQL(PydanticNodeMixin[DomainNode]):
    @gql_field(description="Projects belonging to this domain.")
    async def projects(self, info: Info[StrawberryGQLContext]) -> ProjectV2ConnectionGQL | None: ...

# Trivially derived scalar — exempt, see Exceptions below
class FooConnection(Connection[Foo]):
    @gql_field(description="Total count.")
    def count(self) -> int: ...

# List — only the outer list is nullable; element non-null is fine
@gql_root_field(BackendAIGQLMeta(...))
async def scheduling_handlers(...) -> list[SchedulingHandlerNodeGQL] | None: ...
```

This emits the return type without `!` in the SDL — e.g. `AdminSearchDomainsPayload`,
`AuditLogV2Connection`, `[SchedulingHandlerNode!]`, `ProjectV2Connection`.

**Resolver implementation note**

Returning `None` is allowed and recommended for "not found" / "denied" cases. Do NOT
catch domain exceptions inside fetchers just to swallow them as `None` — let
`BackendAIError` propagate so the failure surfaces in the GraphQL `errors` array.

**Exceptions**

- **Statically projected DTO fields** — class-level attributes that map directly from
  the backing Pydantic DTO (e.g. `name: str`) may stay non-null.
- **Trivially derived scalars** — resolver-decorated fields whose value is computed
  synchronously from non-null parent state with no I/O, permission check, or external
  call. Example: a Connection `count` returning `len(self.edges)` stays non-null.
- **Apollo Federation entry points** — `_service` and `_entities` are mandated by the
  spec and remain non-null.
- **Subscriptions** — streaming-event return types are governed separately.

## Fetcher Pattern

```python
async def fetch_admin_search_domains(
    info: Info[StrawberryGQLContext],
    filter: DomainV2FilterGQL | None,
    order_by: list[DomainV2OrderByGQL] | None,
    limit: int | None,
    offset: int | None,
) -> AdminSearchDomainsPayloadGQL:
    # 1. Convert GQL inputs to DTOs
    filter_dto = filter.to_pydantic() if filter else None
    order_dto = [o.to_pydantic() for o in order_by] if order_by else None

    # 2. Call shared adapter (same adapter used by REST v2)
    payload_dto = await info.context.adapters.domain.admin_search(
        AdminSearchDomainsInput(
            filter=filter_dto, order_by=order_dto, limit=limit, offset=offset
        )
    )

    # 3. Convert DTO payload to GQL type
    return AdminSearchDomainsPayloadGQL.from_pydantic(payload_dto)
```

## Resolver Pattern

### Query Resolvers

```python
@gql_root_field(BackendAIGQLMeta(added_version="25.1.0", description="Search all domains (admin only)."))
async def admin_search_domains(
    info: Info[StrawberryGQLContext],
    filter: DomainV2FilterGQL | None = None,
    order_by: list[DomainV2OrderByGQL] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AdminSearchDomainsPayloadGQL | None:
    check_admin_only(info)
    return await fetch_admin_search_domains(
        info=info, filter=filter, order_by=order_by, limit=limit, offset=offset
    )
```

### Mutation Resolvers

```python
@gql_mutation(BackendAIGQLMeta(added_version="25.1.0", description="Create a domain."))
async def admin_create_domain(
    input: CreateDomainInputGQL,
    info: Info[StrawberryGQLContext],
) -> CreateDomainPayloadGQL | None:
    check_admin_only(info)
    payload_dto = await info.context.adapters.domain.create(input.to_pydantic())
    return CreateDomainPayloadGQL.from_pydantic(payload_dto)
```

### Cross-Entity References

Use `strawberry.lazy()` to avoid circular imports:

```python
if TYPE_CHECKING:
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL

@gql_field(description="Projects associated with this domain.")
async def projects(
    self, info: Info[StrawberryGQLContext]
) -> Annotated[ProjectV2GQL, strawberry.lazy("...project_v2.types.node")] | None:
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    data = await info.context.data_loaders.project_loader.load(self.domain_name)
    return ProjectV2GQL.from_pydantic(data) if data else None
```

`| None` must be **outside** `Annotated[]`.

## Key Principles

- All GQL types are Pydantic-backed via custom decorators.
- Resolvers call Adapters — shared with REST v2 — not Processors directly.
- DataLoaders prevent N+1 queries for cross-entity references.
- Raise `BackendAIError` for all domain exceptions.

## Related Documentation

- [Manager API Overview](../README.md)
- [REST v2 API](../rest/v2/AGENTS.md)
- [Repositories Layer](../../repositories/README.md)
- [Legacy GraphQL (Graphene)](../gql_legacy/README.md) — DEPRECATED
