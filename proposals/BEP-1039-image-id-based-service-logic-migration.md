---
Author: (Author Name)
Status: Draft
Created: 2025-01-26
Created-Version: 25.1.0
Target-Version:
Implemented-Version:
---

# Image ID Based Service Logic Migration

## Related Issues

- JIRA: BA-4036

## Migration Roadmap

The Image-related ID-based migration consists of three stages:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  1. BEP-1039 (this doc)     2. BEP-1038               3. (future)          │
│  Service Logic Migration  → ImageV2 Schema Addition → API Migration        │
│  ───────────────────────    ─────────────────────     ────────────────     │
│  • Action Layer             • New GQL schema design   • Client SDK ext.    │
│  • Repository Layer         • gql_relay impl.         • CLI extension      │
│  • Cache Layer              • ID-based Query/Mutation • REST API ext.      │
│  • Internal logic change    • Coexist with legacy API • Deprecation        │
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
| `image_canonical` | `str` | `ImageRow.name` | User-friendly reference (e.g., `registry/project/image:tag`) |
| `image_id` (ImageID) | `UUID` | `ImageRow.id` | Internal DB primary key |

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

The remaining Actions will be migrated to image_id basis following these existing patterns.

## Proposed Design

### Scope of This BEP: Service Logic Migration

This BEP focuses on **Stage 1: Internal service logic migration** of the three-stage migration.

**What this BEP covers:**
- Action Layer: canonical-based → image_id-based
- Repository Layer: Add image_id-based query methods
- Cache Layer: Unify to image_id keys
- DataLoader: Add batch loading for canonical → image_id conversion
- Convert internal logic of existing API (gql_legacy) to image_id-based (maintain external interface)

**What this BEP does NOT cover:**
- New GraphQL schema → BEP-1038
- Client SDK/CLI extension → Future API migration BEP

### Goals

1. Convert **internal service logic** to `image_id` basis (this BEP scope)
2. Existing API (`gql_legacy`) receives canonical input but **internally converts to image_id immediately** for processing
3. New ID-based API to be designed in BEP-1038 (outside this BEP scope)

### New Data Flow

**Current:**
```
API (canonical) → Action (canonical) → Repository (canonical lookup) → Cache (canonical key)
```

**After migration:**
```
Legacy API (canonical)
  → ImageDataLoader (canonical → image_id conversion via SearchImagesAction)
  → Action (image_id)
  → Repository (image_id lookup)
  → Cache (image_id key)

New API (image_id) ───────────────────────────────────────────────────────────┘
  (implemented in BEP-1038)
```

### Legacy API Internal Migration (gql_legacy)

Existing GraphQL API maintains external interface but **converts canonical → image_id via ImageDataLoader before calling Action**.

#### DataLoader Pattern

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


async def load_images_by_canonicals(
    processor: ImageProcessors,
    canonicals: Sequence[tuple[str, str]],  # (canonical, architecture)
) -> list[Optional[ImageData]]:
    """Batch load images by canonical references."""
    if not canonicals:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(canonicals)),
        conditions=[ImageConditions.by_canonicals(canonicals)],
    )

    action_result = await processor.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    # Map by canonical+arch combination
    image_map = {(img.canonical, img.architecture): img for img in action_result.data}
    return [image_map.get(canonical) for canonical in canonicals]
```

```python
# api/gql/data_loader/data_loaders.py
class DataLoaders:
    @cached_property
    def image_loader(self) -> DataLoader[uuid.UUID, Optional[ImageData]]:
        return DataLoader(load_fn=partial(load_images_by_ids, self._processors.image))

    @cached_property
    def image_by_canonical_loader(
        self,
    ) -> DataLoader[tuple[str, str], Optional[ImageData]]:
        return DataLoader(
            load_fn=partial(load_images_by_canonicals, self._processors.image)
        )
```

#### Usage in API Handler

```python
# api/gql_legacy/image.py - AliasImage mutation
class AliasImage(graphene.Mutation):
    async def mutate(cls, info, target: str, alias: str, architecture: str):
        # Convert canonical → ImageData via DataLoader
        image_data = await info.context.data_loaders.image_by_canonical_loader.load(
            (target, architecture)
        )
        if image_data is None:
            raise ImageNotFoundError(target)

        # Action only receives image_id
        await AliasImageAction(image_id=image_data.id, alias=alias).execute(ctx)
```

**Conversion flow:**

```
API Handler (canonical input)
  → ImageDataLoader.load((canonical, arch))
  → SearchImagesAction call (batch processing)
  → ImageData returned
  → Action(image_id) call
