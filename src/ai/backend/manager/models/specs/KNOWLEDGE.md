---
name: write-spec-design
type: design-rationale
description: write-spec selection criteria (Entity/Global/Field/Sidecar/Relation), why a row two entities own belongs to neither position, why switching a relation off keeps both reads, why the roots share no common ABC, what a sidecar row is and why it belongs to neither position, why the role-managed root is not an EntityCreator subtype, why a global entity is provisioned in the graph, how a field row's owner is read, the two graph relations (own, govern), how created_in combines them, relation and cap-based sharing, open entity-type strings
scope: src/ai/backend/manager/models/specs
keywords: [RelationCreator, RelationPurger, RelationLifecycleUpdater, EntityCreator, GlobalEntityCreator, FieldCreator, RoleManagedEntityCreator, SidecarCreator, FieldOwnerLookup, RoleTemplateSource, created_in, create_relation, entity_id, virtual-entity, preset-role, DataUpdater, soft-delete]
sources:
  - src/ai/backend/manager/models/specs/creator.py
  - src/ai/backend/manager/models/specs/lookup.py
  - src/ai/backend/manager/models/specs/role_template.py
  - src/ai/backend/manager/repositories/ops/v2
generated:
  by: claude-code/opus-5
  at: 2026-08-18
status: stable
---

# Write specs — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

Write specs turn "what to write" (rows, memberships, integrity checks) into
declarations next to the schema, while execution is owned by the ops layer. It
exists so that the RBAC side effects of a write — provisioning in the graph,
registering memberships — are decided by the **spec's type**, not by the
execution path.

## Spec selection: the only remaining question is "is it an entity"

**Every entity has a node in the graph** — it can own memberships and can be shared.

| Spec | Criterion | Write behavior |
|---|---|---|
| Entity | First-class entity (vfolder/session/...) | create provisions the node (it owns and governs itself) and is owned and governed by each `created_in()` scope; purge tears down symmetrically; upsert stays idempotent |
| Global, role-managed | Entities that grant preset roles, created in no scope (domain, resource group) | Global behavior + preset role creation — `RoleManagedGlobalEntityCreator` |
| Entity, role-managed | Entities that grant preset roles, created in a scope (project, user) | Entity behavior + preset role creation — `RoleManagedEntityCreator`, `created_in()` the domain |
| Global | An entity that goes under no other entity | Entity behavior minus `created_in` — the node is provisioned the same way |
| Field | A row another entity owns (even with its own get/delete API) | create requires `owner_id`; purge is a plain delete |
| Sidecar | A row outside the graph — an audit record, an event log | create inserts and nothing else; the entity it names is read by, not belonged to |

## A relation belongs to both, so it belongs to neither position

- The write specs split on ownership, and both positions assume it is zero or one: an
  entity owns itself, a field is owned by exactly one entity. A row linking two entities
  is owned by both, which neither position can say.
- Ownership is read off the schema, not off the call site: what deletes the row when it
  goes is what owns it. A polymorphic reference carries no foreign key, so ownership
  there is a fact about the code that cleans up rather than about a constraint.
- The relation roots therefore name the pair, never a row id. Nothing outside the layer
  that wrote the row holds that id, and a read answers with the entities the relation
  reaches rather than the row between them.
- Switching off is state, not access. A resource group excluded from a project for a
  while must still be read by both sides, so the exclusion shows and can be undone (the
  choice Kubernetes cordon and GitLab archive make). So a lifecycle transition writes
  the row alone, and the graph moves on create and purge only. That is also why create
  has no upsert reviving a row switched off — reviving is restore's alone.
- Full rationale: `proposals/BEP-1075-entity-relation-operations.md`.

## A sidecar belongs to neither position

- An entity can stand on its own and is woven to other entities through virtual entities;
  a field cannot stand on its own and is an extension of its owner's value, handled with
  the owner's permission.
- A sidecar takes the diagonal: it stands on its own, yet carries no node and is read
  through an entity's permission the way a field is. An audit record outlives the entity
  it is about, and some name no entity at all.
