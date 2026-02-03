# ImageV2 GQL - Types to Defer

These types reference entities that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** or use primitive types and added later.

---

## Summary

| Type/Field | Future Node | Current Action |
|------------|-------------|----------------|
| `ImageV2GQL.registry` | `ContainerRegistryNode` | Keep as string, replace later |
| `ImageIdentityInfoGQL.aliases` | N/A (requires DB join) | Omit for now, add as field resolver later |

---

## Registry Types (Defer to ContainerRegistryNode)

### ImageV2GQL.registry field

**Current Action**: Keep as primitive `str` type.

**Future**: Replace with `ContainerRegistryNode` connection.

The `ContainerRegistryNode` will include:
- `is_local`: Whether the registry is local
- `project`: Project/namespace in the registry

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

## Aliases Field (Defer to Field Resolver)

### ImageIdentityInfoGQL.aliases field

**Current Action**: Omit from initial implementation.

**Reason**: The `aliases` field requires a database join with `ImageAliasRow`, which is not included in the basic `ImageData` structure used for efficient batch queries.

**Future**: Add as a separate field resolver that loads aliases on demand.

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

## Future Implementation PRs

| PR | Fields to Add/Modify |
|----|---------------------|
| ContainerRegistryNode PR | Replace `registry: str` with `registry: ContainerRegistryNode` connection |
| Aliases PR | Add `aliases` field resolver to `ImageIdentityInfoGQL` |
