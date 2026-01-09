# Repositories Layer

← [Back to Manager](../README.md#manager-architecture-documentation) | [Architecture Overview](../../README.md#manager)

## Overview

The Repositories layer encapsulates and abstracts database access. This layer separates data access logic from business logic and is responsible for transaction management and query optimization.

## Architecture

```
Services Layer (services/)
    ↓
Repositories Layer (repositories/)  ← Current document
    ↓
Database Models (models/)
    ↓
Database
```

## Service Integration

Repositories are called from the Services Layer to perform data access operations.

**Key Principles**:
- Services do not create transactions (delegate to Repository)
- Repository instances are dependency-injected when Services are created
- Public method naming: `get_*()`, `find_*()`, `list_*()`, `create_*()`, `update_*()`, `delete_*()`, `count_*()`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│  Services Layer                                     │
│  - Execute business logic                           │
│  - Call Repository                                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Repositories Layer                   ← Current doc │
│  - Data access abstraction                          │
│  - Transaction creation and management              │
│  - Query optimization                               │
│  - Cache management                                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Database Models & PostgreSQL                       │
│  - ORM model definitions                            │
│  - Database schema                                  │
└─────────────────────────────────────────────────────┘
```

## Key Responsibilities

### 1. Data Access Abstraction
- Encapsulate database queries as Python methods
- Protect upper layers from database structure changes
- Provide consistent data access interfaces

### 2. Query Optimization
- Write efficient queries (JOIN, index utilization)
- Prevent N+1 problems
- Selectively query only necessary columns
- Perform aggregate operations in the database

### 3. Transaction Management
- Create transactions at the public method level (only one db session per public method)
- Private methods receive db session as parameter to maintain the same session
- Read-only sessions (`begin_readonly_session`)
- Write sessions (`begin_session`)

### 4. Type Safety
- Explicit type hints
- Utilize domain types (SessionId, AgentId, etc.)
- Private methods can return Row objects
- Public methods return dataclasses to prevent exposing ORM objects externally

### 5. Cache Management
- db_source: Basic data access (required)
- cache_source: Separate implementation when cache is needed (optional)
- Pattern of calling db_source on cache miss

## Design Principles

### 1. Source-Based Structure

Repositories have db_source or cache_source as fields. Database is managed by db_source, and Redis is managed by cache_source or stateful_source.

```python
class SessionDBSource:
    """DB data access"""
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_session_by_id(
        self,
        session_id: SessionId,
    ) -> Optional[SessionRow]:
        """Public method: creates session per method"""
        async with self._db.begin_readonly_session() as db_sess:
            return await self._fetch_session(db_sess, session_id)

    async def _fetch_session(
        self,
        db_sess: SASession,
        session_id: SessionId,
    ) -> Optional[SessionRow]:
        """Private method: receives session as parameter"""
        stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
        return await db_sess.scalar(stmt)


class SessionRepository:
    """Repository: orchestrates Sources"""
    _db_source: SessionDBSource
    _cache_source: Optional[SessionCacheSource]

    def __init__(
        self,
        db_source: SessionDBSource,
        cache_source: Optional[SessionCacheSource] = None,
    ) -> None:
        self._db_source = db_source
        self._cache_source = cache_source

    async def get_session(
        self,
        session_id: SessionId,
    ) -> Optional[SessionInfo]:
        """Read: cache first, fallback to DB"""
        # Check cache first
        if self._cache_source:
            cached = await self._cache_source.get_session(session_id)
            if cached:
                return cached

        # Cache miss - query from DB
        session_info = await self._db_source.get_session(session_id)

        # Update cache
        if session_info and self._cache_source:
            await self._cache_source.set_session(session_id, session_info)

        return session_info

    async def create_session(
        self,
        session_data: SessionData,
    ) -> SessionId:
        """Write: DB source handles transaction"""
        # DB source creates session
        session_id = await self._db_source.create_session(session_data)

        # Repository decides cache strategy
        # (cache invalidation or no-op)

        return session_id
```

**Pattern explanation:**

- **DBSource**: Only handles database operations. Public methods create their own sessions, private methods receive sessions as parameters.
- **CacheSource**: Only handles cache operations (no database dependency). Provides get/set methods for cached data.
- **Repository**: Orchestrates both sources. Read operations check cache first and fall back to DB on cache miss. Write operations delegate to DB source and handle cache invalidation.

**Type hint recommendation**: Using `Optional[T]` is recommended over `| None`.

### 2. Resilience Application

Repository methods apply resilience patterns to improve stability and observability.

```python
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import (
    BackoffStrategy,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.resilience import Resilience

# Define resilience policies
session_repository_resilience = Resilience(
    policies=[
        # Metric collection
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.SESSION_REPOSITORY,
            )
        ),
        # Retry policy
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class SessionDBSource:
    @session_repository_resilience.apply()
    async def get_session_by_id(
        self,
        session_id: SessionId,
    ) -> Optional[SessionRow]:
        """Method with resilience applied"""
        async with self._db.begin_readonly_session() as db_sess:
            return await self._fetch_session(db_sess, session_id)
```

**Resilience Policies:**

1. **MetricPolicy**: Automatically collect metrics for Repository method calls
   - Call count, execution time, success/failure rate, etc.

2. **RetryPolicy**: Automatic retry on transient errors
   - Max retries: 10
   - Retry interval: 0.1 seconds (FIXED strategy)
   - Excluded exceptions: `BackendAIError` (business logic errors are not retried)

### 3. Metric Collection

When the `@*_resilience.apply()` decorator is applied to Repository methods, Prometheus metrics are automatically collected by MetricPolicy.

**Collected Metrics:**

1. **backendai_layer_operation_triggered_count** (Gauge)
   - Number of currently executing operations
   - Labels: `domain`, `layer`, `operation`

2. **backendai_layer_operation_count** (Counter)
   - Total number of operation executions
   - Labels: `domain`, `layer`, `operation`, `success`

3. **backendai_layer_operation_error_count** (Counter)
   - Number of operation execution errors
   - Labels: `domain`, `layer`, `operation`, `error_code`

4. **backendai_layer_retry_count** (Counter)
   - Number of retry occurrences
   - Labels: `domain`, `layer`, `operation`

5. **backendai_layer_operation_duration_sec** (Histogram)
   - Operation execution time (seconds)
   - Labels: `domain`, `layer`, `operation`

**Label Descriptions:**
- `domain`: Domain type
  - `"repository"`: Repository layer
  - `"client"`: Client layer
  - `"valkey"`: Valkey client layer
- `layer`: Layer type (actual value examples)
  - Repository: `"session_repository"`, `"agent_repository"`, `"schedule_repository"`, etc.
  - DB Source: `"agent_db_source"`, `"schedule_db_source"`, `"scheduler_db_source"`, etc.
  - Cache Source: `"agent_cache_source"`, `"schedule_cache_source"`, etc.
- `operation`: Method name (e.g., `"get_session_by_id"`, `"create_session"`)
- `success`: `"true"` or `"false"`
- `error_code`: Error code in the format `{domain}_{operation}_{error-detail}` (e.g., `"api_parsing_invalid-parameters"`, `"user_read_not-found"`, `"session_generic_mismatch"`)

### 4. Explicit Return Types

Public methods return dataclasses, and private methods can return Row objects. Row objects are allowed in private methods only for reuse within the same query.

```python
# Public method - recommend returning dataclass
async def get_session_info(
    self,
    session_id: SessionId,
) -> SessionInfo:
    """Externally exposed methods return dataclass"""
    async with self._db.begin_readonly_session() as db_sess:
        session_row = await self._fetch_session(db_sess, session_id)

        if not session_row:
            raise SessionNotFound(session_id)

        # Convert Row to dataclass
        return SessionInfo(
            id=session_row.id,
            name=session_row.name,
            status=session_row.status,
            created_at=session_row.created_at,
        )

# Private method - can return Row
async def _fetch_session(
    self,
    db_sess: SASession,
    session_id: SessionId,
) -> Optional[SessionRow]:
    """Internal methods can return Row"""
    stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
    return await db_sess.scalar(stmt)
```

### 5. Read/Write Separation

Clearly distinguish between read-only and write operations.

```python
class SessionRepository:
    async def get_session(self, session_id: SessionId) -> SessionInfo:
        """Read-only"""
        async with self._db.begin_readonly_session() as db_sess:
            return await self._fetch_and_transform(db_sess, session_id)

    async def create_session(
        self,
        spec: SessionCreationSpec,
    ) -> SessionRow:
        """Write operation"""
        async with self._db.begin_session() as db_sess:
            session = SessionRow(
                id=uuid.uuid4(),
                name=spec.name,
                status=SessionStatus.PENDING,
                ...
            )
            db_sess.add(session)
            await db_sess.flush()
            return session
```

### 6. Single Responsibility Principle

Each Repository is responsible for only one main entity.

```python
# Good example - Clear responsibility
class SessionRepository:
    """Manages only Session entity"""
    async def get_session_by_id(self, session_id: SessionId) -> SessionInfo: ...
    async def create_session(self, spec: SessionCreationSpec) -> SessionRow: ...
    async def update_status(self, session_id: SessionId, status: SessionStatus) -> None: ...

# Bad example - Multiple entities mixed
class MixedRepository:
    """Manages Sessions, Kernels, and Agents - Unclear responsibility"""
    async def get_session_with_kernels_and_agents(self, ...): ...
```

## Querier Pattern

The Querier pattern provides a unified way to build database queries from API requests, supporting filtering, ordering, and pagination.

### Architecture

```
API Layer (adapters)
    ↓ build
Querier (conditions, orders, pagination)
    ↓ pass through
Service Layer
    ↓ delegate
Repository
    ↓ apply
SQLAlchemy Query
    ↓
Database
```

### Querier Structure

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Querier:
    """Unified query specification."""
    conditions: list[QueryCondition]  # WHERE clauses
    orders: list[QueryOrder]          # ORDER BY clauses
    pagination: Optional[QueryPagination]  # LIMIT/OFFSET or cursor


# Type aliases
QueryCondition = Callable[[], ColumnElement[bool]]
QueryOrder = Callable[[SAColumn], ColumnElement]

# Pagination strategies
@dataclass(frozen=True)
class OffsetPagination:
    limit: int
    offset: int

@dataclass(frozen=True)
class CursorForwardPagination:
    first: int
    after: str  # base64 encoded cursor

@dataclass(frozen=True)
class CursorBackwardPagination:
    last: int
    before: str  # base64 encoded cursor
```

### Condition Builders

Repository `options.py` modules provide condition builders:

```python
# repositories/notification/options.py
class NotificationChannelConditions:
    """Condition builders for notification channels."""

    @staticmethod
    def name_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        """Build name equals condition."""
        def condition() -> ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(NotificationChannelRow.name) == value.lower()
            return NotificationChannelRow.name == value
        return condition

    @staticmethod
    def name_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        """Build name contains condition."""
        def condition() -> ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(NotificationChannelRow.name).contains(value.lower())
            return NotificationChannelRow.name.contains(value)
        return condition

    @staticmethod
    def enabled_equals(value: bool) -> QueryCondition:
        """Build enabled equals condition."""
        def condition() -> ColumnElement[bool]:
            return NotificationChannelRow.enabled == value
        return condition
```

### Order Builders

```python
class NotificationChannelOrders:
    """Order builders for notification channels."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        """Order by name."""
        def order(column: SAColumn) -> ColumnElement:
            return column.asc() if ascending else column.desc()
        return lambda: order(NotificationChannelRow.name)

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        """Order by creation time."""
        def order(column: SAColumn) -> ColumnElement:
            return column.asc() if ascending else column.desc()
        return lambda: order(NotificationChannelRow.created_at)
```

### Repository Integration

Repositories accept `Querier` objects and apply them to SQLAlchemy queries:

```python
class NotificationChannelRepository:
    """Repository using Querier pattern."""

    async def search_channels(
        self,
        querier: Querier,
    ) -> list[NotificationChannelData]:
        """Search channels using Querier."""
        async with self._db.begin_readonly_session() as db_sess:
            # Build base query
            stmt = sa.select(NotificationChannelRow)

            # Apply conditions (WHERE)
            for condition in querier.conditions:
                stmt = stmt.where(condition())

            # Apply ordering (ORDER BY)
            for order in querier.orders:
                stmt = stmt.order_by(order())

            # Apply pagination (LIMIT/OFFSET or cursor)
            if querier.pagination:
                stmt = self._apply_pagination(stmt, querier.pagination)

            # Execute query
            result = await db_sess.execute(stmt)
            rows = result.scalars().all()

            # Convert to domain objects
            return [self._to_data(row) for row in rows]

    def _apply_pagination(
        self,
        stmt: Select,
        pagination: QueryPagination,
    ) -> Select:
        """Apply pagination to query."""
        if isinstance(pagination, OffsetPagination):
            return stmt.limit(pagination.limit).offset(pagination.offset)
        elif isinstance(pagination, CursorForwardPagination):
            # Decode cursor and apply
            decoded = decode_cursor(pagination.after)
            return stmt.where(row_id > decoded).limit(pagination.first)
        elif isinstance(pagination, CursorBackwardPagination):
            # Decode cursor and apply
            decoded = decode_cursor(pagination.before)
            return stmt.where(row_id < decoded).limit(pagination.last)
        return stmt
```

### Example Usage Flow

```python
# 1. API Layer: Build Querier from request
@api_handler
async def search_channels(
    body: BodyParam[SearchNotificationChannelsReq],
    processors_ctx: ProcessorsCtx,
) -> APIResponse:
    # Adapter converts DTO to Querier
    querier = adapter.build_querier(body.parsed)

    # Service layer executes query (service delegates to repository)
    results = await processors.notification.search_channels(querier)

    return APIResponse(data=results)

# 2. Adapter: Convert DTO to Querier
class NotificationChannelAdapter:
    def build_querier(self, request: SearchNotificationChannelsReq) -> Querier:
        conditions = []

        # Build conditions
        if request.filter:
            if request.filter.name:
                conditions.append(
                    NotificationChannelConditions.name_contains(
                        request.filter.name.contains
                    )
                )
            if request.filter.enabled is not None:
                conditions.append(
                    NotificationChannelConditions.enabled_equals(
                        request.filter.enabled
                    )
                )

        # Build orders
        orders = []
        if request.order:
            orders.append(request.order.to_query_order())

        # Build pagination
        pagination = None
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

# 3. Service Layer: Pass through to repository
class NotificationService:
    async def search_channels(self, querier: Querier) -> list[ChannelData]:
        """Service delegates to repository."""
        return await self._repository.search_channels(querier)

# 4. Repository: Execute query
class NotificationChannelRepository:
    async def search_channels(self, querier: Querier) -> list[ChannelData]:
        async with self._db.begin_readonly_session() as db_sess:
            stmt = sa.select(NotificationChannelRow)

            # Apply querier
            for condition in querier.conditions:
                stmt = stmt.where(condition())
            for order in querier.orders:
                stmt = stmt.order_by(order())
            if querier.pagination:
                stmt = self._apply_pagination(stmt, querier.pagination)

            result = await db_sess.execute(stmt)
            return [self._to_data(row) for row in result.scalars()]
```

### Benefits

1. **Type Safety**: Strong typing throughout the pipeline
2. **Reusability**: Condition/order builders reused across API layers
3. **Testability**: Each component can be tested independently
4. **Flexibility**: Easy to add new filters/orders without changing repository
5. **Consistency**: Uniform query building across REST and GraphQL APIs

## Data Access Patterns

### 1. Basic Queries

```python
async def get_session_by_id(
    self,
    session_id: SessionId,
) -> SessionInfo:
    """Query by session ID"""
    async with self._db.begin_readonly_session() as db_sess:
        session_row = await self._fetch_session(db_sess, session_id)
        if not session_row:
            raise SessionNotFound(session_id)
        return self._to_session_info(session_row)

async def list_by_access_key(
    self,
    access_key: AccessKey,
    limit: int = 100,
) -> list[SessionInfo]:
    """Query session list by access key"""
    async with self._db.begin_readonly_session() as db_sess:
        session_rows = await self._fetch_sessions_by_access_key(
            db_sess,
            access_key,
            limit,
        )
        return [self._to_session_info(row) for row in session_rows]
```

### 2. Data Creation

```python
async def create_session(
    self,
    spec: SessionCreationSpec,
) -> SessionRow:
    """Create session"""
    async with self._db.begin_session() as db_sess:
        session = SessionRow(
            id=uuid.uuid4(),
            name=spec.name,
            access_key=spec.access_key,
            status=SessionStatus.PENDING,
            requested_slots=spec.requested_slots,
            ...
        )
        db_sess.add(session)
        await db_sess.flush()
        return session
```

### 3. Data Updates

```python
async def update_status(
    self,
    session_id: SessionId,
    status: SessionStatus,
) -> None:
    """Update session status"""
    async with self._db.begin_session() as db_sess:
        await self._update_session_status(db_sess, session_id, status)

async def _update_session_status(
    self,
    db_sess: SASession,
    session_id: SessionId,
    status: SessionStatus,
) -> None:
    """Perform actual update"""
    stmt = (
        sa.update(SessionRow)
        .where(SessionRow.id == session_id)
        .values(
            status=status,
            status_changed_at=datetime.now(timezone.utc),
        )
    )
    await db_sess.execute(stmt)
```

### 4. Read Once, Transform Many Times

All DB queries are performed in a single private method, and transformations are processed in memory.

```python
async def get_scheduling_data(
    self,
    scaling_group: str,
) -> SchedulingData:
    """Query all data needed for scheduling"""
    # Query all data from DB at once
    async with self._db.begin_readonly_session() as db_sess:
        raw_data = await self._fetch_all_scheduling_data(
            db_sess,
            scaling_group,
        )

    # Perform transformation after closing DB connection
    return self._transform_to_scheduling_data(raw_data)

async def _fetch_all_scheduling_data(
    self,
    db_sess: SASession,
    scaling_group: str,
) -> RawSchedulingData:
    """Execute all queries in this method"""
    # Perform all queries here
    pending_sessions = await self._query_pending_sessions(db_sess, scaling_group)
    active_agents = await self._query_active_agents(db_sess, scaling_group)
    occupied_resources = await self._query_occupied_resources(db_sess)

    return RawSchedulingData(
        pending_sessions=pending_sessions,
        active_agents=active_agents,
        occupied_resources=occupied_resources,
    )

def _transform_to_scheduling_data(
    self,
    raw_data: RawSchedulingData,
) -> SchedulingData:
    """Transform data in memory"""
    # Perform transformation without DB connection
    ...
```

## Cache Pattern

### Separating DB Source and Cache Source

```python
class SessionDBSource:
    """DB data access"""
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_session(self, session_id: SessionId) -> Optional[SessionInfo]:
        async with self._db.begin_readonly_session() as db_sess:
            session_row = await self._fetch_session(db_sess, session_id)
            if not session_row:
                return None
            return self._to_session_info(session_row)


class SessionCacheSource:
    """Cache data access - only handles cache operations"""
    _redis: RedisConnectionInfo

    def __init__(self, redis: RedisConnectionInfo) -> None:
        self._redis = redis

    async def get_session(self, session_id: SessionId) -> Optional[SessionInfo]:
        """Get session from cache"""
        return await self._get_from_cache(session_id)

    async def set_session(self, session_id: SessionId, session_info: SessionInfo) -> None:
        """Store session to cache"""
        await self._set_to_cache(session_id, session_info)


class SessionRepository:
    """Repository: orchestrates db_source and cache_source"""
    _db_source: SessionDBSource
    _cache_source: SessionCacheSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        redis: RedisConnectionInfo,
    ) -> None:
        self._db_source = SessionDBSource(db)
        self._cache_source = SessionCacheSource(redis)

    async def get_session(self, session_id: SessionId) -> Optional[SessionInfo]:
        """Cache-first query, fall back to DB on cache miss"""
        # Check cache first
        cached = await self._cache_source.get_session(session_id)
        if cached:
            return cached

        # Cache miss - query from DB
        session_info = await self._db_source.get_session(session_id)
        if session_info:
            await self._cache_source.set_session(session_id, session_info)

        return session_info

    async def create_session(self, session_data: SessionData) -> SessionId:
        """Repository handles transaction and cache invalidation"""
        # DB source handles transaction internally
        session_id = await self._db_source.create_session(session_data)

        # Repository decides cache invalidation strategy
        # (no need to cache newly created session immediately)

        return session_id
```

## Error Handling

### 1. Non-existent Data

In db_source, raising exceptions is recommended over returning None.

```python
# Recommended: Raise exception
async def get_session(self, session_id: SessionId) -> SessionInfo:
    """Query session - raise exception if not found"""
    async with self._db.begin_readonly_session() as db_sess:
        session_row = await self._fetch_session(db_sess, session_id)
        if not session_row:
            raise SessionNotFound(session_id)
        return self._to_session_info(session_row)

# Optional: Use Optional only when existence is uncertain
async def find_session(self, session_id: SessionId) -> Optional[SessionInfo]:
    """Query session - return None if not found (when existence is uncertain)"""
    async with self._db.begin_readonly_session() as db_sess:
        session_row = await self._fetch_session(db_sess, session_id)
        if not session_row:
            return None
        return self._to_session_info(session_row)
```

### 2. Duplicate Data

```python
async def create_session(
    self,
    spec: SessionCreationSpec,
) -> SessionRow:
    """Create session"""
    try:
        async with self._db.begin_session() as db_sess:
            session = SessionRow(id=spec.id, name=spec.name, ...)
            db_sess.add(session)
            await db_sess.flush()
            return session

    except sa.exc.IntegrityError as e:
        if "duplicate key" in str(e):
            raise SessionAlreadyExists(spec.id) from e
        raise
```

## Type Safety

### 1. Utilize Domain Types

```python
from ai.backend.common.types import (
    SessionId,
    AgentId,
    AccessKey,
)

class SessionRepository:
    async def get_session(self, session_id: SessionId) -> Optional[SessionInfo]:
        """Use SessionId type"""
        ...

    async def list_by_access_key(
        self,
        access_key: AccessKey,
    ) -> list[SessionInfo]:
        """Use AccessKey type"""
        ...
```

### 2. Structured Input and Output

```python
@dataclass(frozen=True)
class SessionCreationSpec:
    """Session creation specification"""
    name: str
    access_key: AccessKey
    image: str
    type: SessionType
    requested_slots: ResourceSlot

@dataclass(frozen=True)
class SessionInfo:
    """Session information (for external exposure)"""
    id: SessionId
    name: str
    status: SessionStatus
    created_at: datetime
    requested_slots: ResourceSlot

async def create_session(
    self,
    spec: SessionCreationSpec,
) -> SessionRow:
    """Structured input type"""
    ...

async def get_session(
    self,
    session_id: SessionId,
) -> Optional[SessionInfo]:
    """Structured output type (public method)"""
    ...
```

## Testing Strategy

### Repository Unit Testing

DB fixtures for testing are created as fixture methods for each test class and used only in that file.

```python
# tests/manager/repositories/test_session_repository.py
class TestSessionRepository:
    """SessionRepository tests"""

    @pytest.fixture
    async def session_db_source(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> SessionDBSource:
        """Fixture dedicated to this test class"""
        return SessionDBSource(database_engine)

    @pytest.fixture
    async def session_repository(
        self,
        session_db_source: SessionDBSource,
    ) -> SessionRepository:
        """Fixture dedicated to this test class"""
        return SessionRepository(db_source=session_db_source)

    async def test_create_session(
        self,
        session_repository: SessionRepository,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Session creation test"""
        # Given
        spec = SessionCreationSpec(
            name="test-session",
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            image="python:3.11",
            type=SessionType.INTERACTIVE,
            requested_slots=ResourceSlot(...),
        )

        # When
        session = await session_repository.create_session(spec)

        # Then
        assert session.id is not None
        assert session.name == "test-session"
        assert session.status == SessionStatus.PENDING

        # Cleanup
        async with database_engine.begin_session() as db_sess:
            await db_sess.delete(session)
```

## Best Practices

### 1. Method Structuring

```python
class SessionRepository:
    # Public method: transaction management and transformation
    async def get_session_with_dependencies(
        self,
        session_id: SessionId,
    ) -> SessionWithDependencies:
        """Query session with dependencies"""
        async with self._db.begin_readonly_session() as db_sess:
            raw_data = await self._fetch_session_and_dependencies(
                db_sess,
                session_id,
            )

        # Transform after closing DB connection
        return self._transform_to_session_with_dependencies(raw_data)

    # Private method: perform actual queries
    async def _fetch_session_and_dependencies(
        self,
        db_sess: SASession,
        session_id: SessionId,
    ) -> RawSessionData:
        """Query raw data from DB"""
        session = await self._fetch_session(db_sess, session_id)
        kernels = await self._fetch_kernels(db_sess, session_id)
        vfolders = await self._fetch_vfolders(db_sess, session_id)

        return RawSessionData(
            session=session,
            kernels=kernels,
            vfolders=vfolders,
        )

    # Private method: data transformation
    def _transform_to_session_with_dependencies(
        self,
        raw_data: RawSessionData,
    ) -> SessionWithDependencies:
        """Transform raw data to domain model"""
        ...
```

### 2. Clear Naming

```python
# Good examples
async def get_session_by_id(
    self,
    session_id: SessionId,
) -> Optional[SessionInfo]:
    """Query session by ID"""
    ...

async def list_sessions_by_access_key(
    self,
    access_key: AccessKey,
) -> list[SessionInfo]:
    """Query session list by access key"""
    ...

async def count_active_sessions_by_scaling_group(
    self,
    scaling_group: str,
) -> int:
    """Count active sessions in scaling group"""
    ...

# Bad examples
async def get(self, id: str) -> Any:
    """Ambiguous name"""
    ...

async def fetch(self, params: dict) -> list:
    """Unclear intent"""
    ...
```

## Repository-Specific Documentation

### Specialized Repositories
- **[Metric Repository](./metric/README.md)**: Container metrics data access
  - Prometheus metric querying
  - Time-series data retrieval
  - Metric aggregation patterns

## References

### Related Documentation
- [Services Layer](../services/README.md): Business logic patterns and service implementation
- [Sokovan Orchestration](../sokovan/README.md): Session scheduling and orchestration
- [Manager Overview](../README.md): Manager component architecture

### Query Optimization Guide
- N+1 problem resolution: Use JOIN or separate queries
- Partial column selection: Query only necessary columns
- Aggregate operations: Perform in DB (except JSONB types)
- Batch operations: Process multiple rows at once
- Read once, transform many times: Perform DB queries in one place

### Transaction Guide
- Read-only: `begin_readonly_session()`
- Write operations: `begin_session()`
- Public method: Create and manage transactions
- Private method: Receive and use session parameter
- Short transactions: Close quickly after querying data
