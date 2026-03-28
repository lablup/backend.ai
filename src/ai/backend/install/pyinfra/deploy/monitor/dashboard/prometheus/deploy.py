from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.deploy.cores.appproxy.constants import WORKER_TYPES
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PrometheusDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "prometheus"
        self.service_home = Path(f"{self.home_dir}/dashboard/prometheus")
        self.service_dir = self.service_home
        self.host_data = host_data

        self.config = host_data.services["prometheus"]

        # Set data_dir: use config value if provided, otherwise default to {home_dir}/.data/prometheus
        self.data_dir = self.config.data_dir or f"{self.home_dir}/.data/prometheus"

        # Detect HA configuration and collect exporter targets (using IPs)
        self.postgres_config = self._get_postgres_exporter_targets()
        self.redis_exporter_config = self._get_redis_exporter_targets()
        self.etcd_targets = self._get_etcd_targets()

        self.traefik_targets = self._get_traefik_targets()

        # Blackbox Exporter probe targets
        self.blackbox_http_targets = self._get_blackbox_http_targets()
        self.blackbox_tcp_targets = self._get_blackbox_tcp_targets()

    def _get_postgres_exporter_targets(self) -> None:
        """Get all PostgreSQL Exporter targets using IPs (HA) or configured host (single-node)"""
        exporter_targets = []
        patroni_targets = []

        # Check for HA mode using multiple methods
        is_ha_mode = False
        if hasattr(self.host_data, "services"):
            # Method 1: Check for postgres_ha service
            if "postgres_ha" in self.host_data.services:
                is_ha_mode = True
            # Method 2: Check for postgres service with HA indicators
            elif "postgres" in self.host_data.services:
                postgres_svc = self.host_data.services["postgres"]
                if hasattr(postgres_svc, "cluster_nodes") or hasattr(postgres_svc, "ha_enabled"):
                    is_ha_mode = True

        if is_ha_mode:
            # Get cluster nodes from HA configuration
            postgres_ha_config = self.host_data.services.get("postgres_ha")
            if postgres_ha_config and hasattr(postgres_ha_config, "cluster_nodes"):
                for node_config in postgres_ha_config.cluster_nodes:
                    # Use IP if available, fallback to hostname
                    host = node_config.ip if hasattr(node_config, "ip") else node_config.hostname
                    exporter_targets.append(f"{host}:{self.config.db_exporter_port}")
                    # Add Patroni API endpoints
                    patroni_port = (
                        node_config.pg_api_port if hasattr(node_config, "pg_api_port") else 8111
                    )
                    patroni_targets.append(f"{host}:{patroni_port}")
            else:
                exporter_targets.append(
                    f"{self.resolve_host(self.config.db_exporter_host)}:{self.config.db_exporter_port}"
                )
        else:
            # Single-node mode: use configured VIP/host
            exporter_targets.append(
                f"{self.resolve_host(self.config.db_exporter_host)}:{self.config.db_exporter_port}"
            )

        return {
            "exporter_targets": list(set(exporter_targets)),
            "patroni_targets": list(set(patroni_targets)),
        }

    def _get_redis_exporter_targets(self) -> None:
        """Get Redis Exporter address and Redis instance targets for multi-target pattern"""
        exporter_address = None
        redis_instances = []

        # Check for HA mode
        is_ha_mode = False
        if hasattr(self.host_data, "services"):
            if "redis_ha" in self.host_data.services:
                is_ha_mode = True
            elif "redis" in self.host_data.services:
                redis_svc = self.host_data.services["redis"]
                if hasattr(redis_svc, "cluster_nodes") or hasattr(redis_svc, "ha_enabled"):
                    is_ha_mode = True

        if is_ha_mode:
            # Multi-target: single exporter monitoring multiple Redis instances
            # Redis Exporter is installed on the same host as Prometheus
            exporter_host = self.host_ip
            exporter_address = f"{exporter_host}:{self.config.redis_exporter_port}"

            redis_ha_config = self.host_data.services.get("redis_ha")
            if redis_ha_config and hasattr(redis_ha_config, "cluster_nodes"):
                for node_config in redis_ha_config.cluster_nodes:
                    host_addr = (
                        node_config.ip if hasattr(node_config, "ip") else node_config.hostname
                    )
                    port = node_config.port if hasattr(node_config, "port") else 8112
                    redis_instances.append(f"redis://{host_addr}:{port}")
        else:
            # Single-node: direct exporter connection
            exporter_address = f"{self.resolve_host(self.config.redis_exporter_host)}:{self.config.redis_exporter_port}"

        return {
            "exporter_address": exporter_address,
            "redis_instances": redis_instances,
        }  # Remove duplicates

    def _get_etcd_targets(self) -> None:
        """Get all ETCD targets using IPs (HA) or configured host (single-node)"""
        targets = []

        # In HA mode, add individual node instances
        if hasattr(self.host_data, "services") and (
            "etcd_ha" in self.host_data.services or "postgres_ha" in self.host_data.services
        ):
            # Get cluster nodes from ETCD HA configuration
            etcd_ha_config = self.host_data.services.get("etcd_ha")
            if etcd_ha_config and hasattr(etcd_ha_config, "cluster_nodes"):
                for node_config in etcd_ha_config.cluster_nodes:
                    # Use client_ip and client_port for etcd metrics endpoint (not peer port!)
                    host = (
                        node_config.client_ip
                        if hasattr(node_config, "client_ip")
                        else node_config.hostname
                    )
                    port = (
                        node_config.client_port
                        if hasattr(node_config, "client_port")
                        else self.config.etcd_port
                    )
                    targets.append(f"{host}:{port}")
            # Also try postgres_ha cluster nodes (ETCD runs on same nodes)
            elif "postgres_ha" in self.host_data.services:
                postgres_ha_config = self.host_data.services.get("postgres_ha")
                if postgres_ha_config and hasattr(postgres_ha_config, "cluster_nodes"):
                    for node_config in postgres_ha_config.cluster_nodes:
                        # Use IP if available, fallback to hostname
                        host = (
                            node_config.ip if hasattr(node_config, "ip") else node_config.hostname
                        )
                        targets.append(f"{host}:{self.config.etcd_port}")
            else:
                targets.append(
                    f"{self.resolve_host(self.config.etcd_host)}:{self.config.etcd_port}"
                )
        else:
            # Single-node mode: use configured VIP/host
            targets.append(f"{self.resolve_host(self.config.etcd_host)}:{self.config.etcd_port}")

        return list(set(targets))  # Remove duplicates

    def _get_traefik_targets(self) -> None:
        """Get Traefik metrics targets from appproxy configuration."""
        targets: list[str] = []
        appproxy_config = self.host_data.services.get("appproxy")
        if not appproxy_config:
            return targets

        default_api_ports = {wt: 9090 + i for i, wt in enumerate(WORKER_TYPES)}
        for worker_type, default_port in default_api_ports.items():
            hostname = getattr(appproxy_config, f"worker_{worker_type}_advertised_hostname", None)
            port = getattr(appproxy_config, f"worker_{worker_type}_traefik_api_port", default_port)
            if hostname:
                targets.append(f"{hostname}:{port}")
        return targets

    def _get_blackbox_http_targets(self) -> None:
        """Get HTTP probe targets for Blackbox Exporter from inventory."""
        targets = []

        # Manager endpoints
        manager_config = self.host_data.services.get("manager")
        if manager_config:
            if hasattr(manager_config, "cluster_nodes") and manager_config.cluster_nodes:
                for node in manager_config.cluster_nodes:
                    ip = node.get("ip", node.get("hostname", ""))
                    targets.append(f"http://{ip}:{manager_config.port}")
            else:
                host_addr = manager_config.client_connect_ip
                targets.append(f"http://{host_addr}:{manager_config.port}")
            # HAProxy VIP probe (HA mode)
            haproxy_port = getattr(manager_config, "haproxy_service_port", None)
            if haproxy_port:
                targets.append(f"http://{manager_config.client_connect_ip}:{haproxy_port}")

        # Webserver endpoints
        webserver_config = self.host_data.services.get("webserver")
        if webserver_config:
            if hasattr(webserver_config, "cluster_nodes") and webserver_config.cluster_nodes:
                for node in webserver_config.cluster_nodes:
                    ip = node.get("ip", node.get("hostname", ""))
                    targets.append(f"http://{ip}:{webserver_config.port}")
                # HAProxy probes per node
                haproxy_port = getattr(webserver_config, "haproxy_service_port", None)
                if haproxy_port:
                    for node in webserver_config.cluster_nodes:
                        ip = node.get("ip", node.get("hostname", ""))
                        targets.append(f"http://{ip}:{haproxy_port}")
            else:
                port = (
                    getattr(webserver_config, "haproxy_service_port", None) or webserver_config.port
                )
                # Webserver is co-located with manager in single-node deployments
                host_addr = manager_config.client_connect_ip if manager_config else self.host_ip
                targets.append(f"http://{host_addr}:{port}")

        # AppProxy worker endpoints
        appproxy_config = self.host_data.services.get("appproxy")
        if appproxy_config:
            for attr_suffix in [
                "interactive_advertised_hostname",
                "tcp_advertised_hostname",
                "inference_advertised_hostname",
            ]:
                hostname = getattr(appproxy_config, f"worker_{attr_suffix}", None)
                port = getattr(
                    appproxy_config,
                    f"worker_{attr_suffix.replace('advertised_hostname', 'port')}",
                    None,
                )
                if hostname and port:
                    targets.append(f"http://{hostname}:{port}")
            # AppProxy Coordinator
            coordinator_hostname = getattr(appproxy_config, "coordinator_hostname", None)
            coordinator_port = getattr(appproxy_config, "coordinator_port", None)
            if coordinator_hostname and coordinator_port:
                targets.append(f"http://{coordinator_hostname}:{coordinator_port}/status")

        # Storage Proxy endpoints
        storage_proxy_config = self.host_data.services.get("storage_proxy")
        if storage_proxy_config:
            cluster_nodes = getattr(storage_proxy_config, "cluster_nodes", [])
            if cluster_nodes:
                # HA mode: per-node client and manager-facing ports
                mgr_port = (
                    getattr(storage_proxy_config, "manager_facing_port", None)
                    or storage_proxy_config.manager_port
                )
                for node in cluster_nodes:
                    ip = node.get("ip", node.get("hostname", ""))
                    targets.append(f"http://{ip}:{storage_proxy_config.port}")
                    targets.append(f"http://{ip}:{mgr_port}")
                # HAProxy VIP from client_endpoint and manager_endpoint
                client_endpoint = getattr(storage_proxy_config, "client_endpoint", "")
                if client_endpoint:
                    targets.append(client_endpoint)
                manager_endpoint = getattr(storage_proxy_config, "manager_endpoint", "")
                if manager_endpoint:
                    targets.append(manager_endpoint)
            else:
                host_addr = storage_proxy_config.announce_internal_host
                targets.append(f"http://{host_addr}:{storage_proxy_config.port}")
                targets.append(f"http://{host_addr}:{storage_proxy_config.manager_port}")

        # Hive Gateway (Apollo Router / Hive Gateway) — no HTTP health endpoint
        # on the main GraphQL port; monitored via TCP probe instead.

        # Control Panel (HTTPS with self-signed cert, insecure_skip_verify handles it)
        control_panel_config = self.host_data.services.get("control_panel")
        if control_panel_config:
            # Control Panel is co-located with manager
            host_addr = manager_config.client_connect_ip if manager_config else self.host_ip
            targets.append(f"https://{host_addr}:{control_panel_config.port}")

        # FastTrack
        fasttrack_config = self.host_data.services.get("fasttrack")
        if fasttrack_config:
            targets.append(fasttrack_config.endpoint)

        # License Server (HTTPS with self-signed cert)
        license_server_config = self.host_data.services.get("license_server")
        if license_server_config:
            targets.append(f"https://{license_server_config.hostname}:{license_server_config.port}")

        # Harbor (container registry)
        registry_name = getattr(self.host_data, "registry_name", None)
        registry_port = getattr(self.host_data, "registry_port", None)
        if registry_name and registry_port and "harbor" in self.host_data.services:
            targets.append(f"http://{registry_name}:{registry_port}")

        # Patroni (PostgreSQL HA cluster manager REST API)
        postgres_ha_config = self.host_data.services.get("postgres_ha")
        if postgres_ha_config and hasattr(postgres_ha_config, "cluster_nodes"):
            for node in postgres_ha_config.cluster_nodes:
                ip = getattr(node, "ip", None) or getattr(node, "hostname", "")
                patroni_port = getattr(node, "pg_api_port", 8111)
                targets.append(f"http://{ip}:{patroni_port}")

        # Monitoring services (co-located with Prometheus on the dashboard node)
        dashboard_host = self.host_ip
        targets.append(f"http://{dashboard_host}:{self.config.port}/-/healthy")

        grafana_config = self.host_data.services.get("grafana")
        if grafana_config:
            targets.append(f"http://{dashboard_host}:{grafana_config.port}/api/health")

        loki_config = self.host_data.services.get("loki")
        if loki_config:
            targets.append(f"http://{dashboard_host}:{loki_config.port}/ready")

        otel_config = self.host_data.services.get("otel_collector")
        if otel_config:
            targets.append(f"http://{dashboard_host}:{otel_config.health_port}")

        pyroscope_config = self.host_data.services.get("pyroscope")
        if pyroscope_config:
            targets.append(f"http://{dashboard_host}:{pyroscope_config.port}")

        return sorted(set(targets))

    def _get_blackbox_tcp_targets(self) -> None:
        """Get TCP probe targets for Blackbox Exporter from inventory."""
        targets = []

        # Agent RPC and Watcher ports from compute node targets
        for host_addr in self.config.compute_node_targets:
            targets.append(f"{host_addr}:6001")
            targets.append(f"{host_addr}:6009")

        # Hive Gateway (Apollo Router / Hive Gateway) — GraphQL port only
        # accepts POST; use TCP connectivity check instead of HTTP probe.
        hive_gateway_config = self.host_data.services.get("hive_gateway")
        if hive_gateway_config:
            manager_config = self.host_data.services.get("manager")
            cluster_nodes = getattr(hive_gateway_config, "cluster_nodes", [])
            if cluster_nodes:
                for node in cluster_nodes:
                    ip = getattr(node, "ip", None) or getattr(node, "hostname", "")
                    targets.append(f"{ip}:{hive_gateway_config.port}")
            else:
                gw_host = manager_config.client_connect_ip if manager_config else self.host_ip
                targets.append(f"{gw_host}:{hive_gateway_config.port}")

        # PostgreSQL
        postgres_config = self.host_data.services.get("postgres")
        postgres_ha_config = self.host_data.services.get("postgres_ha")
        if postgres_ha_config:
            # HA: VIP active/standby ports + per-node SQL ports
            if postgres_config:
                targets.append(f"{postgres_config.hostname}:{postgres_ha_config.pg_active_port}")
                targets.append(f"{postgres_config.hostname}:{postgres_ha_config.pg_standby_port}")
            for node in postgres_ha_config.cluster_nodes:
                ip = getattr(node, "ip", None) or getattr(node, "hostname", "")
                sql_port = getattr(node, "pg_sql_port", 8101)
                targets.append(f"{ip}:{sql_port}")
        elif postgres_config:
            targets.append(f"{postgres_config.hostname}:{postgres_config.port}")

        # Redis
        redis_config = self.host_data.services.get("redis")
        redis_ha_config = self.host_data.services.get("redis_ha")
        if redis_ha_config:
            # HA: VIP via HAProxy + per-node ports
            if redis_config:
                targets.append(f"{redis_config.hostname}:{redis_ha_config.haproxy_service_port}")
            for node in redis_ha_config.cluster_nodes:
                ip = getattr(node, "ip", None) or getattr(node, "hostname", "")
                port = getattr(node, "port", 8112)
                targets.append(f"{ip}:{port}")
        elif redis_config:
            targets.append(f"{redis_config.hostname}:{redis_config.port}")

        return sorted(set(targets))

    def create_prometheus_yml(self) -> None:
        files.template(
            name="Create prometheus.yml",
            src=str(Path(__file__).parent / "templates/prometheus.yml.j2"),
            dest=f"{self.service_home}/prometheus.yml",
            user=self.user,
            mode="644",
            # Jinja2 context (resolve host.docker.internal to actual host IP)
            http_sd_host=self.resolve_host(self.config.http_sd_host),
            http_sd_port=self.config.http_sd_port,
            etcd_host=self.resolve_host(self.config.etcd_host),
            etcd_port=self.config.etcd_port,
            redis_exporter_host=self.resolve_host(self.config.redis_exporter_host),
            redis_exporter_port=self.config.redis_exporter_port,
            db_exporter_host=self.resolve_host(self.config.db_exporter_host),
            db_exporter_port=self.config.db_exporter_port,
            # HA-aware exporter targets
            postgres_exporter_targets=self.postgres_config.get("exporter_targets", []),
            patroni_targets=self.postgres_config.get("patroni_targets", []),
            redis_exporter_address=self.redis_exporter_config.get("exporter_address"),
            redis_instances=self.redis_exporter_config.get("redis_instances", []),
            etcd_targets=self.etcd_targets,
            traefik_targets=self.traefik_targets,
            # Blackbox Exporter targets
            blackbox_exporter_host=self.resolve_host(self.config.blackbox_exporter_host),
            blackbox_exporter_port=self.config.blackbox_exporter_port,
            blackbox_http_targets=self.blackbox_http_targets,
            blackbox_tcp_targets=self.blackbox_tcp_targets,
        )

    def create_targets_json(self) -> None:
        if not self.config.dcgm_exporter_targets:
            print(
                "  [INFO] No DCGM exporter targets configured (no GPU compute nodes in inventory)"
            )
        files.template(
            name="Create targets.json for service discovery",
            src=str(Path(__file__).parent / "templates/targets.json.j2"),
            dest=str(self.service_home / "targets.json"),
            user=self.user,
            mode="644",
            # Jinja2 context - compute node targets from PrometheusConfig
            dcgm_exporter_targets=self.config.dcgm_exporter_targets,
            dcgm_exporter_port=self.config.dcgm_exporter_port,
        )

    def change_permissions(self) -> None:
        data_dir = self.data_dir
        server.shell(
            name="Set prometheus data directory permissions for nobody:nogroup",
            commands=[
                # Ensure directory exists
                f"mkdir -p {data_dir}",
                # Set ownership to nobody:nogroup (65534:65534) - force if needed
                f"chown -R 65534:65534 {data_dir} || echo 'Failed to change ownership, continuing...'",
                # Set appropriate permissions for nobody user
                f"chmod -R 755 {data_dir}",
            ],
            _sudo=True,
        )

    def install(self) -> None:
        self.create_directories([self.service_home, self.data_dir])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            prometheus_image_tag=self.config.prometheus_image_tag,
            prometheus_port=self.config.port,
            retention_days=self.config.retention_days,
        )
        self.create_prometheus_yml()
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
            data_dir=self.data_dir,
        )
        self.create_targets_json()
        self.create_service_manage_scripts()
        self.change_permissions()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop Prometheus service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.data_dir, self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = PrometheusDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
