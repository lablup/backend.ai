---
name: code-trace
description: Trace a feature across the layered architecture (REST v2, GraphQL, Service, Repository, DB, Errors) and explore the entity source tree: includes how to read the 21k-line supergraph.graphql without loading it whole
tags:
  - exploration
  - navigation
  - rest-api
  - graphql
  - layers
---

# Code Trace

Locate where a feature lives across layers. The codebase is split per entity, so once you know the entity name (`user`, `session`, `deployment`, …) every layer is a predictable path.

## Layer map (`{entity}` = entity name)

| Layer | Path | What's there |
|-------|------|--------------|
| REST v2 entry | `manager/api/rest/v2/{entity}/registry.py` | `RouteRegistry`: method, path and middleware map to a handler method |
| REST v2 handler | `manager/api/rest/v2/{entity}/handler.py` | `V2{Entity}Handler`, which calls a Processor |
| GraphQL resolver | `manager/api/gql/{entity}/resolver/{query,mutation}.py` | Strawberry query and mutation resolvers |
| GraphQL types | `manager/api/gql/{entity}/types/` | `node`, `inputs`, `payloads`, `filters`, `enums`, `scopes` |
| GraphQL root | `manager/api/gql/schema.py` | Assembles all resolvers into the schema |
| Service | `manager/services/{entity}/` | `service.py`, `processors.py`, `actions/`, `types.py` |
| Repository | `manager/repositories/{entity}/` | `repository.py`, `creators.py`/`updaters.py`/`purgers.py`, `db_source/` |
| DB models | `manager/models/` | SQLAlchemy tables |
| Errors | `{component}/errors/{domain}.py` | See `manager/errors/AGENTS.md` |

Flow: `API handler → Processor → Service → Repository → DB`. Handlers do not call Services directly.

## Trace a request end to end

1. Find the entry: `grep -rn "reg.add" manager/api/rest/v2/{entity}/registry.py` (REST) or open `gql/{entity}/resolver/`.
2. Follow the handler/resolver to its Processor, then to the Service method, then to the Repository.
3. The Action (frozen dataclass) passed into the Service is in `services/{entity}/actions/`.

## supergraph.graphql (21k lines)

Do not read it whole; it is generated as a single file. Extract only the block you need:

```bash
# find the line number of a type or input
grep -n "^type User\b\|^input .*User\|^type Query\|^type Mutation" supergraph.graphql
```

Then `Read` with `offset` and `limit` around that line. For the actual resolver logic, jump to the source under `gql/{entity}/` instead. The schema only shows the contract.

## Related documents

- `/api-guide` - Implement REST and GraphQL endpoints
- `/repository-guide`, `/service-guide` - Layer patterns
- `manager/errors/AGENTS.md` - Find and define exceptions
