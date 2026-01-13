---
Author: (author)
Status: Draft
Created: 2025-01-14
Created-Version: 25.1.0
Target-Version:
Implemented-Version:
---

# Entity Name Resolver for RBAC Entity Search API

## Related Issues

- JIRA: BA-3689

## Motivation

The RBAC system provides APIs to query available entities within a scope for role configuration. Currently, the entity search API (`POST /admin/rbac/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search`) returns only `entity_id` without the entity name. This limitation makes it difficult for UI clients to display meaningful entity information to users.

To provide entity names, we need to query different database tables based on the entity type (e.g., `users` for USER, `groups` for PROJECT, `domains` for DOMAIN). However, embedding this logic directly into the existing data layer would violate the single responsibility principle and create tight coupling between the RBAC module and various entity tables.

This BEP proposes an **Entity Name Resolver** abstraction that cleanly separates name resolution logic from the core entity search functionality, maintaining architectural integrity while enabling the desired feature.

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

```
┌─────────────────────────────────────────────────────────────────┐
│                         Handler Layer                            │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │ search_entities │───▶│ EntityNameResolverRegistry       │    │
│  │    handler      │    │   - resolve_names(entities)      │    │
│  └────────┬────────┘    └──────────────┬───────────────────┘    │
│           │                            │                         │
│           ▼                            ▼                         │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │ Service Layer   │    │ Individual Resolvers              │    │
│  │ (unchanged)     │    │   - UserNameResolver             │    │
│  └────────┬────────┘    │   - ProjectNameResolver          │    │
│           │             │   - DomainNameResolver           │    │
│           ▼             │   - VFolderNameResolver          │    │
│  ┌─────────────────┐    │   - ...                          │    │
│  │ Repository      │    └──────────────────────────────────┘    │
│  │ (unchanged)     │                                            │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ DBSource        │                                            │
│  │ (unchanged)     │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/ai/backend/manager/api/rbac/
├── entity_name_resolver/
│   ├── __init__.py          # Public exports
│   ├── abc.py               # EntityNameResolver ABC
│   ├── base.py              # TableBasedEntityNameResolver
│   ├── registry.py          # EntityNameResolverRegistry
│   └── resolvers.py         # Individual resolver implementations
├── entity_adapter.py
├── handler.py
└── ...
```

### Core Interfaces

#### Abstract Base Class (`abc.py`)

```python
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import EntityType


class EntityNameResolver(ABC):
    """Abstract interface for entity name resolution."""

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Returns the entity type this resolver handles."""
        ...

    @abstractmethod
    async def resolve_names(
        self,
        db_sess: AsyncSession,
        entity_ids: Sequence[str],
    ) -> Mapping[str, str]:
        """
        Batch resolve entity names for given IDs.

        Args:
            db_sess: Database session
            entity_ids: List of entity IDs to resolve

        Returns:
            Mapping of {entity_id: name}. Missing IDs are not included.
        """
        ...
```

#### Table-Based Default Implementation (`base.py`)

```python
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .abc import EntityNameResolver


class TableBasedEntityNameResolver(EntityNameResolver):
    """
    Default implementation for entities stored in a single table.

    Most entity types can inherit this class and only specify configuration values.
    """

    # Configuration to override in subclasses
    table_class: ClassVar[type[DeclarativeBase]]
    id_column: ClassVar[str]
    name_column: ClassVar[str]

    @classmethod
    def convert_id(cls, entity_id: str) -> Any:
        """
        Convert string entity_id to database column type.

        Default: Returns as-is (for string IDs)
        Override: For UUID or other types
        """
        return entity_id

    async def resolve_names(
        self,
        db_sess: AsyncSession,
        entity_ids: Sequence[str],
    ) -> Mapping[str, str]:
        if not entity_ids:
            return {}

        table = self.table_class
        id_col = getattr(table, self.id_column)
        name_col = getattr(table, self.name_column)

        typed_ids = [self.convert_id(eid) for eid in entity_ids]

        query = sa.select(id_col, name_col).where(id_col.in_(typed_ids))
        result = await db_sess.execute(query)

        return {str(row[0]): row[1] for row in result.fetchall()}
```

#### Individual Resolvers (`resolvers.py`)

```python
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.domain.row import DomainRow

from .base import TableBasedEntityNameResolver


class UserNameResolver(TableBasedEntityNameResolver):
    """User entity name resolver."""

    table_class = UserRow
    id_column = "uuid"
    name_column = "username"

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER

    @classmethod
    def convert_id(cls, entity_id: str) -> UUID:
        return UUID(entity_id)


class ProjectNameResolver(TableBasedEntityNameResolver):
    """Project (Group) entity name resolver."""

    table_class = GroupRow
    id_column = "id"
    name_column = "name"

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROJECT

    @classmethod
    def convert_id(cls, entity_id: str) -> UUID:
        return UUID(entity_id)


class DomainNameResolver(TableBasedEntityNameResolver):
    """Domain entity name resolver. ID is the name itself."""

    table_class = DomainRow
    id_column = "name"
    name_column = "name"

    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DOMAIN

    # No convert_id override needed - already a string
```

#### Registry (`registry.py`)

