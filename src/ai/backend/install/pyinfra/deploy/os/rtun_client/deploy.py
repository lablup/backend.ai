from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseSystemdDeploy


class RtunDeploy(BaseSystemdDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config = host_data.services["rtun_client"]
        self.service_name = "cloud-assistant"
        self.local_rtun_binary_path = Path(host.data.bai_rtun_binary_path)  # ./_files/rtun
        self.rtun_binary_name = "rtun"

    def _install_rtun(self) -> None:
        protocol = "https"
        rtun_download_url = self.config.rtun_download_url
        files.directory(f"{self.config.rtun_directory}", present=True)

        if rtun_download_url.startswith(protocol):
            files.download(
                name="Download rtun binary",
                src=rtun_download_url,
                dest=str(self.config.rtun_directory + "/" + self.rtun_binary_name),
            )
        else:
            if not self.local_rtun_binary_path.exists():
                raise FileNotFoundError(self.local_rtun_binary_path)
            server.shell(
                name="Move rtun binary to the directory",
                commands=[
                    f"mv {self.local_rtun_binary_path} {self.config.rtun_directory}/{self.rtun_binary_name}"
                ],
            )
        files.file(path=f"{self.config.rtun_directory}/{self.rtun_binary_name}", mode="775")

    def _remove_directories(self) -> None:
        server.shell(
            name="Stop rtun service and backup the cloud-assistant directory",
            commands=[f"mv {self.config.rtun_directory} {self.config.rtun_directory}.bak"],
            _sudo=True,
        )

    def _create_rtun_configuration_file(self) -> None:
        files.template(
            name="Create rtun configuration file",
            src=self.locate_template("rtun.yml.j2"),
            dest=f"{self.config.rtun_directory}/rtun.yml",
            rtun_auth_key=self.config.rtun_auth_key,
            rtun_client_port=self.config.client_port,
            rtun_client_host=self.config.client_host,
            rtun_server_port=self.config.server_port,
        )

    def _activate_cloud_assistant_service(self) -> None:
        server.shell(
            name="Stop and disable cloud assistant service",
            commands=[
                "systemctl daemon-reload backendai-cloud-assistant",
                "systemctl enable --now backendai-cloud-assistant",
            ],
            _sudo=True,
        )
        self.start_service()

    def install(self) -> None:
        self._install_rtun()
        self._create_rtun_configuration_file()
        self.create_systemd_service(
            src=self.locate_template("systemd/service.j2"),
            service_dir=self.config.rtun_directory,
            exec_start=f"{self.config.rtun_directory}/{self.rtun_binary_name}",
            user_id=self.user_id,
            group_id=self.group_id,
        )
        self._activate_cloud_assistant_service()

    def remove(self) -> None:
        self.stop_service()
        self.remove_systemd_service()
        self._remove_directories()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RtunDeploy(host.data).run(deploy_mode)


main()
