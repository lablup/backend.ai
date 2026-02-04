# Manager REST API Entry Points

← [Back to Manager](../README.md)

## Overview

Manager REST API provides Backend.AI's main HTTP-based API endpoints. Built on the Starlette web framework, it offers various features including session creation, virtual folder management, and user management.

## Architecture

```
┌──────────────────────────────────────────┐
│         Client (SDK/CLI/Web UI)          │
└────────────────┬─────────────────────────┘
                 │
                 ↓ HTTP Request
┌────────────────────────────────────────────┐
│            REST API Handler                │
│         (Starlette Routes)                 │
│                                            │
│  - session.py (session creation/mgmt)      │
│  - vfolder.py (virtual folders)            │
│  - admin.py (admin tasks)                  │
│  - auth.py (authentication)                │
│  - scaling_group.py (scaling groups)       │
│  - ... (other endpoints)                   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Middleware Stack                 │
│                                            │
│  1. Authentication Middleware              │
│  2. Rate Limiting Middleware               │
│  3. Request Validation                     │
│  4. Error Handling Middleware              │
│  5. Metric Collection                      │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Action Processor Layer             │
│                                            │
│  - Authorization (RBAC)                    │
│  - Action Validation                       │
│  - Audit Logging                           │
│  - Monitoring                              │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Services Layer                   │
│                                            │
│  - Business Logic                          │
│  - External Service Orchestration          │
│  - Quota/Limit Enforcement                 │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Repositories Layer                 │
│                                            │
│  - Data Access                             │
│  - Transaction Management                  │
└────────────────────────────────────────────┘
```

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

## Actions Layer Integration

REST API handlers and GraphQL handlers invoke Action Processor to execute business logic.

**Handler Responsibilities:**
- Only handles HTTP request/response data conversion
- Creates Action objects and invokes Processor
- Does not implement business logic directly

See [Actions Layer Documentation](../actions/README.md) for details.

## Adapter Pattern

The API layer uses adapters to convert between API DTOs and repository queries.

### Architecture

```
Client Request (JSON/Form)
    ↓
API Handler
    ↓ parse & validate
DTO Objects (Pydantic models)
    ↓ convert
Adapter
    ↓ build
Querier (conditions, orders, pagination)
    ↓ pass through
Service Layer
    ↓ delegate
Repository
    ↓ query
Database
```

### Adapter Responsibilities

**REST Adapters** convert API request DTOs to repository `Querier` objects:

```python
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import Querier

class NotificationChannelAdapter(BaseFilterAdapter):
    """Converts notification channel DTOs to Querier."""

    def build_querier(self, request: SearchNotificationChannelsReq) -> Querier:
        """Build repository query from API request."""
        conditions = []
        orders = []
        pagination = None

        # Convert filters
        if request.filter:
            conditions.extend(request.filter.build_conditions())

        # Convert ordering
        if request.order:
            orders.append(request.order.to_query_order())

        # Convert pagination
        if request.limit:
            pagination = OffsetPagination(
                limit=request.limit,
                offset=request.offset or 0
            )

        return Querier(
            conditions=conditions,
            orders=orders,
            pagination=pagination
        )
```

### Base Adapter Utilities

`BaseFilterAdapter` provides common filter conversion utilities:

```python
class BaseFilterAdapter:
    """Base adapter for common filter patterns."""

    def convert_string_filter(
        self,
        string_filter: StringFilter,
        equals_fn: Callable[[str, bool], QueryCondition],
        contains_fn: Callable[[str, bool], QueryCondition],
    ) -> Optional[QueryCondition]:
        """Convert StringFilter to QueryCondition."""
        if string_filter.equals:
            return equals_fn(string_filter.equals, False)
        elif string_filter.i_equals:
            return equals_fn(string_filter.i_equals, True)
        elif string_filter.contains:
            return contains_fn(string_filter.contains, False)
        elif string_filter.i_contains:
            return contains_fn(string_filter.i_contains, True)
        return None
```

### Handler Integration

