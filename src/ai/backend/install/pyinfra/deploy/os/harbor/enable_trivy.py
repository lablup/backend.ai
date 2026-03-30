from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseSystemdDeploy


class EnableTrivyDeploy(BaseSystemdDeploy):
    """
    Enable Trivy vulnerability scanner on an existing Harbor installation.

    This deployment script reconfigures a running Harbor instance to include
    the Trivy adapter container by:
    1. Stopping the Harbor systemd service
    2. Regenerating harbor.yml with trivy configuration
    3. Running install.sh --with-trivy to regenerate docker-compose.yml
    4. Starting the Harbor systemd service
    """

    SERVICE_NAME = "harbor"
    SYSTEMD_SERVICE_NAME = f"backendai-{SERVICE_NAME}"

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.user_id: int = host_data.bai_user_id
        self.group_id: int = host_data.bai_user_group_id

        self.config = host_data.services["harbor"]

        self.registry_hostname: str = host_data.registry_name
        self.registry_port: int = host_data.registry_port

        self.service_name = self.SERVICE_NAME
        self.service_dir = self.home_dir / self.SERVICE_NAME

        if self.config.data_dir:
            self.data_dir = Path(self.config.data_dir)
        else:
            self.data_dir = self.home_dir / ".data" / self.SERVICE_NAME

    def create_harbor_yaml(self) -> None:
        """Create Harbor configuration file (harbor.yml) from template."""
        files.template(
            name="Create harbor.yml with trivy configuration",
            src=str(self.locate_template("harbor.yml.j2")),
            dest=str(self.service_dir / "harbor.yml"),
            mode="644",
            harbor_hostname=self.registry_hostname,
            harbor_http_port=self.registry_port,
            harbor_admin_password=self.config.admin_password,
            data_dir=self.data_dir,
        )

    def install(self) -> None:
        """Enable Trivy scanner on existing Harbor installation."""
        # Stop Harbor service
        self.stop_service()

        # Stop containers to allow reconfiguration
        server.shell(
            name="Stop Harbor containers",
            commands=[f"cd {self.service_dir} && docker compose down"],
            _sudo=True,
        )

        # Regenerate harbor.yml
        self.create_harbor_yaml()

        # Run install.sh with --with-trivy to regenerate docker-compose.yml
        server.shell(
            name="Run Harbor install.sh with Trivy enabled",
            commands=[f"cd {self.service_dir} && ./install.sh --with-trivy"],
            _sudo=True,
        )

        # Start Harbor service
        self.start_service()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EnableTrivyDeploy(host.data).run(deploy_mode)


main()
