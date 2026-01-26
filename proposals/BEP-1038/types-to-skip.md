# ImageV2 GQL - Types to Skip

These types are **not to be implemented**. They have been decided to be replaced by other designs or are deprecated.

---

## Summary

| Type | Location | Reason |
|------|----------|--------|
| `Image` (legacy ObjectType) | `gql_legacy/image.py` | Replaced by `ImageV2GQL` with improved structure |

---

## Legacy Image Type

### Image (graphene.ObjectType)

**Action**: Do not implement. Replaced by `ImageV2GQL` with better structure.

**Reason**: The legacy `Image` type has several issues:
1. Flat structure without proper grouping of related fields
2. Missing proper RBAC permission field handling
3. Inconsistent naming (`name` vs `namespace`)
4. Legacy `hash` field that duplicates `digest`

The new `ImageV2GQL` type addresses these issues with:
- Proper field naming conventions
- RBAC permission integration
- Cleaner separation of concerns
