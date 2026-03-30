---
name: halfstack
description: Diagnose and fix Docker Compose halfstack issues — config mapping, service health, DB/Redis/etcd inspection, supergraph regeneration
invoke_method: user
auto_execute: false
enabled: true
tags:
  - dev
  - docker
  - halfstack
  - troubleshooting
---

# Halfstack Troubleshooting & Fix

Diagnose and directly fix issues with the Docker Compose halfstack development environment.

## When to Use

- Docker Compose services fail to start or keep restarting
- Config files are missing, stale, or have wrong port/secret values
- Supergraph schema needs regeneration after GQL changes
- Need to inspect DB, Redis, or etcd state directly
- Halfstack needs to be brought up after a fresh clone or branch switch

## Compose File

The runtime compose file is always `docker-compose.halfstack.current.yml` (project root).
It is generated from `docker-compose.halfstack-main.yml` (or `halfstack-ha.yml` for HA mode).

## Quick Reference Commands

```bash
# Check all halfstack services
docker compose -f docker-compose.halfstack.current.yml ps

# Check a specific service's logs
docker compose -f docker-compose.halfstack.current.yml logs <service-name>

# Restart a specific service
docker compose -f docker-compose.halfstack.current.yml restart <service-name>

# Bring everything up
docker compose -f docker-compose.halfstack.current.yml up -d --wait
```

### Service Names

| Service | Image | Purpose |
|---------|-------|---------|
| `backendai-half-db` | postgres:16.3-alpine | Main database |
| `backendai-half-redis` | redis:7.2-alpine | Cache / pub-sub |
| `backendai-half-etcd` | etcd v3.5 | Config store |
| `backendai-half-minio` | MinIO | Object storage |
| `backendai-half-prometheus` | Prometheus | Metrics |
| `backendai-half-otel-collector` | OTel Collector | Telemetry |
| `backendai-half-loki` | Loki | Log aggregation |
| `backendai-half-tempo` | Tempo | Tracing |
| `backendai-half-grafana` | Grafana | Dashboards |
| `backendai-half-pyroscope` | Pyroscope | Profiling |
| `backendai-half-apollo-router` | Hive Gateway | GraphQL federation |

## Docker Configs — Files That Must Exist in Project Root

The compose file declares a `configs:` section. Docker Compose reads these as **files**.
If a file is missing when `docker compose up` runs, Docker creates a **directory** at that path instead.
Once a directory exists where a file should be, even copying the correct file won't help — the directory must be removed first.

### Fix Procedure for Missing Config Files

**Step 1:** Stop affected services (or all services):

```bash
docker compose -f docker-compose.halfstack.current.yml down
```

**Step 2:** Check and remove any directories that should be files:

```bash
# These MUST be regular files, not directories
for f in prometheus.yaml otel-collector-config.yaml loki-config.yaml \
         tempo-config.yaml supergraph.graphql gateway.config.ts; do
  [ -d "$f" ] && rm -rf "$f" && echo "Removed directory: $f"
done

# These MUST be directories
for d in grafana-dashboards grafana-provisioning; do
  [ -f "$d" ] && rm -f "$d" && echo "Removed file: $d"
done
```

**Step 3:** Copy config files from source (same as `scripts/install-dev.sh`):

```bash
# Docker Compose configs (plain copy, no transformation)
cp configs/prometheus/prometheus.yaml ./prometheus.yaml
cp configs/otel/otel-collector-config.yaml ./otel-collector-config.yaml
cp configs/loki/loki-config.yaml ./loki-config.yaml
cp configs/tempo/tempo-config.yaml ./tempo-config.yaml
cp configs/graphql/gateway.config.ts ./gateway.config.ts

# Supergraph — generated, but can be copied from last known-good
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql

# Grafana (recursive directory copy)
cp -r configs/grafana/dashboards ./grafana-dashboards
cp -r configs/grafana/provisioning ./grafana-provisioning
```

**Step 4:** Ensure volume directories exist:

```bash
mkdir -p volumes/postgres-data
mkdir -p volumes/etcd-data
mkdir -p volumes/redis-data
```

