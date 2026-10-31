from __future__ import annotations

from dataclasses import dataclass
from typing import Final, override

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.storage.probe.reporter import VolumeStatusReporter


@dataclass
class StorageStatusReportTaskArgs:
    reporter: VolumeStatusReporter
    event_producer: EventProducer
    interval: float
    initial_delay: float


class StorageStatusReportTask(PeriodicTask):
    """Periodically publish the latest observation of every volume status check."""

    _reporter: Final[VolumeStatusReporter]
    _event_producer: Final[EventProducer]
    _interval: Final[float]
    _initial_delay: Final[float]

    def __init__(self, args: StorageStatusReportTaskArgs) -> None:
        self._reporter = args.reporter
        self._event_producer = args.event_producer
        self._interval = args.interval
        self._initial_delay = args.initial_delay

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
        return self._initial_delay

    @override
    async def run(self) -> None:
        await self._event_producer.anycast_event(self._reporter.report())
