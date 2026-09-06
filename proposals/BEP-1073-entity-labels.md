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

Define a **generalized `key=value` label** that can be put on any entity, a **search over the labels
themselves**, and a **filter that selects entities by their labels**.

This BEP decides four things:

| Decision | Outcome |
|----------|---------|
| Label identity | A label is a map entry: one value per key on a target, replaced by writing the key again |
| Structure | One table; the entity it labels is a polymorphic reference, never a foreign key |
| Filter | `some` / `every` / `none` nested filter per [BEP-1060](BEP-1060-v2-connection-type-nested-filters.md), one shared `LabelFilter` reused by every labelable entity |
| API surface | One put, one remove, and one search, reusing the `audit_log` filter and page/order shape |

A label goes on any entity. The `labels` filter is wired first for **session, deployment, vfolder,
and agent**.

Labels are a standalone facility. They do not extend RBAC and RBAC does not define them; a label is
treated as a field of the entity it is attached to, so every permission check routes through that
entity. See [Access control](#access-control).

## Motivation

There is no general way to annotate or group entities. Operators cannot answer "which sessions
belong to the `prod` environment", "which vfolders does team `infra` own", or "which agents carry the
`gpu-reserved` marking", because nothing in the schema records that intent.

## Current Design & Scope

For each area, separate **✅ what already exists** from **➕ what to add**.

### Storage

| | Item |
|---|---|
| ✅ | `audit_logs` — the precedent for referring to an arbitrary entity by a polymorphic `(entity_type, entity_id)` pair instead of a foreign key |
| ➕ | The label table |

### Type system

| | Item |
|---|---|
| ✅ | `common/data/entity/types.py` — `EntityType` and `EntityID`, the polymorphic entity reference |

### Filtering

| | Item |
|---|---|
| ✅ | `make_correlated_exists` (`models/condition_utils.py`) — correlated `EXISTS` builder |
| ✅ | `BaseFilterAdapter.convert_string_filter` — `StringFilter` → `QueryCondition` |
| ✅ | `some` / `every` / `none` nested-filter convention (BEP-1060) |
| ✅ | `AND` / `OR` / `NOT` composition on each entity filter (e.g. `SessionFilter`) |
| ➕ | `LabelFilter`, and a `labels` nested field on the filter DTO of each wired entity |

### API

| | Item |
|---|---|
| ✅ | `audit_log` — the filter and page/order shape to reuse: `AND`/`OR`/`NOT` composition, cursor and offset pagination |
| ➕ | Label search, plus add / remove |

## Proposed Design

### 1. Label identity

A label is a **map entry**: a key holds one value on a target, as Kubernetes labels do. Writing a key
the target already carries replaces the value rather than adding a second row, which is why the write
is a put and not an add.

`UNIQUE (entity_type, entity_id, key)` is what enforces it. A caller wanting several values under one
name spells them into the key — `team-infra`, `team-ml` — or into the value as a delimited string it
parses itself.

### 2. Structure and relationships

One table (`entity_labels`), holding one row per key put on one entity: the entity, the key, and
the value.

The entity is a polymorphic `(entity_type, entity_id)` reference in the shape `audit_logs` already
uses — untyped at the DB level, discriminated by the accompanying type. No labelable table gains a
column or a constraint, and no entity type has to be known to the schema, so a label goes on anything.

Purging an entity removes its labels through the existing entity purger, so a dangling reference is
not a reachable state.

Column-level definitions, indexes, and constraints are settled in the implementing PR.

### 3. Searching labels

Label search answers "which labels are in use" — distinct from
[filtering entities](#4-filtering-entities-by-label), which answers "which entities carry this
label". Both are needed and neither substitutes for the other.

**One entry point, `search_labels`**, filtering on `key`, `value`, `entity_type`, and `entity_id`. It
returns the labels on entities the requester may read; an admin sees more because RBAC gives them
more entities, not because a second entry point exists. A label is a field of its entity, and a field
does not get an admin surface separate from a scoped one.

It is exposed on **GraphQL and REST v2 alike** — the SDK and CLI reach the API over REST.

The filter and page/order shapes are taken from `audit_log`: `AND` / `OR` / `NOT` composition on the
filter, and both cursor and offset pagination on the input.

### 4. Filtering entities by label

The shared v2 filter DTO drives GraphQL, REST v2, the SDK, and the CLI at once.

```graphql
input LabelFilter {
  key: StringFilter
  value: StringFilter
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

- **Query shape.** A correlated `EXISTS` over the label table against the entity row, with the key
  and value predicates applied inside it.
- **Visibility.** A label is readable exactly when its entity is, so the entity's own filtering
  already bounds what a label filter can match. Nothing further is needed, and a `none:` clause
  cannot become an oracle for labels the requester cannot see.

### 5. Write operations

Audit records are written by the system and only read through the API; labels are written by users.
These operations therefore have no `audit_log` counterpart.

| Operation | Shape |
|-----------|-------|
| Put | Names the entity and the `key=value`; sets the key, replacing whatever value it held |
| Remove | Names the label's own id, read from a search |

Put is an upsert, not an insert: a key holds one value, so naming a key the entity already carries is
a caller restating what it should be rather than a conflict. `updated_at` records when a value was
last replaced.

Remove names the row rather than the entity and the key, so every operation over a label row is
named the way the other field kinds are named. Which entity answers for it is read from the row
before the delete runs.

Defining a label and putting it on something are not separable steps: a label attached to nothing
has no meaning this BEP assigns it, and no rule anywhere restricts a label to one declared in
advance. Splitting the two would add a call and a state without adding a capability.

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
| Label search | The entities carrying the labels — a label is returned when its entity is readable |

Two things follow. Labels add no permission surface of their own: a label neither widens nor narrows
what its entity exposes, so nothing has to be re-derived when one is added or removed. And label
visibility needs no rule of its own — a label the requester cannot read is one whose entity they
cannot read, which the entity's own filtering already excludes.

## Migration / Compatibility

- **Additive only.** One new table and one optional filter field per wired entity. No existing query changes shape, and no existing table gains a column.
- **No backfill.** Labels start empty.

## Implementation Plan

| Phase | Work |
|-------|------|
| 1 | Domain types and the label table, with the alembic revision |
| 2 | Repository and service layers: add, remove, and search |
| 3 | DTO, adapter, GraphQL, and REST v2 surfaces |
| 4 | `LabelFilter` wiring for session, deployment, vfolder, and agent |
| 5 | SDK and CLI |
| 6 | Tests across the layers, and live verification against a running server |

Each entity beyond the initial four is filter wiring alone.

## Open Questions

None outstanding.

## References

- [BEP-1060: Standardizing v2 Connection-Type Nested Filters](BEP-1060-v2-connection-type-nested-filters.md) — `some`/`every`/`none` semantics and `make_correlated_exists`
- [BEP-1069: Entity Lifecycle Deletion Management](BEP-1069-entity-lifecycle-deletion.md) — purge propagation to dependent rows
- `audit_log` v2 surface — `api/rest/v2/audit_log/`, `api/gql/audit_log/`, `common/dto/manager/v2/audit_log/`