**Step 5:** Bring services back up:

```bash
docker compose -f docker-compose.halfstack.current.yml up -d --wait
```

### Config Source Mapping Reference

| File in project root | Source path | Used by service |
|---------------------|------------|-----------------|
| `prometheus.yaml` | `configs/prometheus/prometheus.yaml` | backendai-half-prometheus |
| `otel-collector-config.yaml` | `configs/otel/otel-collector-config.yaml` | backendai-half-otel-collector |
| `loki-config.yaml` | `configs/loki/loki-config.yaml` | backendai-half-loki |
| `tempo-config.yaml` | `configs/tempo/tempo-config.yaml` | backendai-half-tempo |
| `supergraph.graphql` | `docs/manager/graphql-reference/supergraph.graphql` | backendai-half-apollo-router |
| `gateway.config.ts` | `configs/graphql/gateway.config.ts` | backendai-half-apollo-router |
| `grafana-dashboards/` | `configs/grafana/dashboards/` | backendai-half-grafana (volume mount) |
| `grafana-provisioning/` | `configs/grafana/provisioning/` | backendai-half-grafana (volume mount) |

## Missing or Stale Compose File

If `docker-compose.halfstack.current.yml` doesn't exist or is outdated:

```bash
cp docker-compose.halfstack-main.yml docker-compose.halfstack.current.yml
```

Then apply port substitutions. Read existing component toml files to determine current ports,
or use defaults from `scripts/install-dev.sh`:

| Setting | Default | sed pattern |
|---------|---------|-------------|
| POSTGRES_PORT | 8101 | `s/8100:5432/${POSTGRES_PORT}:5432/` |
| REDIS_PORT | 8111 | `s/8110:6379/${REDIS_PORT}:6379/` |
| ETCD_PORT | 8121 | `s/8120:2379/${ETCD_PORT}:2379/` |

**Note:** The source template has 8100/8110/8120 but `install-dev.sh` defaults are 8101/8111/8121.
Always check existing config files first to determine the correct port.

## Supergraph / Hive Gateway

The Hive Gateway serves the federated GraphQL schema. Regenerate when:
- GQL schema types or fields change
- New GQL modules are added
- v2 schema is modified

```bash
# 1. Generate new schemas and supergraph
./scripts/generate-graphql-schema.sh

# 2. Copy to project root (where compose expects it)
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
cp configs/graphql/gateway.config.ts ./gateway.config.ts

# 3. Restart the gateway
docker compose -f docker-compose.halfstack.current.yml restart backendai-half-apollo-router
```

If manager code is broken and `generate-graphql-schema.sh` fails,
copy the last known-good supergraph from git:

```bash
git show main:docs/manager/graphql-reference/supergraph.graphql > ./supergraph.graphql
```

## Direct Service Inspection

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

**Common fix — appproxy DB missing:**

```bash
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -c "CREATE DATABASE appproxy;"
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -c "CREATE ROLE appproxy WITH LOGIN PASSWORD 'develove';"
docker exec -e PGPASSWORD=develove $PGCONTAINER psql -U postgres -d appproxy -c "GRANT ALL ON SCHEMA public TO appproxy;"
./py -m alembic -c alembic-appproxy.ini upgrade head
```

### Redis

```bash
REDIS_CONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis)

# Ping
docker exec $REDIS_CONTAINER redis-cli ping

# Info
docker exec $REDIS_CONTAINER redis-cli info server
docker exec $REDIS_CONTAINER redis-cli dbsize

# List keys (dev only)
docker exec $REDIS_CONTAINER redis-cli keys '*'

# Get/check specific key
docker exec $REDIS_CONTAINER redis-cli get <key>
docker exec $REDIS_CONTAINER redis-cli type <key>

# Flush all (destructive)
docker exec $REDIS_CONTAINER redis-cli flushall
```

### etcd

