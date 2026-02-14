"""
Common types for config (dotfile) system.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

__all__ = (
    "MAXIMUM_DOTFILE_SIZE",
    "DotfilePermission",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024

DotfilePermission = Annotated[
    str,
    Field(
        pattern=r"^[0-7]{3}$",
        description="Unix-style file permission in octal notation (e.g., '755', '644')",
    ),
]