```python
from collections.abc import Mapping, Sequence
from typing import Optional

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .abc import EntityNameResolver


class EntityNameResolverRegistry:
    """
    Manages entity type resolvers and performs batch name resolution.
    """

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._resolvers: dict[EntityType, EntityNameResolver] = {}

    def register(self, resolver: EntityNameResolver) -> None:
        """Register a resolver."""
        self._resolvers[resolver.entity_type()] = resolver

    def get(self, entity_type: EntityType) -> Optional[EntityNameResolver]:
        """Get resolver for a specific entity type."""
        return self._resolvers.get(entity_type)

    async def resolve_names(
        self,
        entities: Sequence[EntityData],
    ) -> Mapping[tuple[EntityType, str], str]:
        """
        Batch resolve names for mixed entity types.

        Args:
            entities: List of EntityData (mixed types allowed)

        Returns:
            Mapping of {(entity_type, entity_id): name}
        """
        if not entities:
            return {}

        # Group by entity type
        by_type: dict[EntityType, list[str]] = {}
        for entity in entities:
            by_type.setdefault(entity.entity_type, []).append(entity.entity_id)

        result: dict[tuple[EntityType, str], str] = {}

        # Process all types in a single session for efficiency
        async with self._db.begin_readonly_session() as db_sess:
            for entity_type, entity_ids in by_type.items():
                resolver = self._resolvers.get(entity_type)
                if resolver is None:
                    continue

                names = await resolver.resolve_names(db_sess, entity_ids)
                for entity_id, name in names.items():
                    result[(entity_type, entity_id)] = name

        return result


def create_entity_name_resolver_registry(
    db: ExtendedAsyncSAEngine,
) -> EntityNameResolverRegistry:
    """Create a pre-configured registry with all resolvers."""
    from .resolvers import (
        DomainNameResolver,
        ProjectNameResolver,
        UserNameResolver,
        VFolderNameResolver,
        # ... other resolvers
    )

    registry = EntityNameResolverRegistry(db)

    registry.register(UserNameResolver())
    registry.register(ProjectNameResolver())
    registry.register(DomainNameResolver())
    registry.register(VFolderNameResolver())
    # ... register other resolvers

    return registry
```

### Updated Response DTO

```python
class EntityDTO(BaseModel):
    """DTO for entity data."""

    entity_type: EntityType = Field(description="Entity type")
    entity_id: str = Field(description="Entity ID")
    name: Optional[str] = Field(default=None, description="Entity name")  # Added
```

### Handler Integration

```python
class RBACAPIHandler:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        # ... existing code
        self._entity_name_registry = create_entity_name_resolver_registry(db)

    async def search_entities(self, ...):
        # 1. Existing: Query entity IDs
        action_result = await processors.permission_controller.search_entities.wait_for_complete(action)

        # 2. New: Batch resolve names
        name_map = await self._entity_name_registry.resolve_names(action_result.items)

        # 3. Build response with names
        entities = [
            EntityDTO(
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                name=name_map.get((item.entity_type, item.entity_id)),
            )
            for item in action_result.items
        ]

        resp = SearchEntitiesResponse(
            entities=entities,
            pagination=PaginationInfo(...),
        )
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
- **Existing Layers**: DBSource, Repository, and Service layers remain unchanged.

### Breaking Changes

None. This is a purely additive change.

### Migration Steps

1. Add `entity_name_resolver/` module with all components
2. Add optional `name` field to `EntityDTO`
3. Integrate registry into handler
4. No database migration required

## Implementation Plan

### Phase 1: Core Infrastructure

1. Create `abc.py` with `EntityNameResolver` abstract class
2. Create `base.py` with `TableBasedEntityNameResolver`
3. Create `registry.py` with `EntityNameResolverRegistry`

### Phase 2: Resolver Implementations

1. Implement resolvers for primary entity types:
   - `UserNameResolver`
   - `ProjectNameResolver`
   - `DomainNameResolver`
   - `VFolderNameResolver`
2. Implement resolvers for remaining entity types as needed

### Phase 3: API Integration

1. Update `EntityDTO` to include optional `name` field
2. Integrate `EntityNameResolverRegistry` into `RBACAPIHandler`
3. Update `search_entities` handler to resolve and include names

### Phase 4: Testing

1. Unit tests for each resolver
2. Unit tests for registry batch resolution
3. Integration tests for API endpoint

## Design Benefits

| Aspect | Benefit |
|--------|---------|
| **Extensibility** | New entity type = new resolver class + registry registration |
| **Simplicity** | Most resolvers inherit `TableBasedEntityNameResolver` with minimal config |
| **Flexibility** | Complex cases can implement `EntityNameResolver` directly |
| **Efficiency** | Single DB session for all entity types in batch |
| **Testability** | Each resolver can be unit tested independently |
| **Separation** | Existing layers (Service/Repository/DBSource) unchanged |
| **Resilience** | Name resolution failure still returns entity_id |

## Open Questions

1. **Caching**: Should we implement caching for frequently accessed entity names?
2. **Parallel Execution**: Should we use `asyncio.gather` to parallelize queries for different entity types?
3. **Lazy Loading**: Should name resolution be optional via query parameter (e.g., `?include_names=true`)?

## References

- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
