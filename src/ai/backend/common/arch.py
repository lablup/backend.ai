import platform
from collections.abc import Mapping
from typing import Final

__all__ = (
    "CURRENT_ARCH",
    "DEFAULT_IMAGE_ARCH",
    "arch_name_aliases",
)


arch_name_aliases: Final[Mapping[str, str]] = {
    "arm64": "aarch64",  # macOS with LLVM
    "amd64": "x86_64",  # Windows/Linux
    "x64": "x86_64",  # Windows
    "x32": "x86",  # Windows
    "i686": "x86",  # Windows
}

CURRENT_ARCH = platform.machine().lower().strip()
DEFAULT_IMAGE_ARCH = arch_name_aliases.get(CURRENT_ARCH, CURRENT_ARCH)
