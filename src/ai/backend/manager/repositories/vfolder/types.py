"""Types for vfolder repository operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.data.vfolder.types import VFolderData

__all__ = (
    "BulkVFolderPurgeResult",
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
