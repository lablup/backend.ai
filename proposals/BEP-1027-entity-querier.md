---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Draft
Created: 2026-01-14
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# Entity Querier for RBAC Entity Search API

## Related Issues

- JIRA: BA-3689

## Motivation

The RBAC system provides APIs to query available entities within a scope for role configuration. Currently, the entity search API (`POST /admin/rbac/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search`) returns only `entity_id` without the entity name. This limitation makes it difficult for UI clients to display meaningful entity information to users.

To provide entity names, we need to query different database tables based on the entity type (e.g., `users` for USER, `groups` for PROJECT, `domains` for DOMAIN). However, embedding this logic directly into the existing data layer would violate the single responsibility principle and create tight coupling between the RBAC module and various entity tables.

This BEP proposes an **Entity Querier** abstraction that extends the `association_scopes_entities` table query to include entity-specific data (such as names) by joining with appropriate entity tables.

## Current Design

### Data Flow

```
Handler → Service → Repository → DBSource
                                    ↓
                         association_scopes_entities (single table)
                                    ↓
                         EntityData(entity_type, entity_id)
```

### Current Response

```json
{
  "entities": [
    {"entity_type": "user", "entity_id": "550e8400-e29b-41d4-a716-446655440000"},
    {"entity_type": "user", "entity_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"}
  ],
  "pagination": {"total": 2, "offset": 0, "limit": 25}
}
```

### Limitation

- Entity names are stored in separate tables based on entity type
- Each entity type has different table structure and column names:

| EntityType | Table | ID Column | Name Column |
|------------|-------|-----------|-------------|
| USER | users | uuid | username |
| PROJECT | groups | id | name |
| DOMAIN | domains | name | name |
| VFOLDER | vfolders | id | name |
| IMAGE | images | id | name |
| SESSION | sessions | id | name |
| MODEL_DEPLOYMENT | endpoints | id | name |
| ... | ... | ... | ... |

## Proposed Design

### Architecture Overview

The Entity Querier is placed in the **Repository layer** and provides an abstraction for querying entities within a scope. Each entity type has its own querier implementation that joins `association_scopes_entities` with the appropriate entity table.

```
┌─────────────────────────────────────────────────────────────────┐
│  Handler                                                         │
│  └── Input validation, DTO conversion                           │
│           │                                                      │
│           ▼                                                      │
│  Service                                                         │
│  └── Business logic coordination                                │
│           │                                                      │
│           ▼                                                      │
│  Repository                                                      │
│  └── PermissionControllerRepository                             │
│       └── search_entities()                                     │
│                 │                                                │
│                 ▼                                                │
│       EntityQuerierRegistry                                     │
│       └── get_querier(entity_type)                              │
│                 │                                                │
│                 ▼                                                │
│       EntityQuerier (per entity type)                           │
│       ├── UserEntityQuerier                                     │
│       ├── ProjectEntityQuerier                                  │
│       ├── DomainEntityQuerier                                   │
│       └── ...                                                   │
│                 │                                                │
│                 ▼                                                │
│       JOIN: association_scopes_entities + entity table          │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/ai/backend/manager/repositories/permission_controller/
├── entity_querier/
│   ├── __init__.py          # Public exports
│   ├── abc.py               # EntityQuerier ABC
│   ├── base.py              # TableBasedEntityQuerier
│   ├── registry.py          # EntityQuerierRegistry
│   └── queriers/
│       ├── __init__.py
│       ├── user.py          # UserEntityQuerier
│       ├── project.py       # ProjectEntityQuerier
│       ├── domain.py        # DomainEntityQuerier
│       ├── vfolder.py       # VFolderEntityQuerier
│       └── ...
├── db_source/
│   └── db_source.py
├── repository.py
└── ...
```

### Core Interfaces

#### Abstract Base Class (`abc.py`)

```python
from abc import ABC, abstractmethod

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.permission.entity import EntityData, EntityListResult
from ai.backend.manager.repositories.base import BatchQuerier


class EntityQuerier(ABC):
    """
    Abstract interface for querying entities within a scope.

    Each entity type must implement this interface to provide
    entity-specific query logic that joins association_scopes_entities
    with the appropriate entity table.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Returns the entity type this querier handles."""
        ...

    @classmethod
    @abstractmethod
    def id_column(cls) -> sa.Column:
        """Returns the ID column of the entity table."""
        ...

    @classmethod
    @abstractmethod
    def name_column(cls) -> sa.Column:
        """Returns the name column of the entity table."""
        ...

    @abstractmethod
    async def search_in_scope(
        self,
        db_sess: AsyncSession,
        scope_type: ScopeType,
        scope_id: str,
        querier: BatchQuerier,
    ) -> EntityListResult:
        """
        Search entities within a scope.

        Queries the association_scopes_entities table joined with
        the entity-specific table to return entity data including names.
        """
        ...
```

