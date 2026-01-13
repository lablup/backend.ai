---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Reference Document
Created: 2025-11-05
Parent: BEP-1012-main.md
---

# BEP-1012 RBAC Design Decisions

This document records key design decisions made during the development of the BEP-1012 RBAC feature specification.

## Decision: Replace Grant Operations with Role Assignment Entity

### Background

In the initial design phase, the RBAC system included special "grant" operations for delegating permissions to other users. These grant operations (grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete, grant:assign) were proposed to enable users to share resources and delegate permissions.

### Initial Design (Grant Operations)

**Concept**: Special operations that enable permission delegation

**Structure**:
- Define grant operations as special permission types
- `grant:create`: Grant create permission to others
- `grant:read`: Grant read permission to others
- `grant:update`: Grant update permission to others
- `grant:soft-delete`: Grant soft-delete permission to others
- `grant:hard-delete`: Grant hard-delete permission to others
- `grant:assign`: Grant assign permission to others (for Role entity)

**Example Flow**:
```
When User A wants to share VFolder X with User B:
→ User A has grant:read permission on VFolder X
→ User A grants read Object Permission to User B
→ User B can now read VFolder X
```

**Problems Identified**:
1. **Inconsistency**: Grant operations are special-purpose, unlike other standard operations (create, read, update, delete)
2. **Complexity**: Requires a separate permission type system (grant:* operations)
3. **Role Assignment Conflict**: In a situation where Role and Role Assignment are separate entities, requiring a special `assign` operation only for the Role entity creates inconsistency
4. **Industry Practice**: Major cloud providers (AWS, Azure, GCP) use assignment-based models, not grant operations

### Design Evolution

#### Phase 1: Separating Role and Role Assignment Entities

The team recognized that role assignments should be separate entities from roles themselves. This follows the Azure RBAC pattern:

**Rationale**:
- Role defines permissions (what can be done)
- Role Assignment maps users to roles (who has which role)
- Separation enables flexible assignment management without modifying roles

**Benefits**:
- Aligns with industry standards (Azure, AWS IAM)
- Clear audit trail for role assignments
- Reusable roles for multiple users
- Supports role assignment metadata (expiration, grantor, etc.)

#### Phase 2: Reconsidering the Need for Grant Operations

With Role Assignment becoming a separate entity, the following question arose:

**Can Role and Role Assignment completely replace grant operations?**

**Analysis**:

Traditional grant approach:
```
User A grants VFolder X read permission to User B:
1. User A has grant:read permission
2. System creates Object Permission for User B
```

Role Assignment approach:
```
User A grants VFolder X read permission to User B:
1. User A creates/retrieves Role with VFolder X read Object Permission
2. User A creates Role Assignment connecting User B to that Role
```

**Key Insight**: The Role Assignment approach does not cause role explosion
- One "VFolder-X-Reader" Role can be shared across multiple Role Assignments
- Number of Roles stays low, only number of Assignments increases

#### Phase 3: Comparative Analysis

**Grant Operations Approach**:

Pros:
- ✅ Intuitive: "grant" aligns with users' mental model
- ✅ Direct: Single operation for permission delegation
- ✅ Fewer entities to manage

Cons:
- ❌ Special-purpose operations undermine consistency
- ❌ Complex permission model with two operation types (general + grant)
- ❌ Misaligned with industry standards

**Role Assignment Approach**:

Pros:
- ✅ Fully consistent permission model
- ✅ All permissions managed through standard CRUD operations
- ✅ Aligns with industry standards (Azure, AWS, GCP)
- ✅ Better audit trail
- ✅ More flexible (can add metadata to assignments)

Cons:
- ❌ Two-step process (create/retrieve role, then create assignment)
- ❌ More entities to manage
- ❌ Less intuitive for simple sharing use cases

### Final Decision

**Adopt Role Assignment Approach with Optional Convenience API**

**Decision**: Replace all grant operations with Role and Role Assignment management, but provide convenience API for backward compatibility.

**Implementation Strategy**:

#### Option 1: Pure RBAC (Recommended for New Integrations)
```
To share VFolder X with User B:
1. Create/retrieve Role with VFolder X Object Permissions
2. Create Role Assignment: User B → Role
```

#### Option 3: Convenience API (For Backward Compatibility)
```
To share VFolder X with User B:
1. Call sharing API specifying target user and permissions
2. System automatically:
   - Creates/retrieves appropriate Role
   - Creates Role Assignment
```

**Rationale**:
1. **Consistency**: Pure RBAC model using only standard operations
2. **Industry Alignment**: Matches Azure RBAC, AWS IAM patterns
3. **Flexibility**: Role Assignment entity supports rich metadata
4. **Backward Compatibility**: Convenience API maintains existing workflows
5. **Gradual Migration**: Users can transition from convenience API to direct RBAC over time

### Impact on Specification

**Removed**:
- Grant Operations section (grant:create, grant:read, grant:update, grant:soft-delete, grant:hard-delete)
- `assign` operation (special-purpose for Role entity only)
- `grant:assign` grant operation

**Added**:
- Role Assignment as a separate entity
- Permission Delegation section explaining Role + Role Assignment approach
- VFolder sharing use case including both convenience API and direct RBAC approaches
- Cross-scope Object Permissions for flexible sharing

**Changed**:
- Operations: Unified to create, read, update, soft-delete, hard-delete for all entities
- Use cases: Updated to use Role Assignment creation instead of grant operations
- Scope rules: Simplified to focus on scope-local management rather than hierarchical grant delegation

### Comparison with Other Systems

#### AWS IAM
- Uses `AttachUserPolicy`, `DetachUserPolicy` - similar to our Role Assignment approach
- Policy attachment is separate from policy definition
- ✅ Matches our design

#### Azure RBAC
- Treats Role Assignment as a first-class entity
- Separate permission for managing role assignments: `Microsoft.Authorization/roleAssignments/write`
- ✅ Directly matches our design

#### Google Cloud IAM
- Uses "Policy Bindings" to assign roles to users
- Bindings are managed separately from role definitions
- ✅ Conceptually similar to our Role Assignment

### Benefits Realized

1. **Unified Permission Model**: All permissions managed through standard CRUD operations
2. **Simplified Mental Model**: Roles define permissions, Assignments grant them to users
3. **Better Scalability**: Role reuse reduces entity count compared to per-user grant records
4. **Enhanced Audit**: Role Assignment entity tracks who, when, and expiration
5. **Industry Standard**: Matches patterns from major cloud providers
6. **Flexible Evolution**: Easy to add features like assignment approval workflows, temporary access, etc.

### References

- [BEP-1012: Backend.AI Role-Based Access Control (RBAC) Feature Specification](./BEP-1012-main.md)
- [BEP-1008: Backend.AI Role-Based Access Control (RBAC) Technical Implementation](./BEP-1008-RBAC.md)
- [Azure RBAC: Role Assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments)
- [AWS IAM: Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
