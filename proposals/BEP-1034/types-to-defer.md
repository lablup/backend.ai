# KernelV2 GQL - Types to Defer

These types reference entities (Image, User, Group, VFolder) that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented in the Strawberry API, these fields/types should be **omitted from the current PR** and added later.

---

## Summary

| Type/Field | Location | Future Node | Action |
|------------|----------|-------------|--------|
| `KernelImageInfoGQL` | `kernel/types.py` | `ImageNode` | Do not include entire type |
| `KernelV2GQL.image` | `kernel/types.py` | `ImageNode` | Omit field |
| `KernelUserPermissionInfoGQL.user_uuid` | `kernel/types.py` | `UserNode` | Omit field |
| `KernelUserPermissionInfoGQL.group_id` | `kernel/types.py` | `GroupNode` | Omit field |
| `VFolderMountGQL` | `common/types.py` | `VFolderNode` | Do not include |
| `KernelRuntimeInfoGQL.vfolder_mounts` | `kernel/types.py` | `VFolderNode` | Omit field |

---

## Image Types (Defer to ImageNode)

### KernelImageInfoGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="KernelImageInfo",
    description="Added in 26.1.0. Container image information for a kernel.",
)
class KernelImageInfoGQL:
    reference: str | None = strawberry.field(
        description="The canonical reference of the container image (e.g., registry/repo:tag)."
    )
    registry: str | None = strawberry.field(
        description="The container registry hosting the image."
    )
    tag: str | None = strawberry.field(
        description="The tag of the container image."
    )
    architecture: str | None = strawberry.field(
        description="The CPU architecture the image is built for (e.g., x86_64, aarch64)."
    )
```

**Action**: Do not implement. Will be replaced by `ImageNode` connection.

### KernelV2GQL.image field

**Original Definition** (from PR #8079):

```python
class KernelV2GQL(Node):
    # ...
    image: KernelImageInfoGQL = strawberry.field(
        description="Container image information."
    )
```

**Action**: Omit this field from `KernelV2GQL`.

**Future Design**:

```python
@strawberry.type
class KernelV2GQL(Node):
    # ...
    
    @strawberry.field(description="The container image for this kernel.")
    async def image(self, info: Info) -> ImageNode | None:
        return await info.context.loaders.image.load(self._image_ref)
```

---

## User Types (Defer to UserNode)

### KernelUserPermissionInfoGQL.user_uuid

**Original Definition** (from PR #8079):

```python
@strawberry.type(name="KernelUserPermissionInfo")
class KernelUserPermissionInfoGQL:
    user_uuid: UUID = strawberry.field(
        description="The UUID of the user who owns this kernel."
    )
    # ... other fields
```

**Action**: Omit `user_uuid` field. Keep other fields (`access_key`, `domain_name`, `uid`, `main_gid`, `gids`).

**Future Design**:

```python
@strawberry.type
class KernelV2GQL(Node):
    # ...
    
    @strawberry.field(description="The user who owns this kernel.")
    async def owner(self, info: Info) -> UserNode | None:
        return await info.context.loaders.user.load(self._user_uuid)
```

---

## Group Types (Defer to GroupNode)

### KernelUserPermissionInfoGQL.group_id

**Original Definition** (from PR #8079):

```python
@strawberry.type(name="KernelUserPermissionInfo")
class KernelUserPermissionInfoGQL:
    # ...
    group_id: UUID = strawberry.field(
        description="The group (project) ID this kernel belongs to."
    )
    # ... other fields
```

**Action**: Omit `group_id` field.

**Future Design**:

```python
@strawberry.type
class KernelV2GQL(Node):
    # ...
    
    @strawberry.field(description="The project (group) this kernel belongs to.")
    async def project(self, info: Info) -> GroupNode | None:
        return await info.context.loaders.group.load(self._group_id)
```

---

## VFolder Types (Defer to VFolderNode)

### VFolderMountGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="VFolderMount",
    description=(
        "Added in 26.1.0. Information about a mounted virtual folder. "
        "Contains mount path, permissions, and usage mode details."
    ),
)
class VFolderMountGQL:
    name: str = strawberry.field(description="Name of the virtual folder.")
    vfid: str = strawberry.field(description="Unique identifier of the virtual folder.")
    vfsubpath: str = strawberry.field(description="Subpath within the virtual folder to mount.")
    host_path: str = strawberry.field(
        description="Path on the host where the virtual folder is stored."
    )
    kernel_path: str = strawberry.field(
        description="Path inside the container where the folder is mounted."
    )
    mount_perm: MountPermissionGQL = strawberry.field(
        description="Permission level for this mount (ro, rw, wd)."
    )
    usage_mode: VFolderUsageModeGQL = strawberry.field(
        description="Usage mode of the virtual folder (general, model, data)."
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VFolderMountGQL:
        return cls(
            name=data["name"],
            vfid=str(data["vfid"]),
            vfsubpath=str(data["vfsubpath"]),
            host_path=str(data["host_path"]),
            kernel_path=str(data["kernel_path"]),
            mount_perm=MountPermissionGQL(data["mount_perm"]),
            usage_mode=VFolderUsageModeGQL(data["usage_mode"]),
        )
```

**Action**: Do not include in `common/types.py`.

### KernelRuntimeInfoGQL.vfolder_mounts

