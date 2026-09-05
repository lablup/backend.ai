from __future__ import annotations

import enum
from datetime import timedelta
from typing import Final

from pydantic import ConfigDict

from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.common.types import BackendAISchema


class VFolderStorageTarget(BackendAISchema):
    """Target for direct import to a specific virtual folder."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vfolder_id: VFolderIDField
    volume_name: str


class NamedStorageTarget(BackendAISchema):
    """Target for named storage lookup via storage pool."""

    storage_name: str


ArtifactStorageTarget = NamedStorageTarget | VFolderStorageTarget


class StorageBackendType(enum.StrEnum):
    """The storage backend implementations a volume can be served by.

    The value is what a storage-proxy volume config names under ``backend`` and what the
    ``storage_backends.type`` column stores.
    """

    VFS = "vfs"
    XFS = "xfs"
    CEPHFS = "cephfs"
    PURESTORAGE = "purestorage"
    NETAPP = "netapp"
    WEKA = "weka"
    GPFS = "gpfs"
    SPECTRUMSCALE = "spectrumscale"
    DELLEMC_ONEFS = "dellemc-onefs"
    VAST = "vast"
    EXASCALER = "exascaler"
    HAMMERSPACE = "hammerspace"
    HAMMERSPACE_BASE = "hammerspace-base"
    NOOP = "noop"


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS_STORAGE = "vfs_storage"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"


# How long a backend or volume may go without a fresh check before it counts as stale.
# The per-row ``status_stale_after`` column overrides it; this is only its default.
DEFAULT_STATUS_STALE_AFTER: Final[timedelta] = timedelta(hours=1)


class ServiceStorageStatus(enum.StrEnum):
    """How a service currently sees a storage backend or volume it relates to.

    healthy: the last check found no problem.
    unhealthy: the check found a problem.
    stale: no check has landed for a while.
    detached: the relationship was removed outright.
    """

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STALE = "stale"
    DETACHED = "detached"
