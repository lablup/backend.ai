"""Types for vfolder repository operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.specs.searcher import SearcherResult

__all__ = (
    "BulkVFolderPurgeResult",
    "UserVFolderMountPage",
    "VFolderPurgeFailure",
)


@dataclass(frozen=True)
class VFolderPurgeFailure:
    """A single vfolder that failed to purge in a bulk repository call."""

    vfolder_id: UUID
    exception: BackendAIError


@dataclass
class BulkVFolderPurgeResult:
    """Partial-success result of ``delete_vfolders_forever``."""

    succeeded: list[VFolderData] = field(default_factory=list)
    failures: list[VFolderPurgeFailure] = field(default_factory=list)


@dataclass(frozen=True)
class UserVFolderMountPage:
    """A page of vfolders, and the mount policy rows one user holds on them.

    A vfolder the user holds no row on is absent from ``policies``.
    """

    page: SearcherResult[VFolderData]
    policies: Mapping[VFolderUUID, VFolderMountPolicy]
