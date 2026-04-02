from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class EtcdGrpcDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.uid = host_data.bai_user_id
        self.gid = host_data.bai_user_group_id

        self.config = host_data.services["etcd_ha"]
        self.etcd_cluster_info = getattr(host_data, "etcd_cluster_info", {})

        self.service_dir = f"{self.home_dir}/halfstack/etcd_grpc-default"

    def create_node_env_file(self) -> None:
        files.template(
            name="Create node_env file",
            src=self.locate_template("node_env.j2"),
            dest=f"{self.service_dir}/node_env",
            etcd_cluster_info=self.etcd_cluster_info,
            grpc_config=self.config,
        )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            home_dir=self.home_dir,
            uid=self.uid,
            gid=self.gid,
            user_name=self.user,
            etcd_container_image=self.config.grpc_container_image,
            etcd_cluster_name=self.config.name,
            etcd_grpc_service_ip=self.config.grpc_service_ip,
            etcd_grpc_service_port=self.config.grpc_service_port,
            etcd_nodes=self.config.cluster_nodes,
        )
        self.create_node_env_file()
        self.create_docker_compose_yaml(
            config=self.config,
            service_dir=self.service_dir,
            etcd_grpc_service_ip=self.config.grpc_service_ip,
            etcd_grpc_service_port=self.config.grpc_service_port,
            etcd_nodes=self.config.cluster_nodes,
        )
        self.create_service_manage_scripts(
            extra_context={
                "config": self.config,
                "etcd_nodes": self.config.cluster_nodes,
            }
        )
        # Load gRPC proxy image using BaseDockerComposeDeploy's load_image with explicit parameters
        self.load_image(
            container_image=self.config.grpc_container_image,
            local_archive_path=getattr(self.config, "grpc_local_archive_path", None),
        )
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name="Stop ETCD gRPC service",
            commands=[
                f"if [ -d {self.service_dir} ]; then cd {self.service_dir} && {self.docker_compose_cmd} down; fi"
            ],
        )
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcdGrpcDeploy(host.data).run(deploy_mode)


main()
