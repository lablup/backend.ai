from __future__ import annotations

from typing import Final, override

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.storage.probe.reporter import VolumeStatusReporter

STORAGE_STATUS_REPORT_INTERVAL: Final[float] = 60.0


class StorageStatusReportTask(PeriodicTask):
    """Periodically publish the latest observation of every volume status check."""

    _reporter: Final[VolumeStatusReporter]
    _event_producer: Final[EventProducer]

    def __init__(self, reporter: VolumeStatusReporter, event_producer: EventProducer) -> None:
        self._reporter = reporter
        self._event_producer = event_producer

    @property
    @override
    def name(self) -> str:
        return "storage_status_report"

    @property
    @override
    def interval(self) -> float:
        return STORAGE_STATUS_REPORT_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return STORAGE_STATUS_REPORT_INTERVAL

    @override
    async def run(self) -> None:
        await self._event_producer.anycast_event(self._reporter.report())
