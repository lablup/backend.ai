from pyinfra import host
from pyinfra.operations import files, server, systemd

from ai.backend.install.pyinfra.runner import BaseDeploy


class ManagerRestartDeploy(BaseDeploy):
    """Deploy systemd timer for daily manager restart across all manager nodes."""

    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user

    def _deploy_timer(self) -> None:
        """Deploy systemd timer for daily manager restart (replaces cron)."""
        # Calculate restart time based on node number (for HA rolling restart)
        # Allows staggered restarts across nodes to maintain service availability
        restart_time = host.data.get("restart_time")
        if not restart_time:
            # InventoryBuilder passes node_number as worker_node_number in host.data
            node_number = host.data.get("worker_node_number", 1)

            base_hour = 5
            minute_offset = (node_number - 1) * 10  # 10 minutes apart per node
            restart_time = f"{base_hour:02d}:{minute_offset:02d}:00"

        # Deploy service unit
        files.template(
            name="Deploy Manager restart service unit",
            src=self.locate_template("systemd/backendai-manager-restart.service.j2"),
            dest="/etc/systemd/system/backendai-manager-restart.service",
            mode="644",
            _sudo=True,
        )
        # Deploy timer unit
        files.template(
            name="Deploy Manager restart timer unit",
            src=self.locate_template("systemd/backendai-manager-restart.timer.j2"),
            dest="/etc/systemd/system/backendai-manager-restart.timer",
            mode="644",
            restart_time=restart_time,
            _sudo=True,
        )
        # Enable and start timer
        systemd.service(
            name="Enable and start Manager restart timer",
            service="backendai-manager-restart.timer",
            enabled=True,
            running=True,
            daemon_reload=True,
            _sudo=True,
        )

    def _remove_timer(self) -> None:
        """Remove systemd timer for manager restart."""
        # Stop and disable timer
        systemd.service(
            name="Stop and disable Manager restart timer",
            service="backendai-manager-restart.timer",
            enabled=False,
            running=False,
            _sudo=True,
        )
        # Remove timer unit
        files.file(
            name="Remove Manager restart timer unit",
            path="/etc/systemd/system/backendai-manager-restart.timer",
            present=False,
            _sudo=True,
        )
        # Remove service unit
        files.file(
            name="Remove Manager restart service unit",
            path="/etc/systemd/system/backendai-manager-restart.service",
            present=False,
            _sudo=True,
        )
        # Reload systemd
        server.shell(
            name="Reload systemd daemon",
            commands=["systemctl daemon-reload"],
            _sudo=True,
        )

    def install(self) -> None:
        self._deploy_timer()

    def remove(self) -> None:
        self._remove_timer()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    ManagerRestartDeploy(host.data).run(deploy_mode)


main()
