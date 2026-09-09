from __future__ import annotations

import enum
from datetime import timedelta
from typing import Final, NewType

from pydantic import ConfigDict, Field

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


# A storage backend implementation's name, as the storage proxy registers it and as
# ``storage_backend_types.name`` records it. Not a closed set: a storage backend plugin
# registers names of its own.
StorageBackendType = NewType("StorageBackendType", str)


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


class StorageBackendCapability(enum.StrEnum):
    """What a volume implementation can do, as it reports through ``get_capabilities()``."""

    VFOLDER = "vfolder"
    METRIC = "metric"
    QUOTA = "quota"
    FAST_FS_SIZE = "fast-fs-size"
    FAST_SCAN = "fast-scan"
    FAST_SIZE = "fast-size"


class StorageBackendCapabilities(BackendAISchema):
    """What a volume implementation reports through ``get_capabilities()``.

    A capability absent from the set is not supported, so a capability added later
    reads as absent on the rows written before it existed.
    """

    supported: frozenset[StorageBackendCapability] = Field(default_factory=frozenset)


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
