from io import StringIO
from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.operations import files

from ai.backend.install.pyinfra.exceptions import ConfigurationError, DeploymentError
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy

# Directory containing pre-downloaded supergraph schema files
SCHEMAS_DIR = Path(__file__).parent / "schemas"


class HiveGatewayDeploy(BaseDockerComposeDeploy):
    """Deploy GraphQL Federation Router (Hive Gateway or Apollo Router)."""

    HALFSTACK_DIR = "halfstack"

    def __init__(self, host_data: Any) -> None:
        super().__init__()
        self._init_configs(host_data)
        self._validate_config()

    def _init_configs(self, host_data: Any) -> None:
        """Initialize configuration from host data."""
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user

        self.config = host_data.services["hive_gateway"]
        self.config_manager = host_data.services["manager"]
        self.config_bai_core = host_data.services["bai_core"]
        self.bai_version = self.config_bai_core.version

        # Service directory naming: {router_type}-{name} for clear identification on deployed servers
        service_name_suffix = getattr(self.config, "name", "default")
        service_prefix = "apollo_router" if self.config.router_type == "apollo" else "hive_gateway"
        self.service_name = f"{service_prefix}-{service_name_suffix}"
        self.service_dir: Path = Path(f"{self.home_dir}/{self.HALFSTACK_DIR}/{self.service_name}")

        # Determine Manager endpoint (HAProxy or direct)
        manager_port = self.config_manager.haproxy_service_port or self.config_manager.port
        self.manager_graphql_port = self.config.manager_graphql_port or manager_port
        self.manager_endpoint = f"{self.config.manager_hostname}:{self.manager_graphql_port}"

        # Determine actual Manager IP for extra_hosts
        self.manager_ip = self.config_manager.client_connect_ip

        # HA mode detection and port calculation
        self.is_ha_mode = bool(self.config.cluster_nodes and len(self.config.cluster_nodes) > 1)
        if self.is_ha_mode:
            # HA mode: HAProxy on service_port, Gateway on service_port+1
            self.haproxy_port = self.config.port  # External port (4000)
            self.gateway_port = self.config.port + 1  # Backend port (4001)
        else:
            # Single-node: Gateway exposes service_port directly
            self.gateway_port = self.config.port
            self.haproxy_port = None

    def _validate_config(self) -> None:
        """Validate required configuration."""
        if not self.config.enabled:
            raise ConfigurationError(
                "GraphQL Router is not enabled. Set hive_gateway.enabled = True in config."
            )

        # Validate router_type
        if self.config.router_type not in ("hive", "apollo"):
            raise ConfigurationError(
                f"Invalid router_type '{self.config.router_type}'. Must be 'hive' or 'apollo'."
            )

        # Validate cluster_nodes configuration
        if self.config.cluster_nodes and not self.is_ha_mode:
            raise ConfigurationError(
                f"cluster_nodes has {len(self.config.cluster_nodes)} node(s) but HA mode requires "
                f"at least 2. Either add more nodes or remove cluster_nodes entirely for single-node mode."
            )
        if self.is_ha_mode and not self.config.haproxy_container_image:
            raise ConfigurationError(
                "HAProxy container image is required for HA mode but not configured."
            )

        # supergraph_path is optional - schema can be auto-detected from schemas/ directory

    @property
    def is_apollo(self) -> bool:
        """Check if this deployment uses Apollo Router."""
        return self.config.router_type == "apollo"

    @property
    def active_image(self) -> str:
        """Return the container image for the currently configured router type."""
        return self.config.apollo_container_image if self.is_apollo else self.config.container_image

    def _create_gateway_config(self) -> None:
        """Create gateway.config.ts from template or copy existing (Hive Gateway only)."""
        if self.config.gateway_config_path:
            # Copy user-provided config
            files.put(
                name="Deploy gateway.config.ts",
                src=self.config.gateway_config_path,
                dest=f"{self.service_dir}/gateway.config.ts",
                user=self.user,
                mode="0644",
            )
        else:
            # Use template
            files.template(
                name="Create gateway.config.ts",
                src=str(self.locate_template("gateway.config.ts.j2")),
                dest=f"{self.service_dir}/gateway.config.ts",
                user=self.user,
                mode="0644",
                manager_hostname=self.config.manager_hostname,
                manager_graphql_port=self.manager_graphql_port,
            )

    def _create_router_config(self) -> None:
        """Create router.yaml from template (Apollo Router only)."""
        files.template(
            name="Create router.yaml for Apollo Router",
            src=str(self.locate_template("router.yaml.j2")),
            dest=f"{self.service_dir}/router.yaml",
            user=self.user,
            mode="0644",
            manager_hostname=self.config.manager_hostname,
            manager_graphql_port=self.manager_graphql_port,
            advertised_hostname=self.config.advertised_hostname,
            service_port=self.config.port,
        )

    def _find_version_schema(self) -> Path | None:
        """Find the supergraph schema file matching the BAI version."""
        # Try exact version match first
        exact_match = SCHEMAS_DIR / f"supergraph-{self.bai_version}.graphql"
        if exact_match.exists():
            return exact_match

        # Try minor version match (e.g., 25.18.1 -> 25.18.0)
        version_parts = self.bai_version.split(".")
        if len(version_parts) >= 2:
            minor_pattern = f"supergraph-{version_parts[0]}.{version_parts[1]}."
            for schema_file in sorted(SCHEMAS_DIR.glob(f"{minor_pattern}*.graphql"), reverse=True):
                return schema_file

        return None

    def _replace_schema_endpoints(self, content: str) -> str:
        """Replace hardcoded endpoints in supergraph schema with configured values.

        The upstream supergraph.graphql contains development endpoints like:
            http://host.docker.internal:8091/admin/gql

        This replaces them with the actual manager endpoint from configuration.
        """
        # Default development endpoint in upstream schemas
        dev_endpoint = "host.docker.internal:8091"
        actual_endpoint = f"{self.config.manager_hostname}:{self.manager_graphql_port}"

        if dev_endpoint in content:
            logger.info(f"Replacing schema endpoint: {dev_endpoint} -> {actual_endpoint}")
            content = content.replace(dev_endpoint, actual_endpoint)
        elif actual_endpoint not in content:
            # Neither dev endpoint nor actual endpoint found - schema may be misconfigured
            logger.warning(
                f"Schema does not contain expected endpoint '{dev_endpoint}' or '{actual_endpoint}'. "
                "Verify supergraph.graphql has correct Manager GraphQL URLs."
            )

        return content

    def _create_supergraph(self) -> None:
        """Deploy supergraph.graphql schema file.

        Priority:
        1. User-provided supergraph_path in config
        2. Pre-downloaded schema matching BAI version from schemas/ directory

        Note: Hardcoded development endpoints are automatically replaced with
        configured manager hostname and port.
        """
        schema_source: Path | None = None
        source_desc: str = ""

        if self.config.supergraph_path:
            schema_source = Path(self.config.supergraph_path)
            source_desc = "user-provided"
        else:
            schema_source = self._find_version_schema()
            if schema_source:
                source_desc = schema_source.name

        if not schema_source or not schema_source.exists():
            raise ConfigurationError(
                f"No supergraph schema found for BAI version {self.bai_version}. "
                f"Please provide 'supergraph_path' in config or download the schema to "
                f"{SCHEMAS_DIR}/supergraph-{self.bai_version}.graphql"
            )

        logger.info(f"Using supergraph schema: {source_desc}")

        # Read, transform, and deploy schema
        content = schema_source.read_text(encoding="utf-8")
        content = self._replace_schema_endpoints(content)

        files.put(
            name=f"Deploy supergraph.graphql ({source_desc})",
            src=StringIO(content),
            dest=f"{self.service_dir}/supergraph.graphql",
            user=self.user,
            mode="0644",
        )

    def _create_haproxy_config(self) -> None:
        """Create HAProxy configuration for HA mode."""
        if not self.is_ha_mode:
            return

        files.template(
            name="Create haproxy.cfg for HA mode",
            src=str(self.locate_template("haproxy.cfg.j2")),
            dest=f"{self.service_dir}/haproxy.cfg",
            user=self.user,
            mode="0644",
            cluster_nodes=self.config.cluster_nodes,
            gateway_port=self.gateway_port,
        )

    def _get_docker_compose_context(self) -> dict[str, Any]:
        """Get template context for docker-compose.yml."""
        return {
            "home_dir": self.home_dir,
            "service_port": self.config.port,
            "gateway_port": self.gateway_port,
            "haproxy_port": self.haproxy_port,
            "container_image": self.config.container_image,
            "manager_hostname": self.config.manager_hostname,
            "manager_ip": self.manager_ip,
            "manager_graphql_port": self.manager_graphql_port,
            # Router type selection
            "router_type": self.config.router_type,
            "apollo_container_image": self.config.apollo_container_image,
            # HA mode configuration
            "is_ha_mode": self.is_ha_mode,
            "cluster_nodes": self.config.cluster_nodes,
            "haproxy_container_image": self.config.haproxy_container_image,
        }

    def _load_images(self) -> None:
        """Load all required container images."""
        if self.is_apollo:
            # Load Apollo Router image
            self.load_image(
                container_image=self.config.apollo_container_image,
                local_archive_path=self.config.apollo_local_archive_path,
            )
        else:
            # Load Hive Gateway image
            self.load_image(
                container_image=self.config.container_image,
                local_archive_path=self.config.local_archive_path,
            )
        # Load HAProxy image for HA mode
        if self.is_ha_mode:
            self.load_image(
                container_image=self.config.haproxy_container_image,
                local_archive_path=self.config.haproxy_local_archive_path,
            )

    def install(self) -> None:
        """Install GraphQL Router service."""
        try:
            self.create_directories(dirs=[self.service_dir])

            # Create Docker Compose configuration
            self.create_env_file(
                manager_hostname=self.config.manager_hostname,
                port=self.config.port,
                container_image=self.active_image,
            )

            self.create_docker_compose_yaml(**self._get_docker_compose_context())

            # Deploy configuration files based on router type
            if self.is_apollo:
                self._create_router_config()
            else:
                self._create_gateway_config()
            self._create_supergraph()  # Deploy pre-downloaded supergraph schema
            self._create_haproxy_config()  # Only for HA mode

            # Create management scripts and load images
            self.create_service_manage_scripts(extra_context=self._get_docker_compose_context())
            self._load_images()

            self.start_service()

            router_name = "Apollo Router" if self.is_apollo else "Hive Gateway"
            mode_str = "HA mode with HAProxy" if self.is_ha_mode else "single-node mode"
            logger.info(
                f"{router_name} deployed successfully at port {self.config.port} ({mode_str})"
            )

        except ConfigurationError:
            raise
        except Exception as e:
            raise DeploymentError(f"Failed to deploy GraphQL Router: {e}") from e

    def update(self) -> None:
        """Update GraphQL Router configuration and restart."""
        try:
            self.stop_service()

            # Update configuration files based on router type
            if self.is_apollo:
                self._create_router_config()
            else:
                self._create_gateway_config()
            self._create_supergraph()
            self._create_haproxy_config()

            self.create_env_file(
                manager_hostname=self.config.manager_hostname,
                port=self.config.port,
                container_image=self.active_image,
            )
            self.create_docker_compose_yaml(**self._get_docker_compose_context())

            # Load images
            self._load_images()

            self.start_service()
        except Exception as e:
            raise DeploymentError(f"Failed to update GraphQL Router: {e}") from e

    def remove(self) -> None:
        """Remove GraphQL Router service."""
        try:
            self.stop_service()
            self.remove_directories()
        except Exception as e:
            raise DeploymentError(f"Failed to remove GraphQL Router: {e}") from e


def main() -> None:
    """Main entry point."""
    deploy_mode = host.data.get("mode", "install")
    HiveGatewayDeploy(host.data).run(deploy_mode)


main()
