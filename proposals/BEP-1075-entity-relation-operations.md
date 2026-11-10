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

- BA-7467 — (how an action designates an entity)
- BA-7468
- BA-7469
- BA-7470
- BA-8573 — (how the API identifies Nodes and relations)
- BA-8619 — (relation identification and delete response rules)
- BA-8459 — (resource group ↔ keypair moves to user)
- BEP-1076 — (Project Membership) — the contained case

## Motivation

Nothing decides what answers for the permission of an operation that links two entities.

Handling a relation through the virtual scope makes the graph answer. Not handling it there
means the operation has to answer for itself. Today each domain answers differently, so the
same relation lands in the permission graph or not depending on which API created it.

| Operation | Mapping row | Permission graph |
| --- | --- | --- |
| Bind/unbind a resource group to a domain or project | writes | writes |
| Bind/unbind a resource group to a keypair | writes | does not |
| Edit a domain's or project's allowed resource groups | writes | writes |
| Name resource groups while creating or editing a domain | writes | does not |

How the API names a relation differs per relation too. `user_roles` and `idle_checker_bindings`
expose their row id; the other relations are named by their ends. An API taking a row id can change a
relation only for a client that stored that id, and a relation found by row id has to be read again by
its ends before its permission can be asked.

**The virtual scope expresses ownership and nothing else.** A relation creates what business
logic reads, and the permission of that operation is answered by the two scopes it names. A relation
itself is identified by its ends alone.

## Current Design

### Relation tables

| Table | Links | Own data | Polymorphic side | Row id |
| --- | --- | --- | --- | --- |
| `sgroups_for_domains` | resource group ↔ domain | none | no | present, unused |
| `sgroups_for_groups` | resource group ↔ project | none | no | present, one test |
| `sgroups_for_keypairs` | resource group ↔ keypair — the user is what it means to link | none | no | present, unused |
| `association_groups_users` | user ↔ project | none | no | present, unused |
| `user_roles` | user ↔ role | `granted_by` · `granted_at` | no | exposed in the API |
| `idle_checker_bindings` | idle checker ↔ scope | `enabled` | yes | exposed in the API |
| `association_container_registries_groups` | container registry ↔ project | none | no | present, one existence check |

No relation links three or more. No table references a relation row id by foreign key. The first
four tables had the pair of ends as their primary key originally (migration `caf54fcc17ab`).

`session_dependencies` is a field of the depending session: the interaction runs one way, so it
is not a relation. `replica_groups` and `endpoint_tokens` are handled as deployment fields.

### Where a row id reaches the API

| Relation | Uses of the row id |
| --- | --- |
| user ↔ role | `RoleAssignment.id` Node id, data loader, cursor, lookup, SDK response |
| idle checker ↔ scope | REST path (`/idle-checker-assignments/{id}`), GraphQL input and response, CLI, cursor, lookup key |

The WebUI uses the role assignment id only as a list row key and revokes by (userIds, roleId). The
idle checker assignment has no WebUI yet.

### Resource group links replace a whole name list

`adminUpdateAllowedResourceGroupsForDomainV2` · `…ForProjectV2` and their two reverse directions take a
list of names and replace the relation wholesale. No operation links or unlinks a single pair.

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

|  | Position |
| --- | --- |
| The value is an amount of access and the subject is a user | virtual scope edge — no table |
| Any other link between two entities | **relation — its own table, its own operations** |
| The other side is a value that does not hold the relation | field |

### A relation is identified by the UUIDs of its ends

| Layer | Identification |
| --- | --- |
| Table | No row id column. The pair of ends is the primary key |
| Repository · permission check | Looked up by the end UUIDs only |
| Adapter · DTO | End UUIDs only |
| GraphQL relation id | A global ID built from the type name and the end UUIDs. Built and decoded in the GraphQL layer only. The type is `ID!` |
| `node(id:)` | A relation type implements Node. The global ID is decoded into its ends and read again |
| Individual query · mutation · REST | Take both end UUIDs as arguments or in the body. No global ID and no id in the path |

The global ID serves `node(id:)` and the Relay store key only. Arguments that change or select a
relation are the end UUIDs.

Reading a relation through `node(id:)` requires read on both end scopes. The global ID carries both
ends, so both are asked.

Once the ends are fixed the relation is fixed. An id outside the pair becomes a second name for the same
relation, and a relation found by that id has to be read again by its ends before its permission can be asked.

A relation with a polymorphic side includes that side's type in its key. The idle checker assignment's
key is the triple its unique constraint already names: (scope type, scope id, idle checker).

### The action decides the permission, not ops

The relation ops take a pair and write a row; they know nothing about permission. Who may run it
is the action's, and the action's shape splits on **whether one side is contained in the other**.

