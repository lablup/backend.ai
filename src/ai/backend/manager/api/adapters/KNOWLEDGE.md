---
name: adapter-auth-and-scope
type: design-rationale
description: adapters as the single place for auth context and scope building, my_ self-service pattern (current_user inside the adapter)
scope: src/ai/backend/manager/api/adapters
keywords: [adapter, my_, current_user, OperationScope, self-service]
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
resolvers only pass the parsed input through.

## The `my_` pattern

For self-service (`my_`) operations, authentication is handled inside the adapter. The adapter calls `current_user()`
to obtain the user context and builds the `OperationScope` from it. The GQL resolver / REST handler does not pass the scope —
it only passes the search input DTO. This is to gather the auth logic into the adapter instead of scattering it across every resolver.
