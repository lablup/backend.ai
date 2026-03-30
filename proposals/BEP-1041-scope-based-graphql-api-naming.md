---
# Author: Full name and email of the proposal author
Author: HyeokJin Kim
# Status: Draft | Accepted | Implemented | Rejected | Superseded
Status: Draft
# Created: Date when this proposal was first created (YYYY-MM-DD)
Created: 2026-01-30
# Created-Version: Backend.AI version when this proposal was created (YY.Sprint.Patch)
Created-Version: 26.1.0
# Target-Version: Expected version for implementation (fill when Accepted)
Target-Version:
# Implemented-Version: Actual version where this was implemented (fill when Implemented)
Implemented-Version:
---

# Scope-Based GraphQL API Naming Convention

## Related Issues

- Internal discussion: GraphQL API scope clarification and permission system improvement

## Motivation

Currently, Backend.AI's GraphQL API does not clearly express permission levels and access scopes through API naming. This leads to the following problems:

1. **Lack of Clarity**: Cannot determine from API name alone whether it's Admin-only or User-accessible
2. **Unclear Permission System**: Ambiguous whether scope restrictions exist and what scope level (domain/project/user) applies
3. **Inconsistency**: Some APIs have superadmin checks while others don't, causing confusion
4. **Documentation Difficulty**: Hard to convey permission requirements clearly through API documentation alone

Current state:
```graphql
# Unclear whether this API is Admin-only or User-accessible
query {
  resource_groups { ... }        # Admin only? User accessible?
  notification_channels { ... }  # Admin only? User accessible?
  sessions { ... }               # User accessible, but what scope?
}
```

## Current Design

### Current API Permission System

Current GraphQL APIs are structured as follows:

1. **APIs with Explicit Superadmin Check**:
   - Fair Share (domain, project, user)
   - Scheduling History
   - Resource Usage

   ```python
   @strawberry.field
   async def domain_fair_shares(...) -> DomainFairShareConnection:
       me = current_user()
       if me is None or not me.is_superadmin:
           raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")
       ...
   ```

2. **APIs without Scope Check (Presumed Admin-only)**:
   - Agent
   - Resource Group
   - Notification
   - Object Storage
   - VFS Storage
   - Registry-related (HuggingFace, Reservoir)

   ```python
   @strawberry.field
   async def resource_groups(...) -> ResourceGroupConnection:
       # No permission check - presumed Admin-only but not explicit
       ...
   ```

3. **Regular User APIs (Implicit Scope Restriction)**:
   - Sessions
   - VFolders

   ```python
   @strawberry.field
   async def sessions(...) -> SessionConnection:
       me = current_user()
       # Implicitly queries only current_user's domain/project
       ...
   ```

### Problems

1. **Permission level not visible in API name**: Cannot tell if `resource_groups` is Admin-only
2. **Missing Scope Parameter**: No explicit way to specify domain/project scope in User APIs
3. **Lack of Consistency**: Some APIs have permission checks, others don't
4. **Breaking Change Concern**: Changing existing API signatures affects clients

## Proposed Design

### 1. Scope-Based Prefix System

```
admin_*     → Admin exclusive (access all resources, no scope restriction)
rg_*        → Resource Group context (Fair Share etc., scope required)
domain_*    → Domain scope (access only specific domain resources)
project_*   → Project scope (access only specific project resources)
my_*        → User scope (access only current user's own resources)
public_*    → Public (no authentication required)
(no prefix) → Legacy API (to be deprecated)
```

**Resource Group Context (`rg_*`)**:
- Fair Share is always managed within Resource Group
- Therefore, `rg_` prefix explicitly indicates Resource Group context
- Examples: `rg_domain_fair_shares`, `rg_project_fair_shares`

**General Resources (Resource Group Independent)**:
- Sessions, VFolders etc. are independent of Resource Group
- Use only Domain/Project scope
- Examples: `domain_sessions`, `project_sessions`

### 2. API Signature Examples

#### Admin API (No Scope Restriction)
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