#### Table-Based Default Implementation (`base.py`)

```python
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.data.permission.entity import EntityData, EntityListResult
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.executor import execute_batch_querier

from .abc import EntityQuerier


class TableBasedEntityQuerier(EntityQuerier):
    """
    Default implementation for entities stored in a single table.

    Joins association_scopes_entities with the entity table to fetch
    entity data including names in a single query.

    Subclasses only need to implement entity_type(), id_column(), and name_column().
    """

    async def search_in_scope(
        self,
        db_sess: AsyncSession,
        scope_type: ScopeType,
        scope_id: str,
        querier: BatchQuerier,
    ) -> EntityListResult:
        entity_type = self.entity_type()
        id_col = self.id_column()
        name_col = self.name_column()

        # Get table class from column's parent mapper
        table_class = id_col.class_

        query = (
            sa.select(
                AssociationScopesEntitiesRow.entity_id,
                name_col.label("entity_name"),
            )
            .select_from(AssociationScopesEntitiesRow)
            .join(
                table_class,
                sa.cast(AssociationScopesEntitiesRow.entity_id, id_col.type) == id_col,
            )
            .where(
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id,
                    AssociationScopesEntitiesRow.entity_type == entity_type,
                )
            )
        )

        result = await execute_batch_querier(db_sess, query, querier)

        items = [
            EntityData(
                entity_type=entity_type,
                entity_id=row.entity_id,
                name=row.entity_name,
            )
            for row in result.rows
        ]

        return EntityListResult(
            items=items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
```

#### Individual Queriers (`queriers/`)

**User Entity Querier (`queriers/user.py`)**

```python
import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.models.user import UserRow

from ..base import TableBasedEntityQuerier


class UserEntityQuerier(TableBasedEntityQuerier):
    """Entity querier for USER type."""

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER

    @classmethod
    def id_column(cls) -> sa.Column:
        return UserRow.uuid

    @classmethod
    def name_column(cls) -> sa.Column:
        return UserRow.username
```

**Project Entity Querier (`queriers/project.py`)**

```python
import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.models.group.row import GroupRow

from ..base import TableBasedEntityQuerier


class ProjectEntityQuerier(TableBasedEntityQuerier):
    """Entity querier for PROJECT type."""

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROJECT

    @classmethod
    def id_column(cls) -> sa.Column:
        return GroupRow.id

    @classmethod
    def name_column(cls) -> sa.Column:
        return GroupRow.name
```

**Domain Entity Querier (`queriers/domain.py`)**

```python
import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.models.domain.row import DomainRow

from ..base import TableBasedEntityQuerier


class DomainEntityQuerier(TableBasedEntityQuerier):
    """Entity querier for DOMAIN type. ID is the name itself."""

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DOMAIN

    @classmethod
    def id_column(cls) -> sa.Column:
        return DomainRow.name

    @classmethod
    def name_column(cls) -> sa.Column:
        return DomainRow.name
```

**Custom Querier Example (`queriers/session.py`)**

For entity types requiring custom query logic:

```python
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.permission.entity import EntityData, EntityListResult
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.executor import execute_batch_querier

from ..abc import EntityQuerier


class SessionEntityQuerier(EntityQuerier):
    """
    Entity querier for SESSION type.

    Custom implementation because session name can be in multiple columns.
    """

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    async def search_in_scope(
        self,
        db_sess: AsyncSession,
        scope_type: ScopeType,
        scope_id: str,
        querier: BatchQuerier,
    ) -> EntityListResult:
        # Use COALESCE to get name from multiple possible columns
        name_expr = sa.func.coalesce(
            SessionRow.name,
            SessionRow.session_name,
            sa.cast(SessionRow.id, sa.String),
        )

        query = (
            sa.select(
                AssociationScopesEntitiesRow.entity_id,
                name_expr.label("entity_name"),
            )
            .select_from(AssociationScopesEntitiesRow)
            .join(
                SessionRow,
                sa.cast(AssociationScopesEntitiesRow.entity_id, SessionRow.id.type)
                == SessionRow.id,
            )
            .where(
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id,
                    AssociationScopesEntitiesRow.entity_type == EntityType.SESSION,
                )
            )
        )

        result = await execute_batch_querier(db_sess, query, querier)

        items = [
            EntityData(
                entity_type=EntityType.SESSION,
                entity_id=row.entity_id,
                name=row.entity_name,
            )
            for row in result.rows
        ]

        return EntityListResult(
            items=items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
```

