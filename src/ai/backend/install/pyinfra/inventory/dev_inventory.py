"""
Development inventory builder for local pyinfra deployments.

Creates an inventory targeting @local that works with the existing
Docker Compose halfstack used by the dev installer (DevContext).

Usage:
    builder = DevInventoryBuilder()
    locals().update(builder.build())
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from ai.backend.install.pyinfra.configs.cores import (
    AgentConfig,
    AppProxyConfig,
    BackendAICoreConfig,
    ControlPanelConfig,
    LicenseServerConfig,
    ManagerConfig,
    StorageProxyConfig,
    WebserverConfig,
)
from ai.backend.install.pyinfra.configs.dashboard import (
    GrafanaConfig,
    LokiConfig,
    OTELCollectorConfig,
    PrometheusConfig,
    PyroscopeConfig,
)
from ai.backend.install.pyinfra.configs.halfstack import (
    EtcdConfig,
    HiveGatewayConfig,
    PostgreSQLConfig,
    RedisConfig,
)
from ai.backend.install.pyinfra.configs.pro import FastTrackConfig
from ai.backend.install.pyinfra.inventory.shared_defaults import (
    APPPROXY_COORDINATOR_PORT,
    APPPROXY_WORKER_INTERACTIVE_PORT,
    APPPROXY_WORKER_INTERACTIVE_RANGE,
    APPPROXY_WORKER_TCP_PORT,
    APPPROXY_WORKER_TCP_RANGE,
    CORE_PORTS,
    DEFAULT_VERSIONS,
    DEV_DEFAULTS,
    HALFSTACK_PORTS,
    MONITORING_PORTS,
    OTHER_PORTS,
)


class DevInventoryBuilder:
    """
    Build pyinfra inventory for local development environment.

    Uses @local connector (no SSH) and Docker Compose halfstack ports.
    Matches the configuration from DevContext.hydrate_install_info().
    """

    PORTS: dict[str, int] = {
        **HALFSTACK_PORTS,
        **CORE_PORTS,
        "appproxy_coordinator": APPPROXY_COORDINATOR_PORT,
        "appproxy_worker_interactive": APPPROXY_WORKER_INTERACTIVE_PORT,
        "appproxy_worker_interactive_start": APPPROXY_WORKER_INTERACTIVE_RANGE[0],
        "appproxy_worker_interactive_end": APPPROXY_WORKER_INTERACTIVE_RANGE[1],
        "appproxy_worker_tcp": APPPROXY_WORKER_TCP_PORT,
        "appproxy_worker_tcp_start": APPPROXY_WORKER_TCP_RANGE[0],
        "appproxy_worker_tcp_end": APPPROXY_WORKER_TCP_RANGE[1],
        **MONITORING_PORTS,
        **OTHER_PORTS,
    }

    def __init__(
        self,
        *,
        public_facing_address: str = "127.0.0.1",
        home_dir: str | None = None,
        bai_version: str = "26.3.0",
    ) -> None:
        self.host = public_facing_address
        self.home_dir = home_dir or str(Path.cwd())
        self.bai_version = bai_version
        self.api_secret = secrets.token_hex(32)
        self.jwt_secret = secrets.token_hex(32)
        self.permit_hash_secret = secrets.token_hex(32)

    def _build_services(self) -> dict[str, Any]:
        """Build services dict matching what deploy scripts expect from host.data.services."""
        h = self.host
        p = self.PORTS

        postgres_config = PostgreSQLConfig(
            hostname=h,
            port=p["postgres"],
            user=DEV_DEFAULTS["postgres_user"],
            password=DEV_DEFAULTS["postgres_password"],
        )

        redis_config = RedisConfig(
            hostname=h,
            port=p["redis"],
            password="",
            container_image="redis:7.2-alpine",
        )

        etcd_config = EtcdConfig(
            hostname=h,
            port=p["etcd"],
        )

        bai_core_config = BackendAICoreConfig(
            version=self.bai_version,
        )

        manager_config = ManagerConfig(
            hostname=h,
            port=p["manager"],
            superadmin_password=DEV_DEFAULTS["superadmin_password"],
            superadmin_access_key=DEV_DEFAULTS["superadmin_access_key"],
            superadmin_secret_key=DEV_DEFAULTS["superadmin_secret_key"],
            user_password=DEV_DEFAULTS["user_password"],
            user_access_key=DEV_DEFAULTS["user_access_key"],
            user_secret_key=DEV_DEFAULTS["user_secret_key"],
        )

        webserver_config = WebserverConfig(
            hostname=h,
            port=p["webserver"],
            haproxy_service_port=p["webserver"],
        )

        storage_proxy_config = StorageProxyConfig(
            hostname=h,
            client_port=p["storage_proxy_client"],
            manager_port=p["storage_proxy_manager"],
            client_endpoint=f"http://{h}:{p['storage_proxy_client']}",
            manager_token=secrets.token_hex(32),
            jwt_secret=self.jwt_secret,
        )

        appproxy_config = AppProxyConfig(
            shared_key=self.api_secret,
            jwt_secret=self.jwt_secret,
            permit_hash_secret=self.permit_hash_secret,
            db_user=DEV_DEFAULTS["appproxy_db_user"],
            db_password=DEV_DEFAULTS["appproxy_db_password"],
            db_name="appproxy",
            coordinator_hostname=h,
            coordinator_port=p["appproxy_coordinator"],
            coordinator_advertised_hostname=h,
            coordinator_scheme="http",
            worker_interactive_advertised_hostname=h,
            worker_interactive_port=p["appproxy_worker_interactive"],
            worker_interactive_app_port_start=p["appproxy_worker_interactive_start"],
            worker_interactive_app_port_end=p["appproxy_worker_interactive_end"],
            worker_tcp_advertised_hostname=h,
            worker_tcp_port=p["appproxy_worker_tcp"],
            worker_tcp_app_port_start=p["appproxy_worker_tcp_start"],
            worker_tcp_app_port_end=p["appproxy_worker_tcp_end"],
            worker_inference_advertised_hostname=h,
            worker_inference_port=10203,
            worker_inference_app_port_start=10601,
            worker_inference_app_port_end=10700,
            webserver_endpoint=f"http://{h}:{p['webserver']}",
        )

        hive_gateway_config = HiveGatewayConfig(
            hostname=h,
            port=p["hive_gateway"],
        )

        agent_config = AgentConfig()

        return {
            "postgres": postgres_config,
            "redis": redis_config,
            "etcd": etcd_config,
            "bai_core": bai_core_config,
            "manager": manager_config,
            "webserver": webserver_config,
            "storage_proxy": storage_proxy_config,
            "appproxy": appproxy_config,
            "hive_gateway": hive_gateway_config,
            "agent": agent_config,
            "license_server": LicenseServerConfig(enabled=False),
            "control_panel": ControlPanelConfig(enabled=False),
            "fasttrack": FastTrackConfig(enabled=False),
        }

    def build(self) -> dict[str, Any]:
        """Build complete inventory for local dev deployment."""
        user = os.getenv("USER", "dev")
        uid = os.getuid()
        gid = os.getgid()
        services = self._build_services()

        host_data = {
            # OS
            "bai_home_dir": self.home_dir,
            "bai_user": user,
            "bai_user_id": uid,
            "bai_user_group_id": gid,
            "bai_pip_install_options": None,
            # Python
            "python_version": "3.13.7",
            # Version
            "bai_version": self.bai_version,
            "bai_default_versions": DEFAULT_VERSIONS,
            # Services
            "services": services,
            # Deploy mode
            "mode": "install",
            # Network
            "internal_ip": self.host,
            "public_ip": self.host,
        }

        local_node = ("@local", host_data)

        return {
            # Node groups (all point to single local node)
            "mgmt": [local_node],
            "compute": [],
            "agent": [],
            "mgr": [local_node],
            "web": [local_node],
            "sp": [local_node],
            "apc": [local_node],
            "apw": [local_node],
            "dashboard": [local_node],
            # Config objects
            "postgresConfig": services["postgres"],
            "redisConfig": services["redis"],
            "etcdConfig": services["etcd"],
            "backendAICoreConfig": services["bai_core"],
            "managerConfig": services["manager"],
            "hiveGatewayConfig": services["hive_gateway"],
            "webserverConfig": services["webserver"],
            "storageProxyConfig": services["storage_proxy"],
            "storageProxyConfigShared": services["storage_proxy"],
            "appProxyConfig": services["appproxy"],
            # Enterprise stubs (disabled)
            "licenseServerConfig": services["license_server"],
            "controlPanelConfig": services["control_panel"],
            "fastTrackConfig": services["fasttrack"],
            # Monitoring
            "prometheusConfig": PrometheusConfig(),
            "grafanaConfig": GrafanaConfig(admin_password="develove"),
            "lokiConfig": LokiConfig(),
            "otelCollectorConfig": OTELCollectorConfig(),
            "pyroscopeConfig": PyroscopeConfig(),
        }
