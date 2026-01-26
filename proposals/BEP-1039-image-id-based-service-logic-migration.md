---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-26
Created-Version: 26.2.0
Target-Version: 26.2.0
Implemented-Version:
---

# Image ID Based Service Logic Migration

## Migration Roadmap

The Image-related ID-based migration consists of three stages:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  1. BEP-1039 (this doc)     2. BEP-1038               3. (future)          │
│  Service Logic Migration  → ImageV2 Schema Addition → API Migration        │
│  ───────────────────────    ─────────────────────     ────────────────     │
│  • Add ById Actions         • New GQL schema design   • Client SDK ext.    │
│  • Repository Layer         • gql_relay impl.         • CLI extension      │
│  • Cache Layer              • ID-based Query/Mutation • REST API ext.      │
│  • Keep legacy Actions      • Coexist with legacy API • Deprecation        │
└────────────────────────────────────────────────────────────────────────────┘
```

## Motivation

Currently, most internal logic related to images in Backend.AI operates based on `image_canonical` (a string-form image reference, e.g., `registry/project/image:tag`).
This approach has the following problems:

1. **Performance issues**: String-based lookups are less efficient than UUID-based lookups
2. **Consistency problems**: The same image can have different canonical representations (e.g., registry domain changes, tag changes)
3. **Referential integrity**: Strings are difficult to use with foreign key constraints
4. **Cache key mismatch**: Legacy systems use canonical strings as cache keys, while newer systems use ImageID, causing inconsistency

Switching to `image_id` (UUID-based) provides:
- Immutable unique identifiers ensuring consistency
- Improved database query performance (indexing efficiency)
- Type safety (`NewType("ImageID", UUID)`)

## Current Design

### Identifier System

| Identifier | Type | Storage Location | Purpose |
|------------|------|------------------|---------|
| `image_id` (ImageID) | `UUID` | `ImageRow.id` | Internal DB primary key |
| `image_canonical` | `str` | `ImageRow.name` | User-friendly reference (e.g., `registry/project/image:tag`) |

### Current Data Flow

```
API (canonical) → Action (canonical) → Repository (canonical lookup) → Cache (canonical key)
```

### Type Definitions (Current)

```python
# ai/backend/common/types.py
ImageCanonical = NewType("ImageCanonical", str)
ImageID = NewType("ImageID", UUID)

# ai/backend/manager/data/image/types.py
class ImageIdentifier(NamedTuple):
    """Represent a tuple of image's canonical string and architecture"""
    canonical: str
    architecture: str
```

### GraphQL API (Current)

```graphql
# Query - canonical based
query {
  image(reference: "python:3.11", architecture: "x86_64") {
    id
    name
    ...
  }
}

# Mutation - canonical based
mutation {
  alias_image(target: "cr.backend.ai/stable/python:3.11", alias: "python", architecture: "x86_64") {
    ok
  }
}
```

### Session Creation (Current)

```python
# ai/backend/manager/services/session/service.py
image_row = await self._session_repository.resolve_image([
    ImageIdentifier(image, architecture),  # canonical based
    ImageAlias(image),                      # alias based
])
```

### Already ID-based Code

Some code already operates on `image_id` basis:

- `GetImageByIdAction`
- `ForgetImageByIdAction`
- `PurgeImageByIdAction`
- `RemoveAgentFromImagesAction`
- `ValkeyImageClient.add_agent_to_images(image_ids)`
- `ValkeyImageClient.remove_agent_from_images(image_ids)`
- GraphQL: `ForgetImageById`, `PurgeImageById` mutations

New ById versions of the remaining Actions will be added following these existing patterns.

## Proposed Design

### Scope of This BEP: Service Logic Migration

This BEP focuses on **Stage 1: Internal service logic migration** of the three-stage migration.

**What this BEP covers:**
- Action Layer: Add new ById Actions (keep legacy Actions unchanged)
- Repository Layer: Add image_id-based query methods
- Cache Layer: Unify to image_id keys for new ById Actions
- DataLoader: Add batch loading by image_id for new API
- New API (BEP-1038) will use ById Actions directly

**What this BEP does NOT cover:**
- New GraphQL schema → BEP-1038
- Client SDK/CLI extension → Future API migration BEP

### Goals

1. Add new **ById Actions** for `image_id`-based operations (this BEP scope)
2. Keep existing **legacy Actions unchanged** for backward compatibility with gql_legacy
3. New ID-based API (BEP-1038) will use ById Actions directly
4. Legacy Actions to be deprecated in Stage 3 (future)

### Data Flow After Migration

**Legacy API (gql_legacy) - Unchanged:**
```
Legacy API (canonical)
  → Legacy Action (canonical)
  → Repository (canonical lookup)
  → Cache (canonical key)
