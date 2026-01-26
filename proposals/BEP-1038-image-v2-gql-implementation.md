---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-26
Created-Version: 26.2.0
Target-Version: 26.2.0
Implemented-Version:
---

# BEP-1038: ImageV2 GQL Implementation

## Overview

This document defines the implementation plan for `ImageV2GQL` types as part of the Strawberry GraphQL migration (BEP-1010). It specifies:

1. **Types to Include** - Types that will be implemented
2. **Types to Skip** - Types replaced by other designs or deprecated
3. **Types to Defer** - Types requiring Node connections (implement later)

> **Note**: Enums are directly exposed from existing definitions. Mutations, Filters, and OrderBy types are out of scope for this BEP.

## Document Structure

| Document | Description |
|----------|-------------|
| [types-to-include.md](BEP-1038/types-to-include.md) | Detailed specifications of types to implement |
| [types-to-skip.md](BEP-1038/types-to-skip.md) | Types replaced by other designs |
| [types-to-defer.md](BEP-1038/types-to-defer.md) | Types requiring Node connections |

## Summary

### Types to Include

#### Sub-Info Types (Leaf)
- `ImageTagEntryGQL` - Tag key-value pair
- `ImageLabelEntryGQL` - Label key-value pair
- `ImageResourceLimitGQL` - Resource limit info

#### Info Types (Grouped)
- `ImageIdentityInfoGQL` - Identity info (canonical_name, namespace, architecture, aliases)
- `ImageMetadataInfoGQL` - Metadata info (tags, labels, digest, size_bytes, status, created_at)
- `ImageRequirementsInfoGQL` - Requirements info (resource_limits, supported_accelerators)
- `ImagePermissionInfoGQL` - Permission info (permissions)

#### Main Types
- `ImageV2GQL` - Main image node type
- `ImageEdgeGQL` - Edge type
- `ImageConnectionV2GQL` - Connection type

### Types to Skip (Do Not Implement)

| Type | Reason |
|------|--------|
| `Image` (legacy) | Replaced by `ImageV2GQL` with improved structure |

### Types to Defer (Node Connections)

| Type/Field | Future Node | Action |
|------------|-------------|--------|
| `ImageV2GQL.registry` | `ContainerRegistryNode` | Return primitive string for now |

## Type Structure

```
ImageV2GQL
├── id: NodeID[UUID]
│
├── identity: ImageIdentityInfoGQL       # 이미지 식별 정보
│   ├── canonical_name
│   ├── namespace
│   ├── architecture
│   └── aliases
│
├── metadata: ImageMetadataInfoGQL       # 메타데이터 정보
│   ├── tags
│   ├── labels
│   ├── digest
│   ├── size_bytes
│   ├── status
│   └── created_at
│
├── requirements: ImageRequirementsInfoGQL  # 실행 요구사항
│   ├── resource_limits
│   └── supported_accelerators
│
├── permission: ImagePermissionInfoGQL   # RBAC 권한
│   └── permissions
│
├── registry_id: UUID                    # 레지스트리 ID (직접 쿼리용)
└── registry: ContainerRegistryNode      # (deferred)
```

## Implementation Checklist

### PR Scope

- [ ] Implement all types listed in "Types to Include"
- [ ] Skip all types listed in "Types to Skip"
- [ ] Implement `from_row()` factory method for `ImageV2GQL`
- [ ] Implement connection resolver with pagination

### Future PRs

- [ ] ContainerRegistryNode PR: Replace `registry` string with connection

## References

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [BEP-1034: KernelV2 GQL Implementation](BEP-1034-kernel-v2-gql-implementation.md)
