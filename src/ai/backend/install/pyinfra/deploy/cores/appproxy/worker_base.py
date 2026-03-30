from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files

from ai.backend.install.pyinfra.deploy.cores.appproxy.base import AppProxyBaseDeploy
from ai.backend.install.pyinfra.deploy.cores.appproxy.constants import (
    SERVICE_DIR,
    create_worker_config,
)


class AppProxyWorkerBaseDeploy(AppProxyBaseDeploy):
    def __init__(self, host_data: object, worker_type: str) -> None:
        super().__init__()
        self._init_common_properties(host_data)
        self._init_python_env(host_data)

        self.python_worker_venv_path = f"{self.home_dir}/.static-python/venvs/bai-{self.appproxy_major_version}-appproxy-worker"

        self.service_dir = Path(SERVICE_DIR.format(home_dir=self.home_dir))
        self.worker_type = worker_type
        self.worker_config = create_worker_config(self.service_dir, self.config, self.worker_type)
        self.upgrade_dir = f"{self.worker_config['dir']}/upgrades"

        self.service_name = self.worker_config["service_name"]

    def _install_worker(self) -> None:
        # Use specific version to avoid installing latest from local repo
        version = self.config_bai_core.version
        self._install_package_by_name(
            "backend.ai appproxy worker",
            self.python_worker_venv_path,
            [f"backend.ai-appproxy-worker=={version}", f"backend.ai-appproxy-common=={version}"],
        )

    def _create_worker_toml_file(self, dest_path: str | None = None) -> None:
        # Use VIP for coordinator endpoint and actual node public IP for advertised hostname
        coordinator_vip = getattr(self.config, "coordinator_vip_hostname", "bai-apc-vip")
        actual_public_ip = getattr(
            host.data, "public_ip", self.worker_config["advertised_hostname"]
        )

        if dest_path is None:
            dest_path = f"{self.worker_config['dir']}/app-proxy-worker.toml"

        files.template(
            name=f"Create app-proxy-worker.toml ({self.worker_type})",
            src=str(self.locate_template("app-proxy-worker.toml.j2")),
            dest=dest_path,
            advertised_hostname=actual_public_ip,
            port=self.worker_config["port"],
            authority=self.worker_config["authority"],
            aiomonitor_termui_port=self.worker_config["aiomonitor_termui_port"],
            aiomonitor_webui_port=self.worker_config["aiomonitor_webui_port"],
            protocol=self.worker_config["protocol"],
            accepted_traffic=self.worker_config["accepted_traffic"],
            app_port_start=self.worker_config["app_port_start"],
            app_port_end=self.worker_config["app_port_end"],
            coordinator_endpoint=coordinator_vip,
            coordinator_port=self.config.coordinator_port,
            jwt_secret=self.config.jwt_secret,
            shared_key=self.config.shared_key,
            permit_hash_secret=self.config.permit_hash_secret,
            redis_hostname=self.config_redis.hostname,
            redis_port=self.config_redis.port,
            redis_password=self.config_redis.password,
            service_dir=self.worker_config["dir"],
            user_id=self.user_id,
            group_id=self.group_id,
            frontend_mode="traefik",
            traefik_api_port=self.worker_config["traefik_api_port"],
            traefik_last_used_dir=f"{self.service_dir}/traefik/{self.worker_type}",
            etcd_host=self.config_etcd.connect_client_ip,
            etcd_port=self.config_etcd.advertised_client_port,
            otel_collector_endpoint=self.get_otel_collector_endpoint(),
        )

    def _create_run_script(self, dest_path: str | None = None) -> None:
        if dest_path is None:
            dest_path = f"{self.home_dir}/bin/{self.worker_config['run_script_name']}"

        files.template(
            name=f"Create run script for {self.worker_config['service_name']}",
            src=str(self.locate_template("run-appproxy-worker.sh.j2")),
            dest=dest_path,
            mode="755",
            service_dir=self.worker_config["dir"],
            redis_hostname=self.config_redis.hostname,
            redis_port=self.config_redis.port,
            service_name=self.worker_config["service_name"],
        )

    def create_service_manage_scripts(
        self,
        service_dir: Path | str | None = None,
        template_dir: str | None = None,
        extra_context: dict | None = None,
    ) -> None:
        """Override to use worker_config['dir'] instead of service_dir"""
        super().create_service_manage_scripts(
            service_dir=service_dir or self.worker_config["dir"],
            template_dir=template_dir or "systemd",
            extra_context=extra_context
            or {"service_name": f"backendai-{self.worker_config['service_name']}"},
        )

    def _create_systemd_service_file(self, dest_dir: str | None = None) -> None:
        """Create systemd service file.

        Args:
            dest_dir: Optional custom destination directory. If None, installs to /etc/systemd/system/.
        """
        dest = (
            None
            if dest_dir is None
            else f"{dest_dir}/backendai-{self.worker_config['service_name']}.service"
        )

        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_name=self.worker_config["service_name"],
            service_dir=self.worker_config["dir"],
            exec_start=f"{self.home_dir}/bin/{self.worker_config['run_script_name']}",
            user_id=self.user_id,
            group_id=self.group_id,
            dest=dest,
        )

    def _create_diff_script(self) -> None:
        """Create shell script to compare old vs new configurations."""
        files.template(
            name="Create diff comparison script",
            src=str(self.locate_template("scripts/show_diffs_worker.sh.j2")),
            dest=f"{self.upgrade_dir}/show_diffs.sh",
            mode="0755",
            user=self.user,
            upgrade_dir=self.upgrade_dir,
            worker_dir=self.worker_config["dir"],
            home_dir=self.home_dir,
            worker_type=self.worker_type,
            service_name=self.worker_config["service_name"],
            run_script_name=self.worker_config["run_script_name"],
        )

    def _setup_worker(self) -> None:
        # Create python venv (shared across all workers)
        self.remote._create_python_env(self.python_path, self.python_worker_venv_path)
        self._install_worker()

        # Create symbolic link to shared venv
        files.link(
            name=f"Create symbolic link to Python venv on {self.worker_config['dir']}/.venv",
            path=f"{self.worker_config['dir']}/.venv",
            target=self.python_worker_venv_path,
            present=True,
            symbolic=True,
        )

        self._create_worker_toml_file()
        self._create_run_script()
        self._create_systemd_service_file()
        self.start_service()
        self.create_service_manage_scripts()

    def _cleanup_worker(self) -> None:
        self.stop_service()
        self.remove_systemd_service(service_name=self.worker_config["service_name"])
        files.file(
            path=f"{self.home_dir}/bin/{self.worker_config['run_script_name']}", present=False
        )

    def install(self) -> None:
        self.create_directories(dirs=[self.service_dir, self.worker_config["dir"]])
        self._setup_worker()

    def remove(self) -> None:
        self._cleanup_worker()
        self.remove_directories(dirs=[self.worker_config["dir"]])

    def update(self) -> None:
        """Update the worker while preserving existing configurations."""
        logger.info(f"=== AppProxy Worker ({self.worker_type}) Update Mode ===")
        logger.info(f"📦 Updating packages and generating new configs to: {self.upgrade_dir}")
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        # 1. Prepare directories
        self.create_directories(dirs=[self.upgrade_dir])

        # 2. Update packages (shared venv)
        self.remote._create_python_env(self.python_path, self.python_worker_venv_path)
        self._install_worker()

        # Update symbolic link to shared venv
        files.link(
            name=f"Update symbolic link to Python venv on {self.worker_config['dir']}/.venv",
            path=f"{self.worker_config['dir']}/.venv",
            target=self.python_worker_venv_path,
            present=True,
            symbolic=True,
        )

        # 3. Generate new configuration files to upgrade directory
        self._create_worker_toml_file(dest_path=f"{self.upgrade_dir}/app-proxy-worker.toml")
        self._create_run_script(
            dest_path=f"{self.upgrade_dir}/{self.worker_config['run_script_name']}"
        )
        self.create_service_manage_scripts(
            service_dir=self.upgrade_dir,
            extra_context={"service_name": f"backendai-{self.worker_config['service_name']}"},
        )
        self._create_systemd_service_file(dest_dir=self.upgrade_dir)

        # 4. Create diff comparison tool
        self._create_diff_script()
