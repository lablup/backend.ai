# Write specs (v2 lineage) — Guardrails

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

`Global` / `Entity` / `Field` creator, purger, and upserter roots share NO
common ABC, and the shared method declarations are duplicated on purpose.

- Do NOT extract a common base or type any function against "any creator/purger".
  The absence of a common supertype is the enforcement: with one, an entity spec
  could flow through a scope-free execution path and silently skip its scope
  provisioning — the exact bug this lineage exists to prevent.
- Reuse execution logic through ops-layer helpers that take plain values
  (`row_class`, `pk_value`, ...), never through a shared spec supertype.

## Choosing a family

**Every entity doubles as a scope** — it can own memberships and be shared.
The only question left is whether the row is an entity at all:

| Family | Criterion | Write behavior |
|--------|-----------|----------------|
| Entity | A first-class entity (domain/project/user/vfolder/...) | create provisions the row's virtual scope node (self membership + self binding) and joins each `member_of()` scope; purge tears it all down symmetrically; upsert keeps the scope provisioned idempotently |
| Global | System-wide state outside the scope hierarchy | plain insert/delete/upsert |
| Field  | Owned by another entity; authorized through the owner (like an update to it), even if it has its own get/delete API | create requires `owner_id`; purge is a plain delete |

## Role-managed entities

Entities that allow role presets (domain/project/user) implement the combined
roots — `RoleManagedEntityCreator` / `RoleManagedEntityUpserter`, which declare
the entity hooks plus `RoleTemplateSource` — and are executed through the
role-managed ops methods (`create_role_managed_entity`, ...). The type decides
the path; there is NO runtime capability check (`isinstance`) anywhere.

- The combined roots are deliberately NOT subtypes of `EntityCreator` /
  `EntityUpserter` — the entity hooks are duplicated, same as between families.
  With the subtype relation, a role-managed spec would typecheck on the plain
  path and silently skip its preset roles. `RoleTemplateSource` is the only
  shared base; no write path accepts that type bare.

- Entity specs declare NO roles — role provisioning is preset-driven, keyed by
  the scope type; the spec contributes only `template_value(row)` for the
  presets' name templates. Restricting which scope types may carry presets is
  the preset-creation service's validation, not the spec's.
- The plain entity paths never touch roles, even when matching presets exist.
- Enrollment writes graph edges only. Granting a joining user the target scopes'
  auto_assign roles is an explicit ops primitive the user domain wires during
  its migration — never an implicit side effect keyed on the scope type.

## Scope declarations

- Do NOT override `scope_of()` — it is `@final`; answer the two hooks
  (`scope_type()` / `scope_id(row)`) instead.
- `member_of(row)` declares which existing scopes the new entity joins as a
  member (a project joins its domain; a keypair joins its user); a target
  without a virtual scope fails the write. It never carries a permission cap —
  capped sharing is the object-sharing mechanism, not creation.
- Scope types are open strings: types outside the RBAC element enum are
  accepted, and permission-carrying paths convert lazily.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).

## Naming: family vs operation scope

`…_global_entity` / `…_entity` / `…_field_entity` methods name the **write
family** (what is written); `…_in_global` / `…_in_scopes` name the **operation
scope** (where a read looks). Never conflate the two axes.

## Owner existence for field rows

Do NOT pre-read the owner to check existence. Declare the FK violation in
`integrity_error_checks()` mapped to the domain error; state preconditions
beyond existence (e.g. lifecycle) belong to the service layer as EXISTS checks.
