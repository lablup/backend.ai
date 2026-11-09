# 엔티티 Edge 카탈로그

이 문서는 BEP-1048 3타입 모델의 모든 엔티티 edge 에 대한 기준 참고 문서다.
`auto`, `ref`, `guarded` 의 정의는 [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md)을 본다.

## Edge 의미 요약

| 타입 | 권한 | 저장 | Scope chain |
|------|-----------|---------|-------------|
| `auto` | role 권한 전달 | `association_scopes_entities` (`relation_type=auto`) | CTE 상향 순회, 자손 scope 에서 부모 scope 매핑 조회 |
| `ref` | 읽기 전용 (CUD 위임 없음) | `association_scopes_entities` (`relation_type=ref`) | 읽기 전용 제약이 있는 CTE 상향 순회 |
| `guarded` | 독립 RBAC 검사 필요 | 해당 없음 (edge 없음) | 해당 없음 |

## Scope chain 순회

엔티티 가시성은 scope 계층의 CTE 상향 순회로 결정한다.

```
User:U → Project:P → Domain:D → Global
```

사용자가 접근 가능한 엔티티를 조회하면 시스템은 각 scope 수준에서
`association_scopes_entities` 를 상향 순회한다. 최종 결과는 모든 수준에서 찾은
엔티티의 **union** 이다.

**Auto edge**: chain 의 모든 수준에서 권한이 흐른다.
**Ref edge**: READ 권한만 흐르고 CUD 는 별도 RBAC 검사가 필요하다.

### 예시: ResourceGroup 가시성

```
association_scopes_entities:
  (scope=Domain:D,  entity=ResourceGroup:A, relation_type=auto)
  (scope=Project:P, entity=ResourceGroup:B, relation_type=auto)
  (scope=User:U,    entity=ResourceGroup:C, relation_type=auto)

User U (∈ Project:P ∈ Domain:D) queries ResourceGroups:

  CTE traversal:
    User:U    → finds RG:C
    Project:P → finds RG:B
    Domain:D  → finds RG:A

  Result = {RG:A, RG:B, RG:C}
```

이것은 현재의 union 기반 연쇄 동작과 같다. Domain 수준 매핑은 project 별이나
user 별 항목 없이도 그 domain 안의 **모든** user 와 project 가 ResourceGroup 에
접근하게 한다.

---

## Auto edge

### Scope → 엔티티 (N:N scope 접근성 매핑)

이 edge 는 엔티티를 접근 가능한 scope 에 매핑한다.
아래 구성 edge 와 달리 **N:N** 관계다. 엔티티 하나를 여러 scope 에 매핑할 수 있고,
scope 하나가 여러 엔티티를 담을 수 있다.

CTE 상향 순회로 가시성이 하위 scope 에까지 전달된다.

```
Domain  ━━auto━━► ResourceGroup
Domain  ━━auto━━► ContainerRegistry
Project ━━auto━━► ResourceGroup
Project ━━auto━━► ContainerRegistry
User    ━━auto━━► ResourceGroup
```

**기존 테이블에서 마이그레이션:**

| 기존 테이블 | 대체 | Edge |
|---|---|---|
| `ScalingGroupForDomainRow` | `(scope=Domain, entity=ResourceGroup, auto)` | Domain ━━auto━━► ResourceGroup |
| `ScalingGroupForProjectRow` | `(scope=Project, entity=ResourceGroup, auto)` | Project ━━auto━━► ResourceGroup |
| `ScalingGroupForKeypairsRow` | `(scope=User, entity=ResourceGroup, auto)` | User ━━auto━━► ResourceGroup |
| `AssociationContainerRegistriesGroupsRow` | `(scope=Project, entity=ContainerRegistry, auto)` | Project ━━auto━━► ContainerRegistry |

### Scope → 멤버 (1:N scope 구성)

이 edge 는 scope 계층 자체의 구성을 나타낸다.

```
Domain  ━━auto━━► User
Domain  ━━auto━━► Project
Domain  ━━auto━━► Network
Domain  ━━auto━━► DomainFairShare
Project ━━auto━━► Session
Project ━━auto━━► VFolder
Project ━━auto━━► Endpoint
Project ━━auto━━► Network
Project ━━auto━━► ProjectFairShare
User    ━━auto━━► Session
User    ━━auto━━► VFolder
User    ━━auto━━► Endpoint
User    ━━auto━━► KeyPair
User    ━━auto━━► UserFairShare
```

