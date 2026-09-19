---
name: search-field-declarations
type: design-rationale
description: why search filters and orders are declared per field instead of per-entity condition functions, why the declaration builds the data type from a row, why condition classes do not know filter DTOs, why operations reject None, the own / nested / linked split and its permission axes, nested versus flattened fields of other tables, the Correlation naming, why usage relations between entities stay out of the ownership graph, why an unreadable using entity refuses the search, why scopes and uses travel on the searcher, what field caps need from the declarations, how other services bound relational filters
scope: src/ai/backend/manager/models/specs/search
keywords: [SearchableField, NestedSearchableField, RowDataConverter, ToManyCorrelation, ToOneCorrelation, StringConditions, EnumConditions, MembershipConditions, ConditionOrder, apply_string_filter, apply_to_many_filter, UsageConditions, UsedBy, ScopeTarget, ScopedSearcher, GlobalSearcher, used_by]
sources:
  - src/ai/backend/manager/models/specs/search
  - src/ai/backend/manager/models/specs/conditions
  - src/ai/backend/manager/models/specs/orders
  - src/ai/backend/manager/repositories/base/filter_adapter.py
  - src/ai/backend/manager/models/vfolder/searchable_fields.py
  - src/ai/backend/manager/models/entity_label/searchable_fields.py
  - src/ai/backend/manager/models/scopes.py
  - src/ai/backend/manager/models/specs/searcher.py
  - src/ai/backend/manager/actions/v2/scope/validator/used_by.py
generated:
  by: claude-code/opus-5
  at: 2026-09-19
status: stable
---

# Search field declarations — Knowledge

> The rules are in `AGENTS.md` in the same directory.

This package replaces the condition functions and order methods written by hand per entity, one per field and operation, with one declaration per field. Filters, orders and permissions (field caps) all read the same list of fields.

## Declaring per field makes omissions checkable

- With functions, a "field" existed only in a naming convention, so a missing operation or order went unnoticed.
- A declaration carries a filter slot and an order slot together, so whether a field can be filtered or ordered shows in the declaration.
- mypy checks orders through `match` + `assert_never`; a sweep test checks that filter DTOs and declarations pair up.

## Building data from a row through the declaration makes omissions a type error

- Comparing declarations to data in a test misses an omission when the test, or the registration it relies on, is missing.
- `RowDataConverter.to_data` calls the data constructor directly and reads every value through the declaration's `read(row)`. Adding a data field without a declaration then fails mypy.
- `read` returns the column's value type, so mypy also checks that the declaration and the data field agree on type.
- Reading `row.x` directly instead of through the declaration cannot be stopped by types; review stops it.

## Every order is declared unless something forbids it

| Column kind | Order | Why |
|---|---|---|
| JSON/JSONB, arrays | No | A document structure; order has no meaning |
| `SecretColumn` | No | Comparing ciphertext means nothing and hints at the value |
| `DecimalType` | Needs a cast | Stored as VARCHAR, so `"10" < "9"` |
| enum | Yes | Alphabetical, not a meaningful order |
| Other scalars | Yes | |

- The order-field enum decides what is exposed. Cost (ordering without an index) is reviewed when a field is added to the enum.

## Condition classes do not know filter DTOs

| Layer | Holds |
|---|---|
| models (`conditions/`, `orders/`, `search/`) | Columns and SQL operations |
| adapter base (`BaseFilterAdapter.apply_*_filter`) | The branches turning DTO fields into operation calls |
| common DTOs | Fields only. Generic bases such as `EnumFilter[E]` and `ToManyFilter[F]` carry no logic either |

- The branches live in the adapter so that models do not import API DTOs.
- They used to exist three times — in the DTO, the adapter and the GQL type — and now exist once, in the adapter.

## Operations reject None

- Accepting `None` would make even callers that surely hold a value (guards, handlers) receive `QueryCondition | None`, adding branches that never run.
- Narrowing with `@overload` is not used: it multiplies the declarations per operation.
- Skipping an unset field happens in one place, `apply_*_filter`.

## own / nested / linked split by how permission applies

| Part | Criterion | Permission |
|---|---|---|
| own | The entity's own columns | The entity's field cap |
| nested | Rows in another table that the entity owns | The entity's field cap (path `labels.key`) |
| linked | Connections to other entities | Scopes, the other entity's permission |

- The split follows ownership, not tables. Labels live in another table but are the vfolder's data.
- One entry point means the sweep test and the permission check start from one place. The classes behind it are never referenced by name, so they are private.

## Fields of other tables are nested, not flattened

