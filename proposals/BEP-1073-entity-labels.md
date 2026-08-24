---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Draft
Created: 2026-08-24
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Entity Labels

## Related Issues

- JIRA: **BA-7466** (this BEP)
- Epic: **BA-7465** — Entity labels: attach `key=value` labels across scopes and filter by them
- Origin: **BA-7326** (Feature Request) — tagging sessions and agents

## Goal

Define a **generalized `key=value` label** that any scope can define and attach to any entity, a
**search over the labels themselves**, and a **filter that selects entities by their labels**.

This BEP decides four things:

| Decision | Outcome |
|----------|---------|
| Label identity | A label is a `key=value` pair, not a map entry — a target may hold the same key twice with different values |
| Structure | A scope-owned definition table plus an attachment table; the target is a polymorphic entity reference, never a foreign key |
| Filter | `some` / `every` / `none` nested filter per [BEP-1060](BEP-1060-v2-connection-type-nested-filters.md), one shared `LabelFilter` reused by every labelable entity |
| API surface | One add and one remove operation, each naming scope, `key=value`, and target at once; label search as one admin entry point and one scoped entry point taking a scope argument, per `audit_log` |

The first targets are **session, deployment, vfolder, and agent**.

Labels are a standalone facility. They do not extend RBAC and RBAC does not define them; a label is
treated as a field of the entity it is attached to, so every permission check routes through that
entity. See [Access control](#access-control).

## Motivation

There is no general way to annotate or group entities. Operators cannot answer "which sessions
belong to the `prod` environment", "which vfolders does team `infra` own", or "which agents carry the
`gpu-reserved` marking", because nothing in the schema records that intent.

Labels are also the natural place to express **whose annotation this is**. The same key means
different things to a user and to a project — `env=staging` set by a user on their own sessions is
not the project's classification. A label therefore belongs to a scope rather than living as an
anonymous column on the target.

## Current Design & Scope

For each area, separate **✅ what already exists** from **➕ what to add**.

### Storage

| | Item |
|---|---|
| ✅ | `audit_logs` — the precedent for referring to an arbitrary entity by a polymorphic `(entity_type, entity_id)` pair instead of a foreign key |
| ➕ | The label definition table and the attachment table |

### Type system

| | Item |
|---|---|
| ✅ | `common/data/entity/types.py` — `EntityType`, `EntityID`, and `ScopeType`/`ScopeID`, which express that every entity doubles as a scope |
| ➕ | The set of entity types enabled as label targets |

### Filtering

| | Item |
|---|---|
| ✅ | `make_correlated_exists` (`models/condition_utils.py`) — correlated `EXISTS` builder |
| ✅ | `BaseFilterAdapter.convert_string_filter` — `StringFilter` → `QueryCondition` |
| ✅ | `some` / `every` / `none` nested-filter convention (BEP-1060) |
| ✅ | `AND` / `OR` / `NOT` composition on each entity filter (e.g. `SessionFilter`) |
| ➕ | `LabelFilter`, and a `labels` nested field on the filter DTO of each of the four targets |

### API

| | Item |
|---|---|
| ✅ | `audit_log` — admin search and scoped search as two entry points sharing one filter and one page/order shape |
| ✅ | `AuditLogScope` — an explicit scope input whose items are OR'd, rejected when empty |
| ➕ | Label search on both entry points, plus add / remove |

## Proposed Design

### 1. Label identity

A label is a **`key=value` pair**, not a map entry. A target may carry `team=infra` and `team=ml`
simultaneously.

This differs from Kubernetes label maps, where a key holds one value. Multi-value is the more useful
default here — membership in several teams, projects, or cost centers is common — and map behavior
is recoverable as a service-layer rule if a caller needs it. The reverse is not.

### 2. Structure and relationships

Two tables, and neither points at the target with a foreign key.

**The label definition table (`labels`)** holds one row per distinct `key=value` owned by a scope. It
is the catalog, and it is what [label search](#3-searching-labels) reads. The scope is recorded as a
`ScopeType`/`ScopeID` pair, so a label belongs to a domain, a project, or a user without any of those
tables gaining a column.

**The attachment table (`entity_labels`)** holds one row per attachment, linking a definition to a
target. The target is a polymorphic `(entity_type, entity_id)` reference in the shape `audit_logs`
already uses — untyped at the DB level, discriminated by the accompanying type. Enabling a new target
type is therefore filter-wiring work, not a schema change, and no labelable table gains a column or a
constraint.

The split keeps the catalog small — one row per distinct `key=value` per scope, regardless of how
many entities carry it — which keeps the entity filter's extra hop cheap.

**The catalog has no lifecycle of its own.** A definition row appears when a label is first added to
some target in that scope, and is reclaimed when the last target drops it. Nothing creates or deletes
one directly, so the split stays an internal storage choice and never surfaces as a second thing for
a caller to manage.

Purging a target removes its labels through the existing entity purger, so a dangling target
reference is not a reachable state.

Column-level definitions, indexes, and constraints are settled in the implementing PR.

### 3. Searching labels

Label search reads the catalog and answers "which labels are in use here" — distinct from
[filtering entities](#4-filtering-entities-by-label), which answers "which entities carry this
label". Both are needed and neither substitutes for the other.

There are two entry points, as in `audit_log`.

| Entry point | Bounding |
|-------------|----------|
| `admin_search_labels` | No scope input; superadmin only. Mirrors `AdminSearchAuditLogsInput` |
| `scoped_search_labels` | An explicit scope input whose items are OR'd and which is rejected when empty. Mirrors `ScopedSearchAuditLogsInput` / `AuditLogScope` |

There is no unscoped label search for non-admins.

Both are exposed on **GraphQL and REST v2 alike**. `audit_log` registers only its admin route over
REST and leaves the scoped one to GraphQL; labels cannot follow that, because the SDK and CLI reach
the API over REST and a scoped search is the call a non-admin makes.

Both share one filter and one page/order shape, taken from `audit_log`: `AND` / `OR` / `NOT`
composition on the filter, and both cursor and offset pagination on the input. A result is a
definition — scope, key, value — not an attachment.

### 4. Filtering entities by label

The shared v2 filter DTO drives GraphQL, REST v2, the SDK, and the CLI at once.

```graphql
input LabelFilter {
  key: StringFilter
  value: StringFilter
  scopeType: StringFilter
  scopeId: StringFilter
}

input LabelNestedFilter {
  some:  LabelFilter   # at least one label matches
  every: LabelFilter   # all labels match (vacuously true when unlabeled)
  none:  LabelFilter   # no label matches
}

input SessionFilter {
  # ...existing fields
  labels: LabelNestedFilter
}
```

**A `LabelFilter` matches one label row at a time**, so `key` and `value` inside the same block
constrain the *same* label. `some: {key: {equals: "env"}, value: {equals: "prod"}}` selects entities
carrying `env=prod` — not entities that have some label keyed `env` and, separately, some label
valued `prod`.

Conjunction across different labels uses the entity filter's existing `AND`, which every v2 entity
filter already carries:

```graphql
# sessions carrying both env=prod and team=infra
AND: [
  { labels: { some: { key: {equals: "env"},  value: {equals: "prod"} } } },
  { labels: { some: { key: {equals: "team"}, value: {equals: "infra"} } } }
]
```

Set semantics for `some` / `every` / `none` are those defined by BEP-1060; each field restates them
in its description.

Keys and values compare **case-sensitively** — `env=Prod` and `env=prod` are two labels, not one. The
`i_*` fields of `StringFilter` opt a single comparison out of that.

Two contract points bind the implementation:

- **Query shape.** A correlated `EXISTS` over the attachment table against the target row, with the
  definition predicate applied as a subquery on the definition reference. The extra hop is bounded by
  the catalog's size (§2).
- **Visibility.** Attachments whose definition lies outside what the requester may read are excluded
  **before** matching, not after. Otherwise a label filter becomes an oracle for labels the requester
  cannot see: `none: {key: {equals: "x"}}` would leak the existence of `x` by the rows it removes.

### 5. Write operations

Audit records are written by the system and only read through the API; labels are written by users.
These operations therefore have no `audit_log` counterpart.

There are two, and both name the scope, the `key=value`, and the target in a single call.

| Operation | Shape |
|-----------|-------|
| Add | Puts `key=value`, owned by the named scope, on the target |
| Remove | Takes it off the target |

Defining a label and putting it on something are not separable steps: a label that sits in a scope
attached to nothing has no meaning this BEP assigns it, and no rule anywhere restricts attachment to
labels declared in advance. Splitting the two would add a call and a state without adding a
capability.

A managed vocabulary — a scope declaring which labels its members may use — is the one thing the
split would buy. It is not required here, and it can be added later as a per-scope restriction on
`Add` without changing the storage or these two operations.

### 6. Layout

| Layer | Location |
|-------|----------|
| DTO | `common/dto/manager/v2/label/` |
| GraphQL | `api/gql/label/` |
| REST v2 | `api/rest/v2/label/` |
| Adapter | `api/adapters/label/` |
| Service | `services/label/` |
| Repository | `repositories/label/` |
| SDK | `client/v2/domains_v2/label.py` |
| CLI | `client/cli/v2/label/` |

### Access control

**A label is treated as a field of the entity it is attached to**, not as a subject holding
permissions of its own. Every check therefore routes through that entity, and is an ordinary RBAC
check against something that already exists.

| Action | Checked against |
|--------|-----------------|
| Add / remove | The entity, as a write to it |
| Read a label on an entity | The entity, as a read of it |
| Label search | The entities carrying the label — a catalog entry is visible when at least one carrier is |

Two things follow. Labels add no permission surface of their own: a label neither widens nor narrows
what its entity exposes, so nothing has to be re-derived when one is added or removed. And the
visibility rule in §4 stops being a special case — a label the requester cannot read is one whose
entity they cannot read, which the entity's own filtering already excludes.

## Migration / Compatibility

- **Additive only.** Two new tables and one optional filter field on each of the four target filters. No existing query changes shape, and no existing table gains a column.
- **No backfill.** Labels start empty.

## Implementation Plan

| Phase | Work |
|-------|------|
| 1 | Domain types and the two tables, with the alembic revision |
| 2 | Repository and service layers: add, remove, and both label searches, with grammar and scope validation |
| 3 | DTO, adapter, GraphQL, and REST v2 surfaces |
| 4 | `LabelFilter` wiring for session, deployment, vfolder, and agent |
| 5 | SDK and CLI |
| 6 | Tests across the layers, and live verification against a running server |

Each target beyond the initial four is filter wiring alone.

## Open Questions

None outstanding.

## References

- [BEP-1060: Standardizing v2 Connection-Type Nested Filters](BEP-1060-v2-connection-type-nested-filters.md) — `some`/`every`/`none` semantics and `make_correlated_exists`
- [BEP-1069: Entity Lifecycle Deletion Management](BEP-1069-entity-lifecycle-deletion.md) — purge propagation to dependent rows
- `audit_log` v2 surface — `api/rest/v2/audit_log/`, `api/gql/audit_log/`, `common/dto/manager/v2/audit_log/`
