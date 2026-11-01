---
name: halfstack
description: Diagnose and fix Docker Compose halfstack issues: config mapping, service health, DB/Valkey/etcd inspection, supergraph regeneration
invoke_method: user
auto_execute: false
enabled: true
tags:
  - dev
  - docker
  - halfstack
  - troubleshooting
---

# Halfstack troubleshooting

Diagnose and fix issues in the Docker Compose halfstack development environment.

## When to use

- Docker Compose services fail to start or keep restarting
- Config files are missing, stale, or have wrong port or secret values
- The supergraph schema needs regeneration after GQL changes
- DB, Valkey or etcd state must be inspected directly
- The halfstack must be started after a fresh clone or branch switch

## Compose file

The runtime compose file is always `docker-compose.halfstack.current.yml` in the project root. It is generated from `docker-compose.halfstack-main.yml`, or from `halfstack-ha.yml` for HA mode.

## Quick reference commands

```bash
# Check all halfstack services
docker compose -f docker-compose.halfstack.current.yml ps

# Check a specific service's logs
docker compose -f docker-compose.halfstack.current.yml logs <service-name>

# Restart a specific service
docker compose -f docker-compose.halfstack.current.yml restart <service-name>

# Start everything
docker compose -f docker-compose.halfstack.current.yml up -d --wait
```

### Service names and profiles

Optional services are gated behind Docker Compose profiles. By default, `docker compose up -d` starts only the **required** services. Pass `--profile <name>` to include optional ones.

| Service | Image | Purpose | Profile |
|---|---|---|---|
| `backendai-half-db` | postgres:16.3-alpine | Main database | required |
| `backendai-half-redis` | valkey/valkey:9.1.1-alpine | Cache and pub-sub | required |
| `backendai-half-etcd` | etcd v3.5 | Config store | required |
| `backendai-half-apollo-router` | Hive Gateway | GraphQL federation; the manager has 2 GQL servers federated through this | required |
| `backendai-half-prometheus` | Prometheus | Metrics; the manager queries it for deployment auto-scaling rule evaluation | required |
| `backendai-half-otel-collector` | OTel Collector | Trace and metric export | `telemetry`, `observability` |
| `backendai-half-loki` | Loki | Log aggregation | `telemetry`, `observability` |
| `backendai-half-grafana` | Grafana | Dashboards | `observability` |
| `backendai-half-grafana-mcp` | mcp/grafana | Grafana MCP server (streamable-http on :3001/mcp); Claude queries logs and metrics through it | `observability` |
| `backendai-half-tempo` | Tempo | Tracing | `observability` |
| `backendai-half-pyroscope` | Pyroscope | Profiling | `observability` |
| `backendai-half-db-exporter` | postgres-exporter | Postgres metrics | `observability` |
| `backendai-half-redis-exporter` | redis_exporter | Valkey metrics | `observability` |
| `backendai-half-minio` | MinIO | Object storage | `storage` |

Profile semantics:

- `telemetry` - service-level export only (`otel-collector` and `loki`). Visualisation (Grafana) and supporting backends (Tempo, Pyroscope, exporters) are typically managed centrally. This profile suits a dev install that only forwards logs and traces.
- `observability` - a superset of `telemetry`. It starts the full local stack, including Grafana, Tempo, Pyroscope and the exporters.
- `storage` - MinIO only.

### Enabling optional profiles

```bash
# Required only (default)
docker compose -f docker-compose.halfstack.current.yml up -d --wait

# + telemetry export (OTel collector + Loki forwarding logs/traces to a central monitor)
docker compose -f docker-compose.halfstack.current.yml --profile telemetry up -d --wait

# + full observability stack (Grafana / Tempo / Pyroscope / exporters in addition to telemetry)
docker compose -f docker-compose.halfstack.current.yml --profile observability up -d --wait

# + object storage (MinIO)
docker compose -f docker-compose.halfstack.current.yml --profile storage up -d --wait

# Everything
docker compose -f docker-compose.halfstack.current.yml --profile observability --profile storage up -d --wait
```

When stopping or removing, pass the profile flags too so those containers are torn down:

```bash
docker compose -f docker-compose.halfstack.current.yml --profile observability --profile storage down
```

`scripts/delete-dev.sh` already passes both profiles, so a clean wipe works regardless of what was enabled.

## Docker configs

The compose file declares a `configs:` section. Docker Compose reads these as **files**. When a file is missing when `docker compose up` runs, Docker creates a **directory** at that path instead. Once a directory exists where a file should be, copying the correct file does not help; the directory must be removed first.

### Fix procedure for missing config files

**Step 1:** Stop the affected services, or all services:

```bash
docker compose -f docker-compose.halfstack.current.yml down
```

**Step 2:** Check for and remove directories that should be files:

```bash
# These must be regular files, not directories
for f in prometheus.yaml otel-collector-config.yaml loki-config.yaml \
         tempo-config.yaml supergraph.graphql gateway.config.ts; do
  [ -d "$f" ] && rm -rf "$f" && echo "Removed directory: $f"
done

# These must be directories
for d in grafana-dashboards grafana-provisioning; do
  [ -f "$d" ] && rm -f "$d" && echo "Removed file: $d"
done
```

