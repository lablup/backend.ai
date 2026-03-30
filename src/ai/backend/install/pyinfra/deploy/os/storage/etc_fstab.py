from pathlib import Path

from pyinfra import host
from pyinfra.operations import files

from ai.backend.install.pyinfra.runner import BaseDeploy


class EtcFstabDeploy(BaseDeploy):
    def __init__(self) -> None:
        self.etc_fstab_block_marker = host.data.bai_file_block_marker
        self.fstab_contents_path = Path(host.data.bai_fstab_contents_path)

    def read_fstab_contents(self) -> None:
        if not self.fstab_contents_path.exists():
            raise FileNotFoundError(self.fstab_contents_path)
        return self.fstab_contents_path.read_text().strip()

    def install(self) -> None:
        etc_fstab_content = self.read_fstab_contents()
        files.block(
            name="Add host aliases at /etc/fstab",
            path="/etc/fstab",
            content=etc_fstab_content,
            marker=self.etc_fstab_block_marker,
            _sudo=True,
        )

    def update(self) -> None:
        self.install()

    def remove(self) -> None:
        files.block(
            name="Remove mount information from /etc/fstab",
            path="/etc/fstab",
            marker=self.etc_fstab_block_marker,
            present=False,
            _sudo=True,
        )


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcFstabDeploy().run(deploy_mode)


main()
