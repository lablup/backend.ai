from __future__ import annotations

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.storage.probe.check import AbstractStatusCheck


class AbstractVolumeStatusCheck(AbstractStatusCheck[StorageVolumeName]):
    """A volume's status check."""