```

**New API (gql_relay, BEP-1038) - Uses ById Actions:**
```
New API (image_id)
  → ById Action (image_id)
  → Repository (image_id lookup)
  → Cache (image_id key)
```

Both flows coexist until legacy API deprecation in Stage 3.

### Legacy API - No Changes (gql_legacy)

Existing GraphQL API (gql_legacy) **continues to use legacy canonical-based Actions without modification**.

#### Legacy API Flow (Unchanged)

```python
# api/gql_legacy/image.py - AliasImage mutation (NO CHANGES)
class AliasImage(graphene.Mutation):
    async def mutate(cls, info, target: str, alias: str, architecture: str):
        # Continue using legacy canonical-based Action
        await AliasImageAction(
            image_canonical=target,
            architecture=architecture,
            alias=alias,
        ).execute(ctx)
```

**Legacy API flow (unchanged):**

```
Legacy API Handler (canonical input)
  → Legacy Action (canonical)
  → Repository (canonical lookup)
```

| Legacy API Input | Legacy Action Call |
|------------------|-------------------|
| `target: str` (canonical) | `AliasImageAction(image_canonical, architecture, alias)` |
| `references: [str]` | `PreloadImageAction(references)` |
| `image_canonical: str` | `ClearImageCustomResourceLimitAction(image_canonical, architecture)` |

### New API - Uses ById Actions (gql_relay, BEP-1038)

New GraphQL API (gql_relay) **uses new ById Actions directly**.

#### DataLoader Pattern for New API

Following the existing DataLoader pattern from other domains:

```python
# api/gql/data_loader/image/loader.py
async def load_images_by_ids(
    processor: ImageProcessors,
    image_ids: Sequence[uuid.UUID],
) -> list[Optional[ImageData]]:
    """Batch load images by their IDs."""
    if not image_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(image_ids)),
        conditions=[ImageConditions.by_ids(image_ids)],
    )

    action_result = await processor.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    image_map = {image.id: image for image in action_result.data}
    return [image_map.get(image_id) for image_id in image_ids]
```

```python
# api/gql/data_loader/data_loaders.py
class DataLoaders:
    @cached_property
    def image_loader(self) -> DataLoader[uuid.UUID, Optional[ImageData]]:
        return DataLoader(load_fn=partial(load_images_by_ids, self._processors.image))
```

#### Usage in New API Handler

```python
# api/gql_relay/image.py - AliasImageById mutation (NEW)
class AliasImageById(relay.Mutation):
    async def mutate(cls, info, image_id: uuid.UUID, alias: str):
        # Directly use ById Action - no conversion needed
        await AliasImageByIdAction(image_id=image_id, alias=alias).execute(ctx)
```

**New API flow:**

```
New API Handler (image_id input)
  → ById Action (image_id)
  → Repository (image_id lookup)
  → Cache (image_id key)
```

| New API Input | ById Action Call |
|---------------|-----------------|
| `image_id: UUID` | `AliasImageByIdAction(image_id, alias)` |
| `image_ids: [UUID]` | `PreloadImageByIdAction(image_ids)` |
| `image_id: UUID` | `ClearImageCustomResourceLimitByIdAction(image_id)` |

### New API (BEP-1038 Scope)

New ID-based GraphQL API will be designed in [BEP-1038](BEP-1038-image-v2-gql-implementation.md).
The new API receives image_id directly, so no conversion is needed before calling Action.

### Service/Action Layer Migration

**Add new `ById` Actions while keeping legacy Actions unchanged:**

| Legacy Action (Keep) | New ById Action |
|---------------------|-----------------|
| `AliasImageAction(image_canonical, architecture, alias)` | `AliasImageByIdAction(image_id, alias)` |
| `GetImagesAction(image_canonicals)` | `GetImagesByIdsAction(image_ids)` |
| `ClearImageCustomResourceLimitAction(image_canonical, architecture)` | `ClearImageCustomResourceLimitByIdAction(image_id)` |
| `PreloadImageAction(references)` | `PreloadImageByIdAction(image_ids)` |
| `UnloadImageAction(references)` | `UnloadImageByIdAction(image_ids)` |
| `RescanImagesAction(registry)` | `RescanImagesByIdAction(image_ids)` |
| `SetImageResourceLimitAction(image_canonical, architecture, ...)` | `SetImageResourceLimitByIdAction(image_id, ...)` |

**Migration strategy:**

1. **Add new ById Actions**: Create new Actions that accept `image_id` instead of canonical
2. **Keep legacy Actions unchanged**: Existing canonical-based Actions remain for backward compatibility with legacy API
3. **New API uses ById Actions**: BEP-1038 new GraphQL schema calls ById Actions directly
4. **Legacy API continues using legacy Actions**: No changes to gql_legacy handlers
5. **Future deprecation**: Legacy Actions will be deprecated when legacy API is removed (Stage 3)

```python
# ai/backend/manager/services/image/actions/alias_image.py

