from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageStatusResultData
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck


class VolumeStatusCheckRegistry:
    """Every volume status check a service runs, and the latest observation of each."""

    _checks: Sequence[AbstractVolumeStatusCheck]

    def __init__(self, checks: Sequence[AbstractVolumeStatusCheck]) -> None:
        self._checks = checks

    def snapshot(self) -> Mapping[StorageVolumeName, StorageStatusResultData]:
        """The last observation of every check."""
        return {check.id(): check.latest() for check in self._checks}
