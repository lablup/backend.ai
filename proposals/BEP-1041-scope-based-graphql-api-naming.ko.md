# Scope 기반 GraphQL API 이름 규칙

## 관련 이슈

- 내부 논의: GraphQL API scope 명확화와 권한 체계 개선

## 동기

지금 Backend.AI 의 GraphQL API 는 이름으로 권한 수준과 접근 scope 를 드러내지 않는다. 그래서 다음 문제가 있다.

1. **명확성 부족**: API 이름만으로 admin 전용인지 사용자가 접근할 수 있는지 판단할 수 없다
2. **권한 체계 불명확**: scope 제한이 있는지, 어떤 scope 수준(domain, project, user)이 적용되는지 모호하다
3. **일관성 부족**: superadmin 검사가 있는 API 와 없는 API 가 섞여 있다
4. **문서화 어려움**: API 문서만으로 권한 요구 사항을 전달하기 어렵다

현재 상태:
```graphql
# Unclear whether this API is Admin-only or User-accessible
query {
  resource_groups { ... }        # Admin only? User accessible?
  notification_channels { ... }  # Admin only? User accessible?
  sessions { ... }               # User accessible, but what scope?
}
```

## 현재 설계

### 현재 API 권한 체계

현재 GraphQL API 는 세 가지로 나뉜다.

1. **superadmin 검사를 명시한 API**:
   - fair share (domain, project, user)
   - 스케줄링 이력
   - 자원 사용량

   ```python
   @strawberry.field
   async def domain_fair_shares(...) -> DomainFairShareConnection:
       me = current_user()
       if me is None or not me.is_superadmin:
           raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")
       ...
   ```

2. **scope 검사가 없는 API (admin 전용으로 추정)**:
   - 에이전트
   - 자원 그룹
   - 알림
   - 오브젝트 스토리지
   - VFS storage
   - registry 관련 (HuggingFace, Reservoir)

   ```python
   @strawberry.field
   async def resource_groups(...) -> ResourceGroupConnection:
       # No permission check - presumed Admin-only but not explicit
       ...
   ```

3. **일반 사용자 API (scope 제한이 암묵적)**:
   - 세션
   - vfolder

   ```python
   @strawberry.field
   async def sessions(...) -> SessionConnection:
       me = current_user()
       # Implicitly queries only current_user's domain/project
       ...
   ```

### 문제

1. **API 이름에 권한 수준이 드러나지 않는다**: `resource_groups` 가 admin 전용인지 알 수 없다
2. **scope 인자가 없다**: 사용자 API 에서 domain, project scope 를 지정할 방법이 없다
3. **일관성이 없다**: 권한 검사가 있는 API 와 없는 API 가 섞여 있다
4. **breaking change 우려**: 기존 API signature 를 변경하면 클라이언트에 영향이 간다

## 제안 설계

### 1. Scope 기반 접두사 체계

```
admin_*     → Admin exclusive (access all resources, no scope restriction)
rg_*        → Resource Group context (Fair Share etc., scope required)
domain_*    → Domain scope (access only specific domain resources)
project_*   → Project scope (access only specific project resources)
my_*        → User scope (access only current user's own resources)
public_*    → Public (no authentication required)
(no prefix) → Legacy API (to be deprecated)
```

**자원 그룹 문맥 (`rg_*`)**:
- fair share 는 항상 자원 그룹 안에서 관리한다
- 그래서 `rg_` 접두사가 자원 그룹 문맥임을 명시한다
- 예: `rg_domain_fair_shares`, `rg_project_fair_shares`

**일반 자원 (자원 그룹과 무관)**:
- 세션, vfolder 등은 자원 그룹과 무관하다
- domain, project scope 만 사용한다
- 예: `domain_sessions`, `project_sessions`

### 2. API signature 예시

#### Admin API (scope 제한 없음)
```python
@strawberry.field(description="List all resource groups (admin only)")
async def admin_resource_groups(
    filter: ResourceGroupFilter | None = None,
    order_by: list[ResourceGroupOrderBy] | None = None,
    ...
) -> ResourceGroupConnection:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Admin only")

    # Access all resource groups
    # Can filter by resourceGroup, domainName etc. using filter
    ...
```

