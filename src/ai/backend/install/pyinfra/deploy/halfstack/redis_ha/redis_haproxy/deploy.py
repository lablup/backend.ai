from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class RedisHaproxyDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config = host_data.services["redis_ha"]
        self.redis_cluster_info = getattr(host_data, "redis_cluster_info", {})

        # Service and configuration directories
        self.service_dir = f"{self.home_dir}/halfstack/redis_haproxy-{self.config.name}"
        self.conf_dir = f"{self.service_dir}/conf"

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
        )

        # Create HAProxy configuration
        files.template(
            name="Create haproxy.cfg",
            src=self.locate_template("haproxy.cfg.j2"),
            dest=f"{self.conf_dir}/haproxy.cfg",
            config=self.config,
        )

        # Create docker-compose.yml
        self.create_docker_compose_yaml(
            config=self.config,
        )

        # Create HAProxy health check script
        files.template(
            name="Create HAProxy health check script",
            src=self.locate_template("check_haproxy_redis.sh.j2"),
            dest=f"{self.service_dir}/check_haproxy_redis.sh",
            mode="755",
            config=self.config,
        )

        self.create_service_manage_scripts(
            extra_context={
                "service_name": "redis-haproxy",
                "config": self.config,
            }
        )

        # Load and start service
        self.load_image(
            container_image=self.config.haproxy_container_image,
            local_archive_path=self.config.haproxy_local_archive_path,
        )
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name=f"Stop Redis HAProxy service (redis_haproxy-{self.config.name})",
            commands=[
                f"if [ -d {self.service_dir} ] && [ -f {self.service_dir}/stop.sh ]; then {self.service_dir}/stop.sh; fi"
            ],
        )
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RedisHaproxyDeploy(host.data).run(deploy_mode)


main()
