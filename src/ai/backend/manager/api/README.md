# Manager REST API Entry Points

← [Back to Manager](../README.md)

## Overview

The manager REST API is the main HTTP API of Backend.AI. It is built on the Starlette web framework and covers session creation, vfolder management, user management, and similar work.

## Architecture

### REST v2 (new endpoints)

```
Client → REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
                           ↑DTO in/out (common/dto/manager/v2/)
```

### REST v1 (legacy endpoints)

```
Client → REST v1 Handler → Middleware → Processor → Service → Repository
```

**Use the REST v2 pattern for new endpoints.**

## Standard Operations

An API implements six standard operations:

1. **create** - create a new entity
2. **get** - get one entity
3. **search** - query with filters and pagination
4. **update** - update an entity
5. **delete** - mark an entity as deleted
6. **purge** - permanently delete an entity

**Multi-target operations** have two semantics:
- **Batch** (`batch_*`): many rows in one SQL statement, **atomic** (all or nothing), and returns the affected row count only. For example, `batch_update`, `batch_delete`, `batch_purge`.
- **Bulk** (`bulk_*`): rows processed individually, **partial failures allowed** (returns successes and errors). For example, `bulk_create`, `bulk_upsert`.

## Scope Prefix Rules

**API layer only** (the service and repository layers do not use the prefix)

### Scoped Operations

Operations within a scope use the `{scope}_` prefix:

**REST endpoints:**
```
POST   /domains/{domain}/users               → domain_create_user
GET    /domains/{domain}/users/{id}          → domain_user
GET    /domains/{domain}/users?filter=...    → domain_search_users
PATCH  /domains/{domain}/users/{id}          → domain_update_user
DELETE /domains/{domain}/users/{id}          → domain_delete_user
DELETE /domains/{domain}/users/{id}?purge=1  → domain_purge_user
```

**GraphQL:**
```graphql
mutation domainCreateUser(scope: DomainScope, input: ...)
query domainUser(scope: DomainScope, id: ID)
query domainSearchUsers(scope: DomainScope, filter: ...)
```

### Admin Operations (No Scope)

Operations without a scope use the `admin_` prefix (superadmin required):

**REST endpoints:**
```
POST   /admin/domains               → admin_create_domain
GET    /admin/domains/{id}          → admin_domain
GET    /admin/domains?filter=...    → admin_search_domains
PATCH  /admin/domains/{id}          → admin_update_domain
DELETE /admin/domains/{id}          → admin_delete_domain
DELETE /admin/domains/{id}?purge=1  → admin_purge_domain
```

**GraphQL:**
```graphql
mutation adminCreateDomain(input: ...)
query adminDomain(id: ID)
query adminSearchDomains(filter: ...)
```

**See** the `/api-guide` skill for detailed implementation patterns.

## Middleware Stack

### 1. Authentication Middleware

Handles authentication for API handlers through the `@auth_required` decorator.

**Supported Authentication Methods:**
- **HMAC-SHA256 signature** (`Authorization` header)
- **JWT token** (`X-Backendai-Token` header)

### 2. Error Handling Middleware

The middleware converts exceptions to HTTP responses.

## REST v2 Handler Pattern

REST v2 handlers use the shared adapter and pydantic DTOs from `common/dto/manager/v2/`.

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
        payload = await self._adapters.domain.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
```

- `BodyParam[T]` where T is a DTO from `common/dto/manager/v2/`
- The response is a DTO payload returned directly through `APIResponse.build(response_model=payload)`
- adapters are shared with GraphQL and defined in `api/adapters/{domain}.py`

## REST API Pattern Reference

This section documents common patterns used across REST API implementations.

**For implementation guides, see the `/api-guide` skill.**

### Scope Pattern

A scope defines the access boundary of a query (domain, project, or user level).

**Repository Scope:**
```python
from dataclasses import dataclass
from repositories.base.types import QueryCondition


@dataclass(frozen=True)
class DomainFairShareTarget:
    """Scope for domain-level fair share search."""

    resource_group: str
    domain_name: str | None = None  # None = all domains

    def to_conditions(self) -> list[QueryCondition]:
        conditions = [
            QueryCondition(
                column=FairShareRow.resource_group,
                op=FilterOperator.EQ,
                value=self.resource_group,
            ),
        ]
        if self.domain_name is not None:
            conditions.append(
                QueryCondition(
                    column=FairShareRow.domain_name,
                    op=FilterOperator.EQ,
                    value=self.domain_name,
                )
            )
        return conditions