#### 자원 그룹 문맥 API (fair share)
```python
@strawberry.field(description="List domain fair shares in resource group context")
async def rg_domain_fair_shares(
    scope: DomainFairShareScope,  # Required: specify permission scope
    filter: DomainFairShareFilter | None = None,
    ...
) -> DomainFairShareConnection:
    me = current_user()
    if me is None:
        raise web.HTTPUnauthorized()

    # Check scope permission
    if not has_permission(me, scope.resource_group, scope.domain_name):
        raise web.HTTPForbidden(f"No permission for scope={scope}")

    # Query only within scope
    ...
```

**scope 입력 타입:**
```python
@strawberry.input
class DomainFairShareScope:
    resource_group: str  # Required
    domain_name: str  # Required - check specific domain permission
```

```python
@strawberry.field(description="List project fair shares in resource group context")
async def rg_project_fair_shares(
    scope: ProjectFairShareScope,  # Required: specify permission scope
    filter: ProjectFairShareFilter | None = None,
    ...
) -> ProjectFairShareConnection:
    me = current_user()
    if me is None:
        raise web.HTTPUnauthorized()

    # Check scope permission
    if not has_permission(me, scope):
        raise web.HTTPForbidden(f"No permission for scope={scope}")

    # Query only within scope
    ...
```

**scope 입력 타입:**
```python
@strawberry.input
class ProjectFairShareScope:
    resource_group: str  # Required
    domain_name: str  # Required
    project_id: uuid.UUID  # Required - check specific project permission
```

#### Domain scope API (일반 자원)
```python
@strawberry.field(description="List sessions in domain scope")
async def domain_sessions(
    scope: DomainSessionScope,  # Required: specify permission scope
    filter: SessionFilter | None = None,
    ...
) -> SessionConnection:
    me = current_user()
    if me is None:
        raise web.HTTPUnauthorized()

    # Check scope permission
    if not has_permission(me, scope.domain_name):
        raise web.HTTPForbidden(f"No permission for domain={scope.domain_name}")

    # Query only within scope
    ...
```

**scope 입력 타입:**
```python
@strawberry.input
class DomainSessionScope:
    domain_name: str  # Required
```

#### User scope API (자기 자원 대상)
```python
@strawberry.field(description="List my sessions")
async def my_sessions(
    filter: SessionFilter | None = None,
    ...
) -> SessionConnection:
    me = current_user()
    if me is None:
        raise web.HTTPUnauthorized()

    # Query only current_user's sessions
    ...
```

### 3. 대상 API

#### 1단계: 6개 묶음 (우선)

**자원 그룹**
- Query: `admin_resource_groups`, `domain_resource_groups`
- Mutation: `admin_update_resource_group_fair_share_spec`

**알림**
- Query: `admin_notification_channel`, `admin_notification_channels`, `admin_notification_rule`, `admin_notification_rules`, `admin_notification_rule_types`
- Query: `domain_notification_channels`, `domain_notification_rules`
- Mutation: `admin_create_notification_channel`, `admin_update_notification_channel`, `admin_delete_notification_channel`, `admin_validate_notification_channel`
- Mutation: `admin_create_notification_rule`, `admin_update_notification_rule`, `admin_delete_notification_rule`, `admin_validate_notification_rule`

**fair share** (자원 그룹 문맥)
- Query: `admin_domain_fair_shares`, `admin_project_fair_shares`, `admin_user_fair_shares`
- Query: `rg_domain_fair_shares`, `rg_project_fair_shares`, `rg_user_fair_shares` (scope 필수)
- Mutation: `admin_upsert_domain_fair_share_weight`, `admin_bulk_upsert_domain_fair_share_weight`
- Mutation: `admin_upsert_project_fair_share_weight`, `admin_bulk_upsert_project_fair_share_weight`
- Mutation: `admin_upsert_user_fair_share_weight`, `admin_bulk_upsert_user_fair_share_weight`

**스케줄링 이력**
- Query: `admin_session_scheduling_histories`, `admin_deployment_histories`, `admin_route_histories`

**자원 사용량** (자원 그룹 문맥)
- Query: `admin_domain_usage_buckets`, `admin_project_usage_buckets`, `admin_user_usage_buckets`
- Query: `rg_domain_usage_buckets`, `rg_project_usage_buckets`, `rg_user_usage_buckets` (scope 필수)