#### Registry (`registry.py`)

```python
from typing import assert_never

from ai.backend.common.data.permission.types import EntityType

from .abc import EntityQuerier
from .queriers.user import UserEntityQuerier
from .queriers.project import ProjectEntityQuerier
# ... other querier imports


class EntityQuerierRegistry:
    """
    Registry for entity queriers.

    Guarantees all EntityType values have a corresponding querier
    via match + assert_never (type checker catches missing cases).
    """

    def __init__(self) -> None:
        self._queriers: dict[EntityType, EntityQuerier] = {}
        for entity_type in EntityType:
            self._queriers[entity_type] = self._create_querier(entity_type)

    def _create_querier(self, entity_type: EntityType) -> EntityQuerier:
        match entity_type:
            case EntityType.USER:
                return UserEntityQuerier()
            case EntityType.PROJECT:
                return ProjectEntityQuerier()
            case EntityType.DOMAIN:
                return DomainEntityQuerier()
            # ... other cases for all EntityType values
            case _ as unreachable:
                assert_never(unreachable)

    def get(self, entity_type: EntityType) -> EntityQuerier:
        """Get querier for a specific entity type."""
        return self._queriers[entity_type]
```

### Ensuring Querier Completeness

Querier completeness is guaranteed through two layers:

#### Layer 1: Static Type Checking (`match` + `assert_never`)

```python
case _ as unreachable:
    assert_never(unreachable)  # mypy/pyright error if case missing
```

When a new `EntityType` is added, the type checker flags the missing case.

#### Layer 2: Unit Test Verification

```python
def test_all_entity_types_have_queriers() -> None:
    registry = EntityQuerierRegistry()
    for entity_type in EntityType:
        assert registry.has(entity_type), f"Missing querier for {entity_type}"
```

#### Workflow for Adding New EntityType

1. Add new value to `EntityType` enum
2. **Run type checker** → Error on `assert_never` (missing case)
3. Implement the entity querier class
4. Add case to `_create_querier()` match statement
5. **Run tests** → Verify completeness

### Data Layer Update

#### Updated EntityData (`entity.py`)

```python
from dataclasses import dataclass
from typing import Optional

from .types import EntityType


@dataclass(frozen=True)
class EntityData:
    """Information about an entity within a scope."""

    entity_type: EntityType
    entity_id: str
    name: Optional[str] = None
```

### Repository Integration

#### Updated Repository (`repository.py`)

```python
from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.permission.entity import EntityListResult
from ai.backend.manager.repositories.base import BatchQuerier

from .entity_querier.registry import EntityQuerierRegistry


class PermissionControllerRepository:
    _db_source: PermissionDBSource
    _entity_querier_registry: EntityQuerierRegistry

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._db_source = PermissionDBSource(db)
        self._entity_querier_registry = EntityQuerierRegistry()

    @permission_controller_repository_resilience.apply()
    async def search_entities(
        self,
        scope_type: ScopeType,
        scope_id: str,
        entity_type: EntityType,
        querier: BatchQuerier,
    ) -> EntityListResult:
        """Search entities within a scope with names.

        Uses the appropriate EntityQuerier for the entity type to
        query the association_scopes_entities table joined with
        the entity-specific table.

        Args:
            scope_type: The scope type to search within.
            scope_id: The scope ID to search within.
            entity_type: The type of entity to search.
            querier: BatchQuerier with pagination settings.

        Returns:
            EntityListResult with matching entities including names.
        """
        entity_querier = self._entity_querier_registry.get(entity_type)

        async with self._db.begin_readonly_session() as db_sess:
            return await entity_querier.search_in_scope(
                db_sess, scope_type, scope_id, querier
            )
```

