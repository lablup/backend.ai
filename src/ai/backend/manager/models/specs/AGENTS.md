# Write specs (v2 lineage) — Guardrails

> For the family-choice table and design rationale, see `KNOWLEDGE.md` in the same directory.

Declarative write specs, colocated with the schema: a spec says *what* to write
(row, scope, memberships, checks); executing it is the ops layer's job
(`repositories/ops/v2/`). Specs must NOT touch sessions or issue SQL.

## Every v2-consumed spec lives here

Whatever spec type the v2 actions and ops consume is declared in this package —
the write families below, plus the read/update declarations (`querier.py`,
`lookup.py`, `searcher.py`, `updater.py`, `pagination.py`, and the batch purge
spec in `purger.py`). `repositories/base/` keeps legacy-compatible views
(aliases or bridge subclasses) for the transition only; do not declare a new
spec there.

## Three families, deliberately unrelated

- Choose the family (`Entity` / `Global` / `Field`) by the table in `KNOWLEDGE.md`.
- Do NOT extract a common base across the family roots or type any function
  against "any creator/purger" — the absence of a common supertype is the
  enforcement (rationale: `KNOWLEDGE.md`).
- Reuse execution logic through ops-layer helpers that take plain values
  (`row_class`, `pk_value`, ...), never through a shared spec supertype.

## Role-managed entities

- Entities that allow role presets (domain/project/user) implement the combined
  roots — `RoleManagedEntityCreator` / `RoleManagedEntityUpserter` — and are
  executed through the role-managed ops methods (`create_role_managed_entity`, ...).
  The type decides the path; there is NO runtime capability check (`isinstance`).
- The combined roots are deliberately NOT subtypes of `EntityCreator` /
  `EntityUpserter` (rationale: `KNOWLEDGE.md`). `RoleTemplateSource` is the only
  shared base; no write path accepts that type bare.
- Entity specs declare NO roles — the spec contributes only `template_value(row)`
  for the presets' name templates. Restricting which scope types may carry
  presets is the preset-creation service's validation, not the spec's.
- The plain entity paths never touch roles, even when matching presets exist.
- Enrollment writes graph edges only. Granting a joining user the target scopes'
  auto_assign roles is an explicit ops primitive — never an implicit side effect
  keyed on the scope type.

## Scope declarations

- Do NOT override `scope_of()` — it is `@final`; answer the two hooks
  (`scope_type()` / `scope_id(row)`) instead.
- `member_of(row)` declares which existing scopes the new entity joins as a
  member; a target without a virtual scope fails the write. It never carries a
  permission cap (membership vs sharing: `KNOWLEDGE.md`).
- Scope types are open strings: types outside the RBAC element enum are
  accepted, and permission-carrying paths convert lazily.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).

## Soft delete belongs to its own updaters

- The lifecycle column a domain deletes by — `deleted`, `status`, whichever
  carries the removed state — is NOT exposed on the general `DataUpdater`. With
  no field for it, the ordinary edit path cannot make the transition at all.
- Soft delete and restore each get their own updater, and `build_values()`
  returns a constant. A transition value taken as an argument is a value that can
  be passed wrong.
- Naming: `<Entity>SoftDeleteUpdater` / `<Entity>RestoreUpdater`, carried by a
  `Delete*` and a `Restore*` action base respectively.
- ops executes both as an update — the DB operation is an UPDATE, so no delete
  operation exists to generalize. What records the run as a delete is the
  action's `operation_type()`; see `../../actions/AGENTS.md`.

## Naming: family vs operation scope

`…_global_entity` / `…_entity` / `…_field_entity` methods name the **write
family** (what is written); `…_in_global` / `…_in_scopes` name the **operation
scope** (where a read looks). Never conflate the two axes.

## Owner existence for field rows

Do NOT pre-read the owner to check existence. Declare the FK violation in
`integrity_error_checks()` mapped to the domain error; state preconditions
beyond existence (e.g. lifecycle) belong to the service layer as EXISTS checks.
