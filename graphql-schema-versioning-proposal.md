### GraphQL 스키마 버저닝 전략 변경 제안

저는 쿼리만 V2가 생기고 엔티티 타입은 슈퍼그래프로 확장된다고 생각했는데, 엔티티 타입까지 이름이 바뀌면 하위호환성이 완전히 깨져서 GraphQL fragment 활용에 심각한 문제가 됩니다. WebUI에서 Relay fragment를 적극 사용하는 상황에서 `UserNode`과 `UserV2`가 별개 타입이 되면, 사실상 프론트엔드 코드가 두 벌이 되어야 합니다. 우리는 이미 Apollo Federation v2 + Hive Gateway 기반 슈퍼그래프를 운영하고 있으므로, 이 인프라를 활용하면 엔티티 타입은 V2 없이 확장하고 쿼리만 새로운 것을 추가하는 형태로 만들 수 있습니다.

다음은 그 방법과 수정이 필요한 타입 목록을 정리한 내용입니다.

---

### 현재 문제

Strawberry 도입 시 `UserV2`, `DomainV2` 등 V2 접미사가 붙은 별도 타입을 만들고 있습니다.

```graphql
# WebUI에서 fragment가 호환되지 않음
fragment UserFields on UserNode { username, email }        # v1 전용
fragment UserFieldsV2 on UserV2 { basicInfo { ... } }      # v2 전용 — 코드 두 벌
```

### 해결 방법: Federation Entity 합성

Strawberry 서브그래프에서 `UserV2`라는 새 타입을 만드는 대신, **같은 `UserNode`이라는 이름의 Entity를 정의**합니다. Federation이 두 서브그래프의 동일 Entity를 자동으로 합쳐줍니다.

**Before (현재)**
```
Graphene 서브그래프:  UserNode  @key("id")  ← 레거시 필드
Strawberry 서브그래프: UserV2   @key("id")  ← 새 필드, 별도 타입
```

**After (제안)**
```
Graphene 서브그래프:  UserNode  @key("id")  ← 레거시 필드 (변경 없음)
Strawberry 서브그래프: UserNode  @key("id")  ← 새 필드, 같은 Entity
```

**슈퍼그래프 합성 결과:**
```graphql
type UserNode implements Node {
  # Graphene이 소유하는 기존 필드
  username: String        @join__field(graph: GRAPHENE)
  email: String           @join__field(graph: GRAPHENE)

  # Strawberry가 소유하는 새 필드
  basicInfo: UserBasicInfo    @join__field(graph: STRAWBERRY)
  security: UserSecurityInfo  @join__field(graph: STRAWBERRY)
}
```

**프론트엔드 효과:**
```graphql
# 하나의 fragment로 레거시/신규 필드 모두 사용
fragment UserFields on UserNode {
  username           # ← Graphene이 resolve
  basicInfo {        # ← Strawberry가 resolve
    fullName
  }
}

# 레거시 쿼리에서도 새 필드 접근 가능
query { user_nodes { edges { node { ...UserFields } } } }

# 새 쿼리에서도 같은 fragment 재사용
query { adminUsersV2 { edges { node { ...UserFields } } } }
```

### Connection 타입은 충돌하지 않는가?

충돌 없습니다. Connection/Edge는 Entity가 아닌 일반 타입이므로 이름만 다르면 됩니다.

| 구성요소 | Graphene | Strawberry | 충돌 |
|---------|----------|-----------|------|
| Entity | `UserNode @key("id")` | `UserNode @key("id")` | 없음 (Federation이 합침) |
| Connection | `UserConnection` | `UserNodeConnection` | 없음 (이름 다름) |
| Edge | `UserEdge` | `UserNodeEdge` | 없음 (이름 다름) |
| Query | `user_nodes` | `adminUsersV2` | 없음 (이름 다름) |

### 수정이 필요한 V2 타입 목록

아래는 레거시 Graphene에 대응하는 Entity가 있어서, **V2 접미사를 제거하고 기존 Entity 이름으로 변경해야 하는 타입들**입니다.

