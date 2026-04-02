from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.configs.halfstack import RedisHAClusterNodeConfig
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class RedisClusterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config = host_data.services["redis_ha"]
        self.redis_cluster_info = getattr(host_data, "redis_cluster_info", {})

        # Find current node in cluster configuration
        self.current_node = self._find_current_node()

        # Set up service and data directories
        self.service_dir = f"{self.home_dir}/halfstack/redis_cluster-{self.config.name}"
        self.data_dir = f"{self.home_dir}/.data/backend.ai/redis_cluster/{self.config.name}/redis{self.current_node.node_number}"

    def _find_current_node(self) -> RedisHAClusterNodeConfig:
        """
        Find the current node configuration from the cluster nodes list.

        Returns:
            The node configuration for the current host

        Raises:
            ValueError: If current host is not found in cluster configuration
        """
        if not self.redis_cluster_info:
            raise ValueError("redis_cluster_info is not provided in host data")

        node_name = self.redis_cluster_info.get("node_name")
        if not node_name:
            raise ValueError("node_name is not found in redis_cluster_info")

        for node in self.config.cluster_nodes:
            if node.hostname == node_name:
                return node

        raise ValueError(f"Current host {node_name} not found in Redis HA cluster configuration")

    def create_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = False
    ) -> None:
        """Override to set specific permissions for Redis data directory"""
        files.directory(path=self.service_dir, present=True)
        files.directory(path=self.data_dir, present=True, mode="777")

    def install(self) -> None:
        self.create_directories()

        # Determine if this is a slave node
        is_slave = self.current_node.node_number != 1
        master_node = self.config.get_master_node()

        # Create .env file
        self.create_env_file(
            config=self.config,
            current_node=self.current_node,
            master_node=master_node,
            data_dir=self.data_dir,
            home_dir=self.home_dir,
            target_uname=self.user,
            is_slave=is_slave,
        )

        # Create docker-compose.yml
        self.create_docker_compose_yaml(
            config=self.config,
            current_node=self.current_node,
            master_node=master_node,
            data_dir=self.data_dir,
            is_slave=is_slave,
        )

        self.create_service_manage_scripts(
            extra_context={
                "service_name": "redis",
                "config": self.config,
                "current_node": self.current_node,
            }
        )

        # Load and start service
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name=f"Stop Redis cluster service for node {self.current_node.node_number}",
            commands=[
                f"if [ -d {self.service_dir} ] && [ -f {self.service_dir}/stop.sh ]; then {self.service_dir}/stop.sh; fi"
            ],
        )
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RedisClusterDeploy(host.data).run(deploy_mode)


main()
