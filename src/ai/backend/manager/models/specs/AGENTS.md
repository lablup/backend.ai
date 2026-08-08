# Write specs (v2 lineage) — Guardrails

Declarative write specs, colocated with the schema: a spec says *what* to write
(row, membership, checks); executing it is the ops layer's job
(`repositories/ops/v2/provider.py`). Specs must NOT touch sessions or issue SQL.

## Three families, deliberately unrelated

`Global` / `Scoped` / `Field` creator, purger, and upserter roots share NO common
ABC, and the shared method declarations are duplicated on purpose.

- Do NOT extract a common base or type any function against "any creator/purger".
  The absence of a common supertype is the enforcement: with one, a scoped spec
  could flow through a membership-free execution path and silently skip
  registration — the exact bug this lineage exists to prevent.
- Reuse execution logic through ops-layer helpers that take plain values
  (`row_class`, `pk_value`, ...), never through a shared spec supertype.

## Choosing a family

Decided by one question: **does the entity get its own permission (scope
membership)?**

| Family | Criterion | Write behavior |
|--------|-----------|----------------|
| Scoped | Authorized by its own scope membership | create registers under the parent scope; purge removes the membership; upsert registers idempotently |
| Global | System-wide state outside the scope hierarchy | plain insert/delete/upsert |
| Field  | Owned by another entity; authorized through the owner (like an update to it), even if it has its own get/delete API | create requires `owner_id`; purge is a plain delete |

## Membership declarations

- One `ScopedMembership` subclass per entity, shared by all of that entity's
  scoped specs; specs return an instance from `membership()`.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).
- Do NOT override `membership_of()` — it is `@final`; answer the three hooks
  (`entity_type` / `entity_id(row)` / `parent_scope(row)`) instead.

## Naming: family vs operation scope

`…_global_entity` / `…_scoped_entity` / `…_field_entity` methods name the
**membership family** (what is written); `…_in_global` / `…_in_scopes` name the
**operation scope** (where a read looks). Never drop the `_entity` suffix from
family methods — that is what keeps the two axes apart.

## Owner existence for field rows

Do NOT pre-read the owner to check existence. Declare the FK violation in
`integrity_error_checks()` mapped to the domain error; state preconditions
beyond existence (e.g. lifecycle) belong to the service layer as EXISTS checks.