**앱 설정**
- Query: `admin_domain_app_config`
- Mutation: `admin_upsert_domain_app_config`, `admin_delete_domain_app_config`

#### 2단계: 다른 자원 (이후)

- 에이전트: `admin_agent_stats`, `admin_agents_v2`
- 스토리지: `admin_object_storages`, `admin_vfs_storages`
- registry: `admin_huggingface_registries`, `admin_reservoir_registries`
- 세션: `domain_sessions`, `project_sessions`, `my_sessions`
- vfolder: `domain_vfolders`, `project_vfolders`, `my_vfolders`

### 4. GraphQL Schema 예시

**핵심 원칙:**
1. **Admin API**: scope 인자가 없다 (filter 로 조건을 지정한다)
2. **fair share**: `rg_*` 접두사 (자원 그룹 문맥)
3. **일반 자원**: `domain_*`, `project_*`, `my_*` (scope 인자 필수)

### 4. GraphQL Schema 예시

```graphql
type Query {
  # ============ Admin APIs (no scope parameter) ============
  # Resource Group
  admin_resource_groups(filter: ResourceGroupFilter, ...): ResourceGroupConnection

  # Notification
  admin_notification_channels(filter: NotificationChannelFilter, ...): NotificationChannelConnection
  admin_notification_rules(filter: NotificationRuleFilter, ...): NotificationRuleConnection

  # Fair Share
  admin_domain_fair_shares(filter: DomainFairShareFilter, ...): DomainFairShareConnection
  admin_project_fair_shares(filter: ProjectFairShareFilter, ...): ProjectFairShareConnection
  admin_user_fair_shares(filter: UserFairShareFilter, ...): UserFairShareConnection

  # Scheduling History
  admin_session_scheduling_histories(filter: SessionSchedulingHistoryFilter, ...): SessionSchedulingHistoryConnection
  admin_deployment_histories(filter: DeploymentHistoryFilter, ...): DeploymentHistoryConnection
  admin_route_histories(filter: RouteHistoryFilter, ...): RouteHistoryConnection

  # Resource Usage
  admin_domain_usage_buckets(filter: DomainUsageBucketFilter, ...): DomainUsageBucketConnection
  admin_project_usage_buckets(filter: ProjectUsageBucketFilter, ...): ProjectUsageBucketConnection
  admin_user_usage_buckets(filter: UserUsageBucketFilter, ...): UserUsageBucketConnection

  # App Config
  admin_domain_app_config(domainName: String!): AppConfig

  # ============ Resource Group Context APIs (rg_*) ============
  # Fair Share - Resource Group hierarchical structure
  rg_domain_fair_shares(
    scope: DomainFairShareScope!,
    filter: DomainFairShareFilter,
    ...
  ): DomainFairShareConnection

  rg_project_fair_shares(
    scope: ProjectFairShareScope!,
    filter: ProjectFairShareFilter,
    ...
  ): ProjectFairShareConnection

  rg_user_fair_shares(
    scope: UserFairShareScope!,
    filter: UserFairShareFilter,
    ...
  ): UserFairShareConnection

  # Resource Usage - Resource Group hierarchical structure
  rg_domain_usage_buckets(
    scope: DomainUsageBucketScope!,
    filter: DomainUsageBucketFilter,
    ...
  ): DomainUsageBucketConnection

  rg_project_usage_buckets(
    scope: ProjectUsageBucketScope!,
    filter: ProjectUsageBucketFilter,
    ...
  ): ProjectUsageBucketConnection

  rg_user_usage_buckets(
    scope: UserUsageBucketScope!,
    filter: UserUsageBucketFilter,
    ...
  ): UserUsageBucketConnection

  # ============ Domain Scope APIs ============
  domain_sessions(
    scope: DomainSessionScope!,
    filter: SessionFilter,
    ...
  ): SessionConnection

  domain_vfolders(
    scope: DomainVFolderScope!,
    filter: VFolderFilter,
    ...
  ): VFolderConnection

  # ============ Project Scope APIs ============
  project_sessions(
    scope: ProjectSessionScope!,
    filter: SessionFilter,
    ...
  ): SessionConnection

  project_vfolders(
    scope: ProjectVFolderScope!,
    filter: VFolderFilter,
    ...
  ): VFolderConnection

  # ============ User Scope APIs ============
  my_sessions(filter: SessionFilter, ...): SessionConnection
  my_vfolders(filter: VFolderFilter, ...): VFolderConnection

  # ============ Legacy APIs (deprecated) ============
  resource_groups(filter: ResourceGroupFilter, ...) @deprecated(reason: "Use admin_resource_groups")
  notification_channels(filter: NotificationChannelFilter, ...) @deprecated(reason: "Use admin_notification_channels")
  domain_fair_shares(filter: DomainFairShareFilter, ...) @deprecated(reason: "Use admin_domain_fair_shares or rg_domain_fair_shares(scope: ...)")
  project_fair_shares(filter: ProjectFairShareFilter, ...) @deprecated(reason: "Use admin_project_fair_shares or rg_project_fair_shares(scope: ...)")
  sessions(filter: SessionFilter, ...) @deprecated(reason: "Use domain_sessions, project_sessions, or my_sessions")
}

# ============ Scope Input Types ============
# Scope specifies permission boundary (all fields required)
# Additional filtering handled via filter parameter

# Resource Group Context - Fair Share
input DomainFairShareScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required - check specific domain permission
}

input ProjectFairShareScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required
  projectId: UUID!            # Required - check specific project permission
}

input UserFairShareScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required
  projectId: UUID!            # Required
  userId: UUID!               # Required - check specific user permission
}

# Resource Group Context - Usage Bucket
input DomainUsageBucketScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required - check specific domain permission
}

input ProjectUsageBucketScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required
  projectId: UUID!            # Required - check specific project permission
}

input UserUsageBucketScope {
  resourceGroup: String!      # Required
  domainName: String!         # Required
  projectId: UUID!            # Required
  userId: UUID!               # Required - check specific user permission
}

# Domain/Project Scope - General Resources
input DomainSessionScope {
  domainName: String!         # Required
}

input ProjectSessionScope {
  domainName: String!         # Required (or inferred from projectId)
  projectId: UUID!            # Required
}

type Mutation {
  # ============ Admin Mutations (no scope parameter) ============
  admin_update_resource_group_fair_share_spec(input: UpdateInput!): UpdatePayload
  admin_create_notification_channel(input: CreateInput!): CreatePayload
  admin_upsert_domain_fair_share_weight(input: UpsertInput!): UpsertPayload
  admin_upsert_domain_app_config(input: UpsertInput!): UpsertPayload

  # ============ Legacy Mutations (deprecated) ============
  update_resource_group_fair_share_spec(input: UpdateInput!) @deprecated(reason: "Use admin_update_resource_group_fair_share_spec")
  create_notification_channel(input: CreateInput!) @deprecated(reason: "Use admin_create_notification_channel")
  upsert_domain_fair_share_weight(input: UpsertInput!) @deprecated(reason: "Use admin_upsert_domain_fair_share_weight")
}
```

