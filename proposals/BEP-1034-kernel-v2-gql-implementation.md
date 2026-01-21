---
Author: 
Status: Draft
Created: 2025-01-21
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# BEP-1034: KernelV2 GQL Implementation

## Related Issues

- Parent: BEP-1010 (GraphQL API Migration to Strawberry)

## Motivation

As part of the Strawberry GraphQL migration (BEP-1010), we need to implement `KernelV2GQL` types. This document tracks:

1. **Types to skip** - Types that will be replaced by other designs and should not be implemented
2. **Types to defer** - Types representing Node connections (Image, User, Group, VFolder) that require corresponding Node implementations first

Since the PR will be created fresh, we can simply omit these types rather than implementing and then removing them.

## Types to Skip (Do Not Implement)

The following types from the original `KernelInfoGQL` design have been decided to be replaced by other type designs. **These should be skipped entirely in the new implementation.**

### Summary Table

| Type | Reason | Replacement |
|------|--------|-------------|
| `SchedulerPredicateGQL` | Replaced by new scheduler info design | New scheduler types in common |
| `KernelStatusHistoryGQL` | Replaced by new status tracking design | TBD |
| `KernelStatusHistoryEntryGQL` | Replaced by new status tracking design | TBD |

### Details

#### SchedulerPredicateGQL

**Original Location**: `src/ai/backend/manager/api/gql/common/types.py`

```python
@strawberry.type
class SchedulerPredicateGQL:
    name: str
    msg: str | None
```

**Action**: Skip - will be replaced by new scheduler info types.

#### KernelStatusHistoryGQL / KernelStatusHistoryEntryGQL

**Original Location**: `src/ai/backend/manager/api/gql/kernel/types.py`

```python
@strawberry.type
class KernelStatusHistoryEntryGQL:
    status: str
    timestamp: datetime

@strawberry.type
class KernelStatusHistoryGQL:
    entries: list[KernelStatusHistoryEntryGQL]
```

**Action**: Skip - the status history design will be revisited with a new approach.

---

## Types to Defer (Node Connections)

The following types reference entities (Image, User, Group, VFolder) that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, **these should be deferred to a later PR**.

### Summary Table

| Type | Field(s) | Future Node | Action |
|------|----------|-------------|--------|
| `KernelImageInfoGQL` | entire type | `ImageNode` | Do not include; add when ImageNode is ready |
| `KernelUserPermissionInfoGQL` | `user_uuid` | `UserNode` | Omit field; add when UserNode is ready |
| `KernelUserPermissionInfoGQL` | `group_id` | `GroupNode` | Omit field; add when GroupNode is ready |
| `VFolderMountGQL` | `vfid` | `VFolderNode` | Do not include vfolder_mounts; add when VFolderNode is ready |

### Details

#### KernelImageInfoGQL → ImageNode

**Original Design**:
```python
@strawberry.type
class KernelImageInfoGQL:
    reference: str | None
    registry: str | None
    tag: str | None
    architecture: str | None
```

**Future Design**:
```python
@strawberry.type
class KernelV2GQL(Node):
    @strawberry.field
    async def image(self, info: Info) -> ImageNode | None:
        return await info.context.loaders.image.load(self.image_ref)
```

**Action**: Do not include `image` field in `KernelV2GQL`. Will be added when `ImageNode` is implemented.

#### KernelUserPermissionInfoGQL.user_uuid → UserNode

**Original Design**:
```python
@strawberry.type
class KernelUserPermissionInfoGQL:
    user_uuid: UUID  # ← Should be UserNode connection
    access_key: str
    domain_name: str
    group_id: UUID   # ← Should be GroupNode connection
    # ... other fields
```

**Future Design**:
```python
@strawberry.type
class KernelV2GQL(Node):
    @strawberry.field
    async def owner(self, info: Info) -> UserNode | None:
        return await info.context.loaders.user.load(self.user_uuid)
```

**Action**: 
- Omit `user_uuid` field from `KernelUserPermissionInfoGQL`
- Keep other primitive fields (`access_key`, `domain_name`, `uid`, `main_gid`, `gids`)
- Add `owner` connection when `UserNode` is implemented

#### KernelUserPermissionInfoGQL.group_id → GroupNode

**Future Design**:
```python
@strawberry.type
class KernelV2GQL(Node):
    @strawberry.field
    async def project(self, info: Info) -> GroupNode | None:
        return await info.context.loaders.group.load(self.group_id)
```

**Action**:
- Omit `group_id` field from `KernelUserPermissionInfoGQL`
- Add `project` connection when `GroupNode` is implemented

#### VFolderMountGQL → VFolderNode

**Original Design** (in `KernelRuntimeInfoGQL`):
```python
@strawberry.type
class KernelRuntimeInfoGQL:
    vfolder_mounts: list[VFolderMountGQL] | None
    # ... other fields
```

**Future Design**:
```python
@strawberry.type
class VFolderMountEdge(Edge[VFolderNode]):
    mount_path: str
    mount_perm: MountPermissionGQL
    subpath: str

@strawberry.type
class KernelV2GQL(Node):
    @strawberry.field
    async def mounted_vfolders(self, info: Info) -> Connection[VFolderNode]:
        ...
```

**Action**:
- Do not include `vfolder_mounts` field in `KernelRuntimeInfoGQL`
- Add `mounted_vfolders` connection when `VFolderNode` is implemented

---

## Implementation Checklist

### Current PR (Fresh Implementation)

**Skip these types entirely:**
- [ ] `SchedulerPredicateGQL` - do not implement
- [ ] `KernelStatusHistoryGQL` - do not implement
- [ ] `KernelStatusHistoryEntryGQL` - do not implement

**Omit these fields/types (defer to later):**
- [ ] `KernelImageInfoGQL` - do not include
- [ ] `KernelUserPermissionInfoGQL.user_uuid` - omit field
- [ ] `KernelUserPermissionInfoGQL.group_id` - omit field
- [ ] `KernelRuntimeInfoGQL.vfolder_mounts` - omit field

### Future PRs (When Node Types Are Ready)

1. **ImageNode PR**: Add `image` connection to `KernelV2GQL`
2. **UserNode PR**: Add `owner` connection to `KernelV2GQL`
3. **GroupNode PR**: Add `project` connection to `KernelV2GQL`
4. **VFolderNode PR**: Add `mounted_vfolders` connection to `KernelV2GQL`

---

## Open Questions

- Should `domain_name` in `KernelUserPermissionInfoGQL` also become a `DomainNode` connection?
- What is the new design for status history tracking?

## References

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [Relay Connection Specification](https://relay.dev/graphql/connections.htm)
- [Strawberry Relay Documentation](https://strawberry.rocks/docs/guides/relay)
