from pathlib import Path

from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PostgresExporterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "postgres-exporter"
        self.config = None

        # Both HA and single-node connect to the local DB instance
        self.db_host = self.resolve_host("host.docker.internal")

        # Detect HA vs single-node PostgreSQL configuration
        if hasattr(host_data.services, "postgres_ha") or "postgres_ha" in host_data.services:
            self.config_db = host_data.services["postgres_ha"]
            self.is_ha_mode = True
            # In HA mode, use the host-mapped port (e.g., 8101)
            # since PostgreSQL Exporter runs on host, not in container
            pg_cluster_info = getattr(host_data, "pg_cluster_info", {})
            self.db_port = pg_cluster_info.get("pg_sql_port", 8101)
        else:
            self.config_db = host_data.services["postgres"]
            self.is_ha_mode = False
            self.db_port = self.config_db.port

        # Get exporter port and image tag from prometheus config
        # On dashboard nodes the key is "prometheus"; on compute nodes it is "prometheus_config"
        prometheus_config = host_data.services.get("prometheus") or host_data.services.get(
            "prometheus_config"
        )
        if prometheus_config:
            self.exporter_port = prometheus_config.db_exporter_port
            self.exporter_image_tag = prometheus_config.db_exporter_image_tag
            self.local_archive_path = getattr(
                prometheus_config, "db_exporter_local_archive_path", None
            )
        else:
            self.exporter_port = 9187  # fallback default
            self.exporter_image_tag = "v0.17.1"  # fallback default
            self.local_archive_path = None

        self.service_home = Path(f"{self.home_dir}/dashboard/postgres-exporter")
        self.service_dir = self.service_home

        # Prepare container image for base load_image method
        self.container_image = f"prometheuscommunity/postgres-exporter:{self.exporter_image_tag}"

    def install(self) -> None:
        self.create_directories([self.service_home])
        # Handle different config attributes for HA vs single-node
        if self.is_ha_mode:
            db_user = self.config_db.pg_superuser_id
            db_password = self.config_db.pg_superuser_password
        else:
            db_user = self.config_db.user
            db_password = self.config_db.password

        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            exporter_image_tag=self.exporter_image_tag,
            exporter_port=self.exporter_port,
            db_host=self.db_host,
            db_port=self.db_port,
            db_name="backend",
            db_user=db_user,
            db_password=db_password,
        )
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
        )
        self.create_service_manage_scripts(extra_context={"exporter_port": self.exporter_port})
        self.load_image(self.container_image, self.local_archive_path)
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop PostgreSQL Exporter service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = PostgresExporterDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
