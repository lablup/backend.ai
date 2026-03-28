"""RPM-based Package Manager Implementations

This module provides YUM and DNF package managers for RHEL/CentOS/Fedora systems.
"""

import logging
from typing import Any

from .package_manager import PackageManager

logger = logging.getLogger(__name__)


class YUMManager(PackageManager):
    """Manages YUM repository configuration for RHEL/CentOS systems."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "YUM"

    def backup_sources(self) -> None:
        """Backup original YUM repository configuration."""
        raise NotImplementedError("YUM support not yet implemented")

    def restore_sources(self) -> None:
        """Restore original YUM repository configuration."""
        raise NotImplementedError("YUM support not yet implemented")

    def setup_offline_only_repositories(self, repo_filename: str = "local-repo-only") -> None:
        """Setup YUM to use only the specified offline repository."""
        raise NotImplementedError("YUM support not yet implemented")

    def add_local_repository(self, repo_filename: str = "local-repo") -> None:
        """Add local repository alongside existing ones."""
        raise NotImplementedError("YUM support not yet implemented")

    def update_package_lists(self) -> None:
        """Update YUM package lists."""
        raise NotImplementedError("YUM support not yet implemented")

    def install_packages(self, packages: list[str], update: bool = False) -> None:
        """Install packages using YUM."""
        raise NotImplementedError("YUM support not yet implemented")

    def _cleanup_platform_specific_files(self) -> None:
        """Clean up YUM-specific backup and temporary files."""
        raise NotImplementedError("YUM support not yet implemented")

    def _emergency_restore_implementation(self) -> None:
        """Emergency YUM repository restore implementation."""
        raise NotImplementedError("YUM support not yet implemented")

    def setup_docker_repository(
        self,
        docker_installation_uri: str,
        docker_installation_os: str,
        docker_installation_distro: str,
        template_locator: Any = None,
    ) -> None:
        """Setup Docker repository for RHEL/CentOS systems using YUM.

        Args:
            docker_installation_uri: Base URI for Docker installation
            docker_installation_os: OS identifier (e.g., 'centos')
            docker_installation_distro: Distribution identifier (e.g., '7')
            template_locator: Function to locate template files (optional)
        """
        from pyinfra.operations import files, yum

        # Install prerequisites
        yum.packages(
            name="Ensure YUM deps. installed for Docker installation",
            packages=["ca-certificates", "curl"],
            latest=True,
            _sudo=True,
        )

        # Determine template source
        if template_locator:
            template_src = template_locator("docker-yum-repo.j2")
        else:
            template_src = "docker-yum-repo.j2"

        # Add Docker repository
        files.template(
            name="Create Docker YUM repository file",
            src=template_src,
            dest="/etc/yum.repos.d/docker-ce.repo",
            _sudo=True,
            docker_installation_uri=docker_installation_uri,
            docker_installation_os=docker_installation_os,
            docker_installation_distro=docker_installation_distro,
        )

        logger.info(f"Docker YUM repository configured: {docker_installation_uri}")

    def remove_docker_packages_and_repository(self, packages: list[str]) -> None:
        """Remove Docker packages and clean up repository configuration.

        Args:
            packages: List of Docker packages to remove
        """
        from pyinfra.operations import files, yum

        # Remove conflicting packages first
        conflicting_packages = [
            "docker",
            "docker-client",
            "docker-client-latest",
            "docker-common",
            "docker-latest",
            "docker-latest-logrotate",
            "docker-logrotate",
            "docker-engine",
            "podman",
            "runc",
        ]

        yum.packages(
            name="Remove conflicting Docker packages",
            packages=conflicting_packages,
            present=False,
            _sudo=True,
        )

        # Remove Docker CE packages
        yum.packages(
            name="Remove Docker CE packages",
            packages=packages,
            present=False,
            _sudo=True,
        )

        # Remove Docker repository file
        files.file(
            name="Remove Docker YUM repository",
            path="/etc/yum.repos.d/docker-ce.repo",
            present=False,
            _sudo=True,
        )

        logger.info("Docker YUM packages and repository removed")


class DNFManager(PackageManager):
    """Manages DNF repository configuration for Fedora/newer RHEL systems."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "DNF"

    def backup_sources(self) -> None:
        """Backup original DNF repository configuration."""
        raise NotImplementedError("DNF support not yet implemented")

    def restore_sources(self) -> None:
        """Restore original DNF repository configuration."""
        raise NotImplementedError("DNF support not yet implemented")

    def setup_offline_only_repositories(self, repo_filename: str = "local-repo-only") -> None:
        """Setup DNF to use only the specified offline repository."""
        raise NotImplementedError("DNF support not yet implemented")

    def add_local_repository(self, repo_filename: str = "local-repo") -> None:
        """Add local repository alongside existing ones."""
        raise NotImplementedError("DNF support not yet implemented")

    def update_package_lists(self) -> None:
        """Update DNF package lists."""
        raise NotImplementedError("DNF support not yet implemented")

    def install_packages(self, packages: list[str], update: bool = False) -> None:
        """Install packages using DNF."""
        raise NotImplementedError("DNF support not yet implemented")

    def _cleanup_platform_specific_files(self) -> None:
        """Clean up DNF-specific backup and temporary files."""
        raise NotImplementedError("DNF support not yet implemented")

    def _emergency_restore_implementation(self) -> None:
        """Emergency DNF repository restore implementation."""
        raise NotImplementedError("DNF support not yet implemented")

    def setup_docker_repository(
        self,
        docker_installation_uri: str,
        docker_installation_os: str,
        docker_installation_distro: str,
        template_locator: Any = None,
    ) -> None:
        """Setup Docker repository for Fedora/newer RHEL systems using DNF.

        Args:
            docker_installation_uri: Base URI for Docker installation
            docker_installation_os: OS identifier (e.g., 'centos', 'fedora')
            docker_installation_distro: Distribution identifier (e.g., '8', '39')
            template_locator: Function to locate template files (optional)
        """
        from pyinfra.operations import dnf, files

        # Install prerequisites
        dnf.packages(
            name="Ensure DNF deps. installed for Docker installation",
            packages=["ca-certificates", "curl"],
            latest=True,
            _sudo=True,
        )

        # Determine template source
        if template_locator:
            template_src = template_locator("docker-yum-repo.j2")
        else:
            template_src = "docker-yum-repo.j2"

        # Add Docker repository
        files.template(
            name="Create Docker YUM repository file",
            src=template_src,
            dest="/etc/yum.repos.d/docker-ce.repo",
            _sudo=True,
            docker_installation_uri=docker_installation_uri,
            docker_installation_os=docker_installation_os,
            docker_installation_distro=docker_installation_distro,
        )

        logger.info(f"Docker DNF repository configured: {docker_installation_uri}")

    def remove_docker_packages_and_repository(self, packages: list[str]) -> None:
        """Remove Docker packages and clean up repository configuration.

        Args:
            packages: List of Docker packages to remove
        """
        from pyinfra.operations import dnf, files

        # Remove conflicting packages first
        conflicting_packages = [
            "docker",
            "docker-client",
            "docker-client-latest",
            "docker-common",
            "docker-latest",
            "docker-latest-logrotate",
            "docker-logrotate",
            "docker-engine",
            "podman",
            "runc",
        ]

        dnf.packages(
            name="Remove conflicting Docker packages",
            packages=conflicting_packages,
            present=False,
            _sudo=True,
        )

        # Remove Docker CE packages
        dnf.packages(
            name="Remove Docker CE packages",
            packages=packages,
            present=False,
            _sudo=True,
        )

        # Remove Docker repository file
        files.file(
            name="Remove Docker DNF repository",
            path="/etc/yum.repos.d/docker-ce.repo",
            present=False,
            _sudo=True,
        )

        logger.info("Docker DNF packages and repository removed")
