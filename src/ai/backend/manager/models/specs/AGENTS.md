# Write specs (v2 lineage) — Guardrails

> For the selection table and design rationale, see `KNOWLEDGE.md` in the same directory.

Declarative write specs, colocated with the schema: a spec says *what* to write
(row, membership, checks); executing it is the ops layer's job
(`repositories/ops/v2/`). Specs must NOT touch sessions or issue SQL.

## Every v2-consumed spec lives here

Whatever spec type the v2 actions and ops consume is declared in this package — the
write specs below, plus the read/update declarations (`querier.py`, `lookup.py`,
`searcher.py`, `updater.py`, `pagination.py`, and the batch purge spec in
`purger.py`). `repositories/base/` keeps legacy-compatible views for the transition
only; do not declare a new spec there.

## A relation is neither an entity nor a field

- A row linking two entities belongs to neither: both own it. It is not a field row,
  which has exactly one owner, and it is not an entity, which has a node in the graph.
- Its specs are `RelationCreator` / `RelationLifecycleUpdater` / `RelationPurger`
  (`relation.py`), and they name the pair rather than a row id — a relation row's id
  never leaves the layer that wrote it.
- Create inserts a new row only. A pair already linked, switched off or not, is a
  unique violation the spec's `integrity_error_checks` maps to a domain error;
  switching it back on is the restore updater's.
- Switching off / restoring (`RelationLifecycleUpdater`) writes the row's lifecycle
  column alone. What each side reads of the other stays, so a relation switched off is
  still listed on both sides and can be switched back on. Only purge removes access.
  Only relations carrying a lifecycle column declare this updater, one class per
  direction, each answering a constant.
- Do NOT carry a relation as a field on a `DataUpdater`. A value whose change drags
  other writes along does not belong on the general edit path — the same rule soft
  delete follows.
- Rationale: `proposals/BEP-1075-entity-relation-operations.md`.

## What a spec splits on depends on the operation

A row in the graph is an entity or a field, and which one it is comes from the table
in `KNOWLEDGE.md`. A row outside it is a sidecar — it stands on its own like an entity
and is read through an entity's permission like a field, while belonging to neither.

| Operation | Roots | Why |
|---|---|---|
| creator | `GlobalEntityCreator` / `EntityCreator` / `RoleManagedGlobalEntityCreator` / `RoleManagedEntityCreator` / `FieldCreator` / `SidecarCreator` | only a create settles what a row belongs to |
| purger | `EntityPurger` / `EntityBatchPurger` / `FieldPurger` / `GuardedFieldPurger` / `FieldBatchPurger` | removing an entity removes what it left in the graph; a field row splits further on how it is picked: by id, or by id behind a precondition; the batch roots pick by subquery instead of by id |
| updater | `DataUpdater` / `GuardedDataUpdater` | an update never changes what a row belongs to, so the roots split on how the row is picked: by id, or by id behind a precondition |

The roots are deliberately unrelated. Do NOT extract a common base across them
or type any function against "any creator/purger" — the absence of a common supertype
is the enforcement. Reuse execution logic through ops-layer helpers that take plain
values (`row_class`, `pk_value`, ...).

## An entity answers its own id

- A creator and an upserter answer one hook — `entity_id(row)`. It returns an
  `EntityIdentifier`, which answers its own type, so nothing declares the type
  separately.
- It takes the row because the id does not exist before the insert; the database
  usually fills it.
- Some tables key on something else (a resource policy's primary key is `name` and its
  id is a separate `uuid` column). Which column it is, only the domain knows.

## A global entity is an entity too

`GlobalEntityCreator` merely does not go under another entity; it provisions its own
virtual entity node exactly as `EntityCreator` does. Rows are created under a global
entity too — an image under its container registry — so it has to be namable in the
graph. What it does not have is `created_in`, and the missing hook is what says it
is created in no scope.

## Declaring a relation in the graph

- The graph has two relations. **own**: a virtual entity holds an entity, so the entity
  is on that virtual entity's list and one hop away. **govern**: a scope rules a virtual
  entity, so the scope's roles reach everything that virtual entity owns. govern is the
  wider of the two.

| Hook | own | govern | Meaning |
|---|---|---|---|
| `EntityCreator.created_in(row)` / `EntityUpserter.created_in(row)` / `RoleManagedEntityCreator.created_in(row)` | yes | yes | A session is created in its project and user, a project and a user in their domain. Where it is created owns and governs it. A missing target fails the write. `GlobalEntityCreator` / `RoleManagedGlobalEntityCreator` have no such hook |
| (no hook) preset role | yes | no | A role is owned by its scope and governed by nothing |
| share write: `replace_share` / `replace_share_fields` … | yes, capped | no | A share is own under a cap, lent to the receiving scope |
| share write: `transfer(from_scopes, to_scopes, entity)` | yes | yes | Ownership moves: as if removed from the old scopes and created in the new. A share in the new scope's place becomes own |
| relation write: `create_relation(creator, scope, target)` / `purge_relation` | the target holds the scope under cap READ | the scope governs the target under cap READ | A project reads a resource group and what it owns (agents); the resource group reads the project itself only |

- A cap sits in one of two places, and only one on any path.

| entity → virtual entity (own side) | virtual entity → scope (govern side) | Allowed |
|---|---|---|
| own, no cap | its own govern or another's, no cap | yes (creation) |
| own, no cap | another's govern, capped | yes (the scope side of a relation) |
| share, capped | its own govern | yes (a share, the target side of a relation) |
| share, capped | another's govern | **no** |

