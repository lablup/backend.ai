"""
Backend.AI Unified Inventory Base Module

This module provides the core logic for building PyInfra inventory configurations
that support various deployment scenarios from single-node to 100+ node clusters.

Design principles:
- Auto-detect deployment mode based on node count
- Support multiple IP types (ssh, internal, public)
- Provide sensible defaults with override capabilities
- Maintain backward compatibility with existing PyInfra scripts
"""

import os

from dotenv import load_dotenv

from ai.backend.install.pyinfra.artifact_urls import build_artifact_urls
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
    DataSourcesConfig,
    GrafanaConfig,
    LokiConfig,
    OTELCollectorConfig,
    PrometheusConfig,
    PyroscopeConfig,
)
from ai.backend.install.pyinfra.configs.halfstack import (
    EtcdConfig,
    EtcdHAClusterNodeConfig,
    EtcdHAConfig,
    HiveGatewayClusterNodeConfig,
    HiveGatewayConfig,
    PostgresHAClusterNodeConfig,
    PostgresHAConfig,
    PostgreSQLConfig,
    RedisConfig,
    RedisHAClusterNodeConfig,
    RedisHAConfig,
)
from ai.backend.install.pyinfra.configs.pro import FastTrackConfig

load_dotenv()


class InventoryBuilder:
    """
    Unified inventory builder that supports both single-node and HA deployments.

    Usage:
        builder = InventoryBuilder(MANAGEMENT_NODES, COMPUTE_NODES, SERVICE_PLACEMENT, SITE_CONFIG)
        locals().update(builder.build())
    """

    # Reserved node configuration keys (not passed to PyInfra)
    RESERVED_MGMT_KEYS = {
        "ips",
        "ssh_port",
        "enable_sftp",
        "host_alias",
        "node_number",
        "public_host",  # For agent config
    }

    # Reserved compute node configuration keys (not passed to PyInfra)
    RESERVED_COMPUTE_KEYS = {
        "ips",
        "ssh_port",
        "accelerator",
        "resource_group",
        "resource_group_type",
        "container_port_range",
        "public_host",
        "scratch_type",
        "scratch_root",
        "scratch_size",
        "host_alias",
    }

    # Standard port definitions
    DEFAULT_PORTS = {
        "manager": 8082,
        "manager_haproxy": 8081,
        "manager_internal": 18080,
        "hive_gateway": 4000,
        "webserver_single": 8080,
        "webserver": 8079,
        "webserver_haproxy": 8080,
        "storage_proxy_single": 6021,
        "storage_proxy": 6023,
        "storage_proxy_haproxy": 6021,
        "storage_proxy_manager": 6024,
        "storage_proxy_manager_haproxy": 6022,
        "postgres_ha": 8101,
        "postgres_ha_haproxy": 8100,
        "postgres_ha_standby": 8105,
        "postgres_ha_api": 8111,
        "postgres_etcd_client": 8126,
        "postgres_etcd_peer": 8326,
        "postgres_single": 8100,
        "redis_single": 8110,
        "redis": 8112,
        "redis_haproxy": 8110,
        "redis_haproxy_stats": 9000,
        "redis_sentinel": 8114,
        "etcd_single": 8120,
        "etcd_client": 8121,
        "etcd_peer": 8321,
        "etcd_grpc": 8120,
        "appproxy_coordinator": 10200,
        "appproxy_worker_interactive": 10201,
        "appproxy_worker_interactive_start": 10205,
        "appproxy_worker_interactive_end": 10500,
        "appproxy_worker_tcp": 10202,
        "appproxy_worker_tcp_start": 10501,
        "appproxy_worker_tcp_end": 10600,
        "appproxy_worker_inference": 10203,
        "appproxy_worker_inference_start": 10601,
        "appproxy_worker_inference_end": 10700,
        "control_panel": 8443,
        "fasttrack": 9500,
        "license_server": 6099,
        "prometheus": 19090,
        "redis_exporter": 9121,
        "postgres_exporter": 9187,
        "blackbox_exporter": 9115,
        "dcgm_exporter": 9400,
        "grafana": 3000,
        "loki": 3100,
        "pyroscope": 4040,
        "otel_grpc": 4317,
        "otel_http": 4318,
        "otel_health": 13133,
        "tempo": 3200,
    }

    # Standard version definitions for all components
    DEFAULT_VERSIONS = {
        # Halfstack components
        "postgres_ha": "15.12-timescaledb",
        "postgres_etcd": "v3.5.21",
        "redis": "7.2",
        "haproxy": "2.9",
        "hive_gateway": "2.1.12",
        "apollo_router": "v1.61.9",  # Apollo Router for Backend.AI 25.15
        "etcd": "v3.5.21",
        "etcd_grpc": "v3.5.21",
        # Monitoring stack
        "prometheus": "v3.1.0",
        "redis_exporter": "v1.73.0",
        "postgres_exporter": "v0.17.1",
        "blackbox_exporter": "v0.25.0",
        "dcgm_exporter": "3.3.0-3.2.0-ubuntu22.04",
        "grafana": "12.2.1",
        "loki": "3.5.0",
        "pyroscope": "1.9.2",
        "otel": "0.126.0",
        # App proxy
        "traefik": "v3.3.7",
        "traefik_plugin": "0.0.5",
    }

    def __init__(
        self,
        management_nodes: dict,
        compute_nodes: dict,
        service_placement: dict,
        site_config: dict,
    ) -> None:
        """
        Initialize inventory builder.

        Args:
            management_nodes: Dict of management node configurations
            compute_nodes: Dict of compute node configurations
            service_placement: Service placement configuration (if empty, uses profile defaults)
            site_config: Site-specific configuration (repo_url, bai_version, etc.)
        """
        self.mgmt_nodes = management_nodes
        self.compute_nodes = compute_nodes
        self.service_placement = service_placement
        self.site_config = site_config

        # Repository URI
        self.repo_url = site_config.get(
            "repo_url", os.getenv("PYINFRA_BAI_OFFLINE_REPO_URL", "http://bai-repo:9200")
        )

        # Core configuration
        self.bai_version = site_config.get("bai_version", "25.14.5")
        self.vfroot_path = site_config.get("vfroot_path", "/vfroot")
        self.vfroot_volume_names = site_config.get("vfroot_volume_names", "nas")

        # Merge custom versions from SITE_CONFIG (same pattern as ports)
        custom_versions = site_config.get("versions", {})
        self.DEFAULT_VERSIONS = {**self.DEFAULT_VERSIONS, **custom_versions}

        # Merge custom ports from SITE_CONFIG
        custom_ports = site_config.get("ports", {})
        self.DEFAULT_PORTS = {**self.DEFAULT_PORTS, **custom_ports}

        # Detect deployment mode
        self._detect_profile()

        # Initialize cluster helper for HA modes
        self._cluster_helper = None

    def _collect_compute_node_targets(self) -> list[str]:
        """Collect internal IPs of all compute nodes for blackbox TCP probes."""
        return [
            self._process_node_ips(config)["internal"] for config in self.compute_nodes.values()
        ]

    def _collect_dcgm_exporter_targets(self) -> list[str]:
        """Collect internal IPs of GPU compute nodes for Prometheus DCGM targets."""
        return [
            self._process_node_ips(config)["internal"]
            for config in self.compute_nodes.values()
            if config.get("accelerator", "cpu") != "cpu"
        ]

    def _detect_profile(self) -> None:
        """Auto-detect deployment profile based on node count"""
        mgmt_count = len(self.mgmt_nodes)
        if mgmt_count == 1:
            self.profile = "single"
            self.is_ha = False
        elif mgmt_count >= 3:
            self.profile = f"ha-{mgmt_count}"
            self.is_ha = True
        else:
            raise ValueError(
                f"Invalid management node count: {mgmt_count}. Must be 1 or >= 3 for HA."
            )

    def _process_node_ips(self, node_config: dict) -> dict:
        """
        Handle multiple IP types with backward compatibility.

        Returns dict with ssh, internal, and public IPs.
        """
        ips = node_config.get("ips", {})

        # Backward compatibility: string → all IPs same
        if isinstance(ips, str):
            ips = {"ssh": ips, "internal": ips, "public": ips}

        # Ensure required IPs exist
        if "ssh" not in ips:
            raise ValueError(f"Node {node_config} must have 'ssh' IP defined")

        # Auto-fill missing IPs
        if "internal" not in ips:
            ips["internal"] = ips["ssh"]
        if "public" not in ips:
            ips["public"] = ips.get("internal", ips["ssh"])

        return ips

    def _detect_router_type(self) -> str:
        """Detect the appropriate GraphQL router type based on BAI version.

        Backend.AI 25.15.x uses Apollo Router, while post-25.15 uses Hive Gateway.
        Can be overridden via ``router_type`` in SITE_CONFIG.
        """
        # Allow explicit override via SITE_CONFIG, with validation
        explicit = self.site_config.get("router_type")
        if explicit:
            normalized = str(explicit).strip().lower()
            if normalized not in {"apollo", "hive"}:
                raise ValueError(
                    f"Invalid router_type '{explicit}'. Allowed values are 'apollo' or 'hive'."
                )
            return normalized
        # Auto-detect from BAI version: 25.15.x → apollo, otherwise → hive
        version_parts = self.bai_version.split(".")
        if len(version_parts) >= 2:
            try:
                major, minor = int(version_parts[0]), int(version_parts[1])
                if major == 25 and minor == 15:
                    return "apollo"
            except ValueError:
                pass
        return "hive"

    def _get_storage_proxy_client_endpoint(self, default_host: str, default_port: int) -> str:
        """Get storage proxy client endpoint with optional site config override.

        Args:
            default_host: Default hostname/IP for the client endpoint
            default_port: Default port for the client endpoint

        Returns:
            Client endpoint URL (either from site_config override or default)
        """
        return self.site_config.get(
            "storage_proxy_client_endpoint",
            f"http://{default_host}:{default_port}",
        )

    def _validate_service_placement(self) -> dict:
        """
        Validate and return SERVICE_PLACEMENT configuration.

        SERVICE_PLACEMENT is required for all deployment modes (single and HA).
        This ensures explicit, predictable service placement across all scenarios.

        Required keys:
        - halfstack, manager, webserver, storage_proxy, appproxy
        """
        if not self.service_placement:
            raise ValueError(
                "SERVICE_PLACEMENT must be explicitly provided.\n"
                f"Current profile: {self.profile}\n\n"
                "Required keys:\n"
                "  - halfstack (PostgreSQL, Redis, ETCD)\n"
                "  - manager, webserver, storage_proxy\n\n"
                "Optional keys (dashboard services):\n"
                "  - prometheus, grafana, loki, otel_collector, pyroscope\n\n"
                "Example for single-node:\n"
                "SERVICE_PLACEMENT = {\n"
                '    "halfstack": ["mgmt1"],\n'
                '    "manager": ["mgmt1"],\n'
                '    "webserver": ["mgmt1"],\n'
                '    "storage_proxy": ["mgmt1"],\n'
                '    "appproxy": ["mgmt1"],\n'
                "    # Optional dashboard services\n"
                '    "prometheus": ["mgmt1"],\n'
                '    "grafana": ["mgmt1"],\n'
                "}\n\n"
                "Example for 3-node HA:\n"
                "SERVICE_PLACEMENT = {\n"
                '    "halfstack": ["mgmt1", "mgmt2", "mgmt3"],\n'
                '    "manager": ["mgmt1", "mgmt2", "mgmt3"],\n'
                '    "webserver": ["mgmt1", "mgmt2", "mgmt3"],\n'
                '    "storage_proxy": ["mgmt1", "mgmt2", "mgmt3"],\n'
                '    "appproxy": ["mgmt1", "mgmt2", "mgmt3"],\n'
                "    # Optional: Individual dashboard services on different nodes\n"
                '    "prometheus": ["mgmt3"],\n'
                '    "grafana": ["mgmt2"],\n'
                '    "loki": ["mgmt3"],\n'
                "}\n"
            )

        # Validate required keys (core services only)
        required_keys = [
            "halfstack",
            "manager",
            "webserver",
            "storage_proxy",
        ]

        # Optional keys (can be omitted if not needed)
        optional_keys = [
            "appproxy",  # Legacy: single key for both coordinator and worker
            "appproxy_coordinator",  # Separate coordinator placement
            "appproxy_worker",  # Separate worker placement
            "hive_gateway",  # GraphQL Federation Router (defaults to webserver nodes)
            "prometheus",
            "grafana",
            "loki",
            "otel_collector",
            "pyroscope",
        ]

        missing_keys = [key for key in required_keys if key not in self.service_placement]
        if missing_keys:
            raise ValueError(
                f"SERVICE_PLACEMENT is missing required keys: {', '.join(missing_keys)}\n"
                f"All core services must be explicitly placed for {self.profile} mode.\n"
                f"Optional keys: {', '.join(optional_keys)}"
            )

        # Validate appproxy placement: must have either 'appproxy' OR both 'appproxy_coordinator' and 'appproxy_worker'
        has_appproxy_legacy = "appproxy" in self.service_placement
        has_appproxy_split = (
            "appproxy_coordinator" in self.service_placement
            and "appproxy_worker" in self.service_placement
        )

        if not (has_appproxy_legacy or has_appproxy_split):
            raise ValueError(
                "SERVICE_PLACEMENT must include App Proxy placement:\n"
                "  Option 1 (legacy): 'appproxy' key with nodes for both coordinator and worker\n"
                "  Option 2 (split): Both 'appproxy_coordinator' and 'appproxy_worker' keys\n"
                f"Current keys: {list(self.service_placement.keys())}"
            )

        return self.service_placement

    def build(self) -> dict:
        """
        Build complete inventory configuration.

        Returns dict with all PyInfra variables that should be added to locals().
        """
        if self.is_ha:
            return self._build_ha_inventory()
        return self._build_single_inventory()

    def _build_single_inventory(self) -> dict:
        """Build single-node inventory configuration"""
        # Validate and get service placement
        placement = self._validate_service_placement()
        artifact_urls = build_artifact_urls(self.repo_url, self.DEFAULT_VERSIONS)

        # Get the single management node
        node_name = list(self.mgmt_nodes.keys())[0]
        node_config = self.mgmt_nodes[node_name]
        ips = self._process_node_ips(node_config)

        # Build halfstack configurations (single mode)
        # Use VIP hostnames for consistency with HA mode
        postgresConfig = PostgreSQLConfig(
            hostname="bai-db-vip",
            port=self.DEFAULT_PORTS["postgres_single"],
            user="postgres",
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            db_name="backend",
        )

        redisConfig = RedisConfig(
            container_image=f"redis:{self.DEFAULT_VERSIONS['redis']}-alpine",
            hostname="bai-redis-vip",
            port=self.DEFAULT_PORTS["redis_single"],
            password=os.environ.get("REDIS_PASSWORD", ""),
        )

        etcdConfig = EtcdConfig(
            connect_client_ip="bai-etcd-vip",
            advertised_client_port=self.DEFAULT_PORTS["etcd_single"],
            advertised_client_ip="0.0.0.0",
        )

        # Build core configurations
        backendAICoreConfig = BackendAICoreConfig(
            version=self.bai_version,
            vfroot_path=self.vfroot_path,
        )

        # Enterprise stubs (disabled)
        licenseServerConfig = LicenseServerConfig(enabled=False)
        controlPanelConfig = ControlPanelConfig(enabled=False)
        fastTrackConfig = FastTrackConfig(enabled=False)

        managerConfig = ManagerConfig(
            port=self.DEFAULT_PORTS["manager_haproxy"],
            client_connect_ip=ips["internal"],
            haproxy_service_port=None,
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            cluster_nodes=[],
            internal_host=ips["internal"],
            internal_port=self.DEFAULT_PORTS["manager_internal"],
            num_proc=4,
            superadmin_password=os.environ.get("SUPERADMIN_PASSWORD", ""),
            superadmin_access_key=os.environ.get("SUPERADMIN_ACCESS_KEY", ""),
            superadmin_secret_key=os.environ.get("SUPERADMIN_SECRET_KEY", ""),
            user_password=os.environ.get("USER_PASSWORD", ""),
            user_access_key=os.environ.get("USER_ACCESS_KEY", ""),
            user_secret_key=os.environ.get("USER_SECRET_KEY", ""),
        )

        # Auto-detect router type from BAI version (25.15.x → apollo, post-25.15 → hive)
        router_type = self._detect_router_type()

        hiveGatewayConfig = HiveGatewayConfig(
            enabled=True,
            router_type=router_type,
            port=self.DEFAULT_PORTS["hive_gateway"],
            container_image=f"ghcr.io/graphql-hive/gateway:{self.DEFAULT_VERSIONS['hive_gateway']}",
            local_archive_path=artifact_urls["hive_gateway"],
            apollo_container_image=f"ghcr.io/apollographql/router:{self.DEFAULT_VERSIONS['apollo_router']}",
            apollo_local_archive_path=artifact_urls["apollo_router"],
            manager_hostname="bai-m-vip",
            manager_graphql_port=self.DEFAULT_PORTS["manager_haproxy"],
            advertised_hostname="localhost",
            # HA mode (cluster_nodes empty = single-node, HAProxy not used)
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            haproxy_local_archive_path=artifact_urls["haproxy"],
            cluster_nodes=[],
        )

        webserverConfig = WebserverConfig(
            port=self.DEFAULT_PORTS["webserver_haproxy"],
            haproxy_service_port=None,
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            cluster_nodes=[],
        )

        storageProxyConfig = StorageProxyConfig(
            port=self.DEFAULT_PORTS["storage_proxy_single"],
            manager_port=self.DEFAULT_PORTS["storage_proxy_manager_haproxy"],
            haproxy_service_port=None,
            haproxy_manager_service_port=None,
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            client_endpoint=self._get_storage_proxy_client_endpoint(
                ips["public"], self.DEFAULT_PORTS["storage_proxy_single"]
            ),
            manager_endpoint=f"http://{ips['internal']}:{self.DEFAULT_PORTS['storage_proxy_manager_haproxy']}",
            manager_token=os.environ.get("STORAGE_PROXY_MANAGER_TOKEN", ""),
            jwt_secret=os.environ.get("STORAGE_PROXY_JWT_SECRET", ""),
            announce_internal_host=ips["internal"],
            volume_names=self.vfroot_volume_names,
            cluster_nodes=[],
        )

        appProxyConfig = AppProxyConfig(
            shared_key=os.environ.get("APP_PROXY_SHARED_SECRET_KEY", ""),
            jwt_secret=os.environ.get("APP_PROXY_JWT_SECRET", ""),
            permit_hash_secret=os.environ.get("APP_PROXY_PERMIT_HASH_SECRET", ""),
            db_password=os.environ.get("APP_PROXY_DB_PASSWORD", ""),
            coordinator_hostname=ips["internal"],
            coordinator_vip_hostname=ips["internal"],
            coordinator_advertised_hostname=ips["public"],
            coordinator_port=self.DEFAULT_PORTS["appproxy_coordinator"],
            coordinator_scheme="http",
            worker_node_number=1,
            worker_interactive_advertised_hostname=ips["public"],
            worker_interactive_port=self.DEFAULT_PORTS["appproxy_worker_interactive"],
            worker_interactive_app_port_start=self.DEFAULT_PORTS[
                "appproxy_worker_interactive_start"
            ],
            worker_interactive_app_port_end=self.DEFAULT_PORTS["appproxy_worker_interactive_end"],
            worker_tcp_advertised_hostname=ips["public"],
            worker_tcp_port=self.DEFAULT_PORTS["appproxy_worker_tcp"],
            worker_tcp_app_port_start=self.DEFAULT_PORTS["appproxy_worker_tcp_start"],
            worker_tcp_app_port_end=self.DEFAULT_PORTS["appproxy_worker_tcp_end"],
            worker_inference_advertised_hostname=ips["public"],
            worker_inference_port=self.DEFAULT_PORTS["appproxy_worker_inference"],
            worker_inference_app_port_start=self.DEFAULT_PORTS["appproxy_worker_inference_start"],
            worker_inference_app_port_end=self.DEFAULT_PORTS["appproxy_worker_inference_end"],
            traefik_archive_url=artifact_urls["traefik"],
            traefik_plugin_url=artifact_urls["traefik_plugin"],
        )

        # Collect compute node IPs for Prometheus targets
        compute_targets = self._collect_compute_node_targets()
        dcgm_targets = self._collect_dcgm_exporter_targets()

        # Dashboard configs (image tags use Config class defaults from DEFAULT_VERSIONS)
        prometheusConfig = PrometheusConfig(
            hostname="localhost",
            port=self.DEFAULT_PORTS["prometheus"],
            retention_days=180,
            http_sd_host=ips["internal"],
            http_sd_port=self.DEFAULT_PORTS["manager_internal"],
            etcd_host="host.docker.internal",
            etcd_port=self.DEFAULT_PORTS["etcd_single"],
            redis_exporter_host="host.docker.internal",
            redis_exporter_port=self.DEFAULT_PORTS["redis_exporter"],
            redis_exporter_image_tag=self.DEFAULT_VERSIONS["redis_exporter"],
            db_exporter_host="host.docker.internal",
            db_exporter_port=self.DEFAULT_PORTS["postgres_exporter"],
            db_exporter_image_tag=self.DEFAULT_VERSIONS["postgres_exporter"],
            blackbox_exporter_host="host.docker.internal",
            blackbox_exporter_port=self.DEFAULT_PORTS["blackbox_exporter"],
            blackbox_exporter_image_tag=self.DEFAULT_VERSIONS["blackbox_exporter"],
            local_archive_path=artifact_urls["prometheus"],
            redis_exporter_local_archive_path=artifact_urls["redis_exporter"],
            db_exporter_local_archive_path=artifact_urls["postgres_exporter"],
            blackbox_exporter_local_archive_path=artifact_urls["blackbox_exporter"],
            compute_node_targets=compute_targets,
            dcgm_exporter_port=self.DEFAULT_PORTS["dcgm_exporter"],
            dcgm_exporter_image_tag=self.DEFAULT_VERSIONS["dcgm_exporter"],
            dcgm_exporter_local_archive_path=artifact_urls["dcgm_exporter"],
            dcgm_exporter_targets=dcgm_targets,
        )

        grafanaConfig = GrafanaConfig(
            admin_id="admin",
            admin_password=os.environ.get("GRAFANA_ADMIN_PASSWORD", ""),
            local_archive_path=artifact_urls["grafana"],
        )

        lokiConfig = LokiConfig(
            port=self.DEFAULT_PORTS["loki"],
            retention_period="720h",
            local_archive_path=artifact_urls["loki"],
        )

        otelCollectorConfig = OTELCollectorConfig(
            hostname=ips["internal"],
            grpc_port=self.DEFAULT_PORTS["otel_grpc"],
            http_port=self.DEFAULT_PORTS["otel_http"],
            health_port=self.DEFAULT_PORTS["otel_health"],
            local_archive_path=artifact_urls["otel_collector"],
        )

        pyroscopeConfig = PyroscopeConfig(
            port=self.DEFAULT_PORTS["pyroscope"],
            local_archive_path=artifact_urls["pyroscope"],
        )

        dataSourcesConfig = DataSourcesConfig(
            prometheus_host="host.docker.internal",
            prometheus_port=self.DEFAULT_PORTS["prometheus"],
            postgres_host=postgresConfig.hostname,
            postgres_port=postgresConfig.port,
            # Uses read-only credentials from environment variables
            postgres_user=os.environ.get("POSTGRES_READONLY_USER", "ronly"),
            postgres_password=os.environ.get("POSTGRES_READONLY_PASSWORD", "ronly"),
            postgres_database=postgresConfig.db_name,
            pyroscope_host="host.docker.internal",
            pyroscope_port=self.DEFAULT_PORTS["pyroscope"],
            loki_host="host.docker.internal",
            loki_port=self.DEFAULT_PORTS["loki"],
            tempo_host="host.docker.internal",
            tempo_port=self.DEFAULT_PORTS["tempo"],
        )

        # Common services
        COMMON_SERVICES = {
            "postgres": postgresConfig,
            "redis": redisConfig,
            "etcd": etcdConfig,
            "license_server": licenseServerConfig,
            "bai_core": backendAICoreConfig,
            # Shared dashboard config (all nodes can access even if not deployed on that node)
            "prometheus_config": prometheusConfig,
            "otel_collector_config": otelCollectorConfig,
        }

        # Build management node services (core services only)
        mgmt_services = {
            **COMMON_SERVICES,
            "manager": managerConfig,
            "webserver": webserverConfig,
            "hive_gateway": hiveGatewayConfig,
            "storage_proxy": storageProxyConfig,
            "appproxy": appProxyConfig,
            "control_panel": controlPanelConfig,
            "fasttrack": fastTrackConfig,
            # sFTP agent
            "agent": AgentConfig(
                accelerator_type="cpu",
                resource_group="upload",
                resource_group_type="storage",
                rpc_listen_ip=ips["internal"],
                container_port_range=[10801, 10900],
                public_host=node_config.get("public_host"),
                scratch_type="hostfile",
                scratch_root="./scratches",
                scratch_size="50G",
            ),
        }

        # Add individual dashboard services based on placement
        has_any_dashboard_service = False

        if node_name in placement.get("prometheus", []):
            mgmt_services["prometheus"] = prometheusConfig
            has_any_dashboard_service = True

        if node_name in placement.get("grafana", []):
            mgmt_services["grafana"] = grafanaConfig
            has_any_dashboard_service = True

        if node_name in placement.get("loki", []):
            mgmt_services["loki"] = lokiConfig
            has_any_dashboard_service = True

        if node_name in placement.get("otel_collector", []):
            mgmt_services["otel_collector"] = otelCollectorConfig
            has_any_dashboard_service = True

        if node_name in placement.get("pyroscope", []):
            mgmt_services["pyroscope"] = pyroscopeConfig
            has_any_dashboard_service = True

        # Add datasources config if any dashboard service is present
        if has_any_dashboard_service:
            mgmt_services["data_sources"] = dataSourcesConfig

        # Helper for creating nodes
        def make_node(ip: str, **opts: object) -> tuple[str, dict]:
            if (
                sudo_password := os.getenv("PYINFRA_SUDO_PASSWORD")
            ) and "_sudo_password" not in opts:
                opts["_sudo_password"] = sudo_password
            ssh_port = node_config.get("ssh_port", 22)
            if ssh_port != 22:
                ip = f"{ip}:{ssh_port}"
            return (ip, opts)

        # Extract PyInfra-specific options for management node
        mgmt_pyinfra_opts = {
            key: value for key, value in node_config.items() if key not in self.RESERVED_MGMT_KEYS
        }

        # Build node configurations
        mgmt = [
            make_node(
                ips["ssh"],
                node_type="manager",
                services=mgmt_services,
                public_ip=ips["public"],
                internal_ip=ips["internal"],
                bai_version=self.bai_version,
                bai_default_versions=self.DEFAULT_VERSIONS,
                bai_service_placement=placement,
                bai_offline_repo_url=self.repo_url,
                **mgmt_pyinfra_opts,  # Pass through SSH and other PyInfra options
            )
        ]

        # Build compute nodes
        compute = []
        for comp_name, comp_config in self.compute_nodes.items():
            comp_ips = self._process_node_ips(comp_config)

            # Extract PyInfra-specific options (ssh_user, ssh_key, etc.)
            pyinfra_opts = {
                key: value
                for key, value in comp_config.items()
                if key not in self.RESERVED_COMPUTE_KEYS
            }

            compute.append(
                make_node(
                    comp_ips["ssh"],
                    node_type="agent",
                    services={
                        **COMMON_SERVICES,
                        "storage_proxy": storageProxyConfig,
                        "agent": AgentConfig(
                            accelerator_type=comp_config.get("accelerator", "cpu"),
                            resource_group=comp_config.get("resource_group", "default"),
                            resource_group_type="compute",
                            rpc_listen_ip=comp_ips["internal"],
                            container_port_range=comp_config.get(
                                "container_port_range", [30000, 31000]
                            ),
                            public_host=comp_config.get("public_host"),
                            scratch_type=comp_config.get("scratch_type", "hostfile"),
                            scratch_root=comp_config.get("scratch_root", "./scratches"),
                            scratch_size=comp_config.get("scratch_size", "50G"),
                        ),
                    },
                    internal_ip=comp_ips["internal"],
                    **pyinfra_opts,  # Pass through SSH and other PyInfra options
                )
            )

        # Service group mappings for single node
        return {
            # Node lists
            "mgmt": mgmt,
            "compute": compute,
            "agent": compute,
            # Service groups (all point to mgmt node)
            "mgr": mgmt,
            "mgr1": mgmt,
            "web": mgmt,
            "sp": mgmt,
            "apc": mgmt,
            "apw": mgmt,
            "cp": mgmt,
            "sftp": mgmt,
            "dashboard": mgmt,
            "tmp": mgmt,
            # Config objects
            "postgresConfig": postgresConfig,
            "redisConfig": redisConfig,
            "etcdConfig": etcdConfig,
            "backendAICoreConfig": backendAICoreConfig,
            "licenseServerConfig": licenseServerConfig,
            "managerConfig": managerConfig,
            "hiveGatewayConfig": hiveGatewayConfig,
            "webserverConfig": webserverConfig,
            "storageProxyConfig": storageProxyConfig,
            "storageProxyConfigShared": storageProxyConfig,
            "appProxyConfig": appProxyConfig,
            "controlPanelConfig": controlPanelConfig,
            "fastTrackConfig": fastTrackConfig,
            "harborRegistryConfig": None,
            "rtunConfig": None,
            "prometheusConfig": prometheusConfig,
            "grafanaConfig": grafanaConfig,
            "lokiConfig": lokiConfig,
            "otelCollectorConfig": otelCollectorConfig,
            "pyroscopeConfig": pyroscopeConfig,
        }

    def _build_ha_inventory(self) -> dict:
        """Build high-availability inventory configuration"""
        # Validate and get service placement
        placement = self._validate_service_placement()
        artifact_urls = build_artifact_urls(self.repo_url, self.DEFAULT_VERSIONS)

        # Build cluster node configurations for halfstack services
        halfstack_nodes = placement.get("halfstack", list(self.mgmt_nodes.keys())[:3])

        # Helper functions
        def get_node_info(hostname: str) -> dict:
            if hostname not in self.mgmt_nodes:
                raise ValueError(f"Node '{hostname}' not found in management nodes")
            node_config = self.mgmt_nodes[hostname]
            ips = self._process_node_ips(node_config)
            return {
                "hostname": hostname,
                "internal_ip": ips["internal"],
                "public_ip": ips["public"],
                "ssh_ip": ips["ssh"],
                "ssh_port": node_config.get("ssh_port", 22),
                "node_number": node_config.get(
                    "node_number", list(self.mgmt_nodes.keys()).index(hostname) + 1
                ),
                "host_alias": node_config.get(
                    "host_alias", f"bai-m{list(self.mgmt_nodes.keys()).index(hostname) + 1}"
                ),
            }

        def get_service_host(service_key: str) -> str:
            """Get hostname for a service based on placement"""
            service_nodes = placement.get(service_key, [])
            if not service_nodes:
                return "localhost"
            service_hostname = service_nodes[0]
            node_info = get_node_info(service_hostname)
            return node_info["host_alias"]

        # Build PostgreSQL HA cluster configuration (Core TDB)
        postgresHAConfig = PostgresHAConfig(
            name="default",
            cluster_nodes=[
                PostgresHAClusterNodeConfig(
                    hostname=f"node{get_node_info(h)['node_number']}",
                    ip=get_node_info(h)["internal_ip"],
                    etcd_client_port=self.DEFAULT_PORTS["postgres_etcd_client"],
                    etcd_peer_port=self.DEFAULT_PORTS["postgres_etcd_peer"],
                    pg_api_port=self.DEFAULT_PORTS["postgres_ha_api"],
                    pg_sql_port=self.DEFAULT_PORTS["postgres_ha"],
                    node_number=get_node_info(h)["node_number"],
                )
                for h in halfstack_nodes
            ],
            pg_major_version="15",
            pg_active_port=self.DEFAULT_PORTS["postgres_ha_haproxy"],
            pg_standby_port=self.DEFAULT_PORTS["postgres_ha_standby"],
            pg_replicator_password=os.environ.get("POSTGRES_REPLICATOR_PASSWORD", ""),
            pg_superuser_password=os.environ.get("POSTGRES_PASSWORD", ""),
            pg_rewind_password=os.environ.get("POSTGRES_REWIND_PASSWORD", ""),
            container_image=f"cr.backend.ai/halfstack/postgres_ha:{self.DEFAULT_VERSIONS['postgres_ha']}",
            etcd_container_image=f"quay.io/coreos/etcd:{self.DEFAULT_VERSIONS['postgres_etcd']}",
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            local_archive_path=artifact_urls["postgres_ha"],
            etcd_local_archive_path=artifact_urls["postgres_etcd"],
        )

        # Build Redis HA cluster configuration
        redisHAConfig = RedisHAConfig(
            name="default",
            cluster_nodes=[
                RedisHAClusterNodeConfig(
                    hostname=get_node_info(h)["host_alias"],
                    ip=get_node_info(h)["internal_ip"],
                    port=self.DEFAULT_PORTS["redis"],
                    ssh_ip=get_node_info(h)["ssh_ip"],
                    node_number=get_node_info(h)["node_number"],
                )
                for h in halfstack_nodes
            ],
            password=os.environ.get("REDIS_PASSWORD", ""),
            container_image=f"redis:{self.DEFAULT_VERSIONS['redis']}-alpine",
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            haproxy_service_port=self.DEFAULT_PORTS["redis_haproxy"],
            haproxy_stat_port=self.DEFAULT_PORTS["redis_haproxy_stats"],
            sentinel_port=self.DEFAULT_PORTS["redis_sentinel"],
            redis_cpu_count=2,
            redis_memory_limit="4g",
            haproxy_cpu_count=1,
            haproxy_memory_limit="2g",
            sentinel_cpu_count=1,
            sentinel_memory_limit="1g",
            local_archive_path=artifact_urls["redis"],
            haproxy_local_archive_path=artifact_urls["haproxy"],
        )

        # Build ETCD HA cluster configuration
        etcdHAConfig = EtcdHAConfig(
            name="default",
            cluster_nodes=[
                EtcdHAClusterNodeConfig(
                    hostname=h,
                    client_ip=get_node_info(h)["internal_ip"],
                    client_port=self.DEFAULT_PORTS["etcd_client"],
                    ssh_ip=get_node_info(h)["ssh_ip"],
                    peer_ip=get_node_info(h)["internal_ip"],
                    peer_port=self.DEFAULT_PORTS["etcd_peer"],
                    node_number=get_node_info(h)["node_number"],
                )
                for h in halfstack_nodes
            ],
            container_image=f"quay.io/coreos/etcd:{self.DEFAULT_VERSIONS['etcd']}",
            grpc_container_image=f"quay.io/coreos/etcd:{self.DEFAULT_VERSIONS['etcd_grpc']}",
            grpc_service_ip="0.0.0.0",
            grpc_service_port=self.DEFAULT_PORTS["etcd_grpc"],
            local_archive_path=artifact_urls["etcd"],
            grpc_local_archive_path=artifact_urls["etcd_grpc"],
        )

        # Build common service configurations
        backendAICoreConfig = BackendAICoreConfig(
            version=self.bai_version,
            vfroot_path=self.vfroot_path,
        )

        # Enterprise stubs (disabled)
        licenseServerConfig = LicenseServerConfig(enabled=False)
        controlPanelConfig = ControlPanelConfig(enabled=False)
        fastTrackConfig = FastTrackConfig(enabled=False)

        # Get first management node's public IP for external endpoints
        first_mgmt_node = get_node_info(list(self.mgmt_nodes.keys())[0])

        # Build webserver configuration
        webserver_nodes = placement.get("webserver", list(self.mgmt_nodes.keys())[:3])
        webserverConfig = WebserverConfig(
            port=self.DEFAULT_PORTS["webserver"],
            haproxy_service_port=self.DEFAULT_PORTS["webserver_haproxy"],
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            cluster_nodes=[
                {
                    "name": f"webserver_{i + 1}",
                    "hostname": f"bai-web{i + 1}",
                    "ip": get_node_info(hostname)["internal_ip"],
                }
                for i, hostname in enumerate(webserver_nodes)
            ],
        )

        # Build Hive Gateway HA configuration
        # Default to webserver nodes (Hive Gateway serves GraphQL to clients)
        hive_gateway_nodes = placement.get("hive_gateway", webserver_nodes)
        if not hive_gateway_nodes:
            raise ValueError(
                "Hive Gateway placement resolved to an empty list. "
                "Ensure SERVICE_PLACEMENT['webserver'] is non-empty, "
                "or provide an explicit non-empty 'hive_gateway' placement."
            )
        # Auto-detect router type from BAI version (25.15.x → apollo, post-25.15 → hive)
        router_type = self._detect_router_type()

        hiveGatewayConfig = HiveGatewayConfig(
            enabled=True,
            router_type=router_type,
            port=self.DEFAULT_PORTS["hive_gateway"],
            container_image=f"ghcr.io/graphql-hive/gateway:{self.DEFAULT_VERSIONS['hive_gateway']}",
            local_archive_path=artifact_urls["hive_gateway"],
            apollo_container_image=f"ghcr.io/apollographql/router:{self.DEFAULT_VERSIONS['apollo_router']}",
            apollo_local_archive_path=artifact_urls["apollo_router"],
            manager_hostname="bai-m-vip",
            manager_graphql_port=self.DEFAULT_PORTS["manager_haproxy"],
            # GraphQL Router is co-located with webserver, so each webserver
            # connects to its local HAProxy instance via localhost.
            advertised_hostname="localhost",
            # HA mode configuration
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            haproxy_local_archive_path=artifact_urls["haproxy"],
            cluster_nodes=[
                HiveGatewayClusterNodeConfig(
                    name=f"hive_gateway_{i + 1}",
                    hostname=f"bai-gw{i + 1}",
                    ip=get_node_info(hostname)["internal_ip"],
                )
                for i, hostname in enumerate(hive_gateway_nodes)
            ],
        )

        # Collect compute node IPs for Prometheus targets
        compute_targets = self._collect_compute_node_targets()
        dcgm_targets = self._collect_dcgm_exporter_targets()

        # Dashboard configurations
        prometheusConfig = PrometheusConfig(
            hostname=get_service_host("prometheus"),
            port=self.DEFAULT_PORTS["prometheus"],
            retention_days=180,
            http_sd_host="bai-m-vip",
            http_sd_port=self.DEFAULT_PORTS["manager_internal"],
            etcd_host="bai-etcd-vip",
            etcd_port=self.DEFAULT_PORTS["etcd_grpc"],
            redis_exporter_host="bai-redis-vip",
            redis_exporter_port=self.DEFAULT_PORTS["redis_exporter"],
            redis_exporter_image_tag=self.DEFAULT_VERSIONS["redis_exporter"],
            db_exporter_host="bai-db-vip",
            db_exporter_port=self.DEFAULT_PORTS["postgres_exporter"],
            db_exporter_image_tag=self.DEFAULT_VERSIONS["postgres_exporter"],
            blackbox_exporter_host="host.docker.internal",
            blackbox_exporter_port=self.DEFAULT_PORTS["blackbox_exporter"],
            blackbox_exporter_image_tag=self.DEFAULT_VERSIONS["blackbox_exporter"],
            local_archive_path=artifact_urls["prometheus"],
            redis_exporter_local_archive_path=artifact_urls["redis_exporter"],
            db_exporter_local_archive_path=artifact_urls["postgres_exporter"],
            blackbox_exporter_local_archive_path=artifact_urls["blackbox_exporter"],
            compute_node_targets=compute_targets,
            dcgm_exporter_port=self.DEFAULT_PORTS["dcgm_exporter"],
            dcgm_exporter_image_tag=self.DEFAULT_VERSIONS["dcgm_exporter"],
            dcgm_exporter_local_archive_path=artifact_urls["dcgm_exporter"],
            dcgm_exporter_targets=dcgm_targets,
        )

        grafanaConfig = GrafanaConfig(
            admin_id="admin",
            admin_password=os.environ.get("GRAFANA_ADMIN_PASSWORD", ""),
            local_archive_path=artifact_urls["grafana"],
        )

        lokiConfig = LokiConfig(
            port=self.DEFAULT_PORTS["loki"],
            retention_period="720h",
            local_archive_path=artifact_urls["loki"],
        )

        otelCollectorConfig = OTELCollectorConfig(
            hostname=get_service_host("otel_collector"),
            grpc_port=self.DEFAULT_PORTS["otel_grpc"],
            http_port=self.DEFAULT_PORTS["otel_http"],
            health_port=self.DEFAULT_PORTS["otel_health"],
            local_archive_path=artifact_urls["otel_collector"],
        )

        pyroscopeConfig = PyroscopeConfig(
            port=self.DEFAULT_PORTS["pyroscope"],
            local_archive_path=artifact_urls["pyroscope"],
        )

        def create_datasources_config_for_node(_hostname: str) -> DataSourcesConfig:
            """Create datasources config (hostname param for API compatibility)"""
            # PostgreSQL HA uses VIP, get config from COMMON_SERVICES
            postgres_config = COMMON_SERVICES["postgres"]
            return DataSourcesConfig(
                prometheus_host=get_service_host("prometheus")
                if "prometheus" in placement
                else "localhost",
                prometheus_port=self.DEFAULT_PORTS["prometheus"],
                postgres_host=postgres_config.hostname,
                postgres_port=postgres_config.port,
                # Uses read-only credentials from environment variables
                postgres_user=os.environ.get("POSTGRES_READONLY_USER", "ronly"),
                postgres_password=os.environ.get("POSTGRES_READONLY_PASSWORD", "ronly"),
                postgres_database=postgres_config.db_name,
                pyroscope_host=get_service_host("pyroscope")
                if "pyroscope" in placement
                else "localhost",
                pyroscope_port=self.DEFAULT_PORTS["pyroscope"],
                loki_host=get_service_host("loki") if "loki" in placement else "localhost",
                loki_port=self.DEFAULT_PORTS["loki"],
                tempo_host="localhost",  # tempo not yet implemented, default to localhost
                tempo_port=self.DEFAULT_PORTS["tempo"],
            )

        # Shared storage proxy config for compute nodes
        storageProxyConfigShared = StorageProxyConfig(
            port=self.DEFAULT_PORTS["storage_proxy"],
            manager_port=self.DEFAULT_PORTS["storage_proxy_manager"],
            haproxy_service_port=self.DEFAULT_PORTS["storage_proxy_haproxy"],
            haproxy_manager_service_port=self.DEFAULT_PORTS["storage_proxy_manager_haproxy"],
            haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
            client_endpoint=self._get_storage_proxy_client_endpoint(
                first_mgmt_node["public_ip"], self.DEFAULT_PORTS["storage_proxy_haproxy"]
            ),
            manager_endpoint=f"http://bai-sp-vip:{self.DEFAULT_PORTS['storage_proxy_manager_haproxy']}",
            manager_token=os.environ.get("STORAGE_PROXY_MANAGER_TOKEN", ""),
            jwt_secret=os.environ.get("STORAGE_PROXY_JWT_SECRET", ""),
            volume_names=self.vfroot_volume_names,
        )

        # Common services for all nodes (HA mode uses VIPs)
        COMMON_SERVICES = {
            "postgres": type(
                "PostgresConfig",
                (),
                {
                    "hostname": "bai-db-vip",
                    "port": postgresHAConfig.pg_active_port,
                    "user": postgresHAConfig.pg_superuser_id,
                    "password": postgresHAConfig.pg_superuser_password,
                    "db_name": "backend",
                },
            )(),
            "redis": type(
                "RedisConfig",
                (),
                {
                    "hostname": "bai-redis-vip",
                    "port": redisHAConfig.haproxy_service_port,
                    "password": redisHAConfig.password,
                },
            )(),
            "etcd": type(
                "EtcdConfig",
                (),
                {
                    "connect_client_ip": "bai-etcd-vip",
                    "advertised_client_port": etcdHAConfig.grpc_service_port,
                    "advertised_client_ip": "0.0.0.0",
                },
            )(),
            "license_server": licenseServerConfig,
            "bai_core": backendAICoreConfig,
            # Shared dashboard config (all nodes can access even if not deployed on that node)
            "prometheus_config": prometheusConfig,
            "otel_collector_config": otelCollectorConfig,
        }

        # Helper functions for node-specific configurations
        def get_manager_config_for_node(mgmt_node_hostname: str) -> ManagerConfig:
            """Generate node-specific ManagerConfig"""
            node_data = get_node_info(mgmt_node_hostname)
            manager_nodes = placement.get("manager", [])
            return ManagerConfig(
                port=self.DEFAULT_PORTS["manager"],
                client_connect_ip="bai-m-vip",
                haproxy_service_port=self.DEFAULT_PORTS["manager_haproxy"],
                haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
                cluster_nodes=[
                    {
                        "name": f"manager_{i + 1}",
                        "hostname": f"bai-m{i + 1}",
                        "ip": get_node_info(hostname)["internal_ip"],
                    }
                    for i, hostname in enumerate(manager_nodes)
                ],
                internal_host=node_data["internal_ip"],
                internal_port=self.DEFAULT_PORTS["manager_internal"],
                num_proc=4,
                superadmin_password=os.environ.get("SUPERADMIN_PASSWORD", ""),
                superadmin_access_key=os.environ.get("SUPERADMIN_ACCESS_KEY", ""),
                superadmin_secret_key=os.environ.get("SUPERADMIN_SECRET_KEY", ""),
                user_password=os.environ.get("USER_PASSWORD", ""),
                user_access_key=os.environ.get("USER_ACCESS_KEY", ""),
                user_secret_key=os.environ.get("USER_SECRET_KEY", ""),
            )

        def get_storage_proxy_config_for_node(mgmt_node_hostname: str) -> StorageProxyConfig:
            """Generate node-specific StorageProxyConfig"""
            node_data = get_node_info(mgmt_node_hostname)
            sp_nodes = placement.get("storage_proxy", [])
            return StorageProxyConfig(
                port=self.DEFAULT_PORTS["storage_proxy"],
                manager_port=self.DEFAULT_PORTS["storage_proxy_manager"],
                haproxy_service_port=self.DEFAULT_PORTS["storage_proxy_haproxy"],
                haproxy_manager_service_port=self.DEFAULT_PORTS["storage_proxy_manager_haproxy"],
                haproxy_container_image=f"haproxy:{self.DEFAULT_VERSIONS['haproxy']}-alpine",
                client_endpoint=self._get_storage_proxy_client_endpoint(
                    first_mgmt_node["public_ip"], self.DEFAULT_PORTS["storage_proxy_haproxy"]
                ),
                manager_endpoint=f"http://bai-sp-vip:{self.DEFAULT_PORTS['storage_proxy_manager_haproxy']}",
                manager_token=os.environ.get("STORAGE_PROXY_MANAGER_TOKEN", ""),
                jwt_secret=os.environ.get("STORAGE_PROXY_JWT_SECRET", ""),
                announce_internal_host=node_data["internal_ip"],
                volume_names=self.vfroot_volume_names,
                cluster_nodes=[
                    {
                        "name": f"storage-proxy_{i + 1}",
                        "hostname": f"bai-sp{i + 1}",
                        "ip": get_node_info(hostname)["internal_ip"],
                    }
                    for i, hostname in enumerate(sp_nodes)
                ],
            )

        # Determine actual coordinator node from placement
        coordinator_nodes = placement.get("appproxy_coordinator") or placement.get("appproxy", [])
        coordinator_node_hostname = (
            coordinator_nodes[0] if coordinator_nodes else list(self.mgmt_nodes.keys())[0]
        )
        coordinator_node_data = get_node_info(coordinator_node_hostname)
        coordinator_public_ip = coordinator_node_data["public_ip"]

        def get_appproxy_config_for_node(
            mgmt_node_hostname: str, coordinator_public_ip: str
        ) -> AppProxyConfig:
            """Generate node-specific AppProxyConfig"""
            node_data = get_node_info(mgmt_node_hostname)
            return AppProxyConfig(
                shared_key=os.environ.get("APP_PROXY_SHARED_SECRET_KEY", ""),
                jwt_secret=os.environ.get("APP_PROXY_JWT_SECRET", ""),
                permit_hash_secret=os.environ.get("APP_PROXY_PERMIT_HASH_SECRET", ""),
                db_password=os.environ.get("APP_PROXY_DB_PASSWORD", ""),
                coordinator_hostname="bai-apc-vip",
                coordinator_vip_hostname="bai-apc-vip",
                coordinator_advertised_hostname=coordinator_public_ip,
                coordinator_port=self.DEFAULT_PORTS["appproxy_coordinator"],
                coordinator_scheme="http",
                worker_node_number=node_data["node_number"],
                worker_interactive_advertised_hostname=node_data["public_ip"],
                worker_interactive_port=self.DEFAULT_PORTS["appproxy_worker_interactive"],
                worker_interactive_app_port_start=self.DEFAULT_PORTS[
                    "appproxy_worker_interactive_start"
                ],
                worker_interactive_app_port_end=self.DEFAULT_PORTS[
                    "appproxy_worker_interactive_end"
                ],
                worker_tcp_advertised_hostname=node_data["public_ip"],
                worker_tcp_port=self.DEFAULT_PORTS["appproxy_worker_tcp"],
                worker_tcp_app_port_start=self.DEFAULT_PORTS["appproxy_worker_tcp_start"],
                worker_tcp_app_port_end=self.DEFAULT_PORTS["appproxy_worker_tcp_end"],
                worker_inference_advertised_hostname=node_data["public_ip"],
                worker_inference_port=self.DEFAULT_PORTS["appproxy_worker_inference"],
                worker_inference_app_port_start=self.DEFAULT_PORTS[
                    "appproxy_worker_inference_start"
                ],
                worker_inference_app_port_end=self.DEFAULT_PORTS["appproxy_worker_inference_end"],
                traefik_archive_url=artifact_urls["traefik"],
                traefik_plugin_url=artifact_urls["traefik_plugin"],
            )

        # Default configs for backward compatibility
        appProxyConfig = get_appproxy_config_for_node(
            list(self.mgmt_nodes.keys())[0], coordinator_public_ip
        )

        # Cluster info helpers
        class ClusterInfoHelper:
            """Simplified cluster info lookup"""

            def __init__(
                self,
                postgres_config: PostgresHAConfig,
                etcd_config: EtcdHAConfig,
                redis_config: RedisHAConfig,
            ) -> None:
                self._pg_lookup = {node.hostname: node for node in postgres_config.cluster_nodes}
                self._etcd_lookup = {
                    f"node{node.node_number}": node for node in etcd_config.cluster_nodes
                }
                self._redis_lookup = {node.hostname: node for node in redis_config.cluster_nodes}

            def get_pg_cluster_info(self, node_name: str) -> dict:
                if node_name not in self._pg_lookup:
                    raise ValueError(f"Node '{node_name}' not found in PostgresHAConfig")
                node = self._pg_lookup[node_name]
                return {
                    "node_name": node.hostname,
                    "node_number": node.node_number,
                    "etcd_client_port": node.etcd_client_port,
                    "etcd_peer_port": node.etcd_peer_port,
                    "pg_api_port": node.pg_api_port,
                    "pg_sql_port": node.pg_sql_port,
                }

            def get_etcd_cluster_info(self, node_name: str) -> dict:
                if node_name not in self._etcd_lookup:
                    raise ValueError(f"Node '{node_name}' not found in EtcdHAConfig")
                node = self._etcd_lookup[node_name]
                return {
                    "node_name": f"node{node.node_number}",
                    "node_number": node.node_number,
                    "client_ip": node.client_ip,
                    "client_port": node.client_port,
                    "peer_ip": node.peer_ip,
                    "peer_port": node.peer_port,
                }

            def get_redis_cluster_info(self, node_name: str) -> dict:
                if node_name not in self._redis_lookup:
                    raise ValueError(f"Node '{node_name}' not found in RedisHAConfig")
                node = self._redis_lookup[node_name]
                return {
                    "node_name": node.hostname,
                    "node_number": node.node_number,
                    "ip": node.ip,
                    "port": node.port,
                }

        cluster_helper = ClusterInfoHelper(postgresHAConfig, etcdHAConfig, redisHAConfig)

        # Management services
        MGMT_SERVICES = {
            **COMMON_SERVICES,
            "etcd_ha": etcdHAConfig,
            "postgres_ha": postgresHAConfig,
            "redis_ha": redisHAConfig,
            "webserver": webserverConfig,
            "hive_gateway": hiveGatewayConfig,
            "appproxy": appProxyConfig,
            "control_panel": controlPanelConfig,
            "fasttrack": fastTrackConfig,
        }

        # Helper for creating nodes
        def make_node(ip: str, port: int = 22, **opts: object) -> tuple[str, dict]:
            if (
                sudo_password := os.getenv("PYINFRA_SUDO_PASSWORD")
            ) and "_sudo_password" not in opts:
                opts["_sudo_password"] = sudo_password
            if port != 22:
                ip = f"{ip}:{port}"
            return (ip, opts)

        def create_mgmt_node(hostname: str) -> tuple:
            """Create a management node configuration"""
            node_data = get_node_info(hostname)
            node_number = node_data["node_number"]
            internal_ip = node_data["internal_ip"]
            public_ip = node_data["public_ip"]
            ssh_ip = node_data["ssh_ip"]
            ssh_port = node_data["ssh_port"]

            services = {
                **MGMT_SERVICES,
                "manager": get_manager_config_for_node(hostname),
                "storage_proxy": get_storage_proxy_config_for_node(hostname),
                "appproxy": get_appproxy_config_for_node(hostname, coordinator_public_ip),
            }

            # Check if this node is also a compute agent (dual-role node)
            node_config = self.mgmt_nodes[hostname]
            compute_config = None
            for comp_name, comp_cfg in self.compute_nodes.items():
                comp_ips = self._process_node_ips(comp_cfg)
                # Check if this compute node shares the same IP as current mgmt node
                if comp_ips["internal"] == internal_ip or comp_ips["ssh"] == ssh_ip:
                    compute_config = comp_cfg
                    break

            # Add compute agent if this is a dual-role node
            if compute_config is not None:
                services["agent"] = AgentConfig(
                    accelerator_type=compute_config.get("accelerator", "cpu"),
                    resource_group=compute_config.get("resource_group", "default"),
                    resource_group_type="compute",
                    rpc_listen_ip=internal_ip,
                    container_port_range=compute_config.get("container_port_range", [30000, 31000]),
                    public_host=compute_config.get("public_host"),
                    scratch_type=compute_config.get("scratch_type", "hostfile"),
                    scratch_root=compute_config.get("scratch_root", "./scratches"),
                    scratch_size=compute_config.get("scratch_size", "50G"),
                )
            # Add sFTP agent if enabled (overrides compute agent if both are set)
            elif node_config.get("enable_sftp", False):
                services["agent"] = AgentConfig(
                    accelerator_type="cpu",
                    resource_group="upload",
                    resource_group_type="storage",
                    rpc_listen_ip=internal_ip,
                    container_port_range=[10801, 10900],
                    public_host=node_config.get("public_host"),
                    scratch_type="hostfile",
                    scratch_root="./scratches",
                    scratch_size="50G",
                )

            # Add individual dashboard services based on placement
            has_any_dashboard_service = False

            if hostname in placement.get("prometheus", []):
                services["prometheus"] = prometheusConfig
                # Exporters are automatically included with Prometheus
                # (they are deployed together and share config)
                has_any_dashboard_service = True

            if hostname in placement.get("grafana", []):
                services["grafana"] = grafanaConfig
                has_any_dashboard_service = True

            if hostname in placement.get("loki", []):
                services["loki"] = lokiConfig
                has_any_dashboard_service = True

            if hostname in placement.get("otel_collector", []):
                services["otel_collector"] = otelCollectorConfig
                has_any_dashboard_service = True

            if hostname in placement.get("pyroscope", []):
                services["pyroscope"] = pyroscopeConfig
                has_any_dashboard_service = True

            # Add datasources config if any dashboard service is present
            if has_any_dashboard_service:
                services["data_sources"] = create_datasources_config_for_node(hostname)

            # Extract PyInfra-specific options (ssh_user, ssh_key, etc.)
            pyinfra_opts = {
                key: value
                for key, value in node_config.items()
                if key not in self.RESERVED_MGMT_KEYS
            }

            # Only include cluster info if this node is part of the halfstack cluster
            cluster_info = {}
            if hostname in halfstack_nodes:
                cluster_info = {
                    "pg_cluster_info": cluster_helper.get_pg_cluster_info(f"node{node_number}"),
                    "etcd_cluster_info": cluster_helper.get_etcd_cluster_info(f"node{node_number}"),
                    "redis_cluster_info": cluster_helper.get_redis_cluster_info(
                        node_data["host_alias"]
                    ),
                }

            return make_node(
                ssh_ip,
                ssh_port,
                node_type="manager",
                services=services,
                public_ip=public_ip,
                worker_node_number=node_number,
                bai_version=self.bai_version,
                bai_default_versions=self.DEFAULT_VERSIONS,
                bai_service_placement=placement,
                bai_offline_repo_url=self.repo_url,
                **cluster_info,  # Only added if node is in halfstack
                **pyinfra_opts,  # Pass through SSH and other PyInfra options
            )

        # Generate management nodes
        mgmt = [create_mgmt_node(hostname) for hostname in self.mgmt_nodes.keys()]

        # Build compute nodes
        # Compute nodes are handled in two ways:
        # 1. Dual-role nodes: mgmt nodes that also have agent service (already created above)
        # 2. Standalone compute nodes: dedicated compute-only nodes
        compute = []
        mgmt_ips = set()
        for node_tuple in mgmt:
            # Extract IP from node tuple (format: (ip, {options}))
            if node_tuple:
                ip_with_port = node_tuple[0]
                # Remove port if present
                mgmt_ip = ip_with_port.split(":")[0] if ":" in ip_with_port else ip_with_port
                mgmt_ips.add(mgmt_ip)

        for comp_name, comp_config in self.compute_nodes.items():
            comp_ips = self._process_node_ips(comp_config)

            # Check if this compute node is already part of mgmt (dual-role)
            is_dual_role = comp_ips["internal"] in mgmt_ips or comp_ips["ssh"] in mgmt_ips

            if is_dual_role:
                # Find the corresponding mgmt node and add it to compute list
                for node_tuple in mgmt:
                    if node_tuple:
                        node_ip = (
                            node_tuple[0].split(":")[0] if ":" in node_tuple[0] else node_tuple[0]
                        )
                        if node_ip == comp_ips["ssh"] or node_ip == comp_ips["internal"]:
                            compute.append(node_tuple)
                            break
            else:
                # Standalone compute node - create new node
                pyinfra_opts = {
                    key: value
                    for key, value in comp_config.items()
                    if key not in self.RESERVED_COMPUTE_KEYS
                }
                compute.append(
                    make_node(
                        comp_ips["ssh"],
                        comp_config.get("ssh_port", 22),
                        node_type="agent",
                        services={
                            **COMMON_SERVICES,
                            "storage_proxy": storageProxyConfigShared,
                            "agent": AgentConfig(
                                accelerator_type=comp_config.get("accelerator", "cpu"),
                                resource_group=comp_config.get("resource_group", "default"),
                                resource_group_type="compute",
                                rpc_listen_ip=comp_ips["internal"],
                                container_port_range=comp_config.get(
                                    "container_port_range", [30000, 31000]
                                ),
                                public_host=comp_config.get("public_host"),
                                scratch_type=comp_config.get("scratch_type", "hostfile"),
                                scratch_root=comp_config.get("scratch_root", "./scratches"),
                                scratch_size=comp_config.get("scratch_size", "50G"),
                            ),
                        },
                        internal_ip=comp_ips["internal"],
                        **pyinfra_opts,
                    )
                )

        # Helper to select nodes for a service
        def select_nodes_for(service: str) -> list:
            """Return mgmt node tuples hosting a given service"""
            hostnames = placement.get(service, [])
            if not hostnames:
                return []
            ssh_targets = set()
            for h in hostnames:
                node_data = get_node_info(h)
                ssh_target = (
                    f"{node_data['ssh_ip']}:{node_data['ssh_port']}"
                    if node_data["ssh_port"] != 22
                    else node_data["ssh_ip"]
                )
                ssh_targets.add(ssh_target)
            return [node for node in mgmt if node and node[0] in ssh_targets]

        # Build service group mappings
        postgres_ha = select_nodes_for("halfstack")
        etcd_ha = select_nodes_for("halfstack")
        redis_ha = select_nodes_for("halfstack")
        mgr = select_nodes_for("manager")
        web = select_nodes_for("webserver")
        sp = select_nodes_for("storage_proxy")
        # App Proxy: support split deployment with fallback to legacy
        apc = select_nodes_for("appproxy_coordinator") or select_nodes_for("appproxy")
        apw = select_nodes_for("appproxy_worker") or select_nodes_for("appproxy")
        cp = select_nodes_for("control_panel")
        # Collect all nodes with any dashboard service (for backward compatibility)
        # Use mgmt nodes that have any dashboard service in their services dict
        dashboard = [
            node
            for node in mgmt
            if node
            and any(
                svc in node[1].get("services", {})
                for svc in ["prometheus", "grafana", "loki", "otel_collector", "pyroscope"]
            )
        ]
        sftp = [
            node
            for node in mgmt
            if "agent" in node[1].get("services", {})
            and node[1]["services"]["agent"].resource_group_type == "storage"
        ]

        # Create individual manager nodes for mgr1, mgr2, mgr3
        mgr_individual = [[mgr[i]] if i < len(mgr) else [] for i in range(max(3, len(mgr)))]

        return {
            # Node lists
            "mgmt": mgmt,
            "compute": compute,
            "agent": compute,
            # Halfstack services
            "postgres_ha": postgres_ha,
            "etcd_ha": etcd_ha,
            "redis_ha": redis_ha,
            # Core services
            "mgr": mgr,
            "mgr1": mgr_individual[0] if len(mgr_individual) > 0 else [],
            "mgr2": mgr_individual[1] if len(mgr_individual) > 1 else [],
            "mgr3": mgr_individual[2] if len(mgr_individual) > 2 else [],
            "web": web,
            "sp": sp,
            "apc": apc,
            "apw": apw,
            "cp": cp,
            "sftp": sftp,
            "dashboard": dashboard,
            "tmp": mgr[:1] if mgr else [],
            # Config objects
            "postgresHAConfig": postgresHAConfig,
            "redisHAConfig": redisHAConfig,
            "etcdHAConfig": etcdHAConfig,
            "backendAICoreConfig": backendAICoreConfig,
            "licenseServerConfig": licenseServerConfig,
            "webserverConfig": webserverConfig,
            "hiveGatewayConfig": hiveGatewayConfig,
            "storageProxyConfigShared": storageProxyConfigShared,
            "appProxyConfig": appProxyConfig,
            "controlPanelConfig": controlPanelConfig,
            "fastTrackConfig": fastTrackConfig,
            "harborRegistryConfig": None,
            "rtunConfig": None,
            "prometheusConfig": prometheusConfig,
            "grafanaConfig": grafanaConfig,
            "lokiConfig": lokiConfig,
            "otelCollectorConfig": otelCollectorConfig,
            "pyroscopeConfig": pyroscopeConfig,
            # Helper functions
            "get_manager_config_for_node": get_manager_config_for_node,
            "get_storage_proxy_config_for_node": get_storage_proxy_config_for_node,
            "get_appproxy_config_for_node": get_appproxy_config_for_node,
            "create_datasources_config_for_node": create_datasources_config_for_node,
        }
