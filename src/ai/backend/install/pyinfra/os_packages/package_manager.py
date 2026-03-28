"""Package Manager Abstraction Layer

This module provides a platform-agnostic package management system that can be used
across different Linux distributions (APT for Debian/Ubuntu, YUM/DNF for RHEL/CentOS).
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from pyinfra.operations import server

logger = logging.getLogger(__name__)


class UnsupportedPlatformError(Exception):
    """Raised when the platform is not supported by any package manager."""

    pass


class PackageManager(ABC):
    """Abstract base class for package managers across different platforms."""

    def __init__(
        self, offline_repo_url: str | None = None, fallback_repo_url: str | None = None
    ) -> None:
        """Initialize Package Manager.

        Args:
            offline_repo_url: URL for offline package repository
            fallback_repo_url: Fallback repository URL if offline_repo_url is not specified
        """
        self.offline_repo_url = offline_repo_url
        self.fallback_repo_url = fallback_repo_url

        # Generate unique backup suffix using timestamp and process ID for concurrent safety
        self._backup_suffix = f"bak-{int(time.time())}-{os.getpid()}"
        self._lock_file = f"/tmp/package-manager-{os.getpid()}.lock"
        self._sources_backed_up = False

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'apt', 'yum', 'dnf')."""
        pass

    @abstractmethod
    def backup_sources(self) -> None:
        """Backup original package sources before modification."""
        pass

    @abstractmethod
    def restore_sources(self) -> None:
        """Restore original package sources."""
        pass

    @abstractmethod
    def setup_offline_only_repositories(self, repo_filename: str = "local-repo-only") -> None:
        """Setup package manager to use only the specified offline repository."""
        pass

    @abstractmethod
    def add_local_repository(self, repo_filename: str = "local-repo") -> None:
        """Add local repository alongside existing ones."""
        pass

    @abstractmethod
    def update_package_lists(self) -> None:
        """Update package lists with guaranteed restoration on failure."""
        pass

    @abstractmethod
    def install_packages(self, packages: list[str], update: bool = False) -> None:
        """Install packages with guaranteed restoration on failure."""
        pass

    @abstractmethod
    def setup_docker_repository(
        self,
        docker_installation_uri: str,
        docker_installation_os: str,
        docker_installation_distro: str,
        template_locator: Any = None,
    ) -> None:
        """Setup Docker repository for the platform.

        Args:
            docker_installation_uri: Base URI for Docker installation
            docker_installation_os: OS identifier (e.g., 'ubuntu', 'centos')
            docker_installation_distro: Distribution identifier (e.g., 'jammy', '7')
            template_locator: Function to locate template files (optional)
        """
        pass

    @abstractmethod
    def remove_docker_packages_and_repository(self, packages: list[str]) -> None:
        """Remove Docker packages and clean up repository configuration.

        Args:
            packages: List of Docker packages to remove
        """
        pass

    def _acquire_lock(self) -> None:
        """Acquire a file lock to prevent concurrent package manager modifications."""
        server.shell(
            name=f"Acquire {self.get_platform_name()} manager lock",
            commands=[
                "mkdir -p /tmp",
                f"echo $$ > {self._lock_file}",
                "sleep 0.1",  # Small delay to reduce race conditions
            ],
            _sudo=False,
        )

    def _release_lock(self) -> None:
        """Release the file lock."""
        server.shell(
            name=f"Release {self.get_platform_name()} manager lock",
            commands=[f"rm -f {self._lock_file}"],
            _sudo=False,
        )

    def cleanup_resources(self) -> None:
        """Clean up any leftover backup files and locks."""
        try:
            self._cleanup_platform_specific_files()
            server.shell(
                name=f"Clean up {self.get_platform_name()} manager resources",
                commands=[f"rm -f {self._lock_file}"],
                _sudo=True,
            )
            logger.info(f"{self.get_platform_name()} manager resources cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up {self.get_platform_name()} manager resources: {e}")

    @abstractmethod
    def _cleanup_platform_specific_files(self) -> None:
        """Clean up platform-specific backup and temporary files."""
        pass

    def emergency_restore(self) -> None:
        """Emergency package sources restore with multiple strategies."""
        logger.warning(f"Performing emergency {self.get_platform_name()} sources restore")
        self._emergency_restore_implementation()

    @abstractmethod
    def _emergency_restore_implementation(self) -> None:
        """Platform-specific emergency restore implementation."""
        pass

    def __del__(self) -> None:
        """Cleanup resources when object is garbage collected."""
        try:
            if hasattr(self, "_sources_backed_up") and self._sources_backed_up:
                logger.warning(
                    f"{self.get_platform_name()}Manager being destroyed with active backup - attempting cleanup"
                )
                self.cleanup_resources()
        except Exception:
            pass  # Ignore errors during garbage collection

    @contextmanager
    def offline_installation_context(
        self, repo_filename: str = "local-repo-only"
    ) -> Generator["PackageManager", None, None]:
        """Context manager for offline-only package installation.

        This ensures that package sources are restored even if installation fails.

        Args:
            repo_filename: Name for the local repository file

        Usage:
            with package_manager.offline_installation_context():
                package_manager.update_package_lists()
                package_manager.install_packages(['package1', 'package2'])
        """
        try:
            self.setup_offline_only_repositories(repo_filename)
            yield self
        except Exception as install_error:
            logger.error(f"Error during offline installation: {install_error}")
            logger.error(f"Attempting to restore {self.get_platform_name()} sources and cleanup")
            try:
                self.restore_sources()
                logger.info(
                    f"{self.get_platform_name()} sources successfully restored after failed installation"
                )
            except Exception as restore_error:
                logger.error(
                    f"Failed to restore {self.get_platform_name()} sources: {restore_error}"
                )
                logger.error("Attempting emergency restoration")
                try:
                    self.emergency_restore()
                except Exception as emergency_error:
                    logger.error(f"Emergency restore also failed: {emergency_error}")
                    logger.error(
                        "System may be in inconsistent state - manual intervention required"
                    )
                    # Try cleanup as absolute last resort
                    self.cleanup_resources()
            raise
        else:
            logger.info("Offline installation completed successfully")
            self.restore_sources()

    @contextmanager
    def safe_installation_context(self) -> Generator["PackageManager", None, None]:
        """Context manager that ensures cleanup even on failures.

        This is useful when you want to ensure package sources are restored
        regardless of what happens during installation.
        """
        try:
            yield self
        except Exception:
            logger.error(
                f"Error during installation, attempting to restore {self.get_platform_name()} sources and cleanup"
            )
            try:
                self.restore_sources()
            except Exception as restore_error:
                logger.error(
                    f"Failed to restore {self.get_platform_name()} sources: {restore_error}"
                )
                # Try cleanup as last resort
                self.cleanup_resources()
            raise
        finally:
            # Always try to clean up locks and temporary files
            try:
                if hasattr(self, "_lock_file"):
                    self._release_lock()
            except Exception:
                pass  # Ignore lock cleanup errors