#### Resource Group Context API (Fair Share)
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

**Scope Input Type:**
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

**Scope Input Type:**
```python
@strawberry.input
class ProjectFairShareScope:
    resource_group: str  # Required
    domain_name: str  # Required
    project_id: uuid.UUID  # Required - check specific project permission
```

#### Domain Scope API (General Resources)
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

**Scope Input Type:**
```python
@strawberry.input
class DomainSessionScope:
    domain_name: str  # Required
```

#### User Scope API (Own Resources Only)
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

### 3. Target APIs

#### Phase 1: 6 Groups (Priority)

**Resource Group**
- Query: `admin_resource_groups`, `domain_resource_groups`
- Mutation: `admin_update_resource_group_fair_share_spec`

**Notification**
- Query: `admin_notification_channel`, `admin_notification_channels`, `admin_notification_rule`, `admin_notification_rules`, `admin_notification_rule_types`
- Query: `domain_notification_channels`, `domain_notification_rules`
- Mutation: `admin_create_notification_channel`, `admin_update_notification_channel`, `admin_delete_notification_channel`, `admin_validate_notification_channel`
- Mutation: `admin_create_notification_rule`, `admin_update_notification_rule`, `admin_delete_notification_rule`, `admin_validate_notification_rule`

**Fair Share** (Resource Group Context)
- Query: `admin_domain_fair_shares`, `admin_project_fair_shares`, `admin_user_fair_shares`
- Query: `rg_domain_fair_shares`, `rg_project_fair_shares`, `rg_user_fair_shares` (scope required)
- Mutation: `admin_upsert_domain_fair_share_weight`, `admin_bulk_upsert_domain_fair_share_weight`
- Mutation: `admin_upsert_project_fair_share_weight`, `admin_bulk_upsert_project_fair_share_weight`
- Mutation: `admin_upsert_user_fair_share_weight`, `admin_bulk_upsert_user_fair_share_weight`

**Scheduling History**
- Query: `admin_session_scheduling_histories`, `admin_deployment_histories`, `admin_route_histories`

**Resource Usage** (Resource Group Context)
- Query: `admin_domain_usage_buckets`, `admin_project_usage_buckets`, `admin_user_usage_buckets`
- Query: `rg_domain_usage_buckets`, `rg_project_usage_buckets`, `rg_user_usage_buckets` (scope required)

**App Config**
- Query: `admin_domain_app_config`
- Mutation: `admin_upsert_domain_app_config`, `admin_delete_domain_app_config`

#### Phase 2: Other Resources (Future)

- Agent: `admin_agent_stats`, `admin_agents_v2`
- Storage: `admin_object_storages`, `admin_vfs_storages`
- Registry: `admin_huggingface_registries`, `admin_reservoir_registries`
- Sessions: `domain_sessions`, `project_sessions`, `my_sessions`
- VFolders: `domain_vfolders`, `project_vfolders`, `my_vfolders`

### 4. GraphQL Schema 예시

**Key Principles:**
1. **Admin API**: No scope parameter (filtering via filter)
2. **Fair Share**: `rg_*` prefix (Resource Group context)
3. **General Resources**: `domain_*`, `project_*`, `my_*` (scope parameter required)

### 4. GraphQL Schema Examples

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

## Migration / Compatibility

### Backward Compatibility Strategy

#### Phased Transition Strategy

**Phase 1 (v26.1): Add New APIs**
- Add new scope-based APIs (`admin_*`, `domain_*`, `project_*`, `my_*`)
- Keep existing APIs (mark as deprecated)
- No breaking changes

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

**Phase 2 (v26.2~v26.x): Transition Period**
- Clients migrate to new APIs
- Deprecation warnings on legacy API usage
- Documentation updates

**Phase 3 (v27.0): Remove Legacy APIs**
- Completely remove legacy APIs
- Provide only new APIs

### Breaking Changes

#### APIs to be Removed in v27.0 (Legacy)

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

### Migration Guide for Clients

#### Before (v26.0)
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

#### After (v26.1+)
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

