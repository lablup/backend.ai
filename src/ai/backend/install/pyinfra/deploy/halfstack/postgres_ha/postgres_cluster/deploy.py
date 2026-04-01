import os
from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PostgresClusterDeploy(BaseDockerComposeDeploy):
    """Deploy PostgreSQL cluster with Patroni for high-availability."""

    SERVICE_NAME: str = "postgres_ha"
    SCRIPT_MODE: str = "755"
    HELPER_SCRIPT_NAME: str = "apply_pids_limit_to_existing_docker.sh"
    POSTGRES_READY_TIMEOUT: int = 300  # 5 minutes for replica bootstrap
    POSTGRES_READY_INTERVAL: int = 2
    PATRONI_READY_TIMEOUT: int = 30
    PATRONI_READY_INTERVAL: int = 2

    def __init__(self, host_data: Any, service_key: str = "postgres_ha") -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.service_key: str = service_key

        self.config = host_data.services[service_key]
        # Use appropriate cluster_info based on service_key
        self.pg_cluster_info: dict[str, Any]
        if service_key == "controlpanel":
            self.pg_cluster_info = getattr(host_data, "cp_pg_cluster_info", {})
        else:
            self.pg_cluster_info = getattr(host_data, "pg_cluster_info", {})

        # Derive paths from config.name (supports multiple instances)
        # Keep backward compatibility: "default" uses original paths without suffix
        instance_name = getattr(self.config, "name", "default")
        self.service_dir: Path
        self.data_dir: Path
        if instance_name == "default":
            self.service_dir = self.home_dir / "halfstack/postgres_cluster-default"
            self.data_dir = self.home_dir / ".data/backend.ai/postgres-data"
        else:
            self.service_dir = self.home_dir / f"halfstack/postgres_cluster-{instance_name}"
            self.data_dir = self.home_dir / f".data/backend.ai/postgres-data-{instance_name}"

    def fix_data_directory_ownership(self) -> None:
        """Dynamically get postgres user UID:GID from container image and fix ownership."""
        server.shell(
            name="Fix postgres data directory ownership",
            commands=[
                # Extract UID:GID in single container run
                f"POSTGRES_UIDGID=$(docker run --rm {self.config.container_image} sh -c 'echo $(id -u postgres):$(id -g postgres)') && "
                f"chown $POSTGRES_UIDGID {self.data_dir}"
            ],
            _sudo=True,
        )

    def _create_node_env_file(self) -> None:
        node_name = self.pg_cluster_info.get("node_name", "unknown")
        files.template(
            name=f"Create {node_name}.env file",
            src=str(self.locate_template("node_env.j2")),
            dest=str(self.service_dir / f"{node_name}.env"),
            # jinja2 context
            pg_cluster_info=self.pg_cluster_info,
        )

    def _create_postgres_config(self) -> None:
        # Get service configs for database auto-creation
        appproxy_config = getattr(host.data, "services", {}).get("appproxy", None)
        fasttrack_config = getattr(host.data, "services", {}).get("fasttrack", None)

        files.template(
            name="Create postgres.yml",
            src=str(self.locate_template("postgres.yaml.j2")),
            dest=str(self.service_dir / "postgres.yml"),
            # jinja2 context
            config=self.config,
            pg_cluster_info=self.pg_cluster_info,
            appproxy_config=appproxy_config,
            fasttrack_config=fasttrack_config,
        )

    def _create_post_init_script(self) -> None:
        """Create post_init.sh script for database initialization."""
        # Control Panel uses dedicated PostgreSQL with only managerhub DB
        is_controlpanel = self.service_key == "controlpanel"

        # Get service configs for database auto-creation (only for core PostgreSQL)
        # Control Panel only creates managerhub database, no other services needed
        appproxy_config = None
        fasttrack_config = None
        postgres_readonly_user = None
        postgres_readonly_password = None

        if not is_controlpanel:
            appproxy_config = getattr(host.data, "services", {}).get("appproxy", None)
            fasttrack_config = getattr(host.data, "services", {}).get("fasttrack", None)

            # Get readonly user credentials from environment (core PostgreSQL only)
            postgres_readonly_user = os.getenv("POSTGRES_READONLY_USER", "ronly")
            postgres_readonly_password = os.getenv("POSTGRES_READONLY_PASSWORD", "")

            if not postgres_readonly_password:
                raise ValueError(
                    "POSTGRES_READONLY_PASSWORD environment variable is required but not set. "
                    "Please set it in your .env file."
                )

        files.template(
            name="Create post_init.sh",
            src=str(self.locate_template("post_init.sh.j2")),
            dest=str(self.service_dir / "post_init.sh"),
            mode=self.SCRIPT_MODE,
            # jinja2 context
            is_controlpanel=is_controlpanel,
            config=self.config,
            appproxy_config=appproxy_config,
            fasttrack_config=fasttrack_config,
            postgres_readonly_user=postgres_readonly_user,
            postgres_readonly_password=postgres_readonly_password,
        )

    def _copy_helper_scripts(self) -> None:
        files.put(
            name="Copy pids limit script",
            src=str(self.locate_file(self.HELPER_SCRIPT_NAME)),
            dest=str(self.service_dir / self.HELPER_SCRIPT_NAME),
            mode=self.SCRIPT_MODE,
        )

    def create_backup_restore_scripts(self) -> None:
        """Create backup.sh and restore.sh scripts for HA cluster."""
        for script in ["backup.sh", "restore.sh"]:
            files.template(
                name=f"Create {script} script",
                src=str(self.locate_template(f"{script}.j2")),
                dest=str(self.service_dir / script),
                mode=self.SCRIPT_MODE,
                # jinja2 context
                config=self.config,
                pg_cluster_info=self.pg_cluster_info,
            )

    def _wait_for_cluster_ready(self) -> None:
        """Wait for PostgreSQL and Patroni cluster to be ready."""
        container_name = (
            f"{self.config.container_name_prefix}-{self.pg_cluster_info.get('node_name')}"
        )

        # Wait for PostgreSQL to be ready
        server.shell(
            name="Wait for PostgreSQL to be ready",
            commands=[
                f"timeout {self.POSTGRES_READY_TIMEOUT} bash -c 'until docker exec {container_name} pg_isready -U postgres; do "
                f'echo "Waiting for PostgreSQL..."; sleep {self.POSTGRES_READY_INTERVAL}; done\''
            ],
        )

        # Wait for Patroni cluster to stabilize
        server.shell(
            name="Wait for Patroni cluster to stabilize",
            commands=[
                f"timeout {self.PATRONI_READY_TIMEOUT} bash -c 'until docker exec {container_name} "
                f'curl -s localhost:8008/cluster | grep -q "running"; do '
                f'echo "Waiting for Patroni..."; sleep {self.PATRONI_READY_INTERVAL}; done\''
            ],
        )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            config=self.config,
            pg_cluster_info=self.pg_cluster_info,
        )
        self._create_node_env_file()
        self._create_postgres_config()
        self._create_post_init_script()
        self.create_docker_compose_yaml(
            config=self.config,
            pg_cluster_info=self.pg_cluster_info,
            data_dir=str(self.data_dir),
        )
        self.create_service_manage_scripts(
            extra_context={
                "config": self.config,
                "pg_cluster_info": self.pg_cluster_info,
                "data_dir": str(self.data_dir),
            }
        )
        self._copy_helper_scripts()
        self.create_backup_restore_scripts()
        self.load_image()
        self.fix_data_directory_ownership()
        self.start_service()
        self._wait_for_cluster_ready()

    def remove(self) -> None:
        server.shell(
            name="Stop PostgreSQL cluster service",
            commands=[
                f"[ -d {self.service_dir} ] && cd {self.service_dir} && {self.docker_compose_cmd} down || true"
            ],
        )

        # Print warning about ETCD state cleanup
        logger.warning("=" * 80)
        logger.warning("ETCD cluster state NOT automatically cleaned!")
        logger.warning("=" * 80)
        logger.warning("")
        logger.warning("For clean reinstallation, choose ONE of:")
        logger.warning("")
        logger.warning("1. Reinstall ETCD cluster (recommended):")
        logger.warning(
            "   pyinfra inventory.py --limit mgr deploy/halfstack/postgres_ha/postgres_etcd/deploy.py --data mode=remove"
        )
        logger.warning(
            "   pyinfra inventory.py --limit mgr deploy/halfstack/postgres_ha/postgres_etcd/deploy.py"
        )
        logger.warning("")
        logger.warning("2. Manual ETCD cleanup (faster):")
        logger.warning(
            "   docker exec bai-postgres-etcd-node1 etcdctl del /service/pg_cluster --prefix"
        )
        logger.warning("=" * 80)

        # Clean up data directory including failed bootstrap attempts
        server.shell(
            name="Clean up PostgreSQL data directory",
            commands=[f"[ -d {self.data_dir} ] && rm -rf {self.data_dir}* || true"],
            _sudo=True,
        )

        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    service_key = host.data.get("service_key", "postgres_ha")
    PostgresClusterDeploy(host.data, service_key=service_key).run(deploy_mode)


main()
