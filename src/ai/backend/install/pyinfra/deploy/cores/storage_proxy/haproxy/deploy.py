from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.operations import files

from ai.backend.install.pyinfra.exceptions import ConfigurationError, DeploymentError
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class StorageProxyHAProxyDeploy(BaseDockerComposeDeploy):
    """Deploy HAProxy load balancer for Storage Proxy cluster using Docker Compose."""

    # Class constants
    SERVICE_NAME = "sp_haproxy-default"
    HALFSTACK_DIR = "halfstack"
    SSL_CERT_DIR = "ssl_cert"

    def __init__(self, host_data: Any) -> None:
        """Initialize Storage Proxy HAProxy deployment configuration.

        Args:
            host_data: Host-specific configuration data containing service configs

        Raises:
            ConfigurationError: If required configuration values are missing
        """
        super().__init__()
        self._init_user_configs(host_data)
        self._init_service_configs(host_data)
        self._validate_config()

    def _init_user_configs(self, host_data: Any) -> None:
        """Initialize user and directory configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

    def _init_service_configs(self, host_data: Any) -> None:
        """Initialize service-related configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.config_storage_proxy = host_data.services["storage_proxy"]

        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.HALFSTACK_DIR}/{self.service_name}")
        self.service_ip = host_data.host

    def _validate_config(self) -> None:
        """Validate required configuration values.

        Raises:
            ConfigurationError: If required ports are not configured
        """
        # Validate HAProxy service port
        if self.config_storage_proxy.haproxy_service_port is None:
            raise ConfigurationError(
                "storage_proxy.haproxy_service_port is required for HAProxy deployment but not set. "
                "Please set this configuration value before deploying HAProxy."
            )

        # Validate HAProxy manager service port
        if self.config_storage_proxy.haproxy_manager_service_port is None:
            raise ConfigurationError(
                "storage_proxy.haproxy_manager_service_port is required for HAProxy deployment but not set. "
                "Please set this configuration value before deploying HAProxy."
            )

    def _get_storage_proxy_cluster_nodes(self) -> list[dict[str, Any]]:
        """Get storage proxy cluster nodes from configuration.

        Returns:
            List of cluster node configurations with name, hostname, and IP

        Note:
            Falls back to single node mode if cluster_nodes is not configured
        """
        cluster_nodes = getattr(self.config_storage_proxy, "cluster_nodes", [])

        if not cluster_nodes:
            # Fallback for single node mode
            logger.info("No cluster_nodes configured, using single node mode")
            return [{"name": "storage-proxy_1", "hostname": "bai-sp1", "ip": self.service_ip}]

        return cluster_nodes

    def _create_haproxy_cfg(self) -> None:
        """Create HAProxy configuration file from template.

        Raises:
            DeploymentError: If configuration file creation fails
        """
        try:
            files.template(
                name="Create haproxy.cfg",
                src=str(self.locate_template("haproxy.cfg.j2")),
                dest=f"{self.service_dir}/haproxy.cfg",
                # jinja2 context
                storageproxy_port=self.config_storage_proxy.port,
                storageproxy_manager_port=self.config_storage_proxy.manager_port,
                haproxy_service_port=self.config_storage_proxy.haproxy_service_port,
                storage_proxy_nodes=self._get_storage_proxy_cluster_nodes(),
            )
        except Exception as e:
            error_msg = f"Failed to create haproxy.cfg: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def install(self) -> None:
        """Install and configure Storage Proxy HAProxy service.

        Creates directories, generates configurations, loads Docker image,
        and starts the Docker Compose service.

        Raises:
            DeploymentError: If any installation step fails
        """
        try:
            self.create_directories(
                dirs=[str(self.service_dir), f"{self.home_dir}/{self.SSL_CERT_DIR}"]
            )
            self.create_docker_compose_yaml(
                home_dir=self.home_dir,
                service_ip=self.service_ip,
                service_port=self.config_storage_proxy.haproxy_service_port,
                manager_service_port=self.config_storage_proxy.haproxy_manager_service_port,
                storage_proxy_nodes=self._get_storage_proxy_cluster_nodes(),
                haproxy_image=self.config_storage_proxy.haproxy_container_image,
            )
            self._create_haproxy_cfg()
            self.create_service_manage_scripts()
            self.load_image(container_image=self.config_storage_proxy.haproxy_container_image)
            self.start_service()
        except DeploymentError:
            raise
        except Exception as e:
            error_msg = f"Failed to install {self.service_name}: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def remove(self) -> None:
        """Remove Storage Proxy HAProxy service and clean up resources.

        Stops the Docker Compose service before removing directories.

        Raises:
            DeploymentError: If removal fails
        """
        try:
            self.stop_service()
            self.remove_directories()
        except Exception as e:
            error_msg = f"Failed to remove {self.service_name}: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e


def main() -> None:
    """Main entry point for Storage Proxy HAProxy deployment."""
    deploy_mode = host.data.get("mode", "install")
    StorageProxyHAProxyDeploy(host.data).run(deploy_mode)


main()
