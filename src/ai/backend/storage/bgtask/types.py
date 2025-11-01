from __future__ import annotations

import enum
from typing import Self

from ai.backend.common.bgtask.types import BgtaskNameBase


class StorageBgtaskName(enum.StrEnum, BgtaskNameBase):
    """Background task names for storage component."""

    CLONE_VFOLDER = "clone_vfolder"
    DELETE_VFOLDER = "delete_vfolder"

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Create instance from string value."""
        return cls(value)
