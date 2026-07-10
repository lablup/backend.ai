---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-10
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Standardizing v2 Connection-Type (To-Many) Nested Filters

## Related Issues

- JIRA: BA-6819 (this BEP)
- Epic: BA-6818 — Standardize v2 connection-type (to-many) nested filters

## Goal

Define a single convention for **v2 connection-type (to-many) nested filters** — filtering a
parent entity by conditions on its related child collection — and apply it first to
`DeploymentFilter.replicas` (filter deployments by their route/replica conditions).

This BEP decides three things plus the first application:

| Decision | Outcome |
|----------|---------|
| Filter shape | Explicit `some` / `every` / `none` matching modes (new standard) |
| Reusable abstraction | Shared `make_correlated_exists` builder + per-entity binding (rbac-style name) |
| Semantics documentation | Each matching-mode field states its exact set semantics in the description |

The v2 filter DTOs are the single source of truth shared by GraphQL, REST v2, the Client SDK, and
the CLI. This convention governs how every to-many nested filter is added across those layers going
forward.

## Motivation

`DeploymentFilter` today cannot answer operational questions such as "which deployments have at
least one running replica" or "which deployments have no healthy replica." The existing `status`
filter reflects only the deployment lifecycle (`READY`), not the actual `running` / `healthy` /
`active` state of its routes. That gap is what drove Epic BA-6818.

More broadly, two entities already implement to-many nested filters, but each hand-rolled its own
shape with no shared convention. Without a standard, every new filter re-decides shape, semantics,
and query construction — producing an inconsistent API surface across entities.

## Current Design & Scope

For each area, separate **✅ what already exists** from **➕ what to add**.

### Filter shape (DTO/GQL surface)

Both precedents use **implicit-some**: the mere presence of a single `{Relation}NestedFilter` embed
means "at least one child matches."

