from pathlib import Path
from typing import Any

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDeploy


class BaseConfigFileDeploy(BaseDeploy):
    """Base class for config file deployments with common constants and methods."""

    # Constants for config file settings
    FILE_MODE: str = "644"
    CONFIG_DIR: str = "/etc"
    CONFIG_PREFIX: str = "99-backend-ai"

    # Subclasses must define these
    local_template: Path
    remote_host_dest: str

    def __init__(self) -> None:
        """Initialize base config file deployment."""
        super().__init__()

    def remove(self) -> None:
        """Remove the deployed configuration file."""
        files.file(path=self.remote_host_dest, present=False, _sudo=True)

    def _deploy_template(
        self,
        description: str,
        template_context: dict[str, Any],
        post_deploy_commands: list[str] | None = None,
    ) -> None:
        """
        Deploy a template file with given context.

        Args:
            description: Human-readable description of the deployment
            template_context: Jinja2 template variables
            post_deploy_commands: Optional shell commands to run after deployment
        """
        files.template(
            name=f"{description} at {self.remote_host_dest}",
            src=str(self.local_template),
            dest=self.remote_host_dest,
            mode=self.FILE_MODE,
            _sudo=True,
            **template_context,
        )

        if post_deploy_commands:
            for command in post_deploy_commands:
                server.shell(commands=command, _sudo=True)


class ResourceLimitDeploy(BaseConfigFileDeploy):
    """Deploy resource limit configuration for Backend.AI user."""

    local_template: Path = Path(__file__).parent / "templates/limits.conf.j2"
    remote_host_dest: str = "/etc/security/limits.d/99-backend-ai.conf"

    def __init__(self, host_data: Any) -> None:
        """
        Initialize resource limit deployment.

        Args:
            host_data: PyInfra host data containing bai_user configuration
        """
        super().__init__()
        self.user: str = host_data.bai_user

    def install(self) -> None:
        """Deploy resource limits configuration file."""
        self._deploy_template(
            description="Add limits configuration",
            template_context={"username": self.user},
        )


class SecurityConfigDeploy(BaseConfigFileDeploy):
    """Deploy system security (sysctl) configuration."""

    local_template: Path = Path(__file__).parent / "templates/sysctl.conf.j2"
    remote_host_dest: str = "/etc/sysctl.d/99-backend-ai.conf"

    def __init__(self, host_data: Any) -> None:
        """
        Initialize security config deployment.

        Args:
            host_data: PyInfra host data containing node_type configuration
        """
        super().__init__()
        self.resource_limit_type: str = host_data.node_type

    def install(self) -> None:
        """Deploy sysctl configuration file and apply settings."""
        self._deploy_template(
            description="Add sysctl configuration",
            template_context={"resource_limit_type": self.resource_limit_type},
            post_deploy_commands=[f"sysctl -p {self.remote_host_dest}"],
        )


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    ResourceLimitDeploy(host.data).run(deploy_mode)
    SecurityConfigDeploy(host.data).run(deploy_mode)


main()