- So its create settles nothing — no node, no owner. The entity it names is a value a
  reader is authorized by, which is why the read is scope-shaped on that entity while
  the row belongs to no one.

## The absence of a common ABC is itself the enforcement mechanism

- With a shared supertype, an entity spec passed to an execution path that provisions
  nothing would pass type checking and silently skip it — exactly the bug this lineage
  is meant to prevent.
- Duplicating method declarations across roots is the price of making that path
  inexpressible.
- Execution-logic reuse happens via ops helpers that take plain values.

## The role-managed root not being a subtype is the same mechanism

- If `RoleManagedEntityCreator` were a subtype of `EntityCreator`, it would pass type
  checking on the plain `create_entity` path and silently skip preset roles.
- The entity hooks are duplicated onto the combined root so that the only path that
  accepts it is the role-managed path.
- `RoleTemplateSource` remains the sole shared base because no write path accepts it
  on its own.

## Why a global entity is provisioned too

Rows are created under a global entity as well — an image under its container
registry. Without a node those rows have nothing to point their membership at, and
the global entity itself is reachable by nobody but a super-admin.

The delete side always tore the node down (`purge_entity` calls `_teardown_entity`).
The create side removed the asymmetry of tearing down what was never built.

## A field row carries an id of its own

- A row with exactly one owning entity is a field row. How it points at that owner —
  a cascading FK, or a polymorphic `(entity_type, entity_id)` pair — is not the test,
  and neither is whether an API names one individually today.
- So such a table gets an `id` uuid. Where the primary key is composite it stays as it
  is and `id` is added as a unique column: every existing query and index survives, and
  a `FieldIdentifier` becomes expressible.
- The five tables recording one slot's amount per owner (agent / session / model card /
  deployment preset / deployment revision) are this shape.

## Which end the operation starts from decides the check

| Starting point | Owner known | Shape | Checked against |
|---|---|---|---|
| a field row's id | no | field | the owning entity, read first |
| an entity's id | yes | scope | that entity, as the scope |

- A read that comes back with several of that entity's field rows started from the
  entity, so it names where to look rather than what to touch — the scope shape, with
  the owner as the scope.
- Creating a field row takes the owning entity's id for the same reason.
- The rules: `../../actions/AGENTS.md`.

## A field row's membership is only knowable through its owner

- A field row carries no membership of its own, so an operation naming one has nothing
  to validate and nothing to record against. `FieldOwnerLookup` fills that in: from a
  field row's id to its owning entity's id.
- It declares a query rather than conditions for two reasons. An owner may be reachable
  only through a join, and selecting the pair (row id, owner id) is what keeps a batch
  from losing which row each owner belongs to.
- It is generic because `Select`'s type parameter is invariant: a concrete column type
  does not match a loosely declared one, so the implementation states both of its own.
  `DataBatchPurger` is generic over its row type for the same reason.

## Soft delete is guarded by the absence of a field

The same mechanism as the spec roots: what stops a write is the shape of the
declaration, not a check at execution time.

A soft delete is an UPDATE at the DB, so ops cannot tell it apart from an edit — there
is no delete operation to generalize and no place there to enforce anything. What
separates them is the action's `operation_type()`, which decides the RBAC permission
and the audit row's `operation`.

That leaves one hole: an ordinary edit that writes the lifecycle column would be
recorded as `UPDATE`, and the deletion would never appear in the trail. Removing the
field from the general updater closes it — the edit path has nothing to make the
transition with. Splitting delete and restore into their own updaters with constant
`build_values()` closes the rest: a transition value taken as an argument is a value
that can be passed wrong.

Which column carries the state is domain knowledge and varies (`deleted` on a role
preset, `status` on a vfolder or user), which is why this is a rule about the general
updater's fields rather than about a column name.

## own and govern are different relations, and creation composes them

- own: a virtual entity holds an entity. The entity is on that virtual entity's list
  ("listing = enrollment") and one hop away.
