from pathlib import Path

from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class RedisExporterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "redis-exporter"
        self.service_home = Path(f"{self.home_dir}/dashboard/redis-exporter")
        self.service_dir = self.service_home
        self.config = None

        # Auto-detect HA vs single-node Redis configuration
        if "redis_ha" in host_data.services:
            self.config_redis = host_data.services["redis_ha"]
            self.is_ha_mode = True
            self.is_sentinel_mode = False  # Use HAProxy VIP, not direct Sentinel
            # Use HAProxy VIP for HA Redis access - standard naming convention
            self.redis_host = "bai-redis-vip"  # Standard Redis HA VIP hostname
            self.redis_port = self.config_redis.haproxy_service_port  # 8110
            self.redis_password = self.config_redis.password
        else:
            self.config_redis = host_data.services["redis"]
            self.is_ha_mode = False
            self.is_sentinel_mode = False
            self.redis_host = self.config_redis.hostname
            self.redis_port = self.config_redis.port
            self.redis_password = getattr(self.config_redis, "password", None)

        # Get exporter port and image tag from prometheus config
        # On dashboard nodes the key is "prometheus"; on compute nodes it is "prometheus_config"
        prometheus_config = host_data.services.get("prometheus") or host_data.services.get(
            "prometheus_config"
        )
        if prometheus_config:
            self.exporter_port = prometheus_config.redis_exporter_port
            self.exporter_image_tag = prometheus_config.redis_exporter_image_tag
            self.local_archive_path = getattr(
                prometheus_config, "redis_exporter_local_archive_path", None
            )
        else:
            self.exporter_port = 9121  # fallback default
            self.exporter_image_tag = "v1.73.0"  # fallback default
            self.local_archive_path = None

        # Prepare container image for base load_image method
        self.container_image = f"oliver006/redis_exporter:{self.exporter_image_tag}"

    def install(self) -> None:
        self.create_directories([self.service_home])
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            exporter_image_tag=self.exporter_image_tag,
            redis_host=self.redis_host,
            redis_port=self.redis_port,
            redis_password=self.redis_password,
            exporter_port=self.exporter_port,
            is_sentinel_mode=self.is_sentinel_mode,
            is_ha_mode=self.is_ha_mode,
        )
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
        )
        self.create_service_manage_scripts(
            extra_context={
                "exporter_port": self.exporter_port,
                "is_sentinel_mode": self.is_sentinel_mode,
                "is_ha_mode": self.is_ha_mode,
            }
        )
        self.load_image(self.container_image, self.local_archive_path)
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop Redis Exporter service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = RedisExporterDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
