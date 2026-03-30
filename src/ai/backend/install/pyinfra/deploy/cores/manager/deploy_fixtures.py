from pathlib import Path

from pyinfra import host, logger
from pyinfra.operations import server

from ai.backend.install.pyinfra.exceptions import DeploymentError
from ai.backend.install.pyinfra.runner import BaseDeploy
from ai.backend.install.pyinfra.utils import get_major_version


class ManagerFixturesDeploy(BaseDeploy):
    # Class constants
    SERVICE_NAME = "manager"
    FIXTURES_DIR = "fixtures"
    STATIC_PYTHON_DIR = ".static-python"

    # Fixture files to populate into the database
    # Note: etcd-config.json and etcd-volumes.json are handled separately via ETCD commands
    DB_FIXTURE_FILES = [
        "container-registries-harbor.json",
        "users.json",
        "user-main-access-keys.json",
        "resource-presets.json",
    ]

    # ETCD configuration files
    ETCD_CONFIG_FILES = [
        ("config", "etcd-config.json"),
        ("volumes", "etcd-volumes.json"),
    ]

    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = self.SERVICE_NAME
        self.service_dir = Path(f"{self.home_dir}/{self.service_name}")

        # Python environment paths (same as manager deploy)
        self.config_bai_core = host_data.services["bai_core"]
        self.bai_major_version = get_major_version(self.config_bai_core.version)
        self.python_version = host.data.python_version
        self.python_venv_path = f"{self.home_dir}/{self.STATIC_PYTHON_DIR}/venvs/bai-{self.bai_major_version}-{self.service_name}"
        self.backend_ai_cmd = f"{self.python_venv_path}/bin/backend.ai"

    def _generate_rpc_keypair(self) -> None:
        """Generate RPC keypair for manager service."""
        try:
            logger.info("Generating RPC keypair for manager...")

            server.shell(
                name="Generate RPC keypair",
                commands=[
                    f"{self.backend_ai_cmd} mgr generate-rpc-keypair {self.FIXTURES_DIR} {self.service_name}"
                ],
                _chdir=str(self.service_dir),
                _sudo=False,
            )

        except Exception as e:
            error_msg = f"Failed to generate RPC keypair: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _initialize_database_schema(self) -> None:
        """Initialize database schema."""
        try:
            logger.info("Initializing database schema...")

            server.shell(
                name="Initialize database schema",
                commands=[f"{self.backend_ai_cmd} mgr schema oneshot"],
                _chdir=str(self.service_dir),
                _sudo=False,
            )

        except Exception as e:
            error_msg = f"Failed to initialize database schema: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _populate_fixtures(self) -> None:
        """Populate database fixtures.

        Note: ETCD configuration fixtures are handled separately in _configure_etcd().
        """
        try:
            logger.info("Populating database fixtures...")

            populate_commands = [
                f"{self.backend_ai_cmd} mgr fixture populate {self.FIXTURES_DIR}/{fixture}"
                for fixture in self.DB_FIXTURE_FILES
            ]

            server.shell(
                name="Populate database fixtures",
                commands=populate_commands,
                _chdir=str(self.service_dir),
                _sudo=False,
            )

        except Exception as e:
            error_msg = f"Failed to populate database fixtures: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def _configure_etcd(self) -> None:
        """Configure ETCD with fixtures."""
        try:
            logger.info("Configuring ETCD...")

            etcd_commands = [
                f"{self.backend_ai_cmd} mgr etcd put-json {key} {self.FIXTURES_DIR}/{filename}"
                for key, filename in self.ETCD_CONFIG_FILES
            ]

            server.shell(
                name="Configure ETCD",
                commands=etcd_commands,
                _chdir=str(self.service_dir),
                _sudo=False,
            )

        except Exception as e:
            error_msg = f"Failed to configure ETCD: {e}"
            logger.error(error_msg)
            raise DeploymentError(error_msg) from e

    def install(self) -> None:
        """Install fixtures and initialize Backend.AI manager.

        Note: This should only be run once in HA setups to avoid data duplication.
        """
        self._generate_rpc_keypair()
        self._initialize_database_schema()
        self._populate_fixtures()
        self._configure_etcd()
        logger.info("Manager fixtures installation completed successfully!")
        logger.warning(
            "ACTION REQUIRED: Restart the Manager service on all manager nodes "
            "to apply the new DB schema and ETCD configuration. "
            "Run: sudo systemctl restart backendai-manager.service"
        )

    def remove(self) -> None:
        """Remove fixtures - not implemented for safety."""
        logger.warning("Fixture removal is not implemented for safety reasons")
        logger.warning("Please manually clean up the database and ETCD if needed")


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    if deploy_mode == "remove":
        logger.warning("Fixture removal is not supported for safety reasons")
        return

    ManagerFixturesDeploy(host.data).run(deploy_mode)


main()
