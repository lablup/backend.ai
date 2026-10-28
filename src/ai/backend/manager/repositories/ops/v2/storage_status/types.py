from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult, StorageVolumeSubjectData


@dataclass(frozen=True)
class VolumeStatusRecord:
    """One volume a service reported, and its check's result, None while not checked."""

    subject: StorageVolumeSubjectData
    result: StorageStatusResult | None


@dataclass(frozen=True)
class ServiceVolumeStatusReport:
    """Every volume one service reported at once."""

    service_catalog_service_group: str
    service_catalog_instance_id: str
    volumes: Sequence[VolumeStatusRecord]
