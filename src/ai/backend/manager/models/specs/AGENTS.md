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

## What a spec splits on depends on the operation

A row in the graph is an entity or a field, and which one it is comes from the table
in `KNOWLEDGE.md`. A row outside it is a sidecar — it stands on its own like an entity
and is read through an entity's permission like a field, while belonging to neither.

| Operation | Roots | Why |
|---|---|---|
| creator | `GlobalEntityCreator` / `EntityCreator` / `RoleManagedEntityCreator` / `FieldCreator` / `SidecarCreator` | only a create settles what a row belongs to |
| purger | `EntityPurger` / `FieldPurger` / `GuardedFieldPurger` | removing an entity removes what it left in the graph; a field row splits further on how it is picked: by id, or by id behind a precondition |
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
virtual scope node exactly as `EntityCreator` does. Rows are created under a global
entity too — an image under its container registry — so it has to be namable in the
graph. What it does not have is `member_of`, and the missing hook is what says it
joins nothing.

## Membership declarations

- `member_of(row)` declares which existing entities the new one joins as a member; a
  target without a virtual scope node fails the write. It never carries a permission
  cap (membership vs sharing: `KNOWLEDGE.md`).
- Entity types are open strings: types outside the RBAC element enum are accepted, and
  permission-carrying paths convert lazily.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).

## Role-managed entities

- Entities that allow role presets (domain/project/user) implement
  `RoleManagedEntityCreator` and are executed through the role-managed ops methods.
  The type decides the path; there is NO runtime capability check (`isinstance`).
- That root is deliberately NOT a subtype of `EntityCreator`. `RoleTemplateSource` is
  the only shared base; no write path accepts that type bare.
- Entity specs declare NO roles — the spec contributes only `template_value(row)` for
  the presets' name templates. Restricting which types may carry presets is the
  preset-creation service's validation.
- The plain entity paths never touch roles, even when matching presets exist.
- Enrollment writes graph edges only. Granting a joining user the target's auto_assign
  roles is an explicit ops primitive — never an implicit side effect keyed on the type.

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
