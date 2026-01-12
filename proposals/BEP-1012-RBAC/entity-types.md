---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Draft
Created: 2025-01-09
Parent: BEP-1012-main.md
---

# BEP-1012 RBAC Entity and Field Types

This document defines the entity types and field types managed by the Backend.AI RBAC system.

## Entity Types

Entity types are the primary targets of permission checks in the RBAC system. Each entity type supports standard operations (create, read, update, soft-delete, hard-delete).

### Classification

| Category | Examples | Description |
|----------|----------|-------------|
| Resources | VFolder, Compute Session, Image, etc. | Actual business objects that are protected by RBAC |
| Scopes | Domain, Project, User | Organizational structures that define permission boundaries |
| Meta-entities | Role, {Entity}:assignment | Entities that constitute the RBAC system itself |

> **Note**: Update the checklist when the implementation is complete.

| Entity Type | Description | Dual Role | Notes | Migration | Validator | Repo Patterns |
|-------------|-------------|-----------|-------|:---------:|:---------:|:------------:|
| Compute Session | Computational workloads and containers | Entity only | | [ ] | [ ] | [ ] |
| Session Template | Predefined session configurations | Entity only | | [ ] | [ ] | [ ] |
| VFolder | Virtual folders for data storage | Entity only | | [ ] | [ ] | [ ] |
| Image | Container images for sessions | Entity only | | [ ] | [ ] | [ ] |
| Model Deployment | Model serving deployments | Entity only | | [ ] | [ ] | [ ] |
| Artifact | Models, packages, or images in artifact registries | Entity only | | [ ] | [ ] | [ ] |
| Artifact Registry | Registry for storing and managing artifacts | Entity only | | [ ] | [ ] | [ ] |
| Agent | Agent nodes providing computing resources | Entity only | | [ ] | [ ] | [ ] |
| Resource Group | Logical groups of agents | Entity only | | [ ] | [ ] | [ ] |
| Storage Host | Storage backend hosts | Entity only | | [ ] | [ ] | [ ] |
| App Config | Application configuration items | Entity only | | [ ] | [ ] | [ ] |
| Notification Channel | Channels for delivering notifications | Entity only | | [ ] | [ ] | [ ] |
| Notification Rule | Rules for triggering notifications | Entity only | | [ ] | [ ] | [ ] |
| Domain | Administrative domain grouping | Entity & Scope | | [ ] | [ ] | [ ] |
| Project | Project grouping within domains | Entity & Scope | | [ ] | [ ] | [ ] |
| User | User accounts | Entity & Scope | | [ ] | [ ] | [ ] |
| Role | Permission set definitions | Entity only | | [ ] | [ ] | [ ] |
| {Entity}:assignment | Mappings for sharing specific entities with other users | Entity only | e.g., vfolder:assignment, compute_session:assignment | [ ] | [ ] | [ ] |

**Notes**:
- **Dual Role**: Domain, Project, and User serve as both manageable entities and permission scopes.
- **{Entity}:assignment**: These are meta-entities that represent sharing relationships between users and specific entity instances.
- **Migration**: Indicates whether the RBAC migration for this entity type is complete.
- **Validator**: Indicates whether the RBAC permission validator for this entity type is implemented.
- **Repo Patterns**: Indicates whether the RBAC repository patterns (Creator/Granter/Purger) are implemented.

## Field Types

Field types are objects that do not have their own permission checks. Instead, permission checks for a field are delegated to the entity it belongs to. This design simplifies permission management for tightly coupled objects.

### Concept

When checking permissions for a field object:
1. The system looks up the associated entity via the `entity_fields` table
2. The permission check is performed against that entity instead
3. The operation type remains the same (e.g., `kernel:read` → `session:read`)

### Field Types Table

> **Note**: Update the checklist when the implementation is complete.

| Field Type | Entity Type | Description | Migration | Validator | Repo Patterns |
|------------|-------------|-------------|:---------:|:---------:|:-------------:|
| Kernel | Compute Session | Individual container instances within a session | [ ] | [ ] | [ ] |
| Session History | Compute Session | Historical records of session execution | [ ] | [ ] | [ ] |
| Model Revision | Model Deployment | Version snapshots of model deployments | [ ] | [ ] | [ ] |
| Deployment History | Model Deployment | Historical records of deployment changes | [ ] | [ ] | [ ] |
| Route | Model Deployment | Traffic routing configurations for model endpoints | [ ] | [ ] | [ ] |
| Route History | Model Deployment | Historical records of routing changes | [ ] | [ ] | [ ] |
| Endpoint Token | Model Deployment | Authentication tokens for model endpoints | [ ] | [ ] | [ ] |
| Artifact Revision | Artifact | Version snapshots of artifacts | [ ] | [ ] | [ ] |
| Object Permission | Role | Object-level permission assignments | [ ] | [ ] | [ ] |
| Permission | Role | Type-level permission definitions | [ ] | [ ] | [ ] |
| Permission Group | Role | Grouped permissions by scope | [ ] | [ ] | [ ] |

**Notes**:
- **Migration**: Indicates whether the RBAC migration for this field type is complete.
- **Validator**: Indicates whether the RBAC permission validator for this field type is implemented.
- **Repo Patterns**: Indicates whether the RBAC repository patterns (Creator/Granter/Purger) are implemented.

### Example: Kernel Permission Check

```
Permission check: "Does User A have read permission on Kernel X?"

1. Look up entity_fields table:
   - field_type: "kernel"
   - field_id: "X"
   → Returns: entity_type: "compute_session", entity_id: "session-123"

2. Perform permission check on the associated entity:
   - "Does User A have read permission on Compute Session session-123?"

3. Return the result of the entity's permission check
```

### Database Schema

The `entity_fields` table maps field objects to their associated entities:

```sql
CREATE TABLE entity_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(64) NOT NULL,  -- Entity type
    entity_id VARCHAR(64) NOT NULL,    -- Entity ID
    field_type VARCHAR(64) NOT NULL,   -- Field type
    field_id VARCHAR(64) NOT NULL,     -- Field ID
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    UNIQUE (entity_type, entity_id, field_type, field_id)
);

-- Indexes for efficient lookups
CREATE INDEX ix_entity_fields_entity_lookup ON entity_fields (entity_type, entity_id);
CREATE INDEX ix_entity_fields_field_lookup ON entity_fields (field_type, field_id);
```

## References

- [BEP-1012: RBAC Feature Specification](./BEP-1012-main.md) - Main feature specification
- [BEP-1008: RBAC Technical Implementation](./BEP-1008-RBAC.md) - Technical implementation details