- govern: a scope rules a virtual entity. The scope's roles reach everything that
  virtual entity owns. The wider relation of the two.
- The resolver walks one hop: `entity → the virtual entity owning it → the scope
  governing that → role`. The checks live in the ops too (`PermissionReadOps`, the read
  side of `PermissionOpsProvider`); `PermissionDBSource` delegates — the graph is
  written and read through the ops only.
- There are two checks, named after the relations. The repository answers a mask per
  key; the check (`mask.covers(bits)`) is the validator's.

| Check | Question | The mask the repository answers |
|---|---|---|
| own check | Does a virtual entity governed by a scope my role is in own this entity (caps included) — "do I own this entity with these bits" | `owned_permissions(keys)`: per key, the OR of `permission & govern cap & share cap` over the paths |
| govern check | Does a scope my role is in govern this scope's virtual entity (its own govern included), and give these bits on this entity type within it — "do I govern this scope for this type and these bits" | `governed_permissions(keys)` |

  Entity create and search take the govern check (what is created becomes owned by the
  scope); single-entity, bulk and relation actions take the own check; global is outside
  the graph (superadmin). The field check and the list filter (BEP-1077 5.2, 5.4) are
  follow-ups.
- The own check costs one index lookup per hop and answers one row per entity.

| Measurement | How |
|---|---|
| Equivalence | `tests/unit/manager/repositories/permission_controller/test_own_check_query.py` — the old query (one row per path and bit, OR-ed in Python) is kept as a function and checked on every CI run to answer the same as the new one in three shapes (an own chain, a share, many roles) |
| Benchmark | Same file. `BAI_BENCHMARK=1 … -s` runs 1,000 entities; `BAI_BENCHMARK_SCALE=1 … -s` runs a COPY-seeded scale (10 domains, 1,000 projects, 10,000 users, 1M sessions, 1M vfolders, 300k shares, 10,000 roles, 100k permissions, 100k user roles; about 13M relation rows, about 4 minutes to seed; pants needs `--test-timeout-default=3600 --test-attempts-default=1`). After a warm-up the two queries alternate, printing min / median / p95 and `EXPLAIN (ANALYZE, BUFFERS)` |

