---
name: write-spec-design
type: design-rationale
description: write-spec selection criteria (Entity/Global/Field/Sidecar/Relation), why a row two entities own belongs to neither position, why switching a relation off keeps both reads, why the roots share no common ABC, why a guard lives on the root and how ops diagnoses a refusal, what a sidecar row is and why it belongs to neither position, why the role-managed root is not an EntityCreator subtype, why a global entity is provisioned in the graph, how a field row's owner is read, the two graph relations (own, govern), how created_in combines them, relation and cap-based sharing, open entity-type strings
scope: src/ai/backend/manager/models/specs
keywords: [RelationCreator, RelationPurger, RelationLifecycleUpdater, EntityCreator, GlobalEntityCreator, FieldCreator, RoleManagedEntityCreator, SidecarCreator, FieldOwnerLookup, RoleTemplateSource, created_in, create_relation, entity_id, virtual-entity, preset-role, DataUpdater, GuardCheck, guard_checks, soft-delete]
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

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Why this package exists

Write specs turn "what to write" (rows, memberships, integrity checks) into declarations next to the schema,
while execution is owned by the ops layer. The RBAC side effects of a write — provisioning in the graph,
registering memberships — are decided by the spec's type, not by the execution path.

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

- The write specs split on ownership, and both positions assume it is zero or one: an entity owns itself, a
  field is owned by exactly one entity. A row linking two entities is owned by both, which neither position can
  say.
- Ownership is read off the schema, not off the call site: what deletes the row when it goes is what owns it. A
  polymorphic reference carries no foreign key, so ownership there is a fact about the code that cleans up.
- The relation roots therefore name the pair, never a row id. Nothing outside the layer that wrote the row holds
  that id, and a read answers with the entities the relation reaches.
- Switching off is state, not access. A resource group excluded from a project for a while must still be read by
  both sides, so the exclusion shows and can be undone. A lifecycle transition writes the row alone; the graph
  moves on create and purge only, and create has no upsert reviving a row switched off — reviving is restore's.
- Full rationale: `proposals/BEP-1075-entity-relation-operations.md`.

## A sidecar belongs to neither position

- An entity stands on its own and is woven to other entities through virtual entities; a field cannot stand on its own and is an extension of its owner's value, handled with the owner's permission.
- A sidecar takes the diagonal: it stands on its own, yet carries no node and is read through an entity's permission the way a field is. An audit record outlives the entity it is about, and some name no entity.
- Its create settles nothing: no node, no owner. The entity it names is a value a reader is authorized by, so the read is scope-shaped on that entity while the row belongs to no one.

## The absent common ABC and the non-subtype root enforce the path

- With a shared supertype, an entity spec passed to a path that provisions nothing would pass type checking and
  silently skip it. Duplicating method declarations across roots is the price of making that path
  inexpressible. Execution-logic reuse happens via ops helpers that take plain values.
- If `RoleManagedEntityCreator` were a subtype of `EntityCreator`, it would pass type checking on the plain
  `create_entity` path and silently skip preset roles. Its entity hooks are duplicated onto the combined root,
  so only the role-managed path accepts it.
- `RoleTemplateSource` remains the sole shared base because no write path accepts it on its own.

## The guard lives on the root so no path can skip it

- A creator, an updater and a single-row purger each have a root that declares its guard as abstract and one
  subtype that answers an empty list under `@final`. One ops path serves both, so a spec with a guard cannot be
  handed to a path that would write without it.
- Two unrelated roots instead (`DataUpdater` beside `GuardedDataUpdater`, as it once was) doubled the ops,
  service, action and group surfaces and left the refusal generic: the write answered `None`, the caller
  re-read the row to tell a missing one from a refusing one, and each caller invented its own error.
- With the error on the check, the diagnosis moves into ops: after a statement touched nothing, one SELECT of the
  named row evaluates every guard condition beside it. No row means gone; the first `false` names the error. A
  row every guard now passes changed between the two statements, and the first guard answers for it.
- Failure stays at one round trip. A spec whose `guard_checks()` is empty pays nothing: the diagnosis runs only
  when there is a guard to blame.
- `RolePurger` states its SYSTEM refusal as a guard rather than a conflict check: the condition is on the row
  being removed, not on rows it would leave behind.

