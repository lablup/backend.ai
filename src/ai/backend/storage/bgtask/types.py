from __future__ import annotations

import enum


class StorageBgtaskName(enum.StrEnum):
    """Background task names for storage component."""

    CLONE_VFOLDER = "clone_vfolder"
    DELETE_VFOLDER = "delete_vfolder"
