"""Event handler for storage status report events."""

from __future__ import annotations

from ai.backend.common.data.storage.types import ServiceStorageStatus
from ai.backend.common.events.event_types.storage_status.anycast import (
    StorageStatusReportEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.repositories.ops.v2.storage_status.types import (
    VolumeStatusReportWrite,
    VolumeStatusWrite,
)
from ai.backend.manager.repositories.storage_status.repository import StorageStatusRepository


class StorageStatusEventHandler:
    """Records the volumes a service holds and whether and when it last checked them."""

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
            VolumeStatusReportWrite(
                service_group=event.service_group,
                instance_id=event.instance_id,
                volumes=[
                    VolumeStatusWrite(
                        volume_name=observation.subject.name,
                        backend_type=observation.subject.backend_type,
                        status=(
                            ServiceStorageStatus.NOT_CHECKED
                            if observation.check_started_at is None
                            else ServiceStorageStatus.CHECKED
                        ),
                        status_checked_at=observation.check_started_at,
                    )
                    for observation in event.observations
                ],
            )
        )
