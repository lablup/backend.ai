# Manager GraphQL API (Strawberry)

← [Back to Manager API](../README.md)

## Overview

Manager GraphQL API is a GraphQL interface built using the Strawberry framework.

## Architecture

```
┌──────────────────────────────────────────┐
│      Client (Web UI/SDK)                 │
└────────────────┬─────────────────────────┘
                 │
                 ↓ GraphQL Request
┌────────────────────────────────────────────┐
│        GraphQL Schema (Strawberry)         │
│                                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Query  │  │ Mutation │  │Subscript.│   │
│  └─────────┘  └──────────┘  └──────────┘   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│           Resolver Layer                   │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Data Loader Layer                  │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│       Action Processor Layer               │
└────────────────┬───────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────┐
│         Services Layer                     │
└────────────────────────────────────────────┘
```

## Key Principles

### Python Type Hints-Based
Schemas are defined based on Python type hints using the Strawberry framework.

### Using DataLoader
DataLoader is used to solve N+1 query problems.

### Service Layer Invocation
All business logic is processed through the Services Layer.

### Common Error Handling
Raise `BackendAIError` to connect to common error handling middleware.

### Real-time Subscription
Provides real-time updates via WebSocket.

## GraphQL Adapter Pattern

GraphQL adapters convert GraphQL input types to repository `Querier` objects, handling complex filtering and multiple pagination modes.

### Architecture

```
GraphQL Query/Mutation
    ↓
Resolver
    ↓ parse arguments
GraphQL Input Types (Strawberry)
    ↓ convert
GQL Adapter
    ↓ build
Querier (conditions, orders, pagination)
    ↓ pass through
Service Layer
    ↓ delegate
Repository
    ↓ query
Database
```

### GQL Adapter Responsibilities

**GraphQL Adapters** convert Strawberry input types to repository queries:

```python
from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.repositories.base import Querier

class NotificationChannelGQLAdapter(BaseGQLAdapter):
    """Converts GraphQL inputs to Querier."""

    def build_querier(
        self,
        filter: Optional[NotificationChannelFilter] = None,
        order_by: Optional[NotificationChannelOrderBy] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Querier:
        """Build Querier from GraphQL arguments."""
        conditions = []
        orders = []
        pagination = None

        # Convert complex filters (AND/OR/NOT)
        if filter:
            conditions.extend(filter.build_conditions())

        # Convert ordering
        if order_by:
            orders.append(order_by.to_query_order())

        # Handle multiple pagination modes
        pagination = self.build_pagination(
            first, after, last, before, limit, offset
        )

        return Querier(
            conditions=conditions,
            orders=orders,
            pagination=pagination
        )
```

### Base GQL Adapter Utilities

`BaseGQLAdapter` provides common pagination logic:

```python
class BaseGQLAdapter:
    """Base adapter for GraphQL query building."""

    def build_pagination(
        self,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[QueryPagination]:
        """Build pagination from GraphQL arguments.

        Supports three pagination modes:
        - Cursor forward: first + after
        - Cursor backward: last + before
        - Offset: limit + offset
        """
        if first is not None:
            return CursorForwardPagination(first=first, after=after)
        elif last is not None:
            return CursorBackwardPagination(last=last, before=before)
        elif limit is not None:
            return OffsetPagination(limit=limit, offset=offset or 0)
        return None
```

### OrderBy Pattern

GraphQL input types implement `to_query_order()` method:

```python
@strawberry.input
class NotificationChannelOrderBy:
    field: NotificationChannelOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case NotificationChannelOrderField.NAME:
                return NotificationChannelOrders.name(ascending)
            case NotificationChannelOrderField.CREATED_AT:
                return NotificationChannelOrders.created_at(ascending)
```

### Adapter Lifecycle Management

GQL adapters are created once at server startup and reused across requests:

```python
# server_gql_ctx.py
@asynccontextmanager
async def gql_adapters_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Initialize GraphQL adapters as singletons."""
    root_ctx.gql_adapters = GQLAdapters(
        notification_channel=NotificationChannelGQLAdapter(),
        notification_rule=NotificationRuleGQLAdapter(),
    )
    yield

# Resolver usage
@strawberry.field
async def notification_channels(
    info: Info[StrawberryGQLContext],
    filter: Optional[NotificationChannelFilter] = None,
    order_by: Optional[NotificationChannelOrderBy] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationChannelConnection:
    """Query notification channels."""
    # Reuse adapter from context
    querier = info.context.gql_adapters.notification_channel.build_querier(
        filter=filter,
        order_by=order_by,
        limit=limit,
        offset=offset,
    )

    # Pass Querier through Service Layer
    results = await info.context.services.notification.search_channels(querier)
    return NotificationChannelConnection(edges=results)
```

## Schema Reference

For detailed GraphQL schema information, refer to the [GraphQL Reference](../../../../docs/manager/graphql-reference) documentation.

## Related Documentation

- [Manager API Overview](../README.md) - REST API adapters
- [Repositories Layer](../../repositories/README.md) - Querier pattern
- [Legacy GraphQL (Graphene)](../../models/gql_models/README.md) - DEPRECATED
- [Services Layer](../../services/README.md)

## Migration from Graphene

Currently migrating from Graphene to Strawberry. New features are implemented in Strawberry, and existing Graphene code is gradually migrated.
