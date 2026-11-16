# BEP-1038: ImageV2 GQL 구현

## 개요

이 문서는 Strawberry GraphQL 이관(BEP-1010)의 일부로 `ImageV2GQL` 타입의 구현 계획을 정한다. 다음을 명시한다.

1. **포함할 타입** - 구현할 타입
2. **미룰 타입** - Node 연결이 필요한 타입(나중에 구현)

> **참고**: enum 은 기존 정의에서 직접 노출한다. Mutation, Filter, OrderBy 타입은 이 BEP 범위 밖이다.

## 문서 구조

| 문서 | 설명 |
|----------|-------------|
| [types-to-include.md](BEP-1038/types-to-include.md) | 구현할 타입의 상세 명세 |
| [types-to-defer.md](BEP-1038/types-to-defer.md) | Node 연결이 필요한 타입 |

## 요약

### 포함할 타입

#### Sub-Info 타입 (Leaf)
- `ImageTagEntryGQL` - tag key-value 쌍
- `ImageLabelEntryGQL` - label key-value 쌍
- `ImageResourceLimitGQL` - 자원 한도 정보

#### Info 타입 (그룹)
- `ImageIdentityInfoGQL` - 식별 정보(canonical_name, namespace, architecture)
- `ImageMetadataInfoGQL` - 메타데이터 정보(tags, labels, digest, size_bytes, status, created_at)
- `ImageRequirementsInfoGQL` - 요구 사항 정보(resource_limits, supported_accelerators)
- `ImagePermissionInfoGQL` - 권한 정보(permissions)

#### 주요 타입
- `ImageV2GQL` - 주요 이미지 node 타입
- `ImageEdgeGQL` - edge 타입
- `ImageConnectionV2GQL` - connection 타입

### 미룰 타입 (Node 연결)

| 타입/필드 | 향후 Node | 동작 |
|------------|-------------|--------|
| `ImageV2GQL.registry` | `ContainerRegistryNode` | 지금은 원시 string 을 반환 |

## 타입 구조

```
ImageV2GQL
├── id: NodeID[UUID]
│
├── identity: ImageIdentityInfoGQL       # Image identity information
│   ├── canonical_name
│   ├── namespace
│   └── architecture
│
├── metadata: ImageMetadataInfoGQL       # Metadata information
│   ├── tags
│   ├── labels
│   ├── digest
│   ├── size_bytes
│   ├── status
│   └── created_at
│
├── requirements: ImageRequirementsInfoGQL  # Runtime requirements
│   ├── resource_limits
│   └── supported_accelerators
│
├── permission: ImagePermissionInfoGQL   # RBAC permissions
│   └── permissions
│
├── registry_id: UUID                    # Registry ID (for direct query)
└── registry: ContainerRegistryNode      # (deferred)
```

## 구현 체크리스트

### PR 범위

- [ ] "포함할 타입"에 나열한 타입을 모두 구현한다
- [ ] 페이지네이션을 지원하는 connection resolver 를 구현한다

### 향후 PR

- [ ] ContainerRegistryNode PR: `registry` string 을 connection 으로 교체한다

## 참고

- [BEP-1010: GraphQL API Migration to Strawberry](BEP-1010-new-gql.md)
- [BEP-1034: KernelV2 GQL Implementation](BEP-1034-kernel-v2-gql-implementation.md)
