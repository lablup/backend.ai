from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files, pip, systemd

from ai.backend.install.pyinfra.configs.cores import AcceleratorType
from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import ensure_file_exists, get_major_version


class AgentDeploy(BaseSystemdDeploy):
    PACKAGE_PREFIX = "backend.ai-"
    SERVICE_PREFIX = "backendai-"

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config = host_data.services["agent"]
        self.config_etcd = host_data.services["etcd"]
        self.config_redis = host_data.services["redis"]
        self.config_license_server = host_data.services["license_server"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_storage_proxy = host_data.services["storage_proxy"]
        self.config_otel_collector = self.get_otel_collector_config(host_data)

        self.service_name = "agent"
        self.service_dir = Path(f"{self.home_dir}/{self.service_name}")
        self.upgrade_dir = f"{self.service_dir}/upgrades"

        self.bai_major_version = get_major_version(self.config_bai_core.version)
        self.pip_install_options = host.data.bai_pip_install_options
        self.python_version = host.data.python_version
        self.python_path = (
            f"{self.home_dir}/.static-python/versions/{self.python_version}/bin/python3"
        )
        self.python_venv_path = (
            f"{self.home_dir}/.static-python/venvs/bai-{self.bai_major_version}-{self.service_name}"
        )

        self.vfroot_path = Path(self.config_bai_core.vfroot_path)

    def _install_pip_package(
        self, package_name: str, local_path: str | None, pypi_package: str
    ) -> None:
        """Install a package from local path if available, otherwise from PyPI.

        Args:
            package_name: Human-readable name for the installation task
            local_path: Local file path to the package (if available)
            pypi_package: PyPI package name to use as fallback
        """
        if local_path:
            ensure_file_exists(local_path)
            packages = [local_path]
            name_suffix = ""
        else:
            packages = [pypi_package]
            name_suffix = " from PyPI"

        pip.packages(
            name=f"Install {package_name}{name_suffix}",
            packages=packages,
            extra_install_args=self.pip_install_options,
            pip=f"{self.python_venv_path}/bin/pip",
            present=True,
        )

    def _install_agent_package(self) -> None:
        """Install the main backend.ai-agent package."""
        pip.packages(
            name=f"Install {self.PACKAGE_PREFIX}{self.service_name}",
            packages=[f"{self.PACKAGE_PREFIX}{self.service_name}=={self.config_bai_core.version}"],
            extra_install_args=self.pip_install_options,
            pip=f"{self.python_venv_path}/bin/pip",
            present=True,
        )

    def _install_activator_if_needed(self) -> None:
        """Install backend.ai-activator if GPU acceleration is enabled."""
        if self.config.accelerator_type != AcceleratorType.CPU:
            self._install_pip_package(
                package_name=f"{self.PACKAGE_PREFIX}activator",
                local_path=self.config_bai_core.activator_path,
                pypi_package=f"{self.PACKAGE_PREFIX}activator",
            )

    def _install_accelerator_plugin(self) -> None:
        """Install accelerator-specific plugin based on configured accelerator type."""
        if self.config.accelerator_type == AcceleratorType.CUDA:
            self._install_pip_package(
                package_name=f"{self.PACKAGE_PREFIX}CUDA accelerator plugin",
                local_path=self.config.accelerator_cuda_path,
                pypi_package=f"{self.PACKAGE_PREFIX}accelerator-cuda",
            )
        elif self.config.accelerator_type in (
            AcceleratorType.ATOM,
            AcceleratorType.ATOM_PLUS,
            AcceleratorType.ATOM_MAX,
        ):
            self._install_pip_package(
                package_name=f"{self.PACKAGE_PREFIX}ATOM accelerator plugin",
                local_path=self.config.accelerator_atom_path,
                pypi_package=f"{self.PACKAGE_PREFIX}accelerator-atom",
            )

    def _install_service(self) -> None:
        """Install all required packages for the agent service."""
        self._install_agent_package()
        self._install_activator_if_needed()
        self._install_accelerator_plugin()

    def _prepare_vfroot_volume_directories(self) -> None:
        """Create vfroot volume directories for storage proxy integration.

        Errors are ignored because directories may already exist or there could be
        permission issues on shared storage (e.g., NFS mounts).
        """
        for volume in self.config_storage_proxy.volume_names.split(","):
            abs_vol_path = self.vfroot_path / volume
            files.directory(
                path=abs_vol_path,
                present=True,
                user=self.user_id,
                group=self.group_id,
                _sudo=True,
                _ignore_errors=True,  # Directory may already exist or be on shared storage
            )

    def _create_toml_config_file(self, dest_path: str | None = None) -> None:
        """Generate agent TOML configuration file with service and network settings.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.
        """
        config_params = {
            "home_dir": self.home_dir,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "service_name": self.service_name,
            "etcd_ip": self.config_etcd.connect_client_ip,
            "etcd_port": self.config_etcd.advertised_client_port,
            "licensed_ip": self.config_license_server.hostname,
            "licensed_port": self.config_license_server.port,
            "resource_group": self.config.resource_group,
            "resource_group_type": self.config.resource_group_type,
            "rpc_listen_ip": self.config.rpc_listen_ip,
            "rpc_advertised_ip": self.config.rpc_advertised_ip,
            "announce_internal_host": self.config.announce_internal_host,
            "announce_internal_port": self.config.announce_internal_port,
            "metadata_server_port": self.config.metadata_server_port,
            "container_port_range_start": self.config.container_port_range[0],
            "container_port_range_end": self.config.container_port_range[1],
            "vfroot_path": self.config_bai_core.vfroot_path,
            "scratch_type": self.config.scratch_type,
            "scratch_root": self.config.scratch_root,
            "scratch_size": self.config.scratch_size,
            "public_host": getattr(self.config, "public_host", None),
            "otel_collector_endpoint": self.get_otel_collector_endpoint(),
        }
        self.create_toml_config(
            dest_path=dest_path,
            create_symlink=(dest_path is None),
            **config_params,
        )

    def _create_agent_docker_container_opts(self, dest_path: str | None = None) -> None:
        """Generate Docker container options configuration for agent.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.
        """
        if dest_path is None:
            dest_path = f"{self.service_dir}/agent-docker-container-opts.json"

        files.template(
            name="Create agent-docker-container-opts.json",
            src=str(self.locate_template("agent-docker-container-opts.json.j2")),
            dest=dest_path,
        )

    def _create_agent_run_script(self, dest_dir: str | None = None) -> None:
        """Generate the main agent service run script with Redis and ETCD configuration.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        self.create_run_script(
            dest_dir=dest_dir,
            home_dir=self.home_dir,
            service_name=self.service_name,
            redis_ip=self.config_redis.hostname,
            redis_port=self.config_redis.port,
            etcd_ip=self.config_etcd.connect_client_ip,
            etcd_port=self.config_etcd.advertised_client_port,
        )

    def _create_watcher_run_script(self, dest_dir: str | None = None) -> None:
        """Generate the agent watcher service run script for monitoring agent health.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        self.create_run_script(
            dest_dir=dest_dir,
            template_name="run-watcher.sh.j2",
            script_name="run-watcher.sh",
            home_dir=self.home_dir,
        )

    def _create_run_script(self, dest_dir: str | None = None) -> None:
        """Generate all run scripts for agent and watcher services.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        self._create_agent_run_script(dest_dir=dest_dir)
        self._create_watcher_run_script(dest_dir=dest_dir)

    def _create_systemd_service_file(
        self, service_name: str | None = None, dest_dir: str | None = None
    ) -> None:
        """Create systemd service file.

        Args:
            service_name: Service name (without 'backendai-' prefix). If None, uses self.service_name
            dest_dir: Optional custom destination directory. If None, installs to /etc/systemd/system/.
        """
        svc_name = service_name or self.service_name
        dest = None if dest_dir is None else f"{dest_dir}/backendai-{svc_name}.service"

        if svc_name == "watcher":
            exec_start = f"{self.home_dir}/bin/run-watcher.sh"
        else:
            exec_start = f"{self.home_dir}/bin/run-{self.service_name}.sh"

        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_name=svc_name,
            service_dir=self.service_dir,
            exec_start=exec_start,
            dest=dest,
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
            home_dir=self.home_dir,
            service_name=self.service_name,
        )

    def install(self) -> None:
        """Install and configure the Backend.AI agent service.

        This method orchestrates the complete installation process including:
        - Creating necessary directories and Python virtual environment
        - Installing agent packages and accelerator plugins
        - Configuring TOML files and Docker container options
        - Setting up systemd services for agent and watcher
        """
        self.create_directories(
            dirs=[
                self.service_dir,
                f"{self.home_dir}/bin",
                f"{self.home_dir}/.config/backend.ai",
            ]
        )
        self.create_python_venv()
        self._install_service()
        self._prepare_vfroot_volume_directories()
        self._create_toml_config_file()
        self._create_agent_docker_container_opts()
        self._create_run_script()
        self.create_service_manage_scripts(
            extra_context={"service_name": f"{self.SERVICE_PREFIX}{self.service_name}"}
        )
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_name="watcher",
            service_dir=self.service_dir,
            exec_start=f"{self.home_dir}/bin/run-watcher.sh",
        )
        systemd.service(
            service=f"{self.SERVICE_PREFIX}watcher.service",
            running=True,
            _sudo=True,
        )
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_dir=self.service_dir,
            exec_start=f"{self.home_dir}/bin/run-{self.service_name}.sh",
        )
        self.start_service()

    def remove(self) -> None:
        """Remove the Backend.AI agent service and all related configurations.

        This method cleans up all installed components including:
        - Python virtual environment
        - Configuration files
        - Run scripts
        - Systemd services (agent and watcher)
        - Service directories
        """
        self.remove_python_venv()
        self.remove_toml_config()
        self.remove_run_script()
        self.remove_run_script(script_name="run-watcher.sh")
        self.remove_systemd_service()
        self.remove_systemd_service(service_name="watcher")
        self.remove_directories()

    def update(self) -> None:
        """Update the agent while preserving existing configurations."""
        logger.info("=== Agent Update Mode ===")
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        # 1. Prepare directories
        self.create_directories(dirs=[self.upgrade_dir])

        # 2. Update packages
        self.create_python_venv()
        self._install_service()

        # 3. Generate new configuration files to upgrade directory
        self._create_toml_config_file(dest_path=f"{self.upgrade_dir}/{self.service_name}.toml")
        self._create_agent_docker_container_opts(
            dest_path=f"{self.upgrade_dir}/agent-docker-container-opts.json"
        )
        self._create_run_script(dest_dir=self.upgrade_dir)
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": f"{self.SERVICE_PREFIX}{self.service_name}"},
        )
        self._create_systemd_service_file(dest_dir=self.upgrade_dir)
        self._create_systemd_service_file(service_name="watcher", dest_dir=self.upgrade_dir)

        # 4. Create diff comparison tool
        self._create_diff_script()


def main() -> None:
    """Entry point for agent deployment script."""
    deploy_mode = host.data.get("mode", "install")
    deploy = AgentDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    elif deploy_mode == "update":
        deploy.update()
    else:
        deploy.install()


main()