|  | Example | Shape |
| --- | --- | --- |
| Contained | project ⊃ user | `scope_targets` = the container alone, `entity_type` = what it contains |
| Not contained | resource group ↔ domain | `scope_targets` = both, no `entity_type` |

A resource group is a cluster resource several domains share, so neither side is inside the other.
There the permission is asked of each named scope itself.

```
link · unlink  →  permission on the left scope  AND  permission on the right scope
```

With no `entity_type` there is no "permission on this type within this scope" to ask, so the only
thing left to ask is the permission on the scope itself.

The contained case is the scope shape as it already exists. Project membership is that case, and
BEP-1076 covers it.

### ops

```
create_relation (scope, target, creator)   the row, the scope governs the target under READ, the target reads the scope
delete_relation (scope, target, updater)   writes the current time to `deleted_at`; both reads stay
restore_relation(scope, target, updater)   sets `deleted_at` back to NULL
purge_relation  (scope, target, purger)    removes the row and both reads
```

The middle two are wired only for relations carrying the soft delete mixin (`deleted_at`, BEP-1069).
Whoever holds the permission on both scopes may soft delete and restore a relation; soft delete is the
same permission as unlinking. A relation cleans up no external resource, so it has no `purge_status`
and its purge finishes within the request.

### What the spec decides

- Create inserts a new row only. A pair already linked, soft-deleted or not, is a primary key
  violation the spec's `integrity_error_checks` maps to a domain error. Bringing it back is restore's,
  so create has no upsert.
