# ImageV2 GQL - Types to Include

This document lists all types to be implemented with their fields.

> **Note**: Enums (`ImageStatusGQL`, `ImagePermissionGQL`) are directly exposed from existing definitions. Mutations, Filters, and OrderBy types are out of scope for this BEP.

---

## Sub-Info Types

### ImageTagEntryGQL
```python
@strawberry.type(name="ImageTagEntry")
class ImageTagEntryGQL:
    key: str
    value: str
```

### ImageLabelEntryGQL
```python
@strawberry.type(name="ImageLabelEntry")
class ImageLabelEntryGQL:
    key: str
    value: str
```

### ImageResourceLimitGQL
```python
@strawberry.type(name="ImageResourceLimit")
class ImageResourceLimitGQL:
    key: str
    min: str
    max: str | None
```

---

## Info Types

### ImageIdentityInfoGQL
```python
@strawberry.type(name="ImageIdentityInfo")
class ImageIdentityInfoGQL:
    canonical_name: str       # Full canonical name (e.g., cr.backend.ai/stable/python:3.9)
    namespace: str            # Base image namespace (e.g., python)
    architecture: str         # CPU architecture (e.g., x86_64, aarch64)
    aliases: list[str]        # Image aliases
```

### ImageMetadataInfoGQL
```python
@strawberry.type(name="ImageMetadataInfo")
class ImageMetadataInfoGQL:
    # Manifest info
    tags: list[ImageTagEntryGQL]      # Parsed tag components (e.g., 3.9, ubuntu20.04)
    labels: list[ImageLabelEntryGQL]  # Docker labels
    digest: str | None                # Config digest (image hash)
    size_bytes: int                   # Image size in bytes

    # Lifecycle info
    status: ImageStatusGQL            # ALIVE, DELETED
    created_at: datetime | None
```

### ImageRequirementsInfoGQL
```python
@strawberry.type(name="ImageRequirementsInfo")
class ImageRequirementsInfoGQL:
    resource_limits: list[ImageResourceLimitGQL]
    supported_accelerators: list[str]
```

### ImagePermissionInfoGQL
```python
@strawberry.type(name="ImagePermissionInfo")
class ImagePermissionInfoGQL:
    permissions: list[ImagePermissionGQL]
```

---

## Main Types

### ImageV2GQL

```python
@strawberry.type(name="ImageV2")
class ImageV2GQL(Node):
    id: NodeID[UUID]

    # Sub-info types
    identity: ImageIdentityInfoGQL
    metadata: ImageMetadataInfoGQL
    requirements: ImageRequirementsInfoGQL
    permission: ImagePermissionInfoGQL | None

    # Registry
    registry_id: UUID  # For direct query without loading full registry node
    registry: str      # TODO: Replace with ContainerRegistryNode connection
```

### ImageEdgeGQL
```python
ImageEdgeGQL = Edge[ImageV2GQL]
```

### ImageConnectionV2GQL
```python
@strawberry.type(name="ImageConnectionV2")
class ImageConnectionV2GQL(Connection[ImageV2GQL]):
    count: int
```
