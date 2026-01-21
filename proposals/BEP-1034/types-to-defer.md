# KernelV2 GQL - Types to Defer

These types reference entities (Image, User, Group, VFolder) that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** and added later.

---

## Summary

| Type/Field | Future Node | Action |
|------------|-------------|--------|
| `KernelImageInfoGQL` | `ImageNode` | Do not include entire type |
| `KernelV2GQL.image` | `ImageNode` | Omit field |
| `KernelUserPermissionInfoGQL.user_uuid` | `UserNode` | Omit field |
| `KernelUserPermissionInfoGQL.group_id` | `GroupNode` | Omit field |
| `VFolderMountGQL` | `VFolderNode` | Do not include |
| `KernelRuntimeInfoGQL.vfolder_mounts` | `VFolderNode` | Omit field |

---

## Image Types (Defer to ImageNode)

### KernelImageInfoGQL

**Action**: Do not implement. Will be replaced by `ImageNode` connection.

### KernelV2GQL.image field

**Action**: Omit this field from `KernelV2GQL`.

---

## User Types (Defer to UserNode)

### KernelUserPermissionInfoGQL.user_uuid

**Action**: Omit `user_uuid` field. Keep other fields (`access_key`, `domain_name`, `uid`, `main_gid`, `gids`).

---

## Group Types (Defer to GroupNode)

### KernelUserPermissionInfoGQL.group_id

**Action**: Omit `group_id` field.

---

## VFolder Types (Defer to VFolderNode)

### VFolderMountGQL

**Action**: Do not include in `common/types.py`.

### KernelRuntimeInfoGQL.vfolder_mounts

**Action**: Omit `vfolder_mounts` field.

---

## Future Implementation PRs

| PR | Action |
|----|--------|
| ImageNode PR | Add `image` connection to `KernelV2GQL` |
| UserNode PR | Add `owner` connection to `KernelV2GQL` |
| GroupNode PR | Add `project` connection to `KernelV2GQL` |
| VFolderNode PR | Add `mounted_vfolders` connection to `KernelV2GQL` |