| 현재 V2 타입 | 변경 후 타입명 | 연관 V2 타입 (Connection/Filter 등) | 도입 버전 |
|---|---|---|---|
| `UserV2` | `UserNode` | `UserV2Connection`, `UserV2Edge`, `UserV2Filter`, `UserV2OrderBy`, `UserV2OrderField`, `UserStatusV2`, `UserRoleV2`, `UserV2BasicInfo` | 26.2.0 |
| `DomainV2` | `DomainNode` | `DomainV2Connection`, `DomainV2Edge`, `DomainV2Filter`, `DomainV2OrderBy`, `DomainV2OrderField`, `DomainBasicInfoGQL`, `DomainLifecycleInfoGQL` | 26.2.0 |
| `ProjectV2` | `GroupNode` | `ProjectV2Connection`, `ProjectV2Edge`, `ProjectV2Filter`, `ProjectV2OrderBy`, `ProjectV2OrderField`, `ProjectTypeV2` | 26.2.0 |
| `SessionV2` | `ComputeSessionNode` | `SessionV2Connection`, `SessionV2Edge`, `SessionV2Filter`, `SessionV2OrderBy`, `SessionV2OrderField`, `SessionV2Status` | 26.3.0 |
| `KernelV2` | `KernelNode` | `KernelV2Connection`, `KernelV2Edge`, `KernelV2Filter`, `KernelV2OrderBy`, `KernelV2OrderField`, `KernelV2Status` | 26.2.0 |
| `AgentV2` | `AgentNode` | `AgentV2Connection`, `AgentV2Edge`, `AgentFilterGQL`, `AgentOrderByGQL` | 26.1.0 |
| `ImageV2` | `ImageNode` | `ImageV2Connection`, `ImageV2Edge`, `ImageV2Filter`, `ImageV2OrderByGQL`, `ImageV2Status`, `ImageV2Alias`, `ImageV2AliasConnection` | 26.2.0 |
| `ContainerRegistryV2` | `ContainerRegistryNode` | (Connection 미정의) | 26.4.0 |
| `AuditLogV2` | `AuditLogNode` | `AuditLogV2Connection`, `AuditLogV2Edge` | 26.3.0 |

### 수정 불필요 — 신규 Entity (레거시 대응 없음)

아래는 Graphene에 대응하는 레거시 타입이 없는 **완전히 새로운 Entity**이므로, V2 접미사 자체를 빼고 새 이름으로 정의하면 됩니다.

| 현재 타입 | 권장 타입명 | 비고 |
|---|---|---|
| `LoginHistoryV2` | `LoginHistory` | 신규 Entity, V2 불필요 |
| `LoginSessionV2` | `LoginSession` | 신규 Entity, V2 불필요 |

### 마이그레이션 전략

1. **Strawberry의 V2 Entity를 기존 이름으로 변경** — `extend=True` 없이 독립 Entity로 등록
2. **새 필드만 Strawberry가 소유**, 기존 필드는 Graphene이 계속 소유
3. **점진적으로 `@override`로 필드 소유권을 Strawberry로 이전**
4. **Graphene 완전 제거 시** Strawberry가 모든 필드를 소유 (타입명 변화 없음)

### 참고 사항

- **camelCase vs snake_case**: Strawberry 새 필드는 `camelCase`, Graphene 기존 필드는 `snake_case`로 혼재됩니다. `@override` 이전 시 점진적으로 통일 가능합니다.
- **resolve_reference 성능**: 새 필드를 요청할 때만 Strawberry 서브그래프 추가 호출이 발생합니다. 기존 필드만 요청하면 추가 비용 없습니다.
- **쿼리 이름**: `adminUsersV2`, `domainUsersV2` 등 쿼리 이름의 V2는 유지해도 무방합니다. 쿼리는 타입이 아니므로 fragment 호환성에 영향 없습니다.

의견이나 우려 사항 있으시면 이 스레드에 남겨주세요.
