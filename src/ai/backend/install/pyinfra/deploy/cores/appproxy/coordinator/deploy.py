from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files

from ai.backend.install.pyinfra.deploy.cores.appproxy.base import AppProxyBaseDeploy
from ai.backend.install.pyinfra.deploy.cores.appproxy.constants import COORDINATOR_DIR, SERVICE_DIR


class AppProxyCoordinatorDeploy(AppProxyBaseDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self._init_common_properties(host_data)
        self._init_python_env(host_data)

        self.config_db = host_data.services["postgres"]

        self.python_coordinator_venv_path = f"{self.home_dir}/.static-python/venvs/bai-{self.appproxy_major_version}-appproxy-coordinator"

        self.service_dir = Path(SERVICE_DIR.format(home_dir=self.home_dir))
        self.coordinator_dir = Path(COORDINATOR_DIR.format(service_dir=self.service_dir))
        self.upgrade_dir = f"{self.coordinator_dir}/upgrades"

        self.service_name = "appproxy-coordinator"

    def _install_coordinator(self) -> None:
        # Use specific version to avoid installing latest from local repo
        version = self.config_bai_core.version
        self._install_package_by_name(
            "backend.ai appproxy coordinator",
            self.python_coordinator_venv_path,
            [
                f"backend.ai-appproxy-coordinator=={version}",
                f"backend.ai-appproxy-common=={version}",
            ],
        )

    def _create_coordinator_toml_file(self, dest_path: str | None = None) -> None:
        if dest_path is None:
            dest_path = f"{self.coordinator_dir}/app-proxy-coordinator.toml"

        files.template(
            name="Create app-proxy-coordinator.toml",
            src=str(self.locate_template("app-proxy-coordinator.toml.j2")),
            dest=dest_path,
            advertised_hostname=self.config.coordinator_advertised_hostname,
            port=self.config.coordinator_port,
            jwt_secret=self.config.jwt_secret,
            shared_key=self.config.shared_key,
            permit_hash_secret=self.config.permit_hash_secret,
            db_hostname=self.config_db.hostname,
            db_port=self.config_db.port,
            db_user=self.config.db_user,
            db_password=self.config.db_password,
            db_name=self.config.db_name,
            redis_hostname=self.config_redis.hostname,
            redis_port=self.config_redis.port,
            redis_password=self.config_redis.password,
            service_dir=self.coordinator_dir,
            user_id=self.user_id,
            group_id=self.group_id,
            enable_traefik=True,
            etcd_host=self.config_etcd.connect_client_ip,
            etcd_port=self.config_etcd.advertised_client_port,
            otel_collector_endpoint=self.get_otel_collector_endpoint(),
        )

    def _create_alembic_ini(self, dest_path: str | None = None) -> None:
        if dest_path is None:
            dest_path = f"{self.coordinator_dir}/alembic.ini"

        files.template(
            name="Create alembic.ini",
            src=str(self.locate_template("alembic.ini.j2")),
            dest=dest_path,
            db_hostname=self.config_db.hostname,
            db_port=self.config_db.port,
            db_name=self.config.db_name,
            db_user=self.config.db_user,
            db_password=self.config.db_password,
        )

    def _create_run_script(self, dest_path: str | None = None) -> None:
        if dest_path is None:
            dest_path = f"{self.home_dir}/bin/run-appproxy-coordinator.sh"

        files.template(
            name="Create run script for coordinator",
            src=str(self.locate_template("run-appproxy-coordinator.sh.j2")),
            dest=dest_path,
            mode="755",
            service_dir=self.coordinator_dir,
            redis_hostname=self.config_redis.hostname,
            redis_port=self.config_redis.port,
            service_name="appproxy-coordinator",
        )

    def create_service_manage_scripts(
        self,
        service_dir: Path | str | None = None,
        template_dir: str | None = None,
        extra_context: dict | None = None,
    ) -> None:
        """Override to use coordinator_dir instead of service_dir"""
        super().create_service_manage_scripts(
            service_dir=service_dir or self.coordinator_dir,
            template_dir=template_dir or "systemd",
            extra_context=extra_context or {"service_name": "backendai-appproxy-coordinator"},
        )

    def _create_systemd_service_file(self, dest_dir: str | None = None) -> None:
        """Create systemd service file.

        Args:
            dest_dir: Optional custom destination directory. If None, installs to /etc/systemd/system/.
        """
        dest = None if dest_dir is None else f"{dest_dir}/backendai-{self.service_name}.service"

        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_dir=self.coordinator_dir,
            exec_start=f"{self.home_dir}/bin/run-appproxy-coordinator.sh",
            user_id=self.user_id,
            group_id=self.group_id,
            dest=dest,
        )

    def _create_diff_script(self) -> None:
        """Create shell script to compare old vs new configurations."""
        files.template(
            name="Create diff comparison script",
            src=str(self.locate_template("scripts/show_diffs_coordinator.sh.j2")),
            dest=f"{self.upgrade_dir}/show_diffs.sh",
            mode="0755",
            user=self.user,
            upgrade_dir=self.upgrade_dir,
            coordinator_dir=self.coordinator_dir,
            home_dir=self.home_dir,
        )

    def _setup_coordinator(self) -> None:
        self.remote._create_python_env(
            self.python_path, self.python_coordinator_venv_path, self.coordinator_dir
        )
        self._install_coordinator()
        self._create_coordinator_toml_file()
        self._create_alembic_ini()
        self._create_run_script()
        self._create_systemd_service_file()
        self.start_service()
        self.create_service_manage_scripts()

        logger.warning(
            "ACTION REQUIRED: Run Alembic DB migration on one coordinator node:\n"
            f"  cd {self.coordinator_dir}\n"
            f"  {self.python_coordinator_venv_path}/bin/alembic upgrade head\n"
            "  ./stop.sh && ./start.sh"
        )

    def _cleanup_coordinator(self) -> None:
        self.stop_service()
        self.remote._remove_python_env(self.python_coordinator_venv_path, self.coordinator_dir)
        self.remove_systemd_service()
        files.file(path=f"{self.home_dir}/bin/run-appproxy-coordinator.sh", present=False)

    def install(self) -> None:
        self.create_directories(dirs=[self.service_dir, self.coordinator_dir])
        self._setup_coordinator()

    def remove(self) -> None:
        self._cleanup_coordinator()
        self.remove_directories(dirs=[self.coordinator_dir])

    def update(self) -> None:
        """Update the coordinator while preserving existing configurations."""
        logger.info("=== AppProxy Coordinator Update Mode ===")
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        # 1. Prepare directories
        self.create_directories(dirs=[self.upgrade_dir])

        # 2. Update packages
        self.remote._create_python_env(
            self.python_path, self.python_coordinator_venv_path, self.coordinator_dir
        )
        self._install_coordinator()

        # 3. Generate new configuration files to upgrade directory
        self._create_coordinator_toml_file(
            dest_path=f"{self.upgrade_dir}/app-proxy-coordinator.toml"
        )
        self._create_run_script(dest_path=f"{self.upgrade_dir}/run-appproxy-coordinator.sh")
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": "backendai-appproxy-coordinator"},
        )
        self._create_alembic_ini(dest_path=f"{self.upgrade_dir}/alembic.ini")
        self._create_systemd_service_file(dest_dir=self.upgrade_dir)

        # 4. Create diff comparison tool
        self._create_diff_script()


# Execute deployment when script is loaded
def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = AppProxyCoordinatorDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    elif deploy_mode == "update":
        deploy.update()
    else:
        deploy.install()


main()
