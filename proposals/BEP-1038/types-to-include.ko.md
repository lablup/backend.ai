# ImageV2 GQL - 포함할 타입

이 문서는 구현할 모든 타입과 그 필드를 나열한다.

> **참고**: enum(`ImageStatusGQL`, `ImagePermissionGQL`)은 기존 정의에서 직접 노출한다. Mutation, Filter, OrderBy 타입은 이 BEP 범위 밖이다.

---

## Sub-Info 타입

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
    max: str
```

---

## Info 타입

### ImageIdentityInfoGQL
```python
@strawberry.type(name="ImageIdentityInfo")
class ImageIdentityInfoGQL:
    canonical_name: str       # Full canonical name (e.g., cr.backend.ai/stable/python:3.9)
    namespace: str            # Image namespace/path within the registry (e.g., stable/python)
    architecture: str         # CPU architecture (e.g., x86_64, aarch64)
```

> **참고**: `aliases` 필드는 추가 데이터베이스 join 이 필요하므로 포함하지 않는다.
> 이후 단계에서 별도 field resolver 로 추가할 수 있다.

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

## 주요 타입

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
    # registry: ContainerRegistryNode connection to be added later
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
