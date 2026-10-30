---
name: gql-federation-and-pagination
type: constraints
description: adapter-backed resolvers and the scoped/admin_/public operation surface, federation name-collision caveat (V2-suffixed schema names), cursor vs offset pagination mode behavior, Node types by entity/field declaration, relation types as Nodes with a global ID built from the end UUIDs, relation-type connections with end-key cursors and relation-type filters, mutation payloads (target Node vs purgedId for Relay @deleteEdge/@deleteRecord, asynchronous purge), published relation Nodes and their targets
scope: src/ai/backend/manager/api/gql
keywords: [federation, supergraph, Strawberry, Graphene, V2, cursor, offset, pagination, Connection, Edge, RoleAssignment, IdleCheckerAssignment, SessionIdleCheck, EntityShare, purgedId, deleteEdge, purge_status, global ID]
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
  at: 2026-10-20
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

## Relations are Nodes too: the id is a global ID built from the ends

| Declaration | Examples | GQL shape | `id` |
|---|---|---|---|
| `EntityType` | `EntityShare`, `AppConfigAllowList` | Node | global ID of the row id |
| `FieldType`, `DanglingFieldType` | `Permission`, `DomainFairShare`, `UserUsageBucket` | Node | global ID of the row id |
| None (a row joining two entities) | `user_roles`, `idle_checker_bindings`, `session_idle_checks` | relation type, Node | global ID of the end UUIDs |

- A Node is an object the server can refetch from its id alone (Relay Global Object Identification). A relation
  is fixed by its ends, so a global ID carrying the ends refetches it from the id alone.
- A relation table has no row id; the pair of ends is its primary key (BEP-1075). An id outside the pair is a
  second name for the same relation, and a relation found by it has to be read again by its ends before its
  permission can be asked.
- As a Node, a relation is normalized by the Relay store, and the `purgedId` of an unlink response feeds
  `@deleteEdge`.
- The global ID stays in the GQL layer, so an id a client stored does not turn into a request changing the
  relation. Arguments that change a relation are the end UUIDs.
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

- With relation types as Nodes, their connections use strawberry's `Edge` and `Connection` generics as they are.
- A cursor is an opaque string, so encoding the end keys in it opens no path to change a row by id. The cursor
  condition factory takes a string, which holds several primary key columns as well.
- `node(id:)` and `nodes(ids:)` read relations by a list of end keys at once and ask read on both end scopes.
  The global ID carries both ends, so asking one side only would reveal the other end entity without permission.

## A Node cannot keep its id while refusing id-based operations

- The v2 schema's root `node(id: ID!): Node` reads every type implementing Node by id. Blocking it means failing
  that lookup, which breaks the Node contract of refetching from the id alone.
- `DomainFairShare`, `ProjectFairShare` and `UserFairShare` are computed per (resource group, scope) pair and
  have no row id. `node(id:)` and `nodes(ids:)` answer their ids with `null`, not an error.

## A mutation payload follows whether the target exists at response time

| Target at response time | Payload | Why |
|---|---|---|
| exists (create, update, soft delete, restore, purge of an entity with `purge_status`) | the target Node | the Relay store updates the record with the same id |
| gone (purge finishing within the request, force purge) | `purgedId` + UUID | `@deleteEdge` and `@deleteRecord` take an `ID` or `[ID]` field and remove that node's edges and record |

- A global ID in the payload's own `id` becomes the same Relay store key as the removed Node and collides. The
  Relay example (`deletedTodoId`), GitHub (`deletedItemId`) and Shopify (`deletedProductId`) use a field of
  their own.
- Returning the removed target as a Node fails its child connections on the removed target's permission check
  (`PurgeRolePresetPayload.rolePreset.permissionPresets`).
- An entity with `purge_status` (BEP-1069) still has its row when the purge request returns. A `purgedId` there
  would report a Node that still exists as removed. Kubernetes answers a DELETE on an object with pending
  finalizers with 202 and the remaining object; Shopify's asynchronous `productDelete` returns an operation
  object and fills `deletedProductId` once it completes.
- The field is `purgedId`, not `deletedId`: here delete is a soft delete (`deleted_at`) whose response returns
  the Node. The examples above name the field after their own mutation verb (`productDelete` →
  `deletedProductId`).
- A purge payload is a type of its own (`Purge<X>Payload`). A `Delete*Payload` shared with a soft delete or a
  deprecated delete would put `purgedId` on a response whose target may still exist.
- REST and DTOs do not carry global IDs. Azure Key Vault's purge answers 204 with no body, and AIP-165 `Purge`
  returns the removed count only.

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
| user↔role | `RoleAssignment` Node (row id), deprecated | `RoleAssignmentV2` relation Node, id from (user, role) |
| scope↔idle checker | `IdleCheckerAssignment` Node (row id), unreleased | a relation Node of the same name, id from (scope type, scope id, idle checker) |
| session↔idle checker | no read, mutations only | `SessionIdleCheck` relation Node, id from (session, idle checker) |

- `RoleAssignment.id` keeps its `ID!` type; only its value becomes the global ID of the ends.