| | Item |
|---|---|
| ✅ | image → alias: `ImageV2Filter.alias` (implicit-some), desc "at least one alias matching" |
| ✅ | rbac role → user/scope: `RoleConditions.by_assigned_user_id` / `by_mapped_scope` (implicit-some) |
| ✅ | `some`/`every`/`none` matching modes: **zero usage** in the codebase |
| ➕ | Define explicit some/every/none as the new standard (Decision 1) |
| ➕ | deployment → replicas: new nested filter — filter deployments by replica/route state (this BEP's first application) |

> Retrofitting the two existing implicit-some precedents is follow-up work (see Migration).

### Query construction (adapter/conditions translation)

| | Item |
|---|---|
| ✅ | image → alias: `sa.exists` baked into each `ImageConditions.by_alias_*` (one EXISTS per leaf, single predicate). **Non-composable** |
| ✅ | rbac role → user: `RoleConditions.by_assigned_user_id(list[QueryCondition])` — folds a **list** of child predicates into one correlated EXISTS. **Composable** |
| ➕ | Shared `make_correlated_exists` builder + entity binding `DeploymentConditions.by_replica_exists` (Decision 2) |
| ➕ | some/every/none → EXISTS/NOT EXISTS mapping placed in the adapter, reusing `negate_conditions` |

### Shared plumbing (all exists, reused)

| | Item |
|---|---|
| ✅ | `models/clauses.py` — `QueryCondition = Callable[[], ColumnElement[bool]]` |
| ✅ | `repositories/base/filter_adapter.py` — `convert_string_filter` / `convert_uuid_filter` (leaf filter DTO → condition) |
| ✅ | `repositories/base/utils.py` — `combine_conditions_and` / `combine_conditions_or` / `negate_conditions` |
| ✅ | `repositories/base/querier.py` — folds a condition list into the `WHERE` clause |

## Proposed Convention

### Prior art (conventions in other systems)

To-many relation filters already have a de-facto standard across the GraphQL ecosystem. This BEP
follows it.

| System | Shape | `every` on empty collection | Expressing "no match" |
|--------|-------|-----------------------------|-----------------------|
| Prisma | `some` / `every` / `none` | true (documented; also raised as counter-intuitive) | `none: {…}`; existence via `some: {}` / `none: {}` |
| PostGraphile (connection-filter) | `some` / `every` / `none` | true | `none: {…}` |
| Hasura | implicit-some (nested `where` = "any") | (no `every`) | `_not: {condition}` |

- **The `some`/`every`/`none` trio matches the established Prisma/PostGraphile convention** →
  Decision 1 adopts it.
- The "`every` is true on an empty collection" behavior is the same in these systems (Prisma
  documents it explicitly).
- **"has a child and all match"** (non-empty `every`) is expressed in all three systems without a
  dedicated shorthand, by combining **`some: {}` + `every: {…}`**. This BEP likewise adopts that
  idiom rather than adding a shorthand.

### Decision 1 — Shape: explicit `some` / `every` / `none`

A to-many nested filter is expressed as a per-relation nested-filter model with up to three
matching-mode fields, each carrying the child entity's own filter:

```
{Relation}NestedFilter:
  some:  {Child}Filter   # the parent has at least one child matching all conditions
  every: {Child}Filter   # every child of the parent matches all conditions
  none:  {Child}Filter   # the parent has no child matching any condition
```

- All three fields are optional. When more than one is given, they combine with **AND**.
- **Naming rule:** the parent filter embeds this model under a field named after the **plural
  to-many relation** (`DeploymentFilter.replicas`, `ImageFilter.aliases` …). If an existing
  implicit-some field already occupies a singular name, keep that singular field deprecated and add
  the plural one anew (→ Migration).

**Set semantics** (the contract the description must state):

| Matching mode | Meaning | Translation |
|---------------|---------|-------------|
| `some` | at least one child matches | `EXISTS (child where P)` |
| `every` | all children match | `NOT EXISTS (child where NOT P)` |
| `none` | no child matches | `NOT EXISTS (child where P)` |

**Empty-collection note — must be documented:** `every` is also true for a parent that has **no**
children at all. "All children satisfy P" holds trivially when there are zero children, because
there is no child to violate it (`NOT EXISTS (child that violates P)` is true over an empty set).
A deployment with zero replicas therefore matches `replicas.every`. This is standard behavior but
surprises users, so the field description must state it. If you need "has a child and all match,"
combine `some: {}` (has any child) with `every: {…}`, exactly as Prisma/PostGraphile do.

**Trade-off considered.** The house style to date is implicit-some (a bare embed = `some`). Keeping
it would match the two precedents and add no new concept, but it cannot express `every` or `none`
at all — the exact operational queries that drove BA-6818 ("all replicas healthy," "no replica
running"). It was therefore **rejected**. Explicit matching modes cost one extra nesting level and
diverge from the two implicit-some precedents (resolved in Migration), but they are the minimum
shape that covers the real query needs and reads unambiguously.

### Decision 2 — Reusable abstraction: shared `make_correlated_exists` + per-entity binding

The logic that builds a correlated `EXISTS` lives in **one shared builder**; each entity exposes it
as a **domain-named factory** by binding the builder to its relation. The entity-facing name
continues the rbac `by_assigned_user_id(list[QueryCondition])` shape.

```
# shared builder (models/condition_utils.py)
make_correlated_exists(child_row, correlate_row, join_predicate)
    -> Callable[[list[QueryCondition]], QueryCondition]

# entity binding (models/endpoint/conditions.py)
DeploymentConditions.by_replica_exists = make_correlated_exists(
    child_row=RoutingRow,
    correlate_row=EndpointRow,
    join_predicate=RoutingRow.endpoint == EndpointRow.id,
)
# call: by_replica_exists(route_conditions)
#   -> EXISTS ( SELECT 1 FROM routings
#               WHERE routings.endpoint = endpoints.id AND <route_conditions...> )
```

- **Why both:** the shared builder keeps the correlated-`EXISTS` construction (correlated subquery,
  join, `.correlate()`) in one place so entities don't re-hand-roll it. At the same time, entity
  code is exposed under a domain name like `by_replica_exists` to preserve readability and
  discoverability.
- The builder produces only the positive `EXISTS`. The `some`/`every`/`none` → `EXISTS`/`NOT EXISTS`
  mapping is the **adapter's** responsibility, reusing the existing `negate_conditions`.
- The child predicates come from the entity's existing leaf-filter converter — for deployment,
  `_convert_replica_filter`, which already yields `RouteConditions.*` over `RoutingRow`.
- The two precedents (image bakes an `EXISTS` per leaf; rbac folds a list) also converge on this
  shared builder when they are later retrofitted.

### Decision 3 — Semantics documentation standard

Each matching-mode field's description states its exact set semantics, extending the precedent set
by `ImageV2Filter.alias` ("at least one alias matching"):

| Field | Required description form |
|-------|---------------------------|
| `some` | "Matches parents with **at least one** {child} satisfying all conditions." |
| `every` | "Matches parents where **every** {child} satisfies all conditions (**also true when the parent has no {child}**)." |
| `none` | "Matches parents with **no** {child} satisfying any condition." |

The `every` description must carry the "also true when there are no {child}" clause so the behavior
is discoverable from the schema alone.

## First Application — `DeploymentFilter.replicas`

Applies the convention above to filter deployments by their routes. No existing implicit-some field
exists for deployment replicas, so this is greenfield — it starts directly in the new shape.

| Layer | Change |
|-------|--------|
| DTO (`common/dto/manager/v2/deployment/request.py`) | Add `ReplicaNestedFilter { some, every, none: ReplicaFilter }`; embed as `DeploymentFilter.replicas`. Reuse the existing `ReplicaFilter` for inner conditions. |
| GQL (`api/gql/deployment/types/deployment.py`) | Add `ReplicaNestedFilterGQL` (schema name `ReplicaNestedFilter`) and the `DeploymentFilter.replicas` field, `added_version = NEXT_RELEASE_VERSION`, with the Decision-3 descriptions. |
| Adapter (`api/adapters/deployment/adapter.py`, `_convert_deployment_filter`) | Add a `replicas` branch. Build the inner route predicates by **reusing `_convert_replica_filter`**, then map `some` → `by_replica_exists(preds)`, `none` → `negate_conditions([by_replica_exists(preds)])`, `every` → `negate_conditions([by_replica_exists(per-child-negated preds)])`. |
| Conditions (`models/condition_utils.py`, `models/endpoint/conditions.py`) | Add the shared `make_correlated_exists(child_row, correlate_row, join_predicate)` builder + `DeploymentConditions.by_replica_exists` = that builder bound to `RoutingRow.endpoint == EndpointRow.id` (FK `routings.endpoint → endpoints.id`). |

The join key is the existing FK: `RoutingRow.endpoint` → `endpoints.id`. The `EXISTS` correlates on
`EndpointRow`, mirroring rbac's `.correlate(RoleRow)`.

REST v2, the Client SDK, and the CLI pick up the new DTO field automatically as the shared schema;
no behavior specific to those layers is required.

## Migration / Compatibility

- **The new field is additive.** `DeploymentFilter.replicas` is a new optional field — no breaking
  change to the GraphQL schema or existing clients.
- **Existing implicit-some precedents (image → alias, rbac) are kept, marked only `@deprecated`.**
  Their current shape is semantically equivalent to `some`, so they keep working. A new
  `some/every/none` filter is added **as a separate field alongside** them (additive,
  non-breaking). GraphQL cannot have two fields with the same name, so **the new field must be named
  differently** — it uses the plural to-many relation name while the deprecated field keeps its
  original name. Example: image adds a new `aliases: { some, every, none }` next to the deprecated
  `alias`. Deployment is greenfield and starts with `replicas` directly. This per-entity retrofit is
  out of scope for this BEP and tracked as follow-up Stories under BA-6818.
- **No DB migration.** The convention is query-construction only; no schema changes.

## Implementation Plan

1. **Convention + first application (this BEP's scope, one Story)**
   - `ReplicaNestedFilter` DTO + `DeploymentFilter.replicas` embed
   - shared `make_correlated_exists` builder + `DeploymentConditions.by_replica_exists`
   - Adapter `replicas` branch (some/every/none mapping), reusing `_convert_replica_filter`
   - GQL `ReplicaNestedFilterGQL` + field (Decision-3 descriptions)
   - Tests: `some` / `every` (incl. the zero-replica true case) / `none`, plus combination with the
     top-level `AND` / `OR` / `NOT`
2. **Retrofit existing precedents (follow-up Stories under BA-6818)**
   - Mark image → alias and rbac implicit-some fields `@deprecated`
   - Add new `some/every/none` fields under a different (plural relation) name
   - Converge each entity's correlated-`EXISTS` on the shared `make_correlated_exists` builder

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-10 | Shape = explicit `some`/`every`/`none` | implicit-some cannot express `every`/`none` — the operational queries driving BA-6818; matches the established Prisma/PostGraphile convention |
| 2026-07-10 | Non-empty `every` uses `some: {}` + `every: {…}`, no dedicated shorthand | Prisma, PostGraphile, and Hasura all recommend the same idiom |
| 2026-07-10 | Shared `make_correlated_exists(child_row, correlate_row, join_predicate)` builder + per-entity binding (`by_replica_exists`) | Keeps correlated-`EXISTS` construction in one place while exposing a domain name per entity |
| 2026-07-10 | some/every/none → EXISTS/NOT EXISTS mapping lives in the adapter | Keeps the conditions layer to one new symbol per entity, reusing `negate_conditions` |
| 2026-07-10 | New `some/every/none` field name = **plural to-many relation** (e.g. `aliases`, `replicas`); the existing singular implicit-some field is only `@deprecated` | GraphQL forbids duplicate field names + preserves backward compatibility + consistent naming |

## Open Questions

- **Retrofit ordering/timing:** the naming rule is settled (plural), so only the timing of
  deprecating each implicit-some field relative to that entity's v2 GA remains — decided per
  follow-up Story.

## References

- [BEP-1021: GQL StringFilter Enhancement](BEP-1021-gql-string-filter-enhancement.md) — prior filter-convention BEP (same author/area)
- [BEP-1038: ImageV2 GQL Implementation](BEP-1038-image-v2-gql-implementation.md) — image → alias nested filter precedent
- [BEP-1008: RBAC](BEP-1008-RBAC.md) — role → user/scope nested filter precedent
- [Prisma — Relation queries (some/every/none)](https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries) — de-facto standard for to-many filters; `every` on empty collections
- [PostGraphile connection-filter — Filtering](https://www.graphile.org/postgraphile/filtering/) — one-to-many `some`/`every`/`none`
- [Hasura — Filter based on nested objects](https://hasura.io/docs/2.0/queries/postgres/filters/using-nested-objects/) — implicit-some + `_not` (none)
