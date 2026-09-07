# Common DTO — Guardrails

> This package is shared by all components. Changes here affect manager, agent, storage, and client SDK
> at the same time — check all callers before modifying fields.

## Purpose

DTOs shared by multiple backend.ai components (manager, agent, storage, client SDK). DTOs used by only a
single component belong in that component's `dto/` directory.

## Directory structure

Organized by target component: `common/dto/{manager|agent|storage|clients|internal}/`.

## Rules

- All DTOs must inherit from `BaseRequestModel` (Pydantic v2).
- No business logic — validation and serialization only.
- Check all callers across components before modifying fields.
- Use only `v2/` DTOs (e.g., `common/dto/manager/v2/`). DTOs outside `v2/` are deprecated and must not be used in new code.

## Create and update input schemas

Create and update always get separate models. So do nested models.

Tri-state is meaningful in update schemas only.

### Create

Do NOT use `Unset`.

| Field | Declaration |
|---|---|
| required | required — no default |
| nullable | `X \| None = Field(default=None)` |

When adding a field:

- **Required value**: give it a default in the schema. If the default is only known at runtime,
  declare it nullable and fill it in the logic (the model definition mechanism). The latter is
  the more common case, since users often set the default themselves.
- **Nullable value**: add it with `default=None`. The logic takes the null and applies its own
  default.

Reference: `CreateQueryDefinitionRequest` in
`common/dto/manager/prometheus_query_preset/request.py`.

### Update

Only the id that selects the target is required. Every other field is
`X | None | Unset = Field(default=UNSET)`.

What null means is decided by the target column, and the constructor the adapter uses states it.

| Column | Adapter | null | unset |
|---|---|---|---|
| nullable | `TriState.from_unset` | clears it | leaves it |
| non-nullable | `OptionalState.from_unset` | leaves it | leaves it |

A non-nullable column does not separate null from unset. It only decides whether the value changes.

Read a nested model by taking the parent as an `OptionalState` and pulling the child field from
it. Keep the lambda body to a single field access.

| Child field's column | Method |
|---|---|
| non-nullable | `and_optional` |
| nullable | `and_tri` |

An absent parent and a null parent are both nop. Do NOT read the parent as a `TriState` and let a
nullify spread into the children — only the child's own null clears it.

A nested model that occupies one nullable column whole is not taken apart. Use
`TriState.from_unset(...).map(...)`.

A `from_unset` feeding `and_optional` / `and_tri` MUST name its generic type. Other `from_unset`
calls need not.

```python
options = OptionalState[ModifyQueryDefinitionOptionsRequest].from_unset(request.options)
...
    filter_labels=options.and_optional(lambda o: o.filter_labels),
```

`Unset` lives in `common/tristate/unset.py`.


## Bulk mutation payloads

| Operation | Payload fields |
|---|---|
| Soft delete | `items: list[<Entity>Node]`, `failed: list[<Operation><Entity>Error]` |
| Hard delete (purge) | `successes: list[UUID]`, `failed: list[<Operation><Entity>Error]` |
