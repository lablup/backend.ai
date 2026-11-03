# ImageV2 GQL - 미룰 타입

이 타입들은 적절한 Relay Node 연결로 표현해야 하는 엔티티를 참조한다. 해당 Node 타입이 아직 구현되지 않았으므로 이 필드와 타입은 **생략**하거나 원시 타입을 사용하고 나중에 추가한다.

---

## 요약

| 타입/필드 | 향후 Node | 현재 조치 |
|------------|-------------|----------------|
| `ImageV2GQL.registry` | `ContainerRegistryNode` | string 으로 유지하고 나중에 교체 |
| `ImageIdentityInfoGQL.aliases` | 해당 없음 (DB join 필요) | 지금은 생략하고 나중에 field resolver 로 추가 |

---

## Registry 타입 (ContainerRegistryNode 로 미룸)

### ImageV2GQL.registry 필드

**현재 조치**: 원시 `str` 타입으로 유지한다.

**향후**: `ContainerRegistryNode` 연결로 교체한다.

`ContainerRegistryNode` 는 다음을 포함한다.
- `is_local`: registry 가 로컬인지 여부
- `project`: registry 안의 프로젝트 또는 image namespace

```python
# Current implementation
@strawberry.type(name="ImageV2")
class ImageV2GQL(Node):
    registry: str  # Keep as string for now

# Future implementation (after ContainerRegistryNode PR)
@strawberry.type(name="ImageV2")
class ImageV2GQL(Node):
    @strawberry.field
    async def registry(self, info: strawberry.Info) -> ContainerRegistryNode | None:
        # Load via dataloader
        ...
```

---

## Aliases 필드 (field resolver 로 미룸)

### ImageIdentityInfoGQL.aliases 필드

**현재 조치**: 최초 구현에서 생략한다.

**이유**: `aliases` 필드는 `ImageAliasRow` 와의 데이터베이스 join 이 필요하고, 이는 효율적인 batch 조회에 사용하는 기본 `ImageData` 구조에 포함되지 않는다.

**향후**: 필요할 때 aliases 를 가져오는 별도 field resolver 로 추가한다.

```python
# Future implementation
@strawberry.type(name="ImageIdentityInfo")
class ImageIdentityInfoGQL:
    canonical_name: str
    namespace: str
    architecture: str

    @strawberry.field
    async def aliases(self, info: strawberry.Info) -> list[str]:
        # Load aliases via dataloader using image_id
        ...
```

---

## 향후 구현 PR

| PR | 추가하거나 변경할 필드 |
|----|---------------------|
| ContainerRegistryNode PR | `registry: str` 을 `registry: ContainerRegistryNode` 연결로 교체 |
| Aliases PR | `ImageIdentityInfoGQL` 에 `aliases` field resolver 추가 |
