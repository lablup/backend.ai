from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files, pip, server

from ai.backend.install.pyinfra.exceptions import DeploymentError
from ai.backend.install.pyinfra.runner import BaseDeploy
from ai.backend.install.pyinfra.utils import get_major_version


class ClientPyDeploy(BaseDeploy):
    """Deployment class for Backend.AI Python client.

    This class handles the installation and configuration of the Backend.AI Python client,
    including environment setup, credential configuration, and helper script creation.
    """

    # Class constants
    PACKAGE_PREFIX = "backend.ai"
    SERVICE_NAME = "client"
    STATIC_PYTHON_DIR = ".static-python"
    UPGRADE_DIR = "upgrades"

    def __init__(self, host_data: object) -> None:
        """Initialize ClientPyDeploy with host configuration data.

        Args:
            host_data: Host configuration data containing service and user settings
        """
        super().__init__()
        self._init_user_configs(host_data)
        self._init_service_configs(host_data)
        self._init_python_configs(host_data)

    def _init_user_configs(self, host_data: object) -> None:
        """Initialize user and directory configurations.

        Args:
            host_data: Host configuration data
        """
        self.home_dir: str = host_data.bai_home_dir
        self.user: str = host_data.bai_user
        self.user_id: int = host_data.bai_user_id
        self.group_id: int = host_data.bai_user_group_id
        self.service_name: str = self.SERVICE_NAME
        self.service_dir: Path = Path(f"{self.home_dir}/{self.service_name}")
        self.upgrade_dir: str = f"{self.service_dir}/{self.UPGRADE_DIR}"

    def _init_service_configs(self, host_data: object) -> None:
        """Initialize service-related configurations.

        Args:
            host_data: Host configuration data
        """
        self.config_bai_core = host_data.services["bai_core"]
        self.config_manager = host_data.services["manager"]

        # Calculate manager API endpoint
        manager_port = self.config_manager.haproxy_service_port or self.config_manager.port
        self.manager_api_endpoint: str = (
            f"http://{self.config_manager.client_connect_ip}:{manager_port}"
        )

    def _init_python_configs(self, host_data: object) -> None:
        """Initialize Python environment configurations.

        Args:
            host_data: Host configuration data
        """
        self.bai_major_version: str = get_major_version(self.config_bai_core.version)
        self.pip_install_options: str = host.data.bai_pip_install_options
        self.python_version: str = host.data.python_version
        self.python_path: str = (
            f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/versions/{self.python_version}/bin/python3"
        )
        self.python_venv_path: str = f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/venvs/bai-{self.bai_major_version}-{self.service_name}"

    def _install_service(self) -> None:
        """Install the Backend.AI Python client package with error handling."""
        try:
            pip.packages(
                name=f"Install {self.PACKAGE_PREFIX}-{self.service_name} version {self.config_bai_core.version}",
                packages=[
                    f"{self.PACKAGE_PREFIX}-{self.service_name}=={self.config_bai_core.version}"
                ],
                extra_install_args=self.pip_install_options,
                pip=f"{self.python_venv_path}/bin/pip",
                present=True,
            )

        except Exception as e:
            error_msg = f"Failed to install {self.service_name} package: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _get_dot_env_context(self) -> dict:
        """Get template context for .env file with API credentials.

        Returns:
            Dictionary containing template context for .env file
        """
        return {
            "manager_api_endpoint": self.manager_api_endpoint,
            "superadmin_access_key": self.config_manager.superadmin_access_key,
            "superadmin_secret_key": self.config_manager.superadmin_secret_key,
            "user_access_key": self.config_manager.user_access_key,
            "user_secret_key": self.config_manager.user_secret_key,
        }

    def _create_dot_env_file(self, dest_path: str | None = None) -> None:
        """Create .env file with API endpoint and credential configuration.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.
        """
        try:
            env_context = self._get_dot_env_context()

            if dest_path is None:
                dest_path = f"{self.service_dir}/.env"

            files.template(
                name="Create .env configuration file",
                src=str(self.locate_template("dot_env.j2")),
                dest=dest_path,
                **env_context,
            )

        except Exception as e:
            error_msg = f"Failed to create .env file: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _create_session_script(self, dest_dir: str | None = None) -> None:
        """Create helper script for creating compute sessions.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        try:
            if dest_dir is None:
                dest_dir = str(self.service_dir)

            files.template(
                name="Create create_session.sh helper script",
                src=str(self.locate_template("create_session.sh.j2")),
                dest=f"{dest_dir}/create_session.sh",
                mode="0755",
            )

        except Exception as e:
            error_msg = f"Failed to create session script: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _create_rescan_images_script(self, dest_dir: str | None = None) -> None:
        """Create helper script for rescanning container images from registry.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        try:
            if dest_dir is None:
                dest_dir = str(self.service_dir)

            files.template(
                name="Create rescan_images.sh helper script",
                src=str(self.locate_template("rescan_images.sh.j2")),
                dest=f"{dest_dir}/rescan_images.sh",
                mode="0755",
            )

        except Exception as e:
            error_msg = f"Failed to create rescan images script: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _rescan_images_if_ready(self) -> None:
        """Attempt to rescan registry images automatically.

        This is a non-critical operation that tries to refresh the container image
        catalog from the registry. If it fails (e.g., manager not ready, network issues),
        the deployment continues successfully and users can manually run the script later.
        """
        try:
            logger.info("Attempting to rescan container images from registry...")

            # Set environment variables from .env file and run rescan command
            # Use absolute path for .env file to avoid path issues
            server.shell(
                name="Rescan container images from registry",
                commands=[
                    f"set -a && . {self.service_dir}/.env && set +a && "
                    f"{self.python_venv_path}/bin/backend.ai admin image rescan"
                ],
                _ignore_errors=True,
            )

            logger.info("Image rescan completed successfully")

        except Exception as e:
            logger.warning(
                f"Failed to automatically rescan images: {e}. "
                f"You can manually run: {self.service_dir}/rescan_images.sh"
            )

    def _create_diff_script(self) -> None:
        """Create shell script to compare old vs new configurations."""
        files.template(
            name="Create diff comparison script",
            src=str(self.locate_template("scripts/show_diffs.sh.j2")),
            dest=f"{self.upgrade_dir}/show_diffs.sh",
            mode="0755",
            user=self.user,
            upgrade_dir=self.upgrade_dir,
            service_dir=self.service_dir,
        )

    def install(self) -> None:
        """Install and configure the Backend.AI Python client."""
        self.create_directories()
        self.remote._create_python_env(self.python_path, self.python_venv_path, self.service_dir)
        self._install_service()
        self._create_dot_env_file()
        self._create_session_script()
        self._create_rescan_images_script()
        self._rescan_images_if_ready()

    def update(self) -> None:
        """Update the client service while preserving existing configurations."""
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        self.create_directories(dirs=[self.upgrade_dir])
        self.remote._create_python_env(self.python_path, self.python_venv_path, self.service_dir)
        self._install_service()

        self._create_dot_env_file(dest_path=f"{self.upgrade_dir}/.env")
        self._create_session_script(dest_dir=self.upgrade_dir)
        self._create_rescan_images_script(dest_dir=self.upgrade_dir)
        self._create_diff_script()

    def remove(self) -> None:
        """Remove the Backend.AI Python client."""
        self.remote._remove_python_env(self.python_venv_path, self.service_dir)
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    ClientPyDeploy(host.data).run(deploy_mode)


main()
