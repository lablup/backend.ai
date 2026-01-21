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

## Error Handling

Exceptions from each layer are converted to appropriate HTTP responses via Error Handling Middleware.

## Related Documentation

- [GraphQL API](./gql/README.md) - GraphQL endpoints with GQL adapters
- [Repositories Layer](../repositories/README.md) - Querier pattern and data access
- [Actions Layer](../actions/README.md) - Action Processor details
- [Services Layer](../services/README.md) - Business logic
- [Event Stream API](./events.py) - Server-Sent Events