```bash
ETCD_CONTAINER=$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-etcd)

# List all keys
docker exec $ETCD_CONTAINER etcdctl get --prefix "" --keys-only

# Get specific key
docker exec $ETCD_CONTAINER etcdctl get <key>

# Common key prefixes
docker exec $ETCD_CONTAINER etcdctl get --prefix "config/redis"
docker exec $ETCD_CONTAINER etcdctl get --prefix "volumes"

# Health check
docker exec $ETCD_CONTAINER etcdctl endpoint health
```

Or via Backend.AI CLI:

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

# List buckets (set alias first)
docker exec $MINIO_CONTAINER mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec $MINIO_CONTAINER mc ls local/

# Web console: http://127.0.0.1:9001 (minioadmin / minioadmin)
```

## Component Config Files — Port/Secret Consistency

These config files live in the project root and are generated from `configs/` templates.

| Config file | Source template | Key transformations |
|-------------|----------------|---------------------|
| `manager.toml` | `configs/manager/halfstack.toml` | etcd/PG/manager port, ipc-base-path |
| `alembic.ini` | `configs/manager/halfstack.alembic.ini` | PG connection string |
| `account-manager.toml` | `configs/account-manager/halfstack.toml` | etcd/PG/service port, ipc-base-path |
| `alembic-accountmgr.ini` | `configs/account-manager/halfstack.alembic.ini` | PG connection string |
| `agent.toml` | `configs/agent/halfstack.toml` | etcd/RPC/watcher port, ipc/var/mount paths, accelerator plugins |
| `storage-proxy.toml` | `configs/storage-proxy/halfstack.toml` | etcd port, 2 secrets, volume config, MinIO creds |
| `app-proxy-coordinator.toml` | `configs/app-proxy-coordinator/halfstack.toml` | PG/Redis port, service port, 3 generated secrets |
| `alembic-appproxy.ini` | `configs/app-proxy-coordinator/halfstack.alembic.ini` | PG connection string |
| `app-proxy-worker.toml` | `configs/app-proxy-worker/halfstack.toml` | Redis port, service port, **same 3 secrets as coordinator** |
| `webserver.conf` | `configs/webserver/halfstack.conf` | Manager endpoint URL, Redis addr |

### Cross-Config Consistency Rules

- **PG port** in compose must match `manager.toml`, `alembic.ini`, `account-manager.toml`, `app-proxy-coordinator.toml`, `alembic-appproxy.ini`
- **Redis port** in compose must match `app-proxy-coordinator.toml`, `app-proxy-worker.toml`, `webserver.conf`
- **etcd port** in compose must match `manager.toml`, `agent.toml`, `storage-proxy.toml`
- **App Proxy secrets**: `app-proxy-coordinator.toml` and `app-proxy-worker.toml` must share identical `api_secret`, `jwt_secret`, `permit_hash.secret`
- **Manager ↔ Storage Proxy**: the volume auth secret in etcd (set via `dev.etcd.volumes.json`) must match `storage-proxy.toml`'s `[api.manager] secret`

### Regenerating a Component Config

When regenerating, **read existing secret values** from the current config file and reuse them.
Only generate new secrets (`python -c 'import secrets; print(secrets.token_urlsafe(32))'`) when the config file doesn't exist at all.

Reference `scripts/install-dev.sh` lines 1016–1142 for the exact sed substitution patterns per component.

## Diagnostic Workflow

When halfstack issues are reported, follow this order:

1. **Check compose file exists:** `ls -la docker-compose.halfstack.current.yml`
2. **Check service status:** `docker compose -f docker-compose.halfstack.current.yml ps`
3. **For exited/unhealthy services:** read logs with `docker compose ... logs <service>`
4. **For config-dependent services** (prometheus, otel, loki, tempo, gateway):
   - Verify referenced files exist in project root **and are files, not directories**
   - If a directory exists where a file should be: stop service → `rm -rf <dir>` → copy correct file → restart
5. **For Backend.AI components** (manager, agent, etc.): verify `.toml`/`.conf` exists and ports match compose
6. **For DB issues:** connect to PostgreSQL directly and check schema/data
7. **For Redis/etcd issues:** connect directly and inspect state
8. **Fix the root cause directly** — don't just report the problem.
