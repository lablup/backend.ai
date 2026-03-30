from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class OtelCollectorDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "otel-collector"
        self.service_home = Path(f"{self.home_dir}/dashboard/otel-collector")
        self.service_dir = self.service_home
        self.host_data = host_data

        self.config = host_data.services["otel_collector"]
        self.otel_config = self.config

        # Get data sources configuration for Loki and Tempo endpoints
        self.data_sources_config = host_data.services["data_sources"]

    def create_otel_collector_config_yml(self) -> None:
        """Create OTEL Collector configuration with dynamic endpoints"""
        loki_host = self.resolve_host(self.data_sources_config.loki_host)
        tempo_host = self.resolve_host(self.data_sources_config.tempo_host)

        files.template(
            name="Create otel-collector-config.yml",
            src=str(Path(__file__).parent / "templates/otel-collector-config.yml.j2"),
            dest=f"{self.service_home}/configs/otel-collector-config.yml",
            user=self.user,
            mode="644",
            # Jinja2 context (resolve host.docker.internal to actual host IP)
            loki_host=loki_host,
            loki_port=self.data_sources_config.loki_port,
            # Tempo configuration (placeholder for future)
            tempo_host=tempo_host,
            tempo_port=self.data_sources_config.tempo_port,
        )

    def install(self) -> None:
        self.create_directories([
            self.service_home,
            self.service_home / "configs",
        ])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            otel_image_tag=self.otel_config.otel_image_tag,
            otel_grpc_port=self.otel_config.grpc_port,
            otel_http_port=self.otel_config.http_port,
            otel_health_port=self.otel_config.health_port,
        )
        self.create_otel_collector_config_yml()
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
        )
        self.create_service_manage_scripts()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop OTEL Collector service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = OtelCollectorDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