def get_package_manager(
    offline_repo_url: str | None = None, fallback_repo_url: str | None = None
) -> PackageManager:
    """Factory function to detect platform and return appropriate package manager.

    Args:
        offline_repo_url: URL for offline package repository
        fallback_repo_url: Fallback repository URL

    Returns:
        PackageManager instance for the detected platform

    Raises:
        UnsupportedPlatformError: If platform is not supported
    """
    # Import here to avoid circular imports
    from ai.backend.pyinfra.platform_utils import PlatformType, detect_platform

    from .apt_manager import APTManager
    from .rpm_manager import DNFManager, YUMManager

    # Detect platform using centralized utility
    platform_info = detect_platform()

    if platform_info.is_debian_based:
        logger.info(f"Detected {platform_info.distribution} with APT")
        return APTManager(offline_repo_url, fallback_repo_url)

    if platform_info.is_rhel_based:
        if platform_info.package_manager == "dnf":
            logger.info(f"Detected {platform_info.distribution} with DNF")
            return DNFManager(offline_repo_url, fallback_repo_url)
        logger.info(f"Detected {platform_info.distribution} with YUM")
        return YUMManager(offline_repo_url, fallback_repo_url)

    if platform_info.platform_type == PlatformType.ALPINE:
        logger.error("Alpine Linux detected but not yet supported")
        raise UnsupportedPlatformError("Alpine Linux support not implemented")

    if platform_info.platform_type == PlatformType.ARCH:
        logger.error("Arch Linux detected but not yet supported")
        raise UnsupportedPlatformError("Arch Linux support not implemented")

    logger.error(f"Unable to detect supported Linux distribution: {platform_info}")
    raise UnsupportedPlatformError(
        f"Unsupported platform: {platform_info.platform_type.value}. "
        "Supported platforms: Debian/Ubuntu (APT), RHEL/CentOS/Fedora (YUM/DNF)"
    )
