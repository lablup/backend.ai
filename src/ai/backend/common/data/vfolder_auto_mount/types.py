from __future__ import annotations

import enum

__all__ = ("VFolderAutoMountScopeType",)


class VFolderAutoMountScopeType(enum.StrEnum):
    """Scope whose sessions a vfolder is auto-mounted into; a personal project is a project."""

    PROJECT = "project"