## Why a global entity is provisioned too

Rows are created under a global entity as well — an image under its container registry. Without a node those rows have nothing to point their membership at, and the global entity is reachable by nobody but a super-admin. The delete side always tore the node down; the create side removed the asymmetry of tearing down what was never built.

## A field row carries an id of its own

- A row with exactly one owning entity is a field row. How it points at that owner (a cascading FK or a polymorphic `(entity_type, entity_id)` pair) is not the test, and neither is whether an API names one individually today.
- Such a table gets an `id` uuid. Where the primary key is composite it stays and `id` is added as a unique column: every existing query and index survives, and a `FieldIdentifier` becomes expressible.
- The five tables recording one slot's amount per owner (agent / session / model card / deployment preset / deployment revision) are this shape.

## Which end the operation starts from decides the check

| Starting point | Owner known | Shape | Checked against |
|---|---|---|---|
| a field row's id | no | field | the owning entity, read first |
| an entity's id | yes | scope | that entity, as the scope |

- A read that comes back with several of that entity's field rows started from the entity, so it names where to look rather than what to touch: the scope shape, with the owner as the scope.
- Creating a field row takes the owning entity's id for the same reason. The rules: `../../actions/AGENTS.md`.

## A field row's membership is only knowable through its owner

- A field row carries no membership of its own, so an operation naming one has nothing to validate and nothing to record against. `FieldOwnerLookup` fills that in: from a field row's id to its owning entity's id.
- It declares a query rather than conditions because an owner may be reachable only through a join, and selecting the pair (row id, owner id) keeps a batch from losing which row each owner belongs to.
- It is generic because `Select`'s type parameter is invariant: a concrete column type does not match a loosely declared one, so the implementation states both of its own. `DataBatchPurger` is generic over its row type for the same reason.

## Soft delete is guarded by the absence of a field

The same mechanism as the spec roots: the shape of the declaration stops the write, not a check at execution time.

- A soft delete is an UPDATE, so ops cannot tell it from an edit and has no delete operation to generalize. What records it as a delete is the action's `operation_type()`, which decides the RBAC permission and the audit row's `operation`.
- An ordinary edit that wrote the lifecycle column would be recorded as `UPDATE`. Removing the field from the general updater closes that. Delete and restore get their own updaters with a constant `build_values()`: a transition value taken as an argument can be passed wrong.
- Which column carries the state still varies (`deleted` on a role preset, `status` on a vfolder or user). BEP-1069 moves it to the soft delete mixin's `deleted_at`. A business state and a deletion hold at once, so restore keeps the business state; user and role restore currently always write `active`.

## own and govern are different relations, and creation composes them

- own: a virtual entity holds an entity. The entity is on that virtual entity's list ("listing = enrollment")
  and one hop away.
- govern: a scope rules a virtual entity. The scope's roles reach everything that virtual entity owns. The
  wider relation of the two.
- The resolver walks one hop: `entity → the virtual entity owning it → the scope governing that → role`. The
  checks live in the ops too (`PermissionReadOps`, the read side of `PermissionOpsProvider`); `PermissionDBSource`
  delegates, so the graph is written and read through the ops only.

| Check | Question | The mask the repository answers |
|---|---|---|
| own check | Does a virtual entity governed by a scope my role is in own this entity (caps included): "do I own this entity with these bits" | `owned_permissions(keys)`: per key, the OR of `permission & govern cap & share cap` over the paths |
| govern check | Does a scope my role is in govern this scope's virtual entity (its own govern included), and give these bits on this entity type within it: "do I govern this scope for this type and these bits" | `governed_permissions(keys)` |

- Entity create and search take the govern check (what is created becomes owned by the scope); single-entity,
  bulk and relation actions take the own check; global is outside the graph (superadmin). The field check and
  the list filter (BEP-1077 5.2, 5.4) are follow-ups.
- The own check costs one index lookup per hop and answers one row per entity. Its equivalence with the old
  query (one row per path and bit, OR-ed in Python) is checked on every CI run in
  `tests/unit/manager/repositories/permission_controller/test_own_check_query.py` in three shapes (an own chain,
  a share, many roles). At 2,000 sessions the median went from 71~74 ms to 56~59 ms; at 500 vfolders it stayed
  at 13 ms. Both plans are index lookups only, and the gap is the rows returned (5,260 → 2,000) with the Python
  OR loop gone.
