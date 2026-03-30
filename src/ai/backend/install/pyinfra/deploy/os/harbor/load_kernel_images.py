"""
Deploy script to load kernel images into Harbor registry.

This script loads Docker images from tar/tar.gz files and pushes them to Harbor registry.
"""

from pathlib import Path
from typing import Any

from pyinfra import host, logger
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDeploy


class LoadKernelImages(BaseDeploy):
    def __init__(self, host_data: Any) -> None:
        self.home_dir: str = host_data.bai_home_dir
        self.user: str = host_data.bai_user

        self.config = host_data.services["harbor"]
        self.registry_hostname: str = host_data.registry_name
        self.registry_port: int = host_data.registry_port
        self.registry_url: str = f"{self.registry_hostname}:{self.registry_port}"
        self.registry_username: str = host_data.registry_username
        self.registry_password: str = host_data.registry_password
        self.registry_project: str = host_data.registry_projects.split(",")[0]  # Use first project

        self.kernel_images_path: str = self.config.kernel_images_path
        self.service_dir: Path = Path(f"{self.home_dir}/images")

    def _log_info(self, message: str, title: str) -> None:
        """Log informational message using PyInfra shell operation."""
        server.shell(name=title, commands=[f"echo '{message}'"])

    def check_kernel_images_path(self) -> bool:
        """Check if kernel images path is configured and exists."""
        if not self.kernel_images_path:
            self._log_info(
                "No kernel_images_path configured, skipping kernel image loading",
                "No kernel_images_path configured",
            )
            return False

        return True

    def create_load_script(self, source: str) -> None:
        """Create a shell script to load and push kernel images.

        Args:
            source: HTTP URL or local directory path for kernel image files
        """
        # Ensure service directory exists
        server.shell(
            name="Create service directory",
            commands=[f"mkdir -p {self.service_dir}"],
        )

        # Locate template using hierarchical search
        template_path = self.locate_template("load_kernel_images.sh.j2")

        # Deploy script from template
        files.template(
            name="Deploy kernel images loader script",
            src=str(template_path),
            dest=f"{self.service_dir}/load_kernel_images.sh",
            mode="755",
            user=self.user,
            registry_url=self.registry_url,
            registry_project=self.registry_project,
            registry_username=self.registry_username,
            registry_password=self.registry_password,
            source=source,
        )

    def install(self) -> None:
        """Main installation method - creates the loading script."""
        if not self.check_kernel_images_path():
            return

        # Create the loading script
        self.create_load_script(self.kernel_images_path)

        # Show instructions to user
        logger.info("")
        logger.info("=" * 73)
        logger.info("Kernel images loader script has been created.")
        logger.info("")
        logger.info("PERFORMANCE OPTIMIZATION (Optional but Recommended):")
        logger.info("  For faster image loading, install optimization tools on target system:")
        logger.info("")
        logger.info("  apt install skopeo pigz -y")
        logger.info("")
        logger.info("  Benefits:")
        logger.info("    - skopeo: 2-3x faster (direct registry copy, no Docker daemon)")
        logger.info("    - pigz: Parallel decompression for .tar.gz files")
        logger.info("")
        logger.info("  Note: Temporary files are cleaned up immediately after each image.")
        logger.info("")
        logger.info("TO LOAD IMAGES:")
        logger.info("")
        logger.info(f"  ssh {self.user}@<harbor-host>")
        logger.info(f"  cd {self.service_dir}")
        logger.info("  ./load_kernel_images.sh")
        logger.info("")
        logger.info("Or run in background with nohup:")
        logger.info("")
        logger.info("  nohup ./load_kernel_images.sh > load_kernel_images.log 2>&1 &")
        logger.info("  tail -f load_kernel_images.log")
        logger.info("")
        logger.info("=" * 73)
        logger.info("")


def main() -> None:
    """Main entry point - directly runs install as this is a one-time operation."""
    LoadKernelImages(host.data).install()


if __name__ == "__main__":
    main()
else:
    # When imported by PyInfra, run main()
    main()
