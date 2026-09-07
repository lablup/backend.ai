---
name: unset-sentinel-typing
type: design-rationale
description: Unset sentinel for absent request fields — why it aliases typing_extensions.Sentinel instead of pydantic MISSING, mypy PEP 661 gap, nested access on OptionalState only, migration steps
scope: src/ai/backend/common/tristate
keywords: [Unset, UNSET, MISSING, PEP-661, Sentinel, TriState, OptionalState, from_unset, and_optional, and_tri, mypy, pyright]
sources:
  - src/ai/backend/common/tristate/unset.py
  - src/ai/backend/manager/types.py
generated:
  by: claude-code/opus-5
  at: 2026-09-07
status: draft
---

# `Unset` sentinel

## What it solves

It separates "the client did not send this field" from "the client sent null".

`UNSET` is `pydantic_core.MISSING`. pydantic drops a field holding it from serialization and
from the JSON schema, so an absent field puts no placeholder on the wire.

The previous mechanism was a `Sentinel` enum in `common/api_handlers.py`. It serialized the
absent state as the integer `1`, which the OpenAPI spec published as
`{"type":"integer","enum":[1]}`.

## Why `Unset` aliases `Sentinel`, not `MISSING`

`MISSING` is a PEP 661 sentinel, so using it in an annotation requires PEP 661 support in the
type checker.

| Tool | `str \| None \| MISSING` |
|---|---|
| mypy 1.18.2 (current) | `error: Variable "pydantic_core.MISSING" is not valid as a type` |
| mypy 2.3.1 (latest release) | same failure |
| mypy master (2.4.0+dev) | passes |
| pyright 1.1.411 | passes with `enableExperimentalFeatures` |

mypy merged PEP 661 support (`python/mypy#21647`, 2026-08-07) but has not released it.

So `Unset` names the real class the value belongs to, `typing_extensions.Sentinel`, rather than
the exact `MISSING` type. `isinstance(MISSING, Sentinel)` holds, so the annotation is wider than
needed but never false. The runtime value stays `MISSING`, so every serialization behaviour holds.

pyright rejects that widening — it treats `MISSING` as its own singleton type. `pants check` runs
mypy only, so CI is unaffected.

## Why the explicit generic before `and_optional` / `and_tri`

pyright rejects `Field(default=UNSET)`:

```
error: Type "MISSING" is not assignable to declared type "OptionsReq | Unset | None"
```

The field type then collapses to `Unknown`, `from_unset` cannot solve `TVal`, and the lambda
parameter that follows is `Unknown` too. The whole lambda body goes unchecked.

| | `options` | lambda parameter `o` |
|---|---|---|
| mypy, inferred | `OptionalState[OptionsReq]` | `OptionsReq` |
| mypy, explicit | `OptionalState[OptionsReq]` | `OptionsReq` |
| pyright, inferred | `OptionalState[Unknown]` | `Unknown` |
| pyright, explicit | `OptionalState[OptionsReq]` | `OptionsReq` |

An explicit generic fixes `TVal` by declaration instead of inference, skipping `Unknown`. The
target is editor completion and checking, not CI.

The rule goes away once `Unset` becomes `MISSING`.

## Why `TriState` has no nested-access method

A nested request model is a wire-side grouping with no column behind it. There is nothing to
clear, so a null parent means "leave this group alone".

Reading the parent as a `TriState` would spread that null into a NULLIFY on every child field.
A non-nullable child column then violates its constraint, and a nullable one is erased without
the client asking.

Nested access therefore lives on `OptionalState` only. `and_optional` / `and_tri` decides the
child's nullability, and an absent parent is always nop.

A nested model that occupies one nullable column whole is not taken apart. That shape is
`TriState.from_unset(...).map(...)` — see `_convert_model_definition_state` in
`api/adapters/deployment_revision_preset/adapter.py`.

## Why `isinstance`

mypy narrows an identity comparison only for `None`, enum members, and `Literal`. `value is UNSET`
does not narrow, so `cls.update(value)` in a `from_unset` body would receive `TVal | Sentinel`.

## Once mypy ships PEP 661

Two places change. The 78 DTO fields and the adapters do not.

| Location | Change |
|---|---|
| `unset.py` | `Unset: TypeAlias = Sentinel` → `TypeAlias = MISSING` |
| the two `from_unset` bodies in `manager/types.py` | `isinstance(value, Unset)` → `value is UNSET` |

`Unset` must be declared as a `TypeAlias`, not a plain assignment. Even with PEP 661 support mypy
reports `Variable ... is not valid as a type` for an alias variable in type position.

## Related location

`TriState` / `OptionalState` live in `manager/types.py`. `from_graphql` depends on graphql and
strawberry across 154 call sites, so they were not moved into this package.
