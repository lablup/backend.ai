from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendMetadata, StorageStatusResultData
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck


@dataclass(frozen=True)
class VolumeStatusSnapshot:
    """The last observation of one volume's check, and the backend the volume is served by."""

    storage_backend_metadata: StorageBackendMetadata
    result: StorageStatusResultData


class VolumeStatusCheckRegistry:
    """Every volume status check a service runs, and the latest observation of each."""

    _checks: dict[StorageVolumeName, AbstractVolumeStatusCheck]

    def __init__(self, checks: Sequence[AbstractVolumeStatusCheck]) -> None:
        self._checks = {check.id(): check for check in checks}

    def add(self, check: AbstractVolumeStatusCheck) -> None:
        """Adds the check; a check whose volume name is held is skipped."""
        self._checks.setdefault(check.id(), check)

    def remove(self, volume_name: StorageVolumeName) -> None:
        self._checks.pop(volume_name, None)

    def snapshot(self) -> Mapping[StorageVolumeName, VolumeStatusSnapshot]:
        """The last observation of every check."""
        return {
            check.id(): VolumeStatusSnapshot(
                storage_backend_metadata=check.storage_backend_metadata(), result=check.latest()
            )
            for check in self._checks.values()
        }
