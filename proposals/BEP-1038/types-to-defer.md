# ImageV2 GQL - Types to Defer

These types reference entities that should be represented as proper Relay Node connections. Since the corresponding Node types are not yet implemented, these fields/types should be **omitted** or use primitive types and added later.

---

## Summary

| Type/Field | Future Node | Current Action |
|------------|-------------|----------------|
| `ImageV2GQL.registry` | `ContainerRegistryNode` | Keep as string, replace later |

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

## Future Implementation PRs

| PR | Fields to Add/Modify |
|----|---------------------|
| ContainerRegistryNode PR | Replace `registry: str` with `registry: ContainerRegistryNode` connection |
