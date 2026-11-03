# 데이터 모델 상세

> 상위 문서: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## DB 테이블

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

## 역할 정의

엔드포인트가 무엇을 위한 것인지 나타낸다. 역할을 지나치게 세분화하지 않고, 접근 맥락 구분은 scope 가 맡는다.

| 역할 | 설명 | 사용 예시 |
|------|-------------|----------------|
| `api` | 주 API (REST/GraphQL/control) | Manager, Storage Proxy, App Proxy Coordinator |
| `rpc` | ZMQ RPC | Agent |
| `metrics` | Prometheus 지표 수집 | 모든 컴포넌트 |
| `client-api` | 외부 client 용 API | Storage Proxy (file upload/download) |
| `internal-api` | 컴포넌트 간 내부 통신 API | Storage Proxy (container → storage) |

## scope 정의

접근이 어디서 시작되는지 나타낸다. localhost 접근은 `cluster` 에 포함한다.

| scope | 설명 | 주소 예시 |
|-------|-------------|-----------------|
| `cluster` | cluster 내부 접근 (같은 host 포함) | `localhost`, 사설 IP, 내부 DNS |
| `container` | container 에서 host 로의 접근 | `host.docker.internal` |
| `public` | 외부에 노출된 주소 (LB/NAT 뒤) | 공인 IP, domain |

## 유일 키

`(service_id, role, scope)`: service catalog row 하나에 같은 역할과 network scope 를 가진 엔드포인트는 하나만 존재한다.