**Original Definition** (from PR #8079):

```python
@strawberry.type(name="KernelRuntimeInfo")
class KernelRuntimeInfoGQL:
    environ: list[str] | None
    vfolder_mounts: list[VFolderMountGQL] | None = strawberry.field(
        description="List of virtual folders mounted to this kernel."
    )
    bootstrap_script: str | None
    startup_command: str | None
```

**Action**: Omit `vfolder_mounts` field.

**Future Design**:

```python
@strawberry.type
class VFolderMountEdge(Edge[VFolderNode]):
    """Edge with mount-specific metadata."""
    mount_path: str = strawberry.field(
        description="Path inside the container where the folder is mounted."
    )
    mount_perm: MountPermissionGQL = strawberry.field(
        description="Permission level for this mount."
    )
    subpath: str = strawberry.field(
        description="Subpath within the virtual folder."
    )

@strawberry.type
class KernelV2GQL(Node):
    # ...
    
    @strawberry.field(description="Virtual folders mounted to this kernel.")
    async def mounted_vfolders(
        self, 
        info: Info,
        first: int | None = None,
        after: str | None = None,
    ) -> Connection[VFolderNode]:
        # Return vfolders with mount metadata on edges
        ...
```

---

## Affected Types Summary

### KernelUserPermissionInfoGQL (Modified)

```python
# BEFORE (PR #8079)
class KernelUserPermissionInfoGQL:
    user_uuid: UUID      # ← REMOVE
    access_key: str
    domain_name: str
    group_id: UUID       # ← REMOVE
    uid: int | None
    main_gid: int | None
    gids: list[int] | None

# AFTER
class KernelUserPermissionInfoGQL:
    access_key: str
    domain_name: str
    uid: int | None
    main_gid: int | None
    gids: list[int] | None
```

### KernelRuntimeInfoGQL (Modified)

```python
# BEFORE (PR #8079)
class KernelRuntimeInfoGQL:
    environ: list[str] | None
    vfolder_mounts: list[VFolderMountGQL] | None  # ← REMOVE
    bootstrap_script: str | None
    startup_command: str | None

# AFTER
class KernelRuntimeInfoGQL:
    environ: list[str] | None
    bootstrap_script: str | None
    startup_command: str | None
```

### KernelV2GQL (Modified)

```python
# BEFORE (PR #8079)
class KernelV2GQL(Node):
    id: NodeID[str]
    session: KernelSessionInfoGQL
    user_permission: KernelUserPermissionInfoGQL
    image: KernelImageInfoGQL  # ← REMOVE
    network: KernelNetworkInfoGQL
    cluster: KernelClusterInfoGQL
    resource: KernelResourceInfoGQL
    runtime: KernelRuntimeInfoGQL
    lifecycle: KernelLifecycleInfoGQL
    metrics: KernelMetricsInfoGQL
    metadata: KernelMetadataInfoGQL

# AFTER
class KernelV2GQL(Node):
    id: NodeID[str]
    session: KernelSessionInfoGQL
    user_permission: KernelUserPermissionInfoGQL
    network: KernelNetworkInfoGQL
    cluster: KernelClusterInfoGQL
    resource: KernelResourceInfoGQL
    runtime: KernelRuntimeInfoGQL
    lifecycle: KernelLifecycleInfoGQL
    metrics: KernelMetricsInfoGQL
    metadata: KernelMetadataInfoGQL
```

---

## from_kernel_info() Updates

The `from_kernel_info()` method needs to be updated:

```python
# REMOVE these lines:
image=KernelImageInfoGQL(
    reference=image_canonical,
    registry=registry,
    tag=tag,
    architecture=architecture,
),

vfolder_mounts = (
    [VFolderMountGQL.from_dict(m) for m in kernel_info.runtime.vfolder_mounts]
    if kernel_info.runtime.vfolder_mounts
    else None
)

# MODIFY KernelUserPermissionInfoGQL instantiation:
user_permission=KernelUserPermissionInfoGQL(
    # user_uuid=kernel_info.user_permission.user_uuid,  ← REMOVE
    access_key=kernel_info.user_permission.access_key,
    domain_name=kernel_info.user_permission.domain_name,
    # group_id=kernel_info.user_permission.group_id,    ← REMOVE
    uid=kernel_info.user_permission.uid,
    main_gid=kernel_info.user_permission.main_gid,
    gids=kernel_info.user_permission.gids,
),

# MODIFY KernelRuntimeInfoGQL instantiation:
runtime=KernelRuntimeInfoGQL(
    environ=kernel_info.runtime.environ,
    # vfolder_mounts=vfolder_mounts,  ← REMOVE
    bootstrap_script=kernel_info.runtime.bootstrap_script,
    startup_command=kernel_info.runtime.startup_command,
),
```

---

## Future Implementation PRs

### ImageNode PR
- Implement `ImageNode` type
- Add `image` field resolver to `KernelV2GQL`
- Add DataLoader for batch image loading

### UserNode PR
- Implement `UserNode` type
- Add `owner` field resolver to `KernelV2GQL`
- Add DataLoader for batch user loading

### GroupNode PR
- Implement `GroupNode` type
- Add `project` field resolver to `KernelV2GQL`
- Add DataLoader for batch group loading

### VFolderNode PR
- Implement `VFolderNode` type
- Implement `VFolderMountEdge` with mount metadata
- Add `mounted_vfolders` connection to `KernelV2GQL`
- Add DataLoader for batch vfolder loading
