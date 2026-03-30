from pathlib import Path
from typing import Any

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDeploy


class StandalonePythonDeploy(BaseDeploy):
    """Deploy standalone Python using indygreg's python-build-standalone for consistent environment."""

    FILE_MODE_EXECUTABLE: str = "755"
    TEMP_DOWNLOAD_DIR: Path = Path("/tmp/_bainst/indygreg")
    STATIC_PYTHON_SUBDIR: str = ".static-python/versions"
    AUTOENV_SCRIPT_SUBDIR: str = "scripts"
    AUTOENV_SCRIPT_NAME: str = "autoenv.sh"
    BASHRC_FILENAME: str = ".bashrc"

    def __init__(self, host_data: Any) -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.python_version: str = host.data.python_version
        self.indygreg_python_archive: str = host.data.indygreg_python_archive
        self.indygreg_python_download_url: str = host.data.indygreg_python_download_url

        # Derived paths
        self.remote_indygreg_tmp_folder: Path = self.TEMP_DOWNLOAD_DIR
        self.remote_target_python_path: Path = (
            self.home_dir / self.STATIC_PYTHON_SUBDIR / self.python_version
        )
        self.remote_autoenv_script_path: Path = (
            self.home_dir / self.AUTOENV_SCRIPT_SUBDIR / self.AUTOENV_SCRIPT_NAME
        )
        self.bashrc_path: Path = self.home_dir / self.BASHRC_FILENAME

    def _prepare_directories(self) -> None:
        files.directory(path=str(self.remote_indygreg_tmp_folder), present=True)
        files.directory(path=str(self.remote_target_python_path.parent), present=True)
        files.directory(path=str(self.remote_autoenv_script_path.parent), present=True)

    def download_python_archive(self) -> None:
        """Only downloads if URL is remote (http/https), allowing for local file paths."""
        if self._is_remote_url(self.indygreg_python_download_url):
            files.download(
                name="Download Python archive",
                src=self.indygreg_python_download_url,
                dest=str(self.remote_indygreg_tmp_folder / self.indygreg_python_archive),
                insecure=True,  # Allow local repositories without SSL verification
            )

    def extract_and_move_python(self) -> None:
        """Uses rsync --delete to ensure clean installation, removing previous artifacts."""
        archive_path = self.remote_indygreg_tmp_folder / self.indygreg_python_archive
        extract_dir = self.remote_indygreg_tmp_folder / "python"

        server.shell(
            name="Extract and move Python to the target directory",
            commands=[
                f"tar -xf {archive_path} -C {self.remote_indygreg_tmp_folder}",
                f"rsync -avz --delete {extract_dir}/ {self.remote_target_python_path}/",
            ],
        )

    def place_autoenv_script(self) -> None:
        """Deploys autoenv.sh and adds to .bashrc for automatic Python environment activation."""
        template_path = self.locate_template("autoenv.sh.j2")

        files.template(
            name="Create autoenv script",
            src=str(template_path),
            dest=str(self.remote_autoenv_script_path),
            mode=self.FILE_MODE_EXECUTABLE,
        )

        files.line(
            path=str(self.bashrc_path),
            line=f". {self.remote_autoenv_script_path}",
            present=True,
        )

    def _cleanup_temp_files(self) -> None:
        files.directory(path=str(self.remote_indygreg_tmp_folder), present=False)

    def _is_remote_url(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    def install(self) -> None:
        self._prepare_directories()
        self.download_python_archive()
        self.extract_and_move_python()
        self.place_autoenv_script()
        self._cleanup_temp_files()

    def remove(self) -> None:
        """Note: Does not remove .bashrc entry automatically."""
        files.file(path=str(self.remote_autoenv_script_path), present=False)
        files.directory(
            path=str(self.home_dir / self.STATIC_PYTHON_SUBDIR.split("/")[0]), present=False
        )


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    StandalonePythonDeploy(host.data).run(deploy_mode)


main()
