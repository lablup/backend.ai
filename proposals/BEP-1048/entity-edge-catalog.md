# Entity Edge Catalog

This document is the authoritative reference for all entity edges in the BEP-1048 3-Type Model.
See [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md) for definitions of `auto`, `ref`, and `guarded`.

## Edge Semantics Summary

| Type | Permission | Storage | Scope Chain |
|------|-----------|---------|-------------|
| `auto` | Role permissions flow through | `association_scopes_entities` (`relation_type=auto`) | CTE upward traversal propagates visibility to child scopes |
| `ref` | READ-only (no CUD delegation) | `association_scopes_entities` (`relation_type=ref`) | CTE upward traversal with READ-only constraint |
| `guarded` | Independent RBAC check required | N/A (no edge) | N/A |

## Scope Chain Traversal

Entity visibility is resolved by CTE upward traversal of the scope hierarchy:

```
User:U → Project:P → Domain:D → Global
```

When a user queries for accessible entities, the system traverses upward through
`association_scopes_entities` at each scope level. The final result is the **union** of
entities found at all levels.

**Auto edges**: permissions flow through at every level in the chain.
**Ref edges**: only READ permission flows through; CUD requires a separate RBAC check.

### Example: ResourceGroup visibility

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

This matches the current union-based cascading behavior: a Domain-level mapping
makes the ResourceGroup accessible to **all** users and projects within that domain,
without requiring per-project or per-user entries.

---

## Auto Edges

### Scope → Entity (N:N scope-accessibility mappings)

These edges map entities to the scopes in which they are accessible.
Unlike composition edges below, these are **N:N** relationships — one entity can be
mapped to multiple scopes, and one scope can contain multiple entities.

Visibility propagates downward through the scope hierarchy via CTE upward traversal.

```
Domain  ━━auto━━► ResourceGroup
Domain  ━━auto━━► ContainerRegistry
Project ━━auto━━► ResourceGroup
Project ━━auto━━► ContainerRegistry
User    ━━auto━━► ResourceGroup
```

**Migration from legacy tables:**

| Legacy Table | Replacement | Edge |
|---|---|---|
| `ScalingGroupForDomainRow` | `(scope=Domain, entity=ResourceGroup, auto)` | Domain ━━auto━━► ResourceGroup |
| `ScalingGroupForProjectRow` | `(scope=Project, entity=ResourceGroup, auto)` | Project ━━auto━━► ResourceGroup |
| `ScalingGroupForKeypairsRow` | `(scope=User, entity=ResourceGroup, auto)` | User ━━auto━━► ResourceGroup |
| `AssociationContainerRegistriesGroupsRow` | `(scope=Project, entity=ContainerRegistry, auto)` | Project ━━auto━━► ContainerRegistry |

### Scope → Member (1:N scope-composition)

These edges represent the scope hierarchy's own composition.

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

### Entity → Sub-entity (1:N composition)

These edges represent parent entities that own child sub-entities.
The child has no standalone Root Query and is always accessed through the parent.

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

## Ref Edges

Read-only references. Parent's CRUD grants READ-only on child.
Further traversal from the child requires a separate guarded-level RBAC check.

### Scope → Entity (visibility-only mapping)

```
Project ━━ref━━► User  (project membership — visibility only, no permission delegation)
```

**Migration:**

| Legacy Table | Replacement | Edge |
|---|---|---|
| `AssocGroupUserRow` | `(scope=Project, entity=User, ref)` | Project ━━ref━━► User |

### Entity → Referenced Entity

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

## Guarded Entities

These entities have no edge relationship with each other.
Each requires an independent Root Query with its own RBAC check.

**Scoped (Root Query + Mutation):**
- SessionRow, VFolderRow, EndpointRow, KeyPairRow, NotificationChannelRow
- NetworkRow, ScalingGroupRow (ResourceGroup), ContainerRegistryRow, StorageHostRow
- ImageRow, ArtifactRow, SessionTemplateRow
- UserRow, ProjectRow, AppConfigRow

**Superadmin-only (Root Query + Mutation):**
- DomainRow, ResourcePresetRow
- UserResourcePolicyRow, KeyPairResourcePolicyRow, ProjectResourcePolicyRow
- RoleRow

**Read-only (Root Query, no Mutation):**
- AuditLogRow, EventLogRow