## 이관과 호환

### 하위 호환 전략

#### 단계적 전환 전략

**1단계 (v26.1): 새 API 추가**
- scope 기반 새 API(`admin_*`, `domain_*`, `project_*`, `my_*`)를 추가한다
- 기존 API 는 그대로 둔다 (deprecated 표시)
- breaking change 는 없다

```python
@strawberry.type
class Query:
    # New APIs
    admin_resource_groups = admin_resource_groups
    domain_resource_groups = domain_resource_groups

    # Legacy API (deprecated)
    resource_groups = strawberry.field(
        admin_resource_groups,
        deprecation_reason="Use admin_resource_groups or domain_resource_groups instead. Will be removed in v27.0.0"
    )
```

**2단계 (v26.2~v26.x): 전환 기간**
- 클라이언트가 새 API 로 이관한다
- legacy API 사용에 deprecation 경고를 낸다
- 문서를 갱신한다

**3단계 (v27.0): legacy API 제거**
- legacy API 를 완전히 제거한다
- 새 API 만 제공한다

### breaking change

#### v27.0 에서 제거할 API (legacy)

**Query:**
- `resource_groups` → `admin_resource_groups`
- `notification_channels` → `admin_notification_channels`
- `notification_rules` → `admin_notification_rules`
- `domain_fair_shares` → `admin_domain_fair_shares` + `rg_domain_fair_shares(scope: ...)`
- `project_fair_shares` → `admin_project_fair_shares` + `rg_project_fair_shares(scope: ...)`
- `user_fair_shares` → `admin_user_fair_shares` + `rg_user_fair_shares(scope: ...)`
- `session_scheduling_histories` → `admin_session_scheduling_histories`
- `deployment_histories` → `admin_deployment_histories`
- `route_histories` → `admin_route_histories`
- `domain_usage_buckets` → `admin_domain_usage_buckets` + `rg_domain_usage_buckets(scope: ...)`
- `project_usage_buckets` → `admin_project_usage_buckets` + `rg_project_usage_buckets(scope: ...)`
- `user_usage_buckets` → `admin_user_usage_buckets` + `rg_user_usage_buckets(scope: ...)`
- `domain_app_config` → `admin_domain_app_config`

