"""Platform Detection Utilities

This module provides platform detection and OS-specific utilities for PyInfra deployments.
"""

import logging
from enum import Enum
from typing import Any

from pyinfra import host
from pyinfra.facts.files import File

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported platform types for deployments."""

    DEBIAN = "debian"  # Debian and Ubuntu systems (APT-based)
    RHEL = "rhel"  # RHEL, CentOS, Fedora systems (YUM/DNF-based)
    ALPINE = "alpine"  # Alpine Linux (APK-based)
    ARCH = "arch"  # Arch Linux (Pacman-based)
    UNKNOWN = "unknown"


class PlatformInfo:
    """Container for platform detection information."""

    def __init__(
        self,
        platform_type: PlatformType,
        distribution: str | None = None,
        version: str | None = None,
        package_manager: str | None = None,
    ) -> None:
        self.platform_type = platform_type
        self.distribution = distribution
        self.version = version
        self.package_manager = package_manager

    @property
    def is_debian_based(self) -> bool:
        """Check if platform is Debian/Ubuntu-based."""
        return self.platform_type == PlatformType.DEBIAN

    @property
    def is_rhel_based(self) -> bool:
        """Check if platform is RHEL/CentOS/Fedora-based."""
        return self.platform_type == PlatformType.RHEL

    @property
    def is_alpine_based(self) -> bool:
        """Check if platform is Alpine Linux-based."""
        return self.platform_type == PlatformType.ALPINE

    @property
    def is_arch_based(self) -> bool:
        """Check if platform is Arch Linux-based."""
        return self.platform_type == PlatformType.ARCH

    def __repr__(self) -> str:
        return f"PlatformInfo(type={self.platform_type.value}, dist={self.distribution}, pkg_mgr={self.package_manager})"


def detect_platform() -> PlatformInfo:
    """Detect the target platform using PyInfra facts.

    Returns:
        PlatformInfo object with detected platform information

    Raises:
        ValueError: If platform detection fails or platform is unsupported
    """
    # Check for distribution-specific files
    debian_version = host.get_fact(File, path="/etc/debian_version")
    redhat_release = host.get_fact(File, path="/etc/redhat-release")
    centos_release = host.get_fact(File, path="/etc/centos-release")
    alpine_release = host.get_fact(File, path="/etc/alpine-release")
    arch_release = host.get_fact(File, path="/etc/arch-release")

    # Detect Debian/Ubuntu systems
    if debian_version:
        # Try to determine specific distribution
        ubuntu_version = host.get_fact(File, path="/etc/lsb-release")
        if ubuntu_version:
            distribution = "ubuntu"
        else:
            distribution = "debian"

        return PlatformInfo(
            platform_type=PlatformType.DEBIAN, distribution=distribution, package_manager="apt"
        )

    # Detect RHEL/CentOS/Fedora systems
    if redhat_release or centos_release:
        # Determine package manager (DNF for newer systems, YUM for older)
        try:
            from pyinfra.operations import server

            server.shell(
                name="Check for DNF availability",
                commands=["which dnf"],
                _sudo=False,
            )
            package_manager = "dnf"
        except Exception:
            package_manager = "yum"

        # Try to determine specific distribution
        if centos_release:
            distribution = "centos"
        elif redhat_release:
            # Could be RHEL or Fedora, would need more detailed detection
            distribution = "rhel"
        else:
            distribution = "rhel"

        return PlatformInfo(
            platform_type=PlatformType.RHEL,
            distribution=distribution,
            package_manager=package_manager,
        )

    # Detect Alpine Linux
    if alpine_release:
        return PlatformInfo(
            platform_type=PlatformType.ALPINE, distribution="alpine", package_manager="apk"
        )

    # Detect Arch Linux
    if arch_release:
        return PlatformInfo(
            platform_type=PlatformType.ARCH, distribution="arch", package_manager="pacman"
        )

    # Unknown platform
    logger.warning("Unable to detect platform type")
    return PlatformInfo(
        platform_type=PlatformType.UNKNOWN, distribution="unknown", package_manager="unknown"
    )


def get_platform_type() -> PlatformType:
    """Get just the platform type without full detection.

    Returns:
        PlatformType enum value
    """
    return detect_platform().platform_type


def is_supported_platform(platform_info: PlatformInfo | None = None) -> bool:
    """Check if the detected platform is supported for deployments.

    Args:
        platform_info: Optional platform info. If None, will detect automatically.

    Returns:
        True if platform is supported, False otherwise
    """
    if platform_info is None:
        platform_info = detect_platform()

    supported_platforms = {PlatformType.DEBIAN, PlatformType.RHEL}
    return platform_info.platform_type in supported_platforms


def require_supported_platform(operation_name: str) -> PlatformInfo:
    """Ensure the platform is supported for the given operation.

    Args:
        operation_name: Name of the operation requiring platform support

    Returns:
        PlatformInfo for the supported platform

    Raises:
        ValueError: If platform is not supported
    """
    platform_info = detect_platform()

    if not is_supported_platform(platform_info):
        supported = [p.value for p in {PlatformType.DEBIAN, PlatformType.RHEL}]
        raise ValueError(
            f"Platform {platform_info.platform_type.value} is not supported for {operation_name}. "
            f"Supported platforms: {', '.join(supported)}"
        )

    logger.info(f"Platform detection for {operation_name}: {platform_info}")
    return platform_info


# Platform-specific constants and configurations
PLATFORM_CONFIGS: dict[PlatformType, dict[str, Any]] = {
    PlatformType.DEBIAN: {
        "package_extensions": [".deb"],
        "keyring_dir": "/etc/apt/keyrings",
        "sources_dir": "/etc/apt/sources.list.d",
        "package_install_cmd": "dpkg -i",
        "common_packages": ["ca-certificates", "curl", "gnupg", "lsb-release"],
    },
    PlatformType.RHEL: {
        "package_extensions": [".rpm"],
        "repo_dir": "/etc/yum.repos.d",
        "package_install_cmd": "rpm -ivh",
        "common_packages": ["ca-certificates", "curl", "gnupg2"],
    },
    PlatformType.ALPINE: {
        "package_extensions": [".apk"],
        "repo_dir": "/etc/apk/repositories",
        "package_install_cmd": "apk add --allow-untrusted",
        "common_packages": ["ca-certificates", "curl"],
    },
    PlatformType.ARCH: {
        "package_extensions": [".pkg.tar.xz", ".pkg.tar.zst"],
        "package_install_cmd": "pacman -U --noconfirm",
        "common_packages": ["ca-certificates", "curl"],
    },
}


def get_platform_config(platform_type: PlatformType, key: str, default: Any = None) -> Any:
    """Get platform-specific configuration value.

    Args:
        platform_type: The platform type
        key: Configuration key to retrieve
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    return PLATFORM_CONFIGS.get(platform_type, {}).get(key, default)
