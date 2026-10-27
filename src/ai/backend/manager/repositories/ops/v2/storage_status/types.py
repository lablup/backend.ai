from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import ServiceStorageStatus, StorageBackendType


@dataclass(frozen=True)
class VolumeStatusWrite:
    """Whether and when one service last checked a volume it holds."""

    volume_name: StorageVolumeName
    backend_type: StorageBackendType
    status: ServiceStorageStatus
    status_checked_at: datetime | None


@dataclass(frozen=True)
class VolumeStatusReportWrite:
    """Every volume one service reported at once."""

    service_group: str
    instance_id: str
    volumes: Sequence[VolumeStatusWrite]
