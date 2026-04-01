from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.exceptions import ConfigurationError, DeploymentError
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class ManagerHAProxyDeploy(BaseDockerComposeDeploy):
    # Class constants
    SERVICE_NAME = "mgr_haproxy-default"
    HALFSTACK_DIR = "halfstack"
    SSL_CERT_DIR = "ssl_cert/current"

    # Default fallback node configuration for single-node mode
    DEFAULT_MANAGER_NODE = {
        "name": "manager_1",
        "hostname": "bai-m1",
    }

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host.data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config_manager = host_data.services["manager"]
        self._validate_config()

        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.HALFSTACK_DIR}/{self.service_name}")

        self.service_ip = host.data.host
        self.service_port = self.config_manager.haproxy_service_port

    def _validate_config(self) -> None:
        """Validate that all required configuration values are set."""
        if self.config_manager.haproxy_service_port is None:
            raise ConfigurationError(
                "manager.haproxy_service_port is required for HAProxy deployment but not set. "
                "Please set this configuration value before deploying HAProxy."
            )

    def _get_manager_cluster_nodes(self) -> None:
        """Get manager cluster nodes from config.

        Returns:
            list: List of manager cluster node configurations. Falls back to
                  single-node configuration if cluster_nodes is not defined.
        """
        cluster_nodes = getattr(self.config_manager, "cluster_nodes", [])

        if not cluster_nodes:
            # Fallback for single node mode
            fallback_node = self.DEFAULT_MANAGER_NODE.copy()
            fallback_node["ip"] = self.service_ip
            return [fallback_node]

        return cluster_nodes

    def _create_haproxy_cfg(self, manager_nodes: list) -> None:
        """Create HAProxy configuration file.

        Args:
            manager_nodes: List of manager cluster node configurations.

        Raises:
            DeploymentError: If HAProxy configuration creation fails.
        """
        try:
            files.template(
                name="Create haproxy.cfg",
                src=self.locate_template("haproxy.cfg.j2"),
                dest=f"{self.service_dir}/haproxy.cfg",
                manager_port=self.config_manager.port,
                haproxy_service_port=self.config_manager.haproxy_service_port,
                manager_nodes=manager_nodes,
            )

        except Exception as e:
            error_msg = f"Failed to create HAProxy configuration: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def install(self) -> None:
        """Install and configure the HAProxy service for Manager load balancing."""
        # Get manager nodes once to avoid duplicate calls
        manager_nodes = self._get_manager_cluster_nodes()

        self.create_directories(
            dirs=[Path(self.service_dir), Path(f"{self.home_dir}/{self.SSL_CERT_DIR}")]
        )
        self.create_docker_compose_yaml(
            home_dir=self.home_dir,
            service_ip=self.service_ip,
            service_port=self.service_port,
            manager_nodes=manager_nodes,
            haproxy_image=self.config_manager.haproxy_container_image,
        )
        self._create_haproxy_cfg(manager_nodes)
        self.create_service_manage_scripts()
        self.load_image(container_image=self.config_manager.haproxy_container_image)
        self.start_service()

    def remove(self) -> None:
        """Remove the HAProxy service and clean up all related files and configurations."""
        try:
            # Check if service directory exists before trying to stop
            if self.service_dir.exists():
                server.shell(
                    name="Stop docker compose service",
                    commands=[f"cd {self.service_dir} && {self.docker_compose_cmd} down"],
                )
            self.remove_directories()

        except Exception as e:
            error_msg = f"Failed to remove HAProxy service: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    ManagerHAProxyDeploy(host.data).run(deploy_mode)


main()