```

**Handler Usage:**
```python
@api_handler
async def get_domain_fair_shares(
    request: web.Request,
    resource_group: PathParam[str],
    domain_name: PathParam[str | None] = None,
) -> DomainFairShareSearchResult:
    """Get domain fair shares for a resource group."""
    repository = request.app["repositories"].fair_share

    scope = DomainFairShareTarget(
        resource_group=resource_group,
        domain_name=domain_name,
    )

    result = await repository.search_domain_fair_shares(scope)
    return result.to_dto()
```

**Flow**: handler parameters → scope object → repository → query conditions

### Filter Pattern

Filters build query conditions and ordering dynamically.

**Filter Adapter:**
```python
class DomainFairShareAdapter:
    """Adapter for domain fair share filters."""

    @staticmethod
    def to_conditions(filters: dict[str, Any]) -> list[QueryCondition]:
        conditions = []

        if domain_name := filters.get("domain_name"):
            conditions.append(
                QueryCondition(
                    column=FairShareRow.domain_name,
                    op=FilterOperator.EQ,
                    value=domain_name,
                )
            )

        if min_ratio := filters.get("min_ratio"):
            conditions.append(
                QueryCondition(
                    column=FairShareRow.ratio,
                    op=FilterOperator.GTE,
                    value=min_ratio,
                )
            )

        return conditions

    @staticmethod
    def to_orders(order_by: str | None) -> list[QueryOrder]:
        if not order_by:
            return [QueryOrder(column=FairShareRow.domain_name, ascending=True)]

        field, direction = order_by.split(":")
        return [
            QueryOrder(
                column=getattr(FairShareRow, field),
                ascending=(direction == "asc"),
            )
        ]
```

**Handler Usage:**
```python
@api_handler
async def list_domain_fair_shares(
    request: web.Request,
    query: QueryParam[ListDomainFairSharesQuery],
) -> DomainFairShareListResult:
    """List domain fair shares with filtering."""
    repository = request.app["repositories"].fair_share

    conditions = DomainFairShareAdapter.to_conditions(query.filters)
    orders = DomainFairShareAdapter.to_orders(query.order_by)

    result = await repository.batch_query_domain_fair_shares(
        conditions=conditions,
        orders=orders,
        offset=query.offset,
        limit=query.limit,
    )

    return result.to_dto()
```

**Flow**: query parameters → adapter → conditions and orders → repository

### Admin_ Prefix Pattern

Admin operations require superadmin privileges.

**Permission Check:**
```python
from ai.backend.manager.api.exceptions import InsufficientPermission


def _check_superadmin(request: web.Request) -> None:
    """Check if request user is superadmin."""
    user_role = request["user"]["role"]
    if user_role != "superadmin":
        raise InsufficientPermission("Superadmin required")
```

**Handler Usage:**
```python
@api_handler
async def admin_create_domain(
    request: web.Request,
    body: BodyParam[CreateDomainRequest],
) -> CreateDomainResponse:
    """Create domain (superadmin only)."""
    _check_superadmin(request)

    processors = request.app["processors"].domain
    action = CreateDomainAction(
        name=body.name,
        description=body.description,
    )

    result = await processors.create_domain.execute(action)
    return CreateDomainResponse(domain_id=result.domain_id)
```

**Pattern**: function name `admin_{operation}_{entity}`, first line `_check_superadmin()`

### Pagination Pattern

REST APIs use offset-based pagination.

**Query Model:**
```python
from pydantic import BaseModel


class PaginationQuery(BaseModel):
    offset: int = 0
    limit: int = 20
```

**Handler Usage:**
```python
@api_handler
async def list_items(
    request: web.Request,
    query: QueryParam[PaginationQuery],
) -> ItemListResult:
    """List items with pagination."""
    repository = request.app["repositories"].item

    result = await repository.list_items(
        offset=query.offset,
        limit=query.limit,
    )

    return ItemListResult(
        items=[item.to_dto() for item in result.items],
        total_count=result.total_count,
        offset=query.offset,
        limit=query.limit,
    )
```

**Response fields:**
- `items` - current page items
- `total_count` - total items across all pages
- `offset` - current offset
- `limit` - page size

## GraphQL Pattern Reference

See [GraphQL API README](./gql/README.md) for the full patterns.
Every GQL type must be backed by a pydantic DTO from `common/dto/manager/v2/` and uses
the custom decorators in `gql/decorators.py`. Resolvers call adapters (`info.context.adapters.*`).

## Error Handling

The Error Handling Middleware converts exceptions from each layer to HTTP responses.

## Related documents

- [GraphQL API](./gql/README.md) - GraphQL endpoints with GQL adapters
- [Repositories Layer](../repositories/README.md) - Querier pattern and data access
- [Actions Layer](../actions/README.md) - Action Processor details
- [Services Layer](../services/README.md) - Business logic
- [Event Stream API](./events.py) - Server-Sent Events
