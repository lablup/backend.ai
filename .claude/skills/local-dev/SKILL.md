---
name: local-dev
description: Local server management — ./dev start/stop/restart via tmux, startup-crash debugging, pre-flight infra checks, raw component start-server commands, post-change restart workflow
tags:
  - dev
  - local
  - services
  - tmux
---

# Local Development — Server Management

Tools for managing Backend.AI services locally via tmux sessions.

## ./dev — Service Management

```bash
./dev status                         # Show all service statuses
./dev restart mgr                    # Restart manager only
./dev restart all                    # Restart all services
./dev stop <service|all>             # Stop service(s)
./dev start <service|all>            # Start service(s)
```

**Services:** `mgr`, `agent`, `storage`, `web`, `proxy-coordinator`, `proxy-worker`

**Logs & metrics:** view runtime logs and metrics through the Grafana MCP — see
`/observability`. Query Loki by `service_name` (e.g. `{service_name="manager"}`) after a
restart rather than reading console output.

## Running components directly (debugging)

`./dev` is the normal way to run services (tmux-managed). To run a component in the foreground — to read startup errors live or check health — use its raw CLI. These are **server-execution** commands (`./backend.ai <component> ...`), distinct from the `./bai` v2 client; the v1-vs-v2 rule in `/bai-cli` does not apply here.

| Component | CLI prefix | Commands | Pre-flight (depends on) |
|-----------|-----------|----------|--------------------------|
| Manager | `./backend.ai mgr` | `health`, `start-server`, `dbschema show` | PostgreSQL, Valkey, etcd, migrations up-to-date (`/db-migrate`), config |
| Agent | `./backend.ai ag` | `health`, `start-server`, `status` | Manager reachable, Docker daemon, GPU drivers (if GPU), config |
| Storage Proxy | `./backend.ai storage` | `health`, `start-server`, `volume list` | Manager reachable, storage backend, config |
| Web Server | `./backend.ai web` | `health`, `start-server` | Manager reachable, built assets, config |
| App Proxy Coordinator | `./backend.ai app-proxy-coordinator` | `health`, `start-server` | PostgreSQL, Valkey, migrations (`/db-migrate` (appproxy)), config |
| App Proxy Worker | `./backend.ai app-proxy-worker` | `health`, `start-server` | Coordinator reachable, Valkey, config |

`start-server` blocks the terminal. Before starting, confirm infra (DB/Valkey/etcd) is up via `/halfstack` and migrations via `/db-migrate`. When a component fails: infra → `/halfstack`, migrations → `/db-migrate`, runtime logs → `/observability`.

## Debugging Startup Crashes

`./dev` runs services in tmux — if a service crashes on startup, the tmux window
closes and logs are lost. To see the actual error, run the service directly:

```bash
# Run manager directly to see startup errors (e.g., import errors, schema issues)
PYTHONPATH=src python -c "from ai.backend.manager.api.gql.schema import schema; print('OK')"

# Or test a specific import chain
PYTHONPATH=src python -c "from ai.backend.manager.api.adapters.registry import Adapters; print('OK')"
```

After fixing, restart with `./dev start mgr`.

## After Code Changes

Server-side code changes (handler, adapter, DTO, model) require a server restart:

```bash
./dev restart mgr        # Most changes only need manager restart
sleep 5                  # Wait for server initialization
```

If DTO changes affect GQL schema, also restart webserver:

```bash
./dev restart mgr
./dev restart web
sleep 5
```

If GQL schema changes affect the federated supergraph (new types, fields, modules),
regenerate and restart the Hive Gateway — see `/halfstack` skill for details:

```bash
./scripts/generate-graphql-schema.sh
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
docker compose -f docker-compose.halfstack.current.yml restart backendai-half-apollo-router
```

## Related Skills

- `/observability` — Inspect logs/metrics via Grafana MCP after a restart
- `/bai-cli` — Verify changes via CLI after restarting services
- `/halfstack` — Docker Compose infrastructure (DB, Valkey, etcd, Hive Gateway)
- `/db-migrate` — Check schema/migration state before starting a component
