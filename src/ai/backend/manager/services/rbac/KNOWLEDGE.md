---
name: rbac-service-shapes
type: decision-table
description: RBAC service knowledge - why a relation targets no entity type, why membership is scope-shaped, which roles a member may be given
scope: src/ai/backend/manager/services/rbac
keywords: [RBACService, RBACRepository, V2RBACWriteOps, RelationGroup, CreateRelationAction, EnrollAction, GrantRolesAction, RelationCreator, RelationPurger, relation, enroll, withdraw, grant_roles, revoke_roles]
sources:
  - src/ai/backend/manager/services/rbac
  - src/ai/backend/manager/repositories/rbac
  - src/ai/backend/manager/repositories/ops/v2/rbac
  - proposals/BEP-1075-entity-relation-operations.md
  - proposals/BEP-1076-project-membership.md
generated:
  by: claude-code/opus-5
  at: 2026-08-26
status: stable
---

# RBAC service — Knowledge

> Rules: `../AGENTS.md`. Where a relation stands:
> `proposals/BEP-1075-entity-relation-operations.md`. Organization membership:
> `proposals/BEP-1076-project-membership.md`.

Three groups of operations that put two things together sit in one service: links
between entities, membership of an organization, and the roles a member holds.

## A relation targets no entity type

- What it writes is not an entity, so "the permission on this type within this scope"
  is not a question that can be asked. What is left is the permission on the scope
  itself.
- Both scopes have to permit the run. One denial refuses the whole run.
- Its audit row names no entity and no kind, which is why `audit_logs.entity_type` is
  nullable.
- The catalog records it with no entity type either. `GLOBAL_ENTITY_TYPE` does not
  stand for that: it names an operation over every entity, and a relation targets none.
- Hence `relation_group()` rather than an entity group — a group is answered for by an
  entity type, and a relation is not.

## Membership is the contained case, so it is scope-shaped

- The organization is the scope and the user is what the run acts on inside it. One
  scope is enough.
- Enrolment declares `CREATE` and withdrawal `PURGE`. Withdrawal removes the membership
  row; it does not remove the user.
- Granting and revoking roles declare `UPDATE`, and leave the membership alone.

## Roles come only from that organization

- A named role the organization does not hold is refused, in the transaction that
  writes. Membership must not become a path for attaching an unrelated role.
- Enrolling without naming a role gives the organization's auto-assign roles.
- Who granted it is required. The system-provisioned path runs inside entity creation
  and does not come through this operation.
- Withdrawal takes back every role of that organization, with nothing recording which
  of them the join gave: a role may only be named from the organization's own, so one
  held by a non-member is not a state that arises.
