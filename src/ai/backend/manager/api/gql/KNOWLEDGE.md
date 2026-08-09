---
name: gql-federation-and-pagination
type: constraints
description: adapter-backed resolvers and the scoped/admin_/public operation surface, federation name-collision caveat (V2-suffixed schema names), cursor vs offset pagination mode behavior
scope: src/ai/backend/manager/api/gql
keywords: [federation, supergraph, Strawberry, Graphene, V2, cursor, offset, pagination]
sources:
  - scripts/generate-graphql-schema.sh
generated:
  by: claude-code/fable-5
  at: 2026-08-10
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
