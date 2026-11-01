---
name: local-dev
description: Local server management: ./dev start/stop/restart via tmux, startup-crash debugging, pre-flight infra checks, raw component start-server commands, post-change restart workflow
tags:
  - dev
  - local
  - services
  - tmux
---

# Local development: server management

Tools for managing Backend.AI services locally through tmux sessions.

## ./dev

```bash
./dev status                         # Show all service statuses
./dev restart mgr                    # Restart manager only
./dev restart all                    # Restart all services
./dev stop <service|all>             # Stop service(s)
./dev start <service|all>            # Start service(s)
```

**Services:** `mgr`, `agent`, `storage`, `web`, `proxy-coordinator`, `proxy-worker`

View runtime logs and metrics through the Grafana MCP. See `/observability`. Query Loki by `service_name` (for example `{service_name="manager"}`) after a restart instead of reading console output.

## Running components directly

`./dev` is the normal way to run services. To run a component in the foreground, to read startup errors live or check health, use its raw CLI. These are server-execution commands (`./backend.ai <component> ...`), distinct from the `./bai` v2 client. The rule in `/bai-cli` that distinguishes the v1 CLI and `./bai` does not apply here.

| Component | CLI prefix | Commands | Pre-flight (depends on) |
|---|---|---|---|
| Manager | `./backend.ai mgr` | `health`, `start-server`, `dbschema show` | PostgreSQL, Valkey, etcd, migrations up to date (`/db-migrate`), config |
| Agent | `./backend.ai ag` | `health`, `start-server`, `status` | Manager reachable, Docker daemon, GPU drivers (if GPU), config |
| Storage proxy | `./backend.ai storage` | `health`, `start-server`, `volume list` | Manager reachable, storage backend, config |
| Webserver | `./backend.ai web` | `health`, `start-server` | Manager reachable, built assets, config |
| App proxy coordinator | `./backend.ai app-proxy-coordinator` | `health`, `start-server` | PostgreSQL, Valkey, migrations (`/db-migrate` (appproxy)), config |
| App proxy worker | `./backend.ai app-proxy-worker` | `health`, `start-server` | Coordinator reachable, Valkey, config |

`start-server` blocks the terminal. Before starting, confirm the infrastructure (DB, Valkey, etcd) is up via `/halfstack` and migrations via `/db-migrate`. When a component fails, check the infrastructure with `/halfstack`, migrations with `/db-migrate`, and runtime logs with `/observability`.

## Debugging startup crashes

`./dev` runs services in tmux. When a service crashes on startup, the tmux window closes and the logs are lost. Run the service directly to see the actual error:

```bash
# Run manager directly to see startup errors (for example import errors, schema issues)
PYTHONPATH=src python -c "from ai.backend.manager.api.gql.schema import schema; print('OK')"

# Or test a specific import chain
PYTHONPATH=src python -c "from ai.backend.manager.api.adapters.registry import Adapters; print('OK')"
```

After fixing, restart with `./dev start mgr`.

## After code changes

Server-side code changes (handler, adapter, DTO, model) require a server restart:

```bash
./dev restart mgr        # Most changes only need manager restart
sleep 5                  # Wait for server initialization
```

When DTO changes affect the GQL schema, restart the webserver too:

```bash
./dev restart mgr
./dev restart web
sleep 5
```

When GQL schema changes affect the federated supergraph (new types, fields, modules), regenerate it and recreate the Hive Gateway. See `/halfstack`:

```bash
./scripts/generate-graphql-schema.sh
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
docker compose -f docker-compose.halfstack.current.yml up -d --force-recreate --wait backendai-half-apollo-router
```

## Related documents

- `/observability` - Inspect logs and metrics via the Grafana MCP after a restart
- `/bai-cli` - Verify changes via the CLI after restarting services
- `/halfstack` - Docker Compose infrastructure (DB, Valkey, etcd, Hive Gateway)
- `/db-migrate` - Check schema and migration state before starting a component
