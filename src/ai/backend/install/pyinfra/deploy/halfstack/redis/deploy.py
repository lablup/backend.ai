from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class RedisDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user

        self.config = host_data.services["redis"]

        self.service_dir = f"{self.home_dir}/halfstack/redis-default"
        self.data_dir = f"{self.home_dir}/.data/backend.ai/redis-data"

    def fix_data_directory_ownership(self) -> None:
        server.shell(
            name="Fix redis data directory ownership",
            commands=[
                f"REDIS_UID=$(docker run --rm {self.config.container_image} id -u redis)",
                f"REDIS_GID=$(docker run --rm {self.config.container_image} id -g redis)",
                f"chown $REDIS_UID:$REDIS_GID {self.data_dir}",
            ],
            _sudo=True,
        )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            redis_port=self.config.port,
            redis_password=self.config.password,
            container_image=self.config.container_image,
            container_name=self.config.container_name,
        )
        self.create_docker_compose_yaml(
            data_dir=str(self.data_dir),
        )
        self.create_service_manage_scripts()
        self.load_image()
        self.fix_data_directory_ownership()
        self.start_service()

    def remove(self) -> None:
        self.stop_service()
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RedisDeploy(host.data).run(deploy_mode)


main()
