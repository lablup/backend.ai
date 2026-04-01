from pathlib import Path

from pyinfra import host
from pyinfra.operations import files

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class EtcdDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.uid = host_data.bai_user_id
        self.gid = host_data.bai_user_group_id

        self.config = host_data.services["etcd"]

        self.service_dir = f"{self.home_dir}/halfstack/etcd-default"
        self.data_dir = f"{self.home_dir}/.data/backend.ai/etcd-data"

    def create_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = False
    ) -> None:
        """Override to set proper ownership and permissions for etcd data directory."""
        files.directory(path=self.service_dir, present=True)
        files.directory(
            path=self.data_dir,
            present=True,
            user=str(self.uid),
            group=str(self.gid),
            mode="700",
        )

    def create_backup_restore_scripts(self) -> None:
        for script in ["backup.sh", "restore.sh"]:
            files.template(
                name=f"Create {script} script",
                src=self.locate_template(f"{script}.j2"),
                dest=f"{self.service_dir}/{script}",
                mode="755",
                # jinja2 context
                service_dir=self.service_dir,
                container_name=self.config.container_name,
                data_dir=str(self.data_dir),
                etcd_advertise_client_ip=self.config.advertised_client_ip,
                container_image=self.config.container_image,
            )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            data_dir=str(self.data_dir),
            etcd_advertise_client_ip=self.config.advertised_client_ip,
            etcd_advertise_client_port=self.config.advertised_client_port,
            container_image=self.config.container_image,
            container_name=self.config.container_name,
            uid=self.uid,
            gid=self.gid,
        )
        self.create_docker_compose_yaml(
            data_dir=str(self.data_dir),
            service_dir=self.service_dir,
        )
        self.create_service_manage_scripts()
        self.create_backup_restore_scripts()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        self.stop_service()
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcdDeploy(host.data).run(deploy_mode)


main()