### Enhanced Permission Checks

Add explicit permission checks to APIs that previously lacked them:

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

## Implementation Plan

### Phase 1: Core Infrastructure (v26.1.0)

**1.1. Create New API Functions**
- [ ] Resource Group: `admin_resource_groups`, `domain_resource_groups`
- [ ] Notification: `admin_notification_channels`, `admin_notification_rules`, etc.
- [ ] Fair Share: `admin_domain_fair_shares`, `domain_fair_shares(domainName)`, etc.
- [ ] Scheduling History: `admin_session_scheduling_histories`, etc.
- [ ] Resource Usage: `admin_domain_usage_buckets`, `domain_usage_buckets(domainName)`, etc.
- [ ] App Config: `admin_domain_app_config`

**1.2. Add Permission Checks**
- [ ] Add superadmin check to all `admin_*` APIs
- [ ] Add domain permission check to all `domain_*` APIs
- [ ] Add project permission check to all `project_*` APIs

**1.3. Update Schema**
- [ ] Register new APIs in `schema.py`
- [ ] Add `@deprecated` marker to existing APIs
- [ ] Specify permission requirements in descriptions

**1.4. Tests**
- [ ] Unit tests: Verify permission checks for each API
- [ ] Integration tests: Verify GraphQL query execution
- [ ] Permission tests: Verify unauthorized user access blocking

### Phase 2: Documentation (v26.1.0)

**2.1. Update API Documentation**
- [ ] Generate GraphQL schema documentation
- [ ] Write migration guide
- [ ] Document breaking changes

**2.2. Release Notes**
- [ ] Update changelog
- [ ] Announce deprecations

### Phase 3: Client Migration Support (v26.1.0 ~ v26.x)

**3.1. Migration Support**
- [ ] Provide migration guide to client teams
- [ ] Show deprecated API warnings in GraphQL Playground
- [ ] Track deprecated API usage in logs

**3.2. Monitoring**
- [ ] Monitor deprecated API usage
- [ ] Track new API adoption rate

### Phase 4: Legacy API Removal (v27.0.0)

**4.1. Removal Preparation**
- [ ] Verify all clients migrated to new APIs
- [ ] Confirm legacy API usage is zero

**4.2. Code Cleanup**
- [ ] Remove legacy API functions
- [ ] Remove from schema
- [ ] Remove related tests

**4.3. Release**
- [ ] Breaking change release notes
- [ ] Major version bump (v27.0.0)

### Phase 5: Extension (v27.1.0+)

**5.1. Apply to Additional Resources**
- [ ] Agent: `admin_agents`, `domain_agents`
- [ ] Storage: `admin_object_storages`, `domain_object_storages`
- [ ] Sessions: `domain_sessions`, `project_sessions`, `my_sessions`
- [ ] VFolders: `domain_vfolders`, `project_vfolders`, `my_vfolders`

**5.2. Optimization**
- [ ] Optimize permission check logic
- [ ] Apply caching strategies

## Open Questions

1. **Scope Granularity Levels**
   - Current: Domain, Project, User
   - Need for additional levels: Organization, Team, etc.?

2. **Necessity of User Scope APIs**
   - Is `my_sessions` actually needed?
   - Can it be replaced with `domain_sessions(scope: { domainName: "current-user-domain" })`?
   - Current proposal: Provide `my_*` APIs (for convenience)

3. **Domain Name Redundancy in Project Scope**
   - Is `domainName` field needed in `ProjectSessionScope`?
   - Domain can be inferred from `projectId`, but explicit specification might be safer
   - Current proposal: Explicitly include `domainName`

4. **Public API Scope**
   - Are there APIs accessible without authentication?
   - Only `public_version`, `public_health`?

5. **Migration Period**
   - How long should the deprecation period last? (Current proposal: v26.1 ~ v27.0, approximately 6 months)
   - Is a longer period needed?

6. **Boundary Between Scope and Filter**
   - Clear distinction: Scope for permission boundary, Filter for filtering
   - But potential confusion in some use cases?

## References

- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
