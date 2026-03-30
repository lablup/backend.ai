"""Artifact manifest for offline package verification.

Pure-Python module with no pyinfra dependency — safe to import in tests.
URL templates are defined in ``ai.backend.pyinfra.artifact_urls`` (single
source of truth) and re-exported here for convenience.
"""

from __future__ import annotations

from ai.backend.install.pyinfra.artifact_urls import build_artifact_urls

# Maps each artifact key to the service placement key that gates it.
# ``None`` means the artifact is always required.
ARTIFACT_SERVICE_MAP: dict[str, str | None] = {
    "postgres_ha": "halfstack",
    "postgres_etcd": "halfstack",
    "redis": "halfstack",
    "haproxy": "halfstack",
    "etcd": "halfstack",
    "etcd_grpc": "halfstack",
    "hive_gateway": "hive_gateway",
    "apollo_router": "hive_gateway",
    "harbor": "harbor",
    "control_panel": "control_panel",
    "fasttrack": "fasttrack",
    "traefik": "appproxy",
    "traefik_plugin": "appproxy",
    "rtun": None,
    "license_json": "license_server",
    "license_hwtool": "license_server",
    "license_binary": "license_server",
    "grafana": "grafana",
    "prometheus": "prometheus",
    "redis_exporter": "prometheus",
    "postgres_exporter": "prometheus",
    "blackbox_exporter": "prometheus",
    "dcgm_exporter": "prometheus",
    "loki": "loki",
    "pyroscope": "pyroscope",
    "otel_collector": "otel_collector",
}

# Display categories for grouped output.
ARTIFACT_CATEGORIES: dict[str, list[str]] = {
    "Halfstack": [
        "postgres_ha",
        "postgres_etcd",
        "redis",
        "haproxy",
        "etcd",
        "etcd_grpc",
        "hive_gateway",
        "apollo_router",
    ],
    "Core": ["rtun", "license_json", "license_hwtool", "license_binary"],
    "Pro": ["harbor", "control_panel", "fasttrack"],
    "App Proxy": ["traefik", "traefik_plugin"],
    "Monitoring": [
        "prometheus",
        "redis_exporter",
        "postgres_exporter",
        "blackbox_exporter",
        "dcgm_exporter",
        "grafana",
        "loki",
        "pyroscope",
        "otel_collector",
    ],
}

__all__ = [
    "ARTIFACT_CATEGORIES",
    "ARTIFACT_SERVICE_MAP",
    "build_artifact_urls",
    "filter_artifacts_by_placement",
]


def filter_artifacts_by_placement(
    service_placement: dict[str, list[str]],
) -> list[str]:
    """Return artifact keys whose service is placed (or always-checked).

    An artifact is included when:
    - Its ``service_key`` is ``None`` (always required), **or**
    - ``service_key`` exists in *service_placement* and is non-empty.
    """
    result: list[str] = []
    for artifact_key, service_key in ARTIFACT_SERVICE_MAP.items():
        if service_key is None or service_placement.get(service_key):
            result.append(artifact_key)
    return result
