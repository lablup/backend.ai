from pathlib import Path

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import ensure_file_exists


class HarborDeploy(BaseSystemdDeploy):
    """
    Deploy Harbor container registry as a systemd service.

    Harbor is deployed using the official offline installer, which includes
    docker-compose configuration. The deployment creates systemd service
    wrapper for managing Harbor lifecycle.
    """

    # Service constants
    SERVICE_NAME = "harbor"
    SYSTEMD_SERVICE_NAME = f"backendai-{SERVICE_NAME}"
    TMP_INSTALL_DIR = Path("/tmp/_bainst")

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.user_id: int = host_data.bai_user_id
        self.group_id: int = host_data.bai_user_group_id

        self.config = host_data.services["harbor"]

        self.registry_hostname: str = host_data.registry_name
        self.registry_port: int = host_data.registry_port

        # Set service_name for BaseSystemdDeploy
        self.service_name = self.SERVICE_NAME
        self.service_dir = self.home_dir / self.SERVICE_NAME

        # Use custom data_dir from config if provided, otherwise use default
        if self.config.data_dir:
            self.data_dir = Path(self.config.data_dir)
        else:
            self.data_dir = self.home_dir / ".data" / self.SERVICE_NAME

    def extract_and_move_harbor(self, file_path: Path) -> None:
        """
        Extract Harbor installer archive and move to service directory.

        Args:
            file_path: Path to Harbor installer archive file
        """
        files.directory(path=str(self.TMP_INSTALL_DIR), present=True)
        server.shell(
            name=f"Extract and move Harbor to {self.service_dir}",
            commands=[
                f"tar -xzf {file_path} -C {self.TMP_INSTALL_DIR}",
                f"rsync -avz --delete {self.TMP_INSTALL_DIR}/harbor/ {self.service_dir}/",
                f"chown -R {self.user_id}:{self.group_id} {self.service_dir}",
            ],
            _sudo=True,
        )

    def create_harbor_yaml(self) -> None:
        """Create Harbor configuration file (harbor.yml) from template."""
        files.template(
            name="Create harbor.yml",
            src=str(self.locate_template("harbor.yml.j2")),
            dest=str(self.service_dir / "harbor.yml"),
            mode="644",
            # jinja2 context
            harbor_hostname=self.registry_hostname,
            harbor_http_port=self.registry_port,
            harbor_admin_password=self.config.admin_password,
            data_dir=self.data_dir,
        )

    def run_harbor_install_script(self) -> None:
        """
        Run Harbor's install.sh script to generate docker-compose.yml.

        This script is idempotent - it only runs if docker-compose.yml doesn't exist.
        If enable_trivy is set in the config, the --with-trivy flag is added.
        """
        if not host.get_fact(File, f"{self.service_dir}/docker-compose.yml"):
            install_cmd = "./install.sh"
            if self.config.enable_trivy:
                install_cmd += " --with-trivy"
            server.shell(
                name="Run Harbor installation script",
                commands=[f"cd {self.service_dir} && {install_cmd}"],
                _sudo=True,
            )

    def install(self) -> None:
        """Install Harbor container registry service."""
        # Create directories
        self.create_directories()

        # Download and extract Harbor
        file_path = ensure_file_exists(self.config.download_uri)
        self.extract_and_move_harbor(Path(file_path))

        # Configure Harbor
        self.create_harbor_yaml()
        self.run_harbor_install_script()

        # Create systemd service wrapper
        self.create_systemd_service(
            src=self.locate_template(f"systemd/{self.SYSTEMD_SERVICE_NAME}.service.j2"),
            service_dir=self.service_dir,
            exec_start=f"docker compose -f {self.service_dir}/docker-compose.yml up",
            user_id=0,  # Harbor needs root to manage Docker
            group_id=0,
        )

        # Create management scripts
        self.create_service_manage_scripts(
            extra_context={"service_name": self.SYSTEMD_SERVICE_NAME}
        )

        # Start service
        self.start_service()

        # Clean up temporary installation directory
        files.directory(path=str(self.TMP_INSTALL_DIR), present=False, _sudo=True)

    def remove(self) -> None:
        """Remove Harbor container registry service."""
        # Stop and disable systemd service first to prevent restart
        self.stop_service()
        self.remove_systemd_service()

        # Then stop and remove Harbor containers
        server.shell(
            name="Stop and remove Harbor containers",
            commands=[
                f"cd {self.service_dir} && docker compose down --remove-orphans || true",
                "docker container prune -f --filter label=com.docker.compose.project=harbor || true",
                "docker network prune -f --filter label=com.docker.compose.project=harbor || true",
            ],
            _sudo=True,
        )

        # Finally remove directories (note: data_dir is intentionally preserved for safety)
        self.remove_directories(dirs=[self.service_dir])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    HarborDeploy(host.data).run(deploy_mode)


main()
