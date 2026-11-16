"""Internal values read off a user for vfolder creation."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("UserResourceInfo",)


@dataclass(frozen=True)
class UserResourceInfo:
    """The quota scope size a user's folder is made with, and the uid its files take."""

    max_quota_scope_size: int
    container_uid: int | None
