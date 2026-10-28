"""Event handler for storage status report events."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from ai.backend.common.data.storage.types import (
    StorageBackendType,
    StorageStatusObservationData,
    StorageStatusResult,
    StorageStatusResultData,
    StorageVolumeSubjectData,
)
from ai.backend.common.events.event_types.storage_status.anycast import (
    StorageStatusObservation,
    StorageStatusReportEvent,
)
from ai.backend.common.storage.probe.exceptions import InvalidStorageStatusObservation
from ai.backend.common.storage.probe.parser import AbstractStatusDataParser
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.repositories.ops.v2.storage_status.types import (
    ServiceVolumeStatusReport,
    VolumeStatusRecord,
)
from ai.backend.manager.repositories.storage_status.repository import StorageStatusRepository

log = StructuredLogger(logging.getLogger(__spec__.name))


class StorageStatusDataParserRegistry:
    """The data parser of each storage backend type whose reports the manager reads."""

    _parsers: Mapping[StorageBackendType, AbstractStatusDataParser[StorageStatusResult]]

    def __init__(
        self, parsers: Mapping[StorageBackendType, AbstractStatusDataParser[StorageStatusResult]]
    ) -> None:
        self._parsers = parsers

    def get(
        self, backend_type: StorageBackendType
    ) -> AbstractStatusDataParser[StorageStatusResult] | None:
        return self._parsers.get(backend_type)


class StorageStatusEventHandler:
    """Records the volumes a service holds and when it last checked them."""

    _repository: StorageStatusRepository
    _parser_registry: StorageStatusDataParserRegistry

    def __init__(
        self,
        repository: StorageStatusRepository,
        parser_registry: StorageStatusDataParserRegistry,
    ) -> None:
        self._repository = repository
        self._parser_registry = parser_registry

    async def handle_reported(
        self,
        _context: None,
        _source: AgentId,
        event: StorageStatusReportEvent,
    ) -> None:
        volumes = [
            self._volume_status_record(self._observation_data(observation))
            for observation in event.observations
        ]
        await self._repository.record_volume_status_report(
            ServiceVolumeStatusReport(
                service_catalog_service_group=event.service_catalog_service_group,
                service_catalog_instance_id=event.service_catalog_instance_id,
                volumes=volumes,
            )
        )

    def _volume_status_record(
        self, observation: StorageStatusObservationData
    ) -> VolumeStatusRecord:
        """A record without a result where the observation cannot be parsed, so only the
        holding is touched."""
        parser = self._parser_registry.get(observation.subject.backend_type)
        if parser is None:
            log.warning(
                "no data parser for the storage backend type",
                volume_name=observation.subject.name,
                backend_type=observation.subject.backend_type,
            )
            return VolumeStatusRecord(subject=observation.subject, result=None)
        try:
            result = parser.parse(observation.result)
        except InvalidStorageStatusObservation:
            log.exception(
                "storage status observation cannot be parsed",
                volume_name=observation.subject.name,
            )
            return VolumeStatusRecord(subject=observation.subject, result=None)
        return VolumeStatusRecord(subject=observation.subject, result=result)

    def _observation_data(
        self, observation: StorageStatusObservation
    ) -> StorageStatusObservationData:
        return StorageStatusObservationData(
            subject=StorageVolumeSubjectData(
                name=observation.subject.name,
                backend_type=observation.subject.backend_type,
            ),
            result=StorageStatusResultData(
                check_started_at=observation.check_started_at,
                status=observation.status,
                duration=observation.duration,
                error_msg=observation.error_msg,
                device_id=observation.device_id,
            ),
        )
