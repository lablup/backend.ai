"""OS Package Management Module

This module provides cross-platform package management functionality for Backend.AI deployment.
"""

from .apt_manager import APTManager
from .package_manager import PackageManager, UnsupportedPlatformError, get_package_manager
from .rpm_manager import DNFManager, YUMManager

__all__ = [
    "PackageManager",
    "get_package_manager",
    "UnsupportedPlatformError",
    "APTManager",
    "YUMManager",
    "DNFManager",
]
