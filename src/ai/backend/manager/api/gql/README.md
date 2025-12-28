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

## Module Organization Pattern

The GraphQL module follows a consistent pattern for organizing code. Choose between file-based or package-based structure based on complexity.

### Decision Tree

```
Is it a simple module (1-2 entities, < 500 lines total)?
├── Yes → Use file-based: fetcher.py, resolver.py, types.py
└── No → Use package-based: fetcher/, resolver/, types/ directories
```

### File-Based Structure (Simple Modules)

For modules with 1-2 entities and less than ~500 lines total:

```
artifact/
├── __init__.py      # Public exports
├── fetcher.py       # Data loading functions
├── resolver.py      # Query/Mutation/Subscription definitions
└── types.py         # Node, Edge, Connection, Filter, Input, Payload types
```

### Package-Based Structure (Complex Modules)

For modules with 3+ entities or more complex requirements:

```
deployment/
├── __init__.py              # Public exports
├── fetcher/                 # Data loading layer
│   ├── __init__.py
│   ├── deployment.py        # fetch_deployments, fetch_deployment
│   ├── revision.py          # fetch_revisions, fetch_revision
│   ├── replica.py           # fetch_replicas, fetch_replica
│   ├── route.py             # fetch_routes, fetch_route
│   └── access_token.py      # fetch_access_tokens
├── resolver/                # GraphQL operation layer
│   ├── __init__.py
│   ├── deployment.py        # deployments query, create/update/delete mutations
│   ├── revision.py          # revisions query, add_model_revision mutation
│   ├── replica.py           # replicas query, subscription
│   ├── route.py             # routes query, update_traffic mutation
│   ├── access_token.py      # create_access_token mutation
│   └── auto_scaling.py      # auto scaling rule mutations
└── types/                   # Type definitions
    ├── __init__.py
    ├── deployment.py        # ModelDeployment, filters, inputs, payloads
    ├── revision.py          # ModelRevision, configs, filters, inputs
    ├── replica.py           # ModelReplica, status enums, filters
    ├── route.py             # Route, status enums, filters, inputs
    ├── access_token.py      # AccessToken, filters, inputs
    ├── auto_scaling.py      # AutoScalingRule, inputs
    └── policy.py            # DeploymentPolicy, strategy specs
```

### Layer Responsibilities