- Every entity's own virtual entity owns it and its own scope governs it (`_provision`).
- `created_in` (session → project and user): where it is created owns and governs it. Through own the project's
  roles reach the session and list it; through govern they reach what the session owns (invitations). The
  domain governs the user's virtual entity, so it reaches the sessions the user owns.
- Projects and users are `created_in` their domain too. The own adds nothing to resolution (self own + govern
  already reach) but puts scopes and resource entities under one rule. A user's virtual entity is governed by
  its domain only; governed by a project, what the user owns would leak into the project (BEP-1077).
- The former `member_of` wrote both as well. Its name said own only, so govern was hidden.
- A share (`replace_share` / `replace_share_fields`) is a capped own lent to the receiving scope. It answers
  through that scope's own govern only: a shared vfolder taken as a scope does not read its invitations, and a
  project shared to a resource group is not read by another project governing that resource group.
- A relation (`create_relation(scope, target)`): the scope governs the target under cap READ, and the target
  holds the scope under a READ share. A project reads a resource group and its agents; the resource group reads
  the project itself only. The govern-side cap (`scope_bindings.permission_cap`) is written by relations only.
- A relation table carries foreign keys with cascade on both sides (`association_container_registries_groups`,
  `sgroups_for_groups`), and its specs are typed by the pair's id types.
- A resource group seeing sessions and deployments is not a relation: a share at scheduling answers it
  (follow-up). Another project governing the resource group is not answered by the share, so nothing leaks.
- Four roots along two axes: with or without `created_in` (Entity / Global) × with or without preset roles
  (plain / RoleManaged). Role-managed writes the same relations plus the presets.
- Every-field shares and field-path shares are different methods. replace drops everything before it, widen
  reads and only adds, narrow only removes. A mixed share is replace then widen.
- The private primitives are on `V2GraphWriteOpsBase` alone, and no provider hands it out. The public surface is
  three provider / ops pairs.

| Relation | Write | Reverse | Written by |
|---|---|---|---|
| node | `_provision(entities)` — node + self own + self govern | `_teardown(entity)` — the rest goes by FK cascade | create / purge |
| own | written only as part of `_created_in` | `_disown(owners, entity)` | a user leaving a project |
| govern | `_govern(scopes, entity, cap)` | `_ungovern(scopes, entity)` | relation (cap READ) |
| own + govern | `_created_in(scopes, entity)` — one node lookup | `_removed_from(scopes, entity)` | create (preset roles included), transfer |
| share (capped own) | `_reset_share(scope, entity)` / `_widen_share(scope, entity, {bit: paths})` / `_narrow_share` | `_unshare(scope, entities)` | relation, share write |

| Pair | provider / ops | Methods |
|---|---|---|
| entity write | `V2DBOpsProvider` / `V2WriteOps` | create / upsert / purge / update / field / batch. `_created_in` at create, `_teardown` at purge |
| relation write | `RelationOpsProvider` / `V2RelationWriteOps` | `create_relation(creator, scope, target)` / `delete_relation` / `restore_relation` / `purge_relation` — `_govern(cap READ)` + `_widen_share(READ)` |
| share write | `ShareOpsProvider` / `V2ShareWriteOps` | `replace_share` / `replace_share_fields` / `widen_*` / `narrow_*` / `unshare` / `transfer` / `accept_invitation` |

- The latter two ops extend `V2WriteOps`, so a row write and a relation write share one transaction. "grant" is
  not used: it collides with granting a role its permissions.
- Limit: govern is one hop, so domain → user → session → invitation leaves the domain short of the invitation.
  Close it by copying the upper scope's govern along when writing a govern.

## Entity type is an open string

- This is so a new type can register members before the permission layer knows about it — only
  permission-carrying paths convert lazily and reject there.
- The registration-time integrity guarantee is: "a write against a target with no node fails".
- The axis that separated scope type from entity type is gone from the spec hooks. Every entity has a node, so
  there was nothing left to separate.
