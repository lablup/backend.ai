from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck

type VolumeStatusCheck = AbstractVolumeStatusCheck[StorageStatusResult]


class VolumeStatusCheckRegistry:
    """Every volume status check a service runs, and the latest observation of each."""

    _checks: Sequence[VolumeStatusCheck]

    def __init__(self, checks: Sequence[VolumeStatusCheck]) -> None:
        self._checks = checks

    def snapshot(self) -> Mapping[StorageVolumeName, StorageStatusResult | None]:
        """The last observation of every check, None where one has not run yet."""
        return {check.id(): check.latest() for check in self._checks}
