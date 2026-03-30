from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class LokiDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "loki"
        self.service_home = Path(f"{self.home_dir}/dashboard/loki")
        self.service_dir = self.service_home

        self.config = host_data.services["loki"]

        # Set data_dir: use config value if provided, otherwise default to {home_dir}/.data/loki
        self.data_dir = self.config.data_dir or f"{self.home_dir}/.data/loki"

    def create_loki_config_yml(self) -> None:
        files.template(
            name="Create loki-config.yml",
            src=str(Path(__file__).parent / "templates/loki-config.yml.j2"),
            dest=f"{self.service_home}/configs/loki-config.yml",
            user=self.user,
            mode="644",
            # Jinja2 context
            loki_retention_period=self.config.retention_period,
        )

    def change_permissions(self) -> None:
        """Set permissions for Loki data directory (Loki uses UID 10001)"""
        data_dir = self.data_dir
        server.shell(
            name="Set loki data directory permissions for loki user (10001:10001)",
            commands=[
                # Ensure directory exists
                f"mkdir -p {data_dir}",
                # Set ownership to loki user (10001:10001) - force if needed
                f"chown -R 10001:10001 {data_dir} || echo 'Failed to change ownership, continuing...'",
                # Set appropriate permissions for loki user
                f"chmod -R 755 {data_dir}",
            ],
            _sudo=True,
        )

    def install(self) -> None:
        self.create_directories([
            self.service_home,
            self.service_home / "configs",
            self.data_dir,
        ])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            loki_image_tag=self.config.loki_image_tag,
            loki_port=self.config.port,
            loki_retention_period=self.config.retention_period,
        )
        self.create_loki_config_yml()
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
            name="Stop Loki service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.data_dir, self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = LokiDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
