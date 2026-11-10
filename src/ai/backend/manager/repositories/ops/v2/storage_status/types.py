from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendMetadata


@dataclass(frozen=True)
class VolumeStatusRecord:
    """One volume a service reported, and when its check started, None while not checked."""

    volume_name: StorageVolumeName
    storage_backend_metadata: StorageBackendMetadata
    check_started_at: datetime | None


@dataclass(frozen=True)
class ServiceVolumeStatusReport:
    """Every volume one service reported at once."""

    service_catalog_service_group: str
    service_catalog_instance_id: str
    volumes: Sequence[VolumeStatusRecord]
