"""Event handler for storage status report events."""

from __future__ import annotations

import logging

from ai.backend.common.events.event_types.storage_status.anycast import (
    StorageStatusObservation,
    StorageStatusReportEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.repositories.ops.v2.storage_status.types import (
    ServiceVolumeStatusReport,
    VolumeStatusRecord,
)
from ai.backend.manager.repositories.storage_status.repository import StorageStatusRepository

log = StructuredLogger(logging.getLogger(__spec__.name))


class StorageStatusEventHandler:
    """Records the volumes a service holds and when it last checked them."""

    _repository: StorageStatusRepository

    def __init__(self, repository: StorageStatusRepository) -> None:
        self._repository = repository

    async def handle_reported(
        self,
        _context: None,
        _source: AgentId,
        event: StorageStatusReportEvent,
    ) -> None:
        await self._repository.record_volume_status_report(
            ServiceVolumeStatusReport(
                service_catalog_service_group=event.service_catalog_service_group,
                service_catalog_instance_id=event.service_catalog_instance_id,
                volumes=[
                    self._volume_status_record(observation) for observation in event.observations
                ],
            )
        )

    def _volume_status_record(self, observation: StorageStatusObservation) -> VolumeStatusRecord:
        return VolumeStatusRecord(
            volume_name=observation.volume_name,
            storage_backend_metadata=observation.storage_backend_metadata,
            check_started_at=observation.check_started_at,
        )