**Mutation:**
- `update_resource_group_fair_share_spec` → `admin_update_resource_group_fair_share_spec`
- `create_notification_channel` → `admin_create_notification_channel`
- `update_notification_channel` → `admin_update_notification_channel`
- `delete_notification_channel` → `admin_delete_notification_channel`
- `validate_notification_channel` → `admin_validate_notification_channel`
- `create_notification_rule` → `admin_create_notification_rule`
- `update_notification_rule` → `admin_update_notification_rule`
- `delete_notification_rule` → `admin_delete_notification_rule`
- `validate_notification_rule` → `admin_validate_notification_rule`
- `upsert_domain_fair_share_weight` → `admin_upsert_domain_fair_share_weight`
- `bulk_upsert_domain_fair_share_weight` → `admin_bulk_upsert_domain_fair_share_weight`
- `upsert_project_fair_share_weight` → `admin_upsert_project_fair_share_weight`
- `bulk_upsert_project_fair_share_weight` → `admin_bulk_upsert_project_fair_share_weight`
- `upsert_user_fair_share_weight` → `admin_upsert_user_fair_share_weight`
- `bulk_upsert_user_fair_share_weight` → `admin_bulk_upsert_user_fair_share_weight`
- `upsert_domain_app_config` → `admin_upsert_domain_app_config`
- `delete_domain_app_config` → `admin_delete_domain_app_config`

### 클라이언트 이관 안내

#### 이전 (v26.0)
```graphql
query {
  # Admin queries all resources
  resource_groups {
    edges { node { id name } }
  }

  # User queries own sessions
  sessions {
    edges { node { id status } }
  }
}
```

#### 이후 (v26.1+)
```graphql
query {
  # Admin queries all resources
  admin_resource_groups {
    edges { node { id name } }
  }

  # Admin queries all domain fair shares
  admin_domain_fair_shares(
    filter: { resourceGroup: "default" }  # Filter via filter parameter
  ) {
    edges { node { domainName weight } }
  }

  # User queries fair shares for specific domain (permission check)
  rg_domain_fair_shares(
    scope: {
      resourceGroup: "default",
      domainName: "my-domain"    # Required - needs domain permission
    }
  ) {
    edges { node { domainName weight } }
  }

  # User queries sessions in specific domain
  domain_sessions(
    scope: { domainName: "my-domain" }
  ) {
    edges { node { id status } }
  }

  # User queries sessions in specific project
  project_sessions(
    scope: {
      domainName: "my-domain",
      projectId: "uuid"
    }
  ) {
    edges { node { id status } }
  }

  # User queries own sessions only
  my_sessions {
    edges { node { id status } }
  }
}
```

### 권한 검사 강화

권한 검사가 없던 API 에 명시적인 권한 검사를 추가한다.

```python
# Before (no permission check)
@strawberry.field
async def resource_groups(...) -> ResourceGroupConnection:
    # Accessible to anyone (unintended security issue)
    ...

# After (explicit permission check)
@strawberry.field(description="List all resource groups (admin only)")
async def admin_resource_groups(...) -> ResourceGroupConnection:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Admin only")
    ...
```

## 구현 계획

### 1단계: 핵심 기반 (v26.1.0)