**Step 3:** Copy the config files from source, the same way `scripts/install-dev.sh` does:

```bash
# Docker Compose configs (plain copy, no transformation)
cp configs/prometheus/prometheus.yaml ./prometheus.yaml
cp configs/otel/otel-collector-config.yaml ./otel-collector-config.yaml
cp configs/loki/loki-config.yaml ./loki-config.yaml
cp configs/tempo/tempo-config.yaml ./tempo-config.yaml
cp configs/graphql/gateway.config.ts ./gateway.config.ts

# Supergraph: generated, but can be copied from the last known-good version
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql

# Grafana (recursive directory copy)
cp -r configs/grafana/dashboards ./grafana-dashboards
cp -r configs/grafana/provisioning ./grafana-provisioning
```

**Step 4:** Create the volume directories:

```bash
mkdir -p volumes/postgres-data
mkdir -p volumes/etcd-data
mkdir -p volumes/redis-data
```

**Step 5:** Start the services again:

```bash
docker compose -f docker-compose.halfstack.current.yml up -d --wait
```

### Config source mapping

| File in project root | Source path | Used by service |
|---|---|---|
| `prometheus.yaml` | `configs/prometheus/prometheus.yaml` | backendai-half-prometheus |
| `otel-collector-config.yaml` | `configs/otel/otel-collector-config.yaml` | backendai-half-otel-collector |
| `loki-config.yaml` | `configs/loki/loki-config.yaml` | backendai-half-loki |
| `tempo-config.yaml` | `configs/tempo/tempo-config.yaml` | backendai-half-tempo |
| `supergraph.graphql` | `docs/manager/graphql-reference/supergraph.graphql` | backendai-half-apollo-router |
| `gateway.config.ts` | `configs/graphql/gateway.config.ts` | backendai-half-apollo-router |
| `grafana-dashboards/` | `configs/grafana/dashboards/` | backendai-half-grafana (volume mount) |
| `grafana-provisioning/` | `configs/grafana/provisioning/` | backendai-half-grafana (volume mount) |

## Missing or stale compose file

When `docker-compose.halfstack.current.yml` does not exist or is outdated:

```bash
cp docker-compose.halfstack-main.yml docker-compose.halfstack.current.yml
```

Then apply the port substitutions. Read the existing component toml files to determine the current ports, or use the defaults from `scripts/install-dev.sh`:

| Setting | Default | sed pattern |
|---|---|---|
| POSTGRES_PORT | 8101 | `s/8100:5432/${POSTGRES_PORT}:5432/` |
| REDIS_PORT | 8111 | `s/8110:6379/${REDIS_PORT}:6379/` |
| ETCD_PORT | 8121 | `s/8120:2379/${ETCD_PORT}:2379/` |

The source template has 8100, 8110 and 8120, while the `install-dev.sh` defaults are 8101, 8111 and 8121. Check the existing config files first to determine the correct port.

## Supergraph and Hive Gateway

The Hive Gateway serves the federated GraphQL schema. Regenerate it when:

- GQL schema types or fields change
- New GQL modules are added
- The Strawberry schema is modified

```bash
# 1. Generate new schemas and supergraph
./scripts/generate-graphql-schema.sh

# 2. Copy to project root (where compose expects it)
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
cp configs/graphql/gateway.config.ts ./gateway.config.ts

# 3. Recreate the gateway. Docker configs are baked in at container creation,
#    so `restart` keeps serving the old schema.
docker compose -f docker-compose.halfstack.current.yml up -d --force-recreate --wait backendai-half-apollo-router
```

Run steps 1 to 3 in one command: `./scripts/refresh-graphql-gateway.sh --recreate`. Without `--recreate` it only restarts the container, which keeps the old schema.

When manager code is broken and `generate-graphql-schema.sh` fails, copy the last known-good supergraph from git:

```bash
git show main:docs/manager/graphql-reference/supergraph.graphql > ./supergraph.graphql
```

## Direct service inspection

### PostgreSQL

```bash
PGCONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-db)

# Interactive psql
docker exec -it -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d backend

# Non-interactive query
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d backend -c "SELECT version();"

# Check databases
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -tc "SELECT datname FROM pg_database;"

# Check alembic migration version (manager)
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d backend -c "SELECT * FROM alembic_version;"

# Check alembic migration version (appproxy)
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d appproxy -c "SELECT * FROM alembic_version;"

# List tables
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d backend -c "\dt"
```

Common fix for a missing appproxy DB:

```bash
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -c "CREATE DATABASE appproxy;"
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -c "CREATE ROLE appproxy WITH LOGIN PASSWORD 'develove';"
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d appproxy -c "GRANT ALL ON SCHEMA public TO appproxy;"
./py -m alembic -c alembic-appproxy.ini upgrade head
```

### Valkey

