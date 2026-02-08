# Data Model Details

> Parent document: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## DB Tables

```sql
-- Service catalog (1 service = 1 row)
CREATE TABLE service_catalog (
    -- Registration ID: internal DB PK, auto-generated
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business identity: upsert by (service_group, instance_id)
    service_group   VARCHAR NOT NULL,       -- "agent", "manager", "storage-proxy", ...
    instance_id     VARCHAR NOT NULL,       -- specified in config or auto-generated

    display_name    VARCHAR NOT NULL,
    version         VARCHAR NOT NULL,
    labels          JSONB NOT NULL DEFAULT '{}',
    status          VARCHAR NOT NULL,       -- HEALTHY, UNHEALTHY, DEREGISTERED
    startup_time    TIMESTAMPTZ NOT NULL,
    registered_at   TIMESTAMPTZ NOT NULL,
    last_heartbeat  TIMESTAMPTZ NOT NULL,
    config_hash     VARCHAR NOT NULL DEFAULT '',

    UNIQUE (service_group, instance_id)
);

CREATE INDEX ix_service_catalog_group ON service_catalog (service_group);
CREATE INDEX ix_service_catalog_status ON service_catalog (status);

-- Service endpoints (N per service)
CREATE TABLE service_catalog_endpoint (
    id          UUID PRIMARY KEY,
    service_id  UUID NOT NULL REFERENCES service_catalog(id) ON DELETE CASCADE,
    role        VARCHAR NOT NULL,           -- "api", "rpc", "metrics", "client-api", "internal-api"
    scope       VARCHAR NOT NULL,           -- "cluster", "container", "public"
    address     VARCHAR NOT NULL,
    port        INTEGER NOT NULL,
    protocol    VARCHAR NOT NULL,           -- "http", "zmq", "rpc", "ws", "grpc"
    metadata    JSONB NOT NULL DEFAULT '{}',
    UNIQUE (service_id, role, scope)
);
```

## Role Definition

Indicates "what the endpoint is for." Roles are not over-segmented; access context distinction is handled by scope.

| Role | Description | Usage Examples |
|------|-------------|----------------|
| `api` | Main API (REST/GraphQL/control) | Manager, Storage Proxy, AppProxy Coordinator |
| `rpc` | ZMQ RPC | Agent |
| `metrics` | Prometheus metrics collection | All components |
| `client-api` | External client-facing API | Storage Proxy (file upload/download) |
| `internal-api` | Internal inter-service communication API | Storage Proxy (container → storage) |

## Scope Definition

Indicates "where the access originates from." localhost access is included in `cluster`.

| Scope | Description | Address Examples |
|-------|-------------|-----------------|
| `cluster` | Intra-cluster access (including same host) | `localhost`, private IP, internal DNS |
| `container` | Container-to-host access | `host.docker.internal` |
| `public` | Externally exposed address (behind LB/NAT) | public IP, domain |

## Unique Key

`(service_id, role, scope)` — Only one endpoint with the same role and network scope can exist per service.
