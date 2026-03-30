from pathlib import Path

from pyinfra import host
from pyinfra.operations import files

from ai.backend.install.pyinfra.runner import BaseDeploy


class EtcHostsAliasDeploy(BaseDeploy):
    def __init__(self) -> None:
        self.etc_hosts_block_marker = host.data.bai_file_block_marker
        self.hosts_contents_path = Path(host.data.bai_hosts_contents_path)

    def read_hosts_contents(self) -> None:
        if not self.hosts_contents_path.exists():
            raise FileNotFoundError(self.hosts_contents_path)
        return self.hosts_contents_path.read_text().strip()

    def install(self) -> None:
        etc_hosts_content = self.read_hosts_contents()
        files.block(
            name="Add host aliases at /etc/hosts",
            path="/etc/hosts",
            content=etc_hosts_content,
            marker=self.etc_hosts_block_marker,
            _sudo=True,
        )

    def update(self) -> None:
        self.install()

    def remove(self) -> None:
        files.block(
            name="Remove host aliases from /etc/hosts",
            path="/etc/hosts",
            marker=self.etc_hosts_block_marker,
            present=False,
            _sudo=True,
        )


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcHostsAliasDeploy().run(deploy_mode)


main()