# Legacy Action - unchanged
@dataclass
class AliasImageAction:
    """Legacy: Operates on canonical basis"""
    image_canonical: str
    architecture: str
    alias: str

    async def execute(self, ctx: ImageServiceContext) -> None:
        await ctx.image_repository.create_alias_by_canonical(
            self.image_canonical, self.architecture, self.alias
        )


# New ById Action
@dataclass
class AliasImageByIdAction:
    """New: Operates on image_id basis"""
    image_id: ImageID
    alias: str

    async def execute(self, ctx: ImageServiceContext) -> None:
        await ctx.image_repository.create_alias(self.image_id, self.alias)
```

```python
# ai/backend/manager/services/image/actions/get_images.py

# Legacy Action - unchanged
@dataclass
class GetImagesAction:
    image_canonicals: list[ImageCanonical]
    load_installed_agents: bool = False
    ...


# New ById Action
@dataclass
class GetImagesByIdsAction:
    image_ids: list[ImageID]
    load_installed_agents: bool = False

    async def execute(self, ctx: ImageServiceContext) -> list[ImageWithAgentInstallStatus]:
        return await ctx.image_repository.get_images_by_ids(
            self.image_ids,
            load_installed_agents=self.load_installed_agents,
        )
```

### Repository Layer Extension

```python
# ai/backend/manager/repositories/image/repository.py
class ImageRepository:
    async def get_images_by_ids(
        self,
        image_ids: list[ImageID],
        *,
        load_installed_agents: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        ...

# ai/backend/manager/repositories/image/db_source/db_source.py
class ImageDBSource:
    async def query_images_by_ids(
        self,
        image_ids: list[ImageID],
    ) -> dict[ImageID, ImageDataWithDetails]:
        query = sa.select(ImageRow).where(ImageRow.id.in_(image_ids))
        ...
```

### Client SDK & CLI (Outside This BEP Scope)

Client SDK and CLI extension will be addressed in **Stage 3: API Migration**.
This BEP focuses only on **server internal logic migration**.

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Scope Division                               │
├───────────────────────────────────────────────────────────────────────┤
│  BEP-1039 (this doc)    │  BEP-1038             │  Future (Stage 3)   │
│  ─────────────────────  │  ──────────────────   │  ─────────────────  │
│  ✓ Add ById Actions     │  ✓ New GQL schema     │  ✓ Client SDK ext.  │
│  ✓ Repository Layer     │  ✓ gql_relay impl.    │  ✓ CLI extension    │
│  ✓ Cache Layer          │                       │  ✓ REST API ext.    │
│  ✓ DataLoader addition  │                       │  ✓ Legacy deprecate │
└───────────────────────────────────────────────────────────────────────┘
```

## Migration / Compatibility

### Backward Compatibility

1. **No external API changes**: All existing GraphQL/REST APIs work identically
2. **Additive changes only**: New ById Actions added, legacy Actions unchanged
3. **Transparent to users**: Legacy API continues to work without modification
4. **Parallel operation**: Legacy and ById Actions coexist until Stage 3 deprecation

### Cache Migration

Valkey cache key transition:

| Item | Before | After |
|------|--------|-------|
| Cache key | `image:{canonical}` | `image:{image_id}` |
| Read | Support both | ID key preferred |
| Write | - | ID key only |

**Transition period:**
- New writes use ID-based keys only
- Existing canonical keys supported for reading until TTL expiration
- Gradual transition through natural cache refresh

## Implementation Plan

This BEP focuses on **service layer migration**; API extension will proceed in BEP-1038.

### Phase 1: Repository Layer

1. **DB Source extension**
   - Implement `ImageDBSource.query_images_by_ids()`
   - Implement `ImageDBSource.query_images_by_canonicals()` (canonical+arch combination lookup)

2. **Repository extension**
   - Implement `ImageRepository.get_images_by_ids()`
   - Add `ImageConditions.by_ids()`, `ImageConditions.by_canonicals()` conditions

3. **Cache key unification**
   - Unify all `ValkeyImageClient` methods to ImageID key basis
   - Keep legacy canonical keys as read-only (during migration period)

### Phase 2: DataLoader Addition (for New API)

1. **ImageDataLoader implementation**
   - `load_images_by_ids()` - ID-based batch load for new API

2. **DataLoaders registration**
   - Add `DataLoaders.image_loader` - for gql_relay (new API)

3. **SearchImagesAction implementation/extension**
   - Support `BatchQuerier`
   - `ImageConditions`-based queries

### Phase 3: Action Layer - Add ById Actions

1. **Add new ById Actions**
   - Add `AliasImageByIdAction(image_id, alias)` - new ID-based alias creation
   - Add `GetImagesByIdsAction(image_ids)` - new ID-based image retrieval
   - Add `PreloadImageByIdAction(image_ids)` - new ID-based image preload
   - Add `UnloadImageByIdAction(image_ids)` - new ID-based image unload
   - Add `ClearImageCustomResourceLimitByIdAction(image_id)` - new ID-based resource limit clearing
   - Add `RescanImagesByIdAction(image_ids)` - new ID-based image rescan
   - Add `SetImageResourceLimitByIdAction(image_id, ...)` - new ID-based resource limit setting

2. **Keep existing legacy Actions unchanged**
   - `AliasImageAction` - remains canonical-based for legacy API
   - `GetImagesAction` - remains canonical-based for legacy API
   - `PreloadImageAction` - remains reference-based for legacy API
   - `UnloadImageAction` - remains reference-based for legacy API
   - `ClearImageCustomResourceLimitAction` - remains canonical-based for legacy API
   - `RescanImagesAction` - remains registry-based for legacy API
   - `SetImageResourceLimitAction` - remains canonical-based for legacy API

3. **Mark legacy Actions for future deprecation**
   - Add deprecation notices to legacy Actions
   - Document migration path to ById versions

### Phase 4: API Handler Separation

1. **gql_legacy handlers - NO changes required**
   - Continue using existing legacy Actions (canonical-based)
   - Existing behavior preserved without modification
   - No DataLoader conversion needed for legacy API

2. **New gql_relay handlers (BEP-1038)**
   - Use new ById Actions directly
   - Receive image_id from client, pass directly to ById Actions
   - No canonical → image_id conversion needed

3. **Session creation logic**
   - Keep existing canonical-based flow for legacy session creation API
   - New session creation API (if added) will use ById Actions

### Phase 5: Testing

1. **Unit tests**
   - DataLoader tests
   - ID-based Action tests
   - Repository method tests

2. **Integration tests**
   - Verify existing GraphQL API works identically
   - Session creation flow tests

3. **Backward compatibility tests**
   - Verify all existing canonical-based API operations

### Phase 6: Agent Protocol (Optional, Future)

1. **Agent-Manager communication**
   - Use ID for image identification
   - Agent converts to canonical when needed (for Docker operations)

### Follow-up Work (Separate BEPs)

**Stage 2: BEP-1038 (ImageV2 Schema Addition)**
- New GraphQL schema design (gql_relay based)
- ID-based Query/Mutation implementation
- Coexist with existing gql_legacy

**Stage 3: API Migration (Future BEP)**
- Client SDK extension
- CLI extension
- REST API extension
- Existing canonical-based API deprecation

## Related BEPs and Dependencies

### Three-Stage Migration Structure

| Stage | BEP | Title | Scope | Status |
|-------|-----|-------|-------|--------|
| 1 | **1039 (this doc)** | Service Logic Migration | Action, Repository, Cache | Draft |
| 2 | 1038 | ImageV2 GQL Schema Addition | New GraphQL schema | Draft |
| 3 | (future) | API Migration | SDK, CLI, REST, Deprecation | - |

### Dependencies

```
BEP-1039 ──────→ BEP-1038 ──────→ (Future API Migration)
Service logic     New schema        Client migration
(internal)        (API addition)    (deprecate legacy API)
```

### Role Division

| Item | BEP-1039 | BEP-1038 | Future |
|------|----------|----------|--------|
| ById Actions | ✓ Add new | - | - |
| Legacy Actions | Keep unchanged | - | ✓ Deprecate |
| Repository | ✓ Add ID methods | - | - |
| Cache | ✓ Add ID keys | - | - |
| GraphQL schema | - | ✓ Add new | - |
| Client SDK | - | - | ✓ Extend |
| CLI | - | - | ✓ Extend |
| Legacy API Deprecation | - | - | ✓ Handle |

## References

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [BEP-1038: ImageV2 GQL Implementation](BEP-1038-image-v2-gql-implementation.md) (Stage 2: New schema addition)
