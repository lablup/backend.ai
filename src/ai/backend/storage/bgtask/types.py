from __future__ import annotations

import enum
from typing import Self


class StorageBgtaskName(enum.StrEnum):
    """Background task names for storage component."""

    CLONE_VFOLDER = "clone_vfolder"
    DELETE_VFOLDER = "delete_vfolder"
    DELETE_FILES = "delete_files"

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Create instance from string value."""
        return cls(value)
