# RBAC 엔티티 관계 모델

## 관련 이슈

- JIRA: [BA-4179](https://lablup.atlassian.net/browse/BA-4179) — RBAC 엔티티 관계 모델 구현
- JIRA: [BA-4218](https://lablup.atlassian.net/browse/BA-4218) — BEP-1048 문서 등록
- GitHub: #8531
- 관련 BEP:
  - [BEP-1008: RBAC](BEP-1008-RBAC.md) - 원래 RBAC 기술 설계
  - [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md) - RBAC 기능 명세

## 동기

BEP-1008 과 BEP-1012 는 RBAC role, 권한, scope 계층을 정의하지만 **엔티티 가시성**이 RBAC 와 어떻게 맞물리는지는 정하지 않는다. 지금은 다음과 같다.

- entity 타입마다 자체 가시성 로직을 구현해 사용자가 어떤 인스턴스를 볼 수 있는지 정한다.
- 엔티티 관계가 순회와 접근에 어떻게 영향을 주는지 통합된 모델이 없다.
- junction 테이블(`AssociationContainerRegistriesGroupsRow`, `ScalingGroupForDomainRow` 등)이 저장소 곳곳에 일관성 없이 흩어져 있다.

이 제안은 모든 엔티티 관계를 작은 타입 묶음으로 분류하고 가시성 로직을 하나의 테이블(`association_scopes_entities`)로 통합하는 **엔티티 관계 모델**을 소개한다.

## 현재 설계

### 나뉜 가시성

엔티티 가시성은 지금 엔티티마다 처리한다.

- **ResourceGroup**: 별도 junction 테이블(`sgroups_for_domains`, `sgroups_for_groups`, `sgroups_for_keypairs`)로 어떤 resource group 이 어떤 scope 에 보이는지 정한다.
- **ContainerRegistry**: project 수준 가시성에 `association_container_registries_groups` junction 테이블을 사용한다.
- **VFolder**: 공유에 `vfolder_permissions` 와 `vfolder_invitations` 를 사용한다.
- **Session/Kernel/Agent**: 가시성을 즉석 질의 join 으로 정한다.

### 문제

1. **일관성 없는 패턴**: entity 타입마다 scope 기반 가시성에 다른 방식을 사용한다.
2. **순회 모델 없음**: 주어진 진입점에서 어떤 엔티티에 접근할 수 있는지 정하는 통합된 방법이 없다.
3. **DB 테이블 증식**: N:N scope 매핑마다 junction 테이블이 필요하다.
4. **RBAC 공백**: BEP-1008/1012 는 사용자가 **어떤 연산**을 할 수 있는지 정의하지만, 애초에 **어떤 엔티티**가 보이는지는 정하지 않는다.

## 제안 설계

### 엔티티 관계 3타입 모델

모든 엔티티 관계를 정확히 세 타입으로 분류한다.

| 타입 | 의미 | 저장 | GQL 하위 field | 권한 |
|------|-----------|---------|---------------|------------|
| `guarded` | 독립 엔티티. edge 관계 없음 | 해당 없음 (edge 없음) | 없음 | 별도 RBAC 검사 필요 |
| `auto` | 구성. 부모에서 권한 위임 | DB (`association_scopes_entities`, `relation_type=auto`) | 있음 | role 이 정한 권한이 흐른다 |
| `ref` | 읽기 전용 참조. 권한 위임 없음 | DB (`association_scopes_entities`, `relation_type=ref`) | 있음 (읽기 전용) | 부모의 CRUD 는 자식의 READ 에만 적용 |

핵심 의미는 다음과 같다.

- **Guarded** 는 edge 가 아니다. 관계가 없음을 나타낸다. A 의 권한은 B 와 독립이다. B 는 자체 RBAC 검사를 가진 자체 Root Query 가 필요하다. 둘 사이에 GQL 하위 field 는 없다.
- **Auto** edge 는 `association_scopes_entities` 에 인스턴스마다 `relation_type=auto` 로 저장한다. role 의 권한이 edge 를 통해 흐른다. 어떤 연산이 허용되는지는 edge 타입이 아니라 role 이 정한다. 순회에 별도 RBAC 검사가 필요 없다.
- **Ref** edge 는 `association_scopes_entities` 에 인스턴스마다 `relation_type=ref` 로 저장한다. 부모 A 에 CRUD 가 있으면 자식 B 에 READ 만 얻는다. 이 경로로 B 에 CUD 는 허용되지 않는다. 부모는 ref 자식을 나열할 수 있지만 권한 위임은 일어나지 않는다. B 에서 더 순회하려면 별도 guarded 수준 권한 검사가 필요하다.
- `RelationType` enum(`auto`, `ref`)을 코드에 정의한다. `association_scopes_entities` 테이블은 auto 와 ref edge 를 구분하는 `relation_type` column 을 포함한다.

### 버린 대안

- **참조 타입 (ref 엔티티용 별도 GQL 타입)**: 기각. ref 엔티티는 모든 field 를 노출한다.
- **비정규화 (평면 field)**: 기각. 유지 비용이 커진다.

### Auto edge

Auto edge 는 `association_scopes_entities` 를 통한 **권한 위임**이 있는 구성 관계를 나타낸다. A 에서 B 로 auto edge 가 있으면 다음과 같다.

- role 의 권한이 edge 를 통해 B 로 흐른다. B 에 허용되는 연산은 edge 타입이 아니라 role 이 정한다.
- B 에 별도 RBAC 검사가 필요 없다.
- B 는 A 의 GQL 하위 field 로 나타난다.

### Ref edge

Ref edge 는 `association_scopes_entities` 에 인스턴스마다 `relation_type=ref` 로 저장하는 읽기 전용 참조를 나타내며 **권한 위임은 없다**. A 에서 B 로 ref edge 가 있으면 다음과 같다.

- A 의 CRUD 권한은 B 에 READ 만 준다. 이 경로로 B 에 CUD 는 허용되지 않는다.
- 부모는 ref 자식을 나열할 수 있다(`association_scopes_entities` 의 row 가 이것을 가능하게 한다).
- B 는 A 의 읽기 전용 GQL 하위 field 로 나타난다.
- B 에서 더 순회하려면 별도 guarded 수준 권한 검사가 필요하다. 독립 엔티티에 접근할 때와 같다.

#### Ref edge 를 통한 공유

엔티티 공유(예: VFolder 초대)는 ref edge 와 엔티티 scope 권한을 함께 사용한다.

- **Ref edge** 는 가시성(나열)을 제공하고 초대받은 사용자의 scope 에서 권한 상승을 차단한다.
- **엔티티 scope 권한**은 부여하는 정확한 연산(읽기, 쓰기 등)을 제어한다.

사용자 A 가 VFolder X 를 사용자 B 에게 공유할 때(쓰기 초대)는 다음과 같다.

```
association_scopes_entities:
  (scope=User:B, entity=VFolder:X, relation_type=ref)    ← visibility + escalation prevention

permissions (B's system role, entity-scope):
  (scope=VFolder:X, entity_type=vfolder, op=read)         ← explicit read grant
  (scope=VFolder:X, entity_type=vfolder, op=write)        ← explicit write grant
```

권한 검사는 두 계층이다.

1. **엔티티 scope 직접 일치**(우선): 사용자가 전체 scope 식별자 `(scope_type, scope_id)` 가 대상 엔티티의 타입, id 와 일치하는 권한을 가지는지 확인한다. edge 타입과 무관하게 일치한다.
2. **CTE scope chain**(대체): `association_scopes_entities` 를 상향 순회한다. ref edge 는 상속한 권한을 READ 로 제한해 초대받은 사용자의 user scope CRUD 가 공유 엔티티로 확대되지 않게 한다.

그래서 B 의 기존 user scope 권한(예: `scope=User:B` 의 `vfolder:delete`)은 VFolder X 로 흐르지 않고, 명시적으로 부여한 엔티티 scope 권한(읽기, 쓰기)만 의도대로 동작한다.

### Edge 카탈로그

모든 auto, ref, guarded edge 전체 목록은 [Entity Edge Catalog](BEP-1048/entity-edge-catalog.md)를 본다.

### 핵심 원칙

1. **통합 edge 저장.** `association_scopes_entities` 는 흩어진 junction 테이블을 대체하는 모든 엔티티 관계의 단일 기준이다. `relation_type` column 으로 권한 위임(`auto`)과 가시성(`ref`)을 모두 저장한다.
2. **엔티티 속성이 아니라 edge 속성.** 관계 타입은 엔티티 자체가 아니라 부모에서 자식으로 가는 edge 가 정한다. 같은 엔티티가 한 부모에서는 `auto`, 다른 부모에서는 `ref` 일 수 있다(예: Agent 는 ResourceGroup 에서 `auto`, Session 에서 `ref`).

### 질의 제약

#### Root Query 가 있는 엔티티

이 엔티티들은 RBAC 검사를 가진 독립 Root Query 가 있다. 이 엔티티만 `association_scopes_entities` 에 scope 에서 엔티티로 가는 매핑으로 저장한다.

**Scoped:**
- SessionRow, VFolderRow, EndpointRow, KeyPairRow, NotificationChannelRow
- NetworkRow, ScalingGroupRow, ContainerRegistryRow, StorageHostRow
- ImageRow, ArtifactRow, SessionTemplateRow
- UserRow, ProjectRow, AppConfigRow

**Superadmin 전용:**
- DomainRow, ResourcePresetRow, UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow, RoleRow, AuditLogRow, EventLogRow

#### Mutation 이 있는 엔티티

이 엔티티들은 mutation API(Create, Update, Delete, Purge)가 있다. 읽기 전용 시스템 로그를 뺀 Root Query 대상 엔티티 전부다.

**Scoped:**
- SessionRow, VFolderRow, EndpointRow, KeyPairRow, NotificationChannelRow
- NetworkRow, ScalingGroupRow, ContainerRegistryRow, StorageHostRow
- ImageRow, ArtifactRow, SessionTemplateRow
- UserRow, ProjectRow, AppConfigRow

**Superadmin 전용:**
- DomainRow, ResourcePresetRow, UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow, RoleRow

**읽기 전용 (mutation API 없음):**
- AuditLogRow, EventLogRow

#### Auto edge 만 있는 엔티티

독립 단건 질의나 목록 질의가 없다. 항상 부모를 통해 접근한다.

| 엔티티 | 부모 (auto edge) | 접근 방식 |
|--------|-------------------|----------------|
| KernelRow | Session, Agent | `session { kernels }` |
| RoutingRow | Session, Endpoint | `session { routings }` |
| SessionDependencyRow | Session | `session { dependencies }` |
| SessionSchedulingHistoryRow | Session | `session { schedulingHistory }` |
| AgentRow | ResourceGroup | `resourceGroup { agents }` |
| ImageAliasRow | Image | `image { aliases }` |
| VFolderInvitationRow | VFolder | `vfolder { invitations }` |
| EndpointTokenRow | Endpoint | `endpoint { tokens }` |
| EndpointAutoScalingRuleRow | Endpoint | `endpoint { autoScalingRules }` |
| DeploymentRevisionRow | Endpoint | `endpoint { revisions }` |
| DeploymentPolicyRow | Endpoint | `endpoint { policy }` |
| DeploymentAutoScalingPolicyRow | Endpoint | `endpoint { autoScalingPolicy }` |
| DeploymentHistoryRow | Endpoint | `endpoint { deploymentHistory }` |
| ArtifactRevisionRow | Artifact | `artifact { revisions }` |
| NotificationRuleRow | NotificationChannel | `notificationChannel { rules }` |
| KernelSchedulingHistoryRow | Kernel | `kernel { schedulingHistory }` |
| RouteHistoryRow | Routing | `routing { history }` |
| DomainFairShareRow | Domain, ResourceGroup | `domain { fairShare }`, `resourceGroup { domainFairShares }` |
| ProjectFairShareRow | Project, ResourceGroup | `project { fairShare }`, `resourceGroup { projectFairShares }` |
| UserFairShareRow | User, ResourceGroup | `user { fairShare }`, `resourceGroup { userFairShares }` |
| PermissionRow | Role | `role { permissions }` |
| UserRoleRow | Role | `role { userRoles }` |

### RBAC scope 밖의 엔티티

다음 엔티티는 3타입 모델에서 의도적으로 제외한다.

**시스템 내부, 인프라:**
- ResourceSlotTypeRow, AgentResourceRow, ResourceAllocationRow (스케줄러 내부)
- ServiceCatalogRow, ServiceCatalogEndpointRow (내부 서비스 디스커버리)
- StorageNamespaceRow (ObjectStorage 내부 분할)
- EntityFieldRow (RBAC 메타데이터)
- ErrorLogRow (시스템 에러 로그)

**Registry 구현 (Artifact ref 로 접근):**
- HuggingFaceRegistryRow, ReservoirRegistryRow, ArtifactRegistryRow

### StorageHost 마이그레이션

StorageHost 는 계획된 엔티티로 아직 DB 테이블이 없다.

- **현재 상태**: `VFolderRow.host` 가 `"proxy_name:volume_name"` 문자열을 저장한다. `allowed_vfolder_hosts` 는 Domain/Group/KeyPairResourcePolicy 에 흩어진 JSON column 이다.
- **계획**: `StorageHostRow` DB 테이블로 정규화하고 기존 `ObjectStorageRow` 와 `VFSStorageRow` 를 통합한다. ContainerRegistry 처럼 `association_scopes_entities` 를 통한 N:N scope 매핑을 가진 Root Query 대상 엔티티로 둔다.

## 마이그레이션 / 호환성

### DB schema 변경

1. **새 테이블**: `association_scopes_entities`. 인스턴스별 auto, ref edge 를 `relation_type` column 과 함께 저장한다(권한 위임은 `auto`, 읽기 전용 나열은 `ref`).
2. **제거**: `permission_groups` 테이블. field(`role_id`, `scope_type`, `scope_id`)를 `permissions` 로 직접 옮긴다.
3. **제거**: `object_permissions` 테이블. 엔티티를 scope 로 사용하는 패턴으로 대체한다.

### 연결 테이블 대체

기존 junction 테이블을 `association_scopes_entities` 로 대체한다. 이것들은 N:N scope 접근성 매핑이다. 엔티티 가시성은 CTE scope chain 순회로 자식 scope 로 이어진다(자세한 내용은 [Entity Edge Catalog](BEP-1048/entity-edge-catalog.md)를 본다).

| 현재 테이블 | Edge | `relation_type` |
|---|---|---|
| `ScalingGroupForDomainRow` | Domain ━━auto━━► ResourceGroup | `auto` |
| `ScalingGroupForProjectRow` | Project ━━auto━━► ResourceGroup | `auto` |
| `ScalingGroupForKeypairsRow` | User ━━auto━━► ResourceGroup | `auto` |
| (새 테이블) | Domain ━━auto━━► ContainerRegistry | `auto` |
| `AssociationContainerRegistriesGroupsRow` | Project ━━auto━━► ContainerRegistry | `auto` |
| `AssocGroupUserRow` | (폐지. role 부여와 해제 때 자동 동기화하는 `entity_type='user'` 항목으로 대체) | `auto` |
| `VFolderPermissionRow` | User ━━ref━━► VFolder (+ 엔티티 scope 권한) | `ref` |

### 최종 RBAC 테이블

마이그레이션 후 핵심 RBAC 테이블은 다음과 같다.

- `roles`
- `user_roles`
- `permissions` (`role_id`, `scope_type`, `scope_id` 를 직접 가짐)
- `association_scopes_entities`

### 하위 호환성

- **공유**는 ref edge 와 엔티티 scope 권한으로 구현한다.
  - **초대**: `association_scopes_entities` 에 ref edge 를 삽입하고 초대받은 사용자의 시스템 role 에 엔티티 scope 권한(읽기, 쓰기)을 삽입한다.
  - **해지**: ref edge 를 삭제하고 엔티티 scope 권한을 삭제한다.
  - ref edge 는 초대받은 사용자의 user scope CRUD 가 공유 엔티티로 확대되지 않게 한다. 명시적으로 부여한 엔티티 scope 권한만 적용된다.
- project 멤버십은 `association_scopes_entities`(`entity_type='user'`)에 직접 저장하고 role 부여와 해제 때 자동으로 동기화한다. 이전 `association_groups_users` 테이블을 대체하고 단일 테이블 멤버십 조회를 가능하게 한다.

## 구현 계획

1. **1단계: 핵심 schema**
   - `association_scopes_entities` 테이블 생성
   - `permissions` 테이블이 `role_id`, `scope_type`, `scope_id` 를 직접 포함하도록 마이그레이션
   - `permission_groups` 와 `object_permissions` 테이블 제거

2. **2단계: 엔티티 분류 메타데이터**
   - 코드에 `RelationType` enum 정의
   - 모든 entity 타입에 관계 메타데이터(auto/ref edge)를 표시
   - guarded 조회용 CTE 기반 scope chain 순회 구현

3. **3단계: Root Query RBAC 적용**
   - Root Query resolver 에 guarded 검사를 통합
   - 중첩 resolver 에서 auto 순회와 ref 인증 context 초기화 구현

4. **4단계: 연결 테이블 마이그레이션**
   - 기존 junction 테이블을 `association_scopes_entities` 로 마이그레이션
   - 지원이 종료된(deprecated) junction 테이블 제거
   - StorageHost 를 문자열 기반에서 정규화된 DB 테이블로 마이그레이션

## 참고

- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
