---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-26
Created-Version: 26.9.0
Target-Version:
Implemented-Version:
---

# Project Membership

## Related Issues

- BEP-1075 (Entity Relation Operations) — the relation write primitive this uses
- BA-7467 (how an action designates an entity)

## Motivation

Putting a user in a project does two things — it adds the relation and it grants a role. The two
are fused today, and the operation cannot reach someone whose user id is unknown.

- Joining always drags the scope's `auto_assign` roles along, so membership and role state cannot
  be told apart
- A user id is required, so someone without an account yet cannot be added

Handing permission to another person already has two branches, immediate and by invitation.
Project membership takes the same pair.

## Current Design

### Membership today

| | Current |
|---|---|
| Table | `association_groups_users` — `DEPRECATED`, being moved to `association_scopes_entities` |
| Role | `ScopeUserMember.assign_role_on()` grants the scope's `auto_assign` roles on every join |
| Designation | a user id is required |

`ScopeUserMember` states the fusion itself — *"membership always grants the scope's auto_assign
roles (idempotently), so membership and role state cannot drift apart."*

`UserUpdater.group_ids` carries the same membership through the edit path. It is not a column, so
the write path syncs it beside `build_values()` (BEP-1075).

### A domain is not this shape

A user belongs to exactly one domain, held as `users.domain_id` with a foreign key. There is no
domain ↔ user relation table, and the column is `NOT NULL`.

| | Project | Domain |
|---|---|---|
| Storage | `association_groups_users` | `users.domain_id` column |
| Cardinality | many to many | one to many |

So a domain is not invited into. A user is created under a domain, and moving between domains is
an edit of the user, not a membership operation. This proposal covers projects only.

### The invitation that exists

`entity_invitations` offers **access to an entity**.

| Column | Value |
|---|---|
| `target_entity_type` · `target_entity_id` | polymorphic, no foreign key |
| `permission_cap` | the ceiling applied on acceptance |
| `invitee_email` | an email — names someone with no account yet |
| `status` | unique only while `pending` |

Project membership does not fit that shape: the value to carry is a role rather than a ceiling, and
acceptance writes something else.

## Proposed Design

### Two branches

| | When it takes effect | Designation | The other party's account |
|---|---|---|---|
| grant | immediately | user id | must exist |
| invitation | on acceptance | email | need not exist |

The same pair as handing out permission.

### What each branch does

```
1. add the relation      project ↔ user
2. grant the role        the named role if there is one, otherwise the project's auto_assign roles
```

Two writes in one transaction, not one fact — so the `ScopeUserMember` fusion comes apart.

### The role is chosen from that project's roles

Only a role enrolled in that project's scope may be named. Otherwise membership becomes a path for
attaching an unrelated role.

### Permission

Putting a user inside a project means the scope is **one**.

| Axis | Value |
|---|---|
| `scope_targets()` | the project |
| `entity_type()` | `user` |

Naming a role adds one more.

| | What is asked |
|---|---|
| No role named (`auto_assign`) | the `user` permission at the project scope |
| A role named | that, plus **the permission to grant that role** |

Nobody may attach a role they could not grant.

### Removal

```
remove the relation  +  take back the roles enrolled in that project from this user
```

**Nothing has to record which role came from this membership.** A role may only be chosen from that
project's own, so holding a project-scoped role without being a member of that project is not a
state that arises. What comes back is the intersection of "roles enrolled in that project" and the
roles this user holds.

The read already exists — `ScopedRoleOperationScope` selects the roles enrolled in one scope.

Audit logs are for observing. What to take back is not read from audit rows: they are swept by
retention and go away.

### The invitation has its own table

A different axis from `entity_invitations`.

| | `entity_invitations` | Project invitation |
|---|---|---|
| What is offered | access to an entity | project membership |
| Value carried | `permission_cap` | a role, or `auto_assign` |
| Acceptance writes | one membership row | the relation and the role |

The form matches: addressed by email, accepted or declined, unique only while pending.

**After acceptance the invitation and the state part ways.** Deleting the invitation leaves the
relation and the role in place. An invitation is an offer, not a permission — the same rule the
permission invitation follows.

## Migration / Compatibility

- Undo the `ScopeUserMember` role fusion. Granting the role becomes the second step of the
  membership operation
- Take `group_ids` off `UserUpdater`. Enrolling in a project is its own operation
- Stop moving `association_groups_users` into `association_scopes_entities`. Project membership is
  a business relation, not a fact for the permission graph (BEP-1075)
- The relation row is written through BEP-1075's relation primitive; the service composes it with
  the role grant

## Implementation Plan

Decided once this BEP settles.

## Open Questions

- How the invitation table carries the role — one role id column, and how "none named
  (`auto_assign`)" is told apart from it
- Received invitations span two tables. Showing one list to a user needs somewhere to merge them
- What happens when the role named at invitation time is gone by the time it is accepted
- `UserUpdater.domain_name` stays an edit of the user, but it is a move: the identifier becomes
  `domain_id` (resolved from a name by a lookup at the edge), and what else the move has to carry
  — the graph membership, the projects of the old domain, the domain copied onto sessions and
  vfolders — is not settled here
