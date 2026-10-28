from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageStatusResultData
from ai.backend.common.storage.probe.reporter import AbstractVolumeStatusReporter


class VolumeStatusReporterRegistry:
    """Every volume status reporter a service runs, and the latest observation of each."""

    _reporters: Sequence[AbstractVolumeStatusReporter]

    def __init__(self, reporters: Sequence[AbstractVolumeStatusReporter]) -> None:
        self._reporters = reporters

    def snapshot(self) -> Mapping[StorageVolumeName, StorageStatusResultData]:
        """The last observation of every reporter, in the shape it is reported in."""
        snapshot: dict[StorageVolumeName, StorageStatusResultData] = {}
        for reporter in self._reporters:
            snapshot.update(reporter.report())
        return snapshot
