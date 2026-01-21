# KernelV2 GQL - Types to Defer

These types reference entities that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** and added later.

---

## Summary

| Type/Field | Future Node | Action |
|------------|-------------|--------|
| `KernelImageInfoGQL` | `ImageNode` | Do not include entire type |
| `KernelV2GQL.image` | `ImageNode` | Omit field |
| `KernelUserPermissionInfoGQL.user_uuid` | `UserNode` | Omit field |
| `KernelUserPermissionInfoGQL.access_key` | `KeypairNode` | Omit field |
| `KernelUserPermissionInfoGQL.domain_name` | `DomainNode` | Omit field |
| `KernelUserPermissionInfoGQL.group_id` | `GroupNode` | Omit field |
| `KernelSessionInfoGQL.session_id` | `SessionNode` | Omit field |
| `KernelResourceInfoGQL.scaling_group` | `ScalingGroupNode` | Omit field |
| `VFolderMountGQL` | `VFolderNode` | Do not include |
| `KernelRuntimeInfoGQL.vfolder_mounts` | `VFolderNode` | Omit field |

---

## Image Types (Defer to ImageNode)

### KernelImageInfoGQL

**Action**: Do not implement. Will be replaced by `ImageNode` connection.

### KernelV2GQL.image field

**Action**: Omit this field from `KernelV2GQL`.

---

## User/Auth Types (Defer to Node connections)

### KernelUserPermissionInfoGQL

This type needs significant modification. Most fields should be deferred:

| Field | Future Node | Keep? |
|-------|-------------|-------|
| `user_uuid` | `UserNode` | No |
| `access_key` | `KeypairNode` | No |
| `domain_name` | `DomainNode` | No |
| `group_id` | `GroupNode` | No |
| `uid` | - | Yes (Unix UID, primitive) |
| `main_gid` | - | Yes (Unix GID, primitive) |
| `gids` | - | Yes (Unix GIDs, primitive) |

**Action**: Only keep `uid`, `main_gid`, `gids` fields (Unix process permissions). All entity references should be Node connections.

**Resulting type**:
```python
@strawberry.type(name="KernelUserPermissionInfo")
class KernelUserPermissionInfoGQL:
    uid: int | None
    main_gid: int | None
    gids: list[int] | None
```

---

## Session Types (Defer to SessionNode)

### KernelSessionInfoGQL.session_id

**Action**: Omit `session_id` field. The session should be accessed via `SessionNode` connection.

**Resulting type**:
```python
@strawberry.type(name="KernelSessionInfo")
class KernelSessionInfoGQL:
    creation_id: str | None
    name: str | None
    session_type: SessionTypesGQL
```

---

## Resource Types (Defer to Node connections)

### KernelResourceInfoGQL.scaling_group

**Action**: Omit `scaling_group` field. Will be replaced by `ScalingGroupNode` connection.

---

## VFolder Types (Defer to VFolderNode)

### VFolderMountGQL

**Action**: Do not include in `common/types.py`.

### KernelRuntimeInfoGQL.vfolder_mounts

**Action**: Omit `vfolder_mounts` field.

---

## Future Implementation PRs

| PR | Fields to Add |
|----|---------------|
| ImageNode PR | `KernelV2GQL.image` |
| UserNode PR | `KernelV2GQL.owner` (replaces `user_uuid`) |
| KeypairNode PR | `KernelV2GQL.keypair` (replaces `access_key`) |
| DomainNode PR | `KernelV2GQL.domain` (replaces `domain_name`) |
| GroupNode PR | `KernelV2GQL.project` (replaces `group_id`) |
| SessionNode PR | `KernelV2GQL.session` (replaces `session_id`) |
| ScalingGroupNode PR | `KernelV2GQL.scaling_group` |
| VFolderNode PR | `KernelV2GQL.mounted_vfolders` |