```

**Conversion responsibility: DataLoader (used by caller)**

| Legacy API Input | DataLoader | Action Call |
|------------------|------------|-------------|
| `target: str` (canonical) | `image_by_canonical_loader.load()` | `AliasImageAction(image_id)` |
| `references: [str]` | `image_by_canonical_loader.load_many()` | `PreloadImageAction(image_ids)` |
| `image_canonical: str` | `image_by_canonical_loader.load()` | `ClearImageCustomResourceLimitAction(image_id)` |

### New API (BEP-1038 Scope)

New ID-based GraphQL API will be designed in [BEP-1038](BEP-1038-image-v2-gql-implementation.md).
The new API receives image_id directly, so no conversion is needed before calling Action.

### Service/Action Layer Migration

**Change existing Action signatures to image_id-based:**

| Action | Before | After |
|--------|--------|-------|
| `AliasImageAction` | `(image_canonical, architecture, alias)` | `(image_id, alias)` |
| `GetImagesAction` | `(image_canonicals)` | `(image_ids)` |
| `ClearImageCustomResourceLimitAction` | `(image_canonical, architecture)` | `(image_id)` |
| `PreloadImageAction` | `(references)` | `(image_ids)` |
| `UnloadImageAction` | `(references)` | `(image_ids)` |

**Migration strategy:**

1. **Change Action signatures**: canonical → image_id based (keep Action names)
2. **Modify callers**: API handler converts canonical → image_id via DataLoader, then calls Action
3. **Delete existing `*ByCanonicalsAction`**: Remove unnecessary canonical-based Actions

```python
# After: ai/backend/manager/services/image/actions/alias_image.py
@dataclass
class AliasImageAction:
    """Operates on image_id basis"""
    image_id: ImageID
    alias: str

    async def execute(self, ctx: ImageServiceContext) -> None:
        await ctx.image_repository.create_alias(self.image_id, self.alias)
```

```python
# After: ai/backend/manager/services/image/actions/get_images.py
@dataclass
class GetImagesAction:
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
│  ✓ Action Layer         │  ✓ New GQL schema     │  ✓ Client SDK ext.  │
│  ✓ Repository Layer     │  ✓ gql_relay impl.    │  ✓ CLI extension    │
│  ✓ Cache Layer          │                       │  ✓ REST API ext.    │
│  ✓ DataLoader addition  │                       │  ✓ Deprecation      │
└───────────────────────────────────────────────────────────────────────┘
```

## Migration / Compatibility

### Backward Compatibility

1. **No external API changes**: All existing GraphQL/REST APIs work identically
2. **Internal refactoring**: Only Action/Repository layer changes
3. **Transparent migration**: No changes from external user perspective

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

### Phase 2: DataLoader Addition

1. **ImageDataLoader implementation**
   - `load_images_by_ids()` - ID-based batch load
   - `load_images_by_canonicals()` - canonical-based batch load (for conversion)

2. **DataLoaders registration**
   - Add `DataLoaders.image_loader`
   - Add `DataLoaders.image_by_canonical_loader`

3. **SearchImagesAction implementation/extension**
   - Support `BatchQuerier`
   - `ImageConditions`-based queries

### Phase 3: Action Layer Migration

1. **Change existing Action signatures to image_id-based**
   - `AliasImageAction(image_canonical, arch, alias)` → `AliasImageAction(image_id, alias)`
   - `GetImagesAction(canonicals)` → `GetImagesAction(image_ids)`
   - `PreloadImageAction(references)` → `PreloadImageAction(image_ids)`
   - `UnloadImageAction(references)` → `UnloadImageAction(image_ids)`
   - `ClearImageCustomResourceLimitAction(canonical, arch)` → `ClearImageCustomResourceLimitAction(image_id)`

2. **Delete unnecessary Actions**
   - Delete `GetImagesByCanonicalsAction` (merged into GetImagesAction)
   - Delete `RemoveAgentFromImagesByCanonicalsAction` (use RemoveAgentFromImagesAction)

### Phase 4: API Handler Modification

1. **gql_legacy handler modification**
   - Convert via `image_by_canonical_loader` in each mutation/query
   - Call modified Action after conversion
   - No external interface changes (maintain backward compatibility)

2. **Session creation logic**
   - Use ID internally after image resolution via DataLoader in `SessionService.create_from_params()`

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
| Action/Repository | ✓ Migrate | - | - |
| Cache | ✓ Migrate | - | - |
| GraphQL schema | - | ✓ Add new | - |
| Client SDK | - | - | ✓ Extend |
| CLI | - | - | ✓ Extend |
| Legacy API Deprecation | - | - | ✓ Handle |

## References

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [BEP-1038: ImageV2 GQL Implementation](BEP-1038-image-v2-gql-implementation.md) (Stage 2: New schema addition)
- `src/ai/backend/common/types.py` - ImageID, ImageCanonical type definitions
- `src/ai/backend/manager/models/image/row.py` - ImageRow model
