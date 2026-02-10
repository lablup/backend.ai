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

| Type | Semantics | Storage | Traversal |
|------|-----------|---------|-----------|
| `guarded` | Root Query entry point; scope-based access control via CTE recursive lookup | DB per-instance (`association_scopes_entities`) | Entry point, RBAC check performed |
| `auto` | Composition; automatically accessible when parent is accessible | Code (type-level metadata) | Continue traversal |
| `ref` | Reference; all fields readable, no further traversal | Code (type-level metadata) | Terminate traversal |

Key design decisions:

- Only `guarded` relationships are stored in the database. `auto` and `ref` are defined as code-level type metadata.
- No `relation_type` column is needed in the DB table since it only stores guarded relationships.
- A `RelationType` enum is defined in code for type-level annotations.

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
| Global | Domain, ResourcePreset, ResourcePolicy, AuditLog, EventLog |

### Auto Edges

Auto edges represent composition relationships. When a parent entity is accessible, its auto children are automatically accessible without additional RBAC checks. Traversal continues through auto edges.

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
User ━━auto━━► UserFairShare
Role ━━auto━━► Permission
Role ━━auto━━► UserRole
```

### Ref Edges

Ref edges represent read-only references. All fields of the referenced entity are readable, but traversal terminates — no further edges are followed from a ref target.

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

Since relationship type is an edge property, the GQL resolver for a child entity does not inherently know whether it was reached via `auto` or `ref`. However, `ref` edges require traversal termination — nested entity fields should not be resolved further from a ref target.

Example — the same `Agent` entity behaves differently by entry path:

```
resourceGroup { agents { kernels { ... } } }
  └─ auto ──► Agent ──► auto continues → Kernel accessible

session { agent { kernels { ... } } }
  └─ ref ──► Agent ──► traversal terminates → Kernel NOT accessible
```

To enforce this, the **parent resolver** (which owns the edge metadata) must propagate a traversal context to downstream resolvers. The child entity itself does not need to be aware of its classification — it only needs to check whether traversal is permitted in the current context. The specific mechanism (e.g., resolver context flag, middleware decorator) is an implementation detail to be decided in Phase 2–3.

### Query Constraints

#### Scope Inference

| Scope | Implicit Inference | Method |
|-------|--------------------|--------|
| User | Yes | Viewer identity |
| Domain | Yes | `viewer.domain` |
| Project | **No** | Multiple project membership possible; `project_id` required |
| Global | Yes | Superadmin; no parameter needed |

#### Guarded Entities (22 types)

Single-item queries are supported for all guarded entities. List queries depend on scope:

**User + Project Scope:**
- SessionRow, VFolderRow, EndpointRow
- List: User scope implicit / Project scope requires `project_id`

**User Scope only:**
- KeyPairRow, NotificationChannelRow
- List: Implicit (viewer)

**Project Scope only:**
- ArtifactRow, SessionTemplate(session_templates)
- List: Requires `project_id`

**Project + Domain Scope:**
- NetworkRow, ScalingGroupRow, ContainerRegistryRow, StorageHostRow
- List: Project scope requires `project_id` / Domain scope implicit (`viewer.domain`)

**Domain Scope only:**
- UserRow, GroupRow (Project), AppConfigRow
- List: Implicit (`viewer.domain`)

**Global Scope only (superadmin):**
- DomainRow, ResourcePresetRow, UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow, RoleRow, AuditLogRow, EventLogRow
- List: Implicit

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

1. **New table**: `association_scopes_entities` — stores all guarded scope-entity relationships.
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
