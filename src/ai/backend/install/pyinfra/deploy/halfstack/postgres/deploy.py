import os

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class PostgresDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user

        self.config = host_data.services["postgres"]

        self.service_dir = f"{self.home_dir}/halfstack/postgres-default"
        self.data_dir = f"{self.home_dir}/.data/backend.ai/postgres-data"

    def fix_data_directory_ownership(self) -> None:
        server.shell(
            name="Fix postgres data directory ownership",
            commands=[
                f"POSTGRES_UID=$(docker run --rm {self.config.container_image} id -u postgres)",
                f"POSTGRES_GID=$(docker run --rm {self.config.container_image} id -g postgres)",
                f"chown $POSTGRES_UID:$POSTGRES_GID {self.data_dir}",
            ],
            _sudo=True,
        )

    def create_backup_restore_scripts(self) -> None:
        for script in ["backup.sh", "restore.sh"]:
            files.template(
                name=f"Create {script} script",
                src=self.locate_template(f"{script}.j2"),
                dest=f"{self.service_dir}/{script}",
                mode="755",
                # jinja2 context
                service_dir=self.service_dir,
                container_name=self.config.container_name,
                db_user=self.config.user,
            )

    def create_sql_example_file(self) -> None:
        files.template(
            name="Create SQL example file",
            src=self.locate_template("examples.md.j2"),
            dest=f"{self.service_dir}/examples.md",
        )

    def create_init_readonly_user_script(self) -> None:
        """Create SQL script for read-only user initialization."""
        # Get service configs for database auto-creation
        appproxy_config = getattr(host.data, "services", {}).get("appproxy", None)
        fasttrack_config = getattr(host.data, "services", {}).get("fasttrack", None)

        # Get readonly user credentials from environment
        postgres_readonly_user = os.getenv("POSTGRES_READONLY_USER", "ronly")
        postgres_readonly_password = os.getenv("POSTGRES_READONLY_PASSWORD", "")

        if not postgres_readonly_password:
            raise ValueError(
                "POSTGRES_READONLY_PASSWORD environment variable is required but not set. "
                "Please set it in your .env file."
            )

        files.template(
            name="Create init_readonly_user.sql script",
            src=self.locate_template("init_readonly_user.sql.j2"),
            dest=f"{self.service_dir}/init_readonly_user.sql",
            # jinja2 context
            appproxy_config=appproxy_config,
            fasttrack_config=fasttrack_config,
            postgres_readonly_user=postgres_readonly_user,
            postgres_readonly_password=postgres_readonly_password,
        )

    def install(self) -> None:
        self.create_directories()
        self.create_env_file(
            db_user=self.config.user,
            db_password=self.config.password,
            db_name=self.config.db_name,
            db_port=self.config.port,
            container_image=self.config.container_image,
            container_name=self.config.container_name,
        )
        self.create_docker_compose_yaml(
            data_dir=str(self.data_dir),
        )
        self.create_init_readonly_user_script()
        self.create_sql_example_file()
        self.create_service_manage_scripts()
        self.create_backup_restore_scripts()
        self.load_image()
        self.fix_data_directory_ownership()
        self.start_service()

    def remove(self) -> None:
        self.stop_service()
        self.remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    PostgresDeploy(host.data).run(deploy_mode)


main()
