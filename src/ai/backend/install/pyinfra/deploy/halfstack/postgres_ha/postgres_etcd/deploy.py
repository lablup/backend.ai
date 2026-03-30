from pathlib import Path
from typing import Any

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PostgresEtcdDeploy(BaseDockerComposeDeploy):
    """Deploy ETCD cluster for PostgreSQL high-availability coordination."""

    SERVICE_NAME: str = "postgres_ha"
    DATA_DIR_MODE: str = "700"
    SCRIPT_MODE: str = "755"
    HELPER_SCRIPT_NAME: str = "apply_pids_limit_to_existing_docker.sh"

    def __init__(self, host_data: Any, service_key: str = "postgres_ha") -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.uid: int = host_data.bai_user_id
        self.gid: int = host_data.bai_user_group_id

        self.config = host_data.services[service_key]
        # Use appropriate cluster_info based on service_key
        self.pg_cluster_info: dict[str, Any]
        if service_key == "controlpanel":
            self.pg_cluster_info = getattr(host_data, "cp_pg_cluster_info", {})
        else:
            self.pg_cluster_info = getattr(host_data, "pg_cluster_info", {})

        # Derive paths from config.name (supports multiple instances)
        # Keep backward compatibility: "default" uses original paths without suffix
        instance_name = getattr(self.config, "name", "default")
        self.service_dir: Path
        self.data_dir: Path
        if instance_name == "default":
            self.service_dir = self.home_dir / "halfstack/postgres_etcd-default"
            self.data_dir = self.home_dir / ".data/backend.ai/postgres-etcd-data"
        else:
            self.service_dir = self.home_dir / f"halfstack/postgres_etcd-{instance_name}"
            self.data_dir = self.home_dir / f".data/backend.ai/postgres-etcd-data-{instance_name}"

    def _create_directories(self) -> None:
        files.directory(path=str(self.service_dir), present=True)
        files.directory(
            path=str(self.data_dir),
            present=True,
            user=str(self.uid),
            group=str(self.gid),
            mode=self.DATA_DIR_MODE,
        )

    def _remove_directories(self) -> None:
        files.directory(path=str(self.data_dir), present=False, _sudo=True)
        files.directory(path=str(self.service_dir), present=False, _sudo=True)

    def _copy_helper_scripts(self) -> None:
        files.put(
            name="Copy pids limit script",
            src=str(self.locate_file(self.HELPER_SCRIPT_NAME)),
            dest=str(self.service_dir / self.HELPER_SCRIPT_NAME),
            mode=self.SCRIPT_MODE,
        )

    def install(self) -> None:
        self._create_directories()
        self.create_env_file(
            config=self.config,
            pg_cluster_info=self.pg_cluster_info,
            uid=self.uid,
            gid=self.gid,
        )
        self.create_docker_compose_yaml(
            config=self.config,
            pg_cluster_info=self.pg_cluster_info,
            data_dir=str(self.data_dir),
        )
        self.create_service_manage_scripts(
            extra_context={
                "config": self.config,
                "pg_cluster_info": self.pg_cluster_info,
            }
        )
        self._copy_helper_scripts()
        self.load_image(
            container_image=self.config.etcd_container_image,
            local_archive_path=self.config.etcd_local_archive_path,
        )
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name="Stop PostgreSQL ETCD service",
            commands=[
                f"[ -d {self.service_dir} ] && cd {self.service_dir} && {self.docker_compose_cmd} down || true"
            ],
        )
        self._remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    service_key = host.data.get("service_key", "postgres_ha")
    PostgresEtcdDeploy(host.data, service_key=service_key).run(deploy_mode)


main()
