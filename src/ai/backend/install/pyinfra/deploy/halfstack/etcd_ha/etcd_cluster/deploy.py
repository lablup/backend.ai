from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.configs.halfstack import EtcdHAClusterNodeConfig
from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class EtcdClusterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.uid = host_data.bai_user_id
        self.gid = host_data.bai_user_group_id

        self.config = host_data.services["etcd_ha"]
        self.etcd_cluster_info = getattr(host_data, "etcd_cluster_info", {})

        # Find current node in cluster configuration
        self.current_node = self._find_current_node()

        # Set up service and data directories
        self.service_dir = f"{self.home_dir}/halfstack/etcd_cluster-default"
        self.data_dir = f"{self.home_dir}/.data/backend.ai/etcd-cluster/{self.config.name}/etcd{self.current_node.node_number}"

    def _find_current_node(self) -> EtcdHAClusterNodeConfig:
        """
        Find the current node configuration from the cluster nodes list.

        Returns:
            The node configuration for the current host

        Raises:
            ValueError: If current host is not found in cluster configuration
        """
        for node in self.config.cluster_nodes:
            if (
                node.ssh_ip == host.name
                or node.hostname == host.name
                or node.client_ip == host.name
            ):
                return node

        raise ValueError(f"Current host {host.name} not found in ETCD HA cluster configuration")

    def create_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = False
    ) -> None:
        """Override to set proper ownership and permissions for ETCD data directory."""
        files.directory(path=self.service_dir, present=True)
        files.directory(
            path=self.data_dir,
            present=True,
            user=str(self.uid),
            group=str(self.gid),
            mode="700",
        )

    def _cleanup_empty_parent_directories(self) -> None:
        """
        Clean up empty parent directories after removing data directory.

        This removes the cluster-specific and base directories if they are empty,
        which is useful when completely removing an ETCD cluster installation.
        """
        parent_dirs = [
            f"{self.home_dir}/.data/backend.ai/etcd-cluster/{self.config.name}",
            f"{self.home_dir}/.data/backend.ai/etcd-cluster",
        ]
        commands = [f"rmdir {dir_path} 2>/dev/null || true" for dir_path in parent_dirs]
        server.shell(
            name="Remove empty parent directories",
            commands=commands,
            _sudo=True,
        )

    def remove_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = True
    ) -> None:
        """Override to clean up empty parent directories after removal"""
        super().remove_directories(dirs=dirs, use_sudo=use_sudo)
        self._cleanup_empty_parent_directories()

    def create_node_env_file(self) -> None:
        files.template(
            name="Create node_env file",
            src=self.locate_template("node_env.j2"),
            dest=f"{self.service_dir}/node_env",
            etcd_cluster_info=self.etcd_cluster_info,
            current_node=self.current_node,
        )

    def create_backup_restore_scripts(self) -> None:
        """Create backup and restore scripts for ETCD cluster."""
        for script in ["backup.sh", "restore.sh"]:
            files.template(
                name=f"Create {script} script",
                src=str(self.locate_template(f"{script}.j2")),
                dest=str(f"{self.service_dir}/{script}"),
                mode="755",
                service_dir=str(self.service_dir),
                data_dir=str(self.data_dir),
                config=self.config,
                etcd_cluster_info=self.etcd_cluster_info,
                etcd_nodes=self.config.cluster_nodes,
            )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            home_dir=self.home_dir,
            uid=self.uid,
            gid=self.gid,
            user_name=self.user,
            etcd_container_image=self.config.container_image,
            etcd_cluster_name=self.config.name,
            etcd_cluster_member_number=self.current_node.node_number,
            etcd_config_pid_limits=self.config.pids_limit,
            data_dir=self.data_dir,
            etcd_client_ip=self.current_node.client_ip,
            etcd_client_port=self.current_node.client_port,
            etcd_peer_port=self.current_node.peer_port,
            etcd_nodes=self.config.cluster_nodes,
        )
        self.create_node_env_file()
        self.create_docker_compose_yaml(
            config=self.config,
            etcd_cluster_info=self.etcd_cluster_info,
            data_dir=self.data_dir,
            service_dir=self.service_dir,
            etcd_cluster_name=self.config.name,
            etcd_node_number=self.current_node.node_number,
            etcd_client_ip=self.current_node.client_ip,
            etcd_client_port=self.current_node.client_port,
            etcd_peer_ip=self.current_node.peer_ip,
            etcd_peer_port=self.current_node.peer_port,
            etcd_nodes=self.config.cluster_nodes,
            bai_home_dir=self.home_dir,
        )
        self.create_service_manage_scripts(
            extra_context={
                "config": self.config,
                "etcd_cluster_info": self.etcd_cluster_info,
            }
        )
        self.create_backup_restore_scripts()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name="Stop ETCD cluster service",
            commands=[
                f"if [ -d {self.service_dir} ]; then cd {self.service_dir} && {self.docker_compose_cmd} down; fi"
            ],
        )
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcdClusterDeploy(host.data).run(deploy_mode)


main()
