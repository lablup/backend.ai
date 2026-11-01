---
name: code-trace
description: Trace a feature across the layered architecture (REST v2, GraphQL, Service, Repository, DB, Errors) and explore the entity source tree, including how to read the 21k-line supergraph.graphql without loading it whole
tags:
  - exploration
  - navigation
  - rest-api
  - graphql
  - layers
---

# Code trace

Locate where a feature lives across layers. The codebase is split per entity, so once you know the entity name (`user`, `session`, `deployment` and so on), every layer is a predictable path.

## Layer map

`{entity}` is the entity name.

| Layer | Path | What is there |
|---|---|---|
| REST v2 entry | `manager/api/rest/v2/{entity}/registry.py` | `RouteRegistry`: method, path and middleware map to a handler method |
| REST v2 handler | `manager/api/rest/v2/{entity}/handler.py` | `V2{Entity}Handler`, which calls a processor |
| GraphQL resolver | `manager/api/gql/{entity}/resolver/{query,mutation}.py` | Strawberry query and mutation resolvers |
| GraphQL types | `manager/api/gql/{entity}/types/` | `node`, `inputs`, `payloads`, `filters`, `enums`, `scopes` |
| GraphQL root | `manager/api/gql/schema.py` | Assembles all resolvers into the schema |
| Service | `manager/services/{entity}/` | `service.py`, `processors.py`, `actions/`, `types.py` |
| Repository | `manager/repositories/{entity}/` | `repository.py`, `creators.py`/`updaters.py`/`purgers.py`, `db_source/` |
| DB models | `manager/models/` | SQLAlchemy tables |
| Errors | `{component}/errors/{domain}.py` | See `manager/errors/AGENTS.md` |

Flow: API handler → Processor → Service → Repository → DB. A handler does not call a service directly.

## Trace a request end to end

1. Find the entry: `grep -rn "reg.add" manager/api/rest/v2/{entity}/registry.py` for REST, or open `gql/{entity}/resolver/`.
2. Follow the handler or resolver to its processor, then to the service method, then to the repository.
3. The Action (frozen dataclass) passed into the service is in `services/{entity}/actions/`.

## supergraph.graphql

`supergraph.graphql` is 21k lines and generated as one file. Do not read it whole. Extract only the block you need:

```bash
# find the line number of a type or input
grep -n "^type User\b\|^input .*User\|^type Query\|^type Mutation" supergraph.graphql
```

Then `Read` with `offset` and `limit` around that line. The schema shows the contract only. For resolver logic, go to the source under `gql/{entity}/`.

## Related documents

- `/api-guide` - Implement REST and GraphQL endpoints
- `/repository-guide`, `/service-guide` - Layer patterns
- `manager/errors/AGENTS.md` - Find and define exceptions
