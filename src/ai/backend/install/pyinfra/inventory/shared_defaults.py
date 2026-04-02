"""
Shared default constants for Backend.AI installer.

These defaults are used by both:
- DevContext (TUI dev mode installer)
- DevInventoryBuilder (pyinfra local deployment)

Centralizing here avoids duplicating magic numbers across the two systems.
"""

from __future__ import annotations

# -- Halfstack service ports (Docker Compose defaults)
HALFSTACK_PORTS = {
    "postgres": 8100,
    "redis": 8110,
    "etcd": 8120,
}

# -- Core service ports
CORE_PORTS = {
    "manager": 8091,
    "webserver": 8090,
    "storage_proxy_client": 6021,
    "storage_proxy_manager": 6022,
    "agent_rpc": 6011,
    "agent_watcher": 6019,
    "storage_agent_rpc": 6012,
    "storage_watcher": 6029,
    "local_proxy": 5050,
}

# -- AppProxy ports
APPPROXY_COORDINATOR_PORT = 10200
APPPROXY_WORKER_INTERACTIVE_PORT = 10201
APPPROXY_WORKER_INTERACTIVE_RANGE = (10205, 10300)
APPPROXY_WORKER_TCP_PORT = 10202
APPPROXY_WORKER_TCP_RANGE = (10501, 10600)
APPPROXY_WORKER_INFERENCE_PORT = 10203
APPPROXY_WORKER_INFERENCE_RANGE = (10601, 10700)
APPPROXY_TRAEFIK_API_PORT = 18080

# -- Monitoring ports
MONITORING_PORTS = {
    "prometheus": 19090,
    "grafana": 3000,
    "loki": 3100,
    "pyroscope": 4040,
    "otel_grpc": 4317,
    "otel_http": 4318,
}

# -- Other service ports
OTHER_PORTS = {
    "hive_gateway": 4000,
}

# -- Default component versions
DEFAULT_VERSIONS = {
    # Halfstack
    "postgres_ha": "15.12-timescaledb",
    "postgres_etcd": "v3.5.21",
    "redis": "7.2",
    "haproxy": "2.9",
    "etcd": "v3.5.21",
    "etcd_grpc": "v3.5.21",
    "hive_gateway": "2.1.12",
    "apollo_router": "v1.61.9",
    # Monitoring
    "prometheus": "v3.1.0",
    "redis_exporter": "v1.73.0",
    "postgres_exporter": "v0.17.1",
    "blackbox_exporter": "v0.25.0",
    "dcgm_exporter": "3.3.0-3.2.0-ubuntu22.04",
    "grafana": "12.2.1",
    "loki": "3.5.0",
    "pyroscope": "1.9.2",
    "otel": "0.126.0",
    # AppProxy
    "traefik": "v3.3.7",
    "traefik_plugin": "0.0.5",
}

# -- Dev environment defaults
DEV_DEFAULTS = {
    "postgres_user": "postgres",
    "postgres_password": "develove",
    "appproxy_db_user": "appproxy",
    "appproxy_db_password": "develove",
    "superadmin_password": "wJalrXUt",
    "superadmin_access_key": "AKIAIOSFODNN7EXAMPLE",
    "superadmin_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "user_password": "test",
    "user_access_key": "AKIANABBDUSEREXAMPLE",
    "user_secret_key": "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",
}
