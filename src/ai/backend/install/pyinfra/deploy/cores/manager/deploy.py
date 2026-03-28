from pathlib import Path

from pyinfra import host, logger
from pyinfra.facts.hardware import Cpus
from pyinfra.operations import files, pip

from ai.backend.install.pyinfra.exceptions import DeploymentError
from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import ensure_file_exists, get_major_version


class ManagerDeploy(BaseSystemdDeploy):
    # Class constants
    PACKAGE_PREFIX = "backend.ai"
    SERVICE_NAME = "manager"
    FIXTURES_DIR = "fixtures"
    BIN_DIR = "bin"
    CONFIG_DIR = ".config/backend.ai"
    STATIC_PYTHON_DIR = ".static-python"
    UPGRADE_DIR = "upgrades"

    FIXTURE_FILES = [
        "users",
        "user-main-access-keys",
        "resource-presets",
        "container-registries-harbor",
        "etcd-config",
        "etcd-volumes",
    ]

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self._init_user_configs(host_data)
        self._init_service_configs(host_data)
        self._init_registry_configs(host_data)
        self._init_python_configs(host_data)

    def _init_user_configs(self, host_data: object) -> None:
        """Initialize user and directory configurations."""
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id
        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.service_name}")
        self.upgrade_dir = f"{self.service_dir}/{self.UPGRADE_DIR}"

    def _init_service_configs(self, host_data: object) -> None:
        """Initialize service-related configurations."""
        self.config = host_data.services["manager"]
        self.config_license_server = host_data.services["license_server"]
        self.config_db = host_data.services["postgres"]
        self.config_redis = host_data.services["redis"]
        self.config_redis_ha = host_data.services.get("redis_ha", None)
        self.config_etcd = host_data.services["etcd"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_storage_proxy = host_data.services["storage_proxy"]
        self.config_appproxy = host_data.services["appproxy"]
        # Use node-specific prometheus if deployed here, otherwise use shared prometheus_config
        self.config_prometheus = host_data.services.get("prometheus") or host_data.services.get(
            "prometheus_config"
        )
        self.config_otel_collector = self.get_otel_collector_config(host_data)

    def _init_registry_configs(self, host_data: object) -> None:
        """Initialize container registry configurations."""
        self.registry_type = host.data.registry_type
        self.registry_scheme = host.data.registry_scheme
        self.registry_name = host.data.registry_name
        self.registry_port = host.data.registry_port
        self.registry_username = host.data.registry_username
        self.registry_projects = host.data.registry_projects
        self.registry_password = host.data.registry_password

    def _init_python_configs(self, host_data: object) -> None:
        """Initialize Python environment configurations."""
        self.bai_major_version = get_major_version(self.config_bai_core.version)
        self.pip_install_options = host.data.bai_pip_install_options
        self.python_version = host.data.python_version
        self.python_path = (
            f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/versions/{self.python_version}/bin/python3"
        )
        self.python_venv_path = f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/venvs/bai-{self.bai_major_version}-{self.service_name}"

    def _install_service(self) -> None:
        """Install the manager service and its dependencies with error handling."""
        try:
            # Install main manager package
            pip.packages(
                name=f"Install {self.PACKAGE_PREFIX}-{self.service_name} version {self.config_bai_core.version}",
                packages=[
                    f"{self.PACKAGE_PREFIX}-{self.service_name}=={self.config_bai_core.version}"
                ],
                extra_install_args=self.pip_install_options,
                pip=f"{self.python_venv_path}/bin/pip",
                present=True,
            )

            # Install activator package
            if self.config_bai_core.activator_path:
                try:
                    ensure_file_exists(self.config_bai_core.activator_path)
                except FileNotFoundError as e:
                    raise DeploymentError(
                        f"Activator file not found: {self.config_bai_core.activator_path}"
                    ) from e

                pip.packages(
                    name=f"Install {self.PACKAGE_PREFIX}-activator from path: {self.config_bai_core.activator_path}",
                    packages=[self.config_bai_core.activator_path],
                    extra_install_args=self.pip_install_options,
                    pip=f"{self.python_venv_path}/bin/pip",
                    present=True,
                )
            else:
                pip.packages(
                    name=f"Install {self.PACKAGE_PREFIX}-activator from PyPI server",
                    packages=[f"{self.PACKAGE_PREFIX}-activator"],
                    extra_install_args=self.pip_install_options,
                    pip=f"{self.python_venv_path}/bin/pip",
                    present=True,
                )

        except Exception as e:
            error_msg = f"Failed to install {self.service_name} service: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _get_template_context(self) -> None:
        """Get template context with secure credential handling."""
        # Auto-detect remote server's CPU cores and cap num_proc
        remote_cpus = host.get_fact(Cpus)
        effective_num_proc = min(remote_cpus, self.config.num_proc)

        if effective_num_proc < self.config.num_proc:
            logger.info(
                f"Adjusting num_proc from {self.config.num_proc} to {effective_num_proc} "
                f"based on remote server's {remote_cpus} CPU cores"
            )

        return {
            # Basic service information
            "home_dir": self.home_dir,
            "service_name": self.service_name,
            # Manager configuration
            "manager_service_port": self.config.port,
            "manager_num_proc": effective_num_proc,
            "manager_internal_host": self.config.internal_host,
            "manager_internal_port": self.config.internal_port,
            # License server configuration
            "licensed_ip": self.config_license_server.hostname,
            "licensed_port": self.config_license_server.port,
            # ETCD configuration
            "etcd_ip": self.config_etcd.connect_client_ip,
            "etcd_port": self.config_etcd.advertised_client_port,
            # Database configuration
            "db_ip": self.config_db.hostname,
            "db_port": self.config_db.port,
            "db_name": self.config_db.db_name,
            "db_user": self.config_db.user,
            "db_password": self.config_db.password,
            "db_pool_size": self.config.db_pool_size,
            # Monitoring configuration
            "otel_collector_endpoint": self.get_otel_collector_endpoint(),
        }

    def _create_toml_config_file(self, dest_path: str | None = None) -> None:
        """Create TOML configuration file with secure credential handling.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.
        """
        try:
            template_context = self._get_template_context()
            self.create_toml_config(
                dest_path=dest_path,
                create_symlink=(dest_path is None),  # Only create symlink for default install
                **template_context,
            )
        except Exception as e:
            error_msg = f"Failed to create TOML configuration file: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _prepare_redis_config(self) -> None:
        """Prepare Redis configuration including HA sentinel information if configured."""
        redis_sentinels = None
        if hasattr(self, "config_redis_ha") and self.config_redis_ha:
            redis_sentinels = [
                {"hostname": node.hostname, "port": self.config_redis_ha.sentinel_port}
                for node in self.config_redis_ha.cluster_nodes
            ]
        return {
            "redis_ip": self.config_redis.hostname,
            "redis_port": self.config_redis.port,
            "redis_sentinels": redis_sentinels,
        }

    def _create_run_script(self, dest_dir: str | None = None) -> None:
        """Create run script with Redis and ETCD configuration.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        try:
            redis_config = self._prepare_redis_config()

            self.create_run_script(
                dest_dir=dest_dir,
                home_dir=self.home_dir,
                service_name=self.service_name,
                etcd_ip=self.config_etcd.connect_client_ip,
                etcd_port=self.config_etcd.advertised_client_port,
                **redis_config,
            )

        except Exception as e:
            error_msg = f"Failed to create run script: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _create_alembic_ini(self, dest_path: str | None = None) -> None:
        """Create Alembic configuration file for database migrations.

        Args:
            dest_path: Optional custom destination path. If None, uses default location.
        """
        try:
            if dest_path is None:
                dest_path = f"{self.service_dir}/alembic.ini"

            files.template(
                name="Create alembic.ini",
                src=str(self.locate_template("alembic.ini.j2")),
                dest=dest_path,
                db_ip=self.config_db.hostname,
                db_port=self.config_db.port,
                db_name=self.config_db.db_name,
                db_user=self.config_db.user,
                db_password=self.config_db.password,
            )
        except Exception as e:
            error_msg = f"Failed to create Alembic configuration: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _get_fixtures_context(self) -> None:
        """Get fixtures template context with all required configuration values."""
        # Determine prometheus address if prometheus is configured
        prometheus_addr = None
        if self.config_prometheus:
            prometheus_addr = f"{self.config_prometheus.hostname}:{self.config_prometheus.port}"

        # Determine OTEL Collector endpoint if configured
        otel_collector_endpoint = None
        if self.config_otel_collector:
            otel_collector_endpoint = f"http://{self.config_otel_collector.hostname}:{self.config_otel_collector.grpc_port}"

        return {
            # Manager and user configurations
            "default_project_uuid": self.config.default_project_uuid,
            "superadmin_uuid": self.config.superadmin_uuid,
            "superadmin_email": self.config.superadmin_email,
            "superadmin_username": self.config.superadmin_username,
            "superadmin_password": self.config.superadmin_password,
            "superadmin_access_key": self.config.superadmin_access_key,
            "superadmin_secret_key": self.config.superadmin_secret_key,
            "user_uuid": self.config.user_uuid,
            "user_email": self.config.user_email,
            "user_username": self.config.user_username,
            "user_password": self.config.user_password,
            "user_access_key": self.config.user_access_key,
            "user_secret_key": self.config.user_secret_key,
            # Redis configurations
            "redis_ip": self.config_redis.hostname,
            "redis_port": self.config_redis.port,
            "redis_password": self.config_redis.password,
            "redis_ha_config": self.config_redis_ha,
            # Storage proxy configurations
            "storageproxy_client_endpoint": self.config_storage_proxy.client_endpoint,
            "storageproxy_manager_endpoint": self.config_storage_proxy.manager_endpoint,
            "storageproxy_manager_token": self.config_storage_proxy.manager_token,
            "storageproxy_name": self.config_storage_proxy.name,
            "storageproxy_volume_names": self.config_storage_proxy.volume_names,
            # App proxy configurations
            "appproxy_coordinator_ip": self.config_appproxy.coordinator_advertised_hostname,
            "appproxy_coordinator_port": self.config_appproxy.coordinator_port,
            "appproxy_coordinator_scheme": self.config_appproxy.coordinator_scheme,
            "appproxy_shared_key": self.config_appproxy.shared_key,
            # Registry configurations
            "registry_type": self.registry_type,
            "registry_scheme": self.registry_scheme,
            "registry_name": self.registry_name,
            "registry_port": self.registry_port,
            "registry_username": self.registry_username,
            "registry_projects": self.registry_projects,
            "registry_password": self.registry_password,
            # Monitoring configurations
            "prometheus_addr": prometheus_addr,
            "otel_collector_endpoint": otel_collector_endpoint,
        }

    def _create_db_fixtures(self, dest_dir: str | None = None) -> None:
        """Create database fixture files for initial setup.

        Note: This only creates the fixture JSON files. Actual population into the database
        is done separately via deploy_fixtures.py and should be executed only once in HA setups.

        Args:
            dest_dir: Optional custom destination directory. If None, uses default location.
        """
        try:
            if dest_dir is None:
                dest_dir = str(self.service_dir)

            fixtures_context = self._get_fixtures_context()
            for fixture in self.FIXTURE_FILES:
                files.template(
                    name=f"Create fixtures: {self.FIXTURES_DIR}/{fixture}.json",
                    src=str(self.locate_template(f"{self.FIXTURES_DIR}/{fixture}.json.j2")),
                    dest=f"{dest_dir}/{self.FIXTURES_DIR}/{fixture}.json",
                    **fixtures_context,
                )
        except Exception as e:
            error_msg = f"Failed to create database fixtures: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _create_systemd_service_file(self, dest_dir: str | None = None) -> None:
        """Create systemd service file.

        Args:
            dest_dir: Optional custom destination directory. If None, installs to /etc/systemd/system/.
        """
        dest = None if dest_dir is None else f"{dest_dir}/backendai-{self.service_name}.service"
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_dir=self.service_dir,
            exec_start=f"{self.home_dir}/{self.BIN_DIR}/run-{self.service_name}.sh",
            user_id=self.user_id,
            group_id=self.group_id,
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
            bin_dir=self.BIN_DIR,
            config_dir=self.CONFIG_DIR,
            service_name=self.service_name,
            fixture_files=self.FIXTURE_FILES,
        )

    def install(self) -> None:
        """Install and configure the manager service with all dependencies."""
        self.create_directories(
            dirs=[
                self.service_dir,
                f"{self.home_dir}/{self.BIN_DIR}",
                f"{self.home_dir}/{self.CONFIG_DIR}",
                f"{self.service_dir}/{self.FIXTURES_DIR}",
            ]
        )
        self.create_python_venv()
        self._install_service()

        self._create_toml_config_file()
        self._create_run_script()
        self.create_service_manage_scripts(
            extra_context={"service_name": f"backendai-{self.service_name}"}
        )
        self._create_alembic_ini()
        self._create_db_fixtures()
        self._create_systemd_service_file()

        self.start_service()

    def update(self) -> None:
        """Update the manager service while preserving existing configurations."""
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        self.create_directories(dirs=[self.upgrade_dir, f"{self.upgrade_dir}/{self.FIXTURES_DIR}"])
        self.create_python_venv()
        self._install_service()

        self._create_toml_config_file(dest_path=f"{self.upgrade_dir}/{self.service_name}.toml")
        self._create_run_script(dest_dir=self.upgrade_dir)
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": f"backendai-{self.service_name}"},
        )
        self._create_alembic_ini(dest_path=f"{self.upgrade_dir}/alembic.ini")
        self._create_db_fixtures(dest_dir=self.upgrade_dir)
        self._create_systemd_service_file(dest_dir=self.upgrade_dir)
        self._create_diff_script()

    def remove(self) -> None:
        """Remove the manager service and clean up all related files and configurations."""
        self.stop_service()
        self.remove_python_venv()
        self.remove_systemd_service()
        self.remove_toml_config()
        self.remove_run_script()
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    ManagerDeploy(host.data).run(deploy_mode)


main()
