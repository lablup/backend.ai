from pathlib import Path
from typing import Any

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDeploy


class OfflineToolsDeploy(BaseDeploy):
    """Deploy binary tools from offline repository for system administration."""

    FILE_MODE_EXECUTABLE: str = "755"
    TOOLS_SUBDIR: str = "tools"
    TOOLS_ENV_SCRIPT_SUBDIR: str = "scripts"
    TOOLS_ENV_SCRIPT_NAME: str = "tools_env.sh"
    BASHRC_FILENAME: str = ".bashrc"

    def __init__(self, host_data: Any) -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.user: str = host_data.bai_user
        self.offline_repo_url: str = host_data.bai_offline_repo_url

        # Derived paths
        self.tools_dir: Path = self.home_dir / self.TOOLS_SUBDIR
        self.tools_env_script_path: Path = (
            self.home_dir / self.TOOLS_ENV_SCRIPT_SUBDIR / self.TOOLS_ENV_SCRIPT_NAME
        )
        self.bashrc_path: Path = self.home_dir / self.BASHRC_FILENAME

    def _prepare_directories(self) -> None:
        files.directory(path=str(self.tools_dir), present=True)
        files.directory(path=str(self.tools_env_script_path.parent), present=True)

    def _check_offline_repo_available(self) -> bool:
        """Check if offline repository tools directory is accessible."""
        tools_url = f"{self.offline_repo_url}/tools/"
        check_result = server.shell(
            name="Check offline repository tools directory",
            commands=[
                f"curl -sf -o /dev/null -I {tools_url} && echo 'available' || echo 'unavailable'"
            ],
        )
        return bool(check_result.stdout and "available" in check_result.stdout)

    def download_tools(self) -> None:
        """Download tools from offline repository using wget with mirror mode."""
        tools_url = f"{self.offline_repo_url}/tools/"

        print(f"Downloading tools from {tools_url}...")

        server.shell(
            name="Download tools from offline repository",
            commands=[
                f"wget -r -np -nH --cut-dirs=0 --reject='index.html*' "
                f"--timeout=30 --tries=3 -P {self.home_dir} {tools_url}"
            ],
        )

        # Set executable permissions for all files in tools directory
        server.shell(
            name="Set executable permissions for tools",
            commands=[f"chmod -R {self.FILE_MODE_EXECUTABLE} {self.tools_dir}"],
        )

    def place_tools_env_script(self) -> None:
        """Deploy tools_env.sh and add to .bashrc for automatic PATH configuration."""
        template_path = self.locate_template("tools_env.sh.j2")

        files.template(
            name="Create tools environment script",
            src=str(template_path),
            dest=str(self.tools_env_script_path),
            mode=self.FILE_MODE_EXECUTABLE,
            tools_dir=str(self.tools_dir),
        )

        files.line(
            path=str(self.bashrc_path),
            line=f". {self.tools_env_script_path}",
            present=True,
        )

    def install(self) -> None:
        if not self.offline_repo_url:
            print("WARNING: Offline repository URL not configured. Skipping tools installation.")
            return

        print(f"Installing offline tools from {self.offline_repo_url}/tools...")

        self._prepare_directories()
        self.download_tools()
        self.place_tools_env_script()

        print(f"Tools installed successfully at {self.tools_dir}")
        print("Tools will be available in PATH after re-login or sourcing ~/.bashrc")

    def remove(self) -> None:
        """Remove tools directory and environment script configuration."""
        files.file(path=str(self.tools_env_script_path), present=False)
        files.directory(path=str(self.tools_dir), present=False)

        files.line(
            path=str(self.bashrc_path),
            line=f". {self.tools_env_script_path}",
            present=False,
        )

        print(f"Tools removed from {self.tools_dir}")

    def update(self) -> None:
        """Update tools by re-running installation."""
        self.install()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    OfflineToolsDeploy(host.data).run(deploy_mode)


main()
