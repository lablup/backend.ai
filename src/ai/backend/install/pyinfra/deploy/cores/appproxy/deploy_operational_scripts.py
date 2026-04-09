from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, pip, server, systemd

from ai.backend.install.pyinfra.runner import BaseDeploy


class AppProxyOperationalScriptsDeploy(BaseDeploy):
    """Deploy app proxy operational scripts and systemd timers for manager nodes."""

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.scripts_dir = Path(self.home_dir) / "scripts"

        # Construct Python path from python_version (same pattern as manager/agent deployments)
        self.python_version = host.data.python_version
        self.python_path = (
            f"{self.home_dir}/.static-python/versions/{self.python_version}/bin/python3"
        )
        self.scripts_venv_path = self.scripts_dir / ".venv"

        # Get configuration objects
        self.config_appproxy = host_data.services.get("appproxy")
        self.config_postgres = host_data.services.get("postgres")
        self.config_etcd = host_data.services.get("etcd")
        self.config_etcd_ha = host_data.services.get("etcd_ha")

        # Validate required configs
        if not self.config_appproxy:
            raise ValueError("AppProxy configuration is required")
        if not self.config_postgres:
            raise ValueError("PostgreSQL configuration is required")
        if not self.config_etcd and not self.config_etcd_ha:
            raise ValueError("ETCD configuration is required (either etcd or etcd_ha)")

        # Prepare common context
        self.coordinator_endpoint = (
            f"{self.config_appproxy.coordinator_scheme}://"
            f"{self.config_appproxy.coordinator_hostname}:{self.config_appproxy.coordinator_port}"
        )

        # Define operational scripts metadata
        # To add/remove scripts, just modify this list
        self.scripts_metadata = [
            {
                "name": "cleanup_traefik_routers.sh",
                "template": "scripts/cleanup_traefik_routers.sh.j2",
                "systemd_name": "backendai-appproxy-cleanup-traefik",
                "context_builder": self._get_cleanup_traefik_context,
            },
            {
                "name": "delete_unused_circuits.py",
                "template": "scripts/delete_unused_circuits.py.j2",
                "systemd_name": "backendai-appproxy-delete-circuits",
                "context_builder": self._get_delete_circuits_context,
            },
            {
                "name": "sync_inference_circuits.sh",
                "template": "scripts/sync_inference_circuits.sh.j2",
                "systemd_name": "backendai-appproxy-sync-circuits",
                "context_builder": self._get_sync_circuits_context,
            },
        ]

    def _get_etcd_container_name(self) -> str:
        """Get ETCD container name based on deployment mode (single-node vs HA)."""
        if self.config_etcd_ha:
            # HA mode: use gRPC proxy container (client-side, no node number)
            return self.config_etcd_ha.grpc_container_name_prefix
        # Single-node mode
        return self.config_etcd.container_name

    def _get_cleanup_traefik_context(self) -> dict:
        """Get template context for cleanup_traefik_routers.sh"""
        return {
            "api_token": self.config_appproxy.shared_key,
            "coordinator_endpoint": self.coordinator_endpoint,
            "etcd_container_name": self._get_etcd_container_name(),
        }

    def _get_delete_circuits_context(self) -> dict:
        """Get template context for delete_unused_circuits.py"""
        return {
            "backend_db_host": self.config_postgres.hostname,
            "backend_db_port": self.config_postgres.port,
            "backend_db_name": "backend",
            "backend_db_user": self.config_postgres.user,
            "backend_db_password": self.config_postgres.password,
            "wsproxy_db_host": self.config_postgres.hostname,
            "wsproxy_db_port": self.config_postgres.port,
            "wsproxy_db_name": self.config_appproxy.db_name,
            "wsproxy_db_user": self.config_appproxy.db_user,
            "wsproxy_db_password": self.config_appproxy.db_password,
            "api_url": self.coordinator_endpoint,
            "api_token": self.config_appproxy.shared_key,
        }

    def _get_sync_circuits_context(self) -> dict:
        """Get template context for sync_inference_circuits.sh"""
        return {
            "wsproxy_db_host": self.config_postgres.hostname,
            "wsproxy_db_port": self.config_postgres.port,
            "wsproxy_db_name": self.config_appproxy.db_name,
            "wsproxy_db_user": self.config_appproxy.db_user,
            "wsproxy_db_password": self.config_appproxy.db_password,
            "client_dir": f"{self.home_dir}/client",
        }

    def _deploy_scripts(self) -> None:
        """Deploy operational scripts with configuration from templates."""
        # Ensure scripts directory exists
        self.create_directories(dirs=[self.scripts_dir])

        # Deploy each script
        for script_meta in self.scripts_metadata:
            context = script_meta["context_builder"]()
            files.template(
                name=f"Deploy {script_meta['name']} script",
                src=self.locate_template(script_meta["template"]),
                dest=f"{self.scripts_dir}/{script_meta['name']}",
                mode="755",
                user=self.user,
                **context,
            )

    def _setup_python_venv(self) -> None:
        """Create Python venv and install dependencies for Python scripts."""
        # Create Python venv
        pip.venv(
            name=f"Create Python venv: {self.scripts_venv_path}",
            path=str(self.scripts_venv_path),
            python=str(self.python_path),
            present=True,
        )

        # Install required packages
        pip.packages(
            name="Install Python dependencies for operational scripts",
            packages=["psycopg2-binary", "requests"],
            pip=f"{self.scripts_venv_path}/bin/pip",
            present=True,
        )

    def _deploy_systemd_timers(self) -> None:
        """Deploy systemd service and timer units for each operational script."""
        for script_meta in self.scripts_metadata:
            systemd_name = script_meta["systemd_name"]

            # Deploy service unit
            files.template(
                name=f"Deploy {systemd_name} service unit",
                src=self.locate_template(f"systemd/{systemd_name}.service.j2"),
                dest=f"/etc/systemd/system/{systemd_name}.service",
                mode="644",
                home_dir=self.home_dir,
                bai_user=self.user,
                _sudo=True,
            )

            # Deploy timer unit
            files.template(
                name=f"Deploy {systemd_name} timer unit",
                src=self.locate_template(f"systemd/{systemd_name}.timer.j2"),
                dest=f"/etc/systemd/system/{systemd_name}.timer",
                mode="644",
                _sudo=True,
            )

            # Enable and start timer
            systemd.service(
                name=f"Enable and start {systemd_name} timer",
                service=f"{systemd_name}.timer",
                enabled=True,
                running=True,
                daemon_reload=True,
                _sudo=True,
            )

    def _remove_systemd_timers(self) -> None:
        """Remove systemd service and timer units."""
        for script_meta in self.scripts_metadata:
            systemd_name = script_meta["systemd_name"]

            # Stop and disable timer
            systemd.service(
                name=f"Stop and disable {systemd_name} timer",
                service=f"{systemd_name}.timer",
                enabled=False,
                running=False,
                _sudo=True,
            )

            # Remove timer unit
            files.file(
                name=f"Remove {systemd_name} timer unit",
                path=f"/etc/systemd/system/{systemd_name}.timer",
                present=False,
                _sudo=True,
            )

            # Remove service unit
            files.file(
                name=f"Remove {systemd_name} service unit",
                path=f"/etc/systemd/system/{systemd_name}.service",
                present=False,
                _sudo=True,
            )

        # Reload systemd
        server.shell(
            name="Reload systemd daemon",
            commands=["systemctl daemon-reload"],
            _sudo=True,
        )

    def _remove_scripts(self) -> None:
        """Remove deployed scripts."""
        for script_meta in self.scripts_metadata:
            files.file(
                name=f"Remove {script_meta['name']}",
                path=f"{self.scripts_dir}/{script_meta['name']}",
                present=False,
            )

    def _remove_python_venv(self) -> None:
        """Remove Python venv."""
        pip.venv(
            name="Remove Python virtual environment",
            path=str(self.scripts_venv_path),
            present=False,
        )

    def install(self) -> None:
        """Install operational scripts and optionally systemd timers."""
        self._deploy_scripts()
        self._setup_python_venv()

        # Enable timers if requested
        enable_timers = host.data.get("enable_timers", False)
        if enable_timers:
            self._deploy_systemd_timers()

    def remove(self) -> None:
        """Remove operational scripts and systemd timers."""
        self._remove_systemd_timers()
        self._remove_scripts()
        self._remove_python_venv()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    AppProxyOperationalScriptsDeploy(host.data).run(deploy_mode)


main()
