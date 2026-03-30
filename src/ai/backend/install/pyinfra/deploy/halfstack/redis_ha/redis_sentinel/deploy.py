from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.configs.halfstack import RedisHAClusterNodeConfig
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class RedisSentinelDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config = host_data.services["redis_ha"]
        self.redis_cluster_info = getattr(host_data, "redis_cluster_info", {})

        # Find current node in cluster configuration
        self.current_node = self._find_current_node()

        # Set up service and configuration directories
        self.service_dir = f"{self.home_dir}/halfstack/redis_sentinel-{self.config.name}"
        self.conf_dir = f"{self.service_dir}/conf"

    def _find_current_node(self) -> RedisHAClusterNodeConfig:
        """
        Find the current node configuration from the cluster nodes list.

        Returns:
            The node configuration for the current host

        Raises:
            ValueError: If current host is not found in cluster configuration
        """

        for node in self.config.cluster_nodes:
            if node.ssh_ip == host.name or node.hostname == host.name or node.ip == host.name:
                return node

        raise ValueError(f"Current host {host.name} not found in Redis HA cluster configuration")

    def create_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = False
    ) -> None:
        """Override to create both service and config directories"""
        files.directory(path=self.service_dir, present=True)
        files.directory(path=self.conf_dir, present=True)

    def install(self) -> None:
        self.create_directories()

        # Create .env file
        self.create_env_file(
            config=self.config,
            home_dir=self.home_dir,
            target_uname=self.user,
            current_node=self.current_node,
        )

        # Create Sentinel configuration template
        files.template(
            name="Create sentinel.conf template",
            src=self.locate_template("sentinel.conf.j2"),
            dest=f"{self.conf_dir}/sentinel.conf",
            config=self.config,
            master_node=self.config.get_master_node(),
        )

        # Create docker-compose.yml
        self.create_docker_compose_yaml(
            config=self.config,
            current_node=self.current_node,
        )

        self.create_service_manage_scripts(
            extra_context={
                "service_name": f"{self.config.sentinel_container_name_prefix}-node{self.current_node.node_number}",
                "config": self.config,
                "current_node": self.current_node,
            }
        )

        # Load and start service
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name=f"Stop Redis Sentinel service (redis_sentinel-{self.config.name})",
            commands=[
                f"if [ -d {self.service_dir} ] && [ -f {self.service_dir}/stop.sh ]; then {self.service_dir}/stop.sh; fi"
            ],
        )
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RedisSentinelDeploy(host.data).run(deploy_mode)


main()