| Layer | Purpose | Contains |
|-------|---------|----------|
| **types/** | Type definitions | Node types, Edge/Connection, Filters, OrderBy, Input types, Payload types, Enums |
| **fetcher/** | Data loading | Pagination handling, DataLoader usage, Service layer calls, Type conversion |
| **resolver/** | GraphQL operations | Queries, Mutations, Subscriptions (thin wrappers calling fetchers) |

### Type Definition Conventions

#### Node Types (Relay)

Node types represent GraphQL entities with unique IDs:

```python
@strawberry.type
class ModelDeployment(Node):
    id: NodeID[str]
    name: str
    created_at: datetime

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            created_at=data.created_at,
        )

    @strawberry.field
    async def revisions(
        self, info: Info[StrawberryGQLContext], ...
    ) -> ModelRevisionConnection:
        # Use fetcher for nested field resolution
        return await fetch_revisions(info=info, ...)
```

#### Filter Types

Filter types inherit from `GQLFilter` and support AND/OR/NOT logical operators:

```python
@strawberry.input
class DeploymentFilter(GQLFilter):
    name: Optional[StringFilter] = None
    status: Optional[DeploymentStatusFilter] = None
    AND: Optional[list[DeploymentFilter]] = None
    OR: Optional[list[DeploymentFilter]] = None
    NOT: Optional[DeploymentFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.name:
            conditions.extend(self.name.build_conditions(...))
        if self.status:
            conditions.extend(self.status.build_conditions())
        return conditions
```

#### OrderBy Types

OrderBy types inherit from `GQLOrderBy`:

```python
@strawberry.input
class DeploymentOrderBy(GQLOrderBy):
    field: DeploymentOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case DeploymentOrderField.CREATED_AT:
                return DeploymentOrders.created_at(ascending)
            case DeploymentOrderField.NAME:
                return DeploymentOrders.name(ascending)
```

#### Input/Payload Types

```python
@strawberry.input(description="Added in 25.16.0")
class CreateDeploymentInput:
    name: str

    def to_creator(self) -> DeploymentCreator:
        return DeploymentCreator(name=self.name)

@strawberry.type
class CreateDeploymentPayload:
    deployment: ModelDeployment
```

### Fetcher Pattern

#### List Fetcher (with pagination)

```python
async def fetch_deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    base_conditions: Optional[list[QueryCondition]] = None,
) -> ModelDeploymentConnection:
    # 1. Build querier with pagination
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(first=first, after=after, ...),
        get_deployment_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,  # e.g., parent entity filter from nested field
    )

    # 2. Execute service action
    result = await processor.search_deployments.wait_for_complete(
        SearchDeploymentsAction(querier=querier)
    )

    # 3. Transform to GraphQL types
    nodes = [ModelDeployment.from_dataclass(d) for d in result.data]
    edges = [ModelDeploymentEdge(node=n, cursor=encode_cursor(str(n.id))) for n in nodes]

    # 4. Return Connection with PageInfo
    return ModelDeploymentConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
```

#### Usage from Nested Field (with base_conditions)

When calling a fetcher from a parent type's nested field, pass the parent ID filter via `base_conditions`:

```python
@strawberry.type
class ModelDeployment(Node):
    @strawberry.field
    async def routes(
        self, info: Info[StrawberryGQLContext], ...
    ) -> RouteConnection:
        # Pass parent entity filter via base_conditions
        return await fetch_routes(
            info=info,
            filter=filter,
            order_by=order_by,
            base_conditions=[RouteConditions.by_endpoint_id(UUID(self.id))],
        )
```

#### Single Item Fetcher

```python
async def fetch_deployment(
    info: Info[StrawberryGQLContext],
    deployment_id: UUID,
) -> Optional[ModelDeployment]:
    result = await processor.get_deployment_by_id.wait_for_complete(
        GetDeploymentByIdAction(deployment_id=deployment_id)
    )
    return ModelDeployment.from_dataclass(result.data)
```

### Resolver Pattern

#### Query Resolvers

Thin wrappers that delegate to fetcher functions:

```python
@strawberry.field(description="Added in 25.16.0")
async def deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    first: Optional[int] = None,
    ...
) -> ModelDeploymentConnection:
    return await fetch_deployments(
        info=info, filter=filter, order_by=order_by, first=first, ...
    )
```

#### Mutation Resolvers

```python
@strawberry.mutation(description="Added in 25.16.0")
async def create_model_deployment(
    input: CreateDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPayload:
    processor = info.context.processors.deployment
    if processor is None:
        raise ModelDeploymentUnavailable(...)

    result = await processor.create_deployment.wait_for_complete(
        CreateDeploymentAction(creator=input.to_creator())
    )
    return CreateDeploymentPayload(
        deployment=ModelDeployment.from_dataclass(result.data)
    )
```

#### Subscription Resolvers

```python
@strawberry.subscription(description="Added in 25.16.0")
async def deployment_status_changed(
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    # Connect to pub/sub system
    async for event in subscribe_to_deployment_events():
        yield DeploymentStatusChangedPayload(
            deployment=ModelDeployment.from_dataclass(event.data)
        )
```

### Pagination Specification

Create a cached pagination specification for each entity:

```python
@lru_cache(maxsize=1)
def get_deployment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentOrders.created_at(ascending=False),
        backward_order=DeploymentOrders.created_at(ascending=True),
        forward_condition_factory=DeploymentConditions.by_cursor_forward,
        backward_condition_factory=DeploymentConditions.by_cursor_backward,
    )
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
