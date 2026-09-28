---
name: adapter-auth-and-scope
type: design-rationale
description: adapters as the single place for auth context and scope building, my search built on scoped_search by handlers and resolvers, and why response nodes carry entity_id/field_id beside the Relay id
scope: src/ai/backend/manager/api/adapters
keywords: [adapter, my_, current_user, OperationScope, self-service, entity_id, field_id, Relay id]
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager API adapters — Knowledge

> For rules, see the API layer `AGENTS.md`; for implementation patterns, see the `/api-guide` skill.

## Adapters own auth context and scope building

An adapter is the single implementation behind both API surfaces (REST v2 and GraphQL).
It builds the `OperationScope`, carries the caller context, and maps DTOs — handlers and
resolvers only pass the parsed input through. `my` searches are the exception: the handler and resolver build the user scope.

## The `my_` pattern

For an entity with a scoped search, the `my` search has no adapter method of its own. The REST handler takes the user
from `UserContext` and the GQL resolver from `current_user()`; each builds the user scope and calls `scoped_search`. The
scope permission check runs on the same path as the scoped search. This keeps each entity from gaining another adapter method.

A `my_` operation with no matching scoped search still takes the user context from `current_user()` inside the adapter
and builds the `OperationScope` there.

## Why `entity_id` / `field_id` sit beside `id`

The GQL `id` is a Relay global id: the type name and the row key base64-encoded into one
opaque value that clients do not look inside. The REST v2 `id` exposes that inner key as
is, and what the key is differs per entity: domains and resource groups use a name,
keypairs an access key, agents a string id. Recovering the row's UUID from `id` therefore
works differently per entity, and not at all where a name is the key.

`entity_id` and `field_id` expose that UUID under one name. The adapter takes the value
from the data class, so it does not depend on what `id` holds. They are present even
where the inner key of `id` is already the UUID: the two values then match, but `id` is
what Relay reads and `entity_id` is what a client passes to other APIs.

Entities and fields are named apart for the same reason `data/` splits them: an entity
row carries its own membership and a field row does not. The name tells from the response
alone whether a permission can be asked on that row.

Fair share values and resource allocation rows are outside the rule. The former are
computed per (resource group, scope) pair and the latter per (kernel, slot name); neither
is stored under a row id.