| | Flattened (`label_key`, `label_value`) | Nested (`labels.key`) |
|---|---|---|
| Grouping | One EXISTS per field, so a key and a value matching different labels still pass | One EXISTS over all conditions; they must match the same label |
| some / every / none | Not expressible | Provided by `ToManyCorrelation` |
| Path | Needs a new name | Same shape as the field cap and read paths |

- every is `NOT EXISTS(NOT P)`, so it is true when there are no children (BEP-1060).
- A dangling field (labels) differs only in linking by `(entity_type, entity_id)` instead of a foreign key; it is the same to-many.

## No nested filters into other entities, because nothing checks permission there

- The validator checks the caller's permission on a scope beforehand, but a nested filter only evaluates the other row's values inside EXISTS, row by row, without asking whether the caller can read that row.
- A filter result could then reveal values of rows the caller cannot read (another user's email, for example).
- Where it is needed (the related entity's status, searching by a display value, ordering by a related attribute), use a two-step lookup or an identifier copied into the entity's own column.
- Opening it would first need a shared part that adds "rows the caller can read" inside the EXISTS.
- For the same reason, rows with their own permission type, such as entity shares, are not `nested`.

## Called Correlation, not Relation

- In BEP-1075, `Relation` means "a link row two entities own together".
- The types here only find rows of another table linked to the outer row through a correlated subquery, so they take the SQL term.
- `.correlate()` removes the table from the subquery's FROM only when the outer SELECT has it. Used without an outer query it becomes a cross join.

## Usage relations stay out of the graph

- govern means "the scope's roles reach everything the target owns", so a project role governing a session would reach the vfolders it mounts.
- own + cap (a share) does not spread for per-entity permission, but a scoped search's reach ignores caps, so the listing would leak.
- So a usage only narrows and grants nothing. Its source of truth stays one foreign key column on the using side.
- An id inside a JSON value (`extra_mounts`, `vfolder_mounts`) is not a foreign key and is not a usage. It becomes one after it is normalized into rows with a foreign key.

## An unreadable using entity refuses the search

| Input | Check | Effect on the result |
|---|---|---|
| scope | Permission to read the result entity within the scope (govern) | Widens (OR) |
| used_by | Permission to read the using entity itself (own READ) | Narrows (AND) |
| filter | None | Narrows |

- Results only come from rows the scopes allow, so a row a using entity uses is still left out when the caller cannot read it.
- Search APIs with a permission model (GitHub search `repo:`, GCP Cloud Asset scopes) refuse a condition target the caller cannot read and limit results to what the caller can read. This follows them.
- The using side's permission is checked before the query, so SQL carries only the usage condition.
- The check has its own validator, apart from the scope validator: used_by exists only on searches and means nothing to other scope actions such as create. The two validators query the database separately; merging them is follow-up work.
- A global search does not check using entities: the SUPERADMIN gate answers for the unscoped read.
- This does not answer an owner asking "who uses my resource". That needs a limited usage listing on the result entity's side.

## Scopes and uses travel on the searcher

- `ScopedSearcher(scopes, used_by, searcher)` and `GlobalSearcher(used_by, searcher)` are the ops inputs. The action takes that one object as its field, and the checks read their targets from it.
- A `ScopeTarget` holds the scope id to check and the row restriction; a `UsedBy` holds the entity to check and its condition. What is checked cannot drift from what is queried.
- Before this, a `ScopeItem` wrapped an `OperationScope` one-to-one to form that pair. 31 of the 72 `OperationScope` classes had no item, so no authorization target was declared for them. Each becomes a `ScopeTarget` as its entity moves over.

## What field caps need from the declarations

| Need | Why |
|---|---|
| Declaration name = filter DTO field = data field = cap path | The requested path is used as the cap path without translation |
| Masking per row | Shares are per field path, so the same field has a different cap per row. Filters become `cap AND condition`, orders `CASE WHEN cap THEN column END` |
| Checking orders too | Values leak through ordering and repeated filtering even when not in the response |

## How other services open relational filters

| Service | Opens | Depth |
|---|---|---|
| Stripe, GitHub, Jira | Identifiers such as FK ids and names | 0–1 |
| Kubernetes | Its own labels | 0 |
| Linear, Prisma, Hasura | The related entity's full filter | Unlimited |
| Hasura depth limit | Counts only the selection set, not filter conditions | n/a |

- The more public the API, the more it stops at identifiers and owned parts.
- This package opens everything owned, narrows it with field caps, and expresses relations to other entities as scopes.
