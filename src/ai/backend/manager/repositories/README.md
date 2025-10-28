# Repositories Layer

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
PostgreSQL Database
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
```

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
- `error_code`: Exception class name (e.g., `"SessionNotFound"`, `"IntegrityError"`)

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
) -> SessionRow | None:
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

## Data Access Patterns

### 1. Basic Queries

```python
async def get_session_by_id(
    self,
    session_id: SessionId,
) -> SessionInfo | None:
    """Query by session ID"""
    async with self._db.begin_readonly_session() as db_sess:
        session_row = await self._fetch_session(db_sess, session_id)
        if not session_row:
            return None
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
            status_changed_at=datetime.utcnow(),
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

    async def get_session(self, session_id: SessionId) -> SessionInfo | None:
        async with self._db.begin_readonly_session() as db_sess:
            session_row = await self._fetch_session(db_sess, session_id)
            if not session_row:
                return None
            return self._to_session_info(session_row)


class SessionCacheSource:
    """Cache data access"""
    _redis: RedisConnectionInfo
    _db_source: SessionDBSource

    def __init__(
        self,
        redis: RedisConnectionInfo,
        db_source: SessionDBSource,
    ) -> None:
        self._redis = redis
        self._db_source = db_source

    async def get_session(self, session_id: SessionId) -> SessionInfo | None:
        """Cache-first query, fall back to DB on cache miss"""
        # Check cache
        cached = await self._get_from_cache(session_id)
        if cached:
            return cached

        # Cache miss - query from DB
        session_info = await self._db_source.get_session(session_id)
        if session_info:
            await self._set_to_cache(session_id, session_info)

        return session_info


class SessionRepository:
    """Repository: orchestrates db_source and cache_source"""
    _db_source: SessionDBSource
    _cache_source: SessionCacheSource | None

    def __init__(
        self,
        db_source: SessionDBSource,
        cache_source: SessionCacheSource | None = None,
    ) -> None:
        self._db_source = db_source
        self._cache_source = cache_source

    async def get_session(self, session_id: SessionId) -> SessionInfo | None:
        """Use cache if available, otherwise use DB directly"""
        if self._cache_source:
            return await self._cache_source.get_session(session_id)
        return await self._db_source.get_session(session_id)
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
    async def get_session(self, session_id: SessionId) -> SessionInfo | None:
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
) -> SessionInfo | None:
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
) -> SessionInfo | None:
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

## References

### Related Documentation
- [Services Layer](../services/README.md)
- [Database Models](../models/README.md)

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