| Scale run (local container, the range of the two normal runs out of three) | Old query median | New median | Execution inside the DB |
|---|---|---|---|
| 2,000 sessions (1,000 owned + 1,000 someone else's, all reached) | 71 ~ 74 ms | 56 ~ 59 ms | 41 ms vs 42 ms |
| 500 vfolders (261 reached) | 13 ms | 13 ms | 6.7 ms vs 7.2 ms |

- The plan is the same for both: entity unique index → own index → govern index-only →
  governor PK → hash join with the user's permissions (tens of rows). Every hop is an
  index lookup, no seq scan; 31 of the 41 ms is the nested loop over 2,000 entities ×
  about 7 paths.
- The wall-clock gap is all rows returned (5,260 → 2,000) and the Python OR loop gone.
  `bit_or … GROUP BY` adds about 1 ms of Sort + GroupAggregate for it. Leading with the
  user's permissions in a CTE gained nothing — the planner already does — and was left
  out.
- One run put both queries at a median of 29 seconds on the same data (a container DB
  right after COPY, most likely). It did not reproduce; a production-scale call needs
  the plan re-read under production statistics.
- Every entity's own virtual entity owns it and its own scope governs it
  (`_provision`).
- `created_in` (session → project and user): where it is created owns and governs it.
  Through own the project's roles reach the session and list it; through govern they
  reach what the session owns (invitations). The domain governs the user's virtual
  entity, so it reaches the sessions the user owns.
- Projects and users are `created_in` their domain too: the domain owns and governs
  them. The own adds nothing to resolution (self own + govern already reach) but is
  harmless and puts scopes and resource entities under one rule. A user's virtual entity
  is governed by its domain only — governed by a project, what the user owns would leak
  into the project (BEP-1077).
- The former `member_of` wrote both as well. Its name said own only, so govern was
  hidden.
- A share (`replace_share` / `replace_share_fields`) is a capped own, lent to the
  receiving scope. An own goes on the virtual entity, so it belongs to every scope
  governing it; a share is given to one scope of that virtual entity, so it answers
  through that scope's own govern only. The resolver therefore passes a share (1) for the
  shared entity's type only and (2) through the own govern only. A shared vfolder taken
  as a scope does not read its invitations, and a project shared to a resource group is
  not read by another project governing that resource group.
- A relation (`create_relation(scope, target)`): the scope governs the target under cap
  READ, and the target holds the scope under a READ share. A project reads a resource
  group and the agents it owns; the resource group reads the project itself only — the
  users, sessions and vfolders the project owns stay hidden. The govern-side cap
  (`scope_bindings.permission_cap`) is written by relations only; the self govern and
  the `created_in` govern carry none.
- A relation table carries foreign keys with cascade on both sides
  (`association_container_registries_groups`, `sgroups_for_groups`), so an entity going
  away takes its rows with it and no ops method names a whole side. The relation specs
  are typed by the pair's id types, so a spec reads each id as what it is.
- A resource group seeing sessions and deployments is not a relation: it is answered by
  sharing the session to the resource group under READ at scheduling (follow-up).
  Another project governing the resource group is not answered by the share, so nothing
  leaks.
- Four roots along two axes: with or without `created_in` (Entity / Global) × with or
  without preset roles (plain / RoleManaged). Role-managed writes the same relations as
  plain, plus the presets.
- Every-field shares and field-path shares mean different things and are different
  methods. Storage is one cap row tree (rows per bit, path rows) but the declarations
  never mix them. replace drops everything before it (delete and insert, no read); widen
  reads what is there and only adds; narrow only removes. A mixed share is written as
  replace then widen.
- Where the relation ops sit. The private primitives are on `V2GraphWriteOpsBase`
  alone, and no provider hands it out. The public surface is three provider / ops
  pairs.

| Relation | Write | Reverse | Written by |
|---|---|---|---|
| node | `_provision(entities)` — node + self own + self govern | `_teardown(entity)` — the rest goes by FK cascade | create / purge |
| own | `_own(owners, entity)` — a share in its place becomes own | `_disown(owners, entity)` | preset role |
| govern | `_govern(scopes, entity, cap)` | `_ungovern(scopes, entity)` | relation (cap READ) |
| own + govern | `_created_in(scopes, entity)` — one node lookup | `_removed_from(scopes, entity)` | create, transfer |
| share (capped own) | `_reset_share(scope, entity)` / `_widen_share(scope, entity, {bit: paths})` / `_narrow_share` | `_unshare(scope, entities)` | relation, share write |

| Pair | provider / ops | Methods |
|---|---|---|
| entity write | `V2DBOpsProvider` / `V2WriteOps` | create / upsert / purge / update / field / batch. `_created_in` at create, `_teardown` at purge |
| relation write | `RelationOpsProvider` / `V2RelationWriteOps` | `create_relation(creator, scope, target)` / `delete_relation` / `restore_relation` / `purge_relation` — `_govern(cap READ)` + `_widen_share(READ)` |
| share write | `ShareOpsProvider` / `V2ShareWriteOps` | `replace_share` / `replace_share_fields` / `widen_*` / `narrow_*` / `unshare` / `transfer` / `accept_invitation` |

  The latter two ops extend `V2WriteOps`, so a row write and a relation write share one
  transaction (a vfolder's permission row + share, an invitation row's update + share).
  "grant" is not used: it collides with granting a role its permissions.
- Limit: govern is one hop, so three levels like domain → user → session → invitation
  leave the domain short of the invitation. If needed, close it by copying the upper
  scope's govern along when writing a govern.

## Entity type is an open string

- This is so a new type can register members before the permission layer knows about
  it — only permission-carrying paths convert lazily and reject there.
- The registration-time integrity guarantee is: "a write against a target with no node
  fails".
- The axis that separated scope type from entity type is gone from the spec hooks.
  Every entity has a node, so there was nothing left to separate.
