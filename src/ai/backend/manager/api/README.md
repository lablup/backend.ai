# Manager REST API Entry Points

← [Back to Manager](../README.md)

## Overview

Manager REST API provides Backend.AI's main HTTP-based API endpoints. Built on the Starlette web framework, it offers various features including session creation, virtual folder management, and user management.

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

**New endpoints MUST use the REST v2 pattern.**

## Standard Operations

APIs implement 6 standard operations:

1. **create** - Create new entity
2. **get** - Retrieve single entity
3. **search** - Query with filters and pagination
4. **update** - Update entity
5. **delete** - Delete entity (soft)
6. **purge** - Permanently remove entity (hard)

**Batch operations:**
- `batch_update`, `batch_delete`, `batch_purge`

## Scope Prefix Rules

**API layer only** (Service/Repository layers don't use prefix)

### Scoped Operations

Operations within a scope use `{scope}_` prefix:

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

Operations without scope use `admin_` prefix (superadmin required):

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

**See:** `/api-guide` skill for detailed implementation patterns.

## Middleware Stack

### 1. Authentication Middleware

Handles authentication for API handlers with `@auth_required` decorator.

**Supported Authentication Methods:**
- **HMAC-SHA256 signature** (`Authorization` header)
- **JWT token** (`X-Backendai-Token` header)

### 2. Error Handling Middleware

Converts exceptions to appropriate HTTP responses.

## REST v2 Handler Pattern

REST v2 handlers use shared Adapters and Pydantic DTOs from `common/dto/manager/v2/`.

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
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
```

- `BodyParam[T]` where T is a DTO from `common/dto/manager/v2/`
- Response is a DTO Payload returned directly via `APIResponse.build(response_model=payload)`
- Adapters are shared with GraphQL — defined in `api/adapters/{domain}.py`

## REST API Pattern Reference

This section documents common patterns used across REST API implementations.

**For comprehensive implementation guides, see the `/api-guide` skill.**

### Scope Pattern

Scope defines access boundaries (domain, project, user level) for queries.

**Repository Scope:**
```python
from dataclasses import dataclass
from repositories.base.types import QueryCondition


@dataclass(frozen=True)
class DomainFairShareSearchScope:
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

    scope = DomainFairShareSearchScope(
        resource_group=resource_group,
        domain_name=domain_name,
    )

    result = await repository.search_domain_fair_shares(scope)
    return result.to_dto()
```

**Flow**: Handler parameters → Scope object → Repository → Query conditions

### Filter Pattern

Filters enable dynamic querying with conditions and ordering.

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

**Flow**: Query params → Adapter → Conditions/Orders → Repository

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

**Pattern**: Function name `admin_{operation}_{entity}`, first line `_check_superadmin()`

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
- `items`: Current page items
- `total_count`: Total items across all pages
- `offset`: Current offset
- `limit`: Page size

## GraphQL Pattern Reference

See [GraphQL API README](./gql/README.md) for full patterns.
All GQL types must be backed by Pydantic DTOs from `common/dto/manager/v2/` and use
custom decorators from `gql/decorators.py`. Resolvers call Adapters (`info.context.adapters.*`).

## Error Handling

Exceptions from each layer are converted to appropriate HTTP responses via Error Handling Middleware.

## Related Documentation

- [GraphQL API](./gql/README.md) - GraphQL endpoints with GQL adapters
- [Repositories Layer](../repositories/README.md) - Querier pattern and data access
- [Actions Layer](../actions/README.md) - Action Processor details
- [Services Layer](../services/README.md) - Business logic
- [Event Stream API](./events.py) - Server-Sent Events
