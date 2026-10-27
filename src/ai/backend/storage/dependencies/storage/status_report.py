from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Final, override

from ai.backend.common.cron.local_cron import LocalCron
from ai.backend.common.data.storage.types import StorageBackendType
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.report import (
    StorageStatusReportTask,
    StorageStatusReportTaskArgs,
)
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

STATUS_REPORT_INTERVAL: Final[float] = 60.0


@dataclass
class StatusReportInput:
    """Input required for the status report setup."""

    pidx: int
    local_config: StorageProxyUnifiedConfig
    registry: VolumeStatusCheckRegistry
    event_producer: EventProducer


class StatusReportProvider(NonMonitorableDependencyProvider[StatusReportInput, None]):
    """Provider for the periodic storage status report.

    Only worker 0 reports, as only it runs the checks. A service without both a service
    group and an instance id has no catalog record to report under, so it reports nothing.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "status-report"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StatusReportInput) -> AsyncIterator[None]:
        local_config = setup_input.local_config
        service_group = local_config.service_discovery.service_group
        instance_id = local_config.service_discovery.instance_id
        if setup_input.pidx != 0 or not service_group or not instance_id:
            yield None
            return
        cron = LocalCron([
            StorageStatusReportTask(
                StorageStatusReportTaskArgs(
                    registry=setup_input.registry,
                    backend_types={
                        volume_name: StorageBackendType(volume_config.backend)
                        for volume_name, volume_config in local_config.volume.items()
                    },
                    event_producer=setup_input.event_producer,
                    instance_id=instance_id,
                    service_group=service_group,
                    interval=STATUS_REPORT_INTERVAL,
                )
            )
        ])
        await cron.start()
        try:
            yield None
        finally:
            await cron.stop()