API handlers instantiate adapters as instance fields for reuse:

```python
class NotificationAPIHandler:
    """REST API handler for notification operations."""

    def __init__(self) -> None:
        self.channel_adapter = NotificationChannelAdapter()
        self.rule_adapter = NotificationRuleAdapter()

    @api_handler
    async def search_channels(
        self,
        body: BodyParam[SearchNotificationChannelsReq],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search notification channels."""
        # Convert DTO to Querier
        querier = self.channel_adapter.build_querier(body.parsed)

        # Pass Querier through Service Layer
        channels = await processors_ctx.notification.search_channels(querier)

        return APIResponse(data=channels)
```

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

GraphQL APIs follow similar patterns using Strawberry types.

### Scope in GraphQL

**Input Types:**
```python
import strawberry


@strawberry.input
class ResourceGroupDomainScope:
    """Scope for domain-level operations in a resource group."""

    resource_group: str
    domain_name: str | None = None
```

**Resolver Usage:**
```python
@strawberry.field
async def domain_fair_shares(
    self,
    info: Info,
    scope: ResourceGroupDomainScope,
) -> list[DomainFairShareResult]:
    """Query domain fair shares within a resource group."""
    repository = info.context["repositories"].fair_share

    search_scope = DomainFairShareSearchScope(
        resource_group=scope.resource_group,
        domain_name=scope.domain_name,
    )

    result = await repository.search_domain_fair_shares(search_scope)
    return [item.to_gql() for item in result.items]
```

### Admin Check in GraphQL

**Utility Function:**
```python
from strawberry.types import Info


def check_admin_only(info: Info) -> None:
    """Check if request user is superadmin."""
    user_role = info.context["user"]["role"]
    if user_role != "superadmin":
        raise InsufficientPermission("Superadmin required")
```

**Resolver Usage:**
```python
@strawberry.mutation
async def admin_create_domain(
    self,
    info: Info,
    name: str,
    description: str | None = None,
) -> CreateDomainResult:
    """Create domain (superadmin only)."""
    check_admin_only(info)

    processors = info.context["processors"].domain
    action = CreateDomainAction(name=name, description=description)

    result = await processors.create_domain.execute(action)
    return CreateDomainResult(domain_id=result.domain_id)
```

### GraphQL Pagination

GraphQL supports cursor-based pagination (Relay spec):

```python
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@strawberry.type
class DomainFairShareConnection:
    edges: list[DomainFairShareEdge]
    page_info: PageInfo
    total_count: int


@strawberry.field
async def domain_fair_shares(
    self,
    info: Info,
    scope: ResourceGroupDomainScope,
    first: int | None = None,
    after: str | None = None,
) -> DomainFairShareConnection:
    """Query with cursor pagination."""
    offset = decode_cursor(after) if after else 0
    limit = first or 20

    result = await repository.batch_query_domain_fair_shares(
        conditions=scope.to_conditions(),
        offset=offset,
        limit=limit + 1,
    )

    has_next = len(result.items) > limit
    items = result.items[:limit]

    return DomainFairShareConnection(
        edges=[
            DomainFairShareEdge(
                cursor=encode_cursor(offset + i),
                node=item.to_gql(),
            )
            for i, item in enumerate(items)
        ],
        page_info=PageInfo(
            has_next_page=has_next,
            has_previous_page=(offset > 0),
            start_cursor=encode_cursor(offset) if items else None,
            end_cursor=encode_cursor(offset + len(items) - 1) if items else None,
        ),
        total_count=result.total_count,
    )
```

## Error Handling

Exceptions from each layer are converted to appropriate HTTP responses via Error Handling Middleware.

## Related Documentation

- [GraphQL API](./gql/README.md) - GraphQL endpoints with GQL adapters
- [Repositories Layer](../repositories/README.md) - Querier pattern and data access
- [Actions Layer](../actions/README.md) - Action Processor details
- [Services Layer](../services/README.md) - Business logic
- [Event Stream API](./events.py) - Server-Sent Events