- A share is lent to the receiving scope. It answers through that scope's own govern
  only, not to other scopes governing that virtual entity, and only for the shared
  entity itself: a shared vfolder taken as a scope does not read the invitations under
  it, and a project shared to a resource group is not read by another project governing
  that resource group.
- A share is either every field or field paths, and each has replace / widen / narrow.

| | Every-field cap | Field paths (READ/UPDATE, descendants included) |
|---|---|---|
| replace (**everything** before it goes) | `replace_share(scope, entity, cap)` — 0 is a cap too | `replace_share_fields(scope, entity, {READ: paths, UPDATE: paths})` |
| widen | `widen_share` | `widen_share_fields` |
| narrow | `narrow_share` — removes the bit's rows | `narrow_share_fields` — removes the path and its descendants, an emptied row too |
| remove | `unshare(scope, entities)` — own stays | |

- A share mixing every-field bits and paths is not one replace: `replace_share(cap)`
  then `widen_share_fields`.
- Accepting an invitation is `accept_invitation(updater)`: the invitation row's update
  and `widen_share` in one transaction. An invitation is a share on offer, so it lives
  with the share writes.
- The three pairs come in through a provider only, per `repositories/AGENTS.md`. Never
  use a creator to share what already exists.
- Entity types are open strings: types outside the RBAC element enum are accepted, and
  permission-carrying paths convert lazily.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).

## Role-managed entities

- Entities that allow role presets implement `RoleManagedGlobalEntityCreator` (domain,
  resource group: created in no scope) or `RoleManagedEntityCreator` (project, user:
  `created_in` a domain) and are executed through the matching ops methods, as the
  plain `GlobalEntityCreator` / `EntityCreator` pair is. The type decides the path;
  there is NO runtime capability check (`isinstance`).
- Neither role-managed root is a subtype of its plain counterpart. `RoleTemplateSource`
  is the only shared base; no write path accepts that type bare.
- Entity specs declare NO roles — the spec contributes only `template_value(row)` for
  the presets' name templates. Restricting which types may carry presets is the
  preset-creation service's validation.
- The plain entity paths never touch roles, even when matching presets exist.
- Enrollment writes graph relations only. Granting a joining user the target's auto_assign
  roles is an explicit ops primitive — never an implicit side effect keyed on the type.

## A batch purge says which kind it removes, and what bounds it

- `EntityBatchPurger` tears down each deleted row's virtual entity, memberships and
  permissions, as `EntityPurger` does for one; `FieldBatchPurger` does not, because a
  field row holds nothing in the graph.
- The two are unrelated roots, so an entity spec cannot flow through the field path and
  leave its graph rows behind. There is no unmarked batch purge.
- What bounds the sweep follows the same axis every other write does: an entity batch is
  bounded by the scopes the ops call names, a field batch by the owner it is given —
  `build_subquery(owner_id)`, like `create_field(owner_id, ...)`. No field operation is
  scoped, and this one is not either.
- `EntityBatchPurger.entity_id(row)` takes the row: a batch names a subquery, not an id.

## Values left for the database to compute

- A creator may put a SQL expression on a column in `build_row()`; the value is then
  computed inside the INSERT, with no lock and no SELECT before it. A rank asking for
  "one past the last" is what this is for.
- Concurrent inserts can land on the same value. Do NOT use it where the order has to
  be deterministic.
- Such a column is read back once after the insert. ops works that out from the row, so
  a spec declares nothing.

## A field row's owner

- A field row carries no membership of its own. What it belongs to is only knowable
  through the entity that owns it, so an operation naming a field row has to read that
  entity before it has anything to validate and record against.
- `FieldOwnerLookup` declares that read: from a field row's id to its owning entity's
  id. A query rather than conditions, so an owner reached through a join is
  expressible; it selects the pair (row id, owner id), so one spec serves a single row
  and a batch alike.
- It takes two type parameters, so the type `field_id()` answers and the type this
  lookup handles cannot come apart.
- `FieldOwnerKeyLookup` reads the same thing from the other end: a caller-facing key to
  the owner. `FieldKeyLookup` reads the row's id and the owner's from that key in one
  query — an operation naming the row takes its id, so the key has to become one
  somewhere.
- Do NOT pre-read the owner to check existence. Declare the FK violation in
  `integrity_error_checks()` mapped to the domain error; preconditions beyond
  existence (e.g. lifecycle) belong to the service layer as EXISTS checks.

## Soft delete belongs to its own updaters

- The lifecycle column a domain deletes by — `deleted`, `status`, whichever carries
  the removed state — is NOT exposed on the general `DataUpdater`. With no field for
  it, the ordinary edit path cannot make the transition at all.
- Soft delete and restore each get their own updater, and `build_values()` returns a
  constant. A transition value taken as an argument is a value that can be passed
  wrong.
- Naming: `<Entity>SoftDeleteUpdater` / `<Entity>RestoreUpdater`, carried by a
  `Delete*` and a `Restore*` action base respectively.
- A domain that offers soft delete offers restore.
- ops executes both as an update — the DB operation is an UPDATE, so no delete
  operation exists to generalize. What records the run as a delete is the action's
  `operation_type()`; see `../../actions/AGENTS.md`.

## Naming: what is written vs where a read looks

`…_global_entity` / `…_entity` / `…_field_entity` methods name **what is written**;
`…_in_global` / `…_in_scopes` name the **operation scope** (where a read looks). Never
conflate the two axes.
