from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import files, server, systemd

from ai.backend.install.pyinfra.deploy.cores.appproxy.constants import (
    SERVICE_DIR,
    TRAEFIK_DIR,
    WORKER_TYPES,
    create_worker_config,
)
from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import ensure_file_exists


class AppProxyTraefikDeploy(BaseSystemdDeploy):
    """
    Traefik deployment manages multiple systemd services (one per worker type).

    Note: This class inherits from BaseSystemdDeploy to reuse systemd service
    management methods, but manages multiple independent systemd services.
    """

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config = host_data.services["appproxy"]
        self.config_etcd = host_data.services.get("etcd", None)

        self.service_dir = Path(SERVICE_DIR.format(home_dir=self.home_dir))
        self.traefik_dir = Path(TRAEFIK_DIR.format(service_dir=self.service_dir))
        self.upgrade_dir = f"{self.traefik_dir}/upgrades"
        self.worker_types = WORKER_TYPES
        self.worker_configs = {}

        # Create worker configs for all types
        for worker_type in self.worker_types:
            self.worker_configs[worker_type] = create_worker_config(
                self.service_dir, self.config, worker_type
            )

    def _prepare_traefik_packages(self, dest_dir: str | None = None) -> None:
        """Download and extract Traefik binary and plugins.

        Args:
            dest_dir: Optional custom destination directory. If None, uses traefik_dir
        """
        target_dir = dest_dir or str(self.traefik_dir)

        # Traefik binary
        file_path = ensure_file_exists(
            self.config.traefik_archive_url, f"{target_dir}/traefik.tar.gz"
        )
        server.shell(
            name="Extract traefik binary",
            commands=[f"tar -xzf {file_path} -C {target_dir}"],
        )
        files.file(
            name="Remove traefik archive",
            path=f"{target_dir}/traefik.tar.gz",
            present=False,
        )

        # Traefik plugins
        file_path = ensure_file_exists(
            self.config.traefik_plugin_url, f"{target_dir}/traefik-plugin.tar.gz"
        )
        server.shell(
            name="Extract traefik plugin",
            commands=[f"tar -xzf {file_path} -C {target_dir}"],
        )
        files.file(
            name="Remove traefik plugin archive",
            path=f"{target_dir}/traefik-plugin.tar.gz",
            present=False,
        )

        # TLS provider file
        files.template(
            name="Create TLS config",
            src=str(self.locate_template("tls.yml.j2")),
            dest=f"{target_dir}/tls.yml",
            ssl_cert_path=None,  # does not auto support ssl for now
            ssl_key_path=None,
        )

        # Helper script
        files.template(
            name="Create traefik helper script",
            src=str(self.locate_template("generate_traefik_entrypoints.py.j2")),
            dest=f"{target_dir}/generate_traefik_entrypoints.py",
            bai_home_dir=self.home_dir,
        )

    def _setup_traefik(
        self, worker_type: str, dest_dir: str | None = None, start_service: bool = True
    ) -> None:
        """Setup traefik for a specific worker type.

        Args:
            worker_type: Type of worker (inference, interactive, tcp)
            dest_dir: Optional custom destination directory. If None, uses traefik_dir
            start_service: Whether to start the systemd service after setup
        """
        worker_config = self.worker_configs[worker_type]
        config_dir = dest_dir or str(self.traefik_dir)
        bin_dir = f"{dest_dir}/bin" if dest_dir else f"{self.home_dir}/bin"

        # Create traefik config YAML
        files.template(
            name=f"Create traefik config for {worker_type}",
            src=str(self.locate_template("traefik-config.yml.j2")),
            dest=f"{config_dir}/config-{worker_type}.yml",
            mode="644",
            port_start=worker_config["app_port_start"],
            port_end=worker_config["app_port_end"],
            api_port=worker_config["traefik_api_port"],
            authority=worker_config["authority"],
            etcd_host=self.config_etcd.connect_client_ip,
            etcd_port=self.config_etcd.advertised_client_port,
            traefik_dir=self.traefik_dir,
            home_dir=self.home_dir,
        )

        # Create run script
        files.template(
            name=f"Create traefik run script for {worker_type}",
            src=str(self.locate_template("run-traefik.sh.j2")),
            dest=f"{bin_dir}/run-traefik-{worker_type}.sh",
            mode="755",
            home_dir=self.home_dir,
            worker_type=worker_type,
        )

        # Create service management scripts
        for script_name, template_name in [
            (f"start_{worker_type}.sh", "start.sh.j2"),
            (f"stop_{worker_type}.sh", "stop.sh.j2"),
            (f"show_logs_{worker_type}.sh", "show_logs.sh.j2"),
            (f"show_status_{worker_type}.sh", "show_status.sh.j2"),
        ]:
            files.template(
                name=f"Create traefik {script_name} for {worker_type}",
                src=str(self.locate_template(f"systemd/{template_name}")),
                dest=f"{config_dir}/{script_name}",
                mode="755",
                service_name=f"backendai-appproxy-traefik-{worker_type}",
            )

        # Create systemd service
        systemd_dest = (
            None
            if dest_dir is None
            else f"{dest_dir}/backendai-appproxy-traefik-{worker_type}.service"
        )
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_name=f"appproxy-traefik-{worker_type}",
            service_dir=self.traefik_dir if dest_dir is None else Path(dest_dir),
            exec_start=f"{self.home_dir}/bin/run-traefik-{worker_type}.sh",
            user_id=self.user_id,
            group_id=self.group_id,
            dest=systemd_dest,
        )

        # Start service only if requested
        if start_service:
            systemd.service(
                service=f"backendai-appproxy-traefik-{worker_type}.service",
                running=True,
                _sudo=True,
            )

    def _cleanup_traefik(self, worker_type: str) -> None:
        systemd.service(
            service=f"backendai-appproxy-traefik-{worker_type}.service",
            running=False,
            _sudo=True,
        )
        self.remove_systemd_service(service_name=f"appproxy-traefik-{worker_type}")
        files.file(path=f"{self.home_dir}/bin/run-traefik-{worker_type}.sh", present=False)

    def install(self) -> None:
        # Create all necessary directories
        dirs = [self.service_dir, self.traefik_dir]
        dirs.extend([f"{self.traefik_dir}/{worker_type}" for worker_type in self.worker_types])
        self.create_directories(dirs=dirs)

        self._prepare_traefik_packages()

        for worker_type in self.worker_types:
            self._setup_traefik(worker_type)

    def install_for_worker(self, worker_type: str) -> None:
        """Install Traefik for a specific worker type only"""
        if worker_type not in self.worker_types:
            raise ValueError(
                f"Invalid worker type: {worker_type}. Must be one of: {self.worker_types}"
            )

        # Create all necessary directories
        dirs = [self.service_dir, self.traefik_dir]
        dirs.extend([f"{self.traefik_dir}/{worker_type}" for worker_type in self.worker_types])
        self.create_directories(dirs=dirs)

        self._prepare_traefik_packages()
        self._setup_traefik(worker_type)

    def remove(self) -> None:
        for worker_type in self.worker_types:
            self._cleanup_traefik(worker_type)

        self.remove_directories(dirs=[self.traefik_dir])

    def remove_for_worker(self, worker_type: str) -> None:
        """Remove Traefik for a specific worker type only"""
        if worker_type not in self.worker_types:
            raise ValueError(
                f"Invalid worker type: {worker_type}. Must be one of: {self.worker_types}"
            )

        self._cleanup_traefik(worker_type)

    def _create_diff_script(self) -> None:
        """Create shell script to compare old vs new configurations for all worker types."""
        files.template(
            name="Create diff comparison script for traefik",
            src=str(self.locate_template("scripts/show_diffs_traefik.sh.j2")),
            dest=f"{self.upgrade_dir}/show_diffs.sh",
            mode="0755",
            user=self.user,
            upgrade_dir=self.upgrade_dir,
            traefik_dir=self.traefik_dir,
            home_dir=self.home_dir,
            worker_types=self.worker_types,
        )

    def update(self) -> None:
        """Update Traefik binaries, plugins, and generate new configs while preserving existing configurations."""
        logger.info("=== Traefik Update Mode ===")
        logger.info(
            f"📦 Updating Traefik binaries, plugins, and generating new configs to: {self.upgrade_dir}"
        )
        logger.info(f"📝 After completion, review changes with: {self.upgrade_dir}/show_diffs.sh\n")

        # 1. Prepare directories
        self.create_directories(dirs=[self.upgrade_dir, f"{self.upgrade_dir}/bin"])

        # 2. Download and extract Traefik binary and plugins to upgrade directory
        self._prepare_traefik_packages(dest_dir=self.upgrade_dir)

        # 3. Generate new configuration files to upgrade directory for all worker types
        for worker_type in self.worker_types:
            logger.info(f"Generating new configs for worker type: {worker_type}")
            self._setup_traefik(worker_type, dest_dir=self.upgrade_dir, start_service=False)

        # 4. Create diff comparison tool
        self._create_diff_script()

        logger.info("\n✅ Update preparation completed!")
        logger.info("Next steps:")
        logger.info(f"  1. Review diffs: {self.upgrade_dir}/show_diffs.sh")
        logger.info(f"  2. Check new binaries: {self.upgrade_dir}/traefik")
        logger.info(f"  3. Check new plugins: {self.upgrade_dir}/plugins/")
        logger.info("  4. Manually merge changes if needed")
        logger.info(
            f"  5. Copy new binaries/plugins to production: cp -r {self.upgrade_dir}/traefik {self.upgrade_dir}/plugins {self.traefik_dir}/"
        )
        logger.info("  6. Restart services: systemctl restart backendai-appproxy-traefik-*")


# Execute deployment when script is loaded
def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = AppProxyTraefikDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    elif deploy_mode == "update":
        deploy.update()
    else:
        deploy.install()


main()
