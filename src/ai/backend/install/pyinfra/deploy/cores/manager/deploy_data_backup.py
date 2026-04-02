from pyinfra import host
from pyinfra.operations import files, server, systemd

from ai.backend.install.pyinfra.runner import BaseDeploy


class DataBackupDeploy(BaseDeploy):
    """Deploy data backup script and systemd timer for primary manager node."""

    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config_db = host_data.services["postgres"]

    def _deploy_backup_service(self) -> None:
        """Deploy backup script and systemd timer for daily data backup."""
        # Backup directory (configurable via host.data, default to ~/bai_backup)
        backup_dir = host.data.get("backup_dir", f"{self.home_dir}/bai_backup")

        # Ensure backup directory exists
        files.directory(
            name="Create backup directory",
            path=backup_dir,
            present=True,
            user=self.user,
            mode="755",
            _sudo=True,
        )

        # Ensure scripts directory exists
        self.create_directories(dirs=[f"{self.home_dir}/scripts"])

        # Deploy backup script
        files.template(
            name="Deploy data backup script",
            src=self.locate_template("scripts/backup_bai_data.sh.j2"),
            dest=f"{self.home_dir}/scripts/backup_bai_data.sh",
            mode="755",
            user=self.user,
            # Jinja2 context
            home_dir=self.home_dir,
            backup_dir=backup_dir,
            db_host=self.config_db.hostname,
            db_port=self.config_db.port,
            db_user=self.config_db.user,
            db_password=self.config_db.password,
        )

        # Deploy service unit
        files.template(
            name="Deploy Manager data backup service unit",
            src=self.locate_template("systemd/backendai-manager-data-backup.service.j2"),
            dest="/etc/systemd/system/backendai-manager-data-backup.service",
            mode="644",
            user=self.user,  # Set file owner to bai user
            home_dir=self.home_dir,  # Template variable
            bai_user=self.user,  # Template variable
            _sudo=True,
        )

        # Deploy timer unit
        files.template(
            name="Deploy Manager data backup timer unit",
            src=self.locate_template("systemd/backendai-manager-data-backup.timer.j2"),
            dest="/etc/systemd/system/backendai-manager-data-backup.timer",
            mode="644",
            _sudo=True,
        )

        # Enable and start timer
        systemd.service(
            name="Enable and start Manager data backup timer",
            service="backendai-manager-data-backup.timer",
            enabled=True,
            running=True,
            daemon_reload=True,
            _sudo=True,
        )

    def _remove_backup_service(self) -> None:
        """Remove backup script and systemd timer."""
        # Stop and disable timer
        systemd.service(
            name="Stop and disable Manager data backup timer",
            service="backendai-manager-data-backup.timer",
            enabled=False,
            running=False,
            _sudo=True,
        )
        # Remove timer unit
        files.file(
            name="Remove Manager data backup timer unit",
            path="/etc/systemd/system/backendai-manager-data-backup.timer",
            present=False,
            _sudo=True,
        )
        # Remove service unit
        files.file(
            name="Remove Manager data backup service unit",
            path="/etc/systemd/system/backendai-manager-data-backup.service",
            present=False,
            _sudo=True,
        )
        # Remove backup script
        files.file(
            name="Remove data backup script",
            path=f"{self.home_dir}/scripts/backup_bai_data.sh",
            present=False,
        )
        # Reload systemd
        server.shell(
            name="Reload systemd daemon",
            commands=["systemctl daemon-reload"],
            _sudo=True,
        )

    def install(self) -> None:
        self._deploy_backup_service()

    def remove(self) -> None:
        self._remove_backup_service()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    DataBackupDeploy(host.data).run(deploy_mode)


main()