### Updated Response DTO

```python
class EntityDTO(BaseModel):
    """DTO for entity data."""

    entity_type: EntityType = Field(description="Entity type")
    entity_id: str = Field(description="Entity ID")
    name: Optional[str] = Field(default=None, description="Entity name")
```

### Handler (Unchanged)

The handler remains thin, only responsible for input validation and DTO conversion:

```python
class RBACAPIHandler:
    async def search_entities(self, ...):
        # Input validation and action building
        action = SearchEntitiesAction(...)

        # Call service (which calls repository)
        action_result = await processors.permission_controller.search_entities.wait_for_complete(action)

        # Convert to DTO (name is already included from repository)
        entities = [
            EntityDTO(
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                name=item.name,
            )
            for item in action_result.items
        ]

        resp = SearchEntitiesResponse(entities=entities, pagination=...)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
```

### Expected Response

```json
{
  "entities": [
    {
      "entity_type": "user",
      "entity_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "alice"
    },
    {
      "entity_type": "user",
      "entity_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "bob"
    }
  ],
  "pagination": {"total": 2, "offset": 0, "limit": 25}
}
```

## Migration / Compatibility

### Backward Compatibility

- **API Response**: The `name` field is added as optional (`Optional[str]`). Clients that don't use this field will not be affected.
- **Handler Layer**: No changes required.
- **Service Layer**: No changes required (passes through enriched data).

### Breaking Changes

None. This is a purely additive change.

### Migration Steps

1. Add `entity_querier/` module under `repositories/permission_controller/`
2. Implement queriers for all `EntityType` values
3. Add optional `name` field to `EntityData`
4. Add optional `name` field to `EntityDTO`
5. Update repository to use `EntityQuerierRegistry`
6. No database migration required

## Implementation Plan

### Phase 1: Core Infrastructure

1. Create `abc.py` with `EntityQuerier` abstract class
2. Create `base.py` with `TableBasedEntityQuerier`
3. Create `registry.py` with `EntityQuerierRegistry`

### Phase 2: Querier Implementations

1. Implement queriers for primary entity types:
   - `UserEntityQuerier`
   - `ProjectEntityQuerier`
   - `DomainEntityQuerier`
   - `VFolderEntityQuerier`
2. Implement custom queriers for complex entity types:
   - `SessionEntityQuerier` (multiple name columns)
3. Implement queriers for remaining entity types as needed

### Phase 3: Integration

1. Update `EntityData` to include optional `name` field
2. Update `EntityDTO` to include optional `name` field
3. Integrate `EntityQuerierRegistry` into `PermissionControllerRepository`
4. Update `search_entities` method to use queriers

### Phase 4: Testing

1. Unit tests for each querier
2. Unit tests for registry (including completeness verification)
3. Integration tests for repository method
4. Integration tests for API endpoint
5. Querier completeness tests (`test_all_entity_types_have_queriers`)

## Design Benefits

| Aspect | Benefit |
|--------|---------|
| **Single Query** | JOIN in single query instead of separate queries |
| **Layer Separation** | Handler stays thin; Repository handles all data access |
| **Extensibility** | New entity type = new querier class + match case |
| **Simplicity** | Most queriers only implement 3 methods: `entity_type()`, `id_column()`, `name_column()` |
| **Flexibility** | Complex cases can override `search_in_scope()` directly |
| **Completeness Guarantee** | `match` + `assert_never` ensures all EntityTypes have queriers |
| **Testability** | Each querier can be unit tested independently |

## Future Extensions

The `EntityQuerier` abstraction can be extended to support:

1. **Name-based filtering**: Add filter parameter to `search_in_scope`
   ```python
   async def search_in_scope(
       self, db_sess, scope_type, scope_id, querier,
       name_filter: Optional[str] = None,  # Future
   ) -> EntityListResult:
   ```

2. **Additional entity fields**: Return more than just name
   ```python
   @dataclass
   class EntityData:
       entity_type: EntityType
       entity_id: str
       name: Optional[str] = None
       description: Optional[str] = None  # Future
       metadata: Optional[dict] = None    # Future
   ```

## Open Questions

1. **Caching**: Should we implement caching for frequently accessed entities?
2. **Parallel Execution**: For mixed entity type queries, should we parallelize?
3. **Soft-deleted entities**: Should queriers filter out soft-deleted entities?

## References

- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
