from pathlib import Path

from pyinfra import host
from pyinfra.facts.server import Hostname
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class DcgmExporterDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "dcgm-exporter"
        self.service_home = Path(f"{self.home_dir}/dashboard/dcgm-exporter")
        self.service_dir = self.service_home
        self.config = None

        # Get exporter port and image tag from prometheus config
        # On dashboard nodes the key is "prometheus"; on compute nodes it is "prometheus_config"
        prometheus_config = host_data.services.get("prometheus") or host_data.services.get(
            "prometheus_config"
        )
        if prometheus_config:
            self.exporter_port = prometheus_config.dcgm_exporter_port
            self.exporter_image_tag = prometheus_config.dcgm_exporter_image_tag
            self.local_archive_path = getattr(
                prometheus_config, "dcgm_exporter_local_archive_path", None
            )
        else:
            print(
                "  [WARNING] No prometheus config found in host services, using default DCGM Exporter settings"
            )
            self.exporter_port = 9400
            self.exporter_image_tag = "3.3.0-3.2.0-ubuntu22.04"
            self.local_archive_path = None

        # Prepare container image for base load_image method
        self.container_image = f"nvcr.io/nvidia/k8s/dcgm-exporter:{self.exporter_image_tag}"

    def _check_nvidia_runtime(self) -> None:
        """Verify nvidia-smi and Docker nvidia runtime are available; abort if missing."""
        server.shell(
            name="Check NVIDIA driver and Docker runtime availability",
            commands=[
                "if ! command -v nvidia-smi >/dev/null 2>&1; then "
                "echo 'ERROR: nvidia-smi not found. NVIDIA driver must be installed for DCGM Exporter.'; "
                "exit 1; "
                "fi; "
                "if ! docker info 2>/dev/null | grep -qE '^[[:space:]]*Runtimes:.*nvidia'; then "
                "echo 'ERROR: Docker nvidia runtime not found. NVIDIA Container Toolkit must be installed.'; "
                "exit 1; "
                "fi",
            ],
        )

    def install(self) -> None:
        self._check_nvidia_runtime()
        self.create_directories([self.service_home])
        exporter_hostname = host.get_fact(Hostname)
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            exporter_image_tag=self.exporter_image_tag,
            exporter_port=self.exporter_port,
            exporter_hostname=exporter_hostname,
        )
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
            name="Stop DCGM Exporter service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = DcgmExporterDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
