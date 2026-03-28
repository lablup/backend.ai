from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.operations import files, pip

from ai.backend.install.pyinfra.exceptions import ConfigurationError, DeploymentError
from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import get_major_version


class WebserverDeploy(BaseSystemdDeploy):
    """Deploy Backend.AI Webserver service with systemd management."""

    # Class constants
    PACKAGE_PREFIX = "backend.ai"
    SERVICE_NAME = "webserver"
    BIN_DIR = "bin"
    CONFIG_DIR = ".config/backend.ai"
    STATIC_PYTHON_DIR = ".static-python"
    UPGRADE_DIR = "upgrades"

    def __init__(self, host_data: Any) -> None:
        """Initialize Webserver deployment configuration.

        Args:
            host_data: Host-specific configuration data containing service configs and paths
        """
        super().__init__()
        self._init_user_configs(host_data)
        self._init_service_configs(host_data)
        self._init_python_configs(host_data)

    def _init_user_configs(self, host_data: Any) -> None:
        """Initialize user and directory configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id
        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.service_name}")
        self.upgrade_dir = f"{self.service_dir}/{self.UPGRADE_DIR}"

    def _init_service_configs(self, host_data: Any) -> None:
        """Initialize service-related configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.config = host_data.services["webserver"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_manager = host_data.services["manager"]
        self.config_redis = host_data.services["redis"]
        self.config_fasttrack = host_data.services["fasttrack"]
        self.config_otel_collector = self.get_otel_collector_config(host_data)

        # Construct manager API endpoint based on HAProxy availability
        self.manager_api_endpoint = (
            f"http://{self.config_manager.client_connect_ip}:"
            f"{self.config_manager.haproxy_service_port or self.config_manager.port}"
        )

        # Hive Gateway configuration (required for WebUI)
        self.config_hive_gateway = host_data.services.get("hive_gateway")
        if self.config_hive_gateway is None or not self.config_hive_gateway.enabled:
            raise ConfigurationError(
                "Hive Gateway is required for WebUI but not configured or disabled. "
                "Ensure hive_gateway is present in services with enabled=True."
            )

        self.hive_gateway_endpoint = (
            f"http://{self.config_hive_gateway.advertised_hostname}:{self.config_hive_gateway.port}"
        )

    def _init_python_configs(self, host_data: Any) -> None:
        """Initialize Python environment configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.bai_major_version = get_major_version(self.config_bai_core.version)
        self.pip_install_options = host_data.bai_pip_install_options
        self.python_version = host_data.python_version
        self.python_path = (
            f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/versions/{self.python_version}/bin/python3"
        )
        self.python_venv_path = f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/venvs/bai-{self.bai_major_version}-{self.service_name}"

    def _install_service(self) -> None:
        """Install Backend.AI Webserver package via pip.

        Raises:
            DeploymentError: If package installation fails
        """
        try:
            pip.packages(
                name=f"Install {self.PACKAGE_PREFIX}-{self.service_name}",
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

    def _get_template_context(self) -> dict[str, Any]:
        """Get template context for TOML configuration.

        Returns:
            Dictionary containing all configuration values for template rendering
        """
        return {
            "service_name": self.service_name,
            "service_port": self.config.port,
            "webserver_config": self.config,
            "redis_ip": self.config_redis.hostname,
            "redis_port": self.config_redis.port,
            "redis_password": self.config_redis.password,
            "manager_api_endpoint": self.manager_api_endpoint,
            "fasttrack_endpoint": self.config_fasttrack.endpoint,
            "otel_collector_endpoint": self.get_otel_collector_endpoint(),
            "hive_gateway_endpoint": self.hive_gateway_endpoint,
        }

    def _create_toml_config_file(self, dest_path: str | None = None) -> None:
        """Create TOML configuration file for Webserver service.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.

        Raises:
            DeploymentError: If configuration file creation fails
        """
        try:
            context = self._get_template_context()
            self.create_toml_config(
                dest_path=dest_path,
                create_symlink=(dest_path is None),
                **context,
            )
        except Exception as e:
            error_msg = f"Failed to create TOML config file: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def install(self) -> None:
        """Install and configure Webserver service.

        Creates directories, installs packages, generates configurations,
        and starts the systemd service.

        Raises:
            DeploymentError: If any installation step fails
        """
        try:
            self.create_directories(
                dirs=[
                    self.service_dir,
                    f"{self.home_dir}/{self.BIN_DIR}",
                    f"{self.home_dir}/{self.CONFIG_DIR}",
                ]
            )
            self.create_python_venv()
            self._install_service()
            self._create_toml_config_file()
            self.create_run_script(
                home_dir=self.home_dir,
                service_name=self.service_name,
            )
            self.create_service_manage_scripts(
                extra_context={"service_name": f"backendai-{self.service_name}"}
            )
            self.create_systemd_service(
                src=self.locate_template("systemd/service.j2"),
                service_dir=self.service_dir,
                exec_start=f"{self.home_dir}/{self.BIN_DIR}/run-{self.service_name}.sh",
                user_id=self.user_id,
                group_id=self.group_id,
            )
            self.start_service()
        except DeploymentError:
            raise
        except Exception as e:
            error_msg = f"Failed to install {self.service_name}: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

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
            home_dir=self.home_dir,
            bin_dir=self.BIN_DIR,
            config_dir=self.CONFIG_DIR,
            service_name=self.service_name,
        )

    def update(self) -> None:
        """Update the webserver service while preserving existing configurations."""
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        self.create_directories(dirs=[self.upgrade_dir])
        self.create_python_venv()
        self._install_service()

        self._create_toml_config_file(dest_path=f"{self.upgrade_dir}/{self.service_name}.toml")
        self.create_run_script(
            dest_dir=self.upgrade_dir,
            home_dir=self.home_dir,
            service_name=self.service_name,
        )
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": f"backendai-{self.service_name}"},
        )
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_dir=self.service_dir,
            exec_start=f"{self.home_dir}/{self.BIN_DIR}/run-{self.service_name}.sh",
            user_id=self.user_id,
            group_id=self.group_id,
            dest=f"{self.upgrade_dir}/backendai-{self.service_name}.service",
        )
        self._create_diff_script()

    def remove(self) -> None:
        """Remove Webserver service and clean up resources.

        Stops the service before removing configurations and files.

        Raises:
            DeploymentError: If removal fails
        """
        try:
            self.stop_service()
            self.remove_python_venv()
            self.remove_toml_config()
            self.remove_run_script()
            self.remove_systemd_service()
            self.remove_directories()
        except Exception as e:
            error_msg = f"Failed to remove {self.service_name}: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e


def main() -> None:
    """Main entry point for Webserver deployment."""
    deploy_mode = host.data.get("mode", "install")
    WebserverDeploy(host.data).run(deploy_mode)


main()