```bash
REDIS_CONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis)

# Ping
docker exec $REDIS_CONTAINER valkey-cli ping

# Info
docker exec $REDIS_CONTAINER valkey-cli info server
docker exec $REDIS_CONTAINER valkey-cli dbsize

# List keys (dev only)
docker exec $REDIS_CONTAINER valkey-cli keys '*'

# Get or check a specific key
docker exec $REDIS_CONTAINER valkey-cli get <key>
docker exec $REDIS_CONTAINER valkey-cli type <key>

# Flush all (destructive)
docker exec $REDIS_CONTAINER valkey-cli flushall
```

### etcd

```bash
ETCD_CONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-etcd)

# List all keys
docker exec $ETCD_CONTAINER etcdctl get --prefix "" --keys-only

# Get a specific key
docker exec $ETCD_CONTAINER etcdctl get <key>

# Common key prefixes
docker exec $ETCD_CONTAINER etcdctl get --prefix "config/redis"
docker exec $ETCD_CONTAINER etcdctl get --prefix "volumes"

# Health check
docker exec $ETCD_CONTAINER etcdctl endpoint health
```

Or through the Backend.AI CLI:

```bash
./backend.ai mgr etcd get --prefix ''
./backend.ai mgr etcd get config/redis/addr
./backend.ai mgr etcd put config/redis/addr "127.0.0.1:8111"
```

### MinIO

```bash
MINIO_CONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-minio)

# Health check
docker exec $MINIO_CONTAINER curl -sf http://localhost:9000/minio/health/live

# List buckets (set the alias first)
docker exec $MINIO_CONTAINER mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec $MINIO_CONTAINER mc ls local/

# Web console: http://127.0.0.1:9001 (minioadmin / minioadmin)
```

## Component config files

These config files live in the project root and are generated from `configs/` templates.

| Config file | Source template | Key transformations |
|---|---|---|
| `manager.toml` | `configs/manager/halfstack.toml` | etcd, PG and manager port, ipc-base-path |
| `alembic.ini` | `configs/manager/halfstack.alembic.ini` | PG connection string |
| `account-manager.toml` | `configs/account-manager/halfstack.toml` | etcd, PG and service port, ipc-base-path |
| `alembic-accountmgr.ini` | `configs/account-manager/halfstack.alembic.ini` | PG connection string |
| `agent.toml` | `configs/agent/halfstack.toml` | etcd, RPC and watcher port, ipc, var and mount paths, accelerator plugins |
| `storage-proxy.toml` | `configs/storage-proxy/halfstack.toml` | etcd port, 2 secrets, volume config, MinIO credentials |
| `app-proxy-coordinator.toml` | `configs/app-proxy-coordinator/halfstack.toml` | PG and Valkey port, service port, 3 generated secrets |
| `alembic-appproxy.ini` | `configs/app-proxy-coordinator/halfstack.alembic.ini` | PG connection string |
| `app-proxy-worker.toml` | `configs/app-proxy-worker/halfstack.toml` | Valkey port, service port, **the same 3 secrets as the app proxy coordinator** |
| `webserver.conf` | `configs/webserver/halfstack.conf` | Manager endpoint URL, Valkey address |

### Cross-config consistency rules

- The **PG port** in compose matches `manager.toml`, `alembic.ini`, `account-manager.toml`, `app-proxy-coordinator.toml` and `alembic-appproxy.ini`
- The **Valkey port** in compose matches `app-proxy-coordinator.toml`, `app-proxy-worker.toml` and `webserver.conf`
- The **etcd port** in compose matches `manager.toml`, `agent.toml` and `storage-proxy.toml`
- **App proxy secrets** - `app-proxy-coordinator.toml` and `app-proxy-worker.toml` share identical `api_secret`, `jwt_secret` and `permit_hash.secret`
- **Manager and storage proxy** - the volume auth secret in etcd, set via `dev.etcd.volumes.json`, matches `[api.manager] secret` in `storage-proxy.toml`

### Regenerating a component config

When regenerating, read the existing secret values from the current config file and reuse them. Generate new secrets (`python -c 'import secrets; print(secrets.token_urlsafe(32))'`) only when the config file does not exist at all.

See `scripts/install-dev.sh` around lines 1016 to 1142 for the exact sed substitution patterns per component.

## Diagnostic workflow

When halfstack issues are reported, follow this order:

1. **Check the compose file:** `ls -la docker-compose.halfstack.current.yml`
2. **Check service status:** `docker compose -f docker-compose.halfstack.current.yml ps`
3. **For exited or unhealthy services:** read the logs with `docker compose ... logs <service>`
4. **For config-dependent services** (prometheus, otel, loki, tempo, gateway):
   - Verify the referenced files exist in the project root **and are files, not directories**
   - When a directory exists where a file should be: stop the service → `rm -rf <dir>` → copy the correct file → restart
5. **For Backend.AI components** (manager, agent and so on): verify the `.toml` or `.conf` exists and the ports match compose
6. **For DB issues:** connect to PostgreSQL directly and check the schema and data
7. **For Valkey or etcd issues:** connect directly and inspect the state
8. **Fix the root cause directly** instead of only reporting the problem.
