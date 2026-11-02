from __future__ import annotations

from collections.abc import Sequence
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendMetadata,
    StorageBackendType,
    StorageCheckState,
    StorageStatusCheckType,
    StorageStatusResultData,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.report import (
    StorageStatusReportTask,
    StorageStatusReportTaskArgs,
)
from ai.backend.common.storage.probe.reporter import VolumeStatusReporter, VolumeStatusReporterArgs
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck


def _make_check(volume_name: str) -> Mock:
    check = Mock(spec=AbstractVolumeStatusCheck)
    check.id.return_value = StorageVolumeName(volume_name)
    check.storage_backend_metadata.return_value = StorageBackendMetadata(
        name=StorageBackendType("vfs"), capabilities=StorageBackendCapabilities()
    )
    check.latest.return_value = StorageStatusResultData(
        check_type=StorageStatusCheckType.VFS,
        check_state=StorageCheckState.NOT_CHECKED,
        check_started_at=None,
        duration=None,
        error_msg=None,
        device_id=None,
        extra=None,
    )
    return check


def _make_task(
    checks: Sequence[AbstractVolumeStatusCheck], event_producer: EventProducer
) -> StorageStatusReportTask:
    return StorageStatusReportTask(
        StorageStatusReportTaskArgs(
            reporter=VolumeStatusReporter(
                VolumeStatusReporterArgs(
                    registry=VolumeStatusCheckRegistry(checks),
                    service_catalog_instance_id="instance-1",
                    service_catalog_service_group="storage-proxy",
                )
            ),
            event_producer=event_producer,
            interval=30.0,
            initial_delay=10.0,
        )
    )


class TestStorageStatusReportTask:
    @pytest.fixture
    def event_producer(self) -> Mock:
        producer = Mock(spec=EventProducer)
        producer.anycast_event = AsyncMock()
        return producer

    async def test_publishes_observation_of_each_check(self, event_producer: Mock) -> None:
        task = _make_task([_make_check("volume-1"), _make_check("volume-2")], event_producer)

        await task.run()

        event_producer.anycast_event.assert_awaited_once()
        event = event_producer.anycast_event.await_args.args[0]
        assert [observation.volume_name for observation in event.observations] == [
            "volume-1",
            "volume-2",
        ]

    async def test_publishes_nothing_without_checks(self, event_producer: Mock) -> None:
        task = _make_task([], event_producer)

        await task.run()

        event_producer.anycast_event.assert_not_awaited()
