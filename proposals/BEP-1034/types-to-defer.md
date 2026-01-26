# KernelV2 GQL - Types to Defer

These types reference entities that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** and added later.

---

## Summary

For each deferred Node type, we include the **ID field immediately** (for direct fetching) and defer only the **Node connection** (for full object resolution).

| Type/Field | ID Field (Include Now) | Future Node (Defer) |
|------------|------------------------|---------------------|
| `KernelV2GQL.image` | `image_id: str` | `image: ImageNode` |
| `KernelUserPermissionInfoGQL` | `user_id: uuid.UUID` | `user: UserNode` |
| `KernelUserPermissionInfoGQL` | `access_key: str` | `keypair: KeypairNode` |
| `KernelUserPermissionInfoGQL` | `domain_name: str` | `domain: DomainNode` |
| `KernelUserPermissionInfoGQL` | `group_id: uuid.UUID` | `project: GroupNode` |
| `KernelSessionInfoGQL` | `session_id: uuid.UUID` | `session: SessionNode` |
| `KernelResourceInfoGQL` | `resource_group_name: str` | `resource_group: ResourceGroupNode` |
| `KernelRuntimeInfoGQL` | `vfolder_ids: list[uuid.UUID]` | `vfolders: list[VFolderNode]` |

### Types to Skip Entirely
| Type | Reason |
|------|--------|
| `KernelImageInfoGQL` | Replaced by `ImageNode` connection |
| `VFolderMountGQL` | Replaced by `VFolderNode` connection |

---

## Image Types (Defer to ImageNode)

### KernelImageInfoGQL

**Action**: Do not implement. Will be replaced by `ImageNode` connection.

### KernelV2GQL.image field

**Action**: Include `image_id: str | None` field now. Defer `image: ImageNode` connection.

---

## User/Auth Types (Defer to Node connections)

### KernelUserPermissionInfoGQL

This type includes ID fields immediately, with Node connections deferred:

| Field | Type | Include Now? | Future Node |
|-------|------|--------------|-------------|
| `user_id` | `uuid.UUID \| None` | Yes | `user: UserNode` |
| `access_key` | `str \| None` | Yes | `keypair: KeypairNode` |
| `domain_name` | `str \| None` | Yes | `domain: DomainNode` |
| `group_id` | `uuid.UUID \| None` | Yes | `project: GroupNode` |
| `uid` | `int \| None` | Yes | - |
| `main_gid` | `int \| None` | Yes | - |
| `gids` | `list[int] \| None` | Yes | - |

**Action**: Include all ID fields now. Defer Node connections to future PRs.

**Resulting type (current PR)**:
```python
@strawberry.type(name="KernelUserPermissionInfo")
class KernelUserPermissionInfoGQL:
    user_id: uuid.UUID | None
    access_key: str | None
    domain_name: str | None
    group_id: uuid.UUID | None
    uid: int | None
    main_gid: int | None
    gids: list[int] | None
```

**Future additions**:
- `user: UserNode | None`
- `keypair: KeypairNode | None`
- `domain: DomainNode | None`
- `project: GroupNode | None`

---

## Session Types (Defer to SessionNode)

### KernelSessionInfoGQL.session_id

**Action**: Include `session_id` field now. Defer `session: SessionNode` connection.

**Resulting type (current PR)**:
```python
@strawberry.type(name="KernelSessionInfo")
class KernelSessionInfoGQL:
    session_id: uuid.UUID | None
    creation_id: str | None
    name: str | None
    session_type: SessionTypes
```

**Future additions**:
- `session: SessionNode | None`

---

## Resource Types (Defer to Node connections)

### KernelResourceInfoGQL.resource_group

**Action**: Include `resource_group_name: str | None` field now. Defer `resource_group: ResourceGroupNode` connection.

**Future additions**:
- `resource_group: ResourceGroupNode | None`

---

## VFolder Types (Defer to VFolderNode)

### VFolderMountGQL

**Action**: Do not include in `common/types.py`. Will be replaced by `VFolderNode` connection.

### KernelRuntimeInfoGQL.vfolder_mounts

**Action**: Include `vfolder_ids: list[uuid.UUID] | None` field now. Defer `vfolders: list[VFolderNode]` connection.

**Future additions**:
- `vfolders: list[VFolderNode] | None`

---

## Future Implementation PRs

| PR | Node Connections to Add |
|----|-------------------------|
| ImageNode PR | `KernelV2GQL.image: ImageNode` |
| UserNode PR | `KernelUserPermissionInfoGQL.user: UserNode` |
| KeypairNode PR | `KernelUserPermissionInfoGQL.keypair: KeypairNode` |
| DomainNode PR | `KernelUserPermissionInfoGQL.domain: DomainNode` |
| GroupNode PR | `KernelUserPermissionInfoGQL.project: GroupNode` |
| SessionNode PR | `KernelSessionInfoGQL.session: SessionNode` |
| ResourceGroupNode PR | `KernelResourceInfoGQL.resource_group: ResourceGroupNode` |
| VFolderNode PR | `KernelRuntimeInfoGQL.vfolders: list[VFolderNode]` |