- Soft delete / restore writes `deleted_at` alone. What each side reads of the other (the scope's
  govern READ, the target's share READ) stays — a soft-deleted relation is still listed on both sides,
  which is what lets it be restored. Only purge removes access. Leaving a soft-deleted relation unused
  is the reader's job (the scheduler picking resource groups, the idle checker applying).
- A relation without the soft delete mixin has create and purge only.
- `idle_checker_bindings.enabled` is a business value switched on and off. It is not a soft delete.

### Resource group links move to link and unlink

Resource group ↔ domain and ↔ project are handled by link and unlink of a single pair instead of
replacing the whole name list (`adminUpdateAllowed*`). Both take the end UUIDs. Resource group ↔ keypair
is handled by BA-8459, which moves it to the user.

### How a relation is read

A relation is read as a relation type. A relation type is a Node carrying both end entities, the
relation values and the global ID built from its ends. There is no row id.

The permission of a list read needs no new machinery. It sits on the two axes a scope operation
already has.

| Axis | Value |
| --- | --- |
| `scope_targets()` | the domain — the permission is asked here |
| `operation_scopes()` | the condition derived from the relation table |

No edge per resource group is needed. Deriving permission from a relation turns into reference
counting once the same entity is reached through several relations, and a permission written as a
side effect of a business operation is invisible to the permission model.

### Responses of operations that change a relation

| Operation | DTO · REST | GraphQL payload |
| --- | --- | --- |
| link (create) · update · soft delete · restore | relation DTO | relation Node |
| unlink (purge) | end UUIDs | `purgedId: ID!` (the relation's global ID) + end UUIDs |

The rule is the same as for a Node. An operation the relation survives returns the relation; one it
does not returns the global ID Relay's `@deleteEdge` · `@deleteRecord` take. The full rule is in
`api/gql/AGENTS.md`.

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

| Target | Order |
| --- | --- |
| The permission graph edges the resource group relations wrote | Leaving them means only the relations made through that path stay inherited by the domain's administrators |
| The row id of the three `sgroups_for_*`, `association_groups_users` and `association_container_registries_groups` | Dropped right away. The primary key returns to the pair of ends |
| The row id of `user_roles` and `idle_checker_bindings` | Dropped after the API moves to the ends |
| The four `adminUpdateAllowed*` mutations | Deprecated once link and unlink are added |

### API compatibility

- `RoleAssignment.id` and `IdleCheckerAssignment.id` stay `ID!`; only their value becomes the global ID of the ends.
- Inputs and REST paths taking a row id gain a form taking the end UUIDs and are deprecated. Once the row id
  column is gone, nothing can be found by row id.
- The relation types (`RoleAssignmentV2`, `IdleCheckerAssignment`, `SessionIdleCheck`) implement Node. The
  change adds fields.

### A relation is not carried as an updater field

Two updaters carry a relation today and say so themselves.

| Updater | Field | What it writes |
| --- | --- | --- |
| `UserUpdater` | `group_ids` | the user's project memberships |
| `ContainerRegistryUpdater` | `allowed_groups` | the registry's project associations |

Neither field reaches `build_values()`; the repository writes those rows beside the update. This is
the rule soft delete already follows — a value whose change drags other writes along does not
belong on the general updater, because an edit path that can make the transition is an edit path
that can make it wrong. Both fields move to the relation operations.

### When a referenced entity is removed

`purge_relation` takes both values to remove a row. There is no operation that knows one side and
sweeps that entity's relations away.

FK CASCADE is a guarantee about logic, not a statement of ownership. It may be kept, but it cannot
be placed on a polymorphic reference.

Removing a long-lived entity such as a domain will be handled by the lifecycle manager, and the
relation rows it leaves are cleaned up there or by a retention sweep. A relation table has its own
`RetentionCategory` entry.

## Implementation Plan

- Make the relation types implement Node. The GraphQL layer builds and decodes the global ID from the end
  UUIDs, and `node(id:)` asks read on both end scopes.
- user ↔ role: switch the global ID to the ends, and make the changing mutations and REST take (user, role)
  in the body. Move the data loader, cursor, lookup and SDK response onto the ends.
- idle checker ↔ scope: take (scope type, scope id, idle checker) the same way and drop the id from the path.
  Move the GraphQL input and response, CLI, cursor and lookup key.
- resource group ↔ domain · project: add link and unlink, and deprecate `adminUpdateAllowed*`.
- Drop the row id column of the seven relation tables and make the pair of ends the primary key.
  `user_roles` and `idle_checker_bindings` follow the two steps above.
- Build the relation ops (create · delete · restore · purge_relation) and derive the nine `OperationScope`
  from the relation declaration.

## Decision Log

| ID | Date | Decision | Rationale | Alternatives Considered |
| --- | --- | --- | --- | --- |
| D1 | 2026-10-20 | A relation is identified by the UUIDs of its ends alone. Its id in the API is a global ID built from the ends, and repositories and permission checks look it up by the ends only. | An id outside the pair is a second name for the same relation, and a relation found by that id has to be read again by its ends before its permission can be asked. | Keep the row id as the Node id — a client has to store the row id to change the relation. |
| D2 | 2026-10-20 | Drop every relation table's row id column and make the pair of ends the primary key. | No table references the row id by foreign key, and five tables do not use it. The first four had the pair as their primary key originally. | Keep the row id and hide it in the API — an unused key stays and can reach the API again. |
| D3 | 2026-10-20 | A relation's unlink (purge) answers `purgedId` (the relation's global ID) and the end UUIDs in GraphQL, and the end UUIDs in the DTO and REST. An operation the relation survives returns the relation. | Relay's `@deleteEdge` · `@deleteRecord` take a global ID. The global ID is built in the GraphQL layer only. | A global ID in the payload's `id` — it becomes the same key as the removed relation in the Relay store and collides. |
| D4 | 2026-10-20 | Resource group ↔ domain and ↔ project are handled by link and unlink. Replacing the whole name list is deprecated. | A wholesale replacement cannot ask the permission of one pair on its own and does not name a relation by its end UUIDs. |  |
| D5 | 2026-10-20 | Relation types implement Node. The global ID serves `node(id:)` only, and individual queries and mutations take the end UUIDs. `node(id:)` asks read on both end scopes. | A global ID built from the ends lets the relation be read again from its id alone, keeping the Node contract. The global ID carries both ends, so both permissions are asked. | Keep relation types off Node with no `id` — the Relay store cannot normalize a relation, and an unlink response cannot remove its edge. |

## Open Questions

| ID | Question |
| --- | --- |
| Q1 | How to find relation rows whose reference is gone. The reference is polymorphic   (`entity_type`, `entity_id`), so an anti-join needs to know which table that type lives in.   `virtual_scopes` already indexes live entities by `(scope_type, scope_id)` and could be matched   against, but a row created before the virtual scope rollout may have no scope, which would read a   live entity's relation as a dangling one. |
| Q2 | Whether to collapse the three `sgroups_for_*` into one polymorphic table — doing so makes   `query_allowed_sgroups` a single query and turns a new kind of scope into a value. |
| Q3 | Whether to key the resource group ↔ keypair relation on the user — handed to BA-8459. |
| Q4 | What grants a domain administrator the permission to edit a resource group. It is not derived   from the relation, so it has to be stated as a role or a grant. |

## References

- `src/ai/backend/manager/models/specs/KNOWLEDGE.md` — write spec selection criteria
- `src/ai/backend/manager/actions/KNOWLEDGE.md` — the v2 action shapes
- `src/ai/backend/manager/api/gql/AGENTS.md` — mutation payload and relation type rules
- BEP-1069 (Entity Lifecycle Deletion) — the soft delete mixin and `purge_status`
- BEP-1008 · BEP-1012 (RBAC)
- BEP-1076 (Project Membership)

<!-- generated by hejo bep render from hejo report bep/entity-relation-operations (sha256 5727eea6e1c5011e); edit the source, or hejo bep import after editing here -->
