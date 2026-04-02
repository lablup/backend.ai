from pathlib import Path

from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PyroscopeDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "pyroscope"
        self.service_home = Path(f"{self.home_dir}/dashboard/pyroscope")
        self.service_dir = self.service_home

        self.config = host_data.services["pyroscope"]
        self.pyroscope_config = self.config

        # Set data_dir: use config value if provided, otherwise default to {home_dir}/.data/pyroscope
        self.data_dir = self.pyroscope_config.data_dir or f"{self.home_dir}/.data/pyroscope"

    def change_permissions(self) -> None:
        """Set permissions for Pyroscope data directory"""
        data_dir = self.data_dir
        server.shell(
            name="Set pyroscope data directory permissions",
            commands=[
                # Ensure directory exists
                f"mkdir -p {data_dir}",
                # Set ownership to bai user for now (adjust if Pyroscope uses specific UID)
                f"chown -R {self.user}:{self.user} {data_dir} || echo 'Failed to change ownership, continuing...'",
                # Set appropriate permissions
                f"chmod -R 755 {data_dir}",
            ],
            _sudo=True,
        )

    def install(self) -> None:
        self.create_directories([self.service_home, self.data_dir])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            pyroscope_image_tag=self.pyroscope_config.pyroscope_image_tag,
            pyroscope_port=self.pyroscope_config.port,
        )
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
            data_dir=self.data_dir,
        )
        self.create_service_manage_scripts()
        self.change_permissions()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop Pyroscope service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.data_dir, self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = PyroscopeDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
