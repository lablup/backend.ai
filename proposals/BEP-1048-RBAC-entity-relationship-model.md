---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Draft
Created: 2026-02-10
Created-Version: 26.2.0
Target-Version:
Implemented-Version:
---

# RBAC Entity Relationship Model

## Related Issues

- JIRA: [BA-4179](https://lablup.atlassian.net/browse/BA-4179) — Implement RBAC Entity Relationship Model
- JIRA: [BA-4218](https://lablup.atlassian.net/browse/BA-4218) — BEP-1048 document registration
- GitHub: #8531
- Related BEPs:
  - [BEP-1008: RBAC](BEP-1008-RBAC.md) - Original RBAC technical design
  - [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md) - RBAC feature specification

## Motivation

BEP-1008 and BEP-1012 define RBAC roles, permissions, and scope hierarchy, but do not specify how **entity visibility** integrates with RBAC. Currently:

- Each entity type implements its own visibility logic, determining which instances a user can see.
- No unified model exists for how entity relationships affect traversal and access.
- Association tables (`AssociationContainerRegistriesGroupsRow`, `ScalingGroupForDomainRow`, etc.) are scattered across the codebase with inconsistent patterns.

This proposal introduces an **Entity Relationship Model** that classifies all entity relationships into a small set of types, unifying visibility logic into a single table (`association_scopes_entities`) and a set of code-level metadata annotations.

## Current Design

### Fragmented Visibility

Entity visibility is currently handled per-entity:

- **ResourceGroup**: Uses separate junction tables (`sgroups_for_domains`, `sgroups_for_groups`, `sgroups_for_keypairs`) to determine which resource groups are visible to which scopes.
- **ContainerRegistry**: Uses `association_container_registries_groups` junction table for project-level visibility.
- **VFolder**: Uses `vfolder_permissions` and `vfolder_invitations` for sharing.
- **Session/Kernel/Agent**: Visibility determined by ad-hoc query joins.

### Problems

1. **Inconsistent patterns**: Each entity type uses a different mechanism for scope-based visibility.
2. **No traversal model**: No unified way to determine what entities are reachable from a given entry point.
3. **DB table proliferation**: Each N:N scope mapping requires its own junction table.
4. **RBAC gap**: BEP-1008/1012 define *what operations* a user can perform, but not *which entities* are visible in the first place.

## Proposed Design

### Entity Relationship 3-Type Model

All entity relationships are classified into exactly three types:

| Type | Semantics | Storage | GQL Sub-field | Permission |
|------|-----------|---------|---------------|------------|
| `guarded` | Independent entity; no edge relationship | N/A (no edge) | No | Separate RBAC check required |
| `auto` | Composition; permission delegation from parent | DB (`association_scopes_entities`, `relation_type=auto`) | Yes | Parent's CRUD inherited → child's CRUD |
| `ref` | Read-only reference; no permission delegation | DB (`association_scopes_entities`, `relation_type=ref`) | Yes (read-only) | Parent's CRUD → child's READ only |

Key semantics:

- **Guarded** is not an edge — it represents the absence of a relationship. A's permissions are independent of B's. B requires its own Root Query with its own RBAC check. No GQL sub-field exists between them.
- **Auto** edges are stored per-instance in `association_scopes_entities` with `relation_type=auto`. If you have CRUD on parent A, you have CRUD on child B. No separate permission check needed for B. The parent can list and mutate its auto children.
- **Ref** edges are stored per-instance in `association_scopes_entities` with `relation_type=ref`. If you have CRUD on parent A, you get READ-only on child B. CUD on B is not permitted via this path. The parent can list its ref children, but no permission delegation occurs. Further traversal from B requires a separate guarded-level permission check.
- A `RelationType` enum (`auto`, `ref`) is defined in code. The `association_scopes_entities` table includes a `relation_type` column to distinguish auto from ref edges.

### Discarded Alternatives

- **Reference Type (separate GQL types for ref entities)**: Rejected. Ref entities expose all fields.
- **Denormalization (flat fields)**: Rejected. Increases maintenance burden.

### Guarded Root Query Targets

Guarded entities are entry points for Root Queries. RBAC permission checks are performed at this level.

| Scope | Guarded Targets |
|-------|----------------|
| User | Session, VFolder, Endpoint, KeyPair, NotificationChannel |
| Project | Session, VFolder, Endpoint, Network, ResourceGroup, ContainerRegistry, StorageHost, Artifact, SessionTemplate |
| Domain | User, Project, Network, ResourceGroup, ContainerRegistry, StorageHost, AppConfig |

**Superadmin-only (no scope context):**
- DomainRow, ResourcePresetRow, UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow, RoleRow, AuditLogRow, EventLogRow

Since guarded means no edge relationship, there is no "Guarded Edges" diagram. Each guarded entity is independently queried at the Root Query level with its own RBAC check.

### Auto Edges

Auto edges represent composition relationships with **permission delegation** via `association_scopes_entities`. If A ━━auto━━► B:

- A's CRUD permissions are inherited by B (full CRUD delegation).
- No separate RBAC check is needed for B.
- B appears as a GQL sub-field of A.

```
Session ━━auto━━► Kernel
Session ━━auto━━► Routing
Session ━━auto━━► SessionDependency
Session ━━auto━━► SessionSchedulingHistory
ResourceGroup ━━auto━━► Agent ━━auto━━► Kernel
ContainerRegistry ━━auto━━► Image ━━auto━━► ImageAlias
VFolder ━━auto━━► VFolderPermission
VFolder ━━auto━━► VFolderInvitation
Endpoint ━━auto━━► EndpointToken
Endpoint ━━auto━━► EndpointAutoScalingRule
Endpoint ━━auto━━► DeploymentRevision
Endpoint ━━auto━━► DeploymentPolicy
Endpoint ━━auto━━► DeploymentAutoScalingPolicy
Endpoint ━━auto━━► DeploymentHistory
Endpoint ━━auto━━► Routing
Artifact ━━auto━━► ArtifactRevision
NotificationChannel ━━auto━━► NotificationRule
Kernel ━━auto━━► KernelSchedulingHistory
Routing ━━auto━━► RouteHistory
ResourceGroup ━━auto━━► DomainFairShare
ResourceGroup ━━auto━━► ProjectFairShare
ResourceGroup ━━auto━━► UserFairShare
Domain ━━auto━━► DomainFairShare
Project ━━auto━━► ProjectFairShare
Project ━━auto━━► Session
User ━━auto━━► UserFairShare
Role ━━auto━━► Permission
Role ━━auto━━► UserRole
```

### Ref Edges

Ref edges represent read-only references stored per-instance in `association_scopes_entities` with `relation_type=ref`, but with **no permission delegation**. If A ──ref──► B:

- A's CRUD permissions grant READ-only on B. CUD on B is not permitted via this path.
- The parent can list its ref children (the row in `association_scopes_entities` enables this).
- B appears as a read-only GQL sub-field of A.
- Further traversal from B requires a separate guarded-level permission check (same as accessing an independent entity).

```
Session ──ref──► Agent, ResourceGroup, KeyPair
Kernel ──ref──► Image, Agent
Routing ──ref──► Endpoint (from Session), Session (from Endpoint)
VFolderPermission ──ref──► User
VFolderInvitation ──ref──► User (invitee, inviter)
Endpoint ──ref──► Image, User (created_user, session_owner)
User ──ref──► UserResourcePolicy, KeyPair (main_access_key)
KeyPair ──ref──► KeyPairResourcePolicy, User
Project ──ref──► ProjectResourcePolicy
Network ──ref──► Domain, Project
UserRole ──ref──► User
Artifact ──ref──► ArtifactRegistry (HuggingFaceRegistry, ReservoirRegistry)
NotificationChannel ──ref──► User (created_by)
NotificationRule ──ref──► User (created_by)
```

### Key Principles

1. **RBAC checks at Root Query only.** After the entry point, `auto`/`ref`/unregistered determines traversal scope.
2. **Relationship type is an edge property, not an entity property.** The same entity can have different roles depending on the entry path. For example, Agent is `auto` from ResourceGroup but `ref` from Session/Kernel. An entity does not inherently "know" whether it is auto or ref — the parent→child edge determines this.
3. **Auto-only entities have no standalone root query.** They are always accessed through their parent.
4. **RBAC/Visibility separation.** RBAC validates scope + operation. Visibility is resolver-level business logic.

### Resolver Traversal Context

Since relationship type is an edge property, the GQL resolver for a child entity does not inherently know whether it was reached via `auto` or `ref`. After a `ref` edge, further traversal requires a separate guarded-level permission check — the parent's authorization does not carry forward.

Example — the same `Agent` entity behaves differently by entry path:

```
resourceGroup { agents { kernels { ... } } }
  └─ auto ──► Agent ──► auto continues → Kernel accessible (CRUD inherited)

session { agent { kernels { ... } } }
  └─ ref ──► Agent (READ only) ──► further traversal requires separate permission check
```

To enforce this, the **parent resolver** (which owns the edge metadata) must propagate a traversal context to downstream resolvers. After a ref edge, the authorization context resets — any further access requires an independent permission check, equivalent to a guarded Root Query. The specific mechanism (e.g., resolver context flag, middleware decorator) is an implementation detail to be decided in Phase 2–3.

### Query Constraints

#### Scope Inference

| Scope | Implicit Inference | Method |
|-------|--------------------|--------|
| User | Yes | Viewer identity |
| Domain | Yes | `viewer.domain` |
| Project | **No** | Multiple project membership possible; `project_id` required |

#### Root Query Enabled Entities (22 types)

These entities have standalone Root Queries with RBAC checks. Only these entities are stored in `association_scopes_entities` as scope→entity mappings.

**Scoped (14 types):**
- SessionRow, VFolderRow, EndpointRow, KeyPairRow, NotificationChannelRow
- NetworkRow, ScalingGroupRow, ContainerRegistryRow, StorageHostRow
- ArtifactRow, SessionTemplateRow
- UserRow, ProjectRow, AppConfigRow

**Superadmin-only (8 types):**
- DomainRow, ResourcePresetRow, UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow, RoleRow, AuditLogRow, EventLogRow

#### Auto-only Entities (22 types)

No standalone single-item or list queries. Always accessed through parent:

| Entity | Parent (auto edge) | Access Pattern |
|--------|-------------------|----------------|
| KernelRow | Session, Agent | `session { kernels }` |
| RoutingRow | Session, Endpoint | `session { routings }` |
| SessionDependencyRow | Session | `session { dependencies }` |
| SessionSchedulingHistoryRow | Session | `session { schedulingHistory }` |
| AgentRow | ResourceGroup | `resourceGroup { agents }` |
| ImageRow | ContainerRegistry | `containerRegistry { images }` |
| ImageAliasRow | Image | `image { aliases }` |
| VFolderPermissionRow | VFolder | `vfolder { permissions }` |
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

### Entities Outside RBAC Scope

The following entities are intentionally excluded from the 3-Type Model:

**System Internal / Infrastructure:**
- ResourceSlotTypeRow, AgentResourceRow, ResourceAllocationRow (scheduler internals)
- ServiceCatalogRow, ServiceCatalogEndpointRow (internal service discovery)
- StorageNamespaceRow (ObjectStorage internal partitioning)
- EntityFieldRow (RBAC metadata)
- ErrorLogRow (system error log)

**Registry Implementations (accessed via Artifact ref):**
- HuggingFaceRegistryRow, ReservoirRegistryRow, ArtifactRegistryRow

### StorageHost Migration

StorageHost is a planned entity that does not yet exist as a DB table:

- **Current state**: `VFolderRow.host` stores a `"proxy_name:volume_name"` string. `allowed_vfolder_hosts` is a JSON column scattered across Domain/Group/KeyPairResourcePolicy.
- **Plan**: Normalize into a `StorageHostRow` DB table, unifying existing `ObjectStorageRow` and `VFSStorageRow`. Positioned like ContainerRegistry with Domain/Project scope guarded and N:N mapping.

## Migration / Compatibility

### DB Schema Changes

1. **New table**: `association_scopes_entities` — stores per-instance auto and ref edges with a `relation_type` column (`auto` for permission delegation, `ref` for read-only listing).
2. **Remove**: `permission_groups` table — fields (`role_id`, `scope_type`, `scope_id`) moved directly into `permissions`.
3. **Remove**: `object_permissions` table — replaced by entity-as-scope pattern.

### Association Table Replacement

Existing junction tables will be replaced by `association_scopes_entities`:

| Current Table | Replacement |
|--------------|-------------|
| `AssociationContainerRegistriesGroupsRow` | `association_scopes_entities` (ContainerRegistry, Project scope) |
| `ScalingGroupForDomainRow` | `association_scopes_entities` (ResourceGroup, Domain scope) |
| `ScalingGroupForProjectRow` | `association_scopes_entities` (ResourceGroup, Project scope) |
| `ScalingGroupForKeypairsRow` | `association_scopes_entities` (ResourceGroup, User scope) |

`AssocGroupUserRow` (project membership) remains separate as it serves Visibility logic only, not RBAC.

### Final RBAC Tables

After migration, the core RBAC tables are:

- `roles`
- `user_roles`
- `permissions` (with `role_id`, `scope_type`, `scope_id` directly)
- `association_scopes_entities`

### Backward Compatibility

- Sharing is implemented via system role entity-scope permission INSERT/DELETE.
- Project membership is managed through `user_roles` and excluded from RBAC scope chain (Visibility only).

## Implementation Plan

1. **Phase 1: Core Schema**
   - Create `association_scopes_entities` table
   - Migrate `permissions` table to include `role_id`, `scope_type`, `scope_id` directly
   - Remove `permission_groups` and `object_permissions` tables

2. **Phase 2: Entity Classification Metadata**
   - Define `RelationType` enum in code
   - Annotate all entity types with their relationship metadata (auto/ref edges)
   - Implement CTE-based scope chain traversal for guarded lookups

3. **Phase 3: Root Query RBAC Enforcement**
   - Integrate guarded checks into Root Query resolvers
   - Implement auto-traversal and ref-termination in nested resolvers

4. **Phase 4: Association Table Migration**
   - Migrate existing junction tables to `association_scopes_entities`
   - Remove deprecated junction tables
   - Migrate StorageHost from string-based to normalized DB table

## References

- [BEP-1008: RBAC](BEP-1008-RBAC.md)
- [BEP-1012: RBAC (detailed)](BEP-1012-RBAC.md)