### 엔티티 → 하위 엔티티 (1:N 구성)

이 edge 는 하위 엔티티를 가진 부모 엔티티를 나타낸다.
자식은 독립 Root Query 가 없고 항상 부모를 통해 접근한다.

```
Session             ━━auto━━► Kernel
Session             ━━auto━━► Routing
Session             ━━auto━━► SessionDependency
Session             ━━auto━━► SessionSchedulingHistory
ResourceGroup       ━━auto━━► Agent
ResourceGroup       ━━auto━━► DomainFairShare
ResourceGroup       ━━auto━━► ProjectFairShare
ResourceGroup       ━━auto━━► UserFairShare
ContainerRegistry   ━━auto━━► Image
Image               ━━auto━━► ImageAlias
Agent               ━━auto━━► Kernel
VFolder             ━━auto━━► VFolderInvitation
Endpoint            ━━auto━━► EndpointToken
Endpoint            ━━auto━━► EndpointAutoScalingRule
Endpoint            ━━auto━━► DeploymentRevision
Endpoint            ━━auto━━► DeploymentPolicy
Endpoint            ━━auto━━► DeploymentAutoScalingPolicy
Endpoint            ━━auto━━► DeploymentHistory
Endpoint            ━━auto━━► Routing
Artifact            ━━auto━━► ArtifactRevision
NotificationChannel ━━auto━━► NotificationRule
Kernel              ━━auto━━► KernelSchedulingHistory
Routing             ━━auto━━► RouteHistory
Role                ━━auto━━► Permission
Role                ━━auto━━► UserRole
```

---

## Ref edge

이 edge 는 읽기 전용 참조다. 부모의 CRUD 는 자식에 READ 만 허용한다.
자식에서 더 순회하려면 별도 guarded 수준 RBAC 검사가 필요하다.

### Scope → 엔티티 (가시성만 있는 매핑)

```
Project ━━ref━━► User  (project membership — visibility only, no permission delegation)
```

**마이그레이션:**

| 기존 테이블 | 대체 | Edge |
|---|---|---|
| `AssocGroupUserRow` | `(scope=Project, entity=User, ref)` | Project ━━ref━━► User |

### 엔티티 → 참조 엔티티

```
Session             ──ref──► Agent
Session             ──ref──► ResourceGroup
Session             ──ref──► KeyPair
Kernel              ──ref──► Image
Kernel              ──ref──► Agent
Routing             ──ref──► Endpoint (from Session context)
Routing             ──ref──► Session (from Endpoint context)
VFolderInvitation   ──ref──► User (invitee)
VFolderInvitation   ──ref──► User (inviter)
Endpoint            ──ref──► Image
Endpoint            ──ref──► User (created_user)
Endpoint            ──ref──► User (session_owner)
User                ──ref──► UserResourcePolicy
User                ──ref──► KeyPair (main_access_key)
KeyPair             ──ref──► KeyPairResourcePolicy
KeyPair             ──ref──► User
Project             ──ref──► ProjectResourcePolicy
Network             ──ref──► Domain
Network             ──ref──► Project
UserRole            ──ref──► User
Artifact            ──ref──► ArtifactRegistry (HuggingFaceRegistry, ReservoirRegistry)
NotificationChannel ──ref──► User (created_by)
NotificationRule    ──ref──► User (created_by)
```

---

## Guarded 엔티티

이 엔티티들은 서로 edge 관계가 없다.
각각 자체 RBAC 검사를 가진 독립 Root Query 가 필요하다.

**Scoped (Root Query + mutation):**
- SessionRow, VFolderRow, EndpointRow, KeyPairRow, NotificationChannelRow
- NetworkRow, ScalingGroupRow (ResourceGroup), ContainerRegistryRow, StorageHostRow
- ImageRow, ArtifactRow, SessionTemplateRow
- UserRow, ProjectRow, AppConfigRow

**Superadmin 전용 (Root Query + mutation):**
- DomainRow, ResourcePresetRow
- UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow
- RoleRow

**Superadmin 읽기 전용 (Root Query, mutation 없음):**
- AuditLogRow, EventLogRow
