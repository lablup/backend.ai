from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class BlackboxExporterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "blackbox-exporter"
        self.service_home = Path(f"{self.home_dir}/dashboard/blackbox-exporter")
        self.service_dir = self.service_home
        self.config = None

        # Get exporter port and image tag from prometheus config
        # On dashboard nodes the key is "prometheus"; on compute nodes it is "prometheus_config"
        prometheus_config = host_data.services.get("prometheus") or host_data.services.get(
            "prometheus_config"
        )
        if prometheus_config:
            self.exporter_port = prometheus_config.blackbox_exporter_port
            self.exporter_image_tag = prometheus_config.blackbox_exporter_image_tag
            self.local_archive_path = getattr(
                prometheus_config, "blackbox_exporter_local_archive_path", None
            )
        else:
            self.exporter_port = 9115  # fallback default
            self.exporter_image_tag = "v0.25.0"  # fallback default
            self.local_archive_path = None

        # Prepare container image for base load_image method
        self.container_image = f"prom/blackbox-exporter:{self.exporter_image_tag}"

    def create_blackbox_yml(self) -> None:
        """Render blackbox.yml probe configuration."""
        files.template(
            name="Create blackbox.yml",
            src=str(Path(__file__).parent / "templates/blackbox.yml.j2"),
            dest=f"{self.service_home}/blackbox.yml",
            user=self.user,
            mode="644",
        )

    def install(self) -> None:
        self.create_directories([self.service_home])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            exporter_image_tag=self.exporter_image_tag,
            exporter_port=self.exporter_port,
        )
        self.create_blackbox_yml()
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
        )
        self.create_service_manage_scripts(
            extra_context={
                "exporter_port": self.exporter_port,
            }
        )
        self.load_image(self.container_image, self.local_archive_path)
        self.start_service()

    def remove(self) -> None:
        server.shell(
            name="Stop Blackbox Exporter service if directory exists",
            commands=[
                f"if [ -d {self.service_home} ]; then "
                f"cd {self.service_home} && docker compose down; "
                f"fi",
            ],
        )
        self.remove_directories([self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = BlackboxExporterDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