**1.1. 새 API 함수 생성**
- [ ] 자원 그룹: `admin_resource_groups`, `domain_resource_groups`
- [ ] 알림: `admin_notification_channels`, `admin_notification_rules` 등
- [ ] fair share: `admin_domain_fair_shares`, `domain_fair_shares(domainName)` 등
- [ ] 스케줄링 이력: `admin_session_scheduling_histories` 등
- [ ] 자원 사용량: `admin_domain_usage_buckets`, `domain_usage_buckets(domainName)` 등
- [ ] 앱 설정: `admin_domain_app_config`

**1.2. 권한 검사 추가**
- [ ] 모든 `admin_*` API 에 superadmin 검사를 추가한다
- [ ] 모든 `domain_*` API 에 domain 권한 검사를 추가한다
- [ ] 모든 `project_*` API 에 project 권한 검사를 추가한다

**1.3. Schema 갱신**
- [ ] 새 API 를 `schema.py` 에 등록한다
- [ ] 기존 API 에 `@deprecated` 표시를 추가한다
- [ ] description 에 권한 요구 사항을 적는다

**1.4. 테스트**
- [ ] 단위 테스트: API 마다 권한 검사를 검증한다
- [ ] 통합 테스트: GraphQL query 실행을 검증한다
- [ ] 권한 테스트: 권한이 없는 사용자의 접근 차단을 검증한다

### 2단계: 문서 (v26.1.0)

**2.1. API 문서 갱신**
- [ ] GraphQL schema 문서를 생성한다
- [ ] 이관 안내를 작성한다
- [ ] breaking change 를 문서화한다

**2.2. 릴리스 노트**
- [ ] changelog 를 갱신한다
- [ ] deprecation 을 공지한다

### 3단계: 클라이언트 이관 지원 (v26.1.0 ~ v26.x)

**3.1. 이관 지원**
- [ ] 클라이언트 팀에 이관 안내를 제공한다
- [ ] GraphQL Playground 에서 deprecated API 경고를 보여준다
- [ ] 로그에서 deprecated API 사용을 추적한다

**3.2. 모니터링**
- [ ] deprecated API 사용을 모니터링한다
- [ ] 새 API 도입률을 추적한다

### 4단계: legacy API 제거 (v27.0.0)

**4.1. 제거 준비**
- [ ] 모든 클라이언트가 새 API 로 이관했는지 검증한다
- [ ] legacy API 사용이 0 인지 확인한다

**4.2. 코드 정리**
- [ ] legacy API 함수를 제거한다
- [ ] schema 에서 제거한다
- [ ] 관련 테스트를 제거한다

**4.3. 릴리스**
- [ ] breaking change 릴리스 노트를 작성한다
- [ ] major version 을 올린다 (v27.0.0)

### 5단계: 확장 (v27.1.0+)

**5.1. 다른 자원에 적용**
- [ ] 에이전트: `admin_agents`, `domain_agents`
- [ ] 스토리지: `admin_object_storages`, `domain_object_storages`
- [ ] 세션: `domain_sessions`, `project_sessions`, `my_sessions`
- [ ] vfolder: `domain_vfolders`, `project_vfolders`, `my_vfolders`

**5.2. 최적화**
- [ ] 권한 검사 로직을 최적화한다
- [ ] 캐시 전략을 적용한다

## 열린 질문

1. **Scope 세분화 수준**
   - 현재: domain, project, user
   - organization, team 같은 추가 수준의 필요성

2. **User scope API 의 필요성**
   - `my_sessions` 의 실제 필요성
   - `domain_sessions(scope: { domainName: "current-user-domain" })` 로 대체 가능한지 여부
   - 현재 제안: `my_*` API 를 제공한다 (편의)

3. **Project scope 에서 domain name 중복**
   - `ProjectSessionScope` 의 `domainName` field 필요성
   - `projectId` 로 domain 을 유추할 수 있으나, 명시하는 편이 안전하다
   - 현재 제안: `domainName` 을 명시적으로 포함한다

4. **public API scope**
   - 인증 없이 접근 가능한 API 의 존재 여부
   - `public_version`, `public_health` 외에 다른 API 가 있는지 여부

5. **이관 기간**
   - deprecation 기간 (현재 제안: v26.1 ~ v27.0, 약 6개월)
   - 더 긴 기간의 필요성

6. **Scope 와 filter 의 경계**
   - scope 는 권한 경계, filter 는 조회 조건으로 구분한다
   - 일부 사용 사례에서의 혼동 가능성

## 참고

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
