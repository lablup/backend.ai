from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageStatusResultData
from ai.backend.common.events.event_types.storage_status.anycast import (
    StorageStatusObservation,
    StorageStatusReportEvent,
)
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry


@dataclass
class VolumeStatusReporterArgs:
    registry: VolumeStatusCheckRegistry
    service_catalog_instance_id: str
    service_catalog_service_group: str


class VolumeStatusReporter:
    """Turns the latest observation of every volume status check into the report event."""

    _registry: VolumeStatusCheckRegistry
    _service_catalog_instance_id: str
    _service_catalog_service_group: str

    def __init__(self, args: VolumeStatusReporterArgs) -> None:
        self._registry = args.registry
        self._service_catalog_instance_id = args.service_catalog_instance_id
        self._service_catalog_service_group = args.service_catalog_service_group

    def report(self) -> StorageStatusReportEvent:
        return StorageStatusReportEvent(
            service_catalog_instance_id=self._service_catalog_instance_id,
            service_catalog_service_group=self._service_catalog_service_group,
            observations=[
                self._observation(volume_name, data)
                for volume_name, data in self._registry.snapshot().items()
            ],
        )

    def _observation(
        self, volume_name: StorageVolumeName, data: StorageStatusResultData
    ) -> StorageStatusObservation:
        return StorageStatusObservation(
            volume_name=volume_name,
            check_type=data.check_type,
            check_state=data.check_state,
            check_started_at=data.check_started_at,
            duration=data.duration,
            error_msg=data.error_msg,
            device_id=data.device_id,
            extra=dict(data.extra) if data.extra is not None else None,
        )
