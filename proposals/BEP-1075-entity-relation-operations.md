---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-26
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Entity Relation Operations

## Related Issues

- BA-7467 (how an action designates an entity)
- BA-7468 · BA-7469 · BA-7470 (relocating the resource group, fair share and usage history specs)

## Motivation

Nothing decides what answers for the permission of an operation that links two entities.

Handling a relation through the virtual scope makes the graph answer. Not handling it there
means the operation has to answer for itself. Today each domain answers differently, so the
same relation lands in the permission graph or not depending on which API created it.

| Operation | Mapping row | Permission graph |
|---|---|---|
| Bind/unbind a resource group to a domain or project | writes | writes |
| Bind/unbind a resource group to a keypair | writes | does not |
| Edit a domain's or project's allowed resource groups | writes | writes |
| Name resource groups while creating or editing a domain | writes | does not |

**The virtual scope expresses ownership and nothing else.** A relation creates what business
logic reads, and the permission of that operation is answered by the two scopes it names.

## Current Design

### Relation tables

| Table | Links | Own data | Polymorphic side |
|---|---|---|---|
| `sgroups_for_domains` | resource group ↔ domain | none | no |
| `sgroups_for_groups` | resource group ↔ project | none | no |
| `sgroups_for_keypairs` | resource group ↔ keypair — the user is what it means to link | none | no |
| `association_groups_users` | user ↔ project | none | no |
| `user_roles` | user ↔ role | `granted_by` · `granted_at` | no |
| `idle_checker_bindings` | idle checker ↔ scope | `enabled` | yes |

No relation links three or more.

`session_dependencies` is a field of the depending session: the interaction runs one way, so it
is not a relation. `replica_groups` and `endpoint_tokens` are handled as deployment fields.

### Business logic reads the relation tables

`query_allowed_sgroups(domain_name, group, access_key)` reads the three tables as a union to
decide which resource groups a session may run on. Session creation and scheduling call it.
Project ↔ user searches read their relation table the same way.

### The virtual scope expresses ownership

A virtual scope edge carries one value, `permission_cap`, and the graph answers questions of the
form (user, entity, permission). A relation misses on both counts.

- The value to carry is not an amount of access — `enabled`, `granted_by`, or no value at all
- The subject is not a user — a domain schedules on a resource group

Owning something does not make an idle checker run or a role's permissions take effect. Ownership
and behavior are different axes.

## Proposed Design

### A relation is a third position

Neither entity nor field. An individual relation table is treated as neither of the two.

| | Position |
|---|---|
| The value is an amount of access and the subject is a user | virtual scope edge — no table |
| Any other link between two entities | **relation — its own table, its own operations** |
| The other side is a value that does not hold the relation | field |

### The operation takes two scopes and has no entity type

Both sides arrive as scopes. `entity_type` is `None`: what is created is not an entity, so there
is no "permission on this type within this scope" to ask. With no type, the only thing to ask is
the permission on each named scope itself.

```
link · unlink  →  permission on the left scope  AND  permission on the right scope
```

You must be able to touch both to link them, which is the same statement as both owning it.

### ops

```
create_relation (left, right, creator)
delete_relation (left, right, updater)     writes the lifecycle column as a constant
restore_relation(left, right, updater)     its reverse
purge_relation  (left, right, purger)      removes the row
```

The middle two are wired only for relations that declare a lifecycle column. Whoever holds the
permission on both scopes may turn a relation off and back on — turning it off is the same
permission as unlinking.

### The spec declares

Conflict handling and the lifecycle differ per relation, so ops does not decide them.

- With the unique constraint on the bare pair, a soft-deleted row occupies it — the create has to
  revive it
- With a partial index on (pair, alive), a new row is inserted and the history is kept

Which one it is comes from the create spec, as `index_elements` and what to do on conflict.

### The relation value is not exposed

A relation row's id never leaves. A read does not return the relation; it returns the entities the
relation reaches.

Reads need no new machinery. They sit on the two axes a scope operation already has.

| Axis | Value |
|---|---|
| `scope_targets()` | the domain — the permission is asked here |
| `operation_scopes()` | the condition derived from the relation table |

No edge per resource group is needed. Deriving permission from a relation turns into reference
counting once the same entity is reached through several relations, and a permission written as a
side effect of a business operation is invisible to the permission model.

### Relation-based search

Nine of the 48 `OperationScope` implementations already narrow their target through a relation
table as a subquery.

```python
class DomainResourceGroupOperationScope(OperationScope):
    def to_condition(self) -> QueryCondition:
        return lambda: ResourceGroupRow.id.in_(
            sa.select(ResourceGroupForDomainRow.resource_group_id)
            .where(ResourceGroupForDomainRow.domain_id == self.domain_id)
        )
```

Once a relation declares its table and its two reference columns, those nine come from that
declaration instead of being written by hand.

**Scope search as a whole does not collapse into one.** The other 39 carry the scope's id in a
column of the target row (`SessionRow.group_id == project_id`) and go through no relation. What
unifies is the nine that do.

## Migration / Compatibility

### What stays

The relation tables stay. Business logic reads them directly, and the virtual scope cannot express
what those reads decide.

### What goes

The permission graph edges the resource group relations wrote. Leaving them means only the
relations made through that path stay inherited by the domain's administrators.

### When a referenced entity is removed

`purge_relation` takes both values to remove a row. There is no operation that knows one side and
sweeps that entity's relations away.

FK CASCADE is a guarantee about logic, not a statement of ownership. It may be kept, but it cannot
be placed on a polymorphic reference.

Removing a long-lived entity such as a domain will be handled by the lifecycle manager, and the
relation rows it leaves are cleaned up there or by a retention sweep. A relation table has its own
`RetentionCategory` entry.

## Implementation Plan

Decided once this BEP settles.

## Open Questions

- How to find relation rows whose reference is gone. The reference is polymorphic
  (`entity_type`, `entity_id`), so an anti-join needs to know which table that type lives in.
  `virtual_scopes` already indexes live entities by `(scope_type, scope_id)` and could be matched
  against, but a row created before the virtual scope rollout may have no scope, which would read a
  live entity's relation as a dangling one.
- Whether to collapse the three `sgroups_for_*` into one polymorphic table — doing so makes
  `query_allowed_sgroups` a single query and turns a new kind of scope into a value.
- Whether to key the resource group ↔ keypair relation on the user — the access key was the wrong
  choice at design time, and taking a user identifier and resolving the default access key in a
  subquery puts it on the new ops with no column change.
- What grants a domain administrator the permission to edit a resource group. It is not derived
  from the relation, so it has to be stated as a role or a grant.

## References

- `src/ai/backend/manager/models/specs/KNOWLEDGE.md` — write spec selection criteria
- `src/ai/backend/manager/actions/KNOWLEDGE.md` — the v2 action shapes
- BEP-1008 · BEP-1012 (RBAC)
