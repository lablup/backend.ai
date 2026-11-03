from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.report import (
    StorageStatusReportTask,
    StorageStatusReportTaskArgs,
)
from ai.backend.common.storage.probe.reporter import VolumeStatusReporter, VolumeStatusReporterArgs
from ai.backend.common.storage.probe.runner import ProbeCheckRunner, ProbeCheckRunnerArgs
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.volumes.pool import VolumePool


@dataclass
class StatusProbeInput:
    """Input required for the status probe setup."""

    local_config: StorageProxyUnifiedConfig
    pidx: int
    volume_pool: VolumePool
    event_producer: EventProducer


@dataclass
class StatusProbeResources:
    """Container for status probe resources."""

    registry: VolumeStatusCheckRegistry


class StatusProbeProvider(NonMonitorableDependencyProvider[StatusProbeInput, StatusProbeResources]):
    """Provider for the volume status check registry, the runner that drives it and the report.

    Only worker 0 runs the checks and publishes the report, so a node reports each volume
    once; every worker holds the registry.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "status-probe"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StatusProbeInput) -> AsyncIterator[StatusProbeResources]:
        checks = setup_input.volume_pool.volume_status_checks()
        registry = VolumeStatusCheckRegistry(checks)
        runner = ProbeCheckRunner(ProbeCheckRunnerArgs(checks=checks))
        local_cron = LocalCron(self._report_tasks(setup_input, registry))
        if setup_input.pidx == 0:
            await runner.start()
            await local_cron.start()
        try:
            yield StatusProbeResources(registry=registry)
        finally:
            if setup_input.pidx == 0:
                await local_cron.stop()
                await runner.stop()

    def _report_tasks(
        self, setup_input: StatusProbeInput, registry: VolumeStatusCheckRegistry
    ) -> list[PeriodicTask]:
        sd_config = setup_input.local_config.service_discovery
        # The manager tells reports apart by these ids, so without both there is nothing to report.
        if not (sd_config.instance_id and sd_config.service_group):
            return []
        reporter = VolumeStatusReporter(
            VolumeStatusReporterArgs(
                registry=registry,
                service_catalog_instance_id=sd_config.instance_id,
                service_catalog_service_group=sd_config.service_group,
            )
        )
        report_config = setup_input.local_config.storage_status_report
        return [
            StorageStatusReportTask(
                StorageStatusReportTaskArgs(
                    reporter=reporter,
                    event_producer=setup_input.event_producer,
                    interval=report_config.interval,
                    initial_delay=report_config.initial_delay,
                )
            )
        ]
