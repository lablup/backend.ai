# Local Development — Server Management

Tools for managing Backend.AI services locally via tmux sessions.

## ./dev — Service Management

```bash
./dev status                         # Show all service statuses
./dev restart mgr                    # Restart manager only
./dev restart all                    # Restart all services
./dev stop <service|all>             # Stop service(s)
./dev start <service|all>            # Start service(s)
./dev log <service>                  # Show recent log output
```

**Services:** `mgr`, `agent`, `storage`, `web`, `proxy-coordinator`, `proxy-worker`

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

- `/bai-cli` — Verify changes via CLI after restarting services
- `/halfstack` — Docker Compose infrastructure (DB, Redis, etcd, Hive Gateway)
- `/cli-executor` — Run Backend.AI component servers directly
