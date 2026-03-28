from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.facts.server import Hostname
from pyinfra.operations import files, pip, server

from ai.backend.install.pyinfra.exceptions import DeploymentError
from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import get_major_version


class StorageProxyDeploy(BaseSystemdDeploy):
    """Deploy Backend.AI Storage Proxy service with systemd management."""

    # Class constants
    PACKAGE_PREFIX = "backend.ai"
    SERVICE_NAME = "storage-proxy"
    BIN_DIR = "bin"
    CONFIG_DIR = ".config/backend.ai"
    STATIC_PYTHON_DIR = ".static-python"
    DEFAULT_VOLUME_VERSION = "3"
    UPGRADE_DIR = "upgrades"

    def __init__(self, host_data: Any) -> None:
        """Initialize Storage Proxy deployment configuration.

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

    def _init_service_configs(self, host_data: Any) -> None:
        """Initialize service-related configurations.

        Args:
            host_data: Host-specific configuration data
        """
        self.config = host_data.services["storage_proxy"]
        self.config_redis = host_data.services["redis"]
        self.config_etcd = host_data.services["etcd"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_otel_collector = self.get_otel_collector_config(host_data)

        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.service_name}")
        self.upgrade_dir = f"{self.service_dir}/{self.UPGRADE_DIR}"
        self.vfroot_path = Path(self.config_bai_core.vfroot_path)

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
        """Install Backend.AI Storage Proxy package via pip.

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

    def _setup_volume_directories(self) -> None:
        """Prepare vfroot volume directories with version.txt files.

        Creates volume directories and version files for NFS compatibility.

        Raises:
            DeploymentError: If volume directory setup fails
        """
        try:
            for volume in self.config.volume_names.split(","):
                abs_vol_path = self.vfroot_path / volume
                # Create directory without ownership change (for NFS compatibility)
                files.directory(path=abs_vol_path, present=True, _sudo=True, _ignore_errors=True)

                # Create version.txt file if it doesn't exist
                version_file_path = abs_vol_path / "version.txt"
                server.shell(
                    name=f"Create version.txt in {volume} volume",
                    commands=[
                        f"test -f {version_file_path} || echo '{self.DEFAULT_VOLUME_VERSION}' > {version_file_path}",
                        f"chown {self.user_id}:{self.group_id} {version_file_path} 2>/dev/null || true",
                    ],
                    _sudo=True,
                )
        except Exception as e:
            error_msg = f"Failed to setup volume directories: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _get_template_context(self) -> dict[str, Any]:
        """Get template context for TOML configuration.

        Returns:
            Dictionary containing all configuration values for template rendering
        """
        # Generate unique node ID based on actual server hostname
        hostname = host.get_fact(Hostname)
        node_id = f"i-storage-proxy-{hostname}"

        manager_port = getattr(self.config, "manager_port", 6024)

        return {
            "user_id": self.user_id,
            "group_id": self.group_id,
            "service_name": self.service_name,
            "node_id": node_id,
            "etcd_ip": self.config_etcd.connect_client_ip,
            "etcd_port": self.config_etcd.advertised_client_port,
            "client_port": self.config.port,
            "manager_port": manager_port,
            "manager_token": self.config.manager_token,
            "jwt_secret": self.config.jwt_secret,
            "internal_host": self.config.internal_host,
            "internal_port": self.config.internal_port,
            "announce_internal_host": self.config.announce_internal_host,
            "announce_internal_port": self.config.announce_internal_port,
            "volume_names": self.config.volume_names,
            "vfroot_path": self.vfroot_path,
            "otel_collector_endpoint": self.get_otel_collector_endpoint(),
        }

    def _create_toml_config_file(self, dest_path: str | None = None) -> None:
        """Create TOML configuration file for Storage Proxy service.

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

    def _create_run_script(self, dest_dir: str | None = None) -> None:
        """Create run script with Redis and ETCD configuration.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.

        Raises:
            DeploymentError: If run script creation fails
        """
        try:
            self.create_run_script(
                dest_dir=dest_dir,
                home_dir=self.home_dir,
                service_name=self.service_name,
                redis_ip=self.config_redis.hostname,
                redis_port=self.config_redis.port,
                etcd_ip=self.config_etcd.connect_client_ip,
                etcd_port=self.config_etcd.advertised_client_port,
            )
        except Exception as e:
            error_msg = f"Failed to create run script: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _create_systemd_service_file(self, dest_dir: str | None = None) -> None:
        """Create systemd service file.

        Args:
            dest_dir: Optional custom destination directory. If None, installs to /etc/systemd/system/.

        Raises:
            DeploymentError: If systemd service file creation fails
        """
        try:
            dest = None if dest_dir is None else f"{dest_dir}/backendai-{self.service_name}.service"

            self.create_systemd_service(
                src=self.locate_template("systemd/service.j2"),
                service_dir=self.service_dir,
                exec_start=f"{self.home_dir}/{self.BIN_DIR}/run-{self.service_name}.sh",
                user_id=self.user_id,
                group_id=self.group_id,
                dest=dest,
            )
        except Exception as e:
            error_msg = f"Failed to create systemd service file: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def install(self) -> None:
        """Install and configure Storage Proxy service.

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
            self._setup_volume_directories()
            self._create_toml_config_file()
            self._create_run_script()
            self.create_service_manage_scripts(
                extra_context={"service_name": f"backendai-{self.service_name}"}
            )
            self._create_systemd_service_file()
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
        """Update the storage-proxy service while preserving existing configurations."""
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        self.create_directories(dirs=[self.upgrade_dir])
        self.create_python_venv()
        self._install_service()

        self._create_toml_config_file(dest_path=f"{self.upgrade_dir}/{self.service_name}.toml")
        self._create_run_script(dest_dir=self.upgrade_dir)
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": f"backendai-{self.service_name}"},
        )
        self._create_systemd_service_file(dest_dir=self.upgrade_dir)
        self._create_diff_script()

    def remove(self) -> None:
        """Remove Storage Proxy service and clean up resources.

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
    """Main entry point for Storage Proxy deployment."""
    deploy_mode = host.data.get("mode", "install")
    StorageProxyDeploy(host.data).run(deploy_mode)


main()
