---
name: gql-federation-and-pagination
type: constraints
description: adapter-backed resolvers and the scoped/admin_/public operation surface, federation name-collision caveat (V2-suffixed schema names), cursor vs offset pagination mode behavior, Node types by entity/field declaration, relation rows as non-Node relation types, relation-type connections with pair cursors and relation-type filters, published relation Nodes and their targets
scope: src/ai/backend/manager/api/gql
keywords: [federation, supergraph, Strawberry, Graphene, V2, cursor, offset, pagination, Connection, Edge, RoleAssignment, IdleCheckerAssignment, SessionIdleCheck, EntityShare]
sources:
  - scripts/generate-graphql-schema.sh
  - src/ai/backend/manager/api/gql/rbac/types/role.py
  - src/ai/backend/manager/api/gql/idle_checker_assignment/types.py
  - src/ai/backend/manager/api/gql/entity_share/types.py
  - src/ai/backend/manager/models/idle_checker/row.py
  - src/ai/backend/manager/models/rbac_models/user_role/row.py
  - src/ai/backend/common/data/entity/types.py
generated:
  by: claude-code/opus-5
  at: 2026-09-15
status: stable
---
# Manager GraphQL layer — Knowledge

> For the rules, see `AGENTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Adapter dependency and operation surface

Resolvers hold no behavior — every resolver calls the shared per-entity adapter
(`api/adapters/`). The operation surface follows the API-layer naming: scoped queries
take caller-supplied scopes (parent-fixed variants are the outgoing pattern — do not
add new ones), `admin_`-prefixed fields are superadmin global operations, and bare
global reads are public to every authenticated user.

## Federation name-collision caveat

The v2 Strawberry schema is composed into a supergraph together with the v1 Graphene schema. If a schema name with the
`GQL` suffix stripped collides with an existing v1 Graphene type of a different shape (e.g. `KeyPair`,
`CreateContainerRegistryInput`), supergraph composition fails. In that case, use a `V2`-suffixed schema name
(`name="KeyPairV2"`) — consistent with the existing `DomainV2`/`UserV2` convention. After renaming, verify composition with
`scripts/generate-graphql-schema.sh`.

## Pagination mode behavior

A search query accepts both cursor and offset arguments.

- **Default (no arguments):** falls back to offset (`limit=10, offset=0`).
- **Offset (`limit`/`offset`):** applies the user-specified `order_by`, or the entity's default sort if absent. For when custom sorting is needed.
- **Cursor (`first`/`after` or `last`/`before`):** the sort is fixed to the entity's cursor key (usually `created_at` or the PK).
  The user-specified `order_by` is ignored — a fixed sort is required for cursor consistency. Suited for infinite-scroll / "load more" UX.
- Only one mode per request. Mixing `first`+`limit` is an error.

## Nodes are entities and field rows; relation rows are not Nodes

| Declaration | Examples | GQL shape |
|---|---|---|
| `EntityType` | `EntityShare`, `AppConfigAllowList` | Node |
| `FieldType`, `DanglingFieldType` | `Permission`, `DomainFairShare`, `UserUsageBucket` | Node |
| None (a row joining two entities) | `user_roles`, `idle_checker_bindings`, `session_idle_checks` | relation type, not a Node |

- A Node is an object the server can refetch from its id alone (Relay Global Object Identification). A relation
  row is identified by its pair of ends, so an id apart from that pair means nothing.
- `session_idle_checks` has the (session, checker) pair as its primary key; `user_roles` has a surrogate id and a
  unique constraint on (user, role).
- A row with a lifecycle of its own is declared as an entity type, not kept as a relation.

## Relation values are read through connections of a relation type

A relation row carries values a client must read: who granted it and when, whether it is enabled, a session's
idle check status and deadline. Of the two ways to expose them, a connection of a relation type was chosen.

| Criterion | Entities joined directly, values on edge fields | Connection of a relation type |
|---|---|---|
| Reading values | edge fields | relation type fields |
| Types per relation | one Edge, Filter and OrderBy per direction | one relation type, Filter and OrderBy shared by both directions |
| Filtering on relation values and entity conditions together | a wrapper Filter per direction | end entity conditions nested in the relation type's Filter |
| Mutation payload | end ids only, or a separately defined shape | the changed relation type object |
| Distance to the other entity | one step | two steps (`node.checker`) |

- The Relay Connection spec allows an edge's `node` to be a plain Object that does not implement the Node interface.
- strawberry's `Edge` and `Connection` generics bind their type variable to Node, so a relation type connection
  needs a base that is not bound to Node.
- A cursor is an opaque string, so encoding the row's key in it opens no path to fetch or change a row by id. The
  cursor condition factory takes a string, which holds several primary key columns as well.
- A relation type is never read one row at a time by id, only as lists through connections and root scoped
  queries, so it has no data loader.

## A Node cannot keep its id while refusing id-based operations

- The v2 schema's root `node(id: ID!): Node` reads every type implementing Node by id. Blocking it means failing
  that lookup, which breaks the Node contract of refetching from the id alone.
- An `id` visible in the schema gets stored by clients and turns into requests to change rows by id.
- Node's benefit, client cache normalization, matters little here: relation values are shown inside the parent
  connection and a changed value comes back in the mutation payload.

## Relation type names follow the code, not the table

| Relation | Table | Code names (Data, DTO, CLI, REST) | Relation type |
|---|---|---|---|
| session↔idle checker | `session_idle_checks` | `SessionIdleCheckData` | `SessionIdleCheck` |
| scope↔idle checker | `idle_checker_bindings` | `IdleCheckerAssignmentData`, CLI `idle-checker-assignment` | `IdleCheckerAssignment` |
| user↔role | `user_roles` | DTO `RoleAssignmentNode`, CLI `rbac assignment`, REST `/assignments` | `RoleAssignmentV2` |

- Following the table would give `IdleCheckerBinding`, out of step with the service, CLI and REST names.
- `UserRole` would sit beside the account role enum `UserRoleV2` (`UserV2.role`, `UserV2.roles`) and read as a
  version of the same type.

## Published relation Nodes

| Relation | Now | Target |
|---|---|---|
| user↔role | `RoleAssignment` Node, deprecated | `RoleAssignmentV2` relation type connection |
| scope↔idle checker | `IdleCheckerAssignment` Node, unreleased | the same name as a relation type |
| session↔idle checker | no read, mutations only | `SessionIdleCheck` relation type connection |
