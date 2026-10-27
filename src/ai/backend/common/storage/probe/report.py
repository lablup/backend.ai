from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageBackendType, StorageStatusResult
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.storage_status.anycast import (
    StorageStatusObservation,
    StorageStatusReportEvent,
    StorageVolumeSubject,
)
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry

__all__ = (
    "StorageStatusReportTask",
    "StorageStatusReportTaskArgs",
)


@dataclass
class StorageStatusReportTaskArgs:
    registry: VolumeStatusCheckRegistry
    backend_types: Mapping[StorageVolumeName, StorageBackendType]
    event_producer: EventProducer
    instance_id: str
    service_group: str
    interval: float


class StorageStatusReportTask(PeriodicTask):
    """Publishes the latest observation of every check, on a cadence of its own.

    It reads what the checks left behind, so a hung check keeps reporting its last result.
    """

    _registry: VolumeStatusCheckRegistry
    _backend_types: Mapping[StorageVolumeName, StorageBackendType]
    _event_producer: EventProducer
    _instance_id: str
    _service_group: str
    _interval: float

    def __init__(self, args: StorageStatusReportTaskArgs) -> None:
        self._registry = args.registry
        self._backend_types = args.backend_types
        self._event_producer = args.event_producer
        self._instance_id = args.instance_id
        self._service_group = args.service_group
        self._interval = args.interval

    @property
    @override
    def name(self) -> str:
        return "storage_status_report"

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._interval

    @override
    async def run(self) -> None:
        event = StorageStatusReportEvent(
            instance_id=self._instance_id,
            service_group=self._service_group,
            observations=[
                self._volume_observation(volume_name, result)
                for volume_name, result in self._registry.snapshot().items()
            ],
        )
        await self._event_producer.anycast_event(event)

    def _volume_observation(
        self, volume_name: StorageVolumeName, result: StorageStatusResult | None
    ) -> StorageStatusObservation:
        subject = StorageVolumeSubject(
            name=volume_name, backend_type=self._backend_types[volume_name]
        )
        if result is None:
            return StorageStatusObservation(subject=subject)
        return StorageStatusObservation(
            subject=subject,
            check_started_at=result.check_started_at,
            duration=result.duration,
            error_msg=result.error_msg,
        )
