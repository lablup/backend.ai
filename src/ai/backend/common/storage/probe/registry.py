from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

from ai.backend.common.configs.volume.base import VolumeConfigs
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.storage.exceptions import (
    VolumeAlreadyDeclaredError,
    VolumeTypeNotSupportedError,
)
from ai.backend.common.storage.probe.check import AbstractStatusCheck
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck

type VolumeStatusCheck = AbstractStatusCheck[StorageVolumeID, StorageStatusResult]


class VolumeStatusCheckRegistry:
    """Every volume status check a service runs, and the latest observation of each."""

    _checks: Sequence[VolumeStatusCheck]

    def __init__(self, checks: Sequence[VolumeStatusCheck]) -> None:
        self._checks = checks

    @classmethod
    def create(cls, config: VolumeConfigs) -> Self:
        """Validates each declaration against its volume type's schema and builds its check."""
        checks: list[VolumeStatusCheck] = []
        seen: set[StorageVolumeID] = set()
        for volume_id, declared in config.volumes.items():
            if volume_id in seen:
                raise VolumeAlreadyDeclaredError(f"Volume declared twice: {volume_id}")
            check_cls = AbstractVolumeStatusCheck.declared(declared.volume_type)
            if check_cls is None:
                raise VolumeTypeNotSupportedError(
                    f"No status check for volume type {declared.volume_type!r}: {volume_id}"
                )
            checks.append(check_cls.build(volume_id, declared))
            seen.add(volume_id)
        return cls(checks)

    def snapshot(self) -> Mapping[StorageVolumeID, StorageStatusResult | None]:
        """The last observation of every check, None where one has not run yet."""
        return {check.id(): check.latest() for check in self._checks}
