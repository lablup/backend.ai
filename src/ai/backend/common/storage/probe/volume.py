from __future__ import annotations

from abc import abstractmethod

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendMetadata
from ai.backend.common.storage.probe.check import AbstractStatusCheck


class AbstractVolumeStatusCheck(AbstractStatusCheck[StorageVolumeName]):
    """A volume's status check."""

    @abstractmethod
    def storage_backend_metadata(self) -> StorageBackendMetadata:
        """The storage backend implementation the volume is served by."""
        raise NotImplementedError
