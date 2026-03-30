"""Artifact URL builder for Backend.AI package repository.

Pure-Python module with no pyinfra dependency — safe to import anywhere.
This is the single source of truth for artifact URL templates consumed by
``inventory_base.py``, the ``verify_packages`` manifest, and any future
modules that need artifact URLs.
"""

from __future__ import annotations

REQUIRED_VERSION_KEYS = frozenset({
    "postgres_ha",
    "postgres_etcd",
    "redis",
    "haproxy",
    "etcd",
    "etcd_grpc",
    "harbor",
    "control_panel",
    "fasttrack",
    "traefik",
    "traefik_plugin",
    "grafana",
    "prometheus",
    "loki",
    "pyroscope",
    "otel",
    "redis_exporter",
    "postgres_exporter",
    "blackbox_exporter",
    "dcgm_exporter",
    "hive_gateway",
    "apollo_router",
})


def build_artifact_urls(
    repo_url: str,
    versions: dict[str, str],
) -> dict[str, str]:
    """Build full artifact URLs from repo_url and version dict.

    Returns a dict mapping artifact_key -> full URL.

    Raises ``ValueError`` if *versions* is missing any required key.
    Note: the ``otel`` version key maps to the ``otel_collector`` artifact.
    """
    missing = REQUIRED_VERSION_KEYS - versions.keys()
    if missing:
        raise ValueError(
            f"build_artifact_urls(): missing required version keys: {sorted(missing)}. "
            f"Provided keys: {sorted(versions.keys())}"
        )
    v = versions
    return {
        "postgres_ha": f"{repo_url}/halfstack/cr.backend.ai_halfstack_postgres_ha_{v['postgres_ha']}.tar.gz",
        "postgres_etcd": f"{repo_url}/halfstack/quay.io_coreos_etcd_{v['postgres_etcd']}.tar.gz",
        "redis": f"{repo_url}/halfstack/redis_{v['redis']}-alpine.tar.gz",
        "haproxy": f"{repo_url}/halfstack/haproxy_{v['haproxy']}-alpine.tar.gz",
        "etcd": f"{repo_url}/halfstack/quay.io_coreos_etcd_{v['etcd']}.tar.gz",
        "etcd_grpc": f"{repo_url}/halfstack/quay.io_coreos_etcd_{v['etcd_grpc']}.tar.gz",
        "harbor": f"{repo_url}/pro/harbor-offline-installer-{v['harbor']}.tgz",
        "control_panel": f"{repo_url}/pro/control-panel-prod-{v['control_panel']}.zip",
        "fasttrack": f"{repo_url}/pro/backend.ai-fasttrack-{v['fasttrack']}-linux-amd64.release.tar.gz",
        "traefik": f"{repo_url}/appproxy/traefik_{v['traefik']}_linux_amd64.tar.gz",
        "traefik_plugin": f"{repo_url}/appproxy/appproxy-traefik-plugin-{v['traefik_plugin']}.tar.gz",
        "rtun": f"{repo_url}/rtun/rtun-linux-amd64",
        "license_json": f"{repo_url}/license/license.json",
        "license_hwtool": f"{repo_url}/license/hwtool.linux.amd64.bin",
        "license_binary": f"{repo_url}/license/licensed.linux.amd64.bin",
        "grafana": f"{repo_url}/dashboard/grafana_grafana-enterprise_{v['grafana']}.tar.gz",
        "prometheus": f"{repo_url}/dashboard/prom_prometheus_{v['prometheus']}.tar.gz",
        "loki": f"{repo_url}/dashboard/grafana_loki_{v['loki']}.tar.gz",
        "pyroscope": f"{repo_url}/dashboard/grafana_pyroscope_{v['pyroscope']}.tar.gz",
        "otel_collector": f"{repo_url}/dashboard/otel_opentelemetry-collector-contrib_{v['otel']}.tar.gz",
        "redis_exporter": f"{repo_url}/dashboard/oliver006_redis_exporter_{v['redis_exporter']}.tar.gz",
        "postgres_exporter": f"{repo_url}/dashboard/prometheuscommunity_postgres-exporter_{v['postgres_exporter']}.tar.gz",
        "blackbox_exporter": f"{repo_url}/dashboard/prom_blackbox-exporter_{v['blackbox_exporter']}.tar.gz",
        "dcgm_exporter": f"{repo_url}/dashboard/nvcr.io_nvidia_k8s_dcgm-exporter_{v['dcgm_exporter']}.tar.gz",
        "hive_gateway": f"{repo_url}/halfstack/ghcr.io_graphql-hive_gateway_{v['hive_gateway']}.tar.gz",
        "apollo_router": f"{repo_url}/halfstack/ghcr.io_apollographql_router_{v['apollo_router']}.tar.gz",
    }
